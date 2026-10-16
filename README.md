# occ_sim — HNCSM vs baselines on a simulated 8x8 RGB LED-matrix OCC link (simulation only)

## Reproduce (exact)
```bash
cd /workspace/occ_sim
python3 -m venv .venv && .venv/bin/pip install numpy opencv-python-headless matplotlib pandas pytest
.venv/bin/python -m pytest -q tests                                   # 58 tests
.venv/bin/python -m experiments.tune                                  # held-out-seed tuning -> results/tuned_params.json
.venv/bin/python -m experiments.run --frames 1000                     # equal-average-power sweeps (all 4)
.venv/bin/python -m experiments.run --frames 1000 --power peak --sweeps distance_m   # peak-power + goodput/power
.venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --tag _repro   # must be byte-identical to sweep_distance_m.csv
.venv/bin/python -m experiments.plots
```
Seeds: `config.py` (SEED=20261015 for evaluation, TUNE_SEED and GENIE_SEED are held out). Per-condition seeds come from
zlib.crc32 (the old runs used Python's salted `hash()` and were NOT reproducible). Every run writes
`results/run_meta*.json` with the seed, frames, tuned params, power reference, git hash and UTC time.

## Evaluation protocol (after the audit)
- **Equal average optical power (default):** each scheme's drive, pilots included, is scaled so its mean emitted power
  equals the lowest scheme's (pref = 33.0 units, HNCSM v2). `--power peak` turns scaling off (drive ≤ 1 per channel) and
  reports `goodput_per_power`.
- **CRC charge:** every independently decodable layer is charged 8 bits. Net goodput = Σ_layers (n−8)·30·(1−FER).
- **Common random numbers:** frame f uses the same payload stream and the same channel-noise seed for every scheme.
- **Confidence intervals:** Wilson 95% intervals on each layer's frame error rate, giving `goodput_lo/hi`. 1000 frames per point on all sweeps.
- **Adaptive-CSK genie:** picks the best of {OOK, CSK-4, CSK-8} per point using 300 frames on separate seeds
  (GENIE_SEED), then is reported with the evaluation-seed result of that choice.
- **Tuning:** an equal budget of 6 configs each for v2-CS (δ∈{0.1,0.2,0.3}×{1,2} bits), QCD-style (permutation subset)
  and overlay (a1/a2 split). Run on TUNE_SEED over 7 distances × 200 frames. Chosen: v2-CS δ=0.2, 2 bits;
  QCD subset `last16`; overlay a1=a2=0.25 (at the edge of the grid).
- **Ambient sweep:** at 2.5 m with non-uniform light (random linear gradient 0.4–1.6× plus a Gaussian hotspot).

## Layout
- `tx/schemes.py` — all modulation schemes (encode/decode, layers)
- `channel/geometry.py` pinhole projection of the panel (distance, yaw/pitch/roll) · `optics.py` Lambertian gain, Gaussian defocus PSF ·
  `sensor.py` spectral crosstalk, exposure, RGGB Bayer mosaic, Poisson shot + Gaussian read noise, 8-bit ADC, demosaic · `ambient.py` · `render.py` full pipeline (4x supersampled perspective warp → area downsample)
- `rx/sampler.py` homography rectification from finder corners + per-LED sampling + ambient reference · `rx/refs.py` pilot colour references, crosstalk-inverted on/off metric, nearest-colour classifier
- `experiments/run.py` sweeps (multiprocessing) · `experiments/plots.py`

## Channel parameters (defaults)
| Parameter | Value |
|---|---|
| Panel | 8x8 RGB LEDs, 8 mm pitch (64 mm panel), emitter diameter 0.6×pitch |
| Camera | f = 1000 px, 30 fps, global-shutter static frame (one symbol per frame) |
| Blur | Gaussian PSF, σ = hypot(0.5 px base, extra σ) |
| Sensor | full well 6000 e⁻, read noise 3 e⁻, white LED → 75 % full well, 8-bit, RGGB Bayer + OpenCV bilinear demosaic |
| Crosstalk (sensor RGB × LED RGB) | [[.85,.10,.05],[.12,.78,.10],[.04,.14,.82]] |
| Ambient | 0.03 × white-LED level, uniform (ambient sweep: 0–0.6 at 2.5 m, non-uniform gradient + hotspot) |
| Lambertian order | m = 1 (radiance independent of angle; only foreshortening matters) |
| Finder detection | ground-truth corners + N(0, 0.3 px) jitter (no real finder detector) |
| Sub-pixel phase | random per frame |
| Defaults for non-swept vars | d = 1 m, yaw 0°, extra blur 0, ambient 0.03 |
| Frames | 1000 per scheme per point, common random numbers, seeds from `config.py` (genie order chosen on 300 separate-seed frames) |

Metrics: see the evaluation protocol above.

## Schemes (all reserve the same 4 corner pilots: TL white, TR red, BL green, BR blue = finder + colour reference)
| Scheme | Bits/frame (gross; net = −8 CRC per layer) | Avg power (drive units, pilots incl.) | Notes |
|---|---|---|---|
| **HNCSM v1** | 16 base + 64 enh = 80 | 53.9 | per 4×4 quadrant: constant-weight (8 of 15) binary texture from a 16-word max-distance codebook; lit LEDs ∈ {W,R,G,B} |
| **HNCSM v2** | 48 base + 36 enh = 84 | 33.0 | QCD-style colour-balanced 2×2 base cells (first-16 permutations); enh = intensity full vs 0.5 on each lit LED; joint ML |
| **HNCSM v2-CS** (current) | 48 base + 72 enh = 120 | 42.0 | QCD-style base (first-16 permutations); enh = power-neutral colour shift, **δ = 0.2, 2 bits per lit LED**: p, (1−δ)p+δ·next, (1−δ)p+δ·prev, (1−2δ)p+δ(next+prev); base decoded with leaked templates (joint ML). δ/bits tuned on held-out seeds (`results/tuned_params.json`) |
| HNCSM v1 base-only | 16 | 102.0 | v1 textures, all lit LEDs white |
| CSK-8 | 180 | 96.1 | RGB-cube palette {K,R,G,B,Y,C,M,W} per LED (digital RGB keying, not CIE-xy CSK) |
| CSK-4 | 120 | 51.0 | {K,R,G,B} |
| OOK-8x8 (MIMO-OOK / LiCamIoT-like) | 60 | 96.0 | white on/off per LED |
| QR/Aztec-style | 28 | 106.3 | 2×2 finders in 3 corners, Hamming(7,4) on 49 modules |
| NestedTexture-inspired (Salvi & Geetha, IEEE Access 2022) | 16 outer + 16 inner | 93.8 | **assumption** (abstract only): per quadrant 11-LED outer ring (16-word codebook) + 2×2 inner pattern; independent template matching |
| QCD-style-inspired (Vasantha & Salvi, Appl. Sci. 2022) | 48 | 42.0 | **assumption** (abstract only): colour-neutral 2×2 cells (one R, G, B, dark LED); **tuned subset = `last16`** of the 24 permutations; 12 cells; ML decoding |
| Overlay-inspired (Nishimoto et al. 2012, doi:10.1109/GLOCOMW.2012.6477757) | 12 L1 + 24 L2 | 78.2 | **assumption** (abstract only): monochrome; L1 = 2×2 block mean, L2 = zero-mean ± pattern; intensity 0.5 + a1·s1 + a2·s2 with **tuned a1 = a2 = 0.25** (edge of tuning grid) |
| Adaptive-CSK genie (Onodera 2021-style bound) | – | as chosen | per point, best of {OOK, CSK-4, CSK-8} chosen on separate seeds, reported on evaluation seeds |

**Assumptions:** the author's schemes and Nishimoto's were re-implemented from abstracts only, because the full texts weren't retrievable. Matrix sub-structure, codebooks and amplitudes are my design choices, not the originals. "CSK" here is digital RGB-LED keying, not IEEE 802.15.7 CIE-xy CSK.

**v2-CS (current):** the leak is power-neutral. Variants are (1−δ)·p + δ·next, (1−δ)·p + δ·prev and
(1−2δ)·p + δ·(next+prev), and the base decoder uses the leaked templates (joint ML; `joint=False` gives the old two-stage decoder).

## Limitations
- **Rolling shutter is not modelled** and there is **no real finder detector**: the receiver gets true corners plus 0.3 px jitter. Both are left for later.
- No rolling-shutter or temporal effects (static frames, ideal frame sync); no motion blur; no real finder detection; no gamma/AWB/JPEG.
- The distance effect comes from the projected LED pitch: about 3.6 px at 2.25 m and 1.6 px at 5 m. Pixel-grid aliasing near 2 px pitch makes curves non-monotonic (e.g. HNCSM at 4.0 m).
- Ambient up to 0.6 doesn't hurt at 1 m because there's no saturation of the dark level. A low-exposure or high-ambient regime still needs a sweep.
- Codebooks and amplitudes haven't been optimized. The Gaussian PSF is not calibrated to a real lens.
- Hard-decision decoding only, with no soft FEC.

## Power-budget and graceful-degradation study
```bash
for P in 25 33 42 60; do .venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --pref $P --tag _P$P; done
.venv/bin/python -m experiments.efficiency
```
- Every scheme's drive, pilots included, is scaled to average power P. The scale can exceed 1 (LED overdrive up to 1.82× for v2 at P=60), and sensor saturation is modelled.
- **Efficiency** = net goodput / P, with Wilson 95% CIs (`results/efficiency_all_budgets.csv`, `efficiency_winners.csv`).
- **Degradation metrics** (`results/degradation_metrics.csv`):
  - **Peak:** the highest goodput over the sweep.
  - **AUC:** the trapezoid area under goodput vs distance over 0.5–5 m.
  - **auc_norm:** AUC / (peak × 4.5 m).
  - **d90 / d50 / d10:** the first distance after the peak where goodput falls below 90 / 50 / 10 % of peak (linear interpolation).
  - **max_step_drop_frac:** the largest drop between adjacent 0.25 m points, divided by peak.
  - **cliff_ratio:** the largest single-step drop divided by the total decline (peak − goodput at 5 m). 1 means the whole decline happens in one step.
  - **CI bounds** for AUC, d50 and d10 come from the curves built from the Wilson lower and upper goodput bounds.
- **Energy per delivered bit** = P / goodput, in power-unit·s/bit (`results/energy_per_bit.csv`).
- **Figures:** `results/fig_efficiency_vs_distance.{png,pdf}` and `results/fig_degradation_energy_P33.{png,pdf}`.
- **Caveat:** in this channel model goodput hardly depends on P over 25–60 (AUC changes by less than 1.5 %). Failure with distance is set by resolution and blur, not SNR, so efficiency scales as ~1/P. The power axis therefore mainly reflects each scheme's mean drive.

## Low-light (power-limited) channel
Preset `channel/presets.py::low_light(exposure_ms)`. The main results still use `presets.default()`.

| Parameter | Low light | Default | Justification |
|---|---|---|---|
| Photo-electrons, full-drive LED pixel | 80 e⁻ per ms of exposure (80 e⁻ at 1 ms) | 4500 e⁻ (75 % of 6000) | Dim LED, small 1.0–1.4 µm smartphone pixel, short exposure. Calibrated, not derived from a radiometric link budget (see below) |
| Full well | 4000 e⁻ | 6000 e⁻ | small-pixel CMOS, typically 3–6 ke⁻ |
| Analog gain | 1.5 DN/e⁻ (8-bit saturates at ~170 e⁻) | 255/6000 DN/e⁻ | high-ISO mode, so the low signal isn't lost to quantisation |
| Read noise | 3 e⁻ rms | 3 e⁻ | high-gain read noise, typically 1.5–3 e⁻ |
| Dark current | 20 e⁻/s (0.02 e⁻ at 1 ms) + 0.5 e⁻ per-frame offset (Poisson) | 0 | room-temperature CMOS |
| Power cap | no overdrive: scale = min(P/P_scheme, 1); the achieved power is reported | – | v2 (33.0) can't reach P = 42 and runs at 33 |

- **Calibration scan:** PHOTO_E_PER_MS ∈ {20, 40, 80} × P ∈ {15, 33} × d ∈ {1, 2, 3} m, 100 frames each.
  - At 80 e⁻/ms, CSK-8 at P = 33 still works at 1 m (4541 bps) but fails at 2 m.
  - v2 at 3 m gives 348 bps here against 1097 in the default channel.
  - So the link is SNR-limited before it is resolution-limited at mid range, and P changes the results.
- **Distance jitter:** all runs now use ±2 % uniform distance jitter per frame (`distance_jitter_frac = 0.02`). This models hand-held placement and breaks lock-step with the Bayer phase at exact integer LED pitches.

Commands:
```bash
for P in 15 25 33 42; do .venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --channel lowlight --exposure-ms 1.0 --cap --pref $P --tag _LL_P$P; done
.venv/bin/python -m experiments.run --frames 1000 --sweeps exposure_ms --channel lowlight --cap --pref 33 --tag _LL_P33
.venv/bin/python -m experiments.efficiency --pattern 'sweep_distance_m_LL_P*.csv' --prefix lowlight_
.venv/bin/python -m experiments.exposure_plot
```
Outputs: `results/lowlight_*` (efficiency, winners, degradation metrics, energy per bit, figures in png and pdf) and `results/sweep_exposure_ms_LL_P33.csv`.

## The v2-CS "dip" near 1.75 m
`experiments/dip_probe.py` (`results/dip_probe.csv`) scans 1.40–2.20 m in 0.05 m steps, with 400 frames per point at P = 33.
- **With Bayer on, enhancement-layer frame error rises steadily:** 0.025 at 1.4 m, 0.74 at 1.75 m, 0.99 at 1.9 m. Then it falls back sharply to **0.30 at exactly 2.00 m** and returns to 0.96 at 2.05 m. CSK-8 shows the same spike at 2.00 m.
- **With Bayer off, the curve is monotonic and much lower:** 0.07 at 1.75 m, 0.17 at 2.0 m.
- **Explanation:** 2.00 m gives an LED pitch of exactly 4 px, an integer multiple of the 2-px RGGB period. Every LED then sits on the same colour-filter phase, which favours the colour-shift layer. So the "dip" at 1.75 m is the normal decline, and 2.00 m is an aliasing *peak*. The enhancement layer is limited by demosaic colour moiré, not noise.
- **Mitigation:** ±2 % distance jitter (now the default) cuts the 2.0 m spike (v2-CS 2579 → 2104 bps) but doesn't remove it. A wider receiver sampling window (6 px) lowers the 1.75 m frame error to 0.22, but makes it worse at 1.4–1.5 m. It has not been adopted, because it would need equal re-tuning for all schemes.

## Revision runs (16 Oct 2026, all with ±2 % distance jitter, seed 20261015, 1000 frames/point)
Commands:
```bash
for P in 25 33 42 60; do .venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --pref $P --tag _P$P; done
.venv/bin/python -m experiments.efficiency          # regenerates degradation_metrics.csv, energy_per_bit.csv, efficiency_*.csv, fig_*_P33
.venv/bin/python -m experiments.run --frames 1000 --pref 33 --sweeps yaw_deg,ambient,blur_sigma_px --tag _J_P33
```
- The default-channel power sweeps (`sweep_distance_m_P{25,33,42,60}.csv`) used to be pre-jitter. They have been **re-run with jitter**, so every run is now consistent. The pre-jitter files are kept in `results/archive_prejitter/`.
- Effect at P = 33:
  - d10 v2 4.16 → 4.18 m; v2-CS 4.20 → 4.18 m; CSK-4 2.66 → 2.74 m; genie 2.63 → 2.68 m.
  - AUC v2-CS 6264 → 6121 (its CI now overlaps CSK-4's, 5919).
  - v2-CS at 2.0 m: 2588 → 2093 bps.
- New stress sweeps at P = 33 with jitter: `sweep_{yaw_deg,ambient,blur_sigma_px}_J_P33.csv` and `run_meta_J_P33.json`. The older `sweep_{yaw_deg,ambient,blur_sigma_px}.csv` are pre-jitter, at pref 33.011.
- Run metadata: `run_meta_P*.json` and `run_meta_J_P33.json` record `distance_jitter_frac = 0.02` and git `392d057-dirty`.
