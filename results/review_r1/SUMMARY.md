# Review R1 (IEEE VTC): experiment summary

Branch `review-r1`, made from `audit-r3-fix` (77c721d). Simulator modules are unchanged. Additions are limited to `tx/ablation.py`, the `imx219()` preset and the `experiments/review_r1*.py` / `e4_trace.py` scripts.
Additivity check: re-running v2 at P33, 3.0 m (sweep) reproduces `sweeps_PHYS_P33` byte-identically, and E2 P33 d3.0 matches `claims.npz` (576/576 arrays). Tests: `tests/test_review_r1.py`.

## E1: hierarchy ablation (`e1_layers.csv`, `e1_ablation_sweep.csv`, `e1_decomposition.csv`)
- The v2 enhancement layer delivers **0 bps at 3.0 to 3.5 m** for every budget (P25, P33, P42). It delivers about 1 to 10 bps at 2.25 to 2.75 m, 76 to 99 bps at 2.0 m, and about 300 to 420 bps at 1.75 m or closer. In the claims runs it is about 0 at every point.
- v2 beats v2-base-only at 2.25 to 3.75 m (P33: +34.7 at 2.5 m, +162.6 at 3.0 m, +129.6 at 3.25 m, +81.6 at 3.5 m; all CIs exclude 0). v2-base-only vs QCD-style is n.s. at 2.5 to 3.5 m. v2 loses at 4.0 m.
- Decomposition at P33: dimming the data LEDs to 0.75 with pilots at full drive (`[lit 0.75]`) recovers most of the gap (v2 minus lit-0.75 is +39.6, +74.4 and +54.0 at 3.0, 3.25 and 3.5 m). The two-level ML decoder adds +15 to +29 over base-only.
- **Verdict:** v2's advantage in the C2 window does **not** come from hierarchical enhancement bits. It comes from the signal and decoder design: data LEDs below pilot drive under equal power, plus level diversity and the 2-level decoder. Hierarchy contributes bits only at 2 m or closer.

## E2: C2 robustness, P33 only (`e2_robust.csv`, `e2_survival.csv`)
Grid: exposure {fixed 1/1500, tuned} × brightness {1/64, 1/128, 1/256}. The comparison uses the best baseline chosen on the tuning set, and the best on the eval set is also shown.
- **No C2 point survives every perturbation.** Minimum paired lower bounds: 3.0 m −89.4, 3.25 m −116.4, 3.5 m −35.4. They are the same for tune-best and eval-best, and for native and 48-bit CRC.
- All three distances win at 1/64 (fixed and tuned) and at fixed 1/1500 with 1/128 (the paper's operating point).
- 3.0 m and 3.25 m lose at tuned/1/128 (3.0 m: −69 [−89, −49]) and at 1/256. 3.5 m is n.s. at tuned/1/128 and at 1/256.
- P25 and P42: **not run** (stopped to wrap up).

## E3: IMX219 sensor swap (`channel/presets_phys.py::imx219`, `e3_*.csv`, `e3_goodput_vs_pxled.png`)
| Parameter | Value | Source |
|---|---|---|
| Pixel pitch | 1.12 µm | Raspberry Pi camera docs |
| Mode | 1920×1080 at 30 fps | RPi docs |
| Lens | 3.04 mm, F2.0 | RPi docs |
| Focus distance | 2.0 m | ASSUMED |
| t_row | 18.90 µs (3448 / 182.4 MHz) | Linux `imx219.c` (LLP_MIN 0x0d78, PIXEL_RATE) |
| ADC | 10 bit | Linux driver; Pagnutti et al. 2017 |
| Conversion gain | 0.177 DN/e (10 bit) | CQ Interface (Yonemoto), if2610 Table 1 |
| Full well | 5800 e (a lower bound) | CQ |
| Read noise | 1.8 e | CQ |
| DSNU | 0.32 e | CQ |
| PRNU | 1.05 % | CQ (G channel) |
| Dark current | 4.2 e/s | ASSUMED |
| QE | IMX174 curve | ASSUMED (not published) |
| CFA / Bayer pattern | unchanged / RGGB | ASSUMED (real sensor is BGGR) |

- **Validation** (`e3_validation.csv`): BER is 0 from brightness 1/256 to 1/4 and about 0.5 (finder fails) at 1/512 or dimmer. No brightness value reproduces the published 1.13e-2, so nothing was fitted and the transmitter stays at 1/128.
- **C1/C2 do not hold under IMX219.** At the same metres (2.5 to 3.5 m, fixed exposure), v2 gets about 237 to 298 bps vs QCD-style at about 460. With tuned exposure, CSK802-8 (about 2540) beats v2 (about 1020).
- At matched px/LED with tuned exposure, v2 wins only at the 3.5 m equivalent (+34.2 [9.6, 58.2]). The bracket is mixed: at 1/64 v2 wins at m2.5 but loses at m3.0 and m3.25; at 1/256 nearly everything is 0.
- In the 1 to 10 m sweep, v2 (about 240 to 355 bps) sits below v1, QCD-style and base-only.
- Caveat: the corner finder makes gross errors on about 70 to 80 % of IMX219 frames (signal about 17 DN at 8 bit). E3 therefore partly measures the detector, not the modulation.

## E4: traceability (`c2_crc48.csv`, `trow_range.csv`, `seed_sets.csv`, `corner_error.csv`)
- C2 margins with 48-bit CRC match the reviewer's recompute: P33 +148.2 / +116.4 / +61.4, P25 +141.0 / +94.9 / +53.4, P42 +157.8 / +128.4 / +63.0.
- The +148 figure has one value: the sweep seeds give 412.8 vs 264.6, **+148.2 [126.6, 171.6]**. The claims seeds give 402.0 vs 252.0, +150.0 [127.2, 174.0]. The paper must disclose both seed sets.
- t_row sensitivity: **at most 5.16 bps** (CSK802-8, 2.0 m).
- Corner error (IMX174): median 0.02 to 0.03 pitch at 0.5 to 1.5 m, 0.06 at 2 m, 0.09 at 2.5 m, 0.34 at 3 m, 0.31 to 0.43 at 3.25 to 3.5 m.
- The conclusion should mention the 1/256 loss.

## What the paper can honestly claim
On the simulated IMX174 platform at the paper's operating point (fixed 1/1500, 1/128), v2 beats the best baseline at 3.0 to 3.5 m by +61 to +148 bps. This gain comes from data/pilot level design and the 2-level decoder, **not** from layered hierarchy. It is not robust to tuned exposure or 1/256 brightness, and it did not transfer to an IMX219 model. The paper should present hierarchy as a short-range (≤2 m) feature only.

## Caveats
- Single seed set per point, and several CIs are marginal.
- IMX219 QE, CFA and dark current are assumed, and its finder fails often.
- `run_meta_REVIEW_{e1sweep,e1dec,e2_P33,e3valid}.json` record a `-dirty` git state. The working tree then held uncommitted review scripts; simulator modules were unchanged, as the byte-identity checks confirm.

## Remaining (not run)
- E2 at P25 and P42.
- Optional: a second seed set for E1/E2.
