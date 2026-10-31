# results/legacy — LEGACY outputs, excluded from all claims (Research-Validator round 2, F5)

These files are kept for traceability only. Nothing in README.md / METHODS.md §9 "Claims" cites them. Do not use them
for new conclusions. They were moved here unchanged (byte-identical; hashes are in `../MANIFEST.sha256` under
`results/legacy/`).

| Files | Why legacy |
|---|---|
| `sweep_distance_m_PHYS_P60.csv`, `run_meta_PHYS_P60.json`, `phys_distance_m_PHYS_P60.{png,pdf}` | Physical-channel P60 distance sweep. Its run_meta records git `11b1072…-dirty`, so the exact code that produced it cannot be identified. It was not regenerated from a clean commit (unlike P25/P33/P42, regenerated at 034f240). |
| `sweep_{yaw_deg,blur_sigma_px,t_exp,lux}_PHYS_P33.csv`, `phys_{yaw_deg,blur_sigma_px,t_exp,lux}_PHYS_P33.{png,pdf}` | Physical-channel P33 stress sweeps from commit 3c9a83b (round 0). `run_meta_PHYS_P33.json` was overwritten by the clean distance-only re-run (034f240) and no longer describes these sweeps, so they have no matching run metadata. The yaw / blur / exposure questions are answered instead by `results/audit_r1/claims_*.csv` (per-symbol data `results/phys_sym/claims.npz`). |
| `phys_efficiency_winners.csv`, `phys_degradation_metrics.csv` | Superseded (round 1, B5): their "CIs" are Wilson-envelope bounds, not paired intervals. Replaced by `results/audit_r1/efficiency_winners_paired.csv` and `results/audit_r1/auc_paired.csv`. They also include the legacy P60 sweep. |
| `phys_efficiency_all_budgets.csv`, `phys_energy_per_bit.csv`, `phys_fig_efficiency_vs_distance.{png,pdf}`, `phys_fig_degradation_energy_P33.{png,pdf}` | Produced by the same round-0 `experiments.efficiency --prefix phys_` run (3c9a83b) as the two superseded tables. They use Wilson-envelope intervals and pool the legacy P60 sweep. |
