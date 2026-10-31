"""Figures for the physical channel (png + pdf): goodput vs each sweep with Wilson-CI bands, validation plot."""
import os, glob, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from experiments.efficiency import SHORT
RES = os.path.join(os.path.dirname(__file__), '..', 'results')
SCH = ['HNCSM v2-CS', 'HNCSM v2', 'HNCSM', 'QCD-style-inspired (Vasantha22)', 'Overlay-inspired (Nishimoto12)', 'CSK802-8',
       'CSK802-4', 'OOK-8x8', 'Adaptive-CSK genie']
COL = dict(zip(SCH, ['#d62728', '#ff7f0e', '#bcbd22', '#1f77b4', '#2ca02c', '#9467bd', '#e377c2', '#8c564b', '#7f7f7f']))
XL = dict(distance_m='Distance (m)', blur_sigma_px='Extra blur sigma (px)', yaw_deg='Yaw (deg)', lux='Ambient illuminance (lux)', t_exp='Exposure time (ms)')

def save(fig, name):
    for ext in ('png', 'pdf'): fig.savefig(os.path.join(RES, f'{name}.{ext}'), dpi=200)
    plt.close(fig)

def sweep_plot(f):
    d = pd.read_csv(f); d = d[d.layer.str.startswith('TOTAL')]; sw = d.sweep.iloc[0]
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for s in SCH:
        g = d[d.scheme == s].sort_values('value'); x = g.value * (1000 if sw == 't_exp' else 1)
        ax.plot(x, g.goodput_bps, '--' if 'genie' in s else '-', color=COL[s], lw=2 if s.startswith('HNCSM v2') else 1.2, label=SHORT.get(s, s), marker='o', ms=2)
        ax.fill_between(x, g.goodput_lo, g.goodput_hi, color=COL[s], alpha=.15, lw=0)
    if sw in ('lux', 't_exp'): ax.set_xscale('symlog' if sw == 'lux' else 'log', **({'linthresh': 10} if sw == 'lux' else {}))
    tag = os.path.basename(f)[len('sweep_') + len(sw):-4]
    ax.set(xlabel=XL[sw], ylabel='Net goodput (bps)', title=f'Physical channel{tag.replace("_", " ")}'); ax.grid(alpha=.3)
    ax.legend(fontsize=7, frameon=False); fig.tight_layout(); save(fig, f'phys_{sw}{tag}')

def validation_plot():
    v = pd.read_csv(os.path.join(RES, 'validation_qcd.csv'))
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    for br, mk in ((1 / 128, 'o'), (1.0, 's')):
        g = v[(v.brightness.round(6) == round(br, 6)) & (v.tx_fps == 25) & (v.lux == 27)].sort_values('distance_cm')
        ax[0].errorbar(g.distance_cm, g.ber.clip(lower=1e-5), yerr=[g.ber.clip(lower=1e-5) - g.ber_lo.clip(lower=1e-5), g.ber_hi - g.ber.clip(lower=1e-5)], marker=mk, capsize=3, label=f'sim, brightness {"1/128 (default)" if br < 1 else "1 (full)"}')
        h = v[(v.brightness.round(6) == round(br, 6)) & (v.distance_cm == 200) & (v.lux == 27)].sort_values('bitrate_bps')
        ax[1].errorbar(h.bitrate_bps, h.ber, yerr=[h.ber - h.ber_lo, h.ber_hi - h.ber], marker=mk, capsize=3, label=f'sim, brightness {"1/128" if br < 1 else "1"}')
    for a in ax: a.plot([200 if a is ax[0] else 3600], [1.13e-2], 'k*', ms=12, label='QCD-OCC measured (1.13e-2)'); a.set_yscale('log'); a.grid(alpha=.3, which='both'); a.legend(fontsize=7)
    ax[0].set(xlabel='Distance (cm)', ylabel='BER', title='QCD-OCC frame, 3600 bps, 27 lux (floor 1e-5 = 0 errors)')
    ax[1].set(xlabel='Bit rate (bps)', ylabel='BER', title='QCD-OCC frame, 200 cm, 27 lux')
    fig.tight_layout(); save(fig, 'phys_validation_qcd')

if __name__ == '__main__':
    for f in sorted(glob.glob(os.path.join(RES, 'sweep_*_PHYS*.csv'))): sweep_plot(f)
    validation_plot(); print('ok')
