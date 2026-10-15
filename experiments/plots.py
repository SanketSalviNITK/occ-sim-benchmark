import os, glob, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
RES = os.path.join(os.path.dirname(__file__), '..', 'results')
LBL = {'distance_m': 'Distance (m)', 'blur_sigma_px': 'Extra defocus blur sigma (px) @1 m',
       'yaw_deg': 'Viewing angle / yaw (deg) @1 m', 'ambient': 'Non-uniform ambient level @2.5 m (rel. to white LED)'}
for f in sorted(glob.glob(os.path.join(RES, 'sweep_*.csv'))):
    df = pd.read_csv(f); sw = df.sweep.iloc[0]; tag = os.path.basename(f)[6:-4]
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    tot = df[df.layer.str.startswith('TOTAL')]
    for s, d in tot.groupby('scheme', sort=False):
        ls = '--' if 'genie' in s else '-'; lw = 3 if s == 'HNCSM v2-CS' else (2 if s.startswith('HNCSM') else 1.2)
        l, = ax[1].plot(d.value, d.goodput_bps, ls, marker='o', ms=3, lw=lw, label=s)
        ax[1].fill_between(d.value, d.goodput_lo, d.goodput_hi, color=l.get_color(), alpha=0.15)
        if 'genie' not in s: ax[0].semilogy(d.value, d.ber.clip(lower=1e-6), marker='o', ms=3, lw=lw, label=s)
    for (s, l), d in df[df.scheme.isin(['HNCSM v2-CS']) & df.layer.isin(['base', 'enh'])].groupby(['scheme', 'layer']):
        ax[0].semilogy(d.value, d.ber.clip(lower=1e-6), ':', lw=2, label=f'{s} {l} layer')
    ax[0].set(xlabel=LBL[sw], ylabel='BER (floored at 1e-6)', title='BER')
    ax[1].set(xlabel=LBL[sw], ylabel='Net goodput (bps; 30 fps, CRC-8 per layer; Wilson 95% CI)', title='Throughput' + (' — peak-power' if 'peak' in tag else ' — equal average power'))
    for a in ax: a.grid(alpha=.3); a.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(RES, f'{tag}.png'), dpi=130); plt.close(fig); print('wrote', tag)
