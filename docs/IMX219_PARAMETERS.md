# IMX219 (Raspberry Pi Camera Module v2) parameter table (audit R6)

Code: `channel/presets_phys.py`. Presets: `imx219()` (review-r1, legacy), `imx219b()` (benchmark-r0: CQ-anchored QE scale + scale-free finder).
Source keys: [RPI] Raspberry Pi camera hardware spec page; [LNX] Linux `drivers/media/i2c/imx219.c`; [CQ] Yonemoto, Interface (CQ Publishing) 2026-10, p.162, Table 1 (one measured module); [PAG] Pagnutti et al., J. Electron. Imaging 26(1) 013014 (2017).

| Parameter | Value | Status / source |
|---|---|---|
| pixel pitch | 1.12 µm | [RPI] |
| active rows × cols used | 1080 × 1920 (1080p 1:1 crop) | [RPI] mode list |
| focal length, f-number | 3.04 mm, F2.0 | [RPI] |
| focus distance | 2.0 m | **ASSUMED** (module focus is adjustable; ≈ hyperfocal 2.06 m) |
| t_row | 18.90 µs (3448 / 182.4 MHz) | [LNX] IMX219_LLP_MIN = 0x0d78, IMX219_PIXEL_RATE |
| frame rate | 30 fps | [RPI] (≤ 47 fps at 1080p); 30 chosen to match the QCD-OCC setup |
| ADC bit depth | 10 bit (RAW10) | [LNX]/[PAG] |
| conversion gain | 0.177 DN/e (K12 = 0.708) | [CQ]; **bit depth of CQ's DN is ASSUMED 10-bit** (inferred: 1023/0.177 ≈ 5.8 ke ≈ stated saturation) |
| full well | 5800 e | [CQ] (lower bound "> 5800 e") |
| read noise | 1.8 e | [CQ] |
| dark_e_s | 4.2 e/s | [CQ] value is **DCNU** (dark-current non-uniformity, FPN), used as a stand-in for the mean dark current — **ASSUMED** |
| DSNU | 0.32 e | [CQ] |
| PRNU | 1.05 % (G) | [CQ] |
| QE (R,G,B) — `imx219()` | (0.492, 0.671, 0.709) | **ASSUMED** (IMX174 values; absolute IMX219 QE not public) |
| QE (R,G,B) — `imx219b()` | IMX174 shape × 3.0426 = (1.50, 2.04, 2.16) | scale from [CQ] sensitivity S_G = 3400 e/(lx·s) / model G response 1117.5 e/(lx·s). **Values > 1 are unphysical**: the lux→photon interpretation (sensor-plane illuminance, 3-band white model, 555-nm-equivalent photons/lm) does not match CQ's measurement conditions. Treat as an *effective* responsivity, not QE. ASSUMED. |
| CFA / crosstalk | IMX174 matrix, RGGB phase | **ASSUMED** (no published IMX219 crosstalk; native BGGR per [PAG], phase is flip-dependent) |
| corner finder | `imx219b`: scale-free, min_dn = max(k·1.4826·MAD(border), 1 DN), k = 12 | benchmark design choice (results/benchmark/finder_tuning.csv, disjoint seeds; k not binding) |

Corner gross-error rate (results/review_r1/corner_error_bench.csv, 200 frames/distance): IMX219 old finder 0.60–0.83; `imx219f`/`imx219cq` 0.000 at 0.5–5 m (median error 0.02–0.04 pitch). IMX174 default path unchanged (byte-identical).
