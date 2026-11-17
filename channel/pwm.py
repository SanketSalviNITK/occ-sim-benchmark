"""OPT-IN WS2812B temporal model (benchmark-r10). Nothing here is used unless p['pwm_hz'] (PWM) or p['ws_quant']
(integer drive codes) is set; with both off every caller takes the unchanged benchmark-r9 code path.

Physical picture (sources in docs/PWM_MODEL.md):
  * A WS2812B channel is not a DC current source. The driver switches the LED fully on for a fraction `duty` of each
    PWM period T_p = 1/pwm_hz and fully off otherwise. Measured PWM frame rates: 432 Hz (classic WS2812B, cpldcpu
    WS2812Tester findings; datasheet >= 400 Hz), 395.6 Hz (WS2812S), ~2 kHz (WS2812C/D; WS2812B-V5 per
    addressable.wiki citing the V5 datasheet) [cpldcpu 2020 blog].
  * duty = code / 255 with code = the 8-bit value actually latched into the LED, i.e. code = 255 * brightness * drive
    (brightness = the library's global setBrightness factor, P['brightness']). ASSUMED linear code->duty map: cpldcpu
    (2020) measured a mildly non-linear map (code 1 -> 1.1 us pulse at 395.6 Hz, i.e. ~1/2300 duty instead of 1/255),
    which is NOT modelled.
  * The PWM engine is clocked independently of the data interface and of the camera ("not synchronized to the data in
    any way", cpldcpu 2020), so each LED has its own phase. ASSUMED: phase phi_i ~ U[0, T_p) independently per LED and
    per captured frame (free-running oscillators with unknown frequency spread); the R, G and B channels of one LED
    share the phase and all pulses start at the beginning of the PWM cycle (leading-edge aligned); a new duty applies
    from the symbol boundary on (latch / ~125 us start-up delay not modelled).
  * Exposure integration: image row r integrates [a_r, a_r + t_exp] with a_r = t_start + (row0 + r) t_row (the same
    rolling-shutter timing as channel.physical.row_weights). The electrons collected from LED i, channel c, during
    symbol k are the full-on photon rate times the on-time inside [a_r, b_r] n [symbol k interval], computed in closed
    form (no time discretisation). Averaged over phi this equals the DC model exactly (duty x overlap).
  * The PWM factor is applied per LED at the image row where its blurred light lands (the per-LED footprint is
    rendered separately with the same geometry, PSF and supersampling as channel.physical.render_mean_e).
Random numbers: the geometry draws (distance jitter, sub-pixel offset) consume `rng` exactly like render_mean_e; the
PWM phases come from a side stream seeded from a hash of the rng state (rng is not advanced), so payloads, camera phase,
shot/read noise are common random numbers with the DC (benchmark-r9) runs."""
import hashlib, numpy as np, cv2
from . import physical as ph
from .geometry import project_panel, CameraIntrinsics
from .render import SS, PPL, LED_FILL
from .physical import ws_codes, ws_drive   # noqa: F401 (re-exported)

def _disc():
    yy, xx = np.mgrid[0:PPL, 0:PPL] + 0.5
    return (((xx - PPL / 2) ** 2 + (yy - PPL / 2) ** 2) <= (LED_FILL * PPL / 2) ** 2).astype(np.float32)

class Ctx:
    pass

def prepare(drives, distance_m, yaw_deg=0.0, extra_blur_px=0.0, lux=27.0, rng=np.random, p=ph.P, t_exp=None, jitter_frac=0.02):
    """Same geometry / rng draws as physical.render_mean_e, but returns per-LED blurred footprints so that a
    row-dependent per-LED temporal factor can be applied. drives: [prev, cur, next] 8x8x3 (power-scaled)."""
    n = p['n']; pitch = p['panel_mm'] / n
    d = distance_m * (1 + rng.uniform(-jitter_frac, jitter_frac)) if jitter_frac > 0 else distance_m
    cam = CameraIntrinsics(ph.f_px(p))
    c = project_panel(d, yaw_deg, 0.0, 0.0, n, pitch, cam) + rng.uniform(0, 1, 2)
    lo = np.floor(c.min(0)) - 12; size = (np.ceil(c.max(0)) + 12 - lo).astype(int)
    dst = ((c - lo) * SS).astype(np.float32)
    src = np.array([[0, 0], [n * PPL, 0], [n * PPL, n * PPL], [0, n * PPL]], np.float32)
    Hm = cv2.getPerspectiveTransform(src, dst)
    p_px = ph.f_px(p) * pitch * 1e-3 / d
    disc_px = np.pi * (LED_FILL * p_px / 2) ** 2 * max(np.cos(np.radians(yaw_deg)), 1e-3)
    X = Ctx(); X.phot = ph.received_photons(d, yaw_deg, 0.0, p, t_exp) / disc_px
    sig = np.hypot(ph.psf_sigma_px(d, p), extra_blur_px)
    X.amb = ph.ambient_electrons(lux, p, t_exp); X.M = p['cfa'] * np.array(p['qe'])[None, :]
    W, Hh = int(size[0]), int(size[1]); X.shape = (Hh, W)
    disc = _disc(); kmax = max(int(2 * np.ceil(3 * s) + 1) for s in sig); pad = kmax // 2 + 1
    X.fp = []
    for r in range(n):
        for col in range(n):
            q = cv2.perspectiveTransform(np.array([[[col * PPL, r * PPL]], [[(col + 1) * PPL, r * PPL]], [[(col + 1) * PPL, (r + 1) * PPL]], [[col * PPL, (r + 1) * PPL]]], np.float64), Hm)[:, 0] / SS
            x0 = max(int(np.floor(q[:, 0].min())) - 1, 0); x1 = min(int(np.ceil(q[:, 0].max())) + 1, W)
            y0 = max(int(np.floor(q[:, 1].min())) - 1, 0); y1 = min(int(np.ceil(q[:, 1].max())) + 1, Hh)
            T = np.array([[1, 0, -x0 * SS], [0, 1, -y0 * SS], [0, 0, 1]], np.float64) @ Hm @ np.array([[1, 0, col * PPL], [0, 1, r * PPL], [0, 0, 1]], np.float64)
            hi = cv2.warpPerspective(disc, T, ((x1 - x0) * SS, (y1 - y0) * SS), flags=cv2.INTER_LINEAR)
            low = hi.reshape(y1 - y0, SS, x1 - x0, SS).mean((1, 3)).astype(np.float64)
            # blur in a zero-padded window (the full-frame render uses BORDER_REPLICATE on a 12-px dark margin)
            Y0, Y1, X0, X1 = max(y0 - pad, 0), min(y1 + pad, Hh), max(x0 - pad, 0), min(x1 + pad, W)
            win = np.zeros((Y1 - Y0, X1 - X0)); win[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = low
            f = np.empty(win.shape + (3,))
            for j in range(3):
                k = int(2 * np.ceil(3 * sig[j]) + 1)
                f[..., j] = cv2.GaussianBlur(win, (k, k), sig[j], borderType=cv2.BORDER_CONSTANT)
            X.fp.append((Y0, Y1, X0, X1, f))
    X.D = np.stack([np.asarray(ws_drive(np.asarray(Dk, float), p), float).reshape(n * n, 3) for Dk in drives])   # (3 sym, 64, 3)
    X.row0 = int(p['rows'] // 2 + lo[1]); X.corners = c - lo; X.p = p
    X.t_exp = p['t_exp'] if t_exp is None else t_exp
    return X

def side_phases(rng, n_led, p):
    """Per-LED PWM phases in [0, T_p) from a side stream seeded by the rng state (rng is NOT advanced)."""
    st = rng.get_state()
    seed = int.from_bytes(hashlib.sha256(b'pwm' + np.asarray(st[1]).tobytes() + int(st[2]).to_bytes(4, 'little')).digest()[:4], 'little')
    return np.random.RandomState(seed).uniform(0.0, 1.0 / float(p['pwm_hz']), n_led)

def _cum_on(t, phi, Tp, on):
    """On-time of a pulse train (on for `on` seconds at the start of every period Tp, starting at phi) in (-inf, t]
    relative to an arbitrary origin; differences give the on-time inside an interval."""
    u = t - phi; k = np.floor(u / Tp)
    return k * on + np.minimum(u - k * Tp, on)

def row_factors(X, t_start, phases=None):
    """Per image row, LED and LED channel: effective drive a[r, i, c] such that the mean electron image equals
    sum_i footprint_i[r, x, c] * a[r, i, c] * phot_c. Without PWM (phases None) a = sum_k w_k(r) D_k (DC model)."""
    p = X.p; Hh = X.shape[0]; t = X.t_exp; T = 1.0 / p['f_tx']
    a_r = t_start + (X.row0 + np.arange(Hh)) * p['t_row']; b_r = a_r + t
    out = np.zeros((Hh, X.D.shape[1], 3))
    for k, (s, e) in enumerate(((-T, 0.0), (0.0, T), (T, 2 * T))):
        u = np.maximum(a_r, s); v = np.minimum(b_r, e); ov = np.clip(v - u, 0, None)       # (H,)
        if phases is None:
            out += (ov / t)[:, None, None] * X.D[k][None]
            continue
        Tp = 1.0 / float(p['pwm_hz']); b = p['brightness']
        duty = np.clip(b * X.D[k], 0.0, 1.0)                                                # (64, 3)
        on = duty * Tp; ph_ = phases[:, None]
        L = _cum_on(v[:, None, None], ph_[None], Tp, on[None]) - _cum_on(u[:, None, None], ph_[None], Tp, on[None])
        L = np.where(ov[:, None, None] > 0, np.clip(L, 0, None), 0.0)
        out += L / (b * t)
    return out

def compose(X, a):
    """Mean-electron image (H x W x 3 sensor channels) from per-row effective drives a (H x 64 x 3)."""
    rad = np.zeros(X.shape + (3,))
    for i, (Y0, Y1, X0, X1, f) in enumerate(X.fp):
        rad[Y0:Y1, X0:X1] += f * a[Y0:Y1, i, None, :]
    return (rad * X.phot[None, None, :]) @ X.M.T + X.amb[None, None, :]

def frame_e(X, t_start, rng):
    """Mean electrons of one captured frame starting at t_start (PWM if p['pwm_hz'], else DC)."""
    ph_ = side_phases(rng, X.D.shape[1], X.p) if X.p.get('pwm_hz') else None
    return compose(X, row_factors(X, t_start, ph_))
