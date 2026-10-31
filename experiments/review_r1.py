"""IEEE-review round-1 experiments (hncsm_paper/review/review_vtc.md). Per-symbol npz in results/phys_sym/review_*.npz.
Groups:
  e1sweep : 'HNCSM v2-base-only' alone on the run_phys distance grid 0.5..5 m at P25/P33/P42, run_phys seeds
            (cond_seed('distance_m', i, SEED)), 1000 symbols -> CRN-paired with results/phys_sym/sweeps_PHYS_P*.npz.
            Also re-runs 'HNCSM v2' at P33 3.0 m (index 10) as a byte-identity check of default behaviour.
  e2_P<b> : C2 robustness grid, distance {3.0,3.25,3.5} x t_exp {1/4000,1/1500,1/500,1/250} x brightness {1/64,1/128,1/256},
            eval 1000 (cond_seed('d<d>',0,SEED)) + tune 200 (TUNE_SEED); full line-up + v2-base-only. Seeds for d3.0 are
            those of audit_r1 'claims', so P33 d3.0 at 1/128 and 1/256 must reproduce claims.npz exactly.
  e3valid : IMX219 preset, QCD-OCC paper frame (2 m, 27 lux, 25 fps, unscaled), brightness grid, validate_qcd seeds.
  e3claims: IMX219, P33, C1/C2 geometry at the same metres (2.5,3.0,3.25,3.5) and at matched px/LED (x f_px ratio),
            t_exp grid, eval 1000 + tune 200.
  e3bracket: IMX219 brightness 1/64 and 1/256 at 1/1500 (eval only) for d2.5 and the matched-px/LED points.
  e3sweep : IMX219, P33, distance 1.0..4.0 step 0.25 plus 5..10 m, eval 1000 + tune 200 (genie chosen on tune)."""
import os, sys, json, time, datetime, numpy as np
from multiprocessing import Pool
import config
from tx.ablation import HNCSMv2BaseOnly
from experiments.audit_r1 import lineup, BASE, T_EXPS
from experiments.common import power_scales
from experiments.phys_eval import eval_point_phys
from experiments.run import git_hash, RES
from channel import physical as ph
from channel import presets_phys as pp

OUT = os.path.join(RES, 'phys_sym'); CHUNK = 50
DIST = list(np.round(np.arange(0.5, 5.01, 0.25), 2))
PREFS = {'25': 25.0, '33': 33.011, '42': 42.0}
BRS = {'1/64': 1 / 64, '1/128': 1 / 128, '1/256': 1 / 256}
E2_D = {'d3.0': 3.0, 'd3.25': 3.25, 'd3.5': 3.5}
FPX_RATIO = (3.04 / 1.12e-3) / (6.0 / 5.86e-3)
E3_LINE = ['HNCSM v2', 'HNCSM v2-base-only', 'QCD-style-inspired (Vasantha22)', 'CSK802-4', 'CSK802-8', 'OOK-8x8', 'HNCSM']
E3_BR = None   # filled from results/review_r1/e3_calibration.json

def lineup_r1(): return lineup() + [HNCSMv2BaseOnly()]

def preset(name):
    if name == 'imx174': return dict(ph.P)
    b = json.load(open(os.path.join(RES, 'review_r1', 'e3_calibration.json')))['brightness'] if name == 'imx219' else None
    return pp.imx219(b)

def job(a):
    key, cond, pset, pmod, pref, seed, c0, n, only = a
    sch = lineup_r1()
    sc = {s.name: 1.0 for s in sch} if pref is None else power_scales(sch, pref, 'equal', False)[0]
    if only: sch = [s for s in sch if s.name in only]
    p = preset(pset); p.update(pmod); c = dict(BASE); c.update(cond); rec = {}
    eval_point_phys(sch, sc, c, n, seed, p, f0=c0, rec=rec)
    return key, c0, rec

def jobs_for(group):
    J = []
    if group == 'e1sweep':
        for b, pref in PREFS.items():
            for i, d in enumerate(DIST):
                J.append((f'P{b}|distance_m|{i}|eval', dict(distance_m=float(d)), 'imx174', {}, pref,
                          config.cond_seed('distance_m', i, config.SEED), 1000, ['HNCSM v2-base-only']))
        J.append(('P33|distance_m|10|eval|check', dict(distance_m=3.0), 'imx174', {}, 33.011,
                  config.cond_seed('distance_m', 10, config.SEED), 1000, ['HNCSM v2']))
    elif group.startswith('e2_P'):
        b = group[4:]; pref = PREFS[b]
        for bn, br in BRS.items():
            for cn, d in E2_D.items():
                for tn, t in T_EXPS.items():
                    k = f'{cn}|{tn}|{bn}'; c = dict(distance_m=d, t_exp=t)
                    J.append((k + '|eval', c, 'imx174', dict(brightness=br), pref, config.cond_seed(cn, 0, config.SEED), 1000, None))
                    J.append((k + '|tune', c, 'imx174', dict(brightness=br), pref, config.cond_seed(cn, 0, config.TUNE_SEED), 200, None))
    elif group == 'e3valid':
        for m in (1 / 16, 1 / 8, 1 / 4, 1 / 2, 1, 2, 4, 8, 16, 32):
            br = m / 128
            J.append((f'{br}|eval', dict(distance_m=2.0, lux=27), 'imx219raw', dict(brightness=br, f_tx=25.0), None,
                      config.cond_seed(f'val-2.0-27-25-{1/128}', 0, config.SEED), 400, ['QCD-OCC (paper frame)']))
    elif group == 'e3claims':
        conds = {f'd{d}': d for d in (2.5, 3.0, 3.25, 3.5)}
        conds.update({f'm{d}': round(d * FPX_RATIO, 3) for d in (2.5, 3.0, 3.25, 3.5)})
        for cn, d in conds.items():
            for tn, t in T_EXPS.items():
                c = dict(distance_m=d, t_exp=t); k = f'{cn}|{tn}'
                J.append((k + '|eval', c, 'imx219', {}, 33.011, config.cond_seed('imx-' + cn, 0, config.SEED), 1000, None))
                J.append((k + '|tune', c, 'imx219', {}, 33.011, config.cond_seed('imx-' + cn, 0, config.TUNE_SEED), 200, None))
    elif group == 'e3bracket':
        conds = {'d2.5': 2.5}; conds.update({f'm{d}': round(d * FPX_RATIO, 3) for d in (2.5, 3.0, 3.25, 3.5)})
        for bn, br in (('1/64', 1 / 64), ('1/256', 1 / 256)):
            for cn, d in conds.items():
                J.append((f'{cn}|1/1500|{bn}|eval', dict(distance_m=d, t_exp=1 / 1500), 'imx219', dict(brightness=br), 33.011,
                          config.cond_seed('imx-' + cn, 0, config.SEED), 1000, None))
    elif group == 'e3sweep':
        ds = list(np.round(np.arange(1.0, 4.01, 0.25), 2)) + [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        for i, d in enumerate(ds):
            c = dict(distance_m=float(d)); k = f'{float(d)}'
            J.append((k + '|eval', c, 'imx219', {}, 33.011, config.cond_seed('imx-dist', i, config.SEED), 1000, E3_LINE))
            J.append((k + '|tune', c, 'imx219', {}, 33.011, config.cond_seed('imx-dist', i, config.TUNE_SEED), 200, E3_LINE))
    return J

def run(group, procs):
    t = time.time(); J = jobs_for(group); work = []
    for key, cond, ps, pm, pref, seed, N, only in J:
        for c0 in range(0, N, CHUNK): work.append((key, cond, ps, pm, pref, seed, c0, min(CHUNK, N - c0), only))
    with Pool(procs) as pl: out = pl.map(job, work, chunksize=1)
    out.sort(key=lambda x: (x[0], x[1])); arr = {}
    for key, c0, rec in out:
        for s, d in rec.items():
            for f, v in d.items(): arr.setdefault(f'{key}|{s}|{f}', []).append(v)
    arr = {k: np.concatenate(v) for k, v in arr.items()}
    os.makedirs(OUT, exist_ok=True); np.savez_compressed(os.path.join(OUT, f'review_{group}.npz'), **arr)
    meta = dict(group=group, git=git_hash(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t),
                procs=procs, jobs=[dict(key=j[0], cond=j[1], preset=j[2], pmod=j[3], pref=j[4], seed=j[5], symbols=j[6], only=j[7]) for j in J])
    json.dump(meta, open(os.path.join(RES, f'run_meta_REVIEW_{group}.json'), 'w'), indent=0)
    print(group, 'done', meta['elapsed_s'], 's', flush=True)

if __name__ == '__main__':
    procs = int(os.environ.get('PROCS', '6'))
    for g in sys.argv[1:]: run(g, procs)
