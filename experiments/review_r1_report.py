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


# ---------------- E2: C2 robustness grid ----------------
def _variant_vals(z, pre_fn, names, tu_fn, var, block=None):
    """pick per-scheme exposure (fixed 1/1500 or tuned on tune set) -> eval arrays, tune means; genie over GENIE_SET."""
    if var == 'fixed 1/1500': pick = {n: '1/1500' for n in names}
    else: pick = {n: max(T_EXPS, key=lambda t: tu_fn(t, n)) for n in names}
    ev = {n: G(z, pre_fn(pick[n], 'eval'), n, block if n in BASEL else None) for n in names}
    tu = {n: G(z, pre_fn(pick[n], 'tune'), n, block if n in BASEL else None).mean() for n in names}
    gch = [(n, t) for n in GENIE_SET for t in (['1/1500'] if var == 'fixed 1/1500' else T_EXPS)]
    gn, gt = max(gch, key=lambda x: tu_fn(x[1], x[0]))
    ev['genie'] = G(z, pre_fn(gt, 'eval'), gn, block); tu['genie'] = G(z, pre_fn(gt, 'tune'), gn, block).mean()
    pick['genie'] = f'{SHORT[gn]}@{gt}'
    return ev, tu, pick

def e2():
    rows = []
    for b in PREFS:
        f = os.path.join(SYM, f'review_e2_P{b}.npz')
        if not os.path.exists(f): continue
        z = np.load(f)
        for cn, d in E2_D.items():
            for bn in BRS:
                pf = lambda t, s, cn=cn, bn=bn: f'{cn}|{t}|{bn}|{s}'
                tcache = {}
                def tu_fn(t, n, pf=pf):
                    k = (t, n)
                    if k not in tcache: tcache[k] = G(z, pf(t, 'tune'), n).mean()
                    return tcache[k]
                for var in ('fixed 1/1500', 'tuned t_exp'):
                    for blk in (None, 48):
                        ev, tu, pick = _variant_vals(z, pf, list(SCH), tu_fn, var, blk)
                        cands = BASEL + ['genie']
                        bt = max(cands, key=lambda n: tu[n]); be = max(cands, key=lambda n: ev[n].mean())
                        r = dict(budget=b, distance_m=d, brightness=bn, exposure=var, baseline_crc='48-bit blocks' if blk else 'native',
                                 v2=ev[V2].mean(), v2_t=pick[V2], v2_base_only=ev[BO].mean())
                        for lab, o in (('tunebest', bt), ('evalbest', be)):
                            dd = paired_diff(ev[V2], ev[o])
                            r.update({f'{lab}': SHORT[o] + ('' if o != 'genie' else f"({pick['genie']})"), f'{lab}_t': pick[o], f'{lab}_bps': ev[o].mean(),
                                      f'{lab}_diff': dd[0], f'{lab}_lo': dd[1], f'{lab}_hi': dd[2]})
                        dq = paired_diff(ev[V2], ev[Q]); r.update(qcd_bps=ev[Q].mean(), qcd_diff=dq[0], qcd_lo=dq[1], qcd_hi=dq[2])
                        rows.append(r)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'e2_robust.csv'), index=False)
    s = df.groupby(['budget', 'distance_m', 'baseline_crc']).agg(cases=('tunebest_lo', 'size'), min_lo_tunebest=('tunebest_lo', 'min'),
                                                                   min_lo_evalbest=('evalbest_lo', 'min')).reset_index()
    s['survives_all_tunebest'] = s.min_lo_tunebest > 0; s['survives_all_evalbest'] = s.min_lo_evalbest > 0
    s.to_csv(os.path.join(OUT, 'e2_survival.csv'), index=False); return df, s

def e2_identity():
    """P33 d3.0 at 1/128, 1/256 must equal claims.npz (same seeds, same code path)."""
    z = np.load(os.path.join(SYM, 'review_e2_P33.npz')); c = np.load(os.path.join(SYM, 'claims.npz')); n = same = 0
    for k in c.files:
        if k.startswith('d3.0|'):
            n += 1; same += int(np.array_equal(z[k], c[k], equal_nan=True))
    out = dict(compared_arrays=n, identical=same); json.dump(out, open(os.path.join(OUT, 'e2_identity_check.json'), 'w')); return out

# ---------------- E3: IMX219 ----------------
def e3():
    from channel import presets_phys as pp
    z = np.load(os.path.join(SYM, 'review_e3valid.npz')); rows = []
    for k in sorted(z.files, key=lambda k: float(k.split('|')[0])):
        if k.endswith('|err'):
            br = float(k.split('|')[0]); b, lo, hi = cluster_ber(z[k]); s = z[k.replace('|err', '|sat')]
            rows.append(dict(brightness=br, symbols=z[k].shape[0], ber=b, ber_lo=lo, ber_hi=hi, sat=np.nanmean(s) if np.isfinite(s).any() else np.nan,
                             finder_ok_frac=float(np.isfinite(s).mean()), published=0.0113))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'e3_validation.csv'), index=False)
    out = {}
    for g in ('e3claims', 'e3bracket', 'e3sweep'):
        f = os.path.join(SYM, f'review_{g}.npz')
        if os.path.exists(f): out[g] = np.load(f)
    if 'e3claims' in out:
        z = out['e3claims']; rows = []
        conds = sorted({k.split('|')[0] for k in z.files})
        for cn in conds:
            pf = lambda t, s, cn=cn: f'{cn}|{t}|{s}'
            tu_fn = lambda t, n, pf=pf: G(z, pf(t, 'tune'), n).mean()
            for var in ('fixed 1/1500', 'tuned t_exp'):
                for blk in (None, 48):
                    ev, tu, pick = _variant_vals(z, pf, list(SCH), tu_fn, var, blk)
                    cands = BASEL + ['genie']; bt = max(cands, key=lambda n: tu[n]); be = max(cands, key=lambda n: ev[n].mean())
                    d = float(z[f'{pf("1/1500", "eval")}|{V2}|err'].shape[0] and 0) or None
                    r = dict(cond=cn, exposure=var, baseline_crc='48-bit blocks' if blk else 'native', v2=ev[V2].mean(), v2_t=pick[V2],
                             v2_base_only=ev[BO].mean())
                    for lab, o in (('tunebest', bt), ('evalbest', be), ('qcd', Q), ('v2bo', BO)):
                        dd = paired_diff(ev[V2], ev[o])
                        r.update({lab: SHORT[o], f'{lab}_bps': ev[o].mean(), f'{lab}_diff': dd[0], f'{lab}_lo': dd[1], f'{lab}_hi': dd[2]})
                    rows.append(r)
        pd.DataFrame(rows).to_csv(os.path.join(OUT, 'e3_claims.csv'), index=False)
    if 'e3bracket' in out:
        z = out['e3bracket']; zc = out.get('e3claims'); rows = []
        for k in sorted({'|'.join(k.split('|')[:3]) for k in z.files}):
            cn, t, bn = k.split('|'); ev = {n: G(z, k + '|eval', n) for n in SCH}
            for zz, lab, pre in ((z, bn, k + '|eval'),) + (((zc, '1/128', f'{cn}|1/1500|eval'),) if zc is not None and bn == '1/64' else ()):
                ev = {n: G(zz, pre, n) for n in SCH}; be = max(BASEL, key=lambda n: ev[n].mean()); dd = paired_diff(ev[V2], ev[be])
                rows.append(dict(cond=cn, brightness=lab, v2=ev[V2].mean(), v2_base_only=ev[BO].mean(), best_baseline_eval=SHORT[be], best_bps=ev[be].mean(),
                                 diff=dd[0], lo=dd[1], hi=dd[2]))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, 'e3_bracket.csv'), index=False)
    if 'e3sweep' in out:
        z = out['e3sweep']; p19 = pp.imx219(); rows = []
        ds = sorted({float(k.split('|')[0]) for k in z.files})
        for d in ds:
            pre = f'{d}|eval'; tu = {n: G(z, f'{d}|tune', n).mean() for n in GENIE_SET}; gn = max(tu, key=tu.get)
            for n in E3_LINE + ['genie']:
                x = G(z, pre, gn if n == 'genie' else n); m, lo, hi = boot_ci(x)
                rows.append(dict(sensor='IMX219', distance_m=d, px_per_led=ph.f_px(p19) * 65.0 / 8 * 1e-3 / d, scheme=SHORT[n] + (f'({SHORT[gn]})' if n == 'genie' else ''),
                                 goodput=m, lo=lo, hi=hi))
        for i, d in enumerate(DIST):
            zz = np.load(os.path.join(SYM, 'sweeps_PHYS_P33.npz')); zb = np.load(os.path.join(SYM, 'review_e1sweep.npz')); pre = f'distance_m|{i}|eval'
            gg = {n: G(zz, f'distance_m|{i}|genie', n).mean() for n in GENIE_SET}; gn = max(gg, key=gg.get)
            for n in E3_LINE + ['genie']:
                x = sym_goodput(zb[f'P33|{pre}|{BO}|err'], SCH[BO].layers, RATE) if n == BO else G(zz, pre, gn if n == 'genie' else n); m, lo, hi = boot_ci(x)
                rows.append(dict(sensor='IMX174', distance_m=float(d), px_per_led=ph.f_px(ph.P) * 65.0 / 8 * 1e-3 / d, scheme=SHORT[n] + (f'({SHORT[gn]})' if n == 'genie' else ''),
                                 goodput=m, lo=lo, hi=hi))
        df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'e3_sweep_pxled.csv'), index=False); plot_pxled(df)
    return out.keys()

def plot_pxled(df):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for a, sen in zip(ax, ('IMX174', 'IMX219')):
        d = df[df.sensor == sen]
        for sc in sorted(d.scheme.unique(), key=lambda s: (not s.startswith('v2'), s)):
            q = d[d.scheme == sc].sort_values('px_per_led'); lab = 'genie' if sc.startswith('genie') else sc
            a.plot(q.px_per_led, q.goodput, marker='o', ms=3, label=lab, lw=2 if sc == 'v2' else 1)
            a.fill_between(q.px_per_led, q.lo, q.hi, alpha=0.12)
        a.set_xscale('log'); a.set_xlabel('px per LED (pitch on sensor)'); a.set_title(f'{sen}, P33'); a.grid(alpha=0.3)
    ax[0].set_ylabel('goodput [bps]'); ax[1].legend(fontsize=7); fig.tight_layout()
    for e in ('png', 'pdf'): fig.savefig(os.path.join(OUT, f'e3_goodput_vs_pxled.{e}'), dpi=150)

# ---------------- E1: decomposition of the v2 vs base-only gap (P25/P33/P42, 2.25-4.0 m) ----------------
def e1_decomp():
    zd = np.load(os.path.join(SYM, 'review_e1dec.npz')); zb = np.load(os.path.join(SYM, 'review_e1sweep.npz'))
    L2, L7 = BO + ' [2-level dec]', BO + ' [lit 0.75]'; f = lambda d: f"{d[0]:+.1f} [{d[1]:.1f},{d[2]:.1f}]"; rows = []
    for b in PREFS:
        z = np.load(os.path.join(SYM, f'sweeps_PHYS_P{b}.npz'))
        for i in sorted({int(k.split('|')[2]) for k in zd}):
            pre = f'distance_m|{i}|eval'; v2 = G(z, pre, V2); base, _ = layer(z, pre)
            g = lambda zz, n: sym_goodput(zz[f'P{b}|{pre}|{n}|err'], [('base', 48)], RATE)
            bo, b2, b7 = g(zb, BO), g(zd, L2), g(zd, L7)
            rows.append({'P': b, 'd': DIST[i], 'v2': round(v2.mean(), 2), 'v2base': round(base.mean(), 2), 'bo': round(bo.mean(), 2), 'bo_2lvdec': round(b2.mean(), 2),
                         'bo_lit075': round(b7.mean(), 2), 'v2-bo2lv': f(paired_diff(v2, b2)), 'v2-lit075': f(paired_diff(v2, b7)), 'bo2lv-bo': f(paired_diff(b2, bo))})
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'e1_decomposition.csv'), index=False); return df

if __name__ == '__main__':
    for g in sys.argv[1:]: globals()[g]()
