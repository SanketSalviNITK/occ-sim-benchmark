"""Tune HNCSM v2-CS shift magnitude delta and bits per lit LED on the distance sweep (100 frames/point)."""
import numpy as np, pandas as pd, os
from multiprocessing import Pool
from tx.schemes import HNCSMv2CS
from channel.render import simulate
from rx.sampler import rectify_and_sample
JOINT = bool(int(os.environ.get("JOINT", "0")))
DIST = [0.5, 1.0, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0]
def job(a):
    delta, bpl, d, seed = a; rng = np.random.RandomState(seed); sch = HNCSMv2CS(delta, bpl, joint=JOINT)
    fe = {'base': 0, 'enh': 0}; be = {'base': 0, 'enh': 0}; F = 100
    for _ in range(F):
        bits = rng.randint(0, 2, sch.nbits); img, c = simulate(sch.encode(list(bits)), distance_m=d, rng=rng)
        out = np.array(sch.decode(*rectify_and_sample(img, c)))
        for l, sl in [('base', slice(0, 48)), ('enh', slice(48, None))]:
            e = (out[sl] != bits[sl]).sum(); be[l] += e; fe[l] += e > 0
    n = {'base': 48, 'enh': 36 * bpl}
    return dict(delta=delta, bpl=bpl, distance_m=d, base_ber=be['base']/(48*F), enh_ber=be['enh']/(n['enh']*F),
                goodput=sum(n[l]*30*(1-fe[l]/F) for l in n))
if __name__ == '__main__':
    jobs = [(dl, b, d, i) for dl in (0.1, 0.2, 0.3) for b in (1, 2) for i, d in enumerate(DIST)]
    with Pool(os.cpu_count()) as p: df = pd.DataFrame(p.map(job, jobs))
    df.to_csv('results/tune_v2cs_joint%d.csv' % JOINT, index=False)
    print(df.pivot_table(index='distance_m', columns=['delta', 'bpl'], values='goodput').round(0).to_string())
    print(df.pivot_table(index='distance_m', columns=['delta', 'bpl'], values='base_ber').to_string(float_format='%.0e'))
