"""E1 decomposition: v2-base-only variants (tx/ablation.py) on the run_phys distance seeds 2.25..4.0 m, P25/P33/42,
1000 symbols, CRN-paired with sweeps_PHYS_P*.npz and review_e1sweep.npz. Writes results/phys_sym/review_e1dec.npz."""
import os, json, time, datetime, numpy as np
from multiprocessing import Pool
import config
from tx.ablation import BaseOnly2LevelDecoder, BaseOnlyLevel075
from experiments.common import power_scales
from experiments.phys_eval import eval_point_phys
from experiments.audit_r1 import BASE
from experiments.review_r1 import DIST, PREFS, OUT, CHUNK
from experiments.run import git_hash, RES
from channel import physical as ph
IDX = [i for i, d in enumerate(DIST) if 2.2 <= d <= 4.01]

def job(a):
    b, i, c0, n = a
    sch = [BaseOnly2LevelDecoder(), BaseOnlyLevel075()]; sc = power_scales(sch, PREFS[b], 'equal', False)[0]
    c = dict(BASE); c['distance_m'] = float(DIST[i]); rec = {}
    eval_point_phys(sch, sc, c, n, config.cond_seed('distance_m', i, config.SEED), dict(ph.P), f0=c0, rec=rec)
    return f'P{b}|distance_m|{i}|eval', c0, rec

if __name__ == '__main__':
    t = time.time(); work = [(b, i, c0, CHUNK) for b in PREFS for i in IDX for c0 in range(0, 1000, CHUNK)]
    with Pool(int(os.environ.get('PROCS', '3'))) as pl: out = pl.map(job, work, chunksize=1)
    out.sort(key=lambda x: (x[0], x[1])); arr = {}
    for key, c0, rec in out:
        for s, d in rec.items():
            for f, v in d.items(): arr.setdefault(f'{key}|{s}|{f}', []).append(v)
    np.savez_compressed(os.path.join(OUT, 'review_e1dec.npz'), **{k: np.concatenate(v) for k, v in arr.items()})
    json.dump(dict(group='e1dec', git=git_hash(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t),
                   distances=[float(DIST[i]) for i in IDX], budgets=list(PREFS), symbols=1000, seeds="cond_seed('distance_m', i, SEED)"),
              open(os.path.join(RES, 'run_meta_REVIEW_e1dec.json'), 'w'), indent=0)
    print('e1dec done', round(time.time() - t), flush=True)
