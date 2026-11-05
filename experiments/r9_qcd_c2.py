"""benchmark-r9: does the opt-in QCD-OCC-win6 receiver change C2 / rankings? CRN-paired rerun at the C2 cell
(IMX174, P33 = pref 33.011, 1/1500, brightness 1/128, default optics, claims/E2 eval seeds cond_seed('d<d>'), 1000 symbols)
for QCDOCC (identity control vs review_e2_P33.npz) and QCDOCCWin6 (same power scale: identical drive).
v2 and all other schemes are taken unchanged from review_e2_P33.npz (their receiver is unchanged).
Binding = min over the shipped comparison set with QCD-OCC replaced by / added as QCD-OCC-win6 (native and 48-bit CRC).
Usage: OMP_NUM_THREADS=1 PROCS=8 python -m experiments.r9_qcd_c2 -> results/benchmark/r9/qcd_win6_c2.csv"""
import os, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from channel import physical as ph
from tx.schemes import QCDOCC, QCDOCCWin6
from experiments.phys_eval import eval_point_phys
from experiments.common import power_scales
from experiments.review_r1 import lineup_r1
from experiments.r6_report import pairs, binding_p, verdict, boot, Gr
from experiments.bench_report import V2, BO, SCH, VARS, ld, OUT as BOUT
from experiments.stats import sym_goodput

OUT = os.path.join(BOUT, 'r9'); ZF = os.path.join(BOUT, '..', 'phys_sym', 'r9_qcdc2.npz')
D = {'d3.0': 3.0, 'd3.25': 3.25, 'd3.5': 3.5}; CH = 100

def run(a):
    cn, c0 = a; s0, s1 = QCDOCC(), QCDOCCWin6()
    sc = power_scales(lineup_r1(), 33.011, 'equal', False)[0]; sc = {s0.name: sc[s0.name], s1.name: sc[s0.name]}
    c = dict(distance_m=D[cn], t_exp=1 / 1500); p = dict(ph.P); p.update(brightness=1 / 128); rec = {}
    from experiments.revision_r6 import BASE
    cc = dict(BASE); cc.update(c)
    eval_point_phys([s0, s1], sc, cc, CH, config.cond_seed(cn, 0, config.SEED), p, f0=c0, rec=rec)
    return cn, c0, rec[s0.name]['err'], rec[s1.name]['err']

def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(ZF):
        with Pool(int(os.environ.get('PROCS', '1'))) as pl: out = pl.map(run, [(cn, c0) for cn in D for c0 in range(0, 1000, CH)], chunksize=1)
        zz = {}
        for cn in D:
            o = sorted([x for x in out if x[0] == cn], key=lambda x: x[1])
            zz[f'{cn}|old'] = np.concatenate([x[2] for x in o]); zz[f'{cn}|new'] = np.concatenate([x[3] for x in o])
        np.savez_compressed(ZF, **zz)
    zz = np.load(ZF); ze = ld('review_e2_P33.npz'); L = QCDOCC().layers; q = QCDOCC.name; rows = []
    names = [n for n in SCH if n not in VARS]
    for cn in D:
        k = f'{cn}|1/1500|1/128|eval'; ident = bool(np.array_equal(zz[f'{cn}|old'], ze[f'{k}|{q}|err']))
        P0 = pairs(ze, lambda t, s: f'{cn}|{t}|1/128|{s}'); b0 = binding_p(P0)
        v = Gr(ze, k, V2); gn = {blk: sym_goodput(zz[f'{cn}|new'], L, 15.0, blk) for blk in (None, 48)}
        P1 = [x for x in P0 if x[0] != q] + [(QCDOCCWin6.name, 'native' if blk is None else '48-bit', v - gn[blk]) for blk in (None, 48)]
        P2 = P0 + [(QCDOCCWin6.name, 'native' if blk is None else '48-bit', v - gn[blk]) for blk in (None, 48)]
        b1, b2 = binding_p(P1), binding_p(P2)
        g = {n: Gr(ze, k, n).mean() for n in names if n != BO}; g[QCDOCCWin6.name] = gn[None].mean()
        rk = sorted(g, key=lambda n: -g[n])
        mo, mlo, mhi, _ = boot(v - Gr(ze, k, q)); mn, nlo, nhi, _ = boot(v - gn[None]); dd = boot(gn[None] - Gr(ze, k, q))
        rows.append(dict(distance=cn, old_identical_to_e2=ident, qcdocc_old_bps=Gr(ze, k, q).mean(), qcdocc_win6_bps=gn[None].mean(),
                         win6_minus_old=dd[0], wd_lo=dd[1], wd_hi=dd[2], v2_bps=v.mean(), v2_minus_win6=mn, vw_lo=nlo, vw_hi=nhi,
                         binding_shipped=f"{b0['baseline']} {b0['crc']} {b0['margin']:.1f} [{b0['lo']:.1f}, {b0['hi']:.1f}] {verdict(b0['lo'], b0['hi'])}",
                         binding_replaced=f"{b1['baseline']} {b1['crc']} {b1['margin']:.1f} [{b1['lo']:.1f}, {b1['hi']:.1f}] {verdict(b1['lo'], b1['hi'])}",
                         binding_added=f"{b2['baseline']} {b2['crc']} {b2['margin']:.1f} [{b2['lo']:.1f}, {b2['hi']:.1f}] {verdict(b2['lo'], b2['hi'])}",
                         v2_rank_native=1 + rk.index(V2), ranking_native=' > '.join(f'{n.split(" (")[0]}{" win6" if "win6" in n else ""} {g[n]:.0f}' for n in rk)))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'qcd_win6_c2.csv'), index=False, float_format='%.6g'); print(df.T.to_string())

if __name__ == '__main__': main()
