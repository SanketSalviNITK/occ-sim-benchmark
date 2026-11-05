"""benchmark-r6 analysis (analysis only; reads results/phys_sym/*.npz, writes results/benchmark/r6/*.csv|png|pdf).
Bootstrap: paired CRN symbol bootstrap, resampling unit = Tx symbol (one selected frame per symbol), B and bootstrap
seed stated in every output. Two-sided bootstrap p = 2 min(P*(d<=0), P*(d>=0)) (floor 1/B). For a binding margin
(min over comparisons) the intersection-union p is the max over comparisons of the per-comparison p (Berger 1982).
  boot_stab : ablation residual v2 - (lit0.75 + 2-level dec) at 3.0/3.25/3.5 m over 25 bootstrap seeds, B=2000 and B=10000
  holm      : Holm-Bonferroni (Holm 1979) over the CLAIMS_r5 claim family
  sens      : tornado of the C2 binding margin change (r6_sens.npz vs review_e2_P33.npz, same CRN symbols)
  geo       : C2-style binding margins on the second geometries (r6_geo80.npz, r6_geoyaw30.npz)
  finder    : per-scheme finder failure / gross-error rates and detector vs demodulation loss (r6_finder.npz)
  valid6    : QCD-OCC validation grid (r6_valid6.npz)
  phycom    : margins of PhyCom plugin baselines vs v2 at C2 and across distance (r6_phycom.npz)
Usage: python -m experiments.r6_report boot_stab holm sens geo finder valid6 phycom"""
import os, sys, json, numpy as np, pandas as pd
from experiments.stats import sym_goodput, cluster_ber
from experiments.bench_report import SCH, V2, BO, L72, COMP, VARS, ld, pick_tuned, OUT as BOUT, DIST, PREFS, E2_D
from experiments.audit_r1 import T_EXPS
from experiments.run_phys import GENIE_SET

OUT = os.path.join(BOUT, 'r6'); os.makedirs(OUT, exist_ok=True)
B_R6 = 10000; BSEED = 0

def _layers(n):
    if n in SCH: return SCH[n].layers
    from occbench import create; return create(n).layers

def Gr(z, key, n, block=None, rate=15.0):
    k = f'{key}|{n}|err'
    return None if z is None or k not in z else sym_goodput(z[k], _layers(n), rate, block)

def boot(d, B=B_R6, seed=BSEED, idx=None):
    d = np.asarray(d, float); r = np.random.RandomState(seed)
    idx = r.randint(0, len(d), (B, len(d))) if idx is None else idx
    m = d[idx].mean(1)
    p = min(1.0, max(2 * min((m <= 0).mean(), (m >= 0).mean()), 1.0 / B))
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), p

def pairs(z, pre, tuned=False, rate=15.0, names=None):
    """Per-comparison per-symbol differences v2 - X (same rule as bench_report.binding). Returns list of (label, crc, d)."""
    names = [n for n in (names or COMP) if Gr(z, pre('1/1500', 'eval'), n) is not None]
    pk = (lambda n: pick_tuned(z, pre, n)) if tuned else (lambda n: '1/1500')
    v = Gr(z, pre(pk(V2), 'eval'), V2, rate=rate); out = []
    gch = [(n, t) for n in GENIE_SET for t in (T_EXPS if tuned else ['1/1500']) if Gr(z, pre(t, 'tune'), n) is not None]
    for blk in (None, 48):
        for n in names: out.append((n, '48-bit' if blk else 'native', v - Gr(z, pre(pk(n), 'eval'), n, blk, rate)))
        if gch:
            gn, gt = max(gch, key=lambda x: Gr(z, pre(x[1], 'tune'), x[0], blk, rate).mean())
            out.append((f'genie({gn}@{gt})', '48-bit' if blk else 'native', v - Gr(z, pre(gt, 'eval'), gn, blk, rate)))
    return out

def binding_p(P, B=B_R6, seed=BSEED):
    """P = pairs(); binding row (min mean) with its CI, plus IUT p = max_j p_j."""
    res = [(lab, crc) + boot(d, B, seed) for lab, crc, d in P]
    b = min(res, key=lambda r: r[2]); p_iut = max(r[5] for r in res)
    return dict(baseline=b[0], crc=b[1], margin=b[2], lo=b[3], hi=b[4], p_binding_pair=b[5], p_iut=p_iut)

def verdict(lo, hi): return 'positive' if lo > 0 else ('negative' if hi < 0 else 'n.s.')

# ------------------------------------------------------------------ 4a bootstrap-seed stability of the ablation verdict
def boot_stab():
    zs, zf = ld('sweeps_PHYS_P33.npz'), ld('bench_fact.npz'); rows = []
    for i in (10, 11, 12):
        k = f'distance_m|{i}|eval'; d = Gr(zs, k, V2) - Gr(zf, 'P33|' + k, L72)
        for B in (2000, 10000):
            for s in range(25):
                m, lo, hi, p = boot(d, B, s)
                rows.append(dict(distance_m=DIST[i], B=B, boot_seed=s, diff=round(m, 2), lo=round(lo, 2), hi=round(hi, 2), p=p, verdict=verdict(lo, hi)))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'ablation_boot_stability.csv'), index=False)
    s = df.groupby(['distance_m', 'B']).agg(n_seeds=('boot_seed', 'size'), diff=('diff', 'first'), lo_min=('lo', 'min'), lo_max=('lo', 'max'),
                                           hi_min=('hi', 'min'), hi_max=('hi', 'max'), frac_ns=('verdict', lambda v: (v == 'n.s.').mean()),
                                           frac_positive=('verdict', lambda v: (v == 'positive').mean())).reset_index()
    s.to_csv(os.path.join(OUT, 'ablation_boot_stability_summary.csv'), index=False); return s

# ------------------------------------------------------------------ 4b Holm over the claim family
def holm_adjust(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o): run = max(run, min(1.0, (m - r) * p[i])); adj[i] = run
    return adj

def holm():
    rows = []
    # C2 binding, claims/E2 seeds, P25/P33/P42 x 3 distances
    for b in PREFS:
        z = ld(f'review_e2_P{b}.npz')
        for cn in E2_D:
            r = binding_p(pairs(z, lambda t, s, cn=cn: f'{cn}|{t}|1/128|{s}'))
            rows.append(dict(claim='C2 binding', seeds='claims/E2', budget=b, cond=cn, **r))
    # C2 binding P33 on sweep, A, B
    zs = ld('sweeps_PHYS_P33.npz')
    for i, cn in ((10, 'd3.0'), (11, 'd3.25'), (12, 'd3.5')):
        rows.append(dict(claim='C2 binding', seeds='sweep (run_phys)', budget='33', cond=cn, **binding_p(pairs(zs, lambda t, s, i=i: f'distance_m|{i}|{s}'))))
    for lab, f in (('A', 'review_seedA.npz'), ('B', 'review_seedB.npz')):
        z = ld(f)
        for cn in E2_D: rows.append(dict(claim='C2 binding', seeds=lab, budget='33', cond=cn, **binding_p(pairs(z, lambda t, s, cn=cn: f'P33|{cn}|{t}|1/128|{s}'))))
    # oracle 3.0 m claims/E2 vs OOK, vs QCD-style; oracle 3.5 m sweep binding
    zc = ld('review_or_claims.npz'); k = 'd3.0|1/1500|1/128|eval'
    for n in ('OOK-8x8', 'QCD-style-inspired (Vasantha22)'):
        m, lo, hi, p = boot(Gr(zc, k, V2) - Gr(zc, k, n))
        rows.append(dict(claim=f'oracle v2 - {n}', seeds='claims/E2', budget='33', cond='d3.0', baseline=n, crc='native', margin=m, lo=lo, hi=hi, p_binding_pair=p, p_iut=p))
    zo = ld('review_or_sweep.npz'); kk = 'distance_m|12|eval'
    P = [(n, crc, Gr(zo, kk, V2) - Gr(zo, kk, n, blk)) for blk, crc in ((None, 'native'), (48, '48-bit')) for n in SCH if n not in VARS and n != V2 and Gr(zo, kk, n) is not None]
    rows.append(dict(claim='oracle binding', seeds='sweep (run_phys)', budget='33', cond='d3.5', **binding_p(P)))
    # ablation residual
    zf = ld('bench_fact.npz')
    for i in (10, 11, 12):
        k = f'distance_m|{i}|eval'; m, lo, hi, p = boot(Gr(zs, k, V2) - Gr(zf, 'P33|' + k, L72))
        rows.append(dict(claim='ablation residual v2 - (lit0.75+2lv)', seeds='sweep (run_phys)', budget='33', cond=f'd{DIST[i]}', baseline=L72, crc='native', margin=m, lo=lo, hi=hi, p_binding_pair=p, p_iut=p))
    # IMX219 E3 claims (imx219f), real + genie corners, fixed + tuned
    for corners, f in (('real finder (scale-free)', 'review_e3claims@imx219f.npz'), ('genie corners', 'review_or_e3claims@imx219f.npz')):
        z = ld(f)
        if z is None: continue
        for cn in ('d2.5', 'd3.0', 'd3.25', 'd3.5', 'm2.5', 'm3.0', 'm3.25', 'm3.5'):
            for tu in (False, True):
                rows.append(dict(claim=f'IMX219 binding, {corners}', seeds='imx-', budget='33', cond=f'{cn} {"tuned" if tu else "fixed"}',
                                 **binding_p(pairs(z, lambda t, s, cn=cn: f'{cn}|{t}|{s}', tu))))
    df = pd.DataFrame(rows)
    df['verdict_unadj'] = [verdict(a, b) for a, b in zip(df.lo, df.hi)]
    # claim p: 'v2 > every comparison' -> IUT p (max over comparisons); 'v2 < X' or n.s. -> p of that comparison
    df['p_claim'] = np.where(df.verdict_unadj == 'positive', df.p_iut, df.p_binding_pair)
    df['p_holm'] = holm_adjust(df.p_claim.values)
    df['verdict_holm'] = np.where(df.p_holm < 0.05, df.verdict_unadj, 'n.s. (Holm)')
    df['changed'] = df.verdict_unadj != df.verdict_holm
    df['B'] = B_R6; df['boot_seed'] = BSEED; df['family_size'] = len(df)
    df.round(4).to_csv(os.path.join(OUT, 'holm_claims.csv'), index=False); return df

# ------------------------------------------------------------------ 1 sensitivity / tornado
def _delta(PX, PD, B=B_R6, seed=BSEED):
    """Joint bootstrap of binding(X) - binding(D) over the same CRN symbol indices (all pairs share one index draw)."""
    n = len(PX[0][2]); idx = np.random.RandomState(seed).randint(0, n, (B, n))
    mX = np.array([d[idx].mean(1) for _, _, d in PX]).min(0); mD = np.array([d[idx].mean(1) for _, _, d in PD]).min(0)
    pX = min(d.mean() for _, _, d in PX); pD = min(d.mean() for _, _, d in PD); dd = mX - mD
    return pX - pD, float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))

def sens():
    from experiments.revision_r6 import SENS
    zs, zd = ld('r6_sens.npz'), ld('review_e2_P33.npz'); rows = []
    levels = [(f, ln, src, dict(pm)) for f, (_, lv, src) in SENS.items() for ln, (pm, _) in lv.items()]
    for cn in ('d3.0', 'd3.25'):
        PD = pairs(zd, lambda t, s: f'{cn}|{t}|1/128|{s}'); bD = binding_p(PD)
        rows.append(dict(factor='default', level='default', distance=cn, **bD, delta=0.0, d_lo=0.0, d_hi=0.0, source=''))
        for f, ln, src, pm in levels:
            rate = pm.get('f_tx', 15.0)
            pre = lambda t, s, f=f, ln=ln: f'{f}={ln}|{cn}|{t}|1/128|{s}'
            if zs is None or f'{pre("1/1500", "eval")}|{V2}|err' not in zs: continue
            # goodput rate: f_tx levels change the symbol rate; the default cells are rescaled to the same rate for the delta
            PX = pairs(zs, pre, rate=rate); PDr = pairs(zd, lambda t, s: f'{cn}|{t}|1/128|{s}', rate=rate)
            d = _delta(PX, PDr); bX = binding_p(PX)
            rows.append(dict(factor=f, level=ln, distance=cn, **bX, delta=d[0], d_lo=d[1], d_hi=d[2], source=src))
        for bn in ('1/64', '1/256'):   # brightness from the E2 cells (same seeds)
            PX = pairs(zd, lambda t, s, bn=bn: f'{cn}|{t}|{bn}|{s}'); d = _delta(PX, PD); bX = binding_p(PX)
            rows.append(dict(factor='brightness', level=bn, distance=cn, **bX, delta=d[0], d_lo=d[1], d_hi=d[2],
                             source='E2 grid 1/64-1/256 (review_e2_P33.npz); bracket around published QCD-OCC BER, METHODS 9.2'))
    df = pd.DataFrame(rows); df['verdict'] = [verdict(a, b) for a, b in zip(df.lo, df.hi)]
    df['B'] = B_R6; df['boot_seed'] = BSEED
    df.round(2).to_csv(os.path.join(OUT, 'sensitivity_tornado.csv'), index=False)
    _tornado_fig(df); return df

def _tornado_fig(df):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    facs = [f for f in dict.fromkeys(df.factor) if f != 'default']
    for ax, cn in zip(axs, ('d3.0', 'd3.25')):
        g = df[df.distance == cn]; base = g[g.factor == 'default'].margin.iloc[0]
        rng = {f: g[g.factor == f].delta.abs().max() for f in facs}; order = sorted(facs, key=lambda f: rng[f])
        for y, f in enumerate(order):
            for _, r in g[g.factor == f].iterrows():
                col = 'tab:blue' if r.delta >= 0 else 'tab:red'
                ax.barh(y, r.delta, left=0, color=col, alpha=0.6, height=0.6)
                ax.errorbar(r.delta, y, xerr=[[r.delta - r.d_lo], [r.d_hi - r.delta]], fmt='none', ecolor='k', lw=0.8, capsize=2)
                ax.text(r.delta, y + 0.32, str(r.level), fontsize=6, ha='center')
        ax.axvline(0, color='k', lw=0.8); ax.axvline(-base, color='gray', ls='--', lw=0.8)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.set_title(f'{cn[1:]} m: default binding margin {base:+.1f} bps')
        ax.set_xlabel('change in binding margin vs default [bps] (95% paired CI)')
    axs[0].text(0.01, 0.01, 'dashed: margin = 0', transform=axs[0].transAxes, fontsize=7)
    fig.suptitle('C2 sensitivity to ASSUMED parameters (IMX174, P33, 1/1500, claims/E2 seeds, one-at-a-time)', fontsize=9)
    fig.tight_layout(); [fig.savefig(os.path.join(OUT, f'sensitivity_tornado.{e}'), dpi=150) for e in ('png', 'pdf')]; plt.close(fig)

# ------------------------------------------------------------------ 2 second geometry
def geo():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from experiments.revision_r6 import GEO_D
    rows, gp = [], []
    for g, lab in (('geo80', '80 mm panel (10 mm pitch)'), ('geoyaw30', '65 mm panel, 30 deg yaw')):
        z = ld(f'r6_{g}.npz')
        if z is None: continue
        for d in GEO_D:
            pre = lambda t, s, d=d: f'd{d}|{t}|1/128|{s}'
            r = binding_p(pairs(z, pre)); rows.append(dict(geometry=lab, distance_m=d, **r, verdict=verdict(r['lo'], r['hi'])))
            for n in [n for n in SCH if n not in VARS]:
                x = Gr(z, pre('1/1500', 'eval'), n)
                if x is None: continue
                m, lo, hi, _ = boot(x, 2000); gp.append(dict(geometry=lab, distance_m=d, scheme=n, goodput=m, lo=lo, hi=hi))
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED; df.round(2).to_csv(os.path.join(OUT, 'geometry_binding.csv'), index=False)
    gp = pd.DataFrame(gp); gp.round(1).to_csv(os.path.join(OUT, 'geometry_goodput.csv'), index=False)
    if len(gp):
        geos = list(dict.fromkeys(gp.geometry)); fig, axs = plt.subplots(1, len(geos), figsize=(6 * len(geos), 4.5), squeeze=False)
        for ax, g in zip(axs[0], geos):
            for n, h in gp[gp.geometry == g].groupby('scheme'):
                ax.errorbar(h.distance_m, h.goodput, yerr=[h.goodput - h.lo, h.hi - h.goodput], label=n, lw=1.8 if n == V2 else 0.9, capsize=2)
            ax.set_title(g); ax.set_xlabel('distance [m]'); ax.set_ylabel('goodput [bps], native framing')
        axs[0][0].legend(fontsize=6); fig.tight_layout(); [fig.savefig(os.path.join(OUT, f'geometry_goodput.{e}'), dpi=150) for e in ('png', 'pdf')]; plt.close(fig)
    return df

# ------------------------------------------------------------------ 3 finder analysis
def finder():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from experiments.revision_r6 import FIN_D
    z = ld('r6_finder.npz'); ze = ld('review_e2_P33.npz'); zc = ld('claims.npz'); zoc = ld('review_or_claims.npz'); rows = []; chk = []
    names = [n for n in SCH if n not in VARS]
    for d in FIN_D:
        k = f'd{d}|1/1500|1/128|eval'
        for n in names:
            if f'{k}|{n}|err' not in z: continue
            nc, nf, ng = z[f'{k}|{n}|ncand'], z[f'{k}|{n}|nfail'], z[f'{k}|{n}|ngross']; ce = z[f'{k}|{n}|sel_cerr']
            gd, go = Gr(z, k, n), sym_goodput(z[f'{k}|{n}|err_orc'], SCH[n].layers, 15.0)
            R = sym_goodput(np.zeros((1, SCH[n].nbits)), SCH[n].layers, 15.0)[0]
            dl = boot(go - gd, 2000)
            rows.append(dict(distance_m=d, scheme=n, symbols=len(nc), frames=int(nc.sum()), det_fail_frame=nf.sum() / nc.sum(), gross_frame=ng.sum() / nc.sum(),
                             any_bad_frame=(nf + ng).sum() / nc.sum(), sym_no_detection=float((nf == nc).mean()), sym_selected_gross=float(np.nanmean(np.where(np.isfinite(ce), ce > 0.5, np.nan))),
                             R_max=R, detector_bps=gd.mean(), oracle_bps=go.mean(), finder_loss=dl[0], finder_loss_lo=dl[1], finder_loss_hi=dl[2],
                             demod_loss=R - go.mean(), finder_share=(dl[0] / (R - gd.mean())) if R - gd.mean() > 1e-9 else np.nan))
            for zz, kk, f, src in ((ze, f'd{d}|1/1500|1/128|eval', 'err', 'review_e2_P33'), (zc, f'd{d}|1/1500|1/128|eval', 'err', 'claims'),
                                   (zoc, f'd{d}|1/1500|1/128|eval', 'err_orc', 'review_or_claims')):
                key = f'{kk}|{n}|err'
                if zz is not None and key in zz: chk.append(dict(distance_m=d, scheme=n, reference=src, array=f, identical=bool(np.array_equal(zz[key], z[f'{k}|{n}|{f}']))))
    df = pd.DataFrame(rows); df.round(4).to_csv(os.path.join(OUT, 'finder_failure.csv'), index=False)
    pd.DataFrame(chk).to_csv(os.path.join(OUT, 'finder_crn_identity.csv'), index=False)
    # oracle binding margins on canonical seeds at every FIN_D distance (M7)
    ob = []
    for d in FIN_D:
        k = f'd{d}|1/1500|1/128|eval'; v = sym_goodput(z[f'{k}|{V2}|err_orc'], SCH[V2].layers, 15.0)
        P = [(n, crc, v - sym_goodput(z[f'{k}|{n}|err_orc'], SCH[n].layers, 15.0, blk)) for blk, crc in ((None, 'native'), (48, '48-bit')) for n in names if n != V2]
        Pd = [(n, crc, Gr(z, k, V2) - Gr(z, k, n, blk)) for blk, crc in ((None, 'native'), (48, '48-bit')) for n in names if n != V2]
        for mode, PP in (('detector', Pd), ('oracle', P)):
            r = binding_p([x for x in PP if x[0] != BO]); ob.append(dict(seeds='claims/E2', distance_m=d, corners=mode, **r, verdict=verdict(r['lo'], r['hi']),
                                                                          v2_rank=1 + sum(np.mean(-dd) > 0 for nn, c, dd in PP if c == 'native' and nn != BO)))
    pd.DataFrame(ob).round(2).to_csv(os.path.join(OUT, 'oracle_binding_canonical.csv'), index=False)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5))
    for n, h in df.groupby('scheme'):
        lw = 2 if n == V2 else 0.9
        axs[0].plot(h.distance_m, 100 * h.det_fail_frame, marker='o', lw=lw, label=n); axs[1].plot(h.distance_m, 100 * h.gross_frame, marker='o', lw=lw)
        axs[2].plot(h.distance_m, h.finder_loss, marker='o', lw=lw)
    axs[0].set_ylabel('detection failures [% of frames]'); axs[1].set_ylabel('gross errors [% of frames] (corner err > 0.5 pitch)')
    axs[2].set_ylabel('finder loss = oracle - detector [bps]'); [a.set_xlabel('distance [m]') for a in axs]; axs[0].legend(fontsize=6)
    fig.suptitle('Shared corner finder per scheme (IMX174, P33, 1/1500, 1/128, claims/E2 seeds, 1000 symbols/point)', fontsize=9)
    fig.tight_layout(); [fig.savefig(os.path.join(OUT, f'finder_failure.{e}'), dpi=150) for e in ('png', 'pdf')]; plt.close(fig)
    return df


# ------------------------------------------------------------------ 8 PhyCom baselines (plugin schemes)
def phycom():
    """v2 vs each PhyCom-inspired plugin and the paper COMP set; binding including the plugins."""
    from experiments.revision_r6 import PHYCOM_NAMES, PHYCOM_D
    z = ld('r6_phycom.npz'); rows = []
    for d in PHYCOM_D:
        cn = f'd{d}'; pre = lambda t, s, cn=cn: f'{cn}|{t}|1/128|{s}'
        # per-plugin margins (v2 - plugin) native + 48-bit
        for n in PHYCOM_NAMES:
            for blk, crc in ((None, 'native'), (48, '48-bit')):
                dv = Gr(z, pre('1/1500', 'eval'), V2) - Gr(z, pre('1/1500', 'eval'), n, blk)
                m, lo, hi, p = boot(dv); rows.append(dict(distance_m=d, vs=n, crc=crc, margin=m, lo=lo, hi=hi, p=p,
                                                          verdict=verdict(lo, hi), kind='vs_plugin'))
        # binding over COMP + plugins
        P = pairs(z, pre, names=list(COMP) + PHYCOM_NAMES)
        r = binding_p(P); rows.append(dict(distance_m=d, vs=r['baseline'], crc=r['crc'], margin=r['margin'], lo=r['lo'], hi=r['hi'],
                                           p=r['p_iut'], verdict=verdict(r['lo'], r['hi']), kind='binding_with_plugins',
                                           p_binding_pair=r['p_binding_pair']))
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED
    df.round(4).to_csv(os.path.join(OUT, 'phycom_margins.csv'), index=False); return df

# ------------------------------------------------------------------ 5 QCD-OCC validation grid
def valid6():
    z = ld('r6_valid6.npz'); rows = []
    for k in sorted([k for k in z.files if k.endswith('|err')]):
        lux, bn = k.split('|')[:2]; b, lo, hi = cluster_ber(z[k], B=B_R6, seed=BSEED)
        rows.append(dict(distance_cm=200, lux=int(lux), brightness=bn, symbols=z[k].shape[0], ber=b, ber_lo=lo, ber_hi=hi, published=0.0113,
                         ci_contains_published=bool(lo <= 0.0113 <= hi)))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'qcd_validation_grid.csv'), index=False); return df

if __name__ == '__main__':
    for g in sys.argv[1:]: print(globals()[g]().to_string())
