"""Additive sensor presets for the PHYSICAL channel. channel/physical.P (IMX174) is NOT modified; a preset is
dict(ph.P) + overrides, passed as the p argument (functions in physical.py already take p).

IMX219 (Raspberry Pi Camera Module v2), rolling-shutter Bayer colour sensor. Sources per value:
 [RPI]  Raspberry Pi documentation, Camera Module hardware specifications table,
        https://www.raspberrypi.com/documentation/accessories/camera.html  (accessed 2026-10-31)
 [LNX]  Linux kernel drivers/media/i2c/imx219.c (torvalds/linux master, accessed 2026-10-31):
        IMX219_LLP_MIN = 0x0d78 = 3448 pixel clocks/line, IMX219_PIXEL_RATE = 182400000 (2-lane); RAW10 media bus formats
 [CQ]   K. Yonemoto, "CMOS image sensor performance measurement (final), PiCamera V1/V2 comparison", Interface (CQ
        Publishing) Oct 2026 issue p.162, Table 1, https://interface.cqpub.co.jp/wp-content/uploads/if2610_162.pdf
        (measured on the author's own PiCamera V2 module; includes unit-to-unit variation; picamera2 gain definition)
 [PAG]  M. Pagnutti et al., "Laying the foundation to use Raspberry Pi 3 V2 camera module imagery for scientific and
        engineering purposes", J. Electron. Imaging 26(1) 013014, 2017, doi:10.1117/1.JEI.26.1.013014 (BGGR, 10-bit raw)
Absolute per-channel QE is not published (Sony data are under NDA; [PAG] gives only normalised spectral response)."""
from channel import physical as ph

IMX219_OVR = dict(
    pixel_um=1.12,                      # [RPI] pixel size 1.12 um
    rows=1080, cols=1920,               # [RPI] 1080p video mode (1:1 crop of the 3280x2464 array); rows used for RS timing
    f_mm=3.04, f_number=2.0,            # [RPI] focal length 3.04 mm, F2.0
    focus_m=2.0,                        # ASSUMED fixed focus near the hyperfocal distance (f^2/(N*2px) = 2.06 m)
    t_row=3448 / 182.4e6,               # [LNX] line_length_pck 3448 / pixel rate 182.4 MHz = 18.90 us
    fps=30.0,                           # [RPI] 1080p supports up to 47 fps; 30 fps as in QCD-OCC Table 2
    bits=10,                            # [LNX]/[PAG] RAW10 output
    K12=0.177 * 4,                      # [CQ] conversion gain 0.177 DN/e at 10 bit (unity analog gain) -> K12 = 0.708
    sat_e=5800.0,                       # [CQ] saturation > 5800 e (lower bound; ADC clips at 1023/0.177 = 5780 e first)
    read_e=1.8,                         # [CQ] dark random noise 1.8 e
    dark_e_s=4.2,                       # ASSUMED: [CQ] gives DCNU 4.2 e/s (dark-current NON-UNIFORMITY, an FPN); the mean dark current is not given, DCNU used as a stand-in
    dsnu_e=0.32,                        # [CQ] DSNU 0.32 e
    prnu=0.0105,                        # [CQ] PRNU G 1.05 % (R 0.76, B 0.99)
    qe=(0.492, 0.671, 0.709),           # ASSUMED: IMX174 values kept (absolute IMX219 QE unpublished); scale absorbed by brightness calibration
    # cfa: ASSUMED, unchanged (no measured IMX219 crosstalk matrix); Bayer phase RGGB kept (sensor native BGGR [PAG], 1-px offset)
)
IMX219_BRIGHTNESS = None   # set by the E3 validation calibration (results/review_r1/e3_validation.csv)

def imx219(brightness=None):
    p = dict(ph.P); p.update(IMX219_OVR)
    if brightness is not None: p['brightness'] = brightness
    return p

# ---- benchmark r0 IMX219 configuration (audit R1): sensitivity-anchored QE scale + scale-free finder ----
# [CQ] Table 1 also gives a measured sensitivity S_G = 3400 e/(lx s) (G pixel, unity gain). ASSUMED: lx = sensor-plane
# illuminance with the simulator's white model (equal split over the 3 LED bands, 555-nm-equivalent photons/lm).
# The model's own G-pixel response to 1 lx s is computed below; QE is scaled uniformly so it equals S_G. The QE spectral
# SHAPE stays the IMX174 one (ASSUMED). The transmitter (brightness 1/128) is NOT changed: brightness is a Tx property.
CQ_SENS_G = 3400.0                      # [CQ] e/(lx s), G
FINDER_K = 12                            # chosen in results/benchmark/finder_tuning.csv (disjoint cornertune seeds; k is not binding: border sigma < 1 DN, floor q = 1 DN binds)
def model_sens_g(p):
    import numpy as np
    return (p['pixel_um'] * 1e-6) ** 2 * p['lm_to_photons'] * float((p['cfa'] @ (np.array(p['qe']) / 3.0))[1])
def imx219b(brightness=None, finder_k=None):
    p = imx219(brightness); s = CQ_SENS_G / model_sens_g(p)
    p['qe'] = tuple(float(q * s) for q in p['qe']); p['qe_scale_from_cq'] = s
    p['finder'] = 'scalefree'; p['finder_k'] = FINDER_K if finder_k is None else finder_k
    return p
