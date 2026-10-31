# Response to reviewer points (review_vtc.md) — benchmark-r0

| Point | Reviewer concern | Response / where |
|---|---|---|
| M1 | Hierarchy vs ablation | Factorial ablation {lit 1.0, lit 0.75} × {1-level, 2-level decoder} at P33, 3.0–3.5 m (`results/benchmark/ablation_factorial.csv`). Gain re-attributed to "power/level allocation under equal-summed drive + decoder"; lit0.75 alone recovers 76/43/34 % of the v2−base-only gap, lit0.75+2-level 89/73/82 %. Hierarchy claimed only ≤2 m. |
| M2 | Operating point cherry-picked | E2 robustness grid at P25, P33, P42 (brightness × exposure × payload); binding margins over all baselines × {native, 48-bit}. See SUMMARY. |
| M3 | Single sensor | IMX219 preset with sourced parameters (`docs/IMX219_PARAMETERS.md`), scale-free finder (gross error 0 % at 0.5–5 m), genie-corner rows (`e3_claims.csv`). |
| M4 | No hardware validation | Not addressed; stated limitation. Anchor feasibility in `docs/ANCHORS.md` (none quantitatively usable). |
| M5 | Baselines; 802.15.7 OCC PHY | v1, v1-base, v2-CS, -inspired QCD/Overlay/NestedTexture, CSK802-4/8, OOK, genie; OCC-PHY omission reasoned in `BENCHMARK_PROTOCOL.md`; plugin API for additions. |
| M6 | 48-bit equal-payload script | 48-bit variants in every binding margin (`c2_binding_margins.csv`). |
| M7 | Statistics, parameter uncertainty (LHS) | Paired bootstrap CIs on CRN; two extra disjoint master seeds (`seed_spread.csv`), claims with sign-changing CIs downgraded. LHS not run → stated limitation; no multiplicity correction. |
| M8 | Novelty | Paper re-framed as an open benchmark; HNCSM is one entry. |
| m1 | TODOs / authorship | CITATION.cff authors TODO (for the authors to fill); LICENSE_TODO. |
| m2 | 5.16 bps value | Check against regenerated tables before camera-ready (author action). |
| m3 | One value for +148 | Single headline: binding margin at 3.0 m, sweep seeds +148.2 [126.6, 171.6]; claims seeds +150.0 [127.2, 174.0]. |
| m4 | Corner CSV | `results/review_r1/corner_error_bench.csv` shipped. |
| m5 | Fig. 3 naming | Use "-inspired" labels (author action in the figure). |
| m6 | Table II single column | Author action (layout). |
| m7 | Goodput / frame-rate definition | Goodput = CRC-8-verified bits per layer × f_tx = 15 sym/s (METHODS). |
| m8 | Radiant-equal with paired CIs | `ablation_factorial.csv` radiant rows (R8): attribution invariant. |
| m9 | yaw70 tuned −23.4; tuned 2.5 m tie −2.9 | Disclosed in `BENCHMARK_PROTOCOL.md`. |
| m10 | 1/256 result in conclusion | Disclosed; conclusion must state reversal at 3.0/3.25 m. |
| m11 | "abstract-based re-implementations" | Wording adopted throughout. |
| m12 | Vehicular use case | Not supported by simulation scope; drop or mark as future work (author action). |
| m13 | Page budget | Author action. |
