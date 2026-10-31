"""Research-Validator round-1 runs on the PHYSICAL channel, saving PER-SYMBOL bit-error matrices (+ saturation fraction
and RS mixing weight of the selected frame) so that BER uses a symbol-cluster bootstrap and every A>B comparison a
paired CRN bootstrap (experiments/stats.py). Groups:
  claims   : B1/B4  2.5 m, 3.0 m, yaw 70 deg (1 m), blur 4 px (1 m) x t_exp {1/4000,1/1500,1/500,1/250} x brightness
             {1/128, 1/256}; P33; eval 1000 symbols (SEED) + held-out tuning/genie set 200 symbols (TUNE_SEED)
  lowlight : B2  brightness {1/256..1/2048} x ADC {8,10,12} bit x distance 0.5..3.0 m; P15 with cap; 250 + 100 symbols
  trow     : NB3 t_row {0, 10 us, 27 us} at 2.0/2.5 m, P33, 1000 symbols
  radiant  : NB1 radiant-equal power budget, distance 0.5..3.5 m, 500 symbols
  valid    : B3  QCD-OCC paper frame, 2 m / 27 lux / 25 fps, brightness {1/64,1/128,1/256} (validate_qcd.py seeds)
Writes results/phys_sym/<group>.npz and results/run_meta_AUDIT_<group>.json.
Usage: python -m experiments.audit_r1 claims lowlight trow radiant valid"""
import os, sys, json, time, datetime, numpy as np
from multiprocessing import Pool
import config
from tx.schemes import all_schemes_phys, QCDOCC
from experiments.common import power_scales, mean_power
from experiments.phys_eval import eval_point_phys
from experiments.run import git_hash, RES
from channel import physical as ph

OUT = os.path.join(RES, 'phys_sym'); CHUNK = 50
BASE = dict(distance_m=1.0, yaw_deg=0.0, blur_sigma_px=0.0, lux=27.0, jitter=0.02)
CLAIM_CONDS = {'d2.5': dict(distance_m=2.5), 'd3.0': dict(distance_m=3.0), 'yaw70': dict(yaw_deg=70.0), 'blur4': dict(blur_sigma_px=4.0)}
T_EXPS = {'1/4000': 1 / 4000, '1/1500': 1 / 1500, '1/500': 1 / 500, '1/250': 1 / 250}
LL_BR = {'1/256': 1 / 256, '1/512': 1 / 512, '1/1024': 1 / 1024, '1/2048': 1 / 2048}
LL_DIST = list(np.round(np.arange(0.5, 3.01, 0.25), 2))

def lineup(): return all_schemes_phys() + [QCDOCC()]

def radiant_w(p=ph.P):
    Ie = ph.photon_rate_per_sr(p) * ph.H_PLANCK * ph.C_LIGHT / (np.array(p['lam_nm']) * 1e-9)   # W/sr per channel
    return Ie / Ie.mean()

def scales_for(sch, pref, mode, cap):
    if mode == 'radiant':
        w = radiant_w(); rng = np.random.RandomState(0)
        P = {s.name: float(np.mean([(s.encode(list(rng.randint(0, 2, s.nbits))) * w).sum() for _ in range(2000)])) for s in sch}
        return {k: pref / v for k, v in P.items()}
    return power_scales(sch, pref, 'equal', cap)[0]

def job(a):
    key, cond, pmod, pref, mode, cap, seed, c0, n, only = a
    sch = lineup(); sc = scales_for(sch, pref, mode, cap)
    if only: sch = [s for s in sch if s.name in only]
    p = dict(ph.P); p.update(pmod); c = dict(BASE); c.update(cond); rec = {}
    eval_point_phys(sch, sc, c, n, seed, p, f0=c0, rec=rec)
    return key, c0, rec

def jobs_for(group):
    J = []   # (key, cond, pmod, pref, mode, cap, seed, n_total, only)
    if group == 'claims':
        for bn, br in {'1/128': 1 / 128, '1/256': 1 / 256}.items():
            for cn, c in CLAIM_CONDS.items():
                for tn, t in T_EXPS.items():
                    cc = dict(c, t_exp=t); k = f'{cn}|{tn}|{bn}'
                    J.append((k + '|eval', cc, dict(brightness=br), 33.011, 'equal', False, config.cond_seed(k, 0, config.SEED), 1000, None))
                    J.append((k + '|tune', cc, dict(brightness=br), 33.011, 'equal', False, config.cond_seed(k, 0, config.TUNE_SEED), 200, None))
    elif group == 'lowlight':
        for bn, br in LL_BR.items():
            for bits in (8, 10, 12):
                for d in LL_DIST:
                    k = f'{bn}|{bits}|{d}'; pm = dict(brightness=br, bits=bits)
                    J.append((k + '|eval', dict(distance_m=d), pm, 15.0, 'equal', True, config.cond_seed(k, 0, config.SEED), 250, None))
                    J.append((k + '|tune', dict(distance_m=d), pm, 15.0, 'equal', True, config.cond_seed(k, 0, config.TUNE_SEED), 100, None))
    elif group == 'trow':
        for tr in (0.0, 10e-6, 27e-6):
            for d in (2.0, 2.5):
                k = f'{tr}|{d}'; J.append((k + '|eval', dict(distance_m=d), dict(t_row=tr), 33.011, 'equal', False, config.cond_seed(k, 0, config.SEED), 1000, None))
    elif group == 'radiant':
        for d in np.round(np.arange(0.5, 3.51, 0.5), 2):
            k = f'{d}'; J.append((k + '|eval', dict(distance_m=float(d)), {}, 33.011, 'radiant', False, config.cond_seed(k, 0, config.SEED), 500, None))
    elif group == 'valid':
        q = QCDOCC().name
        for br in (1 / 64, 1 / 128, 1 / 256):
            # identical seeds to validate_qcd.py (2 m, 27 lux, 25 fps); QCD frame at scale 1 (unscaled), not power-equalised
            J.append((f'{br}|eval', dict(distance_m=2.0, lux=27), dict(brightness=br, f_tx=25.0), None, 'unit', False,
                      config.cond_seed(f'val-2.0-27-25-{br}', 0, config.SEED), 400, [q]))
    return J

def job_unit(a):
    key, cond, pmod, pref, mode, cap, seed, c0, n, only = a
    s = QCDOCC(); p = dict(ph.P); p.update(pmod); c = dict(BASE); c.update(cond); rec = {}
    eval_point_phys([s], {s.name: 1.0}, c, n, seed, p, f0=c0, rec=rec)
    return key, c0, rec

def run(group):
    t = time.time(); J = jobs_for(group); work = []
    for key, cond, pm, pref, mode, cap, seed, N, only in J:
        for c0 in range(0, N, CHUNK): work.append((key, cond, pm, pref, mode, cap, seed, c0, min(CHUNK, N - c0), only))
    fn = job_unit if group == 'valid' else job
    with Pool(os.cpu_count()) as pl: out = pl.map(fn, work, chunksize=1)
    out.sort(key=lambda x: (x[0], x[1])); arr = {}
    for key, c0, rec in out:
        for s, d in rec.items():
            for f, v in d.items(): arr.setdefault(f'{key}|{s}|{f}', []).append(v)
    arr = {k: np.concatenate(v) for k, v in arr.items()}
    os.makedirs(OUT, exist_ok=True); np.savez_compressed(os.path.join(OUT, f'{group}.npz'), **arr)
    meta = dict(group=group, git=git_hash(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t),
                jobs=[dict(key=j[0], cond=j[1], pmod=j[2], pref=j[3], power_mode=j[4], cap=j[5], seed=j[6], symbols=j[7]) for j in J])
    json.dump(meta, open(os.path.join(RES, f'run_meta_AUDIT_{group}.json'), 'w'), indent=0)
    print(group, 'done', meta['elapsed_s'], 's', flush=True)

if __name__ == '__main__':
    for g in sys.argv[1:]: run(g)
