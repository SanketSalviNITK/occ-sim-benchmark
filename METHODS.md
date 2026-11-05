> **benchmark-r0:** this document describes the simulator; the benchmark protocol (fairness, binding margins, oracle corners, seed replication, power normalisation) is in `docs/BENCHMARK_PROTOCOL.md`, IMX219 parameters in `docs/IMX219_PARAMETERS.md`. Attribution of the v2 gain is worded as **"power/level allocation under equal-summed drive + decoder"**.

## Claims (C2: benchmark-r7; IMX219: benchmark-r5; supersedes §9.0 C1/C2)
> **Claims status r7:** the C2 (IMX174) wording below was rewritten in benchmark-r7 (validator audit of r6, §3 wording): optics, geometry and Holm qualifiers added, stale oracle statements removed; sources and change log `results/benchmark/CLAIMS_r7.md`.
> **Claims status r3→r5:** the benchmark-r2 claims were unchanged through benchmark-r3 and benchmark-r4 (only metas, manifest and wording tidy-ups). In **benchmark-r5** the C2 numbers were re-stated on one canonical seed set (claims/E2) and the oracle-corner numbers were re-sourced (`oracle_pairs.csv`); the qualitative claims are unchanged. Old→new numbers: `results/benchmark/CLAIMS_r5.md`.
**C2 (IMX174), safe wording (benchmark-r7; replaces the r5 wording; canonical seed set = claims/E2, protocol item 9; CIs B = 10000, bootstrap seed 0; sources: `results/benchmark/CLAIMS_r7.md`, `results/benchmark/r6/*.csv`):** (Interaction note added in r7: a 36-cell optics × brightness factorial was run afterwards, see `results/benchmark/CLAIMS_r7.md` §Sensitivity and `results/benchmark/r7/factorial_binding.csv`; the quoted sentence "interactions were not studied" refers to the one-at-a-time study.)
> "At the fixed operating point (IMX174, P33, brightness 1/128, exposure 1/1500), with the ASSUMED default optics (f = 6 mm, f/2.0, focus 1.0 m), the 65 mm 8×8 panel on axis, and the benchmark's shared corner finder, the binding margin of v2 over every comparison scheme × {native, 48-bit} on the canonical claims/E2 seeds is +150.0 [126.6, 173.4] bps at 3.0 m (vs QCD-style-inspired, native) and +107.6 [86.3, 129.0] bps at 3.25 m (vs Overlay-inspired, 48-bit); across all four seed sets the minimum is +148.2 (3.0 m) and +107.6 (3.25 m), all Holm-significant (56-claim family). At 3.5 m it is not claimed (canonical +4.3 [−10.1, 19.1]; P25/P42 positive unadjusted but n.s. after Holm). The advantage is conditional: it disappears under one-at-a-time changes of the ASSUMED lens (f = 4 or 8 mm, f/2.8, focus 0.5 or 2.0 m), CFA crosstalk ×2, brightness 1/256 (at P25/P33), per-scheme tuned exposure, an 80 mm panel (where OOK binds at 3.0/3.25 m), and at 3.25 m under 30° yaw; interactions were not studied. With oracle corners on the same seeds v2 is third at 3.0 m (−114.1 [−141.9, −86.6] vs OOK-8x8) and second at 3.25 m (−24.0 [−45.0, −3.6] vs QCD-style, unadjusted), while at 3.5 m it leads (+46.1 [23.9, 68.2] vs Overlay, 48-bit): the 3.0–3.25 m advantage therefore comes from how reliably the shared finder locates v2 frames (gross-error rate 7 %/17 % vs 57–71 % for QCD-style), not from demodulation."

**C1/C2 on IMX219, safe wording (benchmark-r5; sources: `results/benchmark/CLAIMS_r5.md`):**
> "C1 here means the audit-2 claim that at 2.5 m (1/1500 s, brightness 1/128) v2 exceeds the IEEE 802.15.7 CSK baselines; C2 means the IMX174 binding-margin claim at 3.0–3.5 m above. On the IMX219 preset `imx219f` (sourced geometry and noise, uncalibrated photometric scale), neither transfers. At the same distances (2.5, 3.0, 3.25 and 3.5 m), v2 is significantly below the binding baseline at every point, with fixed or tuned exposure and with the scale-free finder or oracle corners. Examples: 2.5 m, −1273.6 [−1322.6, −1222.0] bps vs genie(CSK802-8); 3.0 m, −999.6 [−1009.9, −985.3] bps vs QCD-OCC (paper frame), and −991.4 [−1005.7, −977.2] with oracle corners. At matched pixels-per-LED v2 is significantly below at 2.5–3.25 m with both finders (e.g. matched 3.0 m: −57.0 [−75.6, −38.4] vs QCD-style-inspired). At matched 3.5 m the result is not significant (+13.2 [−11.4, 36.0] with the scale-free finder; +0.6 [−23.4, 24.6] with oracle corners at fixed exposure). The one exception is oracle corners with tuned exposure (+23.4 [1.2, 45.6], unadjusted; n.s. after Holm, p_holm 0.33, r6 `holm_claims.csv`). These are simulation results on an uncalibrated preset and say nothing about real IMX219 hardware."

IMX219 scope: all IMX219 results use the current preset (`imx219f`), photometrically uncalibrated (sourced geometry and noise). Matching the measured CQ sensitivity would need an effective QE of 1.5–2.16 (impossible as QE); those ×3-QE runs are not shipped. The published QCD-OCC BER is matched by this preset near Tx brightness 1/2048, not the 1/128 used in E3.

**Ablation (R3/N4):** lit0.75 recovers 75.6 / 42.6 / 33.8 % and lit0.75 + 2-level decoder 88.6 / 72.7 / 82.4 % of the v2 − base-only gap (3.0 / 3.25 / 3.5 m). A significant residual of +35.4 [13.2, 58.2] bps remains at 3.25 m; the decoder gain is larger on the 0.75-level Tx (interaction), so the shares are not additive. Radiant-equal power: same within 1.2 bps (scales equal to 3e-4).

Not claimed: that v2's modulation outperforms at 3.0 m; any robust or unqualified C2; that C1/C2 fail on real or calibrated IMX219 hardware.


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
| QCD-style-inspired | 12 non-pilot 2×2 cells, each a permutation of (R,G,B,K), 16 of the 24 used (`last16` after ideal-channel tuning; physical channel/benchmark: `maxdist-0`, §8.1) | $12\times4=48$ |
| Overlay-inspired | 12 cells, monochrome $v=0.5+a_1 s_1+a_2 \mathbf s_2$, $s_1=\pm1$ (1 bit), $\mathbf s_2\in$ 4 zero-mean ±1 patterns (2 bits); tuned $a_1=a_2=0.25$ | $12+24=36$ |
| HNCSM v1 | per quadrant: constant-weight-8 word over 15 LEDs (16-word codebook, seed 2); each lit LED ∈ {W,R,G,B} | $16+4\cdot8\cdot2=80$ |
| HNCSM base-only | v1 textures, all white | 16 |
| HNCSM v2 | QCD base; each lit LED at intensity 1 or $\alpha=0.5$ | $48+36=84$ |
| HNCSM v2-CS | QCD base; each lit primary $c$ takes one of $c$, $(1-\delta)c+\delta\,\text{next}$, $(1-\delta)c+\delta\,\text{prev}$, $(1-2\delta)c+\delta(\text{next}+\text{prev})$; $\delta=0.2$, 2 bits (ideal channel; physical channel/benchmark: $\delta=0.3$, §8.1) | $48+36b=120$ |

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
   - Tuning: re-done on held-out `TUNE_SEED` → `results/tuned_params_phys.json` (v2-CS δ=0.3, bpl 2; QCD subset maxdist-0; overlay a1 0.35 / a2 0.15). These are the values every physical-channel benchmark run uses (`all_schemes_phys()` loads `tuned_params_phys.json`); `results/tuned_params.json` (δ=0.2, last16, (0.25, 0.25)) applies only to the ideal-channel `all_schemes()`.

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
  - Result at 200 cm, 3600 bps, 27 lux: BER 6.0e-3 (per-bit CI 5.4–6.7e-3; symbol-cluster CI 4.51–7.52e-3, §9.2), against the published 1.13e-2.
  - This is the same order, but a factor of ~1.9 lower, and the CI excludes the published value.
  - BER is 0 (CI upper 6.7e-5) at 50–150 cm.
  - At full WS2812B brightness the model saturates and BER is ≈0.39. This differs from the real prototype (C310 webcam, unknown gain/optics), so `brightness` is effectively an unidentified parameter. The default 1/128 is **ASSUMED** (not fitted to the 1.13e-2); the bracket 1/128–1/256 around the published value is given in §9.2.
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

# 9. internal reproducibility audit 1 fixes (31 Oct 2026)
Driver `experiments/audit_r1.py`, analysis `experiments/audit_r1_report.py`, statistics `experiments/stats.py`
(tests `tests/test_stats.py`). Per-symbol bit-error matrices: `results/phys_sym/*.npz`; tables: `results/audit_r1/*.csv`.

## 9.0 [SUPERSEDED] Claims (internal reproducibility audit 2, audit-r2) — historical only
> **SUPERSEDED by "Claims (benchmark-r2)" at the top of this file. C1 and C2 below are historical, not current claims.**

Audit-2 text: only the two statements below were claimed. All numbers come from `results/audit_r1/claims_paired.csv` (C1, C2
reversals) and `results/audit_r1/efficiency_winners_paired.csv` (C2), per-symbol data `results/phys_sym/{claims,sweeps_PHYS_P25,sweeps_PHYS_P33,sweeps_PHYS_P42}.npz`;
differences are paired CRN symbol-bootstrap 95 % CIs (METHODS §9.1). Physical channel, equal summed drive, P33 unless stated.
Former claim 3 (low-light v1 advantage) is **dropped** (METHODS §9.4). Nothing in `results/legacy/` is used.
(The submission's C1/C2 wording was not stored in the repo; the text below is restated from the audit-2 report and the CSVs.)

**C1 (historical, superseded by the benchmark wording).** At t_exp = 1/1500 s, LED brightness 1/128 and 2.5 m, HNCSM v2 delivers 592 bps [586, 596] against
25 bps [13, 39] for IEEE 802.15.7 4-CSK (paired diff +566 [552, 579]; 8-CSK 0 bps). The comparison is against the IEEE
802.15.7 CSK baselines only: at the same point OOK is higher (v2 − OOK −147 [−159, −135]); at 70° yaw (1 m) v2 ties
QCD-style (0 [−17, 18]); at 4 px blur (1 m) QCD-style wins (HNCSM v1 119 vs 395 bps, −276 [−293, −258]). C1 does not hold
under per-scheme tuned exposure (CSK802-4 at 1/250 s: 648 bps, v2 − CSK802-4 −57 [−109, −5]); with 48-bit-CRC baselines at
fixed 1/1500 s it holds against 4-CSK (+335 [313, 355]) and OOK still wins (−34 [−45, −24]).

**[SUPERSEDED by the benchmark-r2 claims at the top of this file — kept for history, NOT a current claim]** **C2 (conditional, audit 2).** v2 has the highest goodput at 3.0–3.5 m at budgets P25/P33/P42 (paired CIs exclude 0; absolute
128–418 bps) under t_exp 1/1500 s, LED brightness 1/128 and equal summed drive. Repo numbers, v2 − runner-up
(`efficiency_winners_paired.csv`, runner-up named):

| Budget | 3.0 m | 3.25 m | 3.5 m |
|---|---|---|---|
| P25 | 417.6 bps; +141.0 [118.8, 163.2] (QCD-style) | 247.8; +114.6 [94.8, 134.1] (QR) | 130.8; +21.4 [7.3, 37.2] (v1-base) |
| P33 | 412.8; +148.2 [126.6, 171.6] (QCD-style) | 242.4; +126.1 [107.3, 144.8] (v1-base) | 133.2; +28.6 [13.9, 45.0] (v1-base) |
| P42 | 412.8; +157.8 [136.2, 180.6] (QCD-style) | 234.0; +117.7 [99.5, 134.6] (v1-base) | 128.4; +29.8 [15.0, 46.1] (v1-base) |

It also holds for radiant-equal power (`radiant_equal.csv`, 1/1500 s, 1/128: 3.0 m v2 397 [371, 422] vs QCD-style 242
[216, 269]; 3.5 m v2 134 [112, 156] vs v1-base 101 [97, 105]; no paired diffs, no 3.25 m point) and for 48-bit-CRC
baselines. The 48-bit-CRC check for C2 was not computed by the repo; an internal audit computation
(audit-2 report, NB2) re-segments only the **non-HNCSM baselines** into 48-bit CRC-8 blocks (the HNCSM family — v1-base,
v1, v2-CS — is excluded from that opponent set) and gives, at P33, v2 − best 48-bit baseline +148 [125, 171] vs
QCD-style / +116 [94, 138] vs Overlay / +61 [43, 80] vs Overlay at 3.0 / 3.25 / 3.5 m (all 9 budget × distance points
separated). The binding margin at 3.5 m is **not** +61 but the native margin over v1-base, +21 to +30 across
P25/P33/P42 (+28.6 [13.9, 45.0] at P33, table above), to which the 48-bit variant does not apply. It **reverses** at 3.0 m against QCD-style under
per-scheme tuned exposure (v2 425 vs 494 bps, −69 [−89, −48]) and at brightness 1/256 (−70 [−89, −49]); at 1/256 with
tuned exposure it is a tie (−22 [−44, 1]) (`claims_paired.csv`, cond d3.0). [r7 correction: this audit-2 sentence is superseded — 3.25 m was perturbed in r6
(E2 grid and the r6 one-at-a-time sensitivity study, `results/benchmark/r6/sensitivity_tornado.csv`; 3.5 m only in the E2 grid); see the C2 wording above.]

**Limitations of the claims (audit 2).** (i) There is no second validation anchor: the channel is calibrated to the
QCD-OCC 200 cm point only, to order of magnitude, through one unidentified brightness constant (METHODS §9.2).
(ii) Tuning (v2-CS, QCD-style, overlay, per-scheme exposure and the genie) used held-out seeds but the **same
distances/geometry** as the evaluation; there was no tuning on disjoint distances. (iii) In
`efficiency_winners_paired.csv`, where the winner is OOK or a CSK802 scheme, the "runner-up" is the genie, which
duplicates the winner (diff 0, `separated=False`); those rows say nothing about separation. The C2 rows have real
runner-ups. (iv) The radiant-equal run (`radiant_equal.csv`) has no paired differences and no 3.25 m point, and was run
only at 1/1500 s and brightness 1/128. (v) The 48-bit-CRC baseline variant reuses the native-CRC tuning picks
(exposure, genie); it was not re-tuned.

## 9.1 Statistics (B5)
- BER: symbol(frame)-cluster bootstrap (2000 resamples of symbols), not per-bit Wilson.
- Goodput per point: symbol bootstrap. Every A − B: **paired CRN bootstrap** (same symbol indices for both schemes).
- AUC differences: symbols resampled independently per distance (independent seeds), jointly for A and B; trapezoid AUC per replicate.
- Winners `separated` flag = paired CI of (winner − runner-up) excludes 0 (`efficiency_winners_paired.csv`). The old
  Wilson-envelope AUC "CIs" are superseded. (The genie-vs-CSK802-4 `auc_hi` mismatch, 469.6 vs 458.0 at LL P15, was an
  envelope artefact: beyond 1.75 m the genie picks CSK802-8 at 0 bps, whose 0/1000 Wilson upper bound is 9.87 bps vs 6.43.)

## 9.2 Brightness is an unidentified nuisance parameter; validation = order-of-magnitude calibration only (B3)
QCD-OCC paper frame, 2 m, 27 lux, 3600 bps, 400 symbols, validate_qcd.py seeds (`validation_bracket.csv`):

| brightness | BER | 95 % symbol-cluster CI | errored symbols |
|---|---|---|---|
| 1/64 | 3.96e-3 | [3.19e-3, 4.81e-3] | 123/400 |
| 1/128 (default) | 6.01e-3 | [4.51e-3, 7.52e-3] | 90/400 |
| 1/256 | 1.42e-2 | [1.20e-2, 1.66e-2] | 176/400 |

The published 1.13e-2 lies between 1/128 and 1/256: one unidentified constant brackets the target. There is no second
independent anchor, so the channel is **calibrated to order of magnitude only**.

Peak own-channel electrons per fully covered pixel at full drive, 1/1500 s (`electrons_per_channel.csv`; radiance-invariant
beyond focus), against µe,sat = 7863 e⁻:

| brightness | R | G | B | clips | 8-bit DN (R/G/B) |
|---|---|---|---|---|---|
| 1/64 | 8195 | 6741 | 18541 | R, B | 246/211/246 |
| 1/128 | 4098 | 3371 | **9270** | **B** | 128/106/246 |
| 1/256 | 2049 | 1685 | 4635 | – | 64/53/145 |
| 1/1024 | 512 | 421 | 1159 | – | 16/13/36 |

**Disclosure:** at the default 1/128 the blue LED clips at full drive. v2 runs unscaled (P33 = v2's own mean power) and
clips; CSK runs at scale 0.5 and does not. The old "full drive would saturate" rationale does not describe the operating
point. 1/256 (no clipping) is reported as a sensitivity case for every claim (§9.3). K8 = 0.0313 DN/e⁻ (1 DN ≈ 32 e⁻).
EMVA 1288 values come from the **mono** IMX174 sheet at 250 µs exposure; the CFA (colour filter array) is ASSUMED.

## 9.3 Evidence vs the best baseline, paired CIs, exposure (B1, B4; claims are stated in §9.0)
Conditions 2.5 m, 3.0 m, 70° yaw (1 m), 4 px blur (1 m) × t_exp {1/4000, 1/1500, 1/500, 1/250} × brightness
{1/128, 1/256}; 1000 eval symbols; per-scheme exposure and the genie chosen on 200 held-out symbols (TUNE_SEED); seeds
shared across exposures (CRN), so tuned comparisons are paired. Full table: `claims_paired.csv`, points incl. BER,
48-bit-CRC baseline goodput, saturation ratio and RS-mixing weight: `claims_points.csv`.
**C1/C2 are conditional on t_exp = 1/1500 s (§9.0)**: e.g. at 2.5 m CSK802-4 goes 25 → 648 bps from 1/1500 to
1/250 s while v2 goes 592 → 263.
Mechanism diagnostic (1/128, 2.5 m): RS mixing weight of the selected frame (`claims_points.csv`, `rs_mix`, verified in audit 2) is ≤ 0.009 for v2,
CSK802-4 and OOK at every exposure (max 0.0085, v2 at 1/250 s), so the rolling shutter does not drive the asymmetry.
Over all 12 schemes at this condition the max is 0.015, and over all claim conditions 0.033 (OOK, 4 px blur, 1/250 s);
the earlier "≤ 0.01 for all schemes" was not correct as stated. Saturation fraction (share of lit pixels, i.e. pixels above 15 % of panel peak, whose mean e⁻ ≥ full well; numerator
restricted to lit pixels in audit 2, F4) for v2 / CSK802-4 / OOK: 0.006 / 0 / 0 at 1/1500 s, 0.43 / 0.13 / 0.14 at 1/500 s,
0.94 / 0.42 / 0.50 at 1/250 s (0 at 1/4000). After the fix every `sat_ratio` in `claims_points.csv` lies in [0, 1] (max
1.0, v2 at 70° yaw, 1/250 s, previously 1.08 — the only value that changed). Goodput, BER and RS-mixing outputs are
bit-identical to audit 1 (`claims.npz`: 1536 err/mix arrays identical; only the v2 yaw70 1/250 1/128 sat
arrays (eval and tune) changed). Longer exposure buys CSK SNR: CSK802-4 BER is 0.072 at 1/1500 s and 0.014 at 1/250 s (the exposure the tuned-exposure
variant picks), while clipping v2's amplitude layers (v2 BER 0.068 → 0.338). t_row ∈ {0, 10, 27 µs} changes no scheme by more than 5 bps (`trow.csv`).

## 9.4 Low-light knife-edge (B2)
P15 with cap, 0.5–3.0 m, 250 symbols/point, brightness × ADC grid (`lowlight_grid.csv`). AUC v1 − genie [paired 95 % CI],
bps·m; G photo-electrons per LED per exposure in brackets:

| brightness (G e⁻/LED) | 8 bit | 10 bit | 12 bit |
|---|---|---|---|
| 1/256 (32 978) | −2024 [−2061, −1986] | −2252 [−2282, −2222] | −2250 [−2280, −2220] |
| 1/512 (16 489) | −409 [−456, −359] | −695 [−744, −644] | −682 [−729, −633] |
| 1/1024 (8 244) | **+715 [670, 758]** | −238 [−291, −184] | −257 [−310, −205] |
| 1/2048 (4 122) | 0 (all schemes 0) | 0 | 0 |

v1 beats the genie (and the best fixed baseline, QCD-style, by +418 [383, 450]) **only** at ≈8.2 ke⁻ (G) per LED with
the 8-bit ADC; the result is a quantisation artefact and **claim 3 is dropped** as a general statement.

## 9.5 Other disclosures
- Equal power is equal *summed drive*; radiant intensities at full drive are R 1.66, G 1.30, B 3.61 mW/sr. P33 = v2's
  natural power (only v2 runs unscaled). The radiant-equal rerun (`radiant_equal.csv`) gives the same ordering at
  2.5–3.5 m (OOK 743 at 2.5 m; v2 397/134 at 3.0/3.5 m, best).
- 48-bit CRC-block baselines: `claims_paired.csv` (baseline_crc = '48-bit blocks').
- 20000 lux: every scheme is 0 bps, because the ambient background (10–13.5 ke⁻) exceeds µe,sat with reflectance 0.5
  applied to every pixel (no dark surround is modelled).
- Tuning: held-out seeds, **same conditions** (tuning distances overlap the evaluation grid); only v2-CS, QCD-style and
  overlay are tuned.
- The QCD-OCC 3600-bps paper frame is now in the claim line-up ("QCD-paper", power-equalised); the 48-bit QCD-style
  variant stays because it is the HNCSM-comparable layered design. The paper frame is 0 bps at 2.5–3.0 m at 1/1500 s.
- Provenance (B6, corrected in audit 2): code commit e1a2904 (clean; `git_hash` now ignores results/). Audit runs
  (meta e1a2904 / e6d9687) and the P25/P33/P42 physical distance sweeps (meta 034f240, clean) were regenerated from clean
  commits, and the CSVs are bit-identical to the committed ones. **P60 was not regenerated**: its run_meta records
  `11b1072-dirty`, so it is LEGACY, excluded from all claims, and moved to `results/legacy/` together with the P33
  yaw/blur/t_exp/lux sweeps (no matching run_meta) and the superseded Wilson-envelope efficiency tables (see
  `results/legacy/README.md`). In audit 2 `claims.npz` was regenerated after the saturation-diagnostic fix (F4).
  Hashes are in `results/MANIFEST.sha256` (legacy files listed under `results/legacy/`).
