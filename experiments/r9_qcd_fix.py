"""benchmark-r9 (reviewer must-fix 2): QCD-OCC error floor root cause + opt-in corrected receiver, CRN-paired.
Both receivers decode the SAME captured frames (same seeds, same rng stream; decode does not consume random numbers):
  old = QCDOCC (4x4 canonical sampling window, r6/r7/r8 default, unchanged)
  new = QCDOCCWin6 (6x6 window; opt-in)
Grids: (a) r6 'valid6' (2 m, lux {27,149,304} x VAL_BR, 2000 symbols, seeds val6-2.0-<lux>-<br>);
       (b) r7 plateau 'base' (27 lux, 11 brightnesses, 1000 symbols, seeds r7plat-base-<br>).
Identity check: old-receiver error arrays must equal the shipped r6_valid6.npz / r7 plateau cache.
(c) noise-free mechanism probe (no shot/read noise, no FPN, no clipping, 16-bit ADC; t_row 0; genie corners).
Usage: OMP_NUM_THREADS=1 PROCS=8 python -m experiments.r9_qcd_fix  -> results/benchmark/r9/*.csv"""
import os, json, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from channel import physical as ph
from tx.schemes import QCDOCC, QCDOCCWin6
from experiments.phys_eval import eval_point_phys
from experiments.revision_r6 import BASE, VAL_BR
from experiments.r7_qcd_plateau import BR
from experiments.stats import cluster_ber, paired_diff
from experiments.bench_report import OUT as BOUT
import rx.sampler as S

OUT = os.path.join(BOUT, 'r9'); ZF = os.path.join(BOUT, '..', 'phys_sym', 'r9_qcdfix.npz')
OLD, NEW = QCDOCC(), QCDOCCWin6()

def run(a):
    key, lux, br, seed, n = a
    p = dict(ph.P); p.update(brightness=br, f_tx=25.0); c = dict(BASE); c.update(distance_m=2.0, lux=lux); rec = {}
    eval_point_phys([OLD, NEW], {OLD.name: 1.0, NEW.name: 1.0}, c, n, seed, p, rec=rec)
    return key, rec[OLD.name]['err'], rec[NEW.name]['err']

def jobs():
    J = [(f'valid6|{lux}|{bn}', lux, br, config.cond_seed(f'val6-2.0-{lux}-{bn}', 0, config.SEED), 2000)
         for lux in (27, 149, 304) for bn, br in VAL_BR.items()]
    J += [(f'plat|27|{bn}', 27, br, config.cond_seed(f'r7plat-base-{bn}', 0, config.SEED), 1000) for bn, br in BR.items()]
    return J

class _NF(np.random.RandomState):
    def poisson(self, mu): return mu
    def normal(self, a, b, size=None): return np.zeros(size)

def noise_free(win, br, nf=300):
    p = dict(ph.P); p.update(brightness=br, f_tx=25.0, t_row=0.0, read_e=0.0, dsnu_e=0.0, prnu=0.0, sat_e=1e12, bits=16, K12=0.501 / 16)
    s = QCDOCC(); rng = np.random.RandomState(9); E = []
    for f in range(nf):
        bits = rng.randint(0, 2, 144); d = s.encode(list(bits))
        es, ct, _ = ph.render_mean_e([d, d, d], 2.0, 0, 0, 27.0, rng, p, None, 0.02)
        for mos in (True, False):
            img = ph.capture(es[0], _NF(0), p) if mos else es[0] * ph.sensor_K(p) / 2 ** 8
            E.append((mos, np.array(s.decode(*S.rectify_and_sample(img, ct, win=win))) != bits))
    rows = []
    for mos in (True, False):
        e = np.array([x for m, x in E if m == mos]); t = max(e.sum(), 1)
        rows.append(dict(win=win, brightness=br, bayer_demosaic=mos, symbols=nf, ber=e.mean(), share_R_bit=e[:, 0::3].sum() / t))
    return rows

def main():
    os.makedirs(OUT, exist_ok=True)
    zz = dict(np.load(ZF)) if os.path.exists(ZF) else {}
    todo = [j for j in jobs() if f'{j[0]}|old' not in zz]
    with Pool(int(os.environ.get('PROCS', '1'))) as pl:
        for k, eo, en in pl.imap_unordered(run, todo):
            zz[f'{k}|old'] = eo; zz[f'{k}|new'] = en; np.savez_compressed(ZF, **zz); print('done', k, flush=True)
    ref6 = np.load(os.path.join(BOUT, '..', 'phys_sym', 'r6_valid6.npz'))
    fp = os.path.join(BOUT, 'r7', '.qcd_plateau_err.npz'); ref7 = np.load(fp) if os.path.exists(fp) else None
    rows = []
    for k, lux, br, seed, n in jobs():
        g, _, bn = k.split('|'); eo, en = zz[f'{k}|old'], zz[f'{k}|new']
        if g == 'valid6': ident = bool(np.array_equal(eo, ref6[f'{lux}|{bn}|eval|{OLD.name}|err']))
        else: ident = bool(np.array_equal(eo, ref7[f'base|{bn}'])) if ref7 is not None else None
        bo, bol, boh = cluster_ber(eo, B=10000, seed=0); bnw, bnl, bnh = cluster_ber(en, B=10000, seed=0)
        d, dl, dh = paired_diff(en.mean(1), eo.mean(1), B=10000, seed=0)
        tn = max(en.sum(), 1)
        rows.append(dict(grid=g, lux=lux, brightness=bn, symbols=len(eo), old_identical_to_shipped=ident,
                         ber_old=bo, ber_old_lo=bol, ber_old_hi=boh, ber_new=bnw, ber_new_lo=bnl, ber_new_hi=bnh,
                         diff_new_minus_old=d, diff_lo=dl, diff_hi=dh, sig=bool(dh < 0 or dl > 0),
                         share_R_old=eo[:, 0::3].sum() / max(eo.sum(), 1), share_R_new=en[:, 0::3].sum() / tn,
                         new_ci_contains_published_0p0113=bool(bnl <= 0.0113 <= bnh) if g == 'valid6' else None))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'qcd_win6_crn.csv'), index=False, float_format='%.6g'); print(df.to_string())
    with Pool(int(os.environ.get('PROCS', '1'))) as pl:
        nf = sum(pl.starmap(noise_free, [(w, b) for w in (2, 4, 6, 8) for b in (1 / 128, 1 / 512, 1 / 2048)]), [])
    pd.DataFrame(nf).to_csv(os.path.join(OUT, 'qcd_floor_noisefree.csv'), index=False, float_format='%.6g'); print(pd.DataFrame(nf).to_string())

if __name__ == '__main__': main()
