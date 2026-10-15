"""Power-budget efficiency, graceful-degradation metrics and energy per bit from results/sweep_distance_m_P*.csv.
Writes results/efficiency_*.csv, results/degradation_metrics.csv, results/energy_per_bit.csv and figures."""
import os, glob, re, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
RES = os.path.join(os.path.dirname(__file__), '..', 'results')
MAIN = ['HNCSM v2-CS', 'HNCSM v2', 'HNCSM', 'QCD-style-inspired (Vasantha22)', 'Overlay-inspired (Nishimoto12)',
        'CSK-8', 'OOK-8x8', 'Adaptive-CSK genie']
SHORT = {'HNCSM v2-CS': 'HNCSM v2-CS', 'HNCSM v2': 'HNCSM v2', 'HNCSM': 'HNCSM v1', 'HNCSM base-only': 'HNCSM v1 base-only',
         'QCD-style-inspired (Vasantha22)': 'QCD-inspired', 'Overlay-inspired (Nishimoto12)': 'Overlay-inspired',
         'NestedTexture-inspired (Salvi22)': 'Nested-inspired', 'QR/Aztec-style': 'QR/Aztec-style', 'CSK-8': 'CSK-8',
         'CSK-4': 'CSK-4', 'OOK-8x8': 'OOK 8x8', 'Adaptive-CSK genie': 'Adaptive-CSK genie'}
COL = dict(zip(MAIN, ['#d62728', '#ff7f0e', '#bcbd22', '#1f77b4', '#2ca02c', '#9467bd', '#8c564b', '#7f7f7f']))
plt.rcParams.update({'font.size': 10, 'axes.titlesize': 11, 'axes.labelsize': 10, 'legend.fontsize': 8, 'font.family': 'DejaVu Sans'})

def load():
    out = []
    for f in sorted(glob.glob(os.path.join(RES, 'sweep_distance_m_P*.csv'))):
        P = float(re.search(r'_P(\d+)', f).group(1)); d = pd.read_csv(f); d = d[d.layer.str.startswith('TOTAL')].copy()
        d['budget'] = P; out.append(d)
    t = pd.concat(out); t['eff'] = t.goodput_bps / t.budget; t['eff_lo'] = t.goodput_lo / t.budget; t['eff_hi'] = t.goodput_hi / t.budget
    return t

def crossing(x, y, frac, peak, ipk):
    thr = frac * peak
    for i in range(ipk, len(x) - 1):
        if y[i] >= thr > y[i + 1]:
            return x[i] + (y[i] - thr) / (y[i] - y[i + 1]) * (x[i + 1] - x[i])
    return np.nan if y[-1] < thr else np.inf   # inf = never falls below within 5 m

def degradation(x, y):
    ipk = int(np.argmax(y)); pk = y[ipk]
    if pk <= 0: return {}
    auc = np.trapezoid(y, x); drops = np.r_[np.diff(y) * -1, 0]
    total_decline = pk - y[-1]; mx = drops[ipk:].max()
    d90, d50, d10 = (crossing(x, y, f, pk, ipk) for f in (0.9, 0.5, 0.1))
    return dict(peak_bps=pk, auc_bps_m=auc, auc_norm=auc / (pk * (x[-1] - x[0])), d90_m=d90, d50_m=d50, d10_m=d10,
                transition_width_m=d10 - d90, max_step_drop_bps=mx, max_step_drop_frac=mx / pk,
                cliff_ratio=mx / total_decline if total_decline > 0 else np.nan)

def main():
    t = load(); t.to_csv(os.path.join(RES, 'efficiency_all_budgets.csv'), index=False)
    budgets = sorted(t.budget.unique())
    # (1) most-efficient band per budget (genie excluded from winners; reported separately)
    wrows = []
    for P in budgets:
        for v, g in t[(t.budget == P) & (t.scheme != 'Adaptive-CSK genie')].groupby('value'):
            g = g.sort_values('eff', ascending=False); w, r = g.iloc[0], g.iloc[1]
            if w.eff <= 0: continue
            wrows.append(dict(budget=P, distance_m=v, winner=SHORT[w.scheme], eff=w.eff, eff_lo=w.eff_lo, eff_hi=w.eff_hi,
                              runner_up=SHORT[r.scheme], ru_eff=r.eff, ru_lo=r.eff_lo, ru_hi=r.eff_hi,
                              separated=bool(w.eff_lo > r.eff_hi)))
    W = pd.DataFrame(wrows); W.to_csv(os.path.join(RES, 'efficiency_winners.csv'), index=False)
    # (2) degradation metrics, with envelope bounds from the CI curves
    drows = []
    for (P, s), g in t.groupby(['budget', 'scheme']):
        g = g.sort_values('value'); x = g.value.values
        m = degradation(x, g.goodput_bps.values); lo = degradation(x, g.goodput_lo.values); hi = degradation(x, g.goodput_hi.values)
        if not m: continue
        row = dict(budget=P, scheme=SHORT[s], **m)
        for k in ('auc_bps_m', 'd50_m', 'd10_m'): row[k + '_lo'] = lo.get(k, np.nan); row[k + '_hi'] = hi.get(k, np.nan)
        row['eff_auc_per_unit_power'] = m['auc_bps_m'] / P
        drows.append(row)
    D = pd.DataFrame(drows); D.to_csv(os.path.join(RES, 'degradation_metrics.csv'), index=False)
    # energy per delivered bit (power-units * s / bit) = budget / goodput
    e = t.copy(); e['energy_per_bit'] = np.where(e.goodput_bps > 0, e.budget / e.goodput_bps, np.inf)
    e['energy_per_bit_lo'] = np.where(e.goodput_hi > 0, e.budget / e.goodput_hi, np.inf)
    e['energy_per_bit_hi'] = np.where(e.goodput_lo > 0, e.budget / e.goodput_lo, np.inf)
    e[['budget', 'value', 'scheme', 'goodput_bps', 'energy_per_bit', 'energy_per_bit_lo', 'energy_per_bit_hi']].to_csv(os.path.join(RES, 'energy_per_bit.csv'), index=False)

    # (3) figures
    fig, axs = plt.subplots(1, len(budgets), figsize=(4.2 * len(budgets), 3.8), sharey=True)
    for ax, P in zip(np.atleast_1d(axs), budgets):
        for s in MAIN:
            g = t[(t.budget == P) & (t.scheme == s)].sort_values('value')
            ax.plot(g.value, g.eff, '--' if 'genie' in s else '-', color=COL[s], lw=2.2 if s.startswith('HNCSM v2') else 1.3, label=SHORT[s])
            ax.fill_between(g.value, g.eff_lo, g.eff_hi, color=COL[s], alpha=0.18, lw=0)
        ax.set(title=f'Average power budget P = {P:g}', xlabel='Distance (m)', xlim=(0.5, 5)); ax.grid(alpha=.3)
    np.atleast_1d(axs)[0].set_ylabel('Goodput per unit power (bps / unit)')
    np.atleast_1d(axs)[0].legend(loc='upper right', frameon=False)
    fig.tight_layout()
    for ext in ('png', 'pdf'): fig.savefig(os.path.join(RES, f'fig_efficiency_vs_distance.{ext}'), dpi=300)
    plt.close(fig)
    P0 = 33.0 if 33.0 in budgets else budgets[len(budgets) // 2]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for s in MAIN:
        g = t[(t.budget == P0) & (t.scheme == s)].sort_values('value'); pk = g.goodput_bps.max()
        if pk <= 0: continue
        ax[0].plot(g.value, g.goodput_bps / pk, '--' if 'genie' in s else '-', color=COL[s], lw=2.2 if s.startswith('HNCSM v2') else 1.3, label=SHORT[s])
        ax[0].fill_between(g.value, g.goodput_lo / pk, g.goodput_hi / pk, color=COL[s], alpha=0.15, lw=0)
        eg = e[(e.budget == P0) & (e.scheme == s)].sort_values('value'); ok = np.isfinite(eg.energy_per_bit)
        ax[1].semilogy(eg.value[ok], eg.energy_per_bit[ok], '--' if 'genie' in s else '-', marker='o', ms=2.5, color=COL[s], lw=2.2 if s.startswith('HNCSM v2') else 1.3, label=SHORT[s])
    ax[0].axhline(0.5, color='k', lw=.6, ls=':'); ax[0].axhline(0.1, color='k', lw=.6, ls=':')
    ax[0].set(xlabel='Distance (m)', ylabel='Goodput / peak goodput', title=f'Graceful degradation (P = {P0:g})', xlim=(0.5, 5), ylim=(0, 1.05))
    ax[1].set(xlabel='Distance (m)', ylabel='Energy per delivered bit (power-unit·s / bit)', title=f'Energy per bit (P = {P0:g})', xlim=(0.5, 5))
    for a in ax: a.grid(alpha=.3, which='both')
    ax[0].legend(frameon=False, loc='lower left')
    fig.tight_layout()
    for ext in ('png', 'pdf'): fig.savefig(os.path.join(RES, f'fig_degradation_energy_P{P0:g}.{ext}'), dpi=300)
    plt.close(fig)
    print('ok', budgets)

if __name__ == '__main__':
    main()
