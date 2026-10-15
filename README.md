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
| Ambient | 0.03 × white-LED level (sweep 0–0.6) |
| Lambertian order | m = 1 (radiance independent of angle; only foreshortening matters) |
| Finder detection | ground-truth corners + N(0, 0.3 px) jitter (no real finder detector) |
| Sub-pixel phase | random per frame |
| Defaults for non-swept vars | d = 1 m, yaw 0°, extra blur 0, ambient 0.03 |
| Frames | 300 random-payload frames per scheme per point |

Metrics: see the evaluation protocol above.

## Schemes (all reserve the same 4 corner pilots: TL white, TR red, BL green, BR blue = finder + colour reference)
| Scheme | Bits/frame | Notes |
|---|---|---|
| **HNCSM** (proposed) | 16 base + 64 enh = 80 | per 4×4 quadrant: constant-weight (8 of 15) binary texture from a 16-word max-distance codebook; each lit LED ∈ {W,R,G,B} |
| **HNCSM v2** | 48 base + 36 enh = 84 | base = QCD-style colour-balanced 2×2 cells (one R/G/B/dark LED, 16 of 24 permutations = 4 bits/cell, 12 cells); enh = per lit LED intensity full vs 0.5 (1 bit, 3 per cell). Joint per-cell ML decoding (arrangement × level) |
| **HNCSM v2-CS (d=0.2,2b)** (chosen) / (d=0.1,1b) | 48 base + 72 enh = 120 / 48 + 36 = 84 | QCD-style base; each lit LED kept at full primary drive, enhancement = leak of δ into the next/previous primary (2 bits: pure, +next, +prev, +both; 1 bit: pure, +next). The leak adds emission, so it is not strictly equal-luminance. Base decided on pure-primary templates first, then enhancement (two-stage; joint ML gave the same results in `experiments/tune_cs.py`). δ∈{0.1,0.2,0.3} × {1,2} bits tuned in `results/tune_v2cs_joint{0,1}.csv` |
| HNCSM base-only | 16 | same textures, all lit LEDs white |
| CSK-8 | 180 | RGB-cube palette {K,R,G,B,Y,C,M,W} per LED |
| CSK-4 | 120 | {K,R,G,B} |
| OOK-8x8 (MIMO-OOK / LiCamIoT-like) | 60 | white on/off per LED |
| QR/Aztec-style | 28 | 2×2 finder blocks in 3 corners, Hamming(7,4) on 49 modules |
| NestedTexture-inspired (Salvi & Geetha, IEEE Access 2022) | 16 outer + 16 inner | **assumption**: per quadrant 11-LED outer ring (16-word codebook) nested with 2×2 inner pattern; independent template matching |
| QCD-style-inspired (Vasantha & Salvi, Appl. Sci. 2022) | 48 | **assumption**: colour-neutral 2×2 "hadrons" (one R, G, B and dark LED; 16 of 24 arrangements = 4 bits/cell), 12 cells, ML decoding |
| Overlay-inspired (Nishimoto et al. 2012, doi:10.1109/GLOCOMW.2012.6477757) | 12 L1 + 24 L2 | **assumption**: monochrome; L1 = 1 bit per 2×2 block as block mean; L2 = zero-mean ±pattern inside block (2 bits); intensity 0.5+0.3·s1+0.2·s2 |
| Adaptive-CSK genie (Onodera 2021-style upper bound) | – | per operating point, best goodput among {OOK, CSK-4, CSK-8} assuming ideal feedback |

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
