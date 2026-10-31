"""Analysis of the IEEE-review round-1 runs -> results/review_r1/*.csv (+ figure). Paired CRN bootstrap (stats.py)."""
import os, sys, json, numpy as np, pandas as pd
from experiments.stats import sym_goodput, boot_ci, paired_diff, cluster_ber
from experiments.review_r1 import lineup_r1, DIST, PREFS, BRS, E2_D, FPX_RATIO, E3_LINE
from experiments.audit_r1 import T_EXPS
from experiments.run_phys import GENIE_SET
from channel import physical as ph

RES = 'results'; SYM = os.path.join(RES, 'phys_sym'); OUT = os.path.join(RES, 'review_r1'); os.makedirs(OUT, exist_ok=True)
SCH = {s.name: s for s in lineup_r1()}; RATE = ph.P['f_tx']
HN = [n for n in SCH if n.startswith('HNCSM')]; BASEL = [n for n in SCH if n not in HN]
V2, BO, Q = 'HNCSM v2', 'HNCSM v2-base-only', 'QCD-style-inspired (Vasantha22)'
SHORT = {'HNCSM v2-CS': 'v2-CS', V2: 'v2', BO: 'v2-base-only', 'HNCSM': 'v1', 'HNCSM base-only': 'v1-base', 'OOK-8x8': 'OOK',
         'QR/Aztec-style': 'QR', 'NestedTexture-inspired (Salvi22)': 'Nested', Q: 'QCD-style', 'Overlay-inspired (Nishimoto12)': 'Overlay',
         'QCD-OCC (paper frame)': 'QCD-paper', 'CSK802-4': 'CSK802-4', 'CSK802-8': 'CSK802-8', 'genie': 'genie'}

def G(z, pre, n, block=None): return sym_goodput(z[f'{pre}|{n}|err'], SCH[n].layers, RATE, block)
def layer(z, pre):
    e = z[f'{pre}|{V2}|err']; return sym_goodput(e[:, :48], [('b', 48)], RATE), sym_goodput(e[:, 48:], [('e', 36)], RATE)
def ci3(x): return boot_ci(x)

def e1():
    rows, ab = [], []
    for b in PREFS:
        z = np.load(os.path.join(SYM, f'sweeps_PHYS_P{b}.npz')); zb = np.load(os.path.join(SYM, 'review_e1sweep.npz'))
        for i, d in enumerate(DIST):
            pre = f'distance_m|{i}|eval'; base, enh = layer(z, pre)
            rows.append(dict(source=f'sweep P{b}', cond=f'{d} m', budget=b, v2_total=(base + enh).mean(), base=base.mean(), base_lo=ci3(base)[1], base_hi=ci3(base)[2],
                             enh=enh.mean(), enh_lo=ci3(enh)[1], enh_hi=ci3(enh)[2], enh_share=enh.mean() / max((base + enh).mean(), 1e-9)))
            v = {V2: G(z, pre, V2), Q: G(z, pre, Q)}; v[BO] = sym_goodput(zb[f'P{b}|{pre}|{BO}|err'], SCH[BO].layers, RATE)
            for a, c in ((V2, BO), (V2, Q), (BO, Q)):
                dd = paired_diff(v[a], v[c])
                ab.append(dict(set='sweep', budget=b, distance_m=d, A=SHORT[a], B=SHORT[c], A_bps=v[a].mean(), B_bps=v[c].mean(), diff=dd[0], lo=dd[1], hi=dd[2],
                               verdict='A > B' if dd[1] > 0 else ('A < B' if dd[2] < 0 else 'n.s.')))
    zc = np.load(os.path.join(SYM, 'claims.npz'))
    for br in ('1/128', '1/256'):
        for cn in ('d2.5', 'd3.0', 'yaw70', 'blur4'):
            for t in T_EXPS:
                base, enh = layer(zc, f'{cn}|{t}|{br}|eval')
                rows.append(dict(source='claims P33', cond=f'{cn} {t} {br}', budget='33', v2_total=(base + enh).mean(), base=base.mean(), base_lo=ci3(base)[1], base_hi=ci3(base)[2],
                                 enh=enh.mean(), enh_lo=ci3(enh)[1], enh_hi=ci3(enh)[2], enh_share=enh.mean() / max((base + enh).mean(), 1e-9)))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'e1_layers.csv'), index=False); pd.DataFrame(ab).to_csv(os.path.join(OUT, 'e1_ablation_sweep.csv'), index=False)
    return pd.DataFrame(rows), pd.DataFrame(ab)

if __name__ == '__main__':
    for g in sys.argv[1:]: globals()[g]()
