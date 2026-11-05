# benchmark-r6 summary (simulation only; local release candidate, not published)

> **Claims status:** qualitative C2 (IMX174) and IMX219 claims are unchanged from r5. r6 adds a Table-2 ASSUMED
> sensitivity study, a second panel geometry + yaw geometry, finder failure attribution (incl. 3.25 m oracle),
> ablation bootstrap-seed stability, Holm–Bonferroni over the claim family, a QCD-OCC validation grid, and two
> PhyCom-inspired plugin baselines. Holmed IMX219 m3.5 oracle+tuned is n.s. Sourced numbers and change log:
> `CLAIMS_r6.md` (r5 artefact kept as `CLAIMS_r5.md`).

Branch `benchmark`. Tests: 91 pass. Default IMX174 path kept byte-identical (plugins and r6 groups are additive;
`lineup_r1` unchanged). r6 bootstrap B = 10000, seed 0; 1000 eval + 200 tune symbols per point.

## Oracle (genie) corners vs detector — `oracle_vs_detector*.csv`, `oracle_ranking.csv`
IMX174 P33, 1–4 m (default 1/1500), mean over 7 points: v2 detector 554 → oracle 597 bps (detector loss 42, modulation loss 423);
QCD-style-inspired 393 → 506 (113 / 94); OOK 465 → 522; Overlay-inspired 195 → 238; v2-base-only 388 → 501.
Claims conditions (d2.5/d3.0/yaw70/blur4), fixed: v2 460 → 560; QCD-style-inspired 424 → 579 (detector share 0.9); OOK 328 → 644.
Oracle-corner paired margins (`oracle_pairs.csv`, v2 − X, both with oracle corners, P33, 1/1500, 1/128): at 3.0 m v2 is below OOK-8x8
(claims/E2 seeds −114.1 [−141.8, −87.2]; sweep seeds −121.3 [−148.6, −94.7]) and QCD-style-inspired (claims −101.4 [−121.8, −80.4]; sweep −95.4 [−117.6, −73.8]),
i.e. 3rd among comparison schemes (4th if the v2-base-only ablation is counted), so the 3.0 m advantage comes from how reliably the shared
finder locates v2 frames, not from demodulation. At 3.5 m (sweep seeds only) v2 leads every comparison scheme with oracle corners: binding
+36.8 [12.8, 60.7] vs Overlay-inspired (48-bit); +44.4 [24.6, 64.8] vs QCD-style-inspired (native).
**3.25 m oracle on claims/E2 is now in `r6/oracle_binding_canonical.csv` (r6):** detector +107.6 / oracle −24.0 vs QCD-style (rank 2). The finder is shared across schemes; a bias toward schemes whose edge LEDs are always lit is suspected, not shown.
IMX219 (current preset imx219f, photometrically uncalibrated; scale-free finder): detector ≈ oracle (v2 697 vs 714; CSK802-8 827 vs 818): detector loss is small after R1.

## Claims wording (benchmark-r5; sources and change log: `CLAIMS_r5.md`)
**C2 (IMX174), canonical seed set claims/E2:**
> "At the fixed operating point (IMX174, P33, brightness 1/128, exposure 1/1500) and with the benchmark's shared corner finder, on the canonical claims/E2 seed set the binding margin of v2 over every comparison scheme × {native, 48-bit} is +150.0 [127.2, 174.0] bps at 3.0 m (vs QCD-style-inspired, native) and +107.6 [85.2, 128.8] bps at 3.25 m (vs Overlay-inspired, 48-bit). At 3.5 m it is not significant (+4.3 [−10.1, 19.3] bps vs HNCSM v1-base). On three further disjoint seed sets (run_phys sweep, A, B) the margins are 148.2–166.2 bps at 3.0 m and 116.4–123.2 bps at 3.25 m, with every CI above 0 (lowest lower bounds 126.6 and 94.4). At 3.5 m they are 28.2–34.3 bps (lower bounds 13.1–19.0), so the 3.5 m result depends on the seed set and is not claimed. At P25 and P42 (claims/E2 seeds) the 3.0 and 3.25 m margins are positive, and the 3.5 m margin is only narrowly positive (+16.6 [1.2, 32.6] and +15.0 [0.6, 29.9]). No C2 point survives the E2 grid (per-scheme tuned exposure, brightness 1/64–1/256) at P25, P33 or P42. With oracle corners on the same claims/E2 seeds, v2 is significantly below OOK-8x8 at 3.0 m (−114.1 [−141.8, −87.2] bps) and below QCD-style-inspired (−101.4 [−121.8, −80.4]); it is 3rd among the comparison schemes. The 3.0 m advantage therefore comes from how reliably the shared finder locates v2 frames, not from demodulation. Oracle corners at 3.5 m were run only on the sweep seeds. There v2 exceeds every comparison scheme, with a binding margin of +36.8 [12.8, 60.7] bps vs Overlay-inspired (48-bit) and +44.4 [24.6, 64.8] bps vs QCD-style-inspired (native). 3.25 m was not run with oracle corners."

**C1/C2 on IMX219** (C1 = audit-2 claim: at 2.5 m, 1/1500, 1/128, v2 exceeds the IEEE 802.15.7 CSK baselines, README "[SUPERSEDED] Claims"; C2 = the IMX174 claim above):
> "C1 here means the audit-2 claim that at 2.5 m (1/1500 s, brightness 1/128) v2 exceeds the IEEE 802.15.7 CSK baselines; C2 means the IMX174 binding-margin claim at 3.0–3.5 m above. On the IMX219 preset `imx219f` (sourced geometry and noise, uncalibrated photometric scale), neither transfers. At the same distances (2.5, 3.0, 3.25 and 3.5 m), v2 is significantly below the binding baseline at every point, with fixed or tuned exposure and with the scale-free finder or oracle corners. Examples: 2.5 m, −1273.6 [−1322.6, −1222.0] bps vs genie(CSK802-8); 3.0 m, −999.6 [−1009.9, −985.3] bps vs QCD-OCC (paper frame), and −991.4 [−1005.7, −977.2] with oracle corners. At matched pixels-per-LED v2 is significantly below at 2.5–3.25 m with both finders (e.g. matched 3.0 m: −57.0 [−75.6, −38.4] vs QCD-style-inspired). At matched 3.5 m the result is not significant (+13.2 [−11.4, 36.0] with the scale-free finder; +0.6 [−23.4, 24.6] with oracle corners at fixed exposure). The one exception is oracle corners with tuned exposure (+23.4 [1.2, 45.6]). These are simulation results on an uncalibrated preset and say nothing about real IMX219 hardware."

IMX219 scope: all IMX219 results use the current preset (`imx219f`), photometrically uncalibrated (sourced geometry and noise). Matching the measured CQ sensitivity would need an effective QE of 1.5–2.16 (impossible as QE); those ×3-QE runs are not shipped. The published QCD-OCC BER is matched by this preset near Tx brightness 1/2048, not the 1/128 used in E3.

**Ablation (R3/N4):** lit0.75 recovers 75.6 / 42.6 / 33.8 % and lit0.75 + 2-level decoder 88.6 / 72.7 / 82.4 % of the v2 − base-only gap (3.0 / 3.25 / 3.5 m). A significant residual of +35.4 [13.2, 58.2] bps remains at 3.25 m; the decoder gain is larger on the 0.75-level Tx (interaction), so the shares are not additive. Radiant-equal power: same within 1.2 bps (scales equal to 3e-4).

Not claimed: that v2's modulation outperforms at 3.0 m; any robust or unqualified C2; that C1/C2 fail on real or calibrated IMX219 hardware.

## IMX219 (R1) — `e3_claims.csv`, `e3_validation.csv`, `docs/IMX219_PARAMETERS.md`
Finder gross error 0.000 at 0.5–5 m (was 0.60–0.83). m3.5: n.s. with the real finder; with genie corners n.s. fixed, v2 > all tuned (+23.4 [1.2, 45.6]).

## Binding margins (R2) — `c2_binding_margins.csv` (min over all baselines × {native, 48-bit}, 1/128, fixed 1/1500)
| P | seeds | 3.0 m | 3.25 m | 3.5 m |
|---|---|---|---|---|
| 25 | claims/E2 | +133.2 [109.2, 157.2] | +80.5 [58.5, 102.8] | +16.6 [1.2, 32.6] |
| 25 | sweep | +141.0 [118.8, 163.2] | +94.9 [73.3, 116.1] | +21.4 [7.3, 37.2] |
| 33 | **claims/E2 (canonical)** | **+150.0 [127.2, 174.0]** | **+107.6 [85.2, 128.8]** | **+4.3 [−10.1, 19.3] n.s.** |
| 33 | sweep (robustness) | +148.2 [126.6, 171.6] | +116.4 [94.4, 139.2] | +28.6 [13.9, 45.0] |
3.5 m binding baseline is v1-base (HNCSM base-only); its significance depends on the seed set → downgraded.

## E2 robustness (R4) — `results/review_r1/e2_survival.csv`, `e2_robust.csv`
E2 survival compares v2 with the baselines only (the binding margin also includes the v1 family and v2-CS). No C2 point survives the grid at P25 or P33. P25 min lower bounds: −103.2 (3.0 m), −81.6 (3.25 m), −12.0 (3.5 m).
P33 (claims/E2): 3.0/3.25 m reverse significantly (fixed 1/256: −69.6 [−89.4, −48.6] / −71.4 [−97.2, −47.4]; 3.0 m also tuned 1/128: −69.0 [−88.8, −48.0]; `e2_robust.csv` rows 46, 58, 44).
(r5 fix: r2–r4 printed −61.8 [−82.8, −40.2] here, which is the **P25** 3.0 m tuned 1/128 row, `e2_robust.csv` row 8.) **3.5 m: "not significant", not reversed**
(P25 worst +10.8 [−12.0, 36.0]; P33 worst n.s.).
P42 (run): no point survives either; min lower bounds −78.6 (3.0 m), −84.6 (3.25 m), −19.8 (3.5 m). Significant reversals only with
tuned exposure (3.0 m tuned 1/128 −60.0 [−78.6, −39.6], tuned 1/256 −42.0 [−63.6, −19.8]; 3.25 m tuned 1/128 −58.8 [−84.6, −34.2]);
3.5 m worst cases n.s. (tuned 1/128 +4.2 [−19.8, 27.6]; fixed 1/256 +7.8 [−14.4, 28.8]).
P42 binding margins (fixed 1/1500, 1/128): claims seeds +156.6 / +119.6 / +15.0 [0.6, 29.9]; sweep seeds +157.8 / +117.7 / +29.8 [15.0, 46.1].

## Ablation (R3, R8) — `ablation_factorial.csv`
P33, equal summed drive: share of v2−base-only gap recovered by lit0.75: 75.6 / 42.6 / 33.8 % (3.0/3.25/3.5 m);
lit0.75 + 2-level decoder: 88.6 / 72.7 / 82.4 %. Residual v2 − (lit0.75+2lv): +18.6 [−0.6, 38.4] n.s., +35.4 [13.2, 58.2],
+14.4 [−4.2, 34.8] n.s. Decoder effect on lit0.75 Tx: +21.0/+39.0/+39.6 (sig.); on lit1.0 Tx: +15.6/+29.4/+17.4.
Attribution: "power/level allocation under equal-summed drive + decoder"; significant residual +35.4 [13.2, 58.2] at 3.25 m; decoder × level interaction, shares not additive. Radiant-equal: same within 1.2 bps (scales equal to 3e-4).

## Seed replication (R5) — `seed_replication.csv`, `seed_spread.csv`
Three disjoint seed sets (claims/E2 + A = 31415926 + B = 27182818, each with own tuning seeds; E1 lit0.75 cells on A, B only).
C2 binding margin (fixed 1/1500, 1/128), mean [min, max] over sets: P25 151.0 [133.2, 165.6] / 83.4 [71.5, 98.2] / 24.8 [16.6, 35.5];
P33 160.2 [150.0, 166.2] / 116.1 [107.6, 123.2] / 22.3 [4.3, 34.3]; P42 170.2 [156.6, 177.0] / 125.2 [119.6, 131.8] / 19.8 [15.0, 24.0]
(3.0 / 3.25 / 3.5 m). Max spread 32.4 bps. All E1 decomposition contrasts at P33 are positive on every set (v2 − base-only 175/133/75).
**Downgraded (CI not of one sign across sets):** (1) P33 3.5 m C2 margin (lo −10.1 on the claims set) → "not significant at P33";
(2) P33 3.0 m E2 tuned 1/256 reversal (hi +1.2 on one set) → "not robust", not "reverses"; (3) all P33 3.5 m E2 cells stay "n.s.".
Robust across sets: C2 at 3.0/3.25 m (all P), 3.5 m at P25/P42 (narrowly, min lo 1.2 / 0.6); P33 reversals at 3.0 m
(fixed 1/256, tuned 1/128) and at 3.25 m (all three E2 cells).

## Runtimes — `runtime.csv`, `runtime_hw.json` (n = 40 symbols, single process, OMP=1, **machine load ≈ 64 on 8 vCPU: inflated**)
IMX174 mean 20.7 ms/symbol (10.4–29.5), IMX219 28.7 (19.9–57.5); the corner finder is the largest stage for v2 (≈7 ms).

## R9 — run metas (updated r5)
All claim-backing REVIEW metas are now from clean commits: e3valid, e1dec, e1sweep, e2_P33 at 83b67a7 (r2/r4, arrays identical),
idcheck at 231abcb (r5, arrays identical). The dirty originals are kept as `run_meta_REVIEW_*_orig_dirty.json`.
(The r2 text here said e1sweep/e1dec/e2_P33 still carried -dirty hashes; that was superseded at r2/r4.)

## benchmark-r6 additions — `results/benchmark/r6/`
- Sensitivity tornado (`sensitivity_tornado.*`): C2 survives Lambertian/bits/t_row/f_tx/reflectance/jitter/1/64;
  flips negative under f_mm 4–8, f/2.8, focus 0.5/2.0 m, brightness 1/256.
- Geometry (`geometry_binding.csv`): 80 mm panel loses C2 at 3.0/3.25 m (OOK binds); 30° yaw keeps only 3.0 m positive.
- Finder (`finder_failure.*`): zero detection failures; gross-error rates drive finder loss; attribution holds at 3.25 m.
- Stats: ablation n.s. stable on 25 seeds; Holm flips 3 unadjusted positives (incl. IMX219 m3.5 oracle+tuned).
- QCD-OCC grid (`qcd_validation_grid.csv`): no cell CI contains published 1.13e-2; brightness unidentified + camera mismatch.
- PhyCom plugins (`phycom_margins.csv`): CSK-16-inspired (Singh 2018) and SM-PAM-inspired (Leblebici 2026) are both well
  below v2 at C2; binding baseline unchanged.
