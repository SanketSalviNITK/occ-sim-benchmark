"""benchmark-r7 diagnostic for the QCD-OCC validation grid BER plateau (audit S1 / R8). Analysis + small additive runs,
no physics or decoder change. Same frame / decoder / seeds style as revision_r6 'valid6' (QCDOCC unit mode, 2 m, 27 lux,
f_tx 25), 1000 symbols per cell, new seeds cond_seed('r7plat-<variant>-<br>').
For every brightness it reports: BER (cluster bootstrap CI), symbol error rate, share of bit errors on the R/G/B bit,
and the photometric operating point from the model itself: peak mean signal electrons of a lit pure-R/G/B LED channel
at the panel centre (render_mean_e, pre-noise) relative to full well sat_e, and the shot-noise SNR sqrt(e).
Variants: base (r6 valid6 settings), t_row=0 (no rolling-shutter mixing of adjacent symbols), f_tx=15 (fps/2);
mechanism probes (diagnostic only, not physical settings): cfa=I (no CFA crosstalk), no_clip (full well 1e12 e-; the 8-bit ADC still clips at 255 DN ~ 1.04 x full well),
no_clip12 (full well 1e12 e-, 12-bit ADC with gain K12/8: ADC range ~65k e-, no clipping up to 1/64).
Usage: OMP_NUM_THREADS=1 python -m experiments.r7_qcd_plateau  -> results/benchmark/r7/qcd_plateau_diag.csv"""
import os, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from channel import physical as ph
from tx.schemes import QCDOCC
from experiments.revision_r6 import job
from experiments.stats import cluster_ber
from experiments.bench_report import OUT as BOUT

OUT = os.path.join(BOUT, 'r7'); N = 1000
BR = {'1/64': 1 / 64, '1/96': 1 / 96, '1/128': 1 / 128, '1/160': 1 / 160, '1/192': 1 / 192, '1/256': 1 / 256,
      '1/384': 1 / 384, '1/512': 1 / 512, '1/1024': 1 / 1024, '1/2048': 1 / 2048, '1/4096': 1 / 4096}
VAR = {'base': {}, 't_row=0': dict(t_row=0.0), 'f_tx=15': dict(f_tx=15.0),
       'cfa=I': dict(cfa=np.eye(3)), 'no_clip': dict(sat_e=1e12), 'no_clip12': dict(sat_e=1e12, bits=12, K12=0.501 / 8)}
SUB = {'cfa=I': ['1/96', '1/128', '1/256', '1/1024'], 'no_clip': ['1/64', '1/96', '1/128', '1/256'],
       'no_clip12': ['1/64', '1/96', '1/128', '1/256']}   # mechanism probes: subset only

def peak_e(br, pm):
    """Peak mean electrons per colour channel for an all-white panel (pre-noise), r6 valid6 settings."""
    p = dict(ph.P); p.update(dict(dict(brightness=br, f_tx=25.0), **pm)); s = QCDOCC()
    d = s.encode([1] * 144)   # all data LEDs white (palette W)
    es, ct, row0 = ph.render_mean_e([d, d, d], 2.0, 0.0, 0.0, 27.0, np.random.RandomState(0), p, None, 0.0)
    return es[0].reshape(-1, 3).max(0)

def cell(a):
    v, bn = a; pm = dict(brightness=BR[bn], f_tx=25.0); pm.update(VAR[v])
    seed = config.cond_seed(f'r7plat-{v}-{bn}', 0, config.SEED)
    _, _, rec = job((None, dict(distance_m=2.0, lux=27), pm, None, seed, 0, N, None, 'unit'))
    return v, bn, rec[QCDOCC.name]['err']

def main():
    os.makedirs(OUT, exist_ok=True); W = [(v, b) for v in VAR for b in SUB.get(v, BR)]
    fz = os.path.join(OUT, '.qcd_plateau_err.npz')   # local cache of the raw error arrays (not shipped)
    zz = dict(np.load(fz)) if os.path.exists(fz) else {}
    todo = [w for w in W if f'{w[0]}|{w[1]}' not in zz]
    with Pool(int(os.environ.get('PROCS', '1'))) as pl:
        for v, b, e in pl.map(cell, todo, chunksize=1): zz[f'{v}|{b}'] = e
    np.savez_compressed(fz, **zz); res = [(v, b, zz[f'{v}|{b}']) for v, b in W]
    rows = []
    for v, bn, e in res:
        b, lo, hi = cluster_ber(e, B=2000, seed=0); tot = max(e.sum(), 1); pe = peak_e(BR[bn], {k: x for k, x in VAR[v].items() if k not in ('sat_e', 'bits', 'K12')})
        rows.append(dict(variant=v, brightness=bn, symbols=len(e), ber=b, ber_lo=lo, ber_hi=hi, sym_err=float((e.sum(1) > 0).mean()),
                         share_R_bit=e[:, 0::3].sum() / tot, share_G_bit=e[:, 1::3].sum() / tot, share_B_bit=e[:, 2::3].sum() / tot,
                         peakR_over_sat=pe[0] / ph.P['sat_e'], peakG_over_sat=pe[1] / ph.P['sat_e'], peakB_over_sat=pe[2] / ph.P['sat_e'],
                         shot_snr_G=float(np.sqrt(min(pe[1], ph.P['sat_e'])))))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'qcd_plateau_diag.csv'), index=False, float_format='%.6g'); print(df.to_string()); return df

if __name__ == '__main__': main()
