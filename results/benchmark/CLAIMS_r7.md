# benchmark-r7 claims (supersedes CLAIMS_r6 claim text; r6 numbers unchanged)

Simulation only. Sources: `results/benchmark/r6/*.csv`, `results/benchmark/r7/*.csv`. CIs: B = 10000, bootstrap seed 0.

## C2 (IMX174) — safe wording (audit r6 §3)
> "At the fixed operating point (IMX174, P33, brightness 1/128, exposure 1/1500), with the ASSUMED default optics (f = 6 mm, f/2.0, focus 1.0 m), the 65 mm 8×8 panel on axis, and the benchmark's shared corner finder, the binding margin of v2 over every comparison scheme × {native, 48-bit} on the canonical claims/E2 seeds is +150.0 [126.6, 173.4] bps at 3.0 m (vs QCD-style-inspired, native) and +107.6 [86.3, 129.0] bps at 3.25 m (vs Overlay-inspired, 48-bit); across all four seed sets the minimum is +148.2 (3.0 m) and +107.6 (3.25 m), all Holm-significant (56-claim family). At 3.5 m it is not claimed (canonical +4.3 [−10.1, 19.1]; P25/P42 positive unadjusted but n.s. after Holm). The advantage is conditional: it disappears under one-at-a-time changes of the ASSUMED lens (f = 4 or 8 mm, f/2.8, focus 0.5 or 2.0 m), CFA crosstalk ×2, brightness 1/256 (at P25/P33), per-scheme tuned exposure, an 80 mm panel (where OOK binds at 3.0/3.25 m), and at 3.25 m under 30° yaw; interactions were not studied. With oracle corners on the same seeds v2 is third at 3.0 m (−114.1 [−141.9, −86.6] vs OOK-8x8) and second at 3.25 m (−24.0 [−45.0, −3.6] vs QCD-style, unadjusted), while at 3.5 m it leads (+46.1 [23.9, 68.2] vs Overlay, 48-bit): the 3.0–3.25 m advantage therefore comes from how reliably the shared finder locates v2 frames (gross-error rate 7 %/17 % vs 57–71 % for QCD-style), not from demodulation."

lambert_m is not a factor that "keeps" C2: on axis it has no effect by construction (cos^m(0) = 1); at 30° yaw (`r7/lambert_yaw30.csv`) no verdict changes.

## Sensitivity
- OAT (`r6/sensitivity_tornado.csv`): C2 flips under f_mm 4/8, f/2.8, focus 0.5/2.0 m, brightness 1/256 and CFA crosstalk ×2.
- Factorial (r7, R7; `r7/factorial_binding.csv`, `r7/factorial_summary.csv`): focus {0.5, 1, 2} m × f_mm {4, 6, 8} × f_number {2.0, 2.8} × brightness {1/128, 1/256} = 36 cells at 3.0 and 3.25 m, claims/E2 seeds, 1000 eval + 200 tune symbols. C2 is positive in **1 of 36 cells (2.8 %)** at each distance, and that cell is the default (focus 1.0 m, 6 mm, f/2.0, 1/128); 34/36 cells are significantly negative at 3.0 m and 35/36 at 3.25 m. The default cell is array-identical to `review_e2_P33.npz` (`r7/factorial_default_identity.csv`). This is a small full factorial, not an LHS/Sobol global analysis; it confirms that C2 is a property of one optical configuration, with no interaction that restores it elsewhere in the grid.

## Statistics
**Holm scope (r7, R4).** The Holm–Bonferroni correction covers only the 56-claim family in `r6/holm_claims.csv`. The following r6/r7 results are **outside the family and are reported unadjusted**: the canonical-seed oracle points at 3.25 and 3.5 m (`oracle_binding_canonical.csv`; in particular the 3.25 m oracle margin −24.0 [−45.0, −3.6] vs QCD-style is **unadjusted**), the geometry runs (`geometry_binding.csv`), the OAT sensitivity runs (`sensitivity_tornado.csv`), the PhyCom plugin margins (`phycom_margins.csv`), the E2 grid cells, and the r7 lambert_m 30° yaw and factorial runs.

## PhyCom plugins (R5)
SM-PAM-inspired uses analytic midpoint thresholds (not tuned) with M fixed at 4; CSK-16-inspired and SM-PAM-inspired both give ≈0 bps at 3.0–3.5 m (`r7/phycom_plugin_goodput.csv`), so "v2 − plugin" there equals v2's own goodput. `r6/phycom_margins.csv` has no duplicate rows.

## QCD-OCC BER plateau (R8)
See `r7/qcd_plateau_diag.csv` and SUMMARY.md.

## Provenance (R6)
See SUMMARY.md provenance note and `r7/provenance_spot.csv`.
