"""benchmark-r7 revision experiments (additive; no default changed, no physics/decoder change).
Re-uses the job runner of experiments.revision_r6 (same chunking / checkpoint / CRN scheme); outputs
results/phys_sym/r7_<group>.npz and results/run_meta_R7_<group>.json.
Groups:
  lamb30 : lambert_m sensitivity at 30 deg yaw (on axis cos^m(0) = 1, so the r6 on-axis lambert_m levels were a no-op by
           construction). 65 mm panel, yaw 30 deg, IMX174 P33 1/1500 1/128, lambert_m in {0.65, 1.56}, d in LAMB_D,
           seeds = r6 geoyaw30 seeds cond_seed('y30-d<d>') -> CRN-paired with the lambert_m = 1 cells of r6_geoyaw30.npz.
  fact   : full factorial focus_m {0.5,1,2} x f_mm {4,6,8} x f_number {2.0,2.8} x brightness {1/128,1/256} = 36 cells at
           the C2 points d3.0/d3.25, canonical claims/E2 seeds (eval 1000 + tune 200), IMX174 P33 1/1500. The default
           cell (1.0 m, 6 mm, f/2.0, 1/128) must reproduce review_e2_P33.npz (checked by experiments.r7_report).
Usage: OMP_NUM_THREADS=1 PROCS=7 python -m experiments.revision_r7 lamb30 fact"""
import os, sys, json, time, datetime, pickle, hashlib, itertools, numpy as np
from multiprocessing import Pool
import config
from experiments.review_r1 import code_key
from experiments.run import git_hash, RES
from experiments.revision_r6 import _ijob, CHUNK, OUT

LAMB_D = [3.0, 3.25]
LAMB_M = {'0.65': 0.65, '1.56': 1.56}
FACT = dict(focus_m={'0.5': 0.5, '1.0': 1.0, '2.0': 2.0}, f_mm={'4': 4.0, '6': 6.0, '8': 8.0},
            f_number={'2.0': 2.0, '2.8': 2.8}, brightness={'1/128': 1 / 128, '1/256': 1 / 256})
FACT_D = {'d3.0': 3.0, 'd3.25': 3.25}

def fact_cells():
    ks = list(FACT); return [dict(zip(ks, c)) for c in itertools.product(*[list(FACT[k]) for k in ks])]

def cell_key(c): return ','.join(f'{k}={c[k]}' for k in FACT)

def jobs_for(group):
    J = []
    if group == 'lamb30':
        for ln, m in LAMB_M.items():
            for d in LAMB_D:
                cn = f'd{d}'; c = dict(distance_m=d, t_exp=1 / 1500, yaw_deg=30.0); k = f'lambert_m={ln}|{cn}|1/1500|1/128'
                pm = dict(brightness=1 / 128, lambert_m=m)
                J.append((k + '|eval', c, pm, 33.011, config.cond_seed(f'y30-{cn}', 0, config.SEED), 1000, None, 'std'))
                J.append((k + '|tune', c, pm, 33.011, config.cond_seed(f'y30-{cn}', 0, config.TUNE_SEED), 200, None, 'std'))
    elif group == 'fact':
        for cell in fact_cells():
            pm = {k: FACT[k][v] for k, v in cell.items()}
            for cn, d in FACT_D.items():
                c = dict(distance_m=d, t_exp=1 / 1500); k = f'{cell_key(cell)}|{cn}|1/1500|1/128'
                J.append((k + '|eval', c, pm, 33.011, config.cond_seed(cn, 0, config.SEED), 1000, None, 'std'))
                J.append((k + '|tune', c, pm, 33.011, config.cond_seed(cn, 0, config.TUNE_SEED), 200, None, 'std'))
    return J

def run(group, procs):
    t = time.time(); J = jobs_for(group); work = []
    for key, cond, pm, pref, seed, N, only, mode in J:
        for c0 in range(0, N, CHUNK): work.append((key, cond, pm, pref, seed, c0, min(CHUNK, N - c0), only, mode))
    ck = os.path.join(os.environ.get('CKPT', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.ckpt')), 'r7_' + group); os.makedirs(ck, exist_ok=True)
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
    os.makedirs(OUT, exist_ok=True); np.savez_compressed(os.path.join(OUT, f'r7_{group}.npz'), **arr)
    meta = dict(group=group, git=git_hash(), code_key=gh, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t), procs=procs,
                jobs=[dict(key=j[0], cond=j[1], pmod=j[2], pref=j[3], seed=j[4], symbols=j[5], mode=j[7]) for j in J])
    json.dump(meta, open(os.path.join(RES, f'run_meta_R7_{group}.json'), 'w'), indent=0)
    print(group, 'done', meta['elapsed_s'], 's', flush=True)

if __name__ == '__main__':
    procs = int(os.environ.get('PROCS', '7'))
    for g in sys.argv[1:]: run(g, procs)
