"""Image sensor: spectral crosstalk, exposure, Bayer CFA, shot/read noise, ADC, demosaic."""
import numpy as np, cv2
from dataclasses import dataclass, field

@dataclass
class SensorParams:
    full_well_e: float = 6000.0
    read_noise_e: float = 3.0
    exposure_gain: float = 0.75     # fraction of full well reached by a full-on white LED (exposure*ISO)
    bits: int = 8
    crosstalk: np.ndarray = field(default_factory=lambda: np.array(
        [[0.85, 0.10, 0.05],    # rows: sensor R,G,B response to LED R,G,B emission
         [0.12, 0.78, 0.10],
         [0.04, 0.14, 0.82]]))
    bayer: bool = True
    dark_e: float = 0.0                 # mean dark-current electrons per exposure (Poisson)
    conversion_gain: float = None       # DN per electron (analog gain/ISO); default = full scale at full well

def capture(radiance_rgb, sp: SensorParams, ambient=0.03, rng=np.random):
    """radiance_rgb: HxWx3 LED radiance in [0,1] (per LED channel). Returns uint8 RGB image."""
    amb = np.asarray(ambient, float)
    sig = radiance_rgb @ sp.crosstalk.T + (amb[..., None] if amb.ndim == 2 else amb)
    e = np.clip(sig * sp.exposure_gain, 0, None) * sp.full_well_e + sp.dark_e
    cg = sp.conversion_gain if sp.conversion_gain is not None else (2**sp.bits - 1) / sp.full_well_e
    if sp.bayer:
        H, W, _ = e.shape
        mos = np.empty((H, W))
        mos[0::2, 0::2] = e[0::2, 0::2, 0]; mos[0::2, 1::2] = e[0::2, 1::2, 1]
        mos[1::2, 0::2] = e[1::2, 0::2, 1]; mos[1::2, 1::2] = e[1::2, 1::2, 2]
        mos = np.minimum(rng.poisson(mos), sp.full_well_e) + rng.normal(0, sp.read_noise_e, mos.shape)
        dn = np.clip(np.round(mos * cg), 0, 2**sp.bits - 1).astype(np.uint8)
        return cv2.cvtColor(dn, cv2.COLOR_BayerBG2RGB)  # OpenCV naming quirk: BayerBG2RGB decodes an RGGB mosaic (verified with a pure-red test)
    e = np.minimum(rng.poisson(e), sp.full_well_e) + rng.normal(0, sp.read_noise_e, e.shape)
    return np.clip(np.round(e * cg), 0, 2**sp.bits - 1).astype(np.uint8)
