# WS2812B PWM dimming and integer drive codes (opt-in, benchmark-r10)

Code: `channel/pwm.py`, `channel/physical.py` (`P['pwm_hz']`, `P['ws_quant']`, `ws_codes`, `ws_drive`), decoder hooks in
`experiments/phys_eval.decode_symbol` and `experiments/revision_r6.decode_symbol_dual`. Tests: `tests/test_r10.py`.
Both options are **off by default** (`pwm_hz=None`, `ws_quant=False`); with them off every function takes the unchanged
benchmark-r9 code path and the per-symbol arrays are byte-identical to the shipped r9 npz files (tested against
`review_e2_P33.npz`, `r6_finder.npz` and `sweeps_PHYS_P33.npz`).

## Why
In benchmark-r9 a WS2812B channel is a DC emitter whose intensity is `drive x brightness x I_full`
(`received_photons()`), with `brightness = 1/128` standing for the library's global `setBrightness`. A WS2812B is a
constant-current driver switched by an internal PWM engine: the LED is either fully on or off, and the 8-bit value
latched into the LED sets the on-fraction of each PWM period. At the benchmark operating point the latched codes are
0, 1 or 2 (out of 255), i.e. each LED is on for at most ~18 us per 2.3 ms period at 432 Hz, while the camera exposes for
0.667 ms (1/1500 s). An exposure therefore sees 0 or 1 pulses of an LED, not its average intensity.

## Sources (values used)

| Quantity | Value used | Source | Type |
|---|---|---|---|
| PWM frame rate, original WS2812B | **432 Hz** (`PWM_432`) | cpldcpu, WS2812Tester "High-Level Findings", https://github.com/cpldcpu/WS2812Tester/blob/master/docs/findings.md ("the PWM frequency of the original WS2812B is 432Hz") | Measured (supply-current, MCU ADC) |
| PWM frame rate, WS2812B-V5 | **2 kHz** (`PWM_2K`) | same page, WS2812B-V5 section ("PWM frequency has been increased to ~2 kHz"); WS2812B-V5 datasheet "scan frequency 2 kHz" as quoted by https://addressable.wiki/protocols/ws2812b/ | Measured / datasheet |
| Datasheet minimum, pre-V5 WS2812B | >= 400 Hz | Worldsemi WS2812B datasheet "scan frequency not less than 400 Hz" as quoted by addressable.wiki (above) | Datasheet |
| WS2812S / WS2812C,D | 395.6 Hz / 2 kHz (not used) | T. (cpldcpu), "Power Analysis: Probing WS2812 RGB LEDs", 2020-12-19, https://cpldcpu.com/2020/12/19/power-analysis-probing-ws2812-rgb-leds/ | Measured (oscilloscope) |
| PWM independent of the data interface | free-running, "not synchronized to the data in any way" | cpldcpu 2020 (above) | Measured |
| 8-bit code per channel | integers 0..255 | WS2812B protocol (24-bit GRB word per LED) | Datasheet |

## Model
* duty = code/255 with code = 255 x brightness x drive (continuous by default; integers with `ws_quant`).
  **ASSUMED linear** code-to-duty map. cpldcpu measured a non-linear ("gamma-like") map: on the WS2812S code 1 gives a
  1.1 us pulse at 395.6 Hz (~1/2300 duty instead of 1/255), and the WS2812B/V5 show a "curious nonlinear relationship"
  between setting and current. No published curve with numbers usable as a parameter was found, so the map is not
  modelled; the measured non-linearity would make the low codes used here *dimmer and shorter* than modelled.
* Per LED one phase phi_i ~ U[0, T_p), **ASSUMED independent per LED and per captured frame** (free-running
  relaxation oscillators, cpldcpu 2020; frequency spread between LEDs not published). R, G, B of one LED share the phase
  and their pulses start at the beginning of the PWM cycle (**ASSUMED** leading-edge alignment). A new duty applies at
  the symbol boundary (the ~125 us PWM start-up delay after a data latch reported by cpldcpu 2020 is not modelled).
* Exposure integration: row r integrates [a_r, a_r + t_exp], a_r = t_start + (row0 + r) t_row (same rolling-shutter
  timing as `row_weights`). Electrons from LED i, channel c, during symbol k = full-on photon rate x on-time inside
  [a_r, b_r] n symbol k, in closed form (`_cum_on`). Averaged over phi this equals the DC model exactly
  (test `test_pwm_phase_average_equals_dc`).
* The factor is applied per LED at the image row where its blurred light lands: each LED's footprint is rendered
  separately with the same homography, supersampling, area resampling and PSF as `render_mean_e`; with PWM off the
  decomposition reproduces the full-frame render to < 1e-5 relative (`test_pwm_decomposition_equals_dc_render`).
* Random numbers: the geometry draws are identical to `render_mean_e`; phases come from a side stream seeded from the
  rng state (rng not advanced), so payloads, camera phase and sensor noise are common random numbers with the r9 runs
  and every r10 result is CRN-paired with its r9 counterpart.
* `ws_quant`: drive -> round(255 x brightness x drive)/255 (round-half-even, clipped to 0..255). **ASSUMED rounding**;
  libraries that scale by `(value * brightness) >> 8` truncate, which would zero even more LEDs.

## Not modelled (stated limitations)
* Non-linear code-to-duty map (above); the 0.6-1 us current ramp and "no output for codes 1-2" measured on
  WS2812C/D (cpldcpu 2020) - if the V5 behaves the same, the 1/128 operating point would emit (almost) no light on 2 kHz parts.
* LED-to-LED PWM frequency spread and drift; data-refresh latency (24 bit x 1.25 us per LED + reset).

## Results (B = 10000, unadjusted; full tables in `results/r10/SUMMARY_r10.md`)
* Codes at P33 (`results/r10/ws2812b_codes_at_P33.csv`): at brightness 1/128 the largest latched code is 2. With integer codes, 40-53 % of the lit channels of v2-CS, CSK802-8, CSK802-4 and Overlay round to 0. At 1/256, 7 of 11 entries emit no light. The maximum on-time per PWM period is 18.1 us at 432 Hz and 3.9 us at 2 kHz (HNCSM v2), and 14.2 / 3.1 us for QCD-style and v2-CS.
* C2 cell, shared finder, 1/1500 s (`results/r10/c2_r10_binding.csv`). Each row gives the HNCSM v2 binding margin at 3.0 m / 3.25 m:

  | Condition | 3.0 m | 3.25 m |
  |---|---|---|
  | DC | +150.0 [126.6, 173.4] | +107.58 [86.34, 129.0] |
  | PWM 432 Hz | −0.54 [−0.90, −0.24] | −0.66 [−1.08, −0.30] |
  | PWM 2 kHz | +31.8 [7.8, 56.4] | +34.2 [12.0, 55.8] |
  | Integer codes | +28.8 [8.4, 49.2] | +47.4 [25.2, 69.0] |
  | PWM 432 Hz + integer codes | −0.84 [−1.32, −0.42] | −0.90 [−1.38, −0.48] |

  Under PWM 432 Hz every entry is ≈0 bps.
* All-entry sweep 0.5-5 m (`results/r10/sweeps_r10_long.csv`, `sweep_table_PWM432Hz_detector.csv`, `sweep_table_PWM2kHz_detector.csv`). At 432 Hz all entries are ≤0.8 bps at every distance. At 2 kHz, v2 reaches 594 bps at 1 m (cap 1020) and CSK802-8 103 bps (cap 2580).
* Caveat: because the code-to-duty map is ASSUMED linear and the measured map is darker at low codes (see above), these PWM results are, if anything, optimistic for the 1/128 operating point.
