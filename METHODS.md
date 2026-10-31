# occ_sim: methods (written from the code only)

Sources read: `channel/{geometry,optics,render,sensor,ambient,presets}.py`, `rx/{sampler,refs}.py`, `tx/schemes.py`,
`experiments/{common,run,efficiency}.py`, `config.py`, `README.md`, `tests/`. Where README and code differ, the code is used and the difference is noted.

## 1. Pipeline overview
Each frame goes through these steps:

payload bits → `scheme.encode` → 8×8×3 LED drive $D\in[0,1]$ (or above 1 under overdrive) × power scale $\kappa$ →
panel texture (16 px per LED, circular emitters) × Lambertian gain → **distance jitter** → pinhole projection of the 4 panel corners + random sub-pixel phase →
homography warp at 4× supersampling → area downsample (pixel integration) → Gaussian PSF → + ambient →
RGB crosstalk → exposure (e⁻) + dark → RGGB mosaic → Poisson shot noise → full-well clip → Gaussian read noise → gain, round, 8-bit clip →
OpenCV bilinear demosaic → receiver: corners (true + jitter) → inverse homography → 8×8 LED samples + border-median dark →
pilot matrix $M$ → scheme decision rule → bits → per-layer BER/FER → net goodput and CIs.

The model is static: one symbol per frame at 30 fps, a global-shutter-like capture, no rolling shutter, no motion blur, no gamma/AWB/JPEG, and ideal frame sync.

## 2. Channel models (exactly as implemented)

### 2.1 Geometry: pinhole projection and homography (`geometry.py`, `render.py`)
The panel is $n=8$ LEDs at pitch $p=8$ mm, so the side is $s=64$ mm. Its corners are centred: $\mathbf P_i=(x_i-s/2,\;y_i-s/2,\;0)$.
$$\mathbf X_i = R_z(\rho)\,R_y(\psi)\,R_x(\theta)\,\mathbf P_i + (0,0,1000\,d)^T,\qquad \mathbf u_i = f\,\frac{(X_i,Y_i)}{Z_i},\quad f=1000\text{ px}$$
Pitch $\theta$ is always 0 in `simulate`. Yaw $\psi$ and roll $\rho$ are passed through, but only yaw is swept.
A random sub-pixel phase $\mathbf u_i \leftarrow \mathbf u_i + U(0,1)^2$ is added, one offset per frame shared by all corners.
The 3×3 homography $H$ maps the canonical texture square $[0,128]^2$ to $4(\mathbf u_i-\mathbf{lo})$ (`cv2.getPerspectiveTransform`), and the texture is warped with `INTER_LINEAR`.
At yaw 0 the LED pitch in the image is $f p/(1000 d)=8/d$ px, i.e. 4 px at 2 m and 1.6 px at 5 m.

### 2.2 Emission: Lambertian gain and distance falloff (`optics.py`)
$$g(\psi)=\max(\cos\psi,0)^{\max(m-1,0)},\qquad m=1\Rightarrow g\equiv 1.$$
This is the gain toward the camera, applied with the yaw angle as the view angle. With $m=1$, radiance does not depend on angle, so off-axis signal loss comes only from geometric foreshortening of the projected area.
**There is no explicit $1/d^2$ term.** The value of an LED pixel does not depend on $d$, because the model treats the emitter as an extended source and radiance is conserved. Distance only shrinks the image (pitch $\propto 1/d$).
Once an LED is smaller than about a pixel, the per-pixel signal does fall, through area integration and blur. That is an effective $1/d^2$ loss for unresolved sources, but it is not coded as a formula.
The emitter is a disc with diameter $0.6p$: $\text{disc}(x,y)=\mathbb 1[(x-8)^2+(y-8)^2\le(0.6\cdot16/2)^2]$ on a 16×16 tile.

### 2.3 Supersampled warp and pixel integration (`render.py`)
The warp is computed at $SS=4$ × the output resolution. `cv2.resize(..., INTER_AREA)` then averages each 4×4 block into one pixel, which is a box-filter integration over the pixel's area with 100 % fill factor. The bounding box has a 12 px margin.

### 2.4 Blur PSF (`optics.py`)
$$h(x,y)=\frac{1}{2\pi\sigma^2}e^{-(x^2+y^2)/2\sigma^2},\qquad \sigma=\sqrt{\sigma_0^2+\sigma_{\text{extra}}^2},\;\sigma_0=0.5\text{ px}.$$
The kernel size is $2\lceil3\sigma\rceil+1$ with `BORDER_REPLICATE`, and the blur is skipped when $\sigma\le0.05$.
**σ does not depend on distance.** The code has no defocus law $\sigma(d)$ (no thin-lens circle of confusion). $\sigma_{\text{extra}}$ is a free sweep variable, swept over {0, 0.5, …, 6} px, and is 0 by default.
The blur is applied after pixel integration, so it acts as a combined lens and pixel-crosstalk PSF in output-pixel units.

### 2.5 Ambient (`ambient.py`)
Ambient is an additive constant in units of a full white LED. The default is $a=0.03$, added equally to every sensor channel after crosstalk.
The non-uniform field (used in the ambient sweep at 2.5 m, $a\in\{0,0.03,0.1,0.2,0.4,0.6\}$) uses normalised coordinates $(\tilde x,\tilde y)=(x,y)/\max(H,W)$:
$$A(\tilde x,\tilde y)=a\Big[0.4+1.2\,\frac{g-\min g}{\operatorname{ptp} g}+1.5\,e^{-\frac{(\tilde y-c_y)^2+(\tilde x-c_x)^2}{2(0.25)^2}}\Big],\quad g=\cos\phi(\tilde x-\bar x)+\sin\phi(\tilde y-\bar y),$$
with $\phi\sim U(0,2\pi)$ and a uniformly random hotspot centre.

### 2.6 Sensor (`sensor.py`)
**Crosstalk.** Each pixel signal is $\mathbf s=C\,\mathbf r + a$, where rows are the sensor R, G, B channels and columns are the LED R, G, B emissions:
$$C=\begin{pmatrix}0.85&0.10&0.05\\0.12&0.78&0.10\\0.04&0.14&0.82\end{pmatrix}$$
**Exposure.** $e=\max(\mathbf s\,\gamma,0)\,N_{fw}+e_{dark}$. The defaults are $\gamma=0.75$ (a white LED fills 75 % of the full well, before crosstalk), $N_{fw}=6000\,e^-$ and $e_{dark}=0$.
**Bayer mosaic.** The pattern is RGGB: (even, even) = R, (even, odd) and (odd, even) = G, (odd, odd) = B.
**Noise, clipping and quantisation.** The steps run in this order:
$$e' = \min(\mathrm{Poisson}(e),N_{fw}) + \mathcal N(0,\sigma_r^2),\quad \sigma_r=3e^-;\qquad DN=\operatorname{clip}(\operatorname{round}(K e'),0,255),\;K=255/N_{fw}\text{ (default)}.$$
Shot noise and dark noise are Poisson together, because dark electrons are added to the mean. Read noise can push values negative; the 8-bit clip then removes them. Full-well saturation is applied to the shot-noise term before read noise is added. There is no PRNU, DSNU/FPN, row noise, gamma or white balance.
**Demosaic.** The code calls `cv2.cvtColor(..., COLOR_BayerBG2RGB)`, which is OpenCV's bilinear demosaic. It is *not* Malvar–He–Cutler. The OpenCV naming quirk was checked with a pure-red test.
With `bayer=False`, noise is applied per channel on all three channels.

### 2.7 Low-light preset (`presets.py`)
| | Value |
|---|---|
| Photo-electrons for a full white LED | $80\,e^-/\text{ms}\times t_{exp}$, applied via $\gamma=80\,t_{exp}/4000$ |
| $N_{fw}$ | 4000 e⁻ |
| $K$ | 1.5 DN/e⁻ (saturates at about 170 e⁻) |
| $\sigma_r$ | 3 e⁻ |
| $e_{dark}$ | $20\,e^-/s\cdot t_{exp}+0.5\,e^-$ (Poisson) |
| Power | `cap`: $\kappa=\min(P/P_s,1)$ |

The code docstring says 80 e⁻/ms was **chosen so that power matters at mid range** (from a 20/40/80 scan) and is "NOT derived from a radiometric link budget". The other values carry "typical small-pixel CMOS" justifications, with no citation.
Ambient sits inside $\mathbf s$, so it scales with exposure.

### 2.8 Distance jitter and finder error (`render.py`)
Distance jitter: $d\leftarrow d\,(1+U(-0.02,0.02))$ per frame, used in all current runs. Finder error: the receiver gets the true corners plus $\mathcal N(0,0.3^2)$ px per coordinate. There is no real finder detector.

### 2.9 Encoding per scheme (`tx/schemes.py`)
All schemes reserve 4 corner pilots: TL = W, TR = R, BL = G, BR = B. That leaves 60 data LEDs.
| Scheme | Mapping | Bits/frame |
|---|---|---|
| OOK-8x8 | white on/off per data LED | $60\times1=60$ |
| CSK-$M$ | palette {K,R,G,B,Y,C,M,W} (M=8) or {K,R,G,B} (M=4), RGB on/off keying | $60\log_2M$ = 180 / 120 |
| QR/Aztec-style | 2×2 finders in 3 corners; 49 modules; Hamming(7,4) | $7\times4=28$ |
| NestedTexture-inspired | per quadrant: 11-LED ring, 16-word codebook (greedy max-min Hamming, seed 1) + inner 2×2 (all 16 words) | $4(4+4)=32$ |
| QCD-style-inspired | 12 non-pilot 2×2 cells, each a permutation of (R,G,B,K), 16 of the 24 used (`last16` after tuning) | $12\times4=48$ |
| Overlay-inspired | 12 cells, monochrome $v=0.5+a_1 s_1+a_2 \mathbf s_2$, $s_1=\pm1$ (1 bit), $\mathbf s_2\in$ 4 zero-mean ±1 patterns (2 bits); tuned $a_1=a_2=0.25$ | $12+24=36$ |
| HNCSM v1 | per quadrant: constant-weight-8 word over 15 LEDs (16-word codebook, seed 2); each lit LED ∈ {W,R,G,B} | $16+4\cdot8\cdot2=80$ |
| HNCSM base-only | v1 textures, all white | 16 |
| HNCSM v2 | QCD base; each lit LED at intensity 1 or $\alpha=0.5$ | $48+36=84$ |
| HNCSM v2-CS | QCD base; each lit primary $c$ takes one of $c$, $(1-\delta)c+\delta\,\text{next}$, $(1-\delta)c+\delta\,\text{prev}$, $(1-2\delta)c+\delta(\text{next}+\text{prev})$; $\delta=0.2$, 2 bits | $48+36b=120$ |

Power-neutrality: every v2-CS variant has channel sum 1, which `test_v2cs_leak_is_power_neutral` checks. The class docstring still describes the older non-neutral leak ("primary kept at FULL drive"); the code is the power-neutral version.

## 3. Receiver math (`rx/`)
**Rectification.** $H$ maps the canonical $64\times64$ square (8 px per LED) to the estimated corners, and the image is inverse-warped bilinearly. Each LED sample is the mean of its central 4×4 canonical-pixel window: $\mathbf y_{ij}\in[0,1]^3$ (DN/255).
**Background.** $\mathbf b=\operatorname{median}$ of the 4-px image border strip around the ROI, per channel. This works because the ROI has a 12-px margin.
**Pilot normalisation and crosstalk inversion.** $M=[\mathbf y_{R}-\mathbf b,\;\mathbf y_{G}-\mathbf b,\;\mathbf y_{B}-\mathbf b]$ (columns, taken from the TR, BL and BR pilots). The white pilot is not used for $M$.
Expected colour: $\hat{\mathbf y}(\mathbf c)=\mathbf b+M\mathbf c$.
On-metric: $x_{ij}=\max_k \operatorname{clip}\big([M^{+}(\mathbf y_{ij}-\mathbf b)]_k,-0.5,1.5\big)$, where $M^{+}$ is the pseudo-inverse.
**Decision rules:**
- **OOK, QR:** $x>0.5$. QR then does a Hamming syndrome lookup and flips a single bit.
- **CSK, HNCSM v1 enhancement:** nearest colour, $\arg\min_c\|\mathbf y-\hat{\mathbf y}(c)\|^2$.
- **Texture codebooks (NestedTexture, HNCSM v1 base):** $\arg\min_w\|\mathbf x-\mathbf w\|^2$ over the soft on-values.
- **QCD-style:** per-cell ML, $\arg\min_a\sum_{j=1}^4\|\mathbf y_j-\hat{\mathbf y}(a_j)\|^2$.
- **v2 and v2-CS (joint ML):** $\arg\min_a\sum_j\min_{v\in V(a_j)}\|\mathbf y_j-\mathbf b-M v\|^2$. Enhancement bits are the minimising variant of each lit LED.
- **Overlay:** luminance is $w=\sum_k(\mathbf y-\mathbf b)_k/\sum_{jk}M_{kj}$. Then $s_1=\mathbb 1[\bar w>0.5]$ and $\mathbf s_2=\arg\max P_2(\mathbf w-\bar w)$.

All decisions are hard. Squared Euclidean distance is ML only under i.i.d. Gaussian noise, which is an approximation here because the noise is Poisson and demosaic-correlated.

## 4. Metrics (`experiments/common.py`, `efficiency.py`)
The test set uses 1000 frames per point. Common random numbers: every scheme sees the same payload and channel seeds, with seed $=(\text{SEED}+\text{crc32}(\cdot)+7919i)\bmod(2^{31}-1)$.
- Per layer $\ell$ with $n_\ell$ bits: $\text{BER}_\ell=\frac{\#\text{bit errors}}{n_\ell F}$ and $\text{FER}_\ell=\frac{k_\ell}{F}$, where $k_\ell$ is the number of frames with at least one error.
- Net goodput: $G=\sum_\ell \max(n_\ell-8,0)\cdot30\cdot(1-\text{FER}_\ell)$ bps. This charges a CRC-8 per layer and assumes perfect error detection.
- Wilson interval ($z=1.96$), with $\hat p=k/n$:
$$\frac{\hat p+\frac{z^2}{2n}}{1+\frac{z^2}{n}}\pm\frac{z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}.$$
  $G_{lo}$ uses $\text{FER}_{hi}$ and $G_{hi}$ uses $\text{FER}_{lo}$. These are summed across layers, which is conservative and not a joint interval.
- Equal-power scaling: $P_s=\mathbb E[\sum D]$ over 2000 random payloads, pilots included, and $\kappa_s=P_{ref}/P_s$. Under `--cap`, $\kappa_s=\min(\cdot,1)$. In `peak` mode, $\kappa=1$.
- Degradation curve over $d\in[0.5,5]$ m (0.25 m steps):
  - Peak: $G^*$.
  - $\text{AUC}=\int G\,dd$ (trapezoid), and $\text{auc\_norm}=\text{AUC}/(G^*\cdot4.5)$.
  - $d_{x}$: the first downward crossing of $x\cdot G^*$ after the peak, with linear interpolation. It is ∞ if the curve never crosses and NaN for edge cases.
  - Cliff ratio: $\max_{i\ge i^*}(G_i-G_{i+1})/(G^*-G(5\,\text{m}))$.
  - CIs for AUC, $d_{50}$ and $d_{10}$ come from the curves built from $G_{lo}$ and $G_{hi}$.
- Efficiency: $\eta=G/P_{achieved}$. Energy per bit: $E_b=P/G$ in power-units·s/bit, which are arbitrary drive units, not joules.
- Adaptive-CSK genie: choose $\arg\max G$ over {OOK, CSK-4, CSK-8} on 300 separate-seed frames, then report that scheme's result on the evaluation seeds.

## 5. Validation: what was actually checked
- **Unit tests:** re-run 31 Oct 2026, 61 legacy + 9 physical = 70 passed (see §8.4). They cover:
  - Bayer/demosaic channel mapping (pure R/G/B).
  - Gaussian kernel normalisation, and spread ≈ σ.
  - Noise statistics: mean $=K\gamma N_{fw}r$ and std $=K\sqrt{e+\sigma_r^2}$ with $+1/12$ quantisation, within 5 %. The same checks are repeated for the low-light preset.
  - Projection side $=f s/d$ and an affine homography at 0°.
  - Yaw foreshortening below 0.6×.
  - Jitter range.
  - Seed determinism.
  - Wilson numeric values.
  - CRN reproducibility, equal-power scaling, CRC charge and the overdrive cap.
  - Ideal and close-range round trips for every scheme.
  - Hierarchy behaviour.
  - v2-CS power neutrality.
  These tests check **internal consistency**: that the code implements its own formulas. They do not check physical fidelity.
- **Sanity checks:**
  - A byte-identical reproduction of the P33 sweep.
  - The "dip" probe, which traced the 2.00 m spike to Bayer-phase aliasing at an integer pitch of 4 px.
  - The low-light calibration scan.
- **The audit (commit 2140cd8):** fixes to the *evaluation protocol*: equal power, CRN, CRC charge, Wilson CIs, held-out tuning seeds, and crc32 seeds. It did not validate the physics.
- **Literature:** **no parameter was taken from, or checked against, a published dataset, datasheet or measurement.**
  - Assumed or chosen without a source: $f=1000$ px, 8 mm pitch, 0.6 fill, $\sigma_0=0.5$ px, the crosstalk matrix, $N_{fw}$ = 6000/4000, $\sigma_r=3e^-$, $\gamma=0.75$, ambient 0.03, the 80 e⁻/ms low-light value (explicitly "calibrated so that power matters"), the dark current, 2 % jitter, 0.3 px corner jitter and the ambient-field shape.
  - The baseline schemes (Salvi & Geetha 2022, Vasantha & Salvi 2022, Nishimoto 2012) were rebuilt **from abstracts only**.
  - The tuned values (δ, subset, $a_1$, $a_2$) were fitted in simulation.

## 6. References
**Used in calibration: none.** The two items below are cited in the code or README only as the source of a scheme *idea*, not of any parameter value:
- Nishimoto et al., "High-speed transmission of overlay coding for road-to-vehicle visible light communication using LED array and high-speed camera," IEEE GLOBECOM Workshops 2012. doi:10.1109/GLOCOMW.2012.6477757
- Salvi & Geetha (IEEE Access 2022) and Vasantha & Salvi (Appl. Sci. 2022) are named, but no DOI appears in the repo, and I did not verify these two.

**Supports the modelling choices (all DOIs checked to resolve via doi.org and Crossref, 31 Oct 2026):**
1. T. Komine, M. Nakagawa, "Fundamental analysis for visible-light communication system using LED lights," IEEE Trans. Consum. Electron. 50(1), 2004. doi:10.1109/TCE.2004.1277847. Generalised-Lambertian LED model, $\cos^m$.
2. J. M. Kahn, J. R. Barry, "Wireless infrared communications," Proc. IEEE 85(2), 1997. doi:10.1109/5.554222. Lambertian order and the $1/d^2$ LOS gain for point sources.
3. C. Danakis, M. Afgani, G. Povey, I. Underwood, H. Haas, "Using a CMOS camera sensor for visible light communication," IEEE GLOBECOM Workshops 2012. doi:10.1109/GLOCOMW.2012.6477759. CMOS camera OCC and rolling shutter (*not* modelled here).
4. N. T. Le, M. A. Hossain, Y. M. Jang, "A survey of design and implementation for optical camera communication," Signal Process. Image Commun. 53, 2017. doi:10.1016/j.image.2017.02.001.
5. N. Saeed, S. Guo, K.-H. Park, T. Y. Al-Naffouri, M.-S. Alouini, "Optical camera communications: Survey, use cases, challenges, and future trends," Physical Communication 37, 2019. doi:10.1016/j.phycom.2019.100900.
6. IEEE Std 802.15.7-2018, "Short-Range Optical Wireless Communications." doi:10.1109/IEEESTD.2019.8697198. Defines OCC PHYs and CIE-xy CSK; the repo's "CSK" is digital RGB keying, not this.
7. A. Foi, M. Trimeche, V. Katkovnik, K. Egiazarian, "Practical Poissonian-Gaussian noise modeling and fitting for single-image raw-data," IEEE TIP 17(10), 2008. doi:10.1109/TIP.2008.2001399. Poisson + Gaussian raw noise with clipping.
8. G. E. Healey, R. Kondepudy, "Radiometric CCD camera calibration and noise estimation," IEEE TPAMI 16(3), 1994. doi:10.1109/34.276126. Shot, read and dark noise, and gain.
9. H. S. Malvar, L.-W. He, R. Cutler, "High-quality linear interpolation for demosaicing of Bayer-patterned color images," IEEE ICASSP 2004. doi:10.1109/ICASSP.2004.1326587. A demosaicing reference; the code uses *bilinear*, not this method.
10. R. Hartley, A. Zisserman, *Multiple View Geometry in Computer Vision*, 2nd ed., CUP 2004. doi:10.1017/CBO9780511811685. Pinhole projection and homography.
11. E. B. Wilson, "Probable inference, the law of succession, and statistical inference," JASA 22(158), 1927. doi:10.1080/01621459.1927.10502953.

Also relevant, though I did not fetch the DOI: EMVA Standard 1288 (camera characterisation: linear model, $\sigma_y^2=K^2\sigma_d^2+K(\mu_y-\mu_{y.dark})+\sigma_q^2$). The sensor model has the same structure, but its parameters were not measured to EMVA 1288.

## 7. Gaps against the literature
- No rolling shutter or temporal effects, which are central to most CMOS OCC work (Danakis 2012, Le 2017). Static frame, global-shutter-like capture.
- No radiometric link budget. There is no $1/d^2$ law or point-source irradiance, the Lambertian order is fixed at $m=1$ (where real LEDs often have $m>1$), and signal levels are given in "white-LED = 75 % full well" units.
- The PSF is a fixed Gaussian with no defocus model $\sigma(d)$, no diffraction and no lens aberrations. The README itself says it is not calibrated to a lens.
- The crosstalk matrix is invented rather than taken from measured LED spectra × CFA QE curves.
- The demosaic is bilinear (not Malvar, nor a vendor ISP). There is no gamma, AWB, denoise, sharpening or JPEG, even though real phone pipelines apply all of these.
- Missing noise terms: PRNU, DSNU, row/column noise and temperature dependence. The dark current only exists in the low-light preset.
- CSK is not the 802.15.7 CIE-xy CSK.
- Finder detection is idealised (true corners + 0.3 px). Decisions are hard, with no soft FEC, and the CRC is idealised.
- The three comparison schemes are re-implemented from abstracts, so their parameters are assumptions.

---

# 8. PHYSICAL channel (added 31 Oct 2026; legacy channel above is unchanged)
Code: `channel/physical.py`, `experiments/phys_eval.py`, `experiments/run_phys.py`, `experiments/validate_qcd.py`,
`experiments/plots_phys.py`; tuning `python -m experiments.tune --channel physical`. Run everything with `./run_phys_all.sh`.

## 8.1 Model, per Tx symbol
1. **LED radiometry.** For each WS2812B die j, the on-axis photon intensity is $I_{e,j}=I_{v,j}/(683\,V(\lambda_j))$ [W/sr], divided by $hc/\lambda_j$ to get photons. The result is multiplied by the global `brightness`.
2. **LOS link (Komine & Nakagawa 2004; Kahn & Barry 1997).** $P_r=P_t\frac{(m+1)A}{2\pi d^2}\cos^m\phi\cos\psi$, with $A=\pi(f/2N)^2$ (the entrance pupil) and $\times t_{exp}$.
   - Received photons are spread over the LED's projected disc (fill 0.6 × pitch, foreshortened by $\cos$ yaw) to give photons per pixel.
   - For a resolved LED, $1/d^2$ cancels against the footprint area (radiance invariance). Distance then acts through PSF and pixel sampling, and the LED becomes a sub-pixel source at ≳3 m.
3. **PSF.**
   - Thin-lens blur circle $c=f^2|d-d_f|/(N d (d_f-f))$ (Pentland 1987), giving $\sigma_{def}=c/4$.
   - Airy $\sigma=0.42\lambda N$ (Zhang, Zerubia & Olivo-Marin 2007).
   - These combine in quadrature, plus the optional sweep `blur_sigma_px`.
4. **Spectral path.** LED j → sensor channel k uses `cfa[k,j] × QE_j` (QE from the IMX174 EMVA sheet at 630/534/466 nm). Ambient uses the camera equation $E_{img}=E\rho/(4N^2)$.
5. **Rolling shutter + asynchrony.**
   - Row r integrates $[t_s+(r_0+r)t_{row},\,+t_{exp}]$. Each row is the overlap-weighted mix of the previous, current and next Tx symbol.
   - The camera phase is uniform-random per symbol.
   - Frames whose ROI mid-exposure falls inside the symbol are candidates. The receiver keeps the one with minimum re-encoding residual. If no frame is usable, the symbol's bits are random.
6. **EMVA 1288 sensor on RGGB.** PRNU gain → +dark → Poisson → clip at full well → +DSNU + read noise → ×K, round, 8-bit → Malvar-He-Cutler 5×5 demosaic.
7. **Real finder (`detect_corners`).**
   - Background-subtracted, per-channel normalised image; threshold 15 %; blob filter.
   - Coarse panel from the minimum-area rectangle of the lit pixels.
   - 3 iterations of LED-centroid refinement with a least-squares homography.
   - Validated: median corner error 0.02–0.08 pitch at 0.5–2 m, and 0.38 pitch at ≥3 m, where the LEDs are about 1 px.
8. **CSK baselines = IEEE 802.15.7 CIE-xy CSK (`CSK802`).**
   - The 802.15.7 design-rule 4/8-CSK points (TG7 example triangle I,J,K) are mapped by barycentric coordinates onto the WS2812B triangle (I→R, J→G, K→B).
   - Drives satisfy $a_j\propto w_j y_j/I_{v,j}$, with $\sum a_j=1$ (constant total drive).
   - Decoding is ML in sensor space against pilot-referenced templates.
9. **Protocol.**
   - Tx symbol rate $f_{tx}=15$ /s (fps/2).
   - Goodput = net bits × $f_{tx}$ × (1−FER).
   - Everything else as before: equal average drive power, CRN, CRC-8 per layer, Wilson 95 % CIs, fixed seeds, 1000 symbols per point.
   - Genie: 300 separate-seed symbols over {OOK, 4-CSK, 8-CSK}.
   - Tuning: re-done on held-out `TUNE_SEED` → `results/tuned_params_phys.json` (v2-CS δ=0.3, bpl 2; QCD subset maxdist-0; overlay a1 0.35 / a2 0.15).

## 8.2 Parameter table
| Parameter | Value | Source |
|---|---|---|
| Panel size / layout | 65 mm, 8×8 | QCD-OCC Table 2, doi:10.3390/app122010204 |
| fps, exposure | 30 fps, 1/1500 s | QCD-OCC Table 2 |
| Ambient levels | 27/149/304 lux | QCD-OCC Table 2 |
| LED dominant λ | 622.5/523.5/466 nm | WS2812B datasheet (Worldsemi; no DOI) |
| LED luminous intensity | 405/690/190 mcd | WS2812B datasheet (no DOI) |
| V(λ), chromaticity xy | 0.3568/0.7778/0.0770; (0.6954,0.3045),(0.1060,0.8292),(0.1335,0.0427) | CIE 015:2018, doi:10.25039/TR.015.2018 (narrow-band treatment ASSUMED) |
| QE | 0.492/0.671/0.709 | IMX174 EMVA 1288 sheet, doi:10.5281/zenodo.33041 |
| Read noise, full well, dark current | 4.41 e⁻, 7863 e⁻, 5.6 e⁻/s | zenodo.33041 |
| DSNU, PRNU, K | 0.81 e⁻, 0.47 %, 0.501 DN/e⁻ (12 bit) | zenodo.33041 |
| Pixel pitch, rows | 5.86 µm, 1216 | zenodo.33041 |
| LOS formula | — | Komine 2004, doi:10.1109/TCE.2004.1277847; Kahn & Barry 1997, doi:10.1109/5.554222 |
| Defocus formula | — | Pentland 1987, doi:10.1109/TPAMI.1987.4767940 |
| Airy-Gaussian σ | 0.42 λN | Zhang et al. 2007, doi:10.1364/AO.46.001819 |
| Demosaic | Malvar 5×5 | doi:10.1109/ICASSP.2004.1326587 |
| Rolling shutter | row-sequential exposure | Danakis 2012, doi:10.1109/GLOCOMW.2012.6477759 |
| CSK constellation | 802.15.7 design rule | IEEE Std 802.15.7-2018, doi:10.1109/IEEESTD.2019.8697198 (points from the TG7 contribution) |
| Lambertian order m | 1 | **ASSUMED** |
| LED brightness factor | 1/128 (low-light preset 1/1024) | **ASSUMED**: full drive would saturate ~100× at 1/1500 s |
| Lens f, N, focus | 6 mm, f/2.0, 1.0 m | **ASSUMED** |
| ADC bits | 8 (K/16) | **ASSUMED** |
| CFA crosstalk matrix | legacy 3×3 | **ASSUMED**: IMX174 sheet is for the mono sensor |
| Row time t_row | 1/(30·1216) s | **ASSUMED**: IMX174 is global shutter (inconsistency) |
| f_tx | 15 /s | **ASSUMED** protocol |
| Background reflectance | 0.5 | **ASSUMED** |
| Ambient spectrum | 555 nm-equivalent, equal split over bands | **ASSUMED** |
| Distance jitter | ±2 % | **ASSUMED** (legacy) |
| Frame-to-symbol association | by timestamp | **ASSUMED** (sequence numbers as in Nguyen 2021, doi:10.3390/s21093023) |
| Finder thresholds | 15 %, blob ≥10 % | **ASSUMED** |
| Equal-power budgets, CRC-8, tuned scheme parameters | — | Protocol / simulation-tuned |

## 8.3 Validation
- **QCD-OCC** (`results/validation_qcd.csv`, `phys_validation_qcd.png/pdf`).
  - Setup: the paper's frame (48 data LEDs × 3 bit RGB on/off, corner anchors) on the physical channel, with **no parameter change**.
  - Result at 200 cm, 3600 bps, 27 lux: BER 6.0e-3 (95 % CI 5.4–6.7e-3), against the published 1.13e-2.
  - This is the same order, but a factor of ~1.9 lower, and the CI excludes the published value.
  - BER is 0 (CI upper 6.7e-5) at 50–150 cm.
  - At full WS2812B brightness the model saturates and BER is ≈0.39. This differs from the real prototype (C310 webcam, unknown gain/optics), so `brightness` is effectively an unidentified parameter. It was set by a saturation argument, **not** fitted to the 1.13e-2.
- **Second published point (Nguyen et al. 2021, BER 1e-4 at 20 m): infeasible.**
  - The paper gives neither the lens focal length nor the LED luminance.
  - Its 8×8 cm panel at 20 m is ≈0.4 px per LED with our assumed 6 mm lens.
  - Any reproduction would require choosing the very parameters that decide the answer.

## 8.4 Tests
`tests/test_physical.py` (9 tests):
- Komine formula and inverse-square law.
- Airy floor and PSF growth with defocus.
- Malvar preserving a constant image.
- Sensor capture.
- Row weights summing to 1.
- CSK802 points: constant drive, distinct.
- Detector accuracy < 0.25 pitch at 1 m.
- Close-range physical round trip with zero errors.
- Physical line-up.
