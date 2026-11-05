# Response to reviewer points (review_vtc.md) — benchmark-r0

| Point | Reviewer concern | Response / where |
|---|---|---|
| M1 | Hierarchy vs ablation | Factorial ablation {lit 1.0, lit 0.75} × {1-level, 2-level decoder} at P33, 3.0–3.5 m (`results/benchmark/ablation_factorial.csv`). Gain re-attributed to "power/level allocation under equal-summed drive + decoder"; lit0.75 alone recovers 76/43/34 % of the v2−base-only gap, lit0.75+2-level 89/73/82 %; significant residual +35.4 [13.2, 58.2] at 3.25 m; decoder × level interaction, shares not additive. Hierarchy claimed only ≤2 m. |
| M2 | Operating point cherry-picked | Safe C2 wording adopted (README). E2 survival is vs baselines only; binding margin also includes the v1 family. E2 robustness grid at P25, P33, P42: no C2 point survives at any P; 3.5 m is n.s. in its worst cases (never significantly reversed). Binding margins over all baselines × {native, 48-bit}. See SUMMARY. |
| M3 | Single sensor | IMX219 preset with sourced geometry and noise, photometrically uncalibrated (effective QE would need 1.5–2.16; published BER matched near 1/2048, not 1/128); scale-free finder (gross error 0 % at 0.5–5 m); genie-corner rows. Claim: "On an IMX219 preset with sourced geometry and noise but an uncalibrated photometric scale, neither C1 nor C2 transfers" (full wording in README). |
| M4 | No hardware validation | Not addressed; stated limitation. Anchor feasibility in `docs/ANCHORS.md` (none quantitatively usable). |
| M5 | Baselines; 802.15.7 OCC PHY | v1, v1-base, v2-CS, -inspired QCD/Overlay/NestedTexture, CSK802-4/8, OOK, genie; OCC-PHY omission reasoned in `BENCHMARK_PROTOCOL.md`; plugin API for additions. |
| M6 | 48-bit equal-payload script | 48-bit variants in every binding margin (`c2_binding_margins.csv`). |
| M7 | Statistics, parameter uncertainty (LHS) | Paired bootstrap CIs on CRN; two extra disjoint master seeds (`seed_spread.csv`); downgraded: P33 3.5 m C2 margin (n.s.) and the P33 3.0 m tuned-1/256 reversal (not robust). LHS not run → stated limitation; no multiplicity correction. |
| M8 | Novelty | Paper re-framed as an open benchmark; HNCSM is one entry. |
| m1 | TODOs / authorship | Resolved in benchmark-r9: MIT `LICENSE`, author Sanket Salvi in `CITATION.cff` / `.zenodo.json` (ORCID/DOI placeholders until release). |
| m2 | 5.16 bps value | Check against regenerated tables before camera-ready (author action). |
| m3 | One value for +148 | Single headline: +148.2 [126.6, 171.6] bps at 3.0 m (audited C2 wording, README), qualified by the oracle-corner result (v2 4th at 3.0 m). **r5 update:** headline now from the canonical claims/E2 seed set, +150.0 [127.2, 174.0] bps at 3.0 m (`c2_binding_margins.csv` row 8); +148.2 is the sweep-seed robustness value. Oracle: v2 3rd among comparison schemes at 3.0 m (4th incl. the v2-base-only ablation), −114.1 [−141.8, −87.2] vs OOK-8x8 (`oracle_pairs.csv`). See `results/benchmark/CLAIMS_r5.md`. |
| m4 | Corner CSV | `results/review_r1/corner_error_bench.csv` shipped. |
| m5 | Fig. 3 naming | Use "-inspired" labels (author action in the figure). |
| m6 | Table II single column | Author action (layout). |
| m7 | Goodput / frame-rate definition | Goodput = CRC-8-verified bits per layer × f_tx = 15 sym/s (METHODS). |
| m8 | Radiant-equal with paired CIs | `ablation_factorial.csv` radiant rows (R8): same within 1.2 bps. |
| m9 | yaw70 tuned −23.4; tuned 2.5 m tie −2.9 | Disclosed in `BENCHMARK_PROTOCOL.md`. |
| m10 | 1/256 result in conclusion | Disclosed; conclusion must state reversal at 3.0/3.25 m. |
| m11 | "abstract-based re-implementations" | Wording adopted throughout. |
| m12 | Vehicular use case | Not supported by simulation scope; drop or mark as future work (author action). |
| m13 | Page budget | Author action. |
