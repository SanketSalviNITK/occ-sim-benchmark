"""benchmark-r7 analysis (analysis only; reads results/phys_sym/*.npz, writes results/benchmark/r7/*.csv|png|pdf).
Same bootstrap conventions as experiments.r6_report (paired CRN symbol bootstrap, B = 10000, seed 0, IUT p for bindings).
  lamb30 : lambert_m 0.65 / 1.56 at 30 deg yaw vs the lambert_m = 1 cells of r6_geoyaw30.npz (same y30 seeds)
  fact   : 36-cell factorial focus x f_mm x f_number x brightness at d3.0/d3.25 (r7_fact.npz), binding margin per cell,
           change vs the default cell (joint bootstrap), fraction of cells with C2 positive, main-effect table,
           default-cell identity check vs review_e2_P33.npz
  plugins: per-plugin goodput of the two PhyCom-inspired plugins per distance (r6_phycom.npz)
NOTE: r7_fact keys are '<cell>|d<d>|1/1500|1/128|<eval|tune>'; the literal '1/128' is a fixed key slot, the actual Tx
brightness of a cell is the 'brightness=' entry in <cell>.
Usage: python -m experiments.r7_report lamb30 fact plugins"""
import os, sys, numpy as np, pandas as pd
from experiments.r6_report import Gr, boot, pairs, binding_p, verdict, _delta, B_R6, BSEED
from experiments.bench_report import V2, ld, OUT as BOUT

OUT = os.path.join(BOUT, 'r7'); os.makedirs(OUT, exist_ok=True)

def lamb30():
    from experiments.revision_r7 import LAMB_M, LAMB_D
    zl, zg = ld('r7_lamb30.npz'), ld('r6_geoyaw30.npz'); rows = []
    for d in LAMB_D:
        cn = f'd{d}'; PD = pairs(zg, lambda t, s: f'{cn}|{t}|1/128|{s}'); bD = binding_p(PD)
        rows.append(dict(geometry='65 mm, yaw 30 deg', lambert_m='1 (default)', distance=cn, **bD, verdict=verdict(bD['lo'], bD['hi']), delta=0.0, d_lo=0.0, d_hi=0.0))
        for ln in LAMB_M:
            PX = pairs(zl, lambda t, s: f'lambert_m={ln}|{cn}|{t}|1/128|{s}'); bX = binding_p(PX); dl = _delta(PX, PD)
            rows.append(dict(geometry='65 mm, yaw 30 deg', lambert_m=ln, distance=cn, **bX, verdict=verdict(bX['lo'], bX['hi']), delta=dl[0], d_lo=dl[1], d_hi=dl[2]))
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED
    df.round(2).to_csv(os.path.join(OUT, 'lambert_yaw30.csv'), index=False); return df

def fact():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from experiments.revision_r7 import fact_cells, cell_key, FACT, FACT_D
    z, ze = ld('r7_fact.npz'), ld('review_e2_P33.npz'); rows = []; chk = []
    dflt = dict(focus_m='1.0', f_mm='6', f_number='2.0', brightness='1/128')
    for cn in FACT_D:
        PD = pairs(z, lambda t, s: f'{cell_key(dflt)}|{cn}|{t}|1/128|{s}')
        for k in [k for k in z.files if k.startswith(cell_key(dflt) + f'|{cn}|')]:
            kk = k[len(cell_key(dflt)) + 1:]
            if kk in ze: chk.append(dict(distance=cn, key=kk, identical=bool(np.array_equal(z[k], ze[kk]))))
        for c in fact_cells():
            P = pairs(z, lambda t, s, c=c: f'{cell_key(c)}|{cn}|{t}|1/128|{s}'); b = binding_p(P)
            dl = (0.0, 0.0, 0.0) if c == dflt else _delta(P, PD)
            rows.append(dict(**c, distance=cn, **b, verdict=verdict(b['lo'], b['hi']), delta_vs_default=dl[0], d_lo=dl[1], d_hi=dl[2],
                             v2_bps=Gr(z, f'{cell_key(c)}|{cn}|1/1500|1/128|eval', V2).mean(), is_default=(c == dflt)))
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED
    df.round(2).to_csv(os.path.join(OUT, 'factorial_binding.csv'), index=False)
    pd.DataFrame(chk).to_csv(os.path.join(OUT, 'factorial_default_identity.csv'), index=False)
    # summaries: fraction positive, and main effects (mean margin and fraction positive by level, per distance)
    s = []
    for cn, g in df.groupby('distance'):
        s.append(dict(scope='all cells', factor='-', level='-', distance=cn, cells=len(g), frac_positive=(g.verdict == 'positive').mean(),
                      frac_negative=(g.verdict == 'negative').mean(), mean_margin=g.margin.mean()))
        for f in FACT:
            for lv, h in g.groupby(f):
                s.append(dict(scope='main effect', factor=f, level=lv, distance=cn, cells=len(h), frac_positive=(h.verdict == 'positive').mean(),
                              frac_negative=(h.verdict == 'negative').mean(), mean_margin=h.margin.mean()))
    w = df.pivot_table(index=list(FACT), columns='distance', values='verdict', aggfunc='first')
    both = ((w['d3.0'] == 'positive') & (w['d3.25'] == 'positive'))
    s.append(dict(scope='both distances positive', factor='-', level='-', distance='d3.0&d3.25', cells=len(w), frac_positive=both.mean(), frac_negative=np.nan, mean_margin=np.nan))
    sm = pd.DataFrame(s); sm.round(3).to_csv(os.path.join(OUT, 'factorial_summary.csv'), index=False)
    # figure: heat-map of the binding margin per cell (rows focus x f_mm, cols f_number x brightness), one panel per distance
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
    for ax, cn in zip(axs, FACT_D):
        g = df[df.distance == cn]; R = [(fo, fm) for fo in FACT['focus_m'] for fm in FACT['f_mm']]; C = [(fn, br) for fn in FACT['f_number'] for br in FACT['brightness']]
        M = np.array([[g[(g.focus_m == r[0]) & (g.f_mm == r[1]) & (g.f_number == c[0]) & (g.brightness == c[1])].margin.iloc[0] for c in C] for r in R])
        V = [[g[(g.focus_m == r[0]) & (g.f_mm == r[1]) & (g.f_number == c[0]) & (g.brightness == c[1])].verdict.iloc[0] for c in C] for r in R]
        lim = np.nanmax(np.abs(np.clip(M, -400, 400))); im = ax.imshow(np.clip(M, -lim, lim), cmap='RdBu', vmin=-lim, vmax=lim, aspect='auto')
        for i in range(len(R)):
            for j in range(len(C)): ax.text(j, i, f'{M[i, j]:+.0f}' + ('' if V[i][j] == 'positive' else ('*' if V[i][j] == 'n.s.' else '')), ha='center', va='center', fontsize=7)
        ax.set_yticks(range(len(R))); ax.set_yticklabels([f'focus {a} m, f {b} mm' for a, b in R], fontsize=7)
        ax.set_xticks(range(len(C))); ax.set_xticklabels([f'f/{a}\n{b}' for a, b in C], fontsize=7); ax.set_title(f'{cn[1:]} m binding margin [bps]')
        fig.colorbar(im, ax=ax, fraction=0.04)
    fig.suptitle('C2 binding margin over the 36-cell optics x brightness factorial (IMX174, P33, 1/1500, claims/E2 seeds; * = n.s.)', fontsize=9)
    fig.tight_layout(); [fig.savefig(os.path.join(OUT, f'factorial_binding.{e}'), dpi=150) for e in ('png', 'pdf')]; plt.close(fig)
    return sm

def plugins():
    from experiments.revision_r6 import PHYCOM_NAMES, PHYCOM_D
    z = ld('r6_phycom.npz'); rows = []
    for d in PHYCOM_D:
        k = f'd{d}|1/1500|1/128|eval'
        for n in [V2] + PHYCOM_NAMES:
            m, lo, hi, _ = boot(Gr(z, k, n)); rows.append(dict(distance_m=d, scheme=n, goodput=m, lo=lo, hi=hi))
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED
    df.round(2).to_csv(os.path.join(OUT, 'phycom_plugin_goodput.csv'), index=False); return df

if __name__ == '__main__':
    for g in sys.argv[1:]: print(globals()[g]().to_string())
