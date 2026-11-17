"""benchmark-r10 analysis (reads results/phys_sym/*.npz and results/r10/sym/*.npz; writes results/r10/*.csv|pdf|png).
Bootstrap conventions = experiments.r6_report: paired CRN symbol bootstrap, B = 10000, bootstrap seed 0, binding margin =
min over comparisons x {native, 48-bit CRC} with that pair's CI, IUT p = max per-comparison p. Comparison set = the
paper's 11-entry line-up (bench_report.COMP minus 'QCD-OCC (paper frame)', which is not a benchmark entry) + the
adaptive-CSK genie where a tune split exists. Every r10 interval is UNADJUSTED (outside the 56-claim Holm family).
Sections:
  rmax     : native and 48-bit R_max of every entry from the code (sym_goodput of an error-free symbol, f_tx 15/s)
  pxled    : pixels per LED, thin-lens blur diameter and code PSF sigma per distance, IMX174 / IMX219 presets (+ focus 3 m)
  radiant  : summary of the radiant-equal rerun (results/phys_sym/radiant.npz), B = 10000
  fig1     : C2 binding margins (P25/P33/P42, claims/E2 + sweep seeds) at B = 10000 -> fig1_binding_margins_B10000.*
  fig6     : IMX219 binding margins at B = 10000 -> fig6_imx219_B10000.*
  fig2     : readable 36-cell factorial heatmap (results/benchmark/r7/factorial_binding.csv) -> fig2_factorial_heatmap.*
  allentry : 11-entry goodput vs distance, shared finder and oracle corners, finder error rates -> all_entry_*.csv, fig
  c2       : C2 cell under the r10 options (PWM 432 Hz / 2 kHz, integer codes, PWM+codes, focus 3 m)
  sweeps   : all-entry goodput-vs-distance under the r10 options, paired against the DC benchmark-r9 sweep
Usage: python -m experiments.r10_report rmax pxled radiant fig1 fig6 fig2 allentry c2 sweeps"""
import os, sys, json, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from experiments.r6_report import Gr, boot, pairs, binding_p, verdict, _delta, B_R6, BSEED
from experiments.bench_report import SCH, V2, BO, VARS, COMP, ld, rmax as _rmax, DIST, PREFS, E2_D
from experiments.stats import sym_goodput
from experiments.revision_r10 import ENTRIES, C2_GROUPS, SW_GROUPS, OUT, SYM
from channel import physical as ph

QO = 'QCD-OCC (paper frame)'; COMP_P = [n for n in COMP if n != QO]
SHORT = {'HNCSM v2-CS': 'v2-CS', 'HNCSM v2': 'v2', 'HNCSM': 'HNCSM v1', 'HNCSM base-only': 'v1 base-only', 'CSK802-8': 'CSK802-8',
         'CSK802-4': 'CSK802-4', 'OOK-8x8': 'OOK-8x8', 'QR/Aztec-style': 'QR/Aztec-style', 'NestedTexture-inspired (Salvi22)': 'NestedTexture-insp.',
         'QCD-style-inspired (Vasantha22)': 'QCD-style-insp.', 'Overlay-inspired (Nishimoto12)': 'Overlay-insp.', QO: 'QCD-OCC (paper frame)', BO: 'v2-base-only'}
os.makedirs(OUT, exist_ok=True)
lr = lambda f: np.load(os.path.join(SYM, f)) if os.path.exists(os.path.join(SYM, f)) else None
def save(df, name, nd=2): df.round(nd).to_csv(os.path.join(OUT, name), index=False); return df
def savefig(fig, stem): [fig.savefig(os.path.join(OUT, f'{stem}.{e}'), dpi=200, bbox_inches='tight') for e in ('pdf', 'png')]; plt.close(fig)

class OrcView:
    """Read-only view mapping '<key>|<scheme>|err' -> the oracle-corner array '<key>|<scheme>|err_orc' of a dual run."""
    def __init__(self, z): self.z = z
    def __contains__(self, k): return k.endswith('|err') and (k + '_orc') in self.z
    def __getitem__(self, k): return self.z[k + '_orc']

def bind(z, pre, tuned=False, names=COMP_P):
    P = pairs(z, pre, tuned, names=names); return P, binding_p(P)

# ---------------------------------------------------------------------------------------------------------- rmax
def rmax():
    rows = []
    for n in ENTRIES + [BO, QO]:
        s = SCH[n]; e = np.zeros((1, s.nbits))
        rows.append(dict(entry=n, in_benchmark=n in ENTRIES, bits_per_symbol=s.nbits, layers=' + '.join(f'{l}:{m}' for l, m in s.layers),
                         crc_bits_per_unit=8, f_tx_sym_per_s=ph.P['f_tx'], camera_fps=ph.P['fps'],
                         R_max_native_bps=sym_goodput(e, s.layers, ph.P['f_tx'])[0], R_max_48bit_bps=sym_goodput(e, s.layers, ph.P['f_tx'], 48)[0]))
    return save(pd.DataFrame(rows), 'rmax_table.csv', 1)

# ---------------------------------------------------------------------------------------------------------- pxled
def pxled():
    from channel import presets_phys as pp
    rows = []
    for preset, p in (('IMX174 (default, focus 1.0 m)', dict(ph.P)), ('IMX174, focus 3.0 m', dict(ph.P, focus_m=3.0)), ('IMX219 (imx219f geometry, focus 2.0 m)', pp.imx219())):
        f = p['f_mm'] * 1e-3; N = p['f_number']; pix = p['pixel_um'] * 1e-6; df = p['focus_m']; pitch = p['panel_mm'] / p['n'] * 1e-3
        for d in DIST:
            c = f * f * abs(d - df) / (N * d * (df - f)); ppl = ph.f_px(p) * pitch / d; sg = ph.psf_sigma_px(d, p)
            rows.append(dict(preset=preset, distance_m=d, f_px=ph.f_px(p), led_pitch_mm=pitch * 1e3, px_per_led=ppl, led_disc_px=0.6 * ppl,
                             blur_diam_px=c / pix, blur_diam_over_pitch=c / pix / ppl, psf_sigma_px_G=sg[1], psf_sigma_over_pitch_G=sg[1] / ppl,
                             psf_sigma_px_R=sg[0], psf_sigma_px_B=sg[2]))
    return save(pd.DataFrame(rows), 'px_per_led_blur.csv', 4)

# ---------------------------------------------------------------------------------------------------------- radiant
def radiant():
    z = ld('radiant.npz'); rows = []
    for d in np.round(np.arange(0.5, 3.51, 0.5), 2):
        k = f'{d}|eval'; g = {n: Gr(z, k, n) for n in ENTRIES if Gr(z, k, n) is not None}
        rk = sorted(g, key=lambda n: -g[n].mean()); best = [n for n in rk if n != V2][0]
        for n in rk:
            m, lo, hi, _ = boot(g[n]); rows.append(dict(distance_m=d, scheme=n, goodput=m, lo=lo, hi=hi, rank=1 + rk.index(n), symbols=len(g[n])))
        m, lo, hi, p = boot(g[V2] - g[best])
        rows.append(dict(distance_m=d, scheme=f'v2 - best other ({SHORT[best]})', goodput=m, lo=lo, hi=hi, rank=np.nan, symbols=len(g[V2])))
    df = pd.DataFrame(rows); df['B'] = B_R6; df['note'] = 'radiant-equal budget (audit_r1.scales_for radiant, pref 33.011), seeds cond_seed(str(d)), 500 symbols, 1/1500, 1/128'
    save(df, 'radiant_equal_long.csv')
    w = df[~df.scheme.str.startswith('v2 -')].pivot(index='scheme', columns='distance_m', values='goodput').loc[ENTRIES].rename(index=SHORT)
    w.columns = [f'{c} m' for c in w.columns]; w.reset_index().round(1).to_csv(os.path.join(OUT, 'radiant_equal_table.csv'), index=False)
    return w

# ---------------------------------------------------------------------------------------------------------- fig1
def fig1():
    old = pd.read_csv('results/benchmark/c2_binding_margins.csv'); rows = []
    for b in PREFS:
        z = ld(f'review_e2_P{b}.npz'); zs = ld(f'sweeps_PHYS_P{b}.npz')
        for cn in E2_D:
            for lab, zz, pre in (('claims/E2', z, lambda t, s, cn=cn: f'{cn}|{t}|1/128|{s}'),
                                 ('sweep (run_phys)', zs, lambda t, s, i=DIST.index(E2_D[cn]): f'distance_m|{i}|{s}')):
                _, r = bind(zz, pre); _, ra = bind(zz, pre, names=COMP)
                o = old[(old.seeds == lab) & (old.budget == int(b)) & (old.distance == cn)].iloc[0]
                rows.append(dict(seeds=lab, budget=int(b), distance=cn, binding_baseline=r['baseline'], crc=r['crc'], margin=r['margin'], lo=r['lo'], hi=r['hi'],
                                 p_iut=r['p_iut'], verdict=verdict(r['lo'], r['hi']), same_binding_incl_QCDOCC=(ra['baseline'] == r['baseline'] and ra['crc'] == r['crc']),
                                 B2000_baseline=o.binding_baseline, B2000_margin=o.margin, B2000_lo=o.lo, B2000_hi=o.hi))
    d = pd.DataFrame(rows); d['B'] = B_R6; d['boot_seed'] = BSEED; save(d, 'fig1_binding_margins_B10000.csv')
    fig, ax = plt.subplots(figsize=(3.5, 2.6)); dist = list(E2_D); off = {'claims/E2': -0.12, 'sweep (run_phys)': 0.12}; cols = {25: 'C0', 33: 'C1', 42: 'C2'}
    for i, (P, g) in enumerate(d.groupby('budget')):
        for s, gg in g.groupby('seeds'):
            x = np.array([dist.index(v) for v in gg.distance]) + (i - 1) * 0.25 + off[s] * 0.8
            ax.errorbar(x, gg.margin, yerr=[gg.margin - gg.lo, gg.hi - gg.margin], fmt='o' if s.startswith('claims') else 's', ms=3, color=cols[P], capsize=2,
                        label=f'P{P}, ' + ('claims/E2 (canonical)' if s.startswith('claims') else 'sweep'))
    ax.axhline(0, color='k', lw=.6); ax.set_xticks(range(3)); ax.set_xticklabels(['3.0 m', '3.25 m', '3.5 m'])
    ax.set_ylabel('binding margin (bps), 95% CI, B=10 000'); ax.set_ylim(-20, 245); ax.legend(fontsize=5.5, ncol=2, loc='upper right'); fig.tight_layout()
    savefig(fig, 'fig1_binding_margins_B10000'); return d

# ---------------------------------------------------------------------------------------------------------- fig6
def fig6():
    rows = []; ref = pd.read_csv('/workspace/occ_benchmark_paper/derived/imx219_binding_B10000.csv') if os.path.exists('/workspace/occ_benchmark_paper/derived/imx219_binding_B10000.csv') else None
    for corners, f in (('real finder', 'review_e3claims@imx219f.npz'), ('oracle corners', 'review_or_e3claims@imx219f.npz')):
        z = ld(f)
        for cn in ('d2.5', 'd3.0', 'd3.25', 'd3.5', 'm2.5', 'm3.0', 'm3.25', 'm3.5'):
            for tu in (False, True):
                _, r = bind(z, lambda t, s, cn=cn: f'{cn}|{t}|{s}', tu)
                row = dict(corners=corners, cond=cn, exposure='tuned' if tu else 'fixed 1/1500', baseline=r['baseline'], crc=r['crc'], margin=r['margin'], lo=r['lo'], hi=r['hi'],
                           p_iut=r['p_iut'], verdict=verdict(r['lo'], r['hi']))
                if ref is not None:
                    q = ref[(ref.corners == ('real finder' if corners == 'real finder' else 'genie corners')) & (ref.cond == cn) & (ref.exposure == ('tuned' if tu else 'fixed'))]
                    if len(q): row.update(derived_B10000_margin=q.margin.iloc[0], derived_lo=q.lo.iloc[0], derived_hi=q.hi.iloc[0])
                rows.append(row)
    e = pd.DataFrame(rows); e['B'] = B_R6; e['boot_seed'] = BSEED; save(e, 'fig6_imx219_B10000.csv')
    order = ['d2.5', 'd3.0', 'd3.25', 'd3.5', 'm2.5', 'm3.0', 'm3.25', 'm3.5']
    fig, ax = plt.subplots(figsize=(7.0, 2.4)); k = 0
    for corners, mk in (('real finder', 'o'), ('oracle corners', 's')):
        for ex in ('fixed 1/1500', 'tuned'):
            g = e[(e.corners == corners) & (e.exposure == ex)].set_index('cond').loc[order]
            x = np.arange(8) + (k - 1.5) * 0.15; ax.errorbar(x, g.margin, yerr=[g.margin - g.lo, g.hi - g.margin], fmt=mk, ms=3, capsize=2, label=f'{"oracle" if "oracle" in corners else "finder"}, {ex}'); k += 1
    ax.axhline(0, color='k', lw=.6); ax.set_xticks(range(8)); ax.set_xticklabels(order); ax.set_ylabel('v2 − binding baseline (bps)\n95% CI, B=10 000')
    ax.set_xlabel('d = same distance, m = matched pixels-per-LED'); ax.legend(fontsize=6, ncol=4); fig.tight_layout(); savefig(fig, 'fig6_imx219_B10000'); return e

# ---------------------------------------------------------------------------------------------------------- fig2
def fig2():
    f = pd.read_csv('results/benchmark/r7/factorial_binding.csv')
    R = [(a, b) for a in (0.5, 1.0, 2.0) for b in (4, 6, 8)]; C = [(a, b) for a in (2.0, 2.8) for b in ('1/128', '1/256')]
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True)
    for ax, cn in zip(axs, ('d3.0', 'd3.25')):
        g = f[f.distance == cn]; M = np.full((len(R), len(C)), np.nan); V = [[''] * len(C) for _ in R]
        for i, r in enumerate(R):
            for j, c in enumerate(C):
                q = g[np.isclose(g.focus_m, r[0]) & (g.f_mm == r[1]) & np.isclose(g.f_number, c[0]) & (g.brightness == c[1])].iloc[0]; M[i, j] = q.margin; V[i][j] = q.verdict
        lim = 400; im = ax.imshow(np.clip(M, -lim, lim), cmap='RdBu', vmin=-lim, vmax=lim, aspect='auto')
        for i in range(len(R)):
            for j in range(len(C)):
                ax.text(j, i, f'{M[i, j]:+.0f}' + ('' if V[i][j] != 'n.s.' else '\n(n.s.)'), ha='center', va='center', fontsize=6.5, color='k' if abs(M[i, j]) < 250 else 'w')
                if R[i] == (1.0, 6) and C[j] == (2.0, '1/128'): ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, ec='k', lw=2))
        ax.set_xticks(range(len(C))); ax.set_xticklabels([f'f/{a:g}\n{b}' for a, b in C], fontsize=7); ax.set_title(f'{cn[1:]} m', fontsize=8)
        ax.set_yticks(range(len(R))); ax.set_yticklabels([f'focus {a:g} m, f = {b} mm' for a, b in R], fontsize=7)
        for y in (2.5, 5.5): ax.axhline(y, color='w', lw=1.5)
        ax.axvline(1.5, color='w', lw=1.5)
    cb = fig.colorbar(im, ax=axs, fraction=0.03, pad=0.02); cb.set_label('binding margin (bps), clipped at ±400', fontsize=7)
    savefig(fig, 'fig2_factorial_heatmap')
    s = f.groupby('distance').agg(cells=('margin', 'size'), positive=('verdict', lambda v: (v == 'positive').sum()), negative=('verdict', lambda v: (v == 'negative').sum()),
                                  ns=('verdict', lambda v: (v == 'n.s.').sum())).reset_index()
    return save(s, 'fig2_factorial_counts.csv')

# ---------------------------------------------------------------------------------------------------------- allentry (DC, existing data)
def _finder_rows(z, key, n):
    nc, nf, ng = z[f'{key}|{n}|ncand'], z[f'{key}|{n}|nfail'], z[f'{key}|{n}|ngross']
    return dict(det_fail_frame=nf.sum() / nc.sum(), gross_frame=ng.sum() / nc.sum(), any_bad_frame=(nf + ng).sum() / nc.sum(), sym_all_frames_failed=float((nf == nc).mean()))

def allentry():
    zs, zo, zf = ld('sweeps_PHYS_P33.npz'), ld('review_or_sweep.npz'), ld('r6_finder.npz'); zd = lr('r10_swdc.npz'); rows = []
    for i, d in enumerate(DIST):
        k = f'distance_m|{i}|eval'
        for n in ENTRIES:
            r = dict(distance_m=d, scheme=n, R_max=_rmax(n)); m, lo, hi, _ = boot(Gr(zs, k, n)); r.update(detector_bps=m, det_lo=lo, det_hi=hi, det_source='phys_sym/sweeps_PHYS_P33.npz')
            if zd is not None and f'{k}|{n}|err_orc' in zd:
                assert np.array_equal(zd[f'{k}|{n}|err'], zs[f'{k}|{n}|err']), (k, n)
                go = sym_goodput(zd[f'{k}|{n}|err_orc'], SCH[n].layers, 15.0); m, lo, hi, _ = boot(go); dl = boot(go - Gr(zs, k, n))
                r.update(oracle_bps=m, orc_lo=lo, orc_hi=hi, finder_loss=dl[0], fl_lo=dl[1], fl_hi=dl[2], orc_source='r10/sym/r10_swdc.npz (dual rerun, detector arrays identical to sweeps_PHYS_P33)', **_finder_rows(zd, k, n))
            elif zo is not None and f'{k}|{n}|err' in zo:
                go = Gr(zo, k, n); m, lo, hi, _ = boot(go); dl = boot(go - Gr(zs, k, n))
                r.update(oracle_bps=m, orc_lo=lo, orc_hi=hi, finder_loss=dl[0], fl_lo=dl[1], fl_hi=dl[2], orc_source='phys_sym/review_or_sweep.npz')
            rows.append(r)
    df = pd.DataFrame(rows); df['B'] = B_R6; save(df, 'all_entry_distance_long.csv')
    # finder error rates on the claims/E2 seeds (r6_finder, dual receiver), used when the r10 DC dual sweep is absent
    fr = []
    for d in (2.0, 2.5, 3.0, 3.25, 3.5, 4.0):
        k = f'd{d}|1/1500|1/128|eval'
        for n in ENTRIES: fr.append(dict(distance_m=d, scheme=n, **_finder_rows(zf, k, n), source='phys_sym/r6_finder.npz (claims/E2 seeds)'))
    save(pd.DataFrame(fr), 'all_entry_finder_rates_claims_seeds.csv', 4)
    # wide tables for the paper
    sel = [1.0, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5, 4.0, 5.0]
    for col, name in (('detector_bps', 'all_entry_table_detector.csv'), ('oracle_bps', 'all_entry_table_oracle.csv'), ('any_bad_frame', 'all_entry_table_finder_bad_frame.csv')):
        if col not in df: continue
        w = df[df.distance_m.isin(sel)].pivot(index='scheme', columns='distance_m', values=col).loc[ENTRIES]
        w.insert(0, 'R_max', [_rmax(n) for n in ENTRIES]) if col != 'any_bad_frame' else None
        w = w.rename(index=SHORT); w.columns = [c if isinstance(c, str) else f'{c} m' for c in w.columns]
        w.reset_index().round(3 if col == 'any_bad_frame' else 1).to_csv(os.path.join(OUT, name), index=False)
    _allentry_fig(df, fr if 'any_bad_frame' not in df else None, 'fig_all_entry_distance', 'IMX174, P33, 1/1500 s, brightness 1/128 (benchmark-r9 DC model)')
    return df

def _allentry_fig(df, fr, stem, title):
    sty = dict(zip(ENTRIES, [('C0', 'o'), ('C1', 's'), ('C2', '^'), ('C3', 'v'), ('C4', 'D'), ('C5', 'x'), ('C6', '*'), ('C7', 'P'), ('C8', 'h'), ('C9', '<'), ('k', '>')]))
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.7))
    for n in ENTRIES:
        g = df[df.scheme == n].sort_values('distance_m'); c, m = sty[n]
        axs[0].plot(g.distance_m, g.detector_bps, color=c, marker=m, ms=2.5, lw=.8, label=SHORT[n])
        if 'oracle_bps' in g: h = g.dropna(subset=['oracle_bps']); axs[1].plot(h.distance_m, h.oracle_bps, color=c, marker=m, ms=2.5, lw=.8)
        if fr is not None:
            f = pd.DataFrame(fr); f = f[f.scheme == n]; axs[2].plot(f.distance_m, f.any_bad_frame, color=c, marker=m, ms=2.5, lw=.8)
        elif 'any_bad_frame' in g: h = g.dropna(subset=['any_bad_frame']); axs[2].plot(h.distance_m, h.any_bad_frame, color=c, marker=m, ms=2.5, lw=.8)
    for a, t in zip(axs, ('shared corner finder', 'oracle (true) corners', 'finder failure or gross error')): a.set_title(t, fontsize=7.5); a.set_xlabel('distance (m)', fontsize=7); a.grid(alpha=.3); a.tick_params(labelsize=6.5)
    axs[0].set_ylabel('goodput (bps)', fontsize=7); axs[1].set_ylabel('goodput (bps)', fontsize=7); axs[2].set_ylabel('share of candidate frames', fontsize=7)
    axs[0].set_yscale('symlog', linthresh=10); axs[1].set_yscale('symlog', linthresh=10)
    fig.legend(*axs[0].get_legend_handles_labels(), loc='lower center', ncol=6, fontsize=6, bbox_to_anchor=(0.5, -0.1)); fig.suptitle(title, fontsize=7.5)
    fig.tight_layout(); savefig(fig, stem)

# ---------------------------------------------------------------------------------------------------------- c2 under r10 options
C2_LAB = {'c2pwm432': 'PWM 432 Hz', 'c2pwm2k': 'PWM 2 kHz', 'c2quant': 'integer codes (DC)', 'c2pwm432q': 'PWM 432 Hz + integer codes', 'c2focus3': 'focus 3.0 m'}

def c2():
    ze = ld('review_e2_P33.npz'); zf = ld('r6_finder.npz'); rows, gp, fin = [], [], []
    for grp in C2_GROUPS:
        z = lr(f'r10_{grp}.npz')
        if z is None: print('missing', grp); continue
        for br in C2_GROUPS[grp]:
            for cn in ('d3.0', 'd3.25'):
                pre = lambda t, s: f'{cn}|{t}|{br}|{s}'; k = pre('1/1500', 'eval')
                for rx, zz in (('shared finder', z), ('oracle corners', OrcView(z))):
                    for tu in (False, True):
                        P, b = bind(zz, pre, tu); _, ba = bind(zz, pre, tu, names=COMP)
                        # DC (benchmark-r9) control on the same CRN symbols
                        if rx == 'shared finder': z0 = ze
                        else: z0 = OrcView(zf) if (not tu and br == '1/128') else None
                        if z0 is not None and f'{pre("1/1500", "eval")}|{V2}|err' in z0:
                            P0, b0 = bind(z0, pre, tu); dl = _delta(P, P0)
                        else: b0, dl = None, (np.nan, np.nan, np.nan)
                        pk = (lambda n: __import__('experiments.bench_report', fromlist=['pick_tuned']).pick_tuned(zz, pre, n)) if tu else (lambda n: '1/1500')
                        g = {n: Gr(zz, pre(pk(n), 'eval'), n).mean() for n in ENTRIES}; rk = sorted(g, key=lambda n: -g[n])
                        rows.append(dict(option=C2_LAB[grp], group=grp, brightness=br, distance=cn, receiver=rx, exposure='tuned' if tu else 'fixed 1/1500',
                                         binding_baseline=b['baseline'], crc=b['crc'], margin=b['margin'], lo=b['lo'], hi=b['hi'], p_iut=b['p_iut'], verdict=verdict(b['lo'], b['hi']),
                                         binding_incl_QCDOCC_same=(ba['baseline'], ba['crc']) == (b['baseline'], b['crc']),
                                         dc_r9_margin=(b0['margin'] if b0 else np.nan), dc_r9_lo=(b0['lo'] if b0 else np.nan), dc_r9_hi=(b0['hi'] if b0 else np.nan),
                                         dc_r9_baseline=(b0['baseline'] if b0 else ''), delta_vs_dc=dl[0], d_lo=dl[1], d_hi=dl[2],
                                         v2_bps=g[V2], v2_rank=1 + rk.index(V2), best_entry=rk[0], ranking=' > '.join(f'{SHORT[n]} {g[n]:.0f}' for n in rk),
                                         dc_source=('phys_sym/review_e2_P33.npz' if rx == 'shared finder' else ('phys_sym/r6_finder.npz (err_orc)' if b0 else 'n/a'))))
                # per-scheme fixed-exposure goodput, both receivers, vs DC
                for n in ENTRIES:
                    gd = Gr(z, k, n); go = Gr(OrcView(z), k, n); m, lo, hi, _ = boot(gd); mo, olo, ohi, _ = boot(go)
                    r = dict(option=C2_LAB[grp], brightness=br, distance=cn, scheme=n, detector_bps=m, det_lo=lo, det_hi=hi, oracle_bps=mo, orc_lo=olo, orc_hi=ohi, **_finder_rows(z, k, n))
                    g0 = Gr(ze, k, n)
                    if g0 is not None: dm, dlo, dhi, _ = boot(gd - g0); r.update(dc_detector_bps=g0.mean(), det_delta_vs_dc=dm, dd_lo=dlo, dd_hi=dhi)
                    if br == '1/128' and f'{k}|{n}|err_orc' in zf:
                        o0 = Gr(OrcView(zf), k, n); dm, dlo, dhi, _ = boot(go - o0); r.update(dc_oracle_bps=o0.mean(), orc_delta_vs_dc=dm, od_lo=dlo, od_hi=dhi, **{f'dc_{a}': b for a, b in _finder_rows(zf, k, n).items()})
                    gp.append(r)
                # PWM bookkeeping: duty / code statistics of the drives at this brightness
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED; df['holm'] = 'unadjusted (outside the 56-claim family)'
    save(df.drop(columns=['ranking']), 'c2_r10_binding.csv'); df[['option', 'brightness', 'distance', 'receiver', 'exposure', 'ranking']].to_csv(os.path.join(OUT, 'c2_r10_rankings.csv'), index=False)
    save(pd.DataFrame(gp), 'c2_r10_goodput.csv', 4)
    return df.drop(columns=['ranking'])

def codes():
    """Integer WS2812B codes each entry actually latches at the C2 power budget (P33), per brightness."""
    from experiments.common import power_scales
    from experiments.review_r1 import lineup_r1
    sch = [s for s in lineup_r1() if s.name in ENTRIES]; sc = power_scales(sch, 33.011, 'equal', False)[0]; rng = np.random.RandomState(0); rows = []
    for s in sch:
        D = np.concatenate([(s.encode(list(rng.randint(0, 2, s.nbits))) * sc[s.name]).ravel() for _ in range(200)])
        for br in (1 / 128, 1 / 256):
            p = dict(ph.P, brightness=br); c = 255 * br * D; q = ph.ws_codes(D, p); lit = D > 0
            rows.append(dict(scheme=s.name, brightness=f'1/{round(1 / br)}', scale=sc[s.name], max_drive=D.max(), max_code_continuous=c.max(),
                             distinct_nonzero_levels_continuous=len(np.unique(np.round(c[lit], 6))), distinct_codes_after_rounding=len(np.unique(q[lit])),
                             share_lit_channels_rounded_to_0=float((q[lit] == 0).mean()), codes_used=' '.join(str(int(x)) for x in np.unique(q)),
                             duty_max=c.max() / 255, on_time_us_432Hz_at_max=c.max() / 255 / 432 * 1e6, on_time_us_2kHz_at_max=c.max() / 255 / 2000 * 1e6))
    return save(pd.DataFrame(rows), 'ws2812b_codes_at_P33.csv', 4)

def sweeps():
    zs, zo = ld('sweeps_PHYS_P33.npz'), ld('review_or_sweep.npz'); zd = lr('r10_swdc.npz'); rows, br = [], []
    lab = {'swpwm432': 'PWM 432 Hz', 'swpwm2k': 'PWM 2 kHz', 'swfocus3': 'focus 3.0 m'}
    for grp in [g for g in SW_GROUPS if g != 'swdc']:
        z = lr(f'r10_{grp}.npz')
        if z is None: print('missing', grp); continue
        for i, d in enumerate(DIST):
            k = f'distance_m|{i}|eval'
            for n in ENTRIES:
                gd, go = Gr(z, k, n), Gr(OrcView(z), k, n); m, lo, hi, _ = boot(gd); mo, olo, ohi, _ = boot(go); dl = boot(gd - Gr(zs, k, n))
                r = dict(option=lab[grp], distance_m=d, scheme=n, detector_bps=m, det_lo=lo, det_hi=hi, oracle_bps=mo, orc_lo=olo, orc_hi=ohi, **_finder_rows(z, k, n),
                         dc_detector_bps=Gr(zs, k, n).mean(), det_delta_vs_dc=dl[0], dd_lo=dl[1], dd_hi=dl[2])
                zo0 = zd if (zd is not None and f'{k}|{n}|err_orc' in zd) else (zo if (zo is not None and f'{k}|{n}|err' in zo) else None)
                if zo0 is not None:
                    o0 = Gr(OrcView(zd), k, n) if zo0 is zd else Gr(zo, k, n); x = boot(go - o0); r.update(dc_oracle_bps=o0.mean(), orc_delta_vs_dc=x[0], od_lo=x[1], od_hi=x[2])
                rows.append(r)
            for rx, zz, z0 in (('shared finder', z, zs), ('oracle corners', OrcView(z), (OrcView(zd) if zd is not None else (zo if f'{k}|{V2}|err' in zo else None)))):
                P, b = bind(zz, lambda t, s: f'distance_m|{i}|{s}')
                if z0 is not None and f'{k}|{V2}|err' in z0: P0, b0 = bind(z0, lambda t, s: f'distance_m|{i}|{s}'); dl = _delta(P, P0)
                else: b0, dl = None, (np.nan,) * 3
                br.append(dict(option=lab[grp], distance_m=d, receiver=rx, binding_baseline=b['baseline'], crc=b['crc'], margin=b['margin'], lo=b['lo'], hi=b['hi'], verdict=verdict(b['lo'], b['hi']),
                               dc_r9_margin=(b0['margin'] if b0 else np.nan), dc_r9_baseline=(b0['baseline'] if b0 else ''), delta_vs_dc=dl[0], d_lo=dl[1], d_hi=dl[2]))
        df = pd.DataFrame([r for r in rows if r['option'] == lab[grp]])
        _allentry_fig(df, None, f'fig_all_entry_distance_{grp}', f'IMX174, P33, 1/1500 s, 1/128, {lab[grp]} (benchmark-r10 option)')
    d = pd.DataFrame(rows); d['B'] = B_R6; save(d, 'sweeps_r10_long.csv', 4)
    b = pd.DataFrame(br); b['B'] = B_R6; b['holm'] = 'unadjusted'; save(b, 'sweeps_r10_v2_binding.csv')
    sel = [1.0, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5, 4.0, 5.0]
    for o in d.option.unique():
        for col in ('detector_bps', 'oracle_bps'):
            w = d[(d.option == o) & d.distance_m.isin(sel)].pivot(index='scheme', columns='distance_m', values=col).loc[ENTRIES].rename(index=SHORT)
            w.columns = [f'{c} m' for c in w.columns]; w.reset_index().round(1).to_csv(os.path.join(OUT, f'sweep_table_{o.replace(" ", "").replace(".", "p")}_{col.split("_")[0]}.csv'), index=False)
    return b

if __name__ == '__main__':
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
    for g in sys.argv[1:]: r = globals()[g](); print(g); print(r.to_string() if hasattr(r, 'to_string') else r)
