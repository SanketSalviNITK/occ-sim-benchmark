"""Channel presets.
DEFAULT: the main-results configuration (bright, resolution/blur-limited).
low_light(exposure_ms): power-limited configuration (short exposure, high analog gain, small-pixel sensor).

Low-light physical justification (per-pixel numbers for a full-on white LED imaged over >= 1 pixel):
- PHOTO_E_PER_MS = 80 e-/ms: photo-electrons per ms of exposure from a full-drive LED pixel. This is a calibrated
  stand-in for 'dim indicator-class LED + small 1.0-1.4 um smartphone pixel + short exposure'; it gives 80 e- at 1 ms,
  i.e. shot-noise SNR ~9 at full drive and ~5 after scaling a CSK-8 frame to P=33; calibration scan (20/40/80 e-/ms x P 15/33 x 1/2/3 m) in README. We picked it so that power
  matters at mid range (it is NOT derived from a radiometric link budget).
- Full well 4000 e- and 8-bit ADC at analog gain 1.5 DN/e- (high-ISO mode: saturation at ~170 e-), so the low
  signal is not lost in quantisation. Typical small-pixel CMOS: full well 3-6 ke-, read noise 1.5-3 e- at high gain.
- Read noise 3 e- rms (high-gain mode); dark current 20 e-/s at room temperature -> 0.02 e- per 1 ms (negligible),
  plus a 0.5 e- fixed per-frame dark/black-level offset term modelled as extra Poisson electrons.
- Ambient 0.03 of LED level as in DEFAULT (scaled with exposure in the same way as the LED signal).
"""
from .sensor import SensorParams

PHOTO_E_PER_MS = 80.0
LL_FULL_WELL = 4000.0
LL_GAIN_DN_PER_E = 1.5
LL_READ_NOISE = 3.0
LL_DARK_E_PER_S = 20.0
LL_DARK_OFFSET_E = 0.5

def default():
    return SensorParams()

def low_light(exposure_ms=1.0):
    sp = SensorParams()
    sp.full_well_e = LL_FULL_WELL
    sp.exposure_gain = PHOTO_E_PER_MS * exposure_ms / LL_FULL_WELL   # fraction of full well for a full white LED
    sp.read_noise_e = LL_READ_NOISE
    sp.dark_e = LL_DARK_E_PER_S * exposure_ms / 1000.0 + LL_DARK_OFFSET_E
    sp.conversion_gain = LL_GAIN_DN_PER_E
    return sp
