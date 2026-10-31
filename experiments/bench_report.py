"""Benchmark r0 analysis -> results/benchmark/*.csv. Paired CRN bootstrap (experiments.stats.paired_diff, B=2000).
  oracle   : detector vs oracle-corner goodput per scheme (IMX174 sweep fixed, IMX174 claims conds fixed+tuned at 1/128,
             IMX219 e3claims points fixed+tuned for presets imx219f / imx219cq). loss_total = R_max - D; detector loss = O - D;
             modulation/channel loss = R_max - O (R_max = error-free goodput incl. CRC overhead).
  e3       : regenerated E3 tables (imx219f, imx219cq): validation, claims (real finder + genie-corner row), binding margins.
  ablation : audit R3 factorial {lit 1.0 scaled, lit 0.75} x {1-level, 2-level} + R8 radiant-equal, P33 3.0-3.5 m.
  seeds    : C2 binding margins, E1 decomposition and E2 worst cases on every available seed set + spread.
Binding margin (audit R2) = min over all other schemes (COMP: baselines, v1, v1-base, v2-CS, genie) x {native CRC, 48-bit blocks} of the paired mean
difference v2 - baseline; reported with that pair's CI."""
import os, sys, json, numpy as np, pandas as pd
from experiments.stats import sym_goodput, paired_diff, cluster_ber
from experiments.review_r1 import lineup_seed, DIST, PREFS, E2_D
from experiments.audit_r1 import T_EXPS
from experiments.run_phys import GENIE_SET
from tx.ablation import Level075TwoLevelDecoder
from channel import physical as ph

RES = 'results'; SYM = os.path.join(RES, 'phys_sym'); OUT = os.path.join(RES, 'benchmark'); os.makedirs(OUT, exist_ok=True)
SCH = {s.name: s for s in lineup_seed()}; RATE = ph.P['f_tx']
V2, BO, Q = 'HNCSM v2', 'HNCSM v2-base-only', 'QCD-style-inspired (Vasantha22)'
L2, L7, L72 = BO + ' [2-level dec]', BO + ' [lit 0.75]', BO + ' [lit 0.75, 2-level dec]'
VARS = (L2, L7, L72)
HN = [n for n in SCH if n.startswith('HNCSM')]; BASEL = [n for n in SCH if n not in HN]
# comparison set for binding margins (audit R2): every scheme except v2 itself and its diagnostic ablations (incl. v1, v1-base, v2-CS)
COMP = [n for n in SCH if n not in (V2, BO) + VARS]
ld = lambda f: np.load(os.path.join(SYM, f)) if os.path.exists(os.path.join(SYM, f)) else None
fmt = lambda d: f"{d[0]:+.1f} [{d[1]:.1f}, {d[2]:.1f}]"

def G(z, key, n, block=None):
    k = f'{key}|{n}|err'
    return None if z is None or k not in z else sym_goodput(z[k], SCH[n].layers, RATE, block)
def rmax(n): return sym_goodput(np.zeros((1, SCH[n].nbits)), SCH[n].layers, RATE)[0]

def pick_tuned(z, pre, n):
    """pre(t, split) -> key. Exposure maximising the tune-set mean (this scheme, this receiver mode)."""
    v = {t: G(z, pre(t, 'tune'), n) for t in T_EXPS}; v = {t: x.mean() for t, x in v.items() if x is not None}
    return max(v, key=v.get) if v else None

# ------------------------------------------------------------------------------------------------ oracle vs detector
def _orows(sensor, cond, mode, zd, zo, pre_d, pre_o, names, tuned):
    rows = []
    for n in names:
        if tuned:
            td, to = pick_tuned(zd, pre_d, n), pick_tuned(zo, pre_o, n)
            if td is None or to is None: continue
            d, o = G(zd, pre_d(td, 'eval'), n), G(zo, pre_o(to, 'eval'), n)
            # paired at a common exposure is not possible if the picks differ; CRN pairing holds (seeds depend on geometry only)
        else:
            d, o = G(zd, pre_d('1/1500', 'eval'), n), G(zo, pre_o('1/1500', 'eval'), n); td = to = '1/1500'
        if d is None or o is None: continue
        R = rmax(n); dd = paired_diff(o, d); lt = R - d.mean()
        rows.append(dict(sensor=sensor, cond=cond, exposure=mode, scheme=n, R_max=round(R, 1), detector_bps=round(d.mean(), 1), oracle_bps=round(o.mean(), 1),
                         t_det=td, t_orc=to, det_loss=round(dd[0], 1), det_lo=round(dd[1], 1), det_hi=round(dd[2], 1), mod_loss=round(R - o.mean(), 1),
                         det_share_of_loss=round(dd[0] / lt, 3) if lt > 1e-9 else np.nan))
    return rows

def oracle():
    rows = []; zs = ld('sweeps_PHYS_P33.npz'); zb = ld('review_e1sweep.npz'); zo = ld('review_or_sweep.npz')
    if zo is not None:
        for i in range(2, 15, 2):
            k = f'distance_m|{i}|eval'
            for n in [x for x in SCH if x not in VARS]:
                zd, kd = (zb, 'P33|' + k) if n == BO else (zs, k)
                d, o = G(zd, kd, n), G(zo, k, n)
                if d is None or o is None: continue
                R = rmax(n); dd = paired_diff(o, d); lt = R - d.mean()
                rows.append(dict(sensor='IMX174', cond=f'{DIST[i]} m', exposure='default 1/1500', scheme=n, R_max=round(R, 1), detector_bps=round(d.mean(), 1),
                                 oracle_bps=round(o.mean(), 1), t_det='1/1500', t_orc='1/1500', det_loss=round(dd[0], 1), det_lo=round(dd[1], 1), det_hi=round(dd[2], 1),
                                 mod_loss=round(R - o.mean(), 1), det_share_of_loss=round(dd[0] / lt, 3) if lt > 1e-9 else np.nan))
    zc, zoc = ld('claims.npz'), ld('review_or_claims.npz')
    if zoc is not None:
        for cn in ('d2.5', 'd3.0', 'yaw70', 'blur4'):
            pre = lambda t, s, cn=cn: f'{cn}|{t}|1/128|{s}'
            for tuned in (False, True):
                rows += _orows('IMX174', cn, 'tuned' if tuned else 'fixed 1/1500', zc, zoc, pre, pre, [n for n in SCH if n not in VARS], tuned)
    for ps in ('imx219f', 'imx219cq'):
        zd, zo2 = ld(f'review_e3claims@{ps}.npz'), ld(f'review_or_e3claims@{ps}.npz')
        if zd is None or zo2 is None: continue
        for cn in ('d2.5', 'd3.0', 'd3.25', 'd3.5', 'm2.5', 'm3.0', 'm3.25', 'm3.5'):
            pre = lambda t, s, cn=cn: f'{cn}|{t}|{s}'
            for tuned in (False, True):
                rows += _orows(f'IMX219 ({ps})', cn, 'tuned' if tuned else 'fixed 1/1500', zd, zo2, pre, pre, [n for n in SCH if n not in VARS], tuned)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'oracle_vs_detector.csv'), index=False)
    if len(df):
        s = df.groupby(['sensor', 'exposure', 'scheme']).agg(n_points=('cond', 'size'), mean_R_max=('R_max', 'mean'), mean_detector=('detector_bps', 'mean'),
                                                            mean_oracle=('oracle_bps', 'mean'), mean_det_loss=('det_loss', 'mean'), mean_mod_loss=('mod_loss', 'mean')).reset_index()
        s['det_share_of_total_loss'] = (s.mean_det_loss / (s.mean_R_max - s.mean_detector)).round(3)
        s.round(1).to_csv(os.path.join(OUT, 'oracle_vs_detector_summary.csv'), index=False)
        # ranking flips: best scheme per point under each receiver
        rk = []
        for (se, c, e), g in df.groupby(['sensor', 'cond', 'exposure']):
            rk.append(dict(sensor=se, cond=c, exposure=e, best_detector=g.loc[g.detector_bps.idxmax(), 'scheme'], best_oracle=g.loc[g.oracle_bps.idxmax(), 'scheme'],
                           v2_rank_det=int((g.detector_bps > g[g.scheme == V2].detector_bps.max()).sum() + 1) if V2 in set(g.scheme) else None,
                           v2_rank_orc=int((g.oracle_bps > g[g.scheme == V2].oracle_bps.max()).sum() + 1) if V2 in set(g.scheme) else None))
        pd.DataFrame(rk).to_csv(os.path.join(OUT, 'oracle_ranking.csv'), index=False)
    return df

# ------------------------------------------------------------------------------------------------ binding margins
def binding(z, pre, tuned, names=None):
    """v2 vs every baseline + genie, native and 48-bit; returns (binding row, all rows). pre(t, split)->key."""
    names = [n for n in (names or COMP) if G(z, pre('1/1500', 'eval'), n) is not None]
    pk = (lambda n: pick_tuned(z, pre, n)) if tuned else (lambda n: '1/1500')
    tv = pk(V2); v = G(z, pre(tv, 'eval'), V2); out = []
    gch = [(n, t) for n in GENIE_SET for t in (T_EXPS if tuned else ['1/1500']) if G(z, pre(t, 'tune'), n) is not None]
    for blk in (None, 48):
        for n in names:
            t = pk(n); b = G(z, pre(t, 'eval'), n, blk); d = paired_diff(v, b)
            out.append(dict(crc='48-bit' if blk else 'native', baseline=n, t=t, v2=v.mean(), base=b.mean(), diff=d[0], lo=d[1], hi=d[2]))
        if gch:
            gn, gt = max(gch, key=lambda x: G(z, pre(x[1], 'tune'), x[0], blk).mean()); b = G(z, pre(gt, 'eval'), gn, blk); d = paired_diff(v, b)
            out.append(dict(crc='48-bit' if blk else 'native', baseline=f'genie({gn}@{gt})', t=gt, v2=v.mean(), base=b.mean(), diff=d[0], lo=d[1], hi=d[2]))
    o = pd.DataFrame(out); return o.loc[o['diff'].idxmin()].to_dict(), o

def seedsets():
    """(label, npz, key-prefix fn(b) -> pre(t,split) or None)."""
    S = []
    for lab, f in (('SEED (claims/E2 seeds)', None), ('A=31415926', 'review_seedA.npz'), ('B=27182818', 'review_seedB.npz')):
        if f is None:
            S.append((lab, {b: ld(f'review_e2_P{b}.npz') for b in PREFS}, lambda b, cn, br: (lambda t, s: f'{cn}|{t}|{br}|{s}')))
        else:
            z = ld(f)
            if z is not None: S.append((lab, {b: z for b in PREFS}, lambda b, cn, br: (lambda t, s, b=b: f'P{b}|{cn}|{t}|{br}|{s}')))
    return S

def seeds():
    rows = []
    for lab, Z, P in seedsets():
        for b in PREFS:
            z = Z[b]
            if z is None: continue
            for cn in E2_D:
                cases = [('C2 fixed 1/1500, 1/128', '1/128', False)] + ([('E2 tuned, 1/128', '1/128', True), ('E2 fixed, 1/256', '1/256', False), ('E2 tuned, 1/256', '1/256', True)] if b == '33' else [])
                for case, br, tu in cases:
                    pre = P(b, cn, br)
                    if G(z, pre('1/1500', 'eval'), V2) is None: continue
                    r, _ = binding(z, pre, tu)
                    rows.append(dict(seed_set=lab, budget=b, distance=cn, case=case, metric='v2 - binding baseline', baseline=r['baseline'], crc=r['crc'],
                                     value=round(r['diff'], 1), lo=round(r['lo'], 1), hi=round(r['hi'], 1)))
                if b == '33':   # E1 decomposition at fixed 1/1500, 1/128
                    pre = P(b, cn, '1/128'); k = pre('1/1500', 'eval')
                    for a, c in ((V2, BO), (V2, L7), (L2, BO), (L72, L7), (L7, BO), (L72, L2)):
                        x, y = G(z, k, a), G(z, k, c)
                        if x is None or y is None: continue
                        d = paired_diff(x, y)
                        rows.append(dict(seed_set=lab, budget=b, distance=cn, case='E1 fixed 1/1500, 1/128', metric=f'{a} - {c}', baseline='', crc='native',
                                         value=round(d[0], 1), lo=round(d[1], 1), hi=round(d[2], 1)))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'seed_replication.csv'), index=False)
    if len(df):
        g = df.groupby(['budget', 'distance', 'case', 'metric'])
        sp = g.agg(n_sets=('value', 'size'), mean=('value', 'mean'), min=('value', 'min'), max=('value', 'max'),
                   min_lo=('lo', 'min'), max_hi=('hi', 'max'), all_lo_gt0=('lo', lambda x: bool((x > 0).all())), all_hi_lt0=('hi', lambda x: bool((x < 0).all()))).reset_index()
        sp['spread'] = sp['max'] - sp['min']
        sp['verdict'] = np.where(sp.all_lo_gt0, 'positive on every set', np.where(sp.all_hi_lt0, 'negative on every set', 'NOT stable in sign / n.s. on some set'))
        sp.round(1).to_csv(os.path.join(OUT, 'seed_spread.csv'), index=False)
    return df

# ------------------------------------------------------------------------------------------------ ablation (R3, R8)
def ablation():
    zs, zb, zd, zf, zr = ld('sweeps_PHYS_P33.npz'), ld('review_e1sweep.npz'), ld('review_e1dec.npz'), ld('bench_fact.npz'), ld('bench_radiant.npz')
    rows = []
    for i in (10, 11, 12):
        k = f'distance_m|{i}|eval'; kp = 'P33|' + k
        cell = {V2: G(zs, k, V2), BO: G(zb, kp, BO), L2: G(zd, kp, L2), L7: G(zd, kp, L7), L72: G(zf, kp, L72)}
        r = dict(distance_m=DIST[i], norm='equal summed drive', **{n: round(v.mean(), 1) for n, v in cell.items() if v is not None})
        gap = paired_diff(cell[V2], cell[BO])
        for lab, a, c in (('v2-bo', V2, BO), ('lit075-bo (TX level, 1-lvl dec)', L7, BO), ('2lv-bo (decoder, TX 1.0)', L2, BO),
                          ('lit075_2lv-lit075 (decoder, TX 0.75)', L72, L7), ('lit075_2lv-2lv (TX level, 2-lvl dec)', L72, L2), ('v2-lit075_2lv (residual)', V2, L72), ('v2-lit075', V2, L7)):
            if cell.get(a) is not None and cell.get(c) is not None: r[lab] = fmt(paired_diff(cell[a], cell[c]))
        r['recovered_by_lit075_%'] = round(100 * paired_diff(cell[L7], cell[BO])[0] / gap[0], 1)
        if cell[L72] is not None: r['recovered_by_lit075_2lv_%'] = round(100 * paired_diff(cell[L72], cell[BO])[0] / gap[0], 1)
        rows.append(r)
        if zr is not None:
            c2 = {n: G(zr, kp, n) for n in (V2, BO, L2, L7, L72, Q)}
            r2 = dict(distance_m=DIST[i], norm='radiant-equal', **{n: round(v.mean(), 1) for n, v in c2.items() if v is not None})
            for lab, a, c in (('v2-bo', V2, BO), ('v2-lit075', V2, L7), ('v2-lit075_2lv (residual)', V2, L72), ('lit075-bo (TX level, 1-lvl dec)', L7, BO), ('v2-QCD', V2, Q)):
                r2[lab] = fmt(paired_diff(c2[a], c2[c]))
            g2 = paired_diff(c2[V2], c2[BO])[0]; r2['recovered_by_lit075_%'] = round(100 * paired_diff(c2[L7], c2[BO])[0] / g2, 1) if abs(g2) > 1e-9 else np.nan
            r2['recovered_by_lit075_2lv_%'] = round(100 * paired_diff(c2[L72], c2[BO])[0] / g2, 1) if abs(g2) > 1e-9 else np.nan
            rows.append(r2)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'ablation_factorial.csv'), index=False); return df

# ------------------------------------------------------------------------------------------------ E3 regenerated
def e3():
    rows, vr = [], []
    for ps in ('imx219f', 'imx219cq'):
        zv = ld(f'review_e3valid@{ps}.npz')
        if zv is not None:
            for k in sorted([k for k in zv.files if k.endswith('|err')], key=lambda k: float(k.split('|')[0])):
                b, lo, hi = cluster_ber(zv[k]); s = zv[k.replace('|err', '|sat')]
                vr.append(dict(preset=ps, brightness=float(k.split('|')[0]), symbols=zv[k].shape[0], ber=b, ber_lo=lo, ber_hi=hi, finder_ok_frac=float(np.isfinite(s).mean()), published=0.0113))
        for corners, f in (('real finder (scale-free)', f'review_e3claims@{ps}.npz'), ('genie corners', f'review_or_e3claims@{ps}.npz')):
            z = ld(f)
            if z is None: continue
            for cn in ('d2.5', 'd3.0', 'd3.25', 'd3.5', 'm2.5', 'm3.0', 'm3.25', 'm3.5'):
                pre = lambda t, s, cn=cn: f'{cn}|{t}|{s}'
                for tu in (False, True):
                    r, allr = binding(z, pre, tu)
                    best = allr[allr.crc == 'native'].sort_values('base').iloc[-1]
                    rows.append(dict(preset=ps, corners=corners, cond=cn, exposure='tuned' if tu else 'fixed 1/1500', v2=round(r['v2'], 1),
                                     best_baseline=best['baseline'], best_bps=round(best['base'], 1), binding_baseline=r['baseline'], binding_crc=r['crc'],
                                     binding_margin=round(r['diff'], 1), lo=round(r['lo'], 1), hi=round(r['hi'], 1),
                                     verdict='v2 > all' if r['lo'] > 0 else ('v2 < binding' if r['hi'] < 0 else 'n.s.')))
    pd.DataFrame(vr).to_csv(os.path.join(OUT, 'e3_validation.csv'), index=False)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'e3_claims.csv'), index=False); return df

# ------------------------------------------------------------------------------------------------ C2 binding (R2), original seeds
def c2_binding():
    rows = []
    for b in PREFS:
        z = ld(f'review_e2_P{b}.npz')
        if z is None: continue
        for cn in E2_D:
            r, allr = binding(z, lambda t, s, cn=cn: f'{cn}|{t}|1/128|{s}', False)
            rows.append(dict(seeds='claims/E2', budget=b, distance=cn, v2=round(r['v2'], 1), binding_baseline=r['baseline'], crc=r['crc'], margin=round(r['diff'], 1), lo=round(r['lo'], 1), hi=round(r['hi'], 1)))
        zs = ld(f'sweeps_PHYS_P{b}.npz')
        for i in (10, 11, 12):
            r, _ = binding(zs, lambda t, s, i=i: f'distance_m|{i}|{s}', False)
            rows.append(dict(seeds='sweep (run_phys)', budget=b, distance=f'd{DIST[i]}', v2=round(r['v2'], 1), binding_baseline=r['baseline'], crc=r['crc'], margin=round(r['diff'], 1), lo=round(r['lo'], 1), hi=round(r['hi'], 1)))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'c2_binding_margins.csv'), index=False); return df

if __name__ == '__main__':
    for g in sys.argv[1:]: print(globals()[g]().to_string())
