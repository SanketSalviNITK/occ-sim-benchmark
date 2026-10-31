"""Audit R3/R8 ablation runs at P33, run_phys sweep seeds, distance index 10/11/12 (3.0/3.25/3.5 m), 1000 symbols.
  fact    : the missing factorial cell lit0.75 x 2-level decoder (equal-summed drive). The other three cells are in
            review_e1sweep (base-only) and review_e1dec ([2-level dec], [lit 0.75]); v2 in sweeps_PHYS_P33.
  radiant : v2, base-only, the 3 variants and QCD-style under RADIANT-equal power (audit_r1.scales_for 'radiant', pref 33.011).
Writes results/phys_sym/bench_<group>.npz + results/run_meta_BENCH_<group>.json."""
import os, sys, json, time, datetime, numpy as np, config
from multiprocessing import Pool
from tx.ablation import HNCSMv2BaseOnly, BaseOnly2LevelDecoder, BaseOnlyLevel075, Level075TwoLevelDecoder
from experiments.audit_r1 import BASE, scales_for, lineup
from experiments.phys_eval import eval_point_phys
from experiments.review_r1 import DIST, OUT, CHUNK
from experiments.run import git_hash, RES
from channel import physical as ph
IDX = [10, 11, 12]
V = lambda: [HNCSMv2BaseOnly(), BaseOnly2LevelDecoder(), BaseOnlyLevel075(), Level075TwoLevelDecoder()]

def job(a):
    g, i, c0, n = a
    if g == 'fact': sch = [Level075TwoLevelDecoder()]; mode = 'equal'
    else: sch = [s for s in lineup() if s.name in ('HNCSM v2', 'QCD-style-inspired (Vasantha22)')] + V(); mode = 'radiant'
    sc = scales_for(sch, 33.011, mode, False); c = dict(BASE, distance_m=float(DIST[i])); rec = {}
    eval_point_phys(sch, sc, c, n, config.cond_seed('distance_m', i, config.SEED), dict(ph.P), f0=c0, rec=rec)
    return f'P33|distance_m|{i}|eval', c0, rec, sc

if __name__ == '__main__':
    for g in sys.argv[1:]:
        t = time.time(); work = [(g, i, c0, CHUNK) for i in IDX for c0 in range(0, 1000, CHUNK)]
        with Pool(int(os.environ.get('PROCS', '7'))) as pl: out = pl.map(job, work, chunksize=1)
        out.sort(key=lambda x: (x[0], x[1])); arr = {}
        for key, c0, rec, sc in out:
            for s, d in rec.items():
                for f, v in d.items(): arr.setdefault(f'{key}|{s}|{f}', []).append(v)
        np.savez_compressed(os.path.join(OUT, f'bench_{g}.npz'), **{k: np.concatenate(v) for k, v in arr.items()})
        json.dump(dict(group=g, git=git_hash(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t),
                       scales=out[0][3], idx=IDX, seeds="cond_seed('distance_m', i, SEED)", symbols=1000), open(os.path.join(RES, f'run_meta_BENCH_{g}.json'), 'w'), indent=0)
        print(g, 'done', round(time.time() - t), flush=True)
