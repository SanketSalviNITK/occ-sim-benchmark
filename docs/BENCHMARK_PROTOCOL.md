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
   normalisation (`audit_r1.scales_for('radiant')`) gives the same ablation result within 1.2 bps (scales equal to 3e-4; colour-balanced schemes).
2. **Common random numbers.** Every scheme sees the same per-symbol seeds (`config.cond_seed`); differences are paired
   (bootstrap B = 2000, 95 % CI).
3. **Disjoint tuning seeds.** Any per-scheme choice (exposure from T_EXPS = {1/4000, 1/1500, 1/500, 1/250}; QCD subset;
   Overlay amplitudes; genie line-up from GENIE_SET; finder k) is made on tune seeds (SEED + 1 000 003), evaluated on eval seeds.
4. **Tuning grids (as run; NOT equal effort).** Exposure: every scheme gets the same 4-value grid T_EXPS (tuned rows only).
   Scheme-internal parameters (`experiments/tune.py`, 6 configs each, tune seeds, 200 frames × distances {0.75,1,1.5,2,2.5,3} m physical):
   - HNCSM v2-CS: delta ∈ {0.1, 0.2, 0.3} × bits/lit LED ∈ {1, 2} (plus the earlier `tune_cs.py` sweep on the ideal channel);
   - QCD-style-inspired: subset ∈ {first16, last16, maxdist-0..3} → last16;
   - Overlay-inspired: (a1, a2) ∈ {(0.4,0.1), (0.35,0.15), (0.3,0.2), (0.25,0.25), (0.25,0.15), (0.35,0.1)} → (0.25, 0.25).
   - Not tuned on any recorded grid: HNCSM v1/v1-base, HNCSM v2 and its levels (author design), NestedTexture-inspired,
     CSK802-4/8, OOK, QR/Aztec-style, QCD-OCC (paper frame).
   Tuning effort is therefore not demonstrably equal across schemes; no equal-effort claim is made.
5. **Two comparison sets (N5).** E2 survival (`e2_survival.csv`) compares v2 against the baselines only
   (QCD-style/Overlay/NestedTexture-inspired, QR/Aztec-style, CSK802-4/8, OOK, QCD-OCC, genie). The binding margin (R2) also includes the
   v1 family (HNCSM v1, v1-base) and v2-CS. Including v1-base in E2 could only make survival stricter.
   **Headline = binding margin.** A claimed advantage is the minimum over all comparison schemes (v1, v1-base, v2-CS,
   QCD, Overlay, NestedTexture, CSK802-4/8, OOK, genie) × {native payload, 48-bit equal payload}
   (`results/benchmark/c2_binding_margins.csv`).
6. **Shared corner finder.** All schemes use the same corner finder (minAreaRect on the thresholded frame; scale-free variant for IMX219).
   Per-scheme oracle−detector gaps are part of the result (scheme × detector interaction). A bias in favour of schemes whose edge
   LEDs are always lit is suspected but not shown.
7. **Genie (oracle) corners** for all spatial schemes (`genie_corners=True`): same seeds, same RNG consumption, true corner
   positions. Detector loss = oracle − detector; modulation loss = what remains (`oracle_vs_detector*.csv`).
8. **Seed replication.** Two further disjoint master seeds (A = 31415926, B = 27182818, each with its own tuning seeds).
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
- IMX219: every IMX219 result uses the current preset `imx219f`, **photometrically uncalibrated (sourced geometry and noise)**.
  Matching the CQ sensitivity would need an effective QE of 1.5–2.16 (impossible as QE); the ×3 runs are not shipped.
  The published QCD-OCC BER (1.13e-2) is matched by this preset near Tx brightness 1/2048, not the 1/128 used in E3.
  Photometric scale uncertainty ≈ ×1–×3, plus this Tx-brightness fit mismatch.
- e3claims@imx219f run meta records worktree commit 83b67a7 although the group started at 8d579f2; the only diff between
  those commits is the seed line-up (`lineup_seed`), which this group does not use.

## Limitations
- **M4 (hardware):** no hardware validation. The only external anchors considered are listed in `docs/ANCHORS.md`; none was
  reproduced.
- **M7 (parameter uncertainty):** no Latin-hypercube / sensitivity study over sensor and optics parameters was run;
  results are conditional on the presets. Many comparisons are reported without multiplicity correction; CIs are per comparison.
- Single matrix geometry (8×8, P = pixels/LED set by distance); one LED spectrum model.

## Run-meta provenance (R9)
Of the four -dirty run metas, only e3valid was regenerated from a clean commit (83b67a7; all arrays np.array_equal to the shipped npz).
e1sweep, e1dec and e2_P33 were not regenerated (time budget); the Research Validator regenerated sampled arrays (57/57 bit-identical: e1sweep P33 3.25 m, P42 3.0 m; e1dec P33 3.5 m, P25 3.0 m; E2 P33 d3.25 1/256) from a89ad29.
