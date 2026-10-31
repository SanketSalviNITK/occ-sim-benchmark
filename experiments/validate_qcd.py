"""Validation against QCD-OCC (Vasantha & Salvi 2022, doi:10.3390/app122010204): published BER 1.13e-2 at 200 cm and
3600 bps (144 bits/frame x 25 Tx frames/s), WS2812B 8x8, 1/1500 s, 27/149/304 lux. We run the paper's frame
(tx.schemes.QCDOCC: 48 data LEDs x 3 bits, RGB on/off, corner anchors) through the PHYSICAL channel with NO parameter
changes (brightness, optics and sensor as in channel/physical.py, i.e. the ASSUMED values are not re-tuned).
BER counts every payload bit; symbols with no usable frame are decoded as random bits (as a real receiver must).
Writes results/validation_qcd.csv."""
import os, json, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from tx.schemes import QCDOCC
from experiments.phys_eval import eval_point_phys
from experiments.common import wilson
from channel import physical as ph

N = 400; CH = 100

def job(a):
    d, lux, ftx, br, c0 = a
    p = dict(ph.P); p['f_tx'] = float(ftx); p['brightness'] = br
    s = QCDOCC()
    res, st = eval_point_phys([s], {s.name: 1.0}, dict(distance_m=d, lux=lux), CH, config.cond_seed(f'val-{d}-{lux}-{ftx}-{br}', 0, config.SEED), p, f0=c0)
    return (d, lux, ftx, br), res[s.name]['all'], st[s.name]

if __name__ == '__main__':
    jobs = []
    for br in (1 / 128, 1.0):
        for d in (0.5, 1.0, 1.5, 2.0):
            for lux in (27, 149, 304):
                for ftx in (5, 10, 15, 20, 25, 30):
                    if ftx != 25 and (lux != 27 or d != 2.0): continue        # rate sweep only at the paper's 2 m / 27 lux
                    for c0 in range(0, N, CH): jobs.append((d, lux, ftx, br, c0))
    with Pool(os.cpu_count()) as pl: out = pl.map(job, jobs, chunksize=1)
    agg = {}
    for k, (be, fe), st in out:
        A = agg.setdefault(k, [0, 0, 0, 0]); A[0] += be; A[1] += fe; A[2] += st['lost']; A[3] += st['frames_per_symbol']
    rows = []
    for (d, lux, ftx, br), (be, fe, lost, nf) in sorted(agg.items()):
        nb = 144 * N; lo, hi = wilson(be, nb)
        rows.append(dict(brightness=br, distance_cm=int(d * 100), lux=lux, tx_fps=ftx, bitrate_bps=144 * ftx, symbols=N,
                         ber=be / nb, ber_lo=lo, ber_hi=hi, ser_frame=fe / N, lost_symbols=lost, frames_per_symbol=nf / N))
    df = pd.DataFrame(rows); df.to_csv('results/validation_qcd.csv', index=False); print(df.to_string())
