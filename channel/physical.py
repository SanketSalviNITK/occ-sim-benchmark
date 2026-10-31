"""PHYSICAL channel (literature-sourced where possible). The legacy channel (render.py/sensor.py) is untouched.

Every parameter is in PARAMS with a 'src' tag: a verified DOI, a datasheet (no DOI), or 'ASSUMED'.
Pipeline per symbol: LED drive -> Lambertian LOS link budget (Komine & Nakagawa 2004; Kahn & Barry 1997) -> photons per
pixel over the LED's projected footprint -> thin-lens defocus (Pentland 1987) + Airy (Gaussian approx., Zhang et al.
2007) PSF -> CFA x QE -> rolling-shutter row mixing of adjacent symbols (Danakis 2012) -> EMVA 1288 sensor
(Poisson shot+dark, DSNU, PRNU, Gaussian read noise, saturation, quantisation; IMX174 values from EMVA 1288 datasheet
doi:10.5281/zenodo.33041) -> Malvar-He-Cutler demosaic (ICASSP 2004) -> 8-bit RGB."""
import numpy as np, cv2
from .geometry import project_panel, CameraIntrinsics
from .render import panel_texture, SS, PPL, LED_FILL

H_PLANCK, C_LIGHT = 6.62607015e-34, 2.99792458e8
P = dict(
    # --- transmitter: WS2812B-64 8x8 matrix (QCD-OCC prototype, doi:10.3390/app122010204, Table 2: 6.5 x 6.5 cm)
    n=8, panel_mm=65.0,                      # src: Vasantha & Salvi 2022 Table 2 (Tx dimension 6.5 cm)
    lam_nm=(622.5, 523.5, 466.0),            # src: WS2812B datasheet (Worldsemi), dominant wavelength mid-range, no DOI
    Iv_cd=(0.405, 0.690, 0.190),             # src: WS2812B datasheet luminous intensity mid-range (390-420/660-720/180-200 mcd)
    V_lam=(0.3568, 0.7778, 0.0770),          # src: CIE 1931 2deg ybar = V(lambda) (CIE 015:2018, doi:10.25039/TR.015.2018) at 622/524/466 nm
    xy=((0.6954, 0.3045), (0.1060, 0.8292), (0.1335, 0.0427)),  # src: CIE 1931 chromaticity of monochromatic lambda (same table); narrowband ASSUMED
    lambert_m=1.0,                           # ASSUMED: Lambertian (half-power semi-angle 60 deg); datasheet gives only 'wide' scattering angle
    brightness=1 / 128,                      # ASSUMED: WS2812B global dimming (~setBrightness 2/255); at full brightness a lit LED is ~100x over full well at 1/1500 s (see METHODS)
    # --- lens (ASSUMED: generic fixed-focus camera module; no cited lens)
    f_mm=6.0, f_number=2.0, focus_m=1.0,     # ASSUMED
    # --- sensor: Sony IMX174 (Basler acA1920-155um), EMVA 1288 datasheet m0728, doi:10.5281/zenodo.33041, gain 12 dB
    pixel_um=5.86, rows=1216, cols=1936,     # src: zenodo.33041
    qe=(0.492, 0.671, 0.709),                # src: zenodo.33041, eta at 630.1 / 533.9 / 465.8 nm
    read_e=4.41, sat_e=7863.0, dark_e_s=5.6, dsnu_e=0.81, prnu=0.0047,   # src: zenodo.33041 (sigma_d, mu_e.sat, mu_c, DSNU1288, PRNU1288)
    K12=0.501,                               # src: zenodo.33041 system gain DN/e- at 12 bit
    bits=8,                                  # ASSUMED 8-bit output: K8 = K12/16
    cfa=np.array([[0.85, 0.10, 0.05], [0.12, 0.78, 0.10], [0.04, 0.14, 0.82]]),  # ASSUMED CFA transmittance (IMX174 measured is mono)
    # --- timing
    fps=30.0,                                # src: QCD-OCC Table 2 (30 fps)
    t_exp=1 / 1500,                          # src: QCD-OCC Table 2 (1/1500 s)
    t_row=1 / (30.0 * 1216),                 # ASSUMED rolling-shutter line time (readout spans the frame period); IMX174 itself is global shutter
    f_tx=15.0,                               # ASSUMED protocol: Tx symbol rate = fps/2 (oversampling, cf. Nguyen 2021 doi:10.3390/s21093023)
    # --- ambient
    reflectance=0.5,                         # ASSUMED background reflectance
    lm_to_photons=555e-9 / (H_PLANCK * C_LIGHT) / 683.0,   # 555-nm-equivalent photons per lumen (ASSUMED spectrum)
    corner_jitter_px=None,                   # real detector is used instead
)

def sensor_K(p=P): return p['K12'] / 2 ** (12 - p['bits'])

def photon_rate_per_sr(p=P):
    """On-axis photon radiant intensity per LED channel at full drive [photons/s/sr]: I_e = I_v / (683 V(lam))."""
    lam = np.array(p['lam_nm']) * 1e-9
    Ie = np.array(p['Iv_cd']) / (683.0 * np.array(p['V_lam']))          # W/sr
    return Ie * lam / (H_PLANCK * C_LIGHT)

def received_photons(d_m, phi_deg=0.0, psi_deg=0.0, p=P, t_exp=None):
    """Komine & Nakagawa (2004) LOS: P_r = P_t (m+1)/(2 pi d^2) A cos^m(phi) cos(psi), with I0 = P_t (m+1)/(2 pi),
    A = pi (f/2N)^2 the entrance pupil. Returns photons per exposure per LED channel at full drive (x brightness)."""
    t = p['t_exp'] if t_exp is None else t_exp; m = p['lambert_m']
    A = np.pi * (p['f_mm'] * 1e-3 / (2 * p['f_number'])) ** 2
    g = np.cos(np.radians(phi_deg)) ** m * np.cos(np.radians(psi_deg))
    return photon_rate_per_sr(p) * p['brightness'] * A * g / d_m ** 2 * t

def psf_sigma_px(d_m, p=P):
    """Thin-lens blur-circle diameter c = f^2 |d - d_f| / (N d (d_f - f)) (Pentland 1987), pillbox -> Gaussian with
    equal 2nd moment sigma = c/4; Airy -> Gaussian sigma = 0.42 lambda N (Zhang et al. 2007, NA = 1/(2N)).
    Returns per-LED-channel sigma in pixels (pixel aperture integration is done by area resampling)."""
    f = p['f_mm'] * 1e-3; N = p['f_number']; pix = p['pixel_um'] * 1e-6; df = p['focus_m']
    c = f * f * abs(d_m - df) / (N * d_m * (df - f))
    s_def = c / 4 / pix
    s_airy = 0.42 * np.array(p['lam_nm']) * 1e-9 * N / pix
    return np.sqrt(s_def ** 2 + s_airy ** 2)

def ambient_electrons(lux, p=P, t_exp=None):
    """Camera equation E_img = E_scene rho / (4 N^2) (Lambertian background, on-axis, no vignetting) -> photons/pixel,
    white light split equally over the three LED bands (ASSUMED), x QE x CFA."""
    t = p['t_exp'] if t_exp is None else t_exp
    Eimg = lux * p['reflectance'] / (4 * p['f_number'] ** 2)
    nph = Eimg * (p['pixel_um'] * 1e-6) ** 2 * t * p['lm_to_photons']
    return nph * (p['cfa'] @ (np.array(p['qe']) / 3.0))

def f_px(p=P): return p['f_mm'] / (p['pixel_um'] * 1e-3)

def render_mean_e(drives, distance_m, yaw_deg=0.0, extra_blur_px=0.0, lux=27.0, rng=np.random, p=P, t_exp=None,
                  jitter_frac=0.02):
    """drives: list of 8x8x3 drive arrays (e.g. [prev, cur, next]) rendered with the SAME geometry.
    Returns list of mean-electron images (H x W x 3 sensor channels, before CFA sampling), true LED-panel corners
    (image px), and the sensor row index of image row 0."""
    n = p['n']; pitch = p['panel_mm'] / n
    d = distance_m * (1 + rng.uniform(-jitter_frac, jitter_frac)) if jitter_frac > 0 else distance_m
    cam = CameraIntrinsics(f_px(p))
    c = project_panel(d, yaw_deg, 0.0, 0.0, n, pitch, cam) + rng.uniform(0, 1, 2)
    lo = np.floor(c.min(0)) - 12; size = (np.ceil(c.max(0)) + 12 - lo).astype(int)
    dst = ((c - lo) * SS).astype(np.float32)
    src = np.array([[0, 0], [n * PPL, 0], [n * PPL, n * PPL], [0, n * PPL]], np.float32)
    Hm = cv2.getPerspectiveTransform(src, dst)
    # photons per pixel for a fully covered pixel of a full-drive LED: received photons / projected disc area (px)
    p_px = f_px(p) * pitch * 1e-3 / d
    disc_px = np.pi * (LED_FILL * p_px / 2) ** 2 * max(np.cos(np.radians(yaw_deg)), 1e-3)
    phot = received_photons(d, yaw_deg, 0.0, p, t_exp) / disc_px                       # per LED channel j
    sig = np.hypot(psf_sigma_px(d, p), extra_blur_px)
    amb = ambient_electrons(lux, p, t_exp)
    M = p['cfa'] * np.array(p['qe'])[None, :]                                          # sensor k <- LED j electrons/photon
    out = []
    for D in drives:
        hi = cv2.warpPerspective(panel_texture(np.asarray(D, np.float32)), Hm, (int(size[0] * SS), int(size[1] * SS)), flags=cv2.INTER_LINEAR)
        rad = cv2.resize(hi, (int(size[0]), int(size[1])), interpolation=cv2.INTER_AREA).astype(np.float64)
        for j in range(3):
            k = int(2 * np.ceil(3 * sig[j]) + 1)
            rad[..., j] = cv2.GaussianBlur(rad[..., j], (k, k), sig[j], borderType=cv2.BORDER_REPLICATE)
        out.append((rad * phot[None, None, :]) @ M.T + amb[None, None, :])
    row0 = int(p['rows'] // 2 + lo[1])
    return out, c - lo, row0

_FPN = {}
def _fpn(shape, p):
    """Fixed-pattern noise maps (DSNU offset in e-, PRNU gain) for this sensor; fixed seed = one physical sensor."""
    key = (shape, p['dsnu_e'], p['prnu'])
    if key not in _FPN:
        r = np.random.RandomState(1288)
        _FPN[key] = (r.normal(0, p['dsnu_e'], shape), 1 + r.normal(0, p['prnu'], shape))
    return _FPN[key]

def capture(e_rgb, rng=np.random, p=P, t_exp=None, raw=False):
    """EMVA 1288 linear model on an RGGB mosaic: mu_e = PRNU*e_photo + mu_dark; e = Poisson(mu_e) clipped at mu_e.sat;
    y = K (e + DSNU + N(0, sigma_d^2)), rounded/clipped to the ADC range; then Malvar-He-Cutler demosaic."""
    t = p['t_exp'] if t_exp is None else t_exp
    Hh, Ww, _ = e_rgb.shape
    mos = np.empty((Hh, Ww))
    mos[0::2, 0::2] = e_rgb[0::2, 0::2, 0]; mos[0::2, 1::2] = e_rgb[0::2, 1::2, 1]
    mos[1::2, 0::2] = e_rgb[1::2, 0::2, 1]; mos[1::2, 1::2] = e_rgb[1::2, 1::2, 2]
    dsnu, prnu = _fpn((Hh, Ww), p)
    mu = np.clip(mos, 0, None) * prnu + p['dark_e_s'] * t
    e = np.minimum(rng.poisson(mu), p['sat_e']) + dsnu + rng.normal(0, p['read_e'], mos.shape)
    dn = np.clip(np.round(e * sensor_K(p)), 0, 2 ** p['bits'] - 1)
    if raw: return dn
    if p['bits'] == 8: return np.clip(np.round(malvar_demosaic(dn)), 0, 255).astype(np.uint8)
    # >8-bit ADC: keep the finer quantisation, expressed on the 8-bit scale (downstream code divides by 255)
    return (np.clip(malvar_demosaic(dn), 0, 2 ** p['bits'] - 1) / 2 ** (p['bits'] - 8)).astype(np.float32)

# Malvar, He & Cutler (ICASSP 2004, doi:10.1109/ICASSP.2004.1326587) 5x5 gradient-corrected bilinear filters (x 1/8)
_G_AT_RB = np.array([[0, 0, -1, 0, 0], [0, 0, 2, 0, 0], [-1, 2, 4, 2, -1], [0, 0, 2, 0, 0], [0, 0, -1, 0, 0]]) / 8.0
_RB_AT_G_ROW = np.array([[0, 0, .5, 0, 0], [0, -1, 0, -1, 0], [-1, 4, 5, 4, -1], [0, -1, 0, -1, 0], [0, 0, .5, 0, 0]]) / 8.0
_RB_AT_G_COL = _RB_AT_G_ROW.T
_RB_AT_BR = np.array([[0, 0, -1.5, 0, 0], [0, 2, 0, 2, 0], [-1.5, 0, 6, 0, -1.5], [0, 2, 0, 2, 0], [0, 0, -1.5, 0, 0]]) / 8.0

def malvar_demosaic(m):
    """RGGB mosaic (R at even/even) -> RGB float."""
    m = m.astype(np.float64)
    f = lambda k: cv2.filter2D(m, -1, k, borderType=cv2.BORDER_REFLECT)
    g_rb, rb_row, rb_col, rb_br = f(_G_AT_RB), f(_RB_AT_G_ROW), f(_RB_AT_G_COL), f(_RB_AT_BR)
    Hh, Ww = m.shape; yy, xx = np.mgrid[0:Hh, 0:Ww]
    Rm = (yy % 2 == 0) & (xx % 2 == 0); Bm = (yy % 2 == 1) & (xx % 2 == 1)
    G1 = (yy % 2 == 0) & (xx % 2 == 1); G2 = (yy % 2 == 1) & (xx % 2 == 0)   # G1 in R rows, G2 in B rows
    R = np.where(Rm, m, 0.0); G = np.where(G1 | G2, m, 0.0); B = np.where(Bm, m, 0.0)
    G = np.where(Rm | Bm, g_rb, G)
    R = np.where(G1, rb_row, R); R = np.where(G2, rb_col, R); R = np.where(Bm, rb_br, R)
    B = np.where(G2, rb_row, B); B = np.where(G1, rb_col, B); B = np.where(Rm, rb_br, B)
    return np.stack([R, G, B], -1)

def row_weights(nrows, row0, t_start, p=P, t_exp=None):
    """Rolling shutter (Danakis 2012): image row r (sensor row row0+r) integrates [t_start + (row0+r) t_row, + t_exp].
    Returns (nrows x 3) overlap fractions with symbol intervals prev=[-T,0), cur=[0,T), next=[T,2T)."""
    t = p['t_exp'] if t_exp is None else t_exp; T = 1.0 / p['f_tx']
    a = t_start + (row0 + np.arange(nrows)) * p['t_row']; b = a + t
    w = np.stack([np.clip(np.minimum(b, e) - np.maximum(a, s), 0, None) for s, e in ((-T, 0), (0, T), (T, 2 * T))], 1)
    return w / t

DEBUG = False

def detect_corners(img, thr_frac=0.15, min_dn=8):
    """Real finder: background-subtracted image, each channel normalised by its 99.9th percentile, max over channels,
    threshold (ASSUMED) 15 % (bright level >= 8/0.15 DN) -> connected LED blobs (specks < 10 % of the 90th-pct blob area dropped) -> coarse panel from the
    minimum-area rectangle of the lit pixels -> refinement: intensity-weighted centroids of all lit LEDs within 0.4 pitch
    of their predicted centres -> least-squares homography to the canonical LED centres (3 iterations). Returns LED-panel corners (px) or None."""
    f = img.astype(np.float32)
    bg = np.median(np.concatenate([f[:4].reshape(-1, 3), f[-4:].reshape(-1, 3), f[:, :4].reshape(-1, 3), f[:, -4:].reshape(-1, 3)]), 0)
    dif = f - bg
    hi = np.maximum(np.percentile(dif.reshape(-1, 3), 99.9, axis=0), min_dn / thr_frac)   # per-channel bright level
    mask = ((dif / hi).max(-1) > thr_frac).astype(np.uint8)
    if mask.sum() < 4: return None
    nl, lab, st, _ = cv2.connectedComponentsWithStats(mask)
    if nl < 2: return None
    a = st[1:, cv2.CC_STAT_AREA]; keep = 1 + np.nonzero(a >= max(1, 0.1 * np.percentile(a, 90)))[0]   # drop specks (ASSUMED 10 %)
    wimg = np.clip((dif / hi).max(-1), 0, None)
    # coarse: minimum-area rectangle of all lit pixels = outer disc edges of the outermost LED rows/columns, i.e. inset
    # (0.5 - fill/2) LED units from the panel outline. (A dim colour pilot can be lost by the CFA; the rectangle is set
    # by the whole edge row, so it is robust to that.)
    ys, xs = np.nonzero(np.isin(lab, keep))
    if len(xs) < 4: return None
    box = cv2.boxPoints(cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32) + 0.5))
    o = np.argsort(np.arctan2(box[:, 1] - box[:, 1].mean(), box[:, 0] - box[:, 0].mean()))   # order: TL, TR, BR, BL
    box = box[o]; k0 = int(np.argmin(box.sum(1))); box = np.roll(box, -k0, 0).astype(np.float32)
    e = 0.5 - LED_FILL / 2
    can = np.array([[e, e], [8 - e, e], [8 - e, 8 - e], [e, 8 - e]], np.float32)
    if DEBUG: print('box', box.tolist())
    try: Hc = cv2.getPerspectiveTransform(can, box)
    except cv2.error: return None
    # refinement: intensity-weighted centroid of every lit LED within 0.4 pitch of its predicted centre, then a
    # least-squares homography (cv2.findHomography) to the canonical LED centres; 3 iterations
    H_, W_ = wimg.shape; yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float64) + 0.5   # pixel i spans [i, i+1)
    grid = np.array([[c + 0.5, r + 0.5] for r in range(8) for c in range(8)], np.float32)
    for _ in range(3):
        g = cv2.perspectiveTransform(grid[:, None], Hc)[:, 0]
        pc = cv2.perspectiveTransform(np.array([[[0, 0]], [[8, 0]], [[8, 8]], [[0, 8]]], np.float32), Hc)[:, 0]
        pitch = np.sqrt(max(cv2.contourArea(pc), 1)) / 8
        src, dst = [], []
        for (gx, gy), cc in zip(g, grid):
            x0, x1 = int(max(gx - pitch, 0)), int(min(gx + pitch + 1, W_)); y0, y1 = int(max(gy - pitch, 0)), int(min(gy + pitch + 1, H_))
            if x1 <= x0 or y1 <= y0: continue
            w = wimg[y0:y1, x0:x1] * ((((xx[y0:y1, x0:x1] - gx) ** 2 + (yy[y0:y1, x0:x1] - gy) ** 2) <= (0.4 * pitch) ** 2))
            if w.max() < thr_frac: continue
            src.append(cc); dst.append([(w * xx[y0:y1, x0:x1]).sum() / w.sum(), (w * yy[y0:y1, x0:x1]).sum() / w.sum()])
        if len(src) < 8: break
        Hn, _ = cv2.findHomography(np.array(src, np.float32), np.array(dst, np.float32), 0)
        if Hn is None: break
        Hc = Hn
    pc = cv2.perspectiveTransform(np.array([[[0, 0]], [[8, 0]], [[8, 8]], [[0, 8]]], np.float32), Hc)[:, 0]
    if not np.isfinite(pc).all() or cv2.contourArea(pc) < 16: return None
    return pc
