"""Equal-budget tuning (6 configs each) of HNCSM v2-CS, QCD-style-inspired and Overlay-inspired on HELD-OUT seeds
(config.TUNE_SEED), equal-average-power channel. Objective: mean net goodput over a distance grid.
Writes results/tuned_params.json and results/tune_results.csv."""
import json, os, sys, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from tx.schemes import HNCSMv2CS, QCDStyle, Nishimoto, all_schemes
from experiments.common import power_scales, mean_power, eval_point, rows_from

DIST = [1.5, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0]; FRAMES = 200
CANDS = {
    'v2cs': [dict(delta=d, bpl=b) for d in (0.1, 0.2, 0.3) for b in (1, 2)],
    'qcd': [dict(subset=x) for x in ('first16', 'last16', 'maxdist-0', 'maxdist-1', 'maxdist-2', 'maxdist-3')],
    'overlay': [dict(a1=0.5 - a2, a2=a2) for a2 in (0.1, 0.15, 0.2, 0.25)] + [dict(a1=0.25, a2=0.15), dict(a1=0.35, a2=0.1)],
}
MK = {'v2cs': lambda p: HNCSMv2CS(**p), 'qcd': lambda p: QCDStyle(**p), 'overlay': lambda p: Nishimoto(**p)}

def job(a):
    fam, i, d, pref = a; s = MK[fam](CANDS[fam][i]); sc = {s.name: pref / mean_power(s)}
    res = eval_point([s], sc, dict(distance_m=d), FRAMES, config.cond_seed(f'tune-{d}', 0, config.TUNE_SEED))
    r = [x for x in rows_from(res, [s], FRAMES, pref, {}) if x['layer'] == 'TOTAL'][0]
    return dict(family=fam, cand=i, params=json.dumps(CANDS[fam][i]), distance_m=d, goodput=r['goodput_bps'])

if __name__ == '__main__':
    allc = [MK[f](p) for f in CANDS for p in CANDS[f]]
    pref = min(mean_power(s) for s in allc + all_schemes())
    jobs = [(f, i, d, pref) for f in CANDS for i in range(len(CANDS[f])) for d in DIST]
    with Pool(os.cpu_count()) as p: df = pd.DataFrame(p.map(job, jobs))
    df.to_csv('results/tune_results.csv', index=False)
    m = df.groupby(['family', 'cand', 'params']).goodput.mean().reset_index()
    print(m.to_string())
    best = {f: json.loads(m[m.family == f].sort_values('goodput').iloc[-1].params) for f in CANDS}
    best['pref_power'] = pref; best['tune_seed'] = config.TUNE_SEED; best['frames_per_point'] = FRAMES; best['distances'] = DIST
    json.dump(best, open('results/tuned_params.json', 'w'), indent=1); print(best)
