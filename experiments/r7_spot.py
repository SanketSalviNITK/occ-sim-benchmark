"""benchmark-r7 provenance spot re-run (audit R6): re-simulate the first SYM symbols of selected jobs of the r6 groups whose
run metas carry '-dirty' git hashes (geoyaw30, valid6, finder) or a later commit (sens) at the current clean commit, and
compare every array with the shipped npz. Writes results/benchmark/r7/provenance_spot.csv.
Usage: OMP_NUM_THREADS=1 python -m experiments.r7_spot"""
import os, json, numpy as np, pandas as pd
from experiments.revision_r6 import job, OUT as SYM
from experiments.run import RES, git_hash
from experiments.bench_report import OUT as BOUT
N = 20
PICK = {'geoyaw30': ['d3.25|1/1500|1/128|eval', 'd3.0|1/1500|1/128|eval'], 'valid6': ['27|1/128|eval', '304|1/256|eval'],
        'finder': ['d3.25|1/1500|1/128|eval'], 'sens': ['cfa=x2|d3.0|1/1500|1/128|eval', 'lambert_m=1.56|d3.0|1/1500|1/128|eval']}

def main():
    rows = []; gh = git_hash()
    for g, keys in PICK.items():
        meta = json.load(open(os.path.join(RES, f'run_meta_R6_{g}.json'))); z = np.load(os.path.join(SYM, f'r6_{g}.npz'))
        for j in [j for j in meta['jobs'] if j['key'] in keys]:
            pm = {k: (np.array(v) if isinstance(v, list) else v) for k, v in j['pmod'].items()}
            _, _, rec = job((j['key'], j['cond'], pm, j['pref'], j['seed'], 0, N, None, j['mode']))
            for s, d in rec.items():
                for f, v in d.items():
                    ref = z[f"{j['key']}|{s}|{f}"][:N]
                    rows.append(dict(group=g, meta_git=meta['git'], rerun_git=gh, key=j['key'], scheme=s, array=f, symbols=N,
                                     identical=bool(np.array_equal(np.asarray(v), ref, equal_nan=np.asarray(v).dtype.kind == 'f'))))
    df = pd.DataFrame(rows); os.makedirs(os.path.join(BOUT, 'r7'), exist_ok=True)
    df.to_csv(os.path.join(BOUT, 'r7', 'provenance_spot.csv'), index=False)
    print(df.groupby('group').identical.agg(['sum', 'size']).to_string()); return df

if __name__ == '__main__': main()
