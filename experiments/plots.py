import os, glob, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
RES = os.path.join(os.path.dirname(__file__), '..', 'results')
LBL = {'distance_m': 'Distance (m)', 'blur_sigma_px': 'Extra defocus blur sigma (px)', 'yaw_deg': 'Viewing angle / yaw (deg)', 'ambient': 'Ambient level (rel. to white LED)'}
for f in sorted(glob.glob(os.path.join(RES, 'sweep_*.csv'))):
    df = pd.read_csv(f); sw = df.sweep.iloc[0]
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.5))
    tot = df[df.layer.str.startswith('TOTAL')]
    for s, d in tot.groupby('scheme', sort=False):
        ls = '--' if 'genie' in s else '-'; lw = 3 if s.startswith('HNCSM v2') else (2.2 if s.startswith('HNCSM') else 1.3)
        ax[1].plot(d.value, d.goodput_bps, ls, marker='o', ms=3, lw=lw, label=s)
        if 'genie' not in s: ax[0].semilogy(d.value, d.ber.clip(lower=1e-5), marker='o', ms=3, lw=lw, label=s)
    for l, d in df[(df.scheme.isin(['HNCSM','HNCSM v2'])) & (df.layer.isin(['base', 'enh']))].groupby(['scheme','layer']):
        ax[0].semilogy(d.value, d.ber.clip(lower=1e-5), ':', lw=2, label=f'{l[0]} {l[1]} layer')
    for l, d in df[(df.scheme.str.startswith('Overlay')) & (df.layer.isin(['L1', 'L2']))].groupby('layer'):
        ax[0].semilogy(d.value, d.ber.clip(lower=1e-5), ':', lw=1, label=f'Overlay {l}')
    ax[0].set(xlabel=LBL[sw], ylabel='BER (floored at 1e-5)', title='BER'); ax[1].set(xlabel=LBL[sw], ylabel='Goodput (bps, 30 fps, frame-error based)', title='Throughput')
    for a in ax: a.grid(alpha=.3)
    ax[0].legend(fontsize=7); ax[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(RES, f'{sw}.png'), dpi=130); plt.close(fig)
    print('wrote', sw)
