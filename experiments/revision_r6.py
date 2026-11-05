"""benchmark-r6 revision experiments (additive; no default changed). Per-symbol npz in results/phys_sym/r6_<group>.npz,
run metas in results/run_meta_R6_<group>.json, chunks checkpointed in $CKPT/<group>/ (same scheme as review_r1).
Groups:
  sens   : one-at-a-time sensitivity of the C2 points (IMX174, P33, 1/1500, brightness 1/128) to every Table-2 ASSUMED
           parameter, each at a LOW and HIGH level (SENS below, with the source of each range). Seeds = canonical
           claims/E2 seeds (cond_seed('d3.0'|'d3.25', 0, SEED), eval 1000 + tune 200), so every level is CRN-paired with
           the default cells of review_e2_P33.npz. Brightness is not re-run: its levels 1/64 and 1/256 are the E2 cells.
  geo80  : second panel geometry, 8x8 matrix with 80 mm side (10 mm pitch; Nguyen et al. 2021, doi:10.3390/s21093023,
           8 x 8 cm panel), IMX174 P33 1/1500 1/128, d in GEO_D, full line-up, eval 1000 + tune 200, seeds cond_seed('g80-d<d>').
  geoyaw30: 65 mm panel at 30 deg yaw (off-axis), same distances, seeds cond_seed('y30-d<d>').
  finder : dual-receiver pass on canonical seeds: for every candidate frame the shared finder AND oracle corners are
           evaluated on the SAME captured image (the finder does not consume RNG, so both paths are exactly CRN);
           records per-symbol detector/oracle bit errors, detection failures and gross errors (mean corner error >
           0.5 LED pitch) per candidate and for the selected frame. d in FIN_D; seeds cond_seed('d<d>', 0, SEED)
           (= claims/E2 seeds at 2.5/3.0/3.25/3.5 m). Detector arrays must equal review_e2_P33 / claims.npz (checked by
           experiments.r6_report).
  valid6 : QCD-OCC paper frame at 2 m, 25 fps, lux {27,149,304} x brightness VAL_BR, 2000 symbols, new seeds.
  phycom : PhyCom baselines as plugins (CSK-16-inspired Singh 2018; SM-PAM-inspired Leblebici 2026) + paper line-up,
           C2 points and distance sweep on canonical seeds (PHYCOM_D). Plugins only; lineup_r1 defaults untouched.
Usage: OMP_NUM_THREADS=1 PROCS=7 python -m experiments.revision_r6 sens geo80 geoyaw30 finder valid6 phycom"""
import os, sys, json, time, datetime, pickle, hashlib, numpy as np
from multiprocessing import Pool
import config
from experiments.review_r1 import lineup_r1, preset, code_key
from experiments.audit_r1 import BASE
from experiments.common import power_scales
from experiments.phys_eval import eval_point_phys, residual, MAX_BITS
from experiments.run import git_hash, RES
from channel import physical as ph
from rx.sampler import rectify_and_sample
from rx.finder import find_corners
from tx.schemes import QCDOCC

OUT = os.path.join(RES, 'phys_sym'); CHUNK = 50
C2_D = {'d3.0': 3.0, 'd3.25': 3.25}

def _cfa(k):
    """Off-diagonal crosstalk of the default CFA scaled by k, diagonal = 1 - row off-diagonal sum (rows stay normalised)."""
    c = np.array(ph.P['cfa'], float); off = c * (1 - np.eye(3)) * k
    return off + np.diag(1 - off.sum(1))

# factor -> (default label, {level: (pmod, condmod)}, source of the range)
SENS = {
    'lambert_m':   ('1', {'0.65': (dict(lambert_m=0.65), {}), '1.56': (dict(lambert_m=1.56), {})},
                    'm = -ln2/ln cos(theta_1/2) for half-power semi-angle 70 / 50 deg (Kahn & Barry 1997, doi:10.1109/5.554222); WS2812B sheet: 120 deg viewing angle (m = 1)'),
    'f_mm':        ('6 mm', {'4 mm': (dict(f_mm=4.0), {}), '8 mm': (dict(f_mm=8.0), {})},
                    'fixed-focus board lenses: RPi Camera v2 3.04 mm (docs/IMX219_PARAMETERS.md); 4-8 mm M12 range bracketing the ASSUMED 6 mm'),
    'f_number':    ('f/2.0', {'f/1.8': (dict(f_number=1.8), {}), 'f/2.8': (dict(f_number=2.8), {})},
                    'RPi Camera v2 f/2.0 (docs/IMX219_PARAMETERS.md); f/1.8-f/2.8 typical webcam / M12 range'),
    'focus_m':     ('1.0 m', {'0.5 m': (dict(focus_m=0.5), {}), '2.0 m': (dict(focus_m=2.0), {})},
                    'IMX219 preset focus 2.0 m ~ hyperfocal (docs/IMX219_PARAMETERS.md); 0.5 m near focus'),
    'bits':        ('8', {'10': (dict(bits=10), {}), '12': (dict(bits=12), {})},
                    'IMX174 ADC 12 bit, EMVA sheet Mono12 (doi:10.5281/zenodo.33041); 8 is the lowest common output'),
    'cfa':         ('x1', {'x0.5': (dict(cfa=_cfa(0.5)), {}), 'x2': (dict(cfa=_cfa(2.0)), {})},
                    'off-diagonal CFA crosstalk halved / doubled (no published IMX174-colour matrix; protocol choice)'),
    't_row':       ('27.4 us', {'0 (global)': (dict(t_row=0.0), {}), '10 us': (dict(t_row=10e-6), {})},
                    'IMX174 is global shutter (zenodo.33041) -> 0; 10 us as in audit trow group'),
    'f_tx':        ('15 /s', {'10 /s': (dict(f_tx=10.0), {}), '20 /s': (dict(f_tx=20.0), {})},
                    'Tx symbol rate below/above fps/2 (QCD-OCC sweeps 5-30 /s, doi:10.3390/app122010204)'),
    'reflectance': ('0.5', {'0.2': (dict(reflectance=0.2), {}), '0.8': (dict(reflectance=0.8), {})},
                    'indoor surface reflectances: floors 0.2-0.4, walls 0.5-0.8 (EN 12464-1:2021 recommended ranges)'),
    'jitter':      ('+-2 %', {'0 %': ({}, dict(jitter=0.0)), '+-5 %': ({}, dict(jitter=0.05))},
                    'distance jitter range (protocol choice; legacy +-2 %)'),
}
GEO_D = [2.0, 2.5, 3.0, 3.25, 3.5, 4.0, 4.5]
FIN_D = [2.0, 2.5, 3.0, 3.25, 3.5, 4.0]
VAL_BR = {'1/96': 1 / 96, '1/128': 1 / 128, '1/160': 1 / 160, '1/192': 1 / 192, '1/256': 1 / 256}
PHYCOM_D = [2.0, 2.5, 3.0, 3.25, 3.5, 4.0]
PHYCOM_NAMES = [
    'CSK-16-inspired (Singh et al., PhyCom 2018, doi:10.1016/j.phycom.2018.04.026)',
    'SM-PAM-inspired (Leblebici et al., PhyCom 2026, doi:10.1016/j.phycom.2026.103205)',
]

def job(a):
    key, cond, pmod, pref, seed, c0, n, only, mode = a
    if mode == 'unit':
        s = QCDOCC(); p = dict(ph.P); p.update(pmod); c = dict(BASE); c.update(cond); rec = {}
        eval_point_phys([s], {s.name: 1.0}, c, n, seed, p, f0=c0, rec=rec); return key, c0, rec
    sch = lineup_r1()
    if mode == 'phycom':
        from occbench import create, available; available()
        sch = sch + [create(n) for n in PHYCOM_NAMES]
    if only: sch = [s for s in sch if s.name in only]
    sc = power_scales(sch, pref, 'equal', False)[0]
    p = preset('imx174'); p.update(pmod); c = dict(BASE); c.update(cond); rec = {}
    if mode == 'dual': eval_point_dual(sch, sc, c, n, seed, p, f0=c0, rec=rec)
    else: eval_point_phys(sch, sc, c, n, seed, p, f0=c0, rec=rec)
    return key, c0, rec

def _ijob(a): return a[0], job(a[1])

def jobs_for(group):
    J = []   # (key, cond, pmod, pref, seed, n, only, mode)
    if group == 'sens':
        for f, (_, lv, _) in SENS.items():
            for ln, (pm, cm) in lv.items():
                for cn, d in C2_D.items():
                    c = dict(distance_m=d, t_exp=1 / 1500, **cm); pmb = dict(brightness=1 / 128, **pm); k = f'{f}={ln}|{cn}|1/1500|1/128'
                    J.append((k + '|eval', c, pmb, 33.011, config.cond_seed(cn, 0, config.SEED), 1000, None, 'std'))
                    J.append((k + '|tune', c, pmb, 33.011, config.cond_seed(cn, 0, config.TUNE_SEED), 200, None, 'std'))
    elif group in ('geo80', 'geoyaw30'):
        tag, pm, cm = ('g80', dict(panel_mm=80.0), {}) if group == 'geo80' else ('y30', {}, dict(yaw_deg=30.0))
        for d in GEO_D:
            cn = f'd{d}'; c = dict(distance_m=d, t_exp=1 / 1500, **cm); k = f'{cn}|1/1500|1/128'
            J.append((k + '|eval', c, dict(brightness=1 / 128, **pm), 33.011, config.cond_seed(f'{tag}-{cn}', 0, config.SEED), 1000, None, 'std'))
            J.append((k + '|tune', c, dict(brightness=1 / 128, **pm), 33.011, config.cond_seed(f'{tag}-{cn}', 0, config.TUNE_SEED), 200, None, 'std'))
    elif group == 'finder':
        for d in FIN_D:
            cn = f'd{d}'; J.append((f'{cn}|1/1500|1/128|eval', dict(distance_m=d, t_exp=1 / 1500), dict(brightness=1 / 128), 33.011,
                                    config.cond_seed(cn, 0, config.SEED), 1000, None, 'dual'))
    elif group == 'valid6':
        for lux in (27, 149, 304):
            for bn, br in VAL_BR.items():
                J.append((f'{lux}|{bn}|eval', dict(distance_m=2.0, lux=lux), dict(brightness=br, f_tx=25.0), None,
                          config.cond_seed(f'val6-2.0-{lux}-{bn}', 0, config.SEED), 2000, None, 'unit'))
    elif group == 'phycom':
        for d in PHYCOM_D:
            cn = f'd{d}'; c = dict(distance_m=d, t_exp=1 / 1500); k = f'{cn}|1/1500|1/128'
            J.append((k + '|eval', c, dict(brightness=1 / 128), 33.011, config.cond_seed(cn, 0, config.SEED), 1000, None, 'phycom'))
            J.append((k + '|tune', c, dict(brightness=1 / 128), 33.011, config.cond_seed(cn, 0, config.TUNE_SEED), 200, None, 'phycom'))
    return J

# ------------------------------------------------------------------ dual receiver (finder diagnostics), additive copy of phys_eval.decode_symbol
def decode_symbol_dual(s, drives, cond, rng, p):
    t_exp = cond.get('t_exp'); t_exp = None if t_exp is None else float(t_exp); te = p['t_exp'] if t_exp is None else t_exp
    es, ct, row0 = ph.render_mean_e(drives, cond['distance_m'], cond.get('yaw_deg', 0.0), cond.get('blur_sigma_px', 0.0),
                                    cond.get('lux', 27.0), rng, p, t_exp, cond.get('jitter', 0.02))
    nrows = es[0].shape[0]; T = 1.0 / p['f_tx']; Tf = 1.0 / p['fps']; r_mid = row0 + nrows / 2
    t0 = rng.uniform(0, Tf)
    starts = t0 + Tf * np.arange(-int(np.ceil((r_mid * p['t_row'] + te) / Tf)) - 1, int(np.ceil(T / Tf)) + 1)
    cands = [ts for ts in starts if 0 <= ts + r_mid * p['t_row'] + te / 2 < T]
    pitch = np.linalg.norm(ct[1] - ct[0]) / 8
    bd = bo = None; nfail = ngross = 0; sel_err = np.nan
    for ts in cands:
        w = ph.row_weights(nrows, row0, ts, p, t_exp)
        e = sum(w[:, i, None, None] * es[i] for i in range(3))
        img = ph.capture(e, rng, p, t_exp)
        c = find_corners(img, p)
        smp, dk = rectify_and_sample(img, ct); b = s.decode(smp, dk); r = residual(s, smp, dk, b)
        if bo is None or r < bo[0]: bo = (r, b)
        if c is None: nfail += 1; continue
        ce = float(np.linalg.norm(c - ct, axis=1).mean() / pitch); ngross += ce > 0.5
        smp, dk = rectify_and_sample(img, c); b = s.decode(smp, dk); r = residual(s, smp, dk, b)
        if bd is None or r < bd[0]: bd = (r, b, ce)
    return (None if bd is None else bd[1]), (None if bo is None else bo[1]), dict(
        ncand=len(cands), nfail=nfail, ngross=ngross, sel_cerr=(np.nan if bd is None else bd[2]))

def eval_point_dual(schemes, scales, cond, frames, seed, p, f0=0, rec=None):
    for f in range(f0, f0 + frames):
        pay = [np.random.RandomState(config.cond_seed(k, f, seed)).randint(0, 2, MAX_BITS) for k in ('payload_prev', 'payload', 'payload_next')]
        cs = config.cond_seed('channel', f, seed)
        for s in schemes:
            b = pay[1][:s.nbits]; drives = [s.encode(list(x[:s.nbits])) * scales[s.name] for x in pay]
            rng = np.random.RandomState(cs)
            od, oo, st = decode_symbol_dual(s, drives, cond, rng, p)
            if od is None: od = rng.randint(0, 2, s.nbits)
            R = rec.setdefault(s.name, dict(err=[], err_orc=[], ncand=[], nfail=[], ngross=[], sel_cerr=[]))
            R['err'].append((np.asarray(od) != b).astype(np.uint8)); R['err_orc'].append((np.asarray(oo) != b).astype(np.uint8))
            for k in ('ncand', 'nfail', 'ngross', 'sel_cerr'): R[k].append(st[k])
    for k in rec: rec[k] = {kk: np.array(v) for kk, v in rec[k].items()}

def run(group, procs):
    t = time.time(); J = jobs_for(group); work = []
    for key, cond, pm, pref, seed, N, only, mode in J:
        for c0 in range(0, N, CHUNK): work.append((key, cond, pm, pref, seed, c0, min(CHUNK, N - c0), only, mode))
    ck = os.path.join(os.environ.get('CKPT', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.ckpt')), 'r6_' + group); os.makedirs(ck, exist_ok=True)
    gh = os.environ.get('R6_CODE_KEY') or code_key()
    fn = lambda w: os.path.join(ck, hashlib.sha1((gh + repr(w)).encode()).hexdigest() + '.pkl')
    todo = [w for w in work if not os.path.exists(fn(w))]
    print(group, len(work), 'chunks,', len(work) - len(todo), 'already checkpointed', flush=True)
    with Pool(procs) as pl:
        for i, (j, r) in enumerate(pl.imap_unordered(_ijob, list(enumerate(todo)), chunksize=1)):
            w = todo[j]; pickle.dump(r, open(fn(w) + '.tmp', 'wb')); os.replace(fn(w) + '.tmp', fn(w))
            if i % 20 == 0: print(group, i + 1, '/', len(todo), round(time.time() - t), 's', flush=True)
    out = [pickle.load(open(fn(w), 'rb')) for w in work]
    out.sort(key=lambda x: (x[0], x[1])); arr = {}
    for key, c0, rec in out:
        for s, d in rec.items():
            for f, v in d.items(): arr.setdefault(f'{key}|{s}|{f}', []).append(v)
    arr = {k: np.concatenate(v) for k, v in arr.items()}
    os.makedirs(OUT, exist_ok=True); np.savez_compressed(os.path.join(OUT, f'r6_{group}.npz'), **arr)
    meta = dict(group=group, git=git_hash(), code_key=gh, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t), procs=procs,
                jobs=[dict(key=j[0], cond=j[1], pmod={k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in j[2].items()}, pref=j[3], seed=j[4], symbols=j[5], mode=j[7]) for j in J])
    json.dump(meta, open(os.path.join(RES, f'run_meta_R6_{group}.json'), 'w'), indent=0)
    print(group, 'done', meta['elapsed_s'], 's', flush=True)

if __name__ == '__main__':
    procs = int(os.environ.get('PROCS', '7'))
    for g in sys.argv[1:]: run(g, procs)
