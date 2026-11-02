# benchmark-r5 claims: C2 (IMX174) and C1/C2 on IMX219, fully sourced

Simulation only. "Line N" means the line number in the CSV file, with the header on line 1 (`grep -n` numbering). All margins are paired CRN
symbol-bootstrap means with 95 % CIs (B = 2000, `experiments.stats.paired_diff`), in bps.
Unless stated otherwise: IMX174, P33, brightness 1/128, exposure fixed 1/1500 s, equal summed drive.
**Canonical seed set for C2: claims/E2** (`docs/BENCHMARK_PROTOCOL.md` item 9). This choice was made at r5, after every seed set had been run, so it is **not a pre-registration**.

## C2 (IMX174)

> "At the fixed operating point (IMX174, P33, brightness 1/128, exposure 1/1500) and with the benchmark's shared corner finder, on the canonical claims/E2 seed set the binding margin of v2 over every comparison scheme × {native, 48-bit} is +150.0 [127.2, 174.0] bps at 3.0 m (vs QCD-style-inspired, native) and +107.6 [85.2, 128.8] bps at 3.25 m (vs Overlay-inspired, 48-bit). At 3.5 m it is not significant (+4.3 [−10.1, 19.3] bps vs HNCSM v1-base). On three further disjoint seed sets (run_phys sweep, A, B) the margins are 148.2–166.2 bps at 3.0 m and 116.4–123.2 bps at 3.25 m, with every CI above 0 (lowest lower bounds 126.6 and 94.4). At 3.5 m they are 28.2–34.3 bps (lower bounds 13.1–19.0), so the 3.5 m result depends on the seed set and is not claimed. At P25 and P42 (claims/E2 seeds) the 3.0 and 3.25 m margins are positive, and the 3.5 m margin is only narrowly positive (+16.6 [1.2, 32.6] and +15.0 [0.6, 29.9]). No C2 point survives the E2 grid (per-scheme tuned exposure, brightness 1/64–1/256) at P25, P33 or P42. With oracle corners on the same claims/E2 seeds, v2 is significantly below OOK-8x8 at 3.0 m (−114.1 [−141.8, −87.2] bps) and below QCD-style-inspired (−101.4 [−121.8, −80.4]); it is 3rd among the comparison schemes. The 3.0 m advantage therefore comes from how reliably the shared finder locates v2 frames, not from demodulation. Oracle corners at 3.5 m were run only on the sweep seeds. There v2 exceeds every comparison scheme, with a binding margin of +36.8 [12.8, 60.7] bps vs Overlay-inspired (48-bit) and +44.4 [24.6, 64.8] bps vs QCD-style-inspired (native). 3.25 m was not run with oracle corners."

| # | Number in text | File | Line | Row key |
|---|---|---|---|---|
| a | +150.0 [127.2, 174.0], 3.0 m, vs QCD-style-inspired native | results/benchmark/c2_binding_margins.csv | 8 | claims/E2, 33, d3.0 |
| b | +107.6 [85.2, 128.8], 3.25 m, vs Overlay-inspired 48-bit | c2_binding_margins.csv | 9 | claims/E2, 33, d3.25 |
| c | +4.3 [−10.1, 19.3], 3.5 m, vs HNCSM base-only (v1-base) | c2_binding_margins.csv | 10 | claims/E2, 33, d3.5 |
| d | 3.0 m other sets 148.2 (sweep) / 164.4 (A) / 166.2 (B); lo 126.6 / 141.6 / 141.0 | c2_binding_margins.csv; seed_replication.csv | 11; 26; 62 | sweep 33 d3.0; A 33 d3.0 C2; B 33 d3.0 C2 |
| e | 3.25 m other sets 116.4 / 123.2 / 117.5; lo 94.4 / 101.6 / 95.3 | c2_binding_margins.csv; seed_replication.csv | 12; 36; 72 | as above, d3.25 |
| f | 3.5 m other sets 28.6 [13.9, 45.0] / 28.2 [13.1, 43.7] / 34.3 [19.0, 49.9] | c2_binding_margins.csv; seed_replication.csv | 13; 46; 82 | as above, d3.5 |
| g | P25 claims/E2: +133.2 / +80.5 / +16.6 [1.2, 32.6] | c2_binding_margins.csv | 2, 3, 4 | claims/E2, 25 |
| h | P42 claims/E2: +156.6 / +119.6 / +15.0 [0.6, 29.9] | c2_binding_margins.csv | 14, 15, 16 | claims/E2, 42 |
| i | No C2 point survives E2 grid | results/review_r1/e2_survival.csv | 2–19 | survives_all_* = False on all 18 rows |
| j | Oracle 3.0 m vs OOK-8x8: −114.1 [−141.8, −87.2] (claims/E2) | results/benchmark/oracle_pairs.csv | 199 | claims/E2, 3.0, native, OOK-8x8 |
| k | Oracle 3.0 m vs QCD-style-inspired: −101.4 [−121.8, −80.4] (claims/E2) | oracle_pairs.csv | 202 | claims/E2, 3.0, native, QCD-style |
| l | "3rd among comparison schemes" (only OOK and QCD-style have higher oracle goodput; the v2-base-only ablation, 495.6 bps, line 205, would make v2 4th) | oracle_pairs.csv | 194–205 (native) | claims/E2, 3.0 |
| m | Oracle 3.5 m binding: +36.8 [12.8, 60.7] vs Overlay-inspired 48-bit (sweep seeds) | oracle_pairs.csv | 143 | sweep (run_phys), 3.5, 48-bit, Overlay |
| n | Oracle 3.5 m vs QCD-style-inspired: +44.4 [24.6, 64.8] (sweep seeds) | oracle_pairs.csv | 130 | sweep (run_phys), 3.5, native, QCD-style |
| o | 3.25 m not run with oracle corners | experiments/review_r1.py `or_sweep` (even indices only); `or_claims` (d2.5/d3.0/yaw70/blur4) | — | — |

Robustness, not in the claim text: oracle at 3.0 m on the sweep seeds: −121.3 [−148.6, −94.7] vs OOK-8x8 (oracle_pairs.csv line 103) and −95.4 [−117.6, −73.8] vs QCD-style (line 106). v2's oracle rank on the sweep seeds is in `oracle_pairs_rank.csv` line 6 (rank 4 counts the v2-base-only ablation).
Generator: `python -m experiments.bench_oracle_pairs` (analysis only) reads `results/phys_sym/review_or_sweep.npz` and `review_or_claims.npz`. `bench_report c2_binding seeds` produces the other files listed.

## C1/C2 on IMX219

> "C1 here means the round-2 claim that at 2.5 m (1/1500 s, brightness 1/128) v2 exceeds the IEEE 802.15.7 CSK baselines; C2 means the IMX174 binding-margin claim at 3.0–3.5 m above. On the IMX219 preset `imx219f` (sourced geometry and noise, uncalibrated photometric scale), neither transfers. At the same distances (2.5, 3.0, 3.25 and 3.5 m), v2 is significantly below the binding baseline at every point, with fixed or tuned exposure and with the scale-free finder or oracle corners. Examples: 2.5 m, −1273.6 [−1322.6, −1222.0] bps vs genie(CSK802-8); 3.0 m, −999.6 [−1009.9, −985.3] bps vs QCD-OCC (paper frame), and −991.4 [−1005.7, −977.2] with oracle corners. At matched pixels-per-LED v2 is significantly below at 2.5–3.25 m with both finders (e.g. matched 3.0 m: −57.0 [−75.6, −38.4] vs QCD-style-inspired). At matched 3.5 m the result is not significant (+13.2 [−11.4, 36.0] with the scale-free finder; +0.6 [−23.4, 24.6] with oracle corners at fixed exposure). The one exception is oracle corners with tuned exposure (+23.4 [1.2, 45.6]). These are simulation results on an uncalibrated preset and say nothing about real IMX219 hardware."

| # | Number / statement | File | Line | Row key |
|---|---|---|---|---|
| p | Definition of C1 | README.md, section "[SUPERSEDED] Claims", paragraph "C1 (historical …)" | — | 592 bps vs 4-CSK 25 bps at 2.5 m (round 2) |
| q | 2.5 m: −1273.6 [−1322.6, −1222.0] vs genie(CSK802-8) | results/benchmark/e3_claims.csv | 2 | imx219f, real finder, d2.5, fixed |
| r | 3.0 m: −999.6 [−1009.9, −985.3] vs QCD-OCC | e3_claims.csv | 4 | imx219f, real finder, d3.0, fixed |
| s | 3.0 m oracle corners: −991.4 [−1005.7, −977.2] | e3_claims.csv | 20 | imx219f, genie corners, d3.0, fixed |
| t | "below at every same-distance point" | e3_claims.csv | 2–9, 18–25 | verdict = "v2 < binding" on all 16 rows |
| u | Matched 2.5–3.25 m below with both finders; m3.0 −57.0 [−75.6, −38.4] | e3_claims.csv | 10–15, 26–31; 12 | verdict "v2 < binding" on all rows |
| v | Matched 3.5 m: +13.2 [−11.4, 36.0] (real finder); +0.6 [−23.4, 24.6] (oracle, fixed) | e3_claims.csv | 16; 32 | m3.5 |
| w | Matched 3.5 m, oracle + tuned: +23.4 [1.2, 45.6] | e3_claims.csv | 33 | imx219f, genie corners, m3.5, tuned |

## Change log: old (benchmark-r2…r4) → new (benchmark-r5)
| Item | Old | New | Reason |
|---|---|---|---|
| C2 3.0 m headline | +148.2 [126.6, 171.6] (sweep seeds) | +150.0 [127.2, 174.0] (claims/E2) | one canonical seed set (issue 1) |
| C2 3.25 m headline | +116.4 [94.4, 139.2] (sweep seeds) | +107.6 [85.2, 128.8] (claims/E2) | issue 1 |
| C2 3.5 m | +4.3 [−10.1, 19.3] (claims/E2, mixed with sweep numbers above) | unchanged, now from the same set as 3.0/3.25 m | issue 1 |
| "three disjoint seed sets" | span 150.0–166.2 (claims, A, B), which excluded 148.2 | explicit ranges over sweep, A, B: 148.2–166.2 / 116.4–123.2 / 28.2–34.3 | issue 1 |
| Oracle 3.0 m | "ranks 4th, −121 [−149, −94] vs OOK" (only in docs and review_r2_audit) | claims/E2: −114.1 [−141.8, −87.2] vs OOK-8x8; 3rd among comparison schemes (4th counting the v2-base-only ablation); sweep −121.3 [−148.6, −94.7] | issue 2; now in oracle_pairs.csv |
| Oracle 3.5 m | "+44 [24, 65] vs QCD-style-inspired" | binding +36.8 [12.8, 60.7] vs Overlay-inspired (48-bit); +44.4 [24.6, 64.8] vs QCD-style (sweep seeds only) | issue 2: +44 was not the minimum over all schemes × CRC |
| SUMMARY E2 P33 3.0 m tuned 1/128 | −61.8 [−82.8, −40.2] (this is the P25 row) | −69.0 [−88.8, −48.0] (e2_robust.csv line 44) | issue 3 |
| Tuning values (protocol item 4) | last16, (0.25, 0.25) | maxdist-0, (0.35, 0.15), v2-CS δ = 0.3 (tuned_params_phys.json) | issue 4 |
| IMX219 claim | "C1" undefined; "largely because higher-rate schemes approach their error-free rate" | C1 defined; unsourced causal clause removed; 2.5 m, oracle 3.0 m and matched 3.5 m numbers added | issue 5 |
| Tests in SUMMARY | 84 | 85 | issue 6 |
| SUMMARY R9 | "e1sweep/e1dec/e2_P33 metas still -dirty" | all claim-backing REVIEW metas are from clean commits, including idcheck (r5) | stale since r2/r4 |
