# benchmark-r10 revision results (branch `revision-r10`, local only)

All numbers below are copied from CSV files in `results/r10/` (named in each table or line). All are paired bootstrap results with B = 10000, boot seed 0 and IUT p-values. They are **unadjusted** and sit outside the 56-claim Holm family. The binding margin is the minimum over the comparison set (bench_report.COMP without "QCD-OCC (paper frame)") × {native CRC, 48-bit CRC}. The baseline setting is IMX174 composite preset, P33 (pref 33.011), brightness 1/128 and exposure 1/1500 s, unless a row says otherwise. Options that are off reproduce benchmark-r9 byte for byte (tests/test_r10.py).
Simulation code key: `r10-2258050`. `code_key` is a manual token, set through the `R6_CODE_KEY` environment variable; it is not a git hash. The run metas record git `2258050…-dirty` (c2pwm432, c2pwm2k) or `f5e780a…-dirty` (all other groups). `-dirty` reflects files that were uncommitted when the runs were made (results, and the report script and docs). Provenance (`git diff 2258050 255be2e`): `channel/`, `rx/` and `tx/` are unchanged after 2258050. `experiments/revision_r10.py` changed at f5e780a: groups `c2radiant`, `swdc` and `swgs` and a `_job10` wrapper were added (+26/−3 lines). The original C2 and sweep job definitions (c2pwm432, c2pwm2k, c2quant, c2pwm432q, c2focus3, swpwm432, swpwm2k, swfocus3) are unchanged. Run completeness was checked: every job key in `run_meta_R10_*.json` has an `err` array for all 11 entries, with 1000 eval and 200 tune symbols (radiant: 1000 eval).

Parameter sources and ASSUMED items for PWM and integer codes: `docs/PWM_MODEL.md`.

**All PWM results are model-based simulations, not hardware measurements.** Only the PWM *frequencies* are measured or from datasheets: 432 Hz on original WS2812B and about 2 kHz on WS2812B-V5. The model also assumes the following:
* a linear code-to-duty map (duty = code/255; ASSUMED);
* one phase per LED, redrawn independently each frame (ASSUMED);
* leading-edge-aligned RGB pulses (ASSUMED).

The measured code-to-duty map is darker at low codes, and WS2812C/D parts are reported to emit no light at codes 1–2 (cpldcpu 2020). The simulated 432 Hz and 2 kHz goodputs are therefore, if anything, optimistic at the 1/128 operating point.

Exposure grid vs PWM period:
* **2 kHz** (period 0.5 ms): 1/500 s and 1/250 s are exact integer multiples (4 and 8 periods), so those tuned exposures are flicker-free.
* **432 Hz** (period 2.315 ms): no grid exposure {1/4000, 1/1500, 1/500, 1/250} is a period multiple. The tuned 1/250 s is 1.73 periods. No period-multiple exposure (e.g. 2/432 s or 3/432 s) was tested. Literature search log: `docs/search_log.md`, `docs/literature_search/`.

## 1. C2 cell (IMX174, 3.0 / 3.25 m, claims/E2 seeds), HNCSM v2 binding margin, bps [95% CI]
Source: `c2_r10_binding.csv` (DC control columns `dc_r9_*`: DC finder = `phys_sym/review_e2_P33.npz`, DC oracle = `phys_sym/r6_finder.npz` err_orc; there is no DC oracle-tuned control). Radiant-equal: `radiant_equal_c2_binding.csv`.

| Condition | d | Receiver | Exposure | Margin [CI] | Binding baseline | v2 bps (rank) | Δ vs DC r9 [CI] |
|---|---|---|---|---|---|---|---|
| DC (r9, reproduced) | 3.0 | finder | 1/1500 | +150.0 [126.6, 173.4] | QCD-style native | — | — |
| DC (r9, reproduced) | 3.25 | finder | 1/1500 | +107.58 [86.34, 129.0] | Overlay 48-bit | — | — |
| DC (r9) | 3.0 / 3.25 | finder | tuned | −69.0 [−88.8, −49.2] / −65.4 [−89.4, −40.2] | QCD-style | — | — |
| DC (r9) | 3.0 / 3.25 | oracle | 1/1500 | −114.06 [−141.9, −86.64] / −24.0 [−45.0, −3.6] | OOK / QCD-style | — | — |
| **PWM 432 Hz** | 3.0 | finder | 1/1500 | **−0.54 [−0.90, −0.24]** | Overlay | 0.0 (5) | −150.54 [−174.0, −127.26] |
| PWM 432 Hz | 3.0 | finder | tuned | +16.2 [−9.0, 41.4] n.s. | QCD-style | 254.4 (1) | +85.2 [55.2, 115.8] |
| PWM 432 Hz | 3.0 | oracle | tuned | +31.8 [20.4, 43.2] | QCD-style | 583.2 (1) | — |
| **PWM 432 Hz** | 3.25 | finder | 1/1500 | **−0.66 [−1.08, −0.30]** | Overlay | 0.0 (5) | −108.24 [−127.08, −85.38] |
| PWM 432 Hz | 3.25 | finder | tuned | −3.84 [−18.24, 10.32] n.s. | v1 base-only | 106.8 (3) | +61.56 [30.48, 88.68] |
| PWM 432 Hz | 3.25 | oracle | tuned | +100.8 [82.2, 120.0] | QCD-style | 534.0 (1) | — |
| **PWM 2 kHz** | 3.0 | finder | 1/1500 (also v2's tuned pick) | **+31.8 [7.8, 56.4]** | QCD-style | 324.6 (1) | −118.2 [−148.2, −87.6] |
| PWM 2 kHz | 3.0 | oracle | 1/1500 | −96.9 [−124.8, −68.64] | OOK | 328.2 (2) | +17.16 [−10.74, 48.0] |
| PWM 2 kHz | 3.0 | oracle | tuned | +1.8 [−1.8, 5.4] n.s. | QCD-style | 598.2 (1) | — |
| **PWM 2 kHz** | 3.25 | finder | 1/1500 | **+34.2 [12.0, 55.8]** | QCD-style | 163.8 (1) | −73.38 [−99.9, −44.52] |
| PWM 2 kHz | 3.25 | finder | tuned | −11.4 [−33.0, 9.6] n.s. | QCD-style | 118.2 (2) | +54.0 [22.2, 85.2] |
| PWM 2 kHz | 3.25 | oracle | 1/1500 / tuned | +4.8 [−16.2, 27.0] n.s. / +78.0 [62.4, 93.6] | QCD-style | 218.4 / 573.0 | — |
| **Integer codes, 1/128** | 3.0 | finder | 1/1500 | **+28.8 [8.4, 49.2]** | v2-CS | 405.6 (1) | −121.2 [−147.6, −95.4] |
| Integer codes, 1/128 | 3.0 | finder | tuned | −55.8 [−75.6, −36.0] | QCD-style | 422.4 (2) | +13.2 [−4.21, 31.2] |
| Integer codes, 1/128 | 3.0 | oracle | 1/1500 / tuned | −121.62 [−148.68, −94.44] / −1.8 [−4.2, 0.0] n.s. | OOK / QCD-style | — | — |
| **Integer codes, 1/128** | 3.25 | finder | 1/1500 | **+47.4 [25.2, 69.0]** | v2-CS | 234.0 (1) | −60.18 [−81.6, −34.92] |
| Integer codes, 1/128 | 3.25 | finder | tuned | −42.6 [−67.8, −16.8] | QCD-style | 301.8 (2) | +22.8 [1.2, 44.4] |
| Integer codes, 1/256 | 3.0 | finder | 1/1500 | −347.52 [−365.7, −329.28] | QCD-style | 1.68 (3) | −277.92 vs DC 1/256 (−69.6) |
| Integer codes, 1/256 | 3.25 | finder | 1/1500 | −187.02 [−204.6, −169.92] | QCD-style | 3.78 (3) | −115.62 vs DC 1/256 (−71.4) |
| PWM 432 Hz + integer codes | 3.0 | finder | 1/1500 / tuned | −0.84 [−1.32, −0.42] / −22.2 [−46.2, 2.4] n.s. | Overlay / QCD-style | 0.0 / 252.0 | — |
| PWM 432 Hz + integer codes | 3.25 | finder | 1/1500 / tuned | −0.90 [−1.38, −0.48] / +3.96 [−10.32, 18.24] n.s. | Overlay / v1 base-only | 0.0 / 104.4 | — |
| PWM 432 Hz + integer codes | 3.25 | oracle | tuned | +44.4 [28.2, 61.2] | QCD-style | 538.8 (1) | — |
| **Focus 3.0 m** | 3.0 | finder | 1/1500 | **−33.66 [−54.6, −13.08]** | OOK 48-bit | 156.0 (4) | −183.66 [−215.04, −156.9] |
| Focus 3.0 m | 3.0 | finder | tuned | −45.24 [−69.48, −21.18] | OOK | 156.0 (4) | — |
| Focus 3.0 m | 3.0 | oracle | tuned | +28.8 [9.0, 48.6] | QCD-style | 493.8 (1) | — |
| **Focus 3.0 m** | 3.25 | finder | 1/1500 | **−61.44 [−71.28, −51.12]** | v1 base-only | 46.8 (6) | −169.02 [−189.18, −144.96] |
| Focus 3.0 m | 3.25 | oracle | tuned | +128.4 [106.8, 150.6] | QCD-style | 334.8 (1) | — |
| **Radiant-equal** (1000 symbols) | 3.0 | finder | 1/1500 | **+147.0 [123.6, 170.4]** | QCD-style native | 399 (1) | −3.0 [−12.0, 6.0] vs summed-drive |
| **Radiant-equal** (1000 symbols) | 3.25 | finder | 1/1500 | **+107.82 [86.52, 129.42]** | Overlay 48-bit | 229 (1) | +0.24 [−14.88, 11.88] |

Per-entry goodputs and rankings: `c2_r10_goodput.csv`, `c2_r10_rankings.csv`, `radiant_equal_c2_goodput.csv`.

**Why PWM at 432 Hz kills the 1/1500 links (in the ASSUMED model).** At 1/128 the largest latched code is 2 of 255 (`ws2812b_codes_at_P33.csv`, column `max_code_continuous`, e.g. QCD-style 1.5658). That gives an on-time per 2.31 ms PWM period of at most 18.1 µs for v2 and 14.2 µs for QCD-style and v2-CS (`on_time_us_432Hz_at_max`), while the exposure is 667 µs. Each row therefore catches either a full pulse or nothing. With random per-LED phases, symbols cannot be decoded: finder goodput is ≈0 for every entry and the gross-frame rate is 0.787 for v2 (`c2_r10_goodput.csv`, `gross_frame`). Longer tuned exposures (≥1/500 s) recover part of the link.

## 2. WS2812B codes at P33 (`ws2812b_codes_at_P33.csv`)
At 1/128 every entry uses codes ≤ 2 (column `codes_used`: subsets of {0, 1, 2}). The share of lit channels rounded to 0 is v2-CS 0.4633, CSK802-8 0.53, CSK802-4 0.40 and Overlay 0.494 (column `share_lit_channels_rounded_to_0`). At 1/256, 7 of 11 entries round to all-zero codes and emit no light: v1 base-only, CSK802-8, CSK802-4, OOK, QR, Nested and Overlay. Only v2 (codes 0/1), v2-CS, v1 and QCD-style still emit.

## 3. All-entry goodput vs distance (IMX174, P33, 1/1500, sweep seeds)
* DC: `all_entry_table_detector.csv` (shared finder), `all_entry_table_oracle.csv`, `all_entry_table_finder_bad_frame.csv`, `all_entry_finder_rates_claims_seeds.csv`, `all_entry_distance_long.csv`. Figure: `fig_all_entry_distance.pdf/png` (finder and oracle panels plus finder error rates). The finder data are byte-identical to `sweeps_PHYS_P33.npz` (asserted).
  v2 finder bps: 1.0 m 1020.0, 2.0 m 694.1, 2.5 m 592.1, 3.0 m 412.8, 3.25 m 242.4, 3.5 m 133.2, 4.0 m 30.6.
* PWM 432 Hz / PWM 2 kHz / focus 3.0 m: `sweeps_r10_long.csv` (627 rows = 3 options × 19 distances × 11 entries), `sweep_table_{PWM432Hz,PWM2kHz,focus3p0m}_{detector,oracle}.csv`, `fig_all_entry_distance_{swpwm432,swpwm2k,swfocus3}.pdf/png`. v2 binding per distance: `sweeps_r10_v2_binding.csv` (114 rows).
  * PWM 432 Hz (`sweeps_r10_long.csv`, option `PWM 432 Hz`; the 9-column `sweep_table_PWM432Hz_detector.csv` starts at 1.0 m): with the shared finder every entry scores ≤1.20 bps over 0.5–5 m. The maximum is HNCSM at 0.5 m; HNCSM base-only scores 0.96 at 0.5 m. From 0.75 to 5 m every entry is ≤0.78 bps. With oracle corners every entry is ≤1.98 bps (Overlay, 2.25 m). v2 scores 0 at every distance and has no positive margin anywhere with either receiver.
  * PWM 2 kHz: v2 finder bps at 1.0 / 3.0 / 3.25 m are 594.0 / 326.4 / 174.0 (cap 1020). Overlay drops to 53.5 at 3.0 m and CSK802-8 to 103.2 at 1.0 m. The v2 finder margin is positive only at 3.0 m (+26.4 [1.8, 51.0]) and 3.25 m (+46.8 [24.6, 69.6]). The oracle margin is positive at 3.25 m (+28.2 [6.6, 49.81]) and 3.5 m (+43.2 [21.6, 64.8]).
  * Focus 3.0 m: v2 finder bps 153.0 at 3.0 m and 51.0 at 3.25 m. No positive v2 margin at any distance with either receiver (3.0 m finder −33.9 [−50.7, −17.7]).

## 4. Rolling shutter on vs off (t_row = 27.4 µs vs 0), 11 entries × 19 distances (`rs_vs_global_sweep.csv`, `rs_vs_global_summary.csv`, `rs_vs_global_v2_binding.csv`)
* Largest |rolling − global| difference: **10.32 bps [−20.64, −2.58]** (CSK802-8, 1.75 m). 5 of 209 cells are significant (unadjusted): CSK802-8 1.75 m; HNCSM 2.25 m −1.92; OOK 2.25 m −3.90; QCD-style 2.25 m −4.20; v2-CS 2.5 m −2.40. The largest |difference| per distance is ≤3.0 bps at 2.75–5 m and 0 at ≤1.25 m.
* v2 binding margin, rolling vs global: 3.0 m +148.2 [125.4, 171.6] vs +150.0 [127.2, 173.4]; 3.25 m +116.4 vs +116.04; 3.5 m +28.56 vs +28.92.

## 5. Rmax (`rmax_table.csv`; (bits/symbol − 8 CRC bits per layer) × 15 symbols/s, camera 30 fps)
This is a correction to the paper's table. The native values are identical to `R_max` in r9 `results/benchmark/r6/finder_failure.csv`. The 48-bit column uses the existing 48-bit CRC convention, which can exceed native for Nested and Overlay.
Native / 48-bit: v2-CS 1560/1440, v2 1020/1020, HNCSM v1 960/960, v1 base-only 120/120, CSK802-8 2580/2220, CSK802-4 1680/1440, OOK 780/660, QR 300/300, Nested 240/360, QCD-style 600/600, Overlay 300/420 (QCD-OCC paper frame, not in the comparison set: 2040/1800).

## 6. Pixels per LED and blur/pitch (`px_per_led_blur.csv`)
* IMX174 (focus 1.0 m): 2.0 m 4.16 px/LED, blur 1.55 px (0.372 pitch); 3.0 m 2.77, 2.06 (0.743); 3.25 m 2.56, 2.14 (0.836); 3.5 m 2.38, 2.21 (0.929).
* IMX174 focus 3.0 m: blur 0 at 3.0 m and 0.079 px at 3.25 m.
* IMX219 (focus 2.0 m): 3.0 m 7.35 px/LED, blur 0.69 px (0.094); 3.25 m 6.79, 0.79 (0.117).

## 7. Figures at B = 10000
* Fig 1: `fig1_binding_margins_B10000.csv/.pdf/.png`. P33 claims: 3.0 m +150.0 [126.6, 173.4]; 3.25 m +107.58 [86.34, 129.0]; 3.5 m +4.32 [−10.08, 19.08] n.s. Binding baselines are the same as at B = 2000 (column `B2000_*`). The largest CI-bound shift from B = 2000 to B = 10000 is 1.8 bps.
* Fig 6 (IMX219): `fig6_imx219_B10000.csv/.pdf/.png`. All 32 rows match `derived/imx219_binding_B10000.csv` to its 0.1-bps rounding (columns `derived_*`). For example, real finder d2.5 fixed is −1273.62 [−1322.64, −1222.02] (CSK802-8).
* Fig 2 (readable factorial heatmap): `fig2_factorial_heatmap.pdf/png`, counts `fig2_factorial_counts.csv`. 3.0 m: 1 positive / 34 negative / 1 n.s. 3.25 m: 1 / 35 / 0.
* Radiant-equal full-range table (old 500-symbol run): `radiant_equal_long.csv`, `radiant_equal_table.csv`.

## 8. Paper conclusions that change
1. **C2 depends on the DC-emitter assumption (model-based; see the qualifier above).** Under the ASSUMED PWM model at the measured 432 Hz frequency (original WS2812B), with the paper's 1/1500 s exposure and brightness 1/128, every entry's simulated goodput collapses to ≤1.20 bps (shared finder) or ≤1.98 bps (oracle corners) over 0.5–5 m.
   * The C2 margins at 3.0 and 3.25 m become −0.54 [−0.90, −0.24] and −0.66 [−1.08, −0.30]. No distance gives v2 a positive margin.
   * Among the tested tuned exposures, the longest (1/250 s, 1.73 periods, not a period multiple) leaves the finder C2 margin non-significant: +16.2 [−9.0, 41.4] and −3.84 [−18.24, 10.32].
   * At 2 kHz (WS2812B-V5) and **the paper's fixed 1/1500 s exposure**, the shared-finder C2 margin stays positive but smaller: +31.8 [7.8, 56.4] at 3.0 m and +34.2 [12.0, 55.8] at 3.25 m, versus +150.0 and +107.58 under DC.
   * That 2 kHz result is not robust to per-scheme tuned exposure. At 3.25 m the margin is −11.4 [−33.0, 9.6] n.s. and v2 ranks 2nd. At 3.0 m v2 keeps 1/1500 s and the margin stays at +31.8.
   * At 2 kHz the 1/500 and 1/250 s exposures are flicker-free period multiples.
   * If V5 parts share the WS2812C/D no-output-at-codes-1–2 behaviour, the 2 kHz operating point at 1/128 would be dark.
2. **Integer drive codes at 1/128 shrink C2 to +28.8 / +47.4 bps** (v2-CS becomes the binding baseline). At 1/256, 7 of 11 entries emit no light and v2 also collapses. The 1/256 sensitivity rows are therefore an artefact of continuous drive.
3. **Focus at 3.0 m reverses C2** (−33.66 at 3.0 m, −61.44 at 3.25 m; v2 ranks 4th/6th). The C2 win therefore depends on the default 1.0 m focus. At 3.0 m that focus gives a 2.06 px blur on a 2.77 px LED pitch (`px_per_led_blur.csv`), and this blur hurts the competitors more than v2 (interpretation; the mechanism was not isolated).
4. Detector and exposure choice can decide the sign, depending on the condition:
   * **Oracle corners, tuned exposure:** the margin is positive under PWM 432 Hz (+31.8 / +100.8), PWM 2 kHz at 3.25 m (+78.0) and focus 3 m (+28.8 / +128.4). PWM 2 kHz at 3.0 m is +1.8 n.s.
   * **Shared finder, fixed 1/1500 s:** the margin is negative under PWM 432 Hz (−0.54 / −0.66) and focus 3 m (−33.66 / −61.44), but positive under PWM 2 kHz (+31.8 / +34.2).
5. **Rmax is a paper-table correction, not a change in r9 physics** (Section 5). The native values are the same as the `R_max` column already shipped in r9 `results/benchmark/r6/finder_failure.csv`. The paper's Table 2 must use them (CSK802-8 2580, CSK802-4 1680, v2 1020, v2-CS 1560) and add the 48-bit column; `rmax_table.csv` is the repo-traceable table.
6. **Rolling-shutter statement:** replace "≤5.2 bps" (old 12-scheme line-up, 2.0/2.5 m) with "≤10.3 bps (CSK802-8, 1.75 m) over 11 entries × 19 distances; ≤3.0 bps at 2.75–5 m; v2 margins at C2 change by ≤1.8 bps".
7. Unchanged: radiant-equal leaves C2 intact (Δ −3.0 / +0.24 bps, 1000 symbols, B = 10000). Fig 1 and Fig 6 at B = 10000 give the same signs and baselines as at B = 2000.
