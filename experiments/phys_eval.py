"""Symbol-level evaluation on the PHYSICAL channel: asynchronous free-running camera (random phase per symbol),
rolling-shutter row mixing of the previous/current/next Tx symbol, real corner detector, and frame selection.
Protocol (ASSUMED): the receiver associates each captured frame with the Tx symbol whose interval contains the frame's
ROI mid-exposure time (equivalent to the sequence-number association of Nguyen et al. 2021); among the frames of a
symbol it keeps the one with the smallest re-encoding residual sum ||y - b - M d_hat||^2 (a receiver-side rule).
A symbol with no frame, or whose frames all fail detection, is decoded as random bits."""
import numpy as np, config
from channel import physical as ph
from rx.sampler import rectify_and_sample
from rx.refs import refs
from rx.finder import find_corners

MAX_BITS = 256

def sat_fraction(roi, sat_e, lit_frac=0.15):
    """Fraction of LIT ROI pixels (mean e- > lit_frac * ROI peak) whose mean e- >= full well; always in [0, 1].
    (Audit r2 F4: the numerator used to count saturated pixels over the whole ROI while dividing by the lit count.)"""
    lit = roi > lit_frac * max(float(roi.max()), 1e-9)
    return float((lit & (roi >= sat_e)).sum() / max(int(lit.sum()), 1))

def residual(s, samples, dark, bits):
    M, dk = refs(samples, dark)
    exp = dk + s.encode(list(bits)) @ M.T
    return float(((samples - exp) ** 2).sum())

def decode_symbol(s, drives, cond, rng, p):
    """Return decoded bits for the current symbol (drives = [prev, cur, next], already power-scaled)."""
    t_exp = cond.get('t_exp'); t_exp = None if t_exp is None else float(t_exp); te = p['t_exp'] if t_exp is None else t_exp
    es, corners_true, row0 = ph.render_mean_e(drives, cond['distance_m'], cond.get('yaw_deg', 0.0),
                                             cond.get('blur_sigma_px', 0.0), cond.get('lux', 27.0), rng, p, t_exp,
                                             cond.get('jitter', 0.02))
    nrows = es[0].shape[0]; T = 1.0 / p['f_tx']; Tf = 1.0 / p['fps']
    r_mid = row0 + nrows / 2
    t0 = rng.uniform(0, Tf)                       # asynchronous camera phase w.r.t. the symbol start
    starts = t0 + Tf * np.arange(-int(np.ceil((r_mid * p['t_row'] + te) / Tf)) - 1, int(np.ceil(T / Tf)) + 1)
    cands = [ts for ts in starts if 0 <= ts + r_mid * p['t_row'] + te / 2 < T]
    best = None
    for ts in cands:
        w = ph.row_weights(nrows, row0, ts, p, t_exp)
        if cond.get('sync'): w = np.zeros_like(w); w[:, 1] = 1.0
        e = sum(w[:, i, None, None] * es[i] for i in range(3))
        img = ph.capture(e, rng, p, t_exp)
        c = find_corners(img, p) if not cond.get('genie_corners') else corners_true
        if c is None: continue
        smp, dk = rectify_and_sample(img, c)
        b = s.decode(smp, dk); r = residual(s, smp, dk, b)
        if best is None or r < best[0]:
            ys = slice(int(max(corners_true[:, 1].min(), 0)), int(corners_true[:, 1].max()) + 1)
            xs = slice(int(max(corners_true[:, 0].min(), 0)), int(corners_true[:, 0].max()) + 1)
            roi = e[ys, xs].max(-1)
            sat = sat_fraction(roi, p['sat_e'])                                   # share of lit panel pixels whose mean e- >= full well
            mix = float(1 - w[ys, 1].mean())                                      # RS mixing: share of other symbols
            best = (r, b, sat, mix)
    if DIAG is not None: DIAG.append((np.nan, np.nan) if best is None else best[2:])
    return (None if best is None else best[1]), len(cands)

DIAG = None   # set to a list to collect (saturated-pixel fraction, RS mixing weight) of the selected frame per symbol

def eval_point_phys(schemes, scales, cond, frames, seed, p=None, f0=0, rec=None):
    """rec: optional dict, filled with rec[name] = dict(err=(frames x nbits) uint8 bit-error matrix, sat=, mix=) for
    per-symbol (cluster / paired-CRN bootstrap) statistics."""
    global DIAG
    p = p or ph.P
    res = {s.name: {l: [0, 0] for l, _ in s.layers} for s in schemes}
    stats = {s.name: dict(lost=0, frames_per_symbol=0) for s in schemes}
    for f in range(f0, f0 + frames):
        pay = [np.random.RandomState(config.cond_seed(k, f, seed)).randint(0, 2, MAX_BITS) for k in ('payload_prev', 'payload', 'payload_next')]
        cs = config.cond_seed('channel', f, seed)
        for s in schemes:
            b = pay[1][:s.nbits]
            drives = [s.encode(list(x[:s.nbits])) * scales[s.name] for x in pay]
            rng = np.random.RandomState(cs)
            DIAG = [] if rec is not None else None
            o, nc = decode_symbol(s, drives, cond, rng, p)
            stats[s.name]['frames_per_symbol'] += nc
            if o is None:
                o = rng.randint(0, 2, s.nbits); stats[s.name]['lost'] += 1
            o = np.asarray(o); i = 0
            if rec is not None:
                R = rec.setdefault(s.name, dict(err=[], sat=[], mix=[]))
                R['err'].append((o != b).astype(np.uint8)); R['sat'].append(DIAG[0][0]); R['mix'].append(DIAG[0][1])
            for l, n in s.layers:
                e = int((o[i:i+n] != b[i:i+n]).sum()); res[s.name][l][0] += e; res[s.name][l][1] += e > 0; i += n
    DIAG = None
    if rec is not None:
        for k in rec: rec[k] = {kk: np.array(v) for kk, v in rec[k].items()}
    return res, stats
