import os, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
RES = os.path.join(os.path.dirname(__file__), '..', 'results')
S = ['HNCSM v2-CS', 'HNCSM v2', 'HNCSM', 'QCD-style-inspired (Vasantha22)', 'Overlay-inspired (Nishimoto12)', 'CSK-8', 'OOK-8x8', 'Adaptive-CSK genie']
d = pd.read_csv(os.path.join(RES, 'sweep_exposure_ms_LL_P33.csv')); t = d[d.layer.str.startswith('TOTAL')]
plt.rcParams.update({'font.size': 10})
fig, ax = plt.subplots(figsize=(5.5, 4))
for s in S:
    g = t[t.scheme == s].sort_values('value')
    l, = ax.plot(g.value, g.goodput_bps, '--' if 'genie' in s else '-', marker='o', ms=3, lw=2.2 if s.startswith('HNCSM v2') else 1.3, label=s.replace(' (Vasantha22)', '').replace(' (Nishimoto12)', ''))
    ax.fill_between(g.value, g.goodput_lo, g.goodput_hi, color=l.get_color(), alpha=.18, lw=0)
ax.set(xscale='log', xlabel='Exposure time (ms)', ylabel='Net goodput (bps)', title='Low light, d = 2.0 m, P = 33 (capped)'); ax.grid(alpha=.3, which='both'); ax.legend(fontsize=7, frameon=False)
fig.tight_layout()
for e in ('png', 'pdf'): fig.savefig(os.path.join(RES, f'lowlight_fig_exposure_sweep.{e}'), dpi=300)
print('ok')
