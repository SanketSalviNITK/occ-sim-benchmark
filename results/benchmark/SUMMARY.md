# benchmark-r8 summary (simulation only; local release candidate, not published)

> **Claims status (r8):** the C2 (IMX174) wording is the strictly scoped §3 wording of the r7 audit (1/36 factorial cells, relative only,
> σ_mult results quoted). **r7:** the wording was rewritten (r6 audit, §3): it then carried the optics,
> geometry, CFA and Holm conditionality, the four-seed-set minimum, the canonical 3.25/3.5 m oracle points, and B = 10000
> CIs. r7 also re-runs lambert_m at 30° yaw, adds a 36-cell optics × brightness factorial at the C2 points, a QCD-OCC BER
> plateau diagnostic, the Holm scope statement and a provenance note. IMX219 claims unchanged (m3.5 oracle+tuned n.s. after
> Holm). Sourced numbers and change log: `CLAIMS_r7.md` (`CLAIMS_r6.md`, `CLAIMS_r5.md` kept as artefacts).

Branch `benchmark`. Tests: 107 pass (benchmark-r8; r7: 97). Default IMX174 path kept byte-identical (plugins and r6 groups are additive;
`lineup_r1` unchanged). r6 bootstrap B = 10000, seed 0; 1000 eval + 200 tune symbols per point.

## Oracle (genie) corners vs detector — `oracle_vs_detector*.csv`, `oracle_ranking.csv`
IMX174 P33, 1–4 m (default 1/1500), mean over 7 points: v2 detector 554 → oracle 597 bps (detector loss 42, modulation loss 423);
QCD-style-inspired 393 → 506 (113 / 94); OOK 465 → 522; Overlay-inspired 195 → 238; v2-base-only 388 → 501.
Claims conditions (d2.5/d3.0/yaw70/blur4), fixed: v2 460 → 560; QCD-style-inspired 424 → 579 (detector share 0.9); OOK 328 → 644.
Oracle-corner paired margins (`oracle_pairs.csv`, v2 − X, both with oracle corners, P33, 1/1500, 1/128): at 3.0 m v2 is below OOK-8x8
(claims/E2 seeds −114.1 [−141.8, −87.2]; sweep seeds −121.3 [−148.6, −94.7]) and QCD-style-inspired (claims −101.4 [−121.8, −80.4]; sweep −95.4 [−117.6, −73.8]),
i.e. 3rd among comparison schemes (4th if the v2-base-only ablation is counted), so the 3.0 m advantage comes from how reliably the shared
finder locates v2 frames, not from demodulation. At 3.5 m v2 leads every comparison scheme with oracle corners: sweep seeds binding
+36.8 [12.8, 60.7] vs Overlay-inspired (48-bit), +44.4 [24.6, 64.8] vs QCD-style-inspired (native); canonical claims/E2 seeds (r6) +46.1 [23.9, 68.2] vs Overlay-inspired (48-bit).
**3.25 m oracle on claims/E2 is now in `r6/oracle_binding_canonical.csv` (r6):** detector +107.6 / oracle −24.0 vs QCD-style (rank 2). The finder is shared across schemes; a bias toward schemes whose edge LEDs are always lit is suspected, not shown.
IMX219 (current preset imx219f, photometrically uncalibrated; scale-free finder): detector ≈ oracle (v2 697 vs 714; CSK802-8 827 vs 818): detector loss is small after R1.

## Claims wording (C2: benchmark-r8, IMX219: benchmark-r5; sources and change log: `CLAIMS_r7.md`)
**C2 (IMX174), strictly scoped wording (benchmark-r8; audit r7 §3 wording, replaces the r7 wording; canonical seed set = claims/E2, protocol item 9; CIs B = 10000, bootstrap seed 0; sources: `results/benchmark/CLAIMS_r7.md`, `results/benchmark/r6/*.csv`, `results/benchmark/r7/factorial_binding.csv`, `results/benchmark/r8/mult_binding.csv`). C2 is reported only as a case study of benchmark sensitivity — how a ranking hinges on optics and receiver front-end assumptions — not as evidence that v2 outperforms:**
> "In one assumed configuration — IMX174 model, P33, brightness 1/128, exposure 1/1500, ASSUMED lens f = 6 mm, f/2.0 focused at 1.0 m, 65 mm 8×8 panel on axis, shared corner finder, canonical seeds — HNCSM v2 has the highest simulated goodput at 3.0 m and 3.25 m (binding margin +150.0 [126.6, 173.4] and +107.6 [86.3, 129.0] bps). This is not a robust result: in a 36-cell factorial over focus, focal length, f-number and brightness it holds only in this default cell (1/36 at each distance), and it disappears under an 80 mm panel, under 30° yaw at 3.25 m, under CFA crosstalk ×2 and under per-scheme tuned exposure. With oracle corners v2 is not first at 3.0 or 3.25 m, so the difference reflects how reliably the shared finder locates v2 frames, not demodulation. The comparison is relative only: the noise model omits a signal-dependent (multiplicative) term that external anchors show is needed for absolute BER (validation-r0), and with σ_mult = 0.15 (the A2 one-point fit; per-pixel, redrawn every frame) the margin is +100.8 [76.8, 124.8] bps at 3.0 m and +97.8 [74.4, 121.2] bps at 3.25 m (per-frame colour gain: +114.0 [90.6, 137.4] / +96.0 [72.6, 119.4]; σ_mult = 0.024, the A3 fit: +153.0 [129.6, 176.4] / +113.5 [92.2, 134.9], per-pixel). No claim is made for real hardware or for other optics."

Supporting statistics (outside the quote): across all four seed sets the minimum margin is +148.2 (3.0 m) and +107.6 (3.25 m), Holm-significant in the 56-claim family; 3.5 m is not claimed (canonical +4.3 [−10.1, 19.1]); oracle corners on the same seeds: −114.1 [−141.9, −86.6] vs OOK-8x8 at 3.0 m and −24.0 [−45.0, −3.6] vs QCD-style at 3.25 m (unadjusted; n.s. under σ_mult ≥ 0.05, `r8/mult_binding.csv`). Under every tested σ_mult (0.024/0.05/0.15, per-pixel and per-frame) v2 remains first at 3.0 and 3.25 m and the binding margin stays significantly positive; it shrinks significantly only at σ_mult = 0.15 at 3.0 m (Δ −49.2 [−73.8, −25.2] per-pixel, −36.0 [−60.0, −12.0] per-frame). The r8 noise runs are outside the Holm family.

**C1/C2 on IMX219** (C1 = audit-2 claim: at 2.5 m, 1/1500, 1/128, v2 exceeds the IEEE 802.15.7 CSK baselines, README "[SUPERSEDED] Claims"; C2 = the IMX174 claim above):
> "C1 here means the audit-2 claim that at 2.5 m (1/1500 s, brightness 1/128) v2 exceeds the IEEE 802.15.7 CSK baselines; C2 means the IMX174 binding-margin claim at 3.0–3.5 m above. On the IMX219 preset `imx219f` (sourced geometry and noise, uncalibrated photometric scale), neither transfers. At the same distances (2.5, 3.0, 3.25 and 3.5 m), v2 is significantly below the binding baseline at every point, with fixed or tuned exposure and with the scale-free finder or oracle corners. Examples: 2.5 m, −1273.6 [−1322.6, −1222.0] bps vs genie(CSK802-8); 3.0 m, −999.6 [−1009.9, −985.3] bps vs QCD-OCC (paper frame), and −991.4 [−1005.7, −977.2] with oracle corners. At matched pixels-per-LED v2 is significantly below at 2.5–3.25 m with both finders (e.g. matched 3.0 m: −57.0 [−75.6, −38.4] vs QCD-style-inspired). At matched 3.5 m the result is not significant (+13.2 [−11.4, 36.0] with the scale-free finder; +0.6 [−23.4, 24.6] with oracle corners at fixed exposure). The one exception is oracle corners with tuned exposure (+23.4 [1.2, 45.6], unadjusted; n.s. after Holm, p_holm 0.33, r6 `holm_claims.csv`). These are simulation results on an uncalibrated preset and say nothing about real IMX219 hardware."

IMX219 scope: all IMX219 results use the current preset (`imx219f`), photometrically uncalibrated (sourced geometry and noise). Matching the measured CQ sensitivity would need an effective QE of 1.5–2.16 (impossible as QE); those ×3-QE runs are not shipped. The published QCD-OCC BER is matched by this preset near Tx brightness 1/2048, not the 1/128 used in E3.

**Ablation (R3/N4):** lit0.75 recovers 75.6 / 42.6 / 33.8 % and lit0.75 + 2-level decoder 88.6 / 72.7 / 82.4 % of the v2 − base-only gap (3.0 / 3.25 / 3.5 m). A significant residual of +35.4 [13.2, 58.2] bps remains at 3.25 m; the decoder gain is larger on the 0.75-level Tx (interaction), so the shares are not additive. Radiant-equal power: same within 1.2 bps (scales equal to 3e-4).

Not claimed: that v2's modulation outperforms at 3.0 m; any robust or unqualified C2; that C1/C2 fail on real or calibrated IMX219 hardware.

## IMX219 (R1) — `e3_claims.csv`, `e3_validation.csv`, `docs/IMX219_PARAMETERS.md`
Finder gross error 0.000 at 0.5–5 m (was 0.60–0.83). m3.5: n.s. with the real finder; with genie corners n.s. fixed, v2 > all tuned (+23.4 [1.2, 45.6]).

## Binding margins (R2) — `c2_binding_margins.csv` (min over all baselines × {native, 48-bit}, 1/128, fixed 1/1500; **CIs in this table: B = 2000** (bench_report, r0); the claim text uses B = 10000, e.g. canonical 3.0 m +150.0 [126.6, 173.4])
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
- Sensitivity tornado (`sensitivity_tornado.*`): C2 stays positive under f/1.8, bits 10/12, cfa×0.5, t_row, f_tx 10/20, reflectance, jitter, brightness 1/64;
  flips (negative or n.s.) under f_mm 4–8, f/2.8, focus 0.5/2.0 m, brightness 1/256 and **cfa×2** (binding margin +7.0 [−14.3, 28.2] n.s. at 3.0 m, −34.1 [−52.7, −15.5] at 3.25 m; `sensitivity_tornado.csv` lines 14/37; r7 R3).
  lambert_m is **not** a "keep" factor: on axis (yaw 0, all C2 runs) cos^m(0) = 1, so lambert_m has no effect by construction (r6 arrays identical to default).
  r7 re-ran it at 30° yaw (`r7/lambert_yaw30.csv`): no verdict changes (3.0 m stays positive, 3.25 m stays negative).
- Factorial (r7, R7; `r7/factorial_binding.csv`, `r7/factorial_summary.csv`): 36 cells focus × f_mm × f_number × brightness at 3.0/3.25 m; C2 positive in 1/36 cells (2.8 %) at each distance — only the default cell. Not an LHS/Sobol analysis.
- Holm scope (r7, R4): outside the 56-claim family and unadjusted: canonical oracle 3.25/3.5 m (3.25 m −24.0 is unadjusted), geometry, OAT sensitivity, PhyCom plugins, E2 cells, r7 lambert yaw30 and factorial.
- Geometry (`geometry_binding.csv`): 80 mm panel loses C2 at 3.0/3.25 m (OOK binds); 30° yaw keeps only 3.0 m positive.
- Finder (`finder_failure.*`): zero detection failures; gross-error rates drive finder loss; attribution holds at 3.25 m.
- Stats: ablation n.s. stable on 25 seeds; Holm flips 3 unadjusted positives (incl. IMX219 m3.5 oracle+tuned).
- QCD-OCC grid (`qcd_validation_grid.csv`): no cell CI contains published 1.13e-2; brightness unidentified + camera mismatch.
- PhyCom plugins (`phycom_margins.csv`, `r7/phycom_plugin_goodput.csv`): CSK-16-inspired (Singh 2018) and SM-PAM-inspired (Leblebici 2026,
  analytic midpoint thresholds, M = 4 fixed, not tuned) deliver ≈0 bps at 3.0–3.5 m (CSK-16 0.0; SM-PAM 1.56 / 0.0 / 0.0), i.e. they are
  non-functional at the C2 distances in this harness; "v2 − plugin" there equals v2's own goodput. Binding baseline unchanged.

## benchmark-r7 additions — `results/benchmark/r7/`, `CLAIMS_r7.md`
- **Provenance note (r6 run metas, audit R6).** `run_meta_R6_geoyaw30.json` and `run_meta_R6_valid6.json` record
  `05a1e0bf…-dirty` and `run_meta_R6_finder.json` records `b0d6806c…-dirty` (uncommitted files outside results/ at run
  time); `run_meta_R6_sens.json` records 2e641161 (the later Holm commit) although the sens outputs were committed at
  05a1e0b (the sens npz was assembled from checkpoints after that commit). Regeneration evidence: the independent audit's
  192/192 spot re-runs at 962ba5fc matched, and the r7 spot re-run at a clean r7 commit (`r7/provenance_spot.csv`,
  `experiments/r7_spot.py`, first 20 symbols of 7 jobs) gives 240/240 identical arrays for geoyaw30, valid6, finder and
  sens. The dirty trees therefore did not affect the sampled arrays. The metas are kept unchanged (as in r2).
  r7 metas `run_meta_R7_lamb30.json`/`run_meta_R7_fact.json` record `06ef6143…-dirty` (r7 report/diagnostic scripts and
  docs were uncommitted; no physics/decoder file differed); the default factorial cell is array-identical to
  `review_e2_P33.npz` (`r7/factorial_default_identity.csv`).

## benchmark-r8 additions — `results/benchmark/r8/`, `CLAIMS_r7.md` (r8 sections)
- **QCD-OCC BER plateau (R8; `r7/qcd_plateau_diag.csv`, 1000 symbols per cell, QCD-OCC unit at 2.0 m, f_tx 25).** The plateau is a **deterministic error floor, not noise-limited**: the base BER stays at ≈1.5–1.8e-2 from brightness 1/160 to 1/1024 (1.52e-2, 1.83e-2, 1.56e-2, 1.61e-2, 1.56e-2, 1.48e-2) while the model's shot SNR (G) falls from 62.9 to 25.1. About 65–75 % of the bit errors are on the **R bit** (share_R_bit 0.65–0.74 over that range; 0.76 at 1/128). It is **not rolling-shutter mixing** (t_row = 0: 1.40–1.56e-2; f_tx = 15: 1.27–1.54e-2 over 1/160–1/1024) and **not CFA crosstalk** (cfa = I: 1.96e-2 at 1/256, 1.79e-2 at 1/1024, with the R-bit share rising to 0.82–0.86). The **low BER at 1/96–1/128 depends on saturation clipping**: base 1.6e-4 at 1/96 and 7.1e-3 at 1/128, where peak B is 1.66× / 1.24× full well; with the clipping removed (no_clip12) the floor appears there too (1.44e-2 at 1/96, 1.61e-2 at 1/128, 1.66e-2 at 1/64). Consequence: the published 1.13e-2 is "bracketed" by the grid only because of a saturation transition, not because the model reproduces the link. The floor most likely sits in the QCD-OCC decoder's R-channel decision (suspected, not traced in code).
- **Signal-proportional noise (R-V1; `r8/mult_binding.csv`, `r8/mult_goodput.csv`, `r8/mult_finder.csv`, `r8/mult_sigma0_identity.csv`).** Optional `sigma_mult` in `channel.physical.capture` (default 0 → unchanged code path; the σ = 0 control is 234/234 arrays identical to `review_e2_P33.npz`). Model: mean electrons per mosaic site × max(0, 1 + σ z) before PRNU and Poisson; z redrawn for every captured frame (temporally independent); spatial correlation either **per-pixel** (i.i.d.) or **per-frame** (one gain per R/G/B channel over the whole frame); per-LED correlation is not implemented. z comes from a side stream seeded from the capture rng state (the rng is not advanced), so payloads, geometry jitter and camera phase are common across σ levels (CRN-paired with E2); later Poisson draws within a symbol can diverge. Default C2 cell, claims/E2 seeds, eval 1000 + tune 200, B = 10000:

  | σ_mult | corr | 3.0 m | 3.25 m | 3.5 m |
  |---|---|---|---|---|
  | 0 | – | +150.0 [126.6, 173.4] | +107.6 [86.3, 129.0] | +4.3 [−10.1, 19.1] n.s. |
  | 0.024 | pixel | +153.0 [129.6, 176.4] | +113.5 [92.2, 134.9] | +15.0 [0.5, 30.1] |
  | 0.024 | frame | +145.2 [121.2, 168.6] | +112.6 [91.7, 133.9] | +4.3 [−9.8, 18.8] n.s. |
  | 0.05 | pixel | +137.4 [114.6, 160.8] | +121.8 [98.4, 144.6] | +13.0 [−1.8, 28.2] n.s. |
  | 0.05 | frame | +150.0 [126.0, 174.0] | +113.3 [91.6, 134.8] | +10.8 [−3.7, 25.8] n.s. |
  | 0.15 | pixel | +100.8 [76.8, 124.8] | +97.8 [74.4, 121.2] | +22.0 [7.1, 37.4] |
  | 0.15 | frame | +114.0 [90.6, 137.4] | +96.0 [72.6, 119.4] | +1.4 [−12.5, 15.8] n.s. |

  v2 is ranked first (native goodput) in every cell. Change vs σ = 0 (joint bootstrap): significant only at σ = 0.15, 3.0 m (−49.2 [−73.8, −25.2] pixel, −36.0 [−60.0, −12.0] frame); all 3.25 m changes n.s. 3.5 m stays not claimed (positive cells are unadjusted and outside the Holm family). Oracle-corner binding at 3.0 m stays negative (−66.6 to −121.9); at 3.25 m it becomes n.s. for σ ≥ 0.05 and for σ = 0.024 per-frame. **Baselines gain throughput under noise (S1 explained):** at 3.0 m, σ = 0.15, QCD-style-inspired +61.8 [43.8, 79.8] bps (pixel; 252 → 314) and +49.2 [31.2, 67.8] (frame), v2-base-only +45.0 / +38.4, OOK-8x8 +28.9 (frame), while v2 changes by +12.6 / +13.2 (n.s.). The gain is a **finder effect**: the shared finder's gross-error rate (corner error > 0.5 pitch, per frame) falls for QCD-style from 0.572 to 0.515/0.516 and for v2-base-only from 0.562 to 0.516/0.534, whereas the same schemes' oracle-corner goodput falls (QCD-style 523 → 494/500). Noise dithers the thresholded LED blobs and the refinement centroids, so part of the baselines' finder loss at σ = 0 is a deterministic artefact of noise-free rendering; this shrinks the C2 margin, consistent with C2 being a finder property. Detection failures stay 0.
- **Factorial key label (R-K).** `r7_fact.npz` keys are `<cell>|d<d>|1/1500|1/128|<eval|tune>|<scheme>|<field>`; the literal `1/128` is a fixed key slot copied from the E2 key format and is **not** the brightness of the cell. The Tx brightness of a cell is the `brightness=` entry in `<cell>` (e.g. `focus_m=1.0,f_mm=6,f_number=2.0,brightness=1/256|d3.0|1/1500|1/128|eval|…` is a 1/256 cell). Keys were left unchanged so the shipped arrays and checkpoints stay valid; `experiments/r7_report.py` documents the same and `tests/test_r8.py` checks the run meta.
- **Provenance (r8).** Both R8 runs were made from commit e97905f (sigma_mult option + runner + tests, no later code change to any
  simulation file). `run_meta_R8_mult.json` code_key is clean (e97905f); its `git` field and `run_meta_R8_multfin.json` read `-dirty`
  because `results/` outputs of the first group and the analysis-only `experiments/r8_report.py` were uncommitted at that moment.
  The σ = 0 control reproduces `review_e2_P33.npz` 234/234, and the dual-receiver `err` arrays equal the std-receiver arrays 273/273
  (`r8/mult_finder.csv`, column std_vs_dual_err_identical).
