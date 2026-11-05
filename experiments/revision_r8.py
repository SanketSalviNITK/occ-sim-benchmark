"""benchmark-r8 revision experiments (additive; no default changed; physics modules unchanged except the OPTIONAL
sigma_mult term in channel.physical.capture, default 0 = byte-identical).
Re-uses the job runner of experiments.revision_r6 (same chunking / checkpoint / CRN scheme); outputs
results/phys_sym/r8_<group>.npz and results/run_meta_R8_<group>.json.
Groups:
  mult    : signal-proportional noise sigma_mult in {0 (control), 0.024, 0.05, 0.15} x correlation {pixel, frame} at the
            C2 cell (IMX174, P33, 1/1500, brightness 1/128, default optics), d in {3.0, 3.25, 3.5}, canonical claims/E2
            seeds cond_seed('d<d>') (eval 1000 + tune 200) -> CRN-paired with review_e2_P33.npz and across sigma levels
            (the added z is drawn from a side stream that does not advance the capture rng). The sigma = 0 control
            must be byte-identical to review_e2_P33.npz (checked by experiments.r8_report).
  multfin : dual receiver (detected vs oracle corners, finder failure / gross-error counts) on the eval seeds of
            'mult' for sigma > 0; the sigma = 0 reference is r6_finder.npz (same seeds).
Usage: OMP_NUM_THREADS=1 PROCS=7 python -m experiments.revision_r8 mult multfin"""
import os, sys, json, time, datetime, pickle, hashlib, numpy as np
from multiprocessing import Pool
import config
from experiments.review_r1 import code_key
from experiments.run import git_hash, RES
from experiments.revision_r6 import _ijob, CHUNK, OUT

MULT_D = {'d3.0': 3.0, 'd3.25': 3.25, 'd3.5': 3.5}
MULT_S = {'0.024': 0.024, '0.05': 0.05, '0.15': 0.15}
MULT_C = ('pixel', 'frame')

def mkey(s, c): return f'sigma_mult={s},corr={c}'

def jobs_for(group):
    J = []
    cells = [('0', 'pixel', 0.0)] + [(sn, c, s) for sn, s in MULT_S.items() for c in MULT_C]
    for sn, corr, s in cells:
        if group == 'multfin' and s == 0.0: continue
        for cn, d in MULT_D.items():
            c = dict(distance_m=d, t_exp=1 / 1500); k = f'{mkey(sn, corr)}|{cn}|1/1500|1/128'
            pm = dict(brightness=1 / 128, sigma_mult=s, sigma_mult_corr=corr)
            if group == 'mult':
                J.append((k + '|eval', c, pm, 33.011, config.cond_seed(cn, 0, config.SEED), 1000, None, 'std'))
                J.append((k + '|tune', c, pm, 33.011, config.cond_seed(cn, 0, config.TUNE_SEED), 200, None, 'std'))
            elif group == 'multfin':
                J.append((k + '|eval', c, pm, 33.011, config.cond_seed(cn, 0, config.SEED), 1000, None, 'dual'))
    return J

def run(group, procs):
    t = time.time(); J = jobs_for(group); work = []
    for key, cond, pm, pref, seed, N, only, mode in J:
        for c0 in range(0, N, CHUNK): work.append((key, cond, pm, pref, seed, c0, min(CHUNK, N - c0), only, mode))
    ck = os.path.join(os.environ.get('CKPT', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.ckpt')), 'r8_' + group); os.makedirs(ck, exist_ok=True)
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
    os.makedirs(OUT, exist_ok=True); np.savez_compressed(os.path.join(OUT, f'r8_{group}.npz'), **arr)
    meta = dict(group=group, git=git_hash(), code_key=gh, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t), procs=procs,
                jobs=[dict(key=j[0], cond=j[1], pmod=j[2], pref=j[3], seed=j[4], symbols=j[5], mode=j[7]) for j in J])
    json.dump(meta, open(os.path.join(RES, f'run_meta_R8_{group}.json'), 'w'), indent=0)
    print(group, 'done', meta['elapsed_s'], 's', flush=True)

if __name__ == '__main__':
    procs = int(os.environ.get('PROCS', '7'))
    for g in sys.argv[1:]: run(g, procs)
