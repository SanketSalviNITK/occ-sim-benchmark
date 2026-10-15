"""Investigate the HNCSM v2-CS goodput dip near 1.75 m: fine distance scan, Bayer on/off, sampling window."""
import sys, os, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from tx.schemes import all_schemes
from channel.sensor import SensorParams
from experiments.common import power_scales, eval_point, rows_from
import rx.sampler as smp
def job(a):
    d, bayer, win, seed = a
    smp.WIN = win
    s = [x for x in all_schemes() if x.name in ('HNCSM v2-CS', 'HNCSM v2', 'CSK-8')]
    sc, P, _ = power_scales(all_schemes(), 33.0)
    sp = SensorParams(); sp.bayer = bayer
    res = eval_point(s, {k: sc[k] for k in sc}, dict(distance_m=d, sp=sp), 400, config.cond_seed('dip', int(d * 100), seed))
    out = []
    for x in s:
        for l, n in x.layers:
            out.append(dict(d=d, bayer=bayer, win=win, scheme=x.name, layer=l, ber=res[x.name][l][0] / (n * 400), fer=res[x.name][l][1] / 400))
    return out
if __name__ == '__main__':
    D = np.round(np.arange(1.40, 2.21, 0.05), 2)
    jobs = [(d, b, w, config.SEED) for d in D for b, w in [(True, 4), (False, 4), (True, 2), (True, 6)]]
    with Pool(os.cpu_count()) as p: df = pd.DataFrame(sum(p.map(job, jobs), []))
    df.to_csv('results/dip_probe.csv', index=False)
    t = df[(df.scheme == 'HNCSM v2-CS') & (df.layer == 'enh')]
    print(t.pivot_table(index='d', columns=['bayer', 'win'], values='fer').round(3).to_string())
    print(df[(df.layer != 'enh') & df.bayer & (df.win == 4)].pivot_table(index='d', columns=['scheme', 'layer'], values='fer').round(3).to_string())
