# occ_sim — open, physics-grounded benchmark of LED-matrix OCC schemes (benchmark-r0, simulation only)

**Quick start**
```
python3.13 -m venv .venv && .venv/bin/pip install -r requirements.lock
make test          # unit tests
make tables        # verify shipped results (MANIFEST.sha256) and regenerate every table from the npz arrays
make full          # re-simulate all benchmark groups (many CPU-hours; resumable via CKPT checkpoints)
.venv/bin/python -m experiments.bench_run --list   # registered schemes; add your own: docs/ADDING_A_SCHEME.md
```
Protocol, fairness rules, release statement, 802.15.7 OCC-PHY rationale and limitations: `docs/BENCHMARK_PROTOCOL.md`.
IMX219 parameters with sources: `docs/IMX219_PARAMETERS.md`. External anchors: `docs/ANCHORS.md`.
Results: `results/benchmark/SUMMARY.md`; reviewer response table: `docs/RESPONSE_TABLE.md`.
Release status: benchmark-r9 release candidate, local only (not yet pushed, DOI pending). Licence: MIT (`LICENSE`). Citation: `CITATION.cff` / `.zenodo.json`.
## Install
Requires Python 3.13 (tested 3.13.5) on Linux/macOS; ~130 MB disk for the repository incl. shipped results.
```bash
git clone https://github.com/SanketSalviNITK/occ-sim-benchmark.git && cd occ-sim-benchmark
python3.13 -m venv .venv && .venv/bin/pip install -r requirements.lock
make test                      # 111 unit tests
```
## Reproduce
```bash
./reproduce.sh tables          # minutes: sha256-verify shipped data (results/MANIFEST.sha256), run tests, regenerate tables from npz
./reproduce.sh full            # many CPU-hours: re-simulate every benchmark group (resumable, CKPT=.ckpt), then tables
OMP_NUM_THREADS=1 PROCS=8 .venv/bin/python -m experiments.r9_qcd_fix   # benchmark-r9 QCD-OCC floor analysis (minutes)
```
Additive revision runners (r6–r9) are listed at the end of `reproduce.sh`. All seeds are fixed in `config.py`; every run writes a `run_meta*.json`.
## Citation
If you use this benchmark please cite it via `CITATION.cff` (GitHub "Cite this repository") or the Zenodo DOI
the Zenodo concept DOI (minted automatically on the first GitHub release; not reserved yet). Re-implemented third-party schemes are labelled
"-inspired"; please also cite the original papers given in their docstrings.
## License
Code and shipped results: MIT (`LICENSE`), © 2026 Sanket Salvi. Python dependencies (not vendored) are under permissive licences (BSD/MIT/Apache-2.0/PSF/MIT-CMU).

## Claims (C2: benchmark-r8; IMX219: benchmark-r5)
> **Claims status r8:** the C2 (IMX174) wording below is the strictly scoped wording of the r7 audit (§3): 1/36 factorial cells, relative only, with the R-V1 σ_mult results filled in; change log `results/benchmark/CLAIMS_r7.md` (r8 section).
> **Claims status r3→r5:** the benchmark-r2 claims were unchanged through benchmark-r3 and benchmark-r4 (only metas, manifest and wording tidy-ups). In **benchmark-r5** the C2 numbers were re-stated on one canonical seed set (claims/E2) and the oracle-corner numbers were re-sourced (`oracle_pairs.csv`); the qualitative claims are unchanged. Old→new numbers: `results/benchmark/CLAIMS_r5.md`.
**C2 (IMX174), strictly scoped wording (benchmark-r8; audit r7 §3 wording, replaces the r7 wording; canonical seed set = claims/E2, protocol item 9; CIs B = 10000, bootstrap seed 0; sources: `results/benchmark/CLAIMS_r7.md`, `results/benchmark/r6/*.csv`, `results/benchmark/r7/factorial_binding.csv`, `results/benchmark/r8/mult_binding.csv`). C2 is reported only as a case study of benchmark sensitivity — how a ranking hinges on optics and receiver front-end assumptions — not as evidence that v2 outperforms:**
> "In one assumed configuration — IMX174 model, P33, brightness 1/128, exposure 1/1500, ASSUMED lens f = 6 mm, f/2.0 focused at 1.0 m, 65 mm 8×8 panel on axis, shared corner finder, canonical seeds — HNCSM v2 has the highest simulated goodput at 3.0 m and 3.25 m (binding margin +150.0 [126.6, 173.4] and +107.6 [86.3, 129.0] bps). This is not a robust result: in a 36-cell factorial over focus, focal length, f-number and brightness it holds only in this default cell (1/36 at each distance), and it disappears under an 80 mm panel, under 30° yaw at 3.25 m, under CFA crosstalk ×2 and under per-scheme tuned exposure. The comparison is relative only. With an added signal-proportional noise term fitted to external anchors (σ_mult 0.024–0.15, per-pixel or per-frame, outside the Holm family) v2 stays first and the margin stays positive (minimum +100.8 [76.8, 124.8] at 3.0 m and +96.0 [72.6, 119.4] at 3.25 m), but it shrinks by 36–49 bps at 3.0 m at σ_mult = 0.15 because noise reduces the shared finder's gross errors on the baselines; part of the noise-free margin is therefore an artefact of noise-free rendering. With oracle corners v2 is not first at 3.0 m under any tested noise level, so at 3.0 m the advantage lies in finder reliability, not demodulation; at 3.25 m this attribution holds only without added noise (oracle margin n.s. for σ_mult ≥ 0.05). No claim is made for real hardware or for other optics."

Limitations of the σ_mult check: per-LED correlated noise is untested; the per-frame mode may be largely cancelled by the pilot references (inferred); the σ_mult values are one-point fits (plausible, not validated).

Supporting statistics (outside the quote): across all four seed sets the minimum margin is +148.2 (3.0 m) and +107.6 (3.25 m), Holm-significant in the 56-claim family; 3.5 m is not claimed (canonical +4.3 [−10.1, 19.1]); oracle corners on the same seeds: −114.1 [−141.9, −86.6] vs OOK-8x8 at 3.0 m and −24.0 [−45.0, −3.6] vs QCD-style at 3.25 m (unadjusted; n.s. under σ_mult ≥ 0.05, `r8/mult_binding.csv`). Under every tested σ_mult (0.024/0.05/0.15, per-pixel and per-frame) v2 remains first at 3.0 and 3.25 m and the binding margin stays significantly positive; it shrinks significantly only at σ_mult = 0.15 at 3.0 m (Δ −49.2 [−73.8, −25.2] per-pixel, −36.0 [−60.0, −12.0] per-frame). The r8 noise runs are outside the Holm family.

**C1/C2 on IMX219, safe wording (benchmark-r5; sources: `results/benchmark/CLAIMS_r5.md`):**
> "C1 here means the audit-2 claim that at 2.5 m (1/1500 s, brightness 1/128) v2 exceeds the IEEE 802.15.7 CSK baselines; C2 means the IMX174 binding-margin claim at 3.0–3.5 m above. On the IMX219 preset `imx219f` (sourced geometry and noise, uncalibrated photometric scale), neither transfers. At the same distances (2.5, 3.0, 3.25 and 3.5 m), v2 is significantly below the binding baseline at every point, with fixed or tuned exposure and with the scale-free finder or oracle corners. Examples: 2.5 m, −1273.6 [−1322.6, −1222.0] bps vs genie(CSK802-8); 3.0 m, −999.6 [−1009.9, −985.3] bps vs QCD-OCC (paper frame), and −991.4 [−1005.7, −977.2] with oracle corners. At matched pixels-per-LED v2 is significantly below at 2.5–3.25 m with both finders (e.g. matched 3.0 m: −57.0 [−75.6, −38.4] vs QCD-style-inspired). At matched 3.5 m the result is not significant (+13.2 [−11.4, 36.0] with the scale-free finder; +0.6 [−23.4, 24.6] with oracle corners at fixed exposure). The one exception is oracle corners with tuned exposure (+23.4 [1.2, 45.6], unadjusted; n.s. after Holm, p_holm 0.33, r6 `holm_claims.csv`). These are simulation results on an uncalibrated preset and say nothing about real IMX219 hardware."

IMX219 scope: all IMX219 results use the current preset (`imx219f`), photometrically uncalibrated (sourced geometry and noise). Matching the measured CQ sensitivity would need an effective QE of 1.5–2.16 (impossible as QE); those ×3-QE runs are not shipped. The published QCD-OCC BER is matched by this preset near Tx brightness 1/2048, not the 1/128 used in E3.

**Ablation (R3/N4):** lit0.75 recovers 75.6 / 42.6 / 33.8 % and lit0.75 + 2-level decoder 88.6 / 72.7 / 82.4 % of the v2 − base-only gap (3.0 / 3.25 / 3.5 m). A significant residual of +35.4 [13.2, 58.2] bps remains at 3.25 m; the decoder gain is larger on the 0.75-level Tx (interaction), so the shares are not additive. Radiant-equal power: same within 1.2 bps (scales equal to 3e-4).

Not claimed: that v2's modulation outperforms at 3.0 m; any robust or unqualified C2; that C1/C2 fail on real or calibrated IMX219 hardware.

**QCD-OCC error floor (benchmark-r9):** the ≈1.5e-2 QCD-OCC BER floor is a Bayer under-sampling artefact of the 4×4 sampling window; an opt-in `QCDOCCWin6` receiver removes it (≈1e-3 at 1/160–1/1024) and C2/rankings are unchanged. Details: `results/benchmark/CLAIMS_r7.md` (R9).

Re-implemented schemes are labelled **-inspired** (abstract-based re-implementations).

---

# occ_sim — HNCSM vs baselines on a simulated 8x8 RGB LED-matrix OCC link (simulation only)

## Reproduce (exact)
```bash
cd occ-sim-benchmark   # repository root
python3 -m venv .venv && .venv/bin/pip install numpy opencv-python-headless matplotlib pandas pytest
.venv/bin/python -m pytest -q tests                                   # 78 tests
.venv/bin/python -m experiments.tune                                  # held-out-seed tuning -> results/tuned_params.json
.venv/bin/python -m experiments.run --frames 1000                     # equal-average-power sweeps (all 4)
.venv/bin/python -m experiments.run --frames 1000 --power peak --sweeps distance_m   # peak-power + goodput/power
.venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --pref 33 --tag _repro   # must be byte-identical to sweep_distance_m_P33.csv (headline, jittered)
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
- **Tuning (see docs/BENCHMARK_PROTOCOL.md item 4):** exposure is tuned over T_EXPS for all schemes; `tune.py` additionally
  tries 6 configs for each of v2-CS (δ∈{0.1,0.2,0.3}×{1,2} bits), QCD-style (permutation subset) and overlay (a1/a2 split);
  the other schemes get no scheme-parameter tuning, so no equal-tuning-effort claim is made. Run on TUNE_SEED over 7 distances × 200 frames. Chosen on the **ideal channel**
  (`results/tuned_params.json`, used only by `all_schemes()`): v2-CS δ=0.2, 2 bits; QCD subset `last16`; overlay a1=a2=0.25 (at the edge of the grid).
  **Physical channel / all benchmark runs** (`results/tuned_params_phys.json`, loaded by `all_schemes_phys()`): v2-CS δ=0.3, 2 bits; QCD subset `maxdist-0`; overlay (0.35, 0.15).
- **Ambient sweep:** at 2.5 m with non-uniform light (random linear gradient 0.4–1.6× plus a Gaussian hotspot).

## [SUPERSEDED] Claims (internal reproducibility audit 2, audit-r2) — historical only
> **SUPERSEDED by the benchmark claims (now benchmark-r5) at the top of this README. Nothing in this section (C1, C2, table, limitations) is a current claim; kept for history.**

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

**C2 (historical, superseded by the benchmark wording).** v2 has the highest goodput at 3.0–3.5 m at budgets P25/P33/P42 (paired CIs exclude 0; absolute
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

## Layout
- `tx/schemes.py` — all modulation schemes (encode/decode, layers)
- `channel/geometry.py` pinhole projection of the panel (distance, yaw/pitch/roll) · `optics.py` Lambertian gain, Gaussian defocus PSF ·
  `sensor.py` spectral crosstalk, exposure, RGGB Bayer mosaic, Poisson shot + Gaussian read noise, 8-bit ADC, demosaic · `ambient.py` · `render.py` full pipeline (4x supersampled perspective warp → area downsample)
- `rx/sampler.py` homography rectification from finder corners + per-LED sampling + ambient reference · `rx/refs.py` pilot colour references, crosstalk-inverted on/off metric, nearest-colour classifier
- `experiments/run.py` sweeps (multiprocessing) · `experiments/plots.py`

# IDEAL (legacy) channel — historical, NOT used by any claim
Everything from here to "Physical channel" describes the original ideal channel (global-shutter static frames, true
corners + jitter, 30 fps). The Claims section above uses only the physical channel (METHODS §8–§9). Historical
ideal-channel P60 files (`sweep_distance_m_P60.csv`, `run_meta_P60.json`) are kept for traceability only.

## [Ideal channel] Channel parameters (defaults)
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

## [Ideal channel] Schemes (all reserve the same 4 corner pilots: TL white, TR red, BL green, BR blue = finder + colour reference)
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
| QCD-style-inspired (Vasantha & Salvi, Appl. Sci. 2022) | 48 | 42.0 | **assumption** (abstract only): colour-neutral 2×2 cells (one R, G, B, dark LED); **tuned subset = `last16`** (ideal channel; physical channel/benchmark: `maxdist-0`, `results/tuned_params_phys.json`) of the 24 permutations; 12 cells; ML decoding |
| Overlay-inspired (Nishimoto et al. 2012, doi:10.1109/GLOCOMW.2012.6477757) | 12 L1 + 24 L2 | 78.2 | **assumption** (abstract only): monochrome; L1 = 2×2 block mean, L2 = zero-mean ± pattern; intensity 0.5 + a1·s1 + a2·s2 with **tuned a1 = a2 = 0.25** (edge of tuning grid) |
| Adaptive-CSK genie (Onodera 2021-style bound) | – | as chosen | per point, best of {OOK, CSK-4, CSK-8} chosen on separate seeds, reported on evaluation seeds |

**Assumptions:** the author's schemes and Nishimoto's were re-implemented from abstracts only, because the full texts weren't retrievable. Matrix sub-structure, codebooks and amplitudes are my design choices, not the originals. "CSK" here is digital RGB-LED keying, not IEEE 802.15.7 CIE-xy CSK.

**v2-CS (current):** the leak is power-neutral. Variants are (1−δ)·p + δ·next, (1−δ)·p + δ·prev and
(1−2δ)·p + δ·(next+prev), and the base decoder uses the leaked templates (joint ML; `joint=False` gives the old two-stage decoder).

## [Ideal channel] Limitations
- (Ideal channel only; the physical channel models rolling shutter and a real corner detector, METHODS §8.) No rolling-shutter or temporal effects (static frames, ideal frame sync); no motion blur; no real finder detection; no gamma/AWB/JPEG.
- The distance effect comes from the projected LED pitch: about 3.6 px at 2.25 m and 1.6 px at 5 m. Pixel-grid aliasing near 2 px pitch makes curves non-monotonic (e.g. HNCSM at 4.0 m).
- Ambient up to 0.6 doesn't hurt at 1 m because there's no saturation of the dark level. A low-exposure or high-ambient regime still needs a sweep.
- Codebooks and amplitudes haven't been optimized. The Gaussian PSF is not calibrated to a real lens.
- Hard-decision decoding only, with no soft FEC.

## [Ideal channel] Power-budget and graceful-degradation study
```bash
for P in 25 33 42; do .venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --pref $P --tag _P$P; done
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

## [Ideal channel] Low-light (power-limited) channel
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

## [Ideal channel] The v2-CS "dip" near 1.75 m
`experiments/dip_probe.py` (`results/dip_probe.csv`) scans 1.40–2.20 m in 0.05 m steps, with 400 frames per point at P = 33.
- **With Bayer on, enhancement-layer frame error rises steadily:** 0.025 at 1.4 m, 0.74 at 1.75 m, 0.99 at 1.9 m. Then it falls back sharply to **0.30 at exactly 2.00 m** and returns to 0.96 at 2.05 m. CSK-8 shows the same spike at 2.00 m.
- **With Bayer off, the curve is monotonic and much lower:** 0.07 at 1.75 m, 0.17 at 2.0 m.
- **Explanation:** 2.00 m gives an LED pitch of exactly 4 px, an integer multiple of the 2-px RGGB period. Every LED then sits on the same colour-filter phase, which favours the colour-shift layer. So the "dip" at 1.75 m is the normal decline, and 2.00 m is an aliasing *peak*. The enhancement layer is limited by demosaic colour moiré, not noise.
- **Mitigation:** ±2 % distance jitter (now the default) cuts the 2.0 m spike (v2-CS at P=33: 2588 → 2093 bps, archive_prejitter/sweep_distance_m_P33.csv vs sweep_distance_m_P33.csv; the earlier "2579" could not be traced to any stored file and is withdrawn) but doesn't remove it. A wider receiver sampling window (6 px) lowers the 1.75 m frame error to 0.22, but makes it worse at 1.4–1.5 m. It has not been adopted, because it would need equal re-tuning for all schemes.

## [Ideal channel] Revision runs (16 Oct 2026, all with ±2 % distance jitter, seed 20261015, 1000 frames/point)
Commands:
```bash
for P in 25 33 42; do .venv/bin/python -m experiments.run --frames 1000 --sweeps distance_m --pref $P --tag _P$P; done
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

## [Ideal channel] Reproducibility check and run provenance (16 Oct 2026)
- Repro: `--frames 1000 --sweeps distance_m --pref 33 --tag _repro` (89 s) gives `sweep_distance_m_repro.csv` byte-identical to `sweep_distance_m_P33.csv` (`cmp` clean). That replaces the stale pre-jitter repro file. Its run_meta records `ddf7e7e-dirty`; the only dirty files were these untracked/modified result outputs, and the source matched ddf7e7e.
- Commits per result set: 708204b = low-light preset, jitter, overdrive cap, dip probe; 392d057 = low-light study (`*_LL_*`, lowlight_*), dip analysis; 2140cd8 = audit fixes (equal power, CRN, per-layer CRC, Wilson CI, tuning, seeds); pre-jitter baseline code; ddf7e7e = jittered default power sweeps (`sweep_distance_m_P{25,33,42,60}.csv`) and stress sweeps (`*_J_P33.csv`). run_meta files that show `-dirty` were written before their results were committed.
- Default channel (`cap: false`): the power scale can exceed 1 (overdrive up to 1.82× for v2 at P=60). Low light uses `cap: true`.

# PHYSICAL channel (used by the claims)
## Physical channel (31 Oct 2026)
This is a literature-sourced channel. It sits alongside the legacy one, which is unchanged. The full model, formulas and parameter table (each parameter has a DOI or is marked ASSUMED) are in METHODS.md §8.

```
.venv/bin/python -m experiments.tune --channel physical       # held-out retune -> results/tuned_params_phys.json
./run_phys_all.sh                                             # all PHYS sweeps (1000 symbols/point, ~90 min on 8 cores)
.venv/bin/python -m experiments.validate_qcd                  # QCD-OCC reproduction -> results/validation_qcd.csv
.venv/bin/python -m experiments.efficiency --pattern 'sweep_distance_m_PHYS_P*.csv' --prefix phys_
.venv/bin/python -m experiments.efficiency --pattern 'sweep_distance_m_PHYS_LL_P*.csv' --prefix phys_lowlight_
.venv/bin/python -m experiments.plots_phys                    # results/phys_*.png/.pdf
```

Key differences from the legacy channel:
- Goodput uses f_tx = 15 symbols/s (rolling-shutter, asynchronous camera), not 30 fps.
- The CSK baselines are IEEE 802.15.7 CIE-xy 4/8-CSK.
- A real corner detector replaces the true corners + jitter.

Validation: QCD-OCC at 200 cm, 3600 bps gives a simulated BER of 6.0e-3 (symbol-cluster 95 % CI 4.5–7.5e-3, METHODS §9.2) against the measured 1.13e-2; order-of-magnitude calibration only.

## Internal audit 1 fixes (31 Oct 2026)
See METHODS §9. New: `experiments/stats.py` (cluster/paired bootstrap), `experiments/audit_r1.py` (runs),
`experiments/audit_r1_report.py` (tables → `results/audit_r1/`), per-symbol data `results/phys_sym/`,
`results/MANIFEST.sha256`. The claims are stated only in the "Claims" section above; brightness is an unidentified nuisance parameter
(validation = order of magnitude only); the blue channel clips at the default brightness 1/128. Legacy outputs: `results/legacy/`.
