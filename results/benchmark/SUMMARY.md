# benchmark-r0 summary (simulation only; local release candidate, not published)

Branch `benchmark` (from review-r1-exp cee4082). Tests: 84 pass. Default IMX174 path byte-identical (idcheck: v2 P33 3.0 m
err/sat/mix arrays equal to sweeps_PHYS_P33, fresh checkpoints; also equal with OMP_NUM_THREADS=1).

## Oracle (genie) corners vs detector — `oracle_vs_detector*.csv`, `oracle_ranking.csv`
IMX174 P33, 1–4 m (default 1/1500), mean over 7 points: v2 detector 554 → oracle 597 bps (detector loss 42, modulation loss 423);
QCD-style-inspired 393 → 506 (113 / 94); OOK 465 → 522; Overlay-inspired 195 → 238; v2-base-only 388 → 501.
Claims conditions (d2.5/d3.0/yaw70/blur4), fixed: v2 460 → 560; QCD-style-inspired 424 → 579 (detector share 0.9); OOK 328 → 644.
**v2's rank 1 at 3.0 m (detector) becomes rank 3–4 with oracle corners (OOK best); at 3.5 m v2 stays rank 1.**
So the C2 advantage at 3.0 m is largely a detector-robustness effect, not a modulation effect.
IMX219 (imx219f, scale-free finder): detector ≈ oracle (v2 697 vs 714; CSK802-8 827 vs 818): detector loss is small after R1.

## IMX219 (R1) — `e3_claims.csv`, `e3_validation.csv`, `docs/IMX219_PARAMETERS.md`
Finder gross error 0.000 at 0.5–5 m (was 0.60–0.83). With real and genie corners alike, v2 loses to the binding baseline at
every d-point (e.g. d3.0 fixed: −999.6 [−1009.9, −985.3] vs QCD-OCC paper frame) and at m2.5–m3.25; m3.5 n.s.
(genie, tuned: +23.4 [1.2, 45.6]). C1/C2 do not transfer to IMX219 — now independent of the detector.

## Binding margins (R2) — `c2_binding_margins.csv` (min over all baselines × {native, 48-bit}, 1/128, fixed 1/1500)
| P | seeds | 3.0 m | 3.25 m | 3.5 m |
|---|---|---|---|---|
| 25 | claims/E2 | +133.2 [109.2, 157.2] | +80.5 [58.5, 102.8] | +16.6 [1.2, 32.6] |
| 25 | sweep | +141.0 [118.8, 163.2] | +94.9 [73.3, 116.1] | +21.4 [7.3, 37.2] |
| 33 | claims/E2 | +150.0 [127.2, 174.0] | +107.6 [85.2, 128.8] | **+4.3 [−10.1, 19.3] n.s.** |
| 33 | sweep | +148.2 [126.6, 171.6] | +116.4 [94.4, 139.2] | +28.6 [13.9, 45.0] |
3.5 m binding baseline is v1-base (HNCSM base-only); its significance depends on the seed set → downgraded.

## E2 robustness (R4) — `results/review_r1/e2_survival.csv`, `e2_robust.csv`
No C2 point survives the grid at P25 or P33. P25 min lower bounds: −103.2 (3.0 m), −81.6 (3.25 m), −12.0 (3.5 m).
3.0/3.25 m reverse significantly (1/256; 3.0 m also tuned 1/128: −61.8 [−82.8, −40.2]). **3.5 m: "not significant", not reversed**
(P25 worst +10.8 [−12.0, 36.0]; P33 worst n.s.). P42: NOT RUN (see remaining).

## Ablation (R3, R8) — `ablation_factorial.csv`
P33, equal summed drive: share of v2−base-only gap recovered by lit0.75: 75.6 / 42.6 / 33.8 % (3.0/3.25/3.5 m);
lit0.75 + 2-level decoder: 88.6 / 72.7 / 82.4 %. Residual v2 − (lit0.75+2lv): +18.6 [−0.6, 38.4] n.s., +35.4 [13.2, 58.2],
+14.4 [−4.2, 34.8] n.s. Decoder effect on lit0.75 Tx: +21.0/+39.0/+39.6 (sig.); on lit1.0 Tx: +15.6/+29.4/+17.4.
Attribution: "power/level allocation under equal-summed drive + decoder". Radiant-equal: same numbers (colour-balanced schemes) → invariant.

## Seed replication (R5): NOT RUN (seedA/seedB). Only the sweep-vs-claims seed comparison above exists.

## Runtimes — `runtime.csv`, `runtime_hw.json` (n = 40 symbols, single process, OMP=1, **machine load ≈ 64 on 8 vCPU: inflated**)
IMX174 mean 20.7 ms/symbol (10.4–29.5), IMX219 28.7 (19.9–57.5); the corner finder is the largest stage for v2 (≈7 ms).

## R9 — e3valid regenerated at clean 83b67a7: all 30 arrays np.array_equal → original npz kept, meta updated.
e1sweep, e1dec, e2_P33 not regenerated (remaining).
