"""Audit R1: choose the scale-free finder constant k on DISJOINT seeds (cond_seed('cornertune-<d>', f)), never the
corner_error / eval seeds. Gross error = mean corner error > 0.5 LED pitch OR detection failure. Rule (fixed before
running): smallest mean gross-error fraction over d <= 3.5 m for imx219 (unscaled QE); ties -> larger k."""
import os, sys, numpy as np, pandas as pd, config
from multiprocessing import Pool
OUT = os.path.join(os.path.dirname(__file__), '..', 'results', 'benchmark')
KS = [2, 3, 4, 6, 8, 12]; DS = [0.5, 1.0, 2.0, 3.0, 3.5, 4.0, 5.0]; N = 60

def preset(pn, k):
    from channel import physical as ph, presets_phys as pp
    if pn == 'imx174': p = dict(ph.P)
    elif pn == 'imx219': p = pp.imx219(1 / 128)
    else: p = pp.imx219b(1 / 128, k)
    p['finder'] = 'scalefree'; p['finder_k'] = k; return p

def job(a):
    pn, k, d = a
    from channel import physical as ph
    from experiments.common import power_scales
    from tx.schemes import HNCSMv2
    from rx.finder import find_corners
    p = preset(pn, k); s = HNCSMv2(); sc = power_scales([s], 33.011, 'equal', False)[0][s.name]; g = []
    for f in range(N):
        rng = np.random.RandomState(config.cond_seed(f'cornertune-{d}', f))
        es, ct, _ = ph.render_mean_e([s.encode(list(rng.randint(0, 2, s.nbits))) * sc], d, rng=rng, p=p)
        c = find_corners(ph.capture(es[0], rng, p=p), p); pitch = np.linalg.norm(ct[1] - ct[0]) / 8
        g.append(1.0 if c is None else float(np.linalg.norm(c - ct, axis=1).mean() / pitch > 0.5))
    return dict(sensor=pn, k=k, distance_m=d, frames=N, gross_frac=np.mean(g))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    work = [(pn, k, d) for pn in ('imx219', 'imx219cq', 'imx174') for k in KS for d in DS]
    with Pool(int(os.environ.get('PROCS', '7'))) as pl: df = pd.DataFrame(pl.map(job, work))
    df.to_csv(os.path.join(OUT, 'finder_tuning.csv'), index=False)
    m = df[(df.sensor == 'imx219') & (df.distance_m <= 3.5)].groupby('k').gross_frac.mean()
    k = max(m.index[m == m.min()]); print(df.pivot_table(index=['sensor', 'k'], columns='distance_m', values='gross_frac').to_string()); print('chosen k', k)
    open(os.path.join(OUT, 'finder_k.txt'), 'w').write(str(k))
