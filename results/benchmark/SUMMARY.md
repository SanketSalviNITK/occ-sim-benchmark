# benchmark-r2 summary (simulation only; local release candidate, not published)

Branch `benchmark` (from review-r1-exp cee4082). Tests: 84 pass. Default IMX174 path byte-identical (idcheck: v2 P33 3.0 m
err/sat/mix arrays equal to sweeps_PHYS_P33, fresh checkpoints; also equal with OMP_NUM_THREADS=1).

## Oracle (genie) corners vs detector — `oracle_vs_detector*.csv`, `oracle_ranking.csv`
IMX174 P33, 1–4 m (default 1/1500), mean over 7 points: v2 detector 554 → oracle 597 bps (detector loss 42, modulation loss 423);
QCD-style-inspired 393 → 506 (113 / 94); OOK 465 → 522; Overlay-inspired 195 → 238; v2-base-only 388 → 501.
Claims conditions (d2.5/d3.0/yaw70/blur4), fixed: v2 460 → 560; QCD-style-inspired 424 → 579 (detector share 0.9); OOK 328 → 644.
With oracle corners v2 ranks 4th at 3.0 m (−121 [−149, −94] bps vs OOK), so the 3.0 m advantage comes from how reliably the shared
finder locates v2 frames, not from demodulation; at 3.5 m v2 also leads with oracle corners (+44 [24, 65] vs QCD-style-inspired).
**3.25 m was not tested with oracle corners.** The finder is shared across schemes; a bias toward schemes whose edge LEDs are always lit is suspected, not shown.
IMX219 (current preset imx219f, photometrically uncalibrated; scale-free finder): detector ≈ oracle (v2 697 vs 714; CSK802-8 827 vs 818): detector loss is small after R1.

## Claims wording (validator-approved safe wording, N2)
**C2 (IMX174), safe wording (benchmark-r2):**
> "At the fixed operating point (P33, brightness 1/128, exposure 1/1500) and with the benchmark's shared corner finder, v2 exceeds every comparison scheme (binding margin over all schemes × {native, 48-bit}) at 3.0 m (+148.2 [126.6, 171.6] bps) and 3.25 m (+116.4 [94.4, 139.2]). This holds on three disjoint seed sets and at P25–P42. At 3.5 m the binding margin over HNCSM v1-base is not significant at P33 (+4.3 [−10.1, 19.3]) and only narrowly positive at P25/P42. The advantage does not survive tuned exposure or 1/256 brightness at any power budget. With oracle corners, v2 ranks 4th at 3.0 m (−121 [−149, −94] bps vs OOK), so the 3.0 m advantage comes from how reliably the shared finder locates v2 frames, not from demodulation. At 3.5 m v2 also leads with oracle corners (+44 [24, 65] vs QCD-style-inspired). 3.25 m was not tested with oracle corners."

**C1/C2 on IMX219, safe wording (benchmark-r2):**
> "On an IMX219 preset with sourced geometry and noise but an uncalibrated photometric scale, neither C1 nor C2 transfers. At the same distances, v2 is below the binding baseline at every point (e.g. 3.0 m: −999.6 [−1009.9, −985.3] bps vs QCD-OCC), largely because the higher-rate schemes approach their error-free rate. At matched pixels-per-LED it is below at 2.5–3.25 m. Both hold with the scale-free finder and with oracle corners. At matched 3.5 m the result is not significant, except v2 > all with oracle corners and tuned exposure (+23.4 [1.2, 45.6])."

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
| 33 | claims/E2 | +150.0 [127.2, 174.0] | +107.6 [85.2, 128.8] | **+4.3 [−10.1, 19.3] n.s.** |
| 33 | sweep | +148.2 [126.6, 171.6] | +116.4 [94.4, 139.2] | +28.6 [13.9, 45.0] |
3.5 m binding baseline is v1-base (HNCSM base-only); its significance depends on the seed set → downgraded.

## E2 robustness (R4) — `results/review_r1/e2_survival.csv`, `e2_robust.csv`
E2 survival compares v2 with the baselines only (the binding margin also includes the v1 family and v2-CS). No C2 point survives the grid at P25 or P33. P25 min lower bounds: −103.2 (3.0 m), −81.6 (3.25 m), −12.0 (3.5 m).
3.0/3.25 m reverse significantly (1/256; 3.0 m also tuned 1/128: −61.8 [−82.8, −40.2]). **3.5 m: "not significant", not reversed**
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

## R9 — run metas
Only e3valid was regenerated from a clean commit (83b67a7): all 30 arrays np.array_equal → original npz kept, meta updated.
e1sweep, e1dec (review_r1_dec) and e2_P33 were NOT regenerated here (time budget); their metas still carry the -dirty hash.
The Research Validator regenerated sampled arrays (57/57 bit-identical) from a89ad29.
Command to close it: in a clean checkout, `OMP_NUM_THREADS=1 python -m experiments.review_r1_dec; python -m experiments.review_r1 e1sweep; python -m experiments.review_r1 e2_P33`, then compare arrays.
