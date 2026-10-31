"""Review round-1 E4 traceability outputs (results/review_r1/):
  c2_crc48.csv      C2 native and 48-bit-CRC margins (v2 - best opponent, paired CRN bootstrap) at 3.0/3.25/3.5 m, P25/P33/P42,
                    from results/phys_sym/sweeps_PHYS_P*.npz (same computation as hncsm_paper/review/recompute_c2.py)
  trow_range.csv    per-scheme range of goodput across t_row {0,10,27 us} (results/audit_r1/trow.csv)
  seed_sets.csv     v2 and QCD-style goodput at 3.0 m P33 in the two seed sets (sweep EWP vs claims CP)
  corner_error.csv  real-finder corner error vs distance (python -m experiments.e4_trace corners; IMX174 and IMX219)"""
import os, sys, numpy as np, pandas as pd
from experiments.audit_r1_report import G, SCH, HN, BASEL
from experiments.stats import paired_diff
from experiments.run import RES
OUT = os.path.join(RES, 'review_r1')

def c2_crc48():
    rows = []
    for P in (25, 33, 42):
        z = np.load(os.path.join(RES, 'phys_sym', f'sweeps_PHYS_P{P}.npz'), allow_pickle=True)
        for i, d in ((10, 3.0), (11, 3.25), (12, 3.5)):
            pre = f'distance_m|{i}|eval'; v2 = G(z, pre, 'HNCSM v2')
            nat = {n: G(z, pre, n) for n in SCH if n != 'HNCSM v2' and f'{pre}|{n}|err' in z.files}
            bn = max(nat, key=lambda n: nat[n].mean()); dn = paired_diff(v2, nat[bn])
            b48 = {n: G(z, pre, n, 48) for n in BASEL if f'{pre}|{n}|err' in z.files}
            bb = max(b48, key=lambda n: b48[n].mean()); d48 = paired_diff(v2, b48[bb])
            rows.append(dict(budget=P, distance_m=d, v2=round(v2.mean(), 2), native_best=bn, native_margin=round(dn[0], 2), native_lo=round(dn[1], 2),
                             native_hi=round(dn[2], 2), crc48_best_nonHNCSM=bb, crc48_margin=round(d48[0], 2), crc48_lo=round(d48[1], 2), crc48_hi=round(d48[2], 2),
                             note='identical to native: opponent is natively a 48-bit scheme' if bb == bn else ''))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'c2_crc48.csv'), index=False); return rows

def trow_range():
    t = pd.read_csv(os.path.join(RES, 'audit_r1', 'trow.csv'))
    r = t.groupby(['distance_m', 'scheme']).goodput.agg(lambda x: x.max() - x.min()).reset_index(name='range_bps')
    r.to_csv(os.path.join(OUT, 'trow_range.csv'), index=False); return r

def seed_sets():
    from experiments.audit_r1_report import G
    zs = np.load(os.path.join(RES, 'phys_sym', 'sweeps_PHYS_P33.npz')); zc = np.load(os.path.join(RES, 'phys_sym', 'claims.npz'))
    q = 'QCD-style-inspired (Vasantha22)'; rows = []
    for lab, z, pre, seed in (('sweep (EWP)', zs, 'distance_m|10|eval', "cond_seed('distance_m',10,SEED)"),
                              ('claims (CP)', zc, 'd3.0|1/1500|1/128|eval', "cond_seed('d3.0',0,SEED)")):
        a, b = G(z, pre, 'HNCSM v2'), G(z, pre, q); d = paired_diff(a, b)
        rows.append(dict(seed_set=lab, seed_expr=seed, symbols=len(a), v2=round(a.mean(), 2), qcd=round(b.mean(), 2), margin=round(d[0], 2), lo=round(d[1], 2), hi=round(d[2], 2)))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'seed_sets.csv'), index=False); return rows

def _corner_job(a):
    pname, d, f0, n = a
    from channel import physical as ph, presets_phys as pp
    from experiments.common import power_scales
    from tx.schemes import HNCSMv2
    from rx.finder import find_corners
    import json, config
    br = json.load(open(os.path.join(OUT, 'e3_calibration.json')))['brightness']
    if pname == 'imx174': p = dict(ph.P)
    elif pname == 'imx219': p = pp.imx219(br)                       # review-r1 preset (fixed min_dn = 8 finder)
    elif pname == 'imx219cq': p = pp.imx219b(br)                    # benchmark r0: CQ-sensitivity QE + scale-free finder
    else: p = pp.imx219(br); p.update(finder='scalefree', finder_k=pp.FINDER_K)   # 'imx219f': scale-free finder
    s = HNCSMv2(); sc = power_scales([s], 33.011, 'equal', False)[0][s.name]; out = []
    for f in range(f0, f0 + n):
        rng = np.random.RandomState(config.cond_seed(f'corner-{d}', f))
        es, ct, _ = ph.render_mean_e([s.encode(list(rng.randint(0, 2, s.nbits))) * sc], d, rng=rng, p=p)
        c = find_corners(ph.capture(es[0], rng, p=p), p); pitch = np.linalg.norm(ct[1] - ct[0]) / 8
        out.append((pitch, np.nan if c is None else float(np.linalg.norm(c - ct, axis=1).mean() / pitch)))
    return pname, d, out

def corners(procs=6, n=200, sensors=('imx174', 'imx219'), fname='corner_error.csv'):
    from multiprocessing import Pool
    ds = [0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5, 4.0, 5.0]
    work = [(pn, d, f0, 50) for pn in sensors for d in ds for f0 in range(0, n, 50)]
    with Pool(procs) as pl: res = pl.map(_corner_job, work)
    acc = {}
    for pn, d, o in res: acc.setdefault((pn, d), []).extend(o)
    rows = []
    for (pn, d), o in sorted(acc.items()):
        pit = np.array([x[0] for x in o]); e = np.array([x[1] for x in o]); ok = ~np.isnan(e)
        rows.append(dict(sensor=pn, distance_m=d, frames=len(o), px_per_led=round(pit.mean(), 3), detect_fail_frac=round(1 - ok.mean(), 4),
                         gross_err_frac_gt0p5pitch=round(float((e[ok] > 0.5).mean()), 4) if ok.any() else np.nan, median_err_pitch=round(np.median(e[ok]), 4) if ok.any() else np.nan, p90_err_pitch=round(np.percentile(e[ok], 90), 4) if ok.any() else np.nan))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, fname), index=False); return rows

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    if 'corners_bench' in sys.argv[1:]:   # audit R1 acceptance: same corner seeds, old vs scale-free finder, both IMX219 presets
        print(pd.DataFrame(corners(int(os.environ.get('PROCS', '6')), sensors=('imx174', 'imx219', 'imx219f', 'imx219cq'), fname='corner_error_bench.csv')).to_string())
    elif 'corners' in sys.argv[1:]: print(pd.DataFrame(corners(int(os.environ.get('PROCS', '6')))).to_string())
    else:
        print(pd.DataFrame(c2_crc48()).to_string()); r = trow_range(); print(r.sort_values('range_bps').tail(3).to_string(), 'max', r.range_bps.max())
        print(pd.DataFrame(seed_sets()).to_string())
