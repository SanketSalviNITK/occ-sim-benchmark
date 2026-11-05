# benchmark-r6 claims: C2 (IMX174), IMX219, sensitivity, geometry, finder, PhyCom baselines, statistics

Simulation only. "Line N" means the line number in the CSV (header = line 1). Margins are paired CRN symbol-bootstrap
means with 95 % CIs. Unless stated: IMX174, P33, brightness 1/128, exposure 1/1500, equal summed drive.
**Canonical seed set for C2: claims/E2** (`docs/BENCHMARK_PROTOCOL.md` item 9). r6 bootstrap: B = 10000, seed 0
(`experiments.r6_report`); r5 used B = 2000. Symbols per point: **1000 eval + 200 tune**.

## C2 (IMX174) — qualitative claims unchanged; Holm softens two narrow 3.5 m positives

**[r7] Superseded:** the r5 C2 wording is no longer the claim text; the claim text is the r7 C2 wording in `CLAIMS_r7.md` (audit §3), also in README/METHODS/SUMMARY. Binding margins on claims/E2 at P33 are reproduced by the
r6 sensitivity default rows and by the PhyCom lineup run (same CRN seeds):

| # | Number | File | Line | Notes |
|---|---|---|---|---|
| a | +150.0 [126.6, 173.4] at 3.0 m vs QCD-style native | results/benchmark/r6/sensitivity_tornado.csv | 2 (default,d3.0); also phycom_margins.csv line 15 | B=10000; r5 was [127.2,174.0] at B=2000 |
| b | +107.58 [86.34, 129.0] at 3.25 m vs Overlay 48-bit | sensitivity_tornado.csv | 24; phycom_margins.csv line 20 | matches r5 +107.6 |
| c | +4.32 [−10.08, 19.08] at 3.5 m vs HNCSM base-only, n.s. | holm_claims.csv / phycom_margins.csv line 25 | — | unchanged verdict |
| Holm | P25/P42 claims/E2 at 3.5 m (+16.56 / +15.00) become **n.s. after Holm** (p_holm 0.28 / 0.33) | holm_claims.csv | rows claim=C2 binding, cond=d3.5, budget 25/42 | family size 56 |

## Sensitivity (Table-2 ASSUMED parameters at C2 points)

One-at-a-time LOW/HIGH levels; paired Δ(binding) vs default on the same CRN symbols.
Source: `results/benchmark/r6/sensitivity_tornado.csv` (+ `.png`/`.pdf`).

| Factor levels that **keep** C2 positive at both 3.0 and 3.25 m | Levels that **flip** C2 to negative (or n.s.) |
|---|---|
| f_number f/1.8; bits 10/12; cfa×0.5; t_row 0/10 µs; f_tx 10/20; reflectance 0.2/0.8; jitter 0/±5 %; brightness 1/64 | f_mm 4/8 mm; f_number f/2.8; focus_m 0.5/2.0 m; brightness 1/256; cfa×2 (n.s. at 3.0 m, negative at 3.25 m) |

**[r7]** lambert_m 0.65/1.56 is listed in neither column: on axis (yaw 0, every C2 run) it has **no effect by construction** (cos^m 0 = 1; arrays identical to default). At 30° yaw it changes no verdict (`r7/lambert_yaw30.csv`).

Largest |Δ| (tornado): f_mm=8 mm (Δ −878.6 at 3.0 m; −378.2 at 3.25 m); focus_m=0.5 m; brightness 1/256; f_number f/2.8.
Optics (focal length, f-number, focus), CFA crosstalk ×2 and deep dimming dominate; ADC bits, t_row, reflectance and
jitter within the stated brackets do not overturn C2.

## Second geometries

`results/benchmark/r6/geometry_binding.csv`

| Geometry | 3.0 m binding | 3.25 m | 3.5 m |
|---|---|---|---|
| 80 mm panel (Nguyen 2021, doi:10.3390/s21093023) | −140.5 [−152.4, −128.1] vs OOK (negative) | −107.6 [−126.5, −88.3] vs OOK (negative) | +84.4 [58.5, 110.8] vs OOK (positive) |
| 65 mm, 30° yaw | +71.4 [48.6, 93.6] vs QCD-style (positive) | −41.0 [−52.4, −28.9] vs HNCSM base-only (negative) | −46.3 [−56.9, −35.2] (negative) |

C2 does **not** transfer unchanged to the 80 mm panel at 3.0/3.25 m (OOK binds and beats v2). At 30° yaw, only 3.0 m stays positive.

## Finder attribution (canonical seeds)

`finder_failure.csv`, `oracle_binding_canonical.csv`. Detection failures = 0 at every point; all finder loss is gross error
(corner error > 0.5 LED pitch). Gross-error frame rates (v2 / QCD-style / v2-base-only): 3.0 m 0.071 / 0.572 / 0.562;
3.25 m 0.166 / 0.706 / 0.712; 3.5 m 0.328 / 0.691 / 0.724. Finder loss (oracle−detector) for v2: 3.0 m +19.8 [−2.4, 41.4];
3.25 m +85.8 [64.2, 107.4]; 3.5 m +211.8 [189.6, 233.4]. Oracle binding on claims/E2: 3.0 m detector +150 / oracle −114 vs OOK
(rank 3); **3.25 m detector +107.6 / oracle −24.0 [−45.0, −3.6] vs QCD-style (rank 2)** — finder attribution now also at 3.25 m;
3.5 m detector +4.3 n.s. / oracle +46.1 [23.9, 68.2] vs Overlay 48-bit.

## Statistics

| Item | Result | File |
|---|---|---|
| Ablation residual bootstrap stability (25 seeds) | 3.0 m +18.6: n.s. on all 25 (B=2k and 10k); 3.25 m +35.4: positive on all 25; 3.5 m +14.4: n.s. on all 25 | ablation_boot_stability_summary.csv |
| Holm–Bonferroni (56-claim family) | 3 of 20 unadjusted positives become n.s. (Holm), incl. IMX219 m3.5 oracle+tuned +23.4 (p 0.0416 → p_holm 0.33) and C2 d3.5 at P25/P42 | holm_claims.csv |

## QCD-OCC validation grid

`qcd_validation_grid.csv` (2.0 m, f_tx=25, 2000 symbols/cell, lux ∈ {27,149,304} × brightness ∈ {1/96…1/256}).
Published BER 1.13e-2 is **not** inside any cell's Monte-Carlo CI. At brightness 1/128, BER ≈ 5.4e-3–6.2e-3 (below published);
at 1/160–1/256 ≈ 1.5e-2 (above); at 1/96 ≈ 1e-4. Honest explanation: Tx brightness is unidentified in the paper protocol,
the camera differs (Logitech C310 vs IMX174 model), and the CIs cover Monte Carlo noise only — not model mismatch.
DataPort (doi:10.21227/j0zd-gq12) is subscription-gated (not downloaded). E-VLC is single bullet-LED + event camera (not used).

## PhyCom baselines (Elsevier Physical Communication)

Plugins in `schemes_contrib/` (labelled **-inspired**, not reproductions); paper lineup untouched.
`phycom_margins.csv` (canonical seeds, P33, 1/1500, 1/128):

| Distance | v2 − CSK-16-inspired (native) | v2 − SM-PAM-inspired (native) | Binding with plugins included |
|---|---|---|---|
| 3.0 m | +402.0 [384.0, 419.4] | +400.4 [382.6, 418.0] | +150.0 vs QCD-style (unchanged) |
| 3.25 m | +234.0 [216.0, 252.0] | +234.0 [216.0, 252.0] | +107.58 vs Overlay 48-bit (unchanged) |
| 3.5 m | +109.8 [95.4, 124.2] | +109.8 [95.4, 124.2] | +4.32 vs HNCSM base-only (n.s.) |

Neither PhyCom baseline becomes the binding comparison at any C2 point.

## IMX219

Qualitative claim unchanged (C1/C2 do not transfer on `imx219f`). The sole r5 exception (matched 3.5 m, oracle + tuned,
+23.4 [1.2, 45.6]) is **n.s. after Holm** (holm_claims.csv). Unadjusted per-comparison CI is unchanged.

## Change log vs r5

| Item | r5 | r6 |
|---|---|---|
| Bootstrap B | 2000 | 10000 (seed 0) in r6 reports |
| Sensitivity / 2nd geometry / finder table | absent (M7 / single geometry / 3.25 m oracle missing) | sensitivity_tornado.*, geometry_binding.csv, finder_failure.*, oracle_binding_canonical.csv |
| Ablation n.s. stability | single B=2000 | 25 seeds × {2000,10000} |
| Multiplicity | none | Holm over 56-claim family |
| QCD-OCC | one point (BER 6.0e-3 vs 1.13e-2) | 15-cell lux×brightness grid + DataPort/E-VLC attempt |
| PhyCom baselines | — | CSK-16-inspired (Singh 2018), SM-PAM-inspired (Leblebici 2026) |
| C2 3.0/3.25 m claim | positive | positive (unchanged); survives ASSUMED brackets except optics (f_mm, f/2.8, focus), cfa×2 and 1/256 (lambert_m untested on axis: no effect by construction) [r7-corrected] |
| IMX219 m3.5 oracle+tuned | +23.4 positive (unadj.) | n.s. after Holm |
| Tests | 85 | see SUMMARY |
| Tag | benchmark-r5 (8886c77a) | benchmark-r6 |

**Holm scope (r7, R4).** The Holm–Bonferroni correction covers only the 56-claim family in `r6/holm_claims.csv`. The following r6/r7 results are **outside the family and are reported unadjusted**: the canonical-seed oracle points at 3.25 and 3.5 m (`oracle_binding_canonical.csv`; in particular the 3.25 m oracle margin −24.0 [−45.0, −3.6] vs QCD-style is **unadjusted**), the geometry runs (`geometry_binding.csv`), the OAT sensitivity runs (`sensitivity_tornado.csv`), the PhyCom plugin margins (`phycom_margins.csv`), the E2 grid cells, and the r7 lambert_m 30° yaw and factorial runs.
