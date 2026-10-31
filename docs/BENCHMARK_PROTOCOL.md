# Benchmark protocol (benchmark-r0)

## Release statement
All code, configuration, seeds, raw per-symbol error arrays (`results/**/*.npz`), run metadata (`run_meta_*.json`, git hash +
environment) and table generators are contained in this repository, together with a pinned environment (`requirements.lock`)
and `reproduce.sh` (`tables` / `full`). **benchmark-r0 is a local release candidate: nothing has been pushed or archived
(no GitHub repo, no Zenodo DOI). No licence has been chosen yet (see `LICENSE_TODO`); authors in `CITATION.cff` are TODO.**

## Scope and labels
Simulation only (no hardware). The schemes "NestedTexture-inspired", "QCD-style-inspired" and "Overlay-inspired" are
**re-implementations from abstracts only** (abstract-based re-implementations, not the original codes); every table and
figure must carry the "-inspired" label. CSK802-4/8 are IEEE 802.15.7 CIE-xy CSK. OOK and the HNCSM variants are ours.

## Fairness protocol
1. **Same channel, same power.** All schemes share the 8×8 matrix, the 4 corner pilots, the channel draw and the power
   normalisation (`power_scales('equal')`: equal summed drive, independent of the set of schemes). R8: a radiant-equal
   normalisation (`audit_r1.scales_for('radiant')`) gives the same ablation result (colour-balanced schemes have identical scales).
2. **Common random numbers.** Every scheme sees the same per-symbol seeds (`config.cond_seed`); differences are paired
   (bootstrap B = 2000, 95 % CI).
3. **Disjoint tuning seeds.** Any per-scheme choice (exposure from T_EXPS = {1/4000, 1/1500, 1/500, 1/250}; QCD subset;
   Overlay amplitudes; genie line-up from GENIE_SET; finder k) is made on tune seeds (SEED + 1 000 003), evaluated on eval seeds.
4. **Equal tuning effort.** Each scheme gets the same tuning grid for exposure; scheme-internal parameters of the
   re-implementations were tuned on a grid at least as large as HNCSM's.
5. **Headline = binding margin.** A claimed advantage is the minimum over all comparison schemes (v1, v1-base, v2-CS,
   QCD, Overlay, NestedTexture, CSK802-4/8, OOK, genie) × {native payload, 48-bit equal payload}
   (`results/benchmark/c2_binding_margins.csv`).
6. **Genie (oracle) corners** for all spatial schemes (`genie_corners=True`): same seeds, same RNG consumption, true corner
   positions. Detector loss = oracle − detector; modulation loss = what remains (`oracle_vs_detector*.csv`).
7. **Seed replication.** Two further disjoint master seeds (A = 31415926, B = 27182818, each with its own tuning seeds).
   A claim whose CI changes sign across seed sets is downgraded (`seed_spread.csv`).

## IEEE 802.15.7 OCC PHY modes
Not implemented. The 802.15.7-2018 OCC PHYs (e.g. UFSOOK, Twinkle-VPPM, S2-PSK, HS-PSK, offset-VPPM, MIMO/A-QL, HA-QL,
RS-FSK, C-OOK, CM-FSK, VTASC, SS2DC, IDE…) are defined for frame-rate/rolling-shutter temporal modulation or specific 2-D
code layouts with their own framing; they do not map onto an 8×8 RGB matrix with one symbol per frame without
choosing many free parameters ourselves, which would again be an "-inspired" re-implementation. The benchmark therefore uses
the 802.15.7 CIE-xy CSK constellations (CSK802-4/8) as the standard reference, and the plugin API
(`docs/ADDING_A_SCHEME.md`) is the intended route for adding OCC-PHY modes. This is a stated limitation.

## Disclosures
- At 70° yaw with tuned exposure, QCD-style-inspired beats v2: v2 − QCD = −23.4 bps (review-r1 E2/claims); with tuned
  exposure at 2.5 m the two tie (−2.9, n.s.).
- At 1/256 brightness the C2 margins reverse at 3.0 and 3.25 m (E2); this must appear in the conclusion.
- IMX219: see `docs/IMX219_PARAMETERS.md` (CQ-anchored effective QE > 1, i.e. unphysical as QE).
- e3claims@imx219f run meta records worktree commit 83b67a7 although the group started at 8d579f2; the only diff between
  those commits is the seed line-up (`lineup_seed`), which this group does not use.

## Limitations
- **M4 (hardware):** no hardware validation. The only external anchors considered are listed in `docs/ANCHORS.md`; none was
  reproduced.
- **M7 (parameter uncertainty):** no Latin-hypercube / sensitivity study over sensor and optics parameters was run;
  results are conditional on the presets. Many comparisons are reported without multiplicity correction; CIs are per comparison.
- Single matrix geometry (8×8, P = pixels/LED set by distance); one LED spectrum model.
