"""Analysis of the round-1 audit runs (results/phys_sym/*.npz) -> results/audit_r1/*.csv + summary.md.
All goodput CIs: symbol bootstrap; all A-B: paired CRN bootstrap; BER: symbol-cluster bootstrap (experiments/stats.py)."""
import os, json, numpy as np, pandas as pd
from experiments.stats import cluster_ber, sym_goodput, boot_ci, paired_diff, paired_auc_diff, auc
from experiments.audit_r1 import lineup, LL_BR, LL_DIST, CLAIM_CONDS, T_EXPS
from experiments.run_phys import SWEEPS, GENIE_SET
from channel import physical as ph

RES = 'results'; SYM = os.path.join(RES, 'phys_sym'); OUT = os.path.join(RES, 'audit_r1'); os.makedirs(OUT, exist_ok=True)
SCH = {s.name: s for s in lineup()}; RATE = ph.P['f_tx']
HN = [n for n in SCH if n.startswith('HNCSM')]; BASEL = [n for n in SCH if n not in HN]
SHORT = {'HNCSM v2-CS': 'v2-CS', 'HNCSM v2': 'v2', 'HNCSM': 'v1', 'HNCSM base-only': 'v1-base', 'OOK-8x8': 'OOK',
         'QR/Aztec-style': 'QR', 'NestedTexture-inspired (Salvi22)': 'Nested', 'QCD-style-inspired (Vasantha22)': 'QCD-style',
         'Overlay-inspired (Nishimoto12)': 'Overlay', 'QCD-OCC (paper frame)': 'QCD-paper', 'CSK802-4': 'CSK802-4', 'CSK802-8': 'CSK802-8'}
md = []
def f0(x): return f'{x:.0f}'
def ci(m, lo, hi, f=f0): return f'{f(m)} [{f(lo)}, {f(hi)}]'

def G(z, pre, name, block=None):
    e = z[f'{pre}|{name}|err']; s = SCH[name]
    return sym_goodput(e, s.layers, RATE, block)

# ---------------- B3: electrons + validation ----------------
def electrons():
    rows = []
    for br in (1 / 64, 1 / 128, 1 / 256, 1 / 512, 1 / 1024, 1 / 2048):
        for bits in (8, 10, 12):
            p = dict(ph.P); p['brightness'] = br; p['bits'] = bits
            d = 1.0; pitch = p['panel_mm'] / p['n']; p_px = ph.f_px(p) * pitch * 1e-3 / d
            disc = np.pi * (ph.LED_FILL * p_px / 2) ** 2
            phot = ph.received_photons(d, 0, 0, p)                          # photons / LED channel / exposure (full drive)
            M = p['cfa'] * np.array(p['qe'])[None, :]
            e_led = phot * np.diag(M)                                       # own-channel photo-electrons per LED per exposure
            e_px = e_led / disc                                             # fully covered pixel, before blur
            K = ph.sensor_K(p)
            rows.append(dict(brightness=br, bits=bits, e_LED_R=e_led[0], e_LED_G=e_led[1], e_LED_B=e_led[2],
                             peak_e_px_R=e_px[0], peak_e_px_G=e_px[1], peak_e_px_B=e_px[2], sat_e=p['sat_e'],
                             clips=','.join(c for c, v in zip('RGB', e_px) if v >= p['sat_e']) or '-',
                             DN_R=min(e_px[0], p['sat_e']) * K, DN_G=min(e_px[1], p['sat_e']) * K, DN_B=min(e_px[2], p['sat_e']) * K,
                             e_per_DN=1 / K))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'electrons_per_channel.csv'), index=False); return df

def validation():
    z = np.load(os.path.join(SYM, 'valid.npz')); rows = []
    for br in (1 / 64, 1 / 128, 1 / 256):
        e = z[f'{br}|eval|QCD-OCC (paper frame)|err']; b, lo, hi = cluster_ber(e)
        rows.append(dict(brightness=br, symbols=len(e), bit_errors=int(e.sum()), errored_symbols=int((e.sum(1) > 0).sum()),
                         ber=b, ber_lo_cluster=lo, ber_hi_cluster=hi, published=1.13e-2))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'validation_bracket.csv'), index=False); return df

# ---------------- B1/B4: claims ----------------
PROP = {'d2.5': 'HNCSM v2', 'd3.0': 'HNCSM v2', 'yaw70': 'HNCSM v2', 'blur4': 'HNCSM'}
def claims():
    z = np.load(os.path.join(SYM, 'claims.npz')); rows = []; ctab = []; diag = []
    for br in ('1/128', '1/256'):
        for cn in CLAIM_CONDS:
            ev = {t: {n: G(z, f'{cn}|{t}|{br}|eval', n) for n in SCH} for t in T_EXPS}
            tu = {t: {n: G(z, f'{cn}|{t}|{br}|tune', n).mean() for n in SCH} for t in T_EXPS}
            for t in T_EXPS:
                for n in SCH:
                    pre = f'{cn}|{t}|{br}|eval'; m, lo, hi = boot_ci(ev[t][n]); b, blo, bhi = cluster_ber(z[f'{pre}|{n}|err'])
                    g48 = G(z, pre, n, 48).mean() if n in BASEL else np.nan
                    rows.append(dict(cond=cn, t_exp=t, brightness=br, scheme=n, goodput=m, lo=lo, hi=hi, ber=b, ber_lo=blo, ber_hi=bhi,
                                     goodput_crc48=g48, sat_ratio=np.nanmean(z[f'{pre}|{n}|sat']), rs_mix=np.nanmean(z[f'{pre}|{n}|mix'])))
            # variants: fixed 1/1500 (genie over schemes on tune seeds) and per-scheme tuned exposure (tune seeds)
            for var in ('fixed 1/1500', 'tuned t_exp'):
                if var == 'fixed 1/1500': pick = {n: '1/1500' for n in SCH}; gch = [(n, '1/1500') for n in GENIE_SET]
                else: pick = {n: max(T_EXPS, key=lambda t: tu[t][n]) for n in SCH}; gch = [(n, t) for n in GENIE_SET for t in T_EXPS]
                gn, gt = max(gch, key=lambda x: tu[x[1]][x[0]])
                val = {n: ev[pick[n]][n] for n in SCH}; val['genie'] = ev[gt][gn]
                for blk in (None, 48):
                    vb = dict(val)
                    if blk:   # baselines re-segmented into 48-bit CRC-8 blocks (NB2)
                        for n in BASEL: vb[n] = G(z, f'{cn}|{pick[n]}|{br}|eval', n, 48)
                        vb['genie'] = G(z, f'{cn}|{gt}|{br}|eval', gn, 48)
                    P = PROP[cn]; cands = BASEL + ['genie']; best = max(cands, key=lambda n: vb[n].mean())
                    for opp in sorted(set([best, 'CSK802-4', 'CSK802-8', 'OOK-8x8', 'QCD-style-inspired (Vasantha22)', 'genie'])):
                        d, lo, hi = paired_diff(vb[P], vb[opp])
                        ctab.append(dict(cond=cn, brightness=br, exposure=var, baseline_crc='48-bit blocks' if blk else 'native',
                                         proposed=SHORT[P], proposed_t=pick[P], proposed_bps=vb[P].mean(), prop_lo=boot_ci(vb[P])[1], prop_hi=boot_ci(vb[P])[2],
                                         opponent=('genie(' + SHORT[gn] + ')' if opp == 'genie' else SHORT[opp]), opp_t=(gt if opp == 'genie' else pick[opp]),
                                         is_best_baseline=opp == best, opp_bps=vb[opp].mean(), opp_lo=boot_ci(vb[opp])[1], opp_hi=boot_ci(vb[opp])[2],
                                         diff=d, diff_lo=lo, diff_hi=hi,
                                         verdict='proposed > opp' if lo > 0 else ('proposed < opp' if hi < 0 else 'not distinguishable')))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'claims_points.csv'), index=False)
    ct = pd.DataFrame(ctab); ct.to_csv(os.path.join(OUT, 'claims_paired.csv'), index=False); return pd.DataFrame(rows), ct

# ---------------- B5/C2: distance sweeps, winners + AUC ----------------
def sweeps():
    win, aucs = [], []
    x = SWEEPS['distance_m'][0]
    for P in ('25', '33', '42', '60'):
        if not os.path.exists(os.path.join(SYM, f'sweeps_PHYS_P{P}.npz')): continue
        z = np.load(os.path.join(SYM, f'sweeps_PHYS_P{P}.npz')); names = [n for n in SCH if n != 'QCD-OCC (paper frame)']
        V = {i: {n: G(z, f'distance_m|{i}|eval', n) for n in names} for i in range(len(x))}
        for i in range(len(x)):
            gg = {n: G(z, f'distance_m|{i}|genie', n).mean() for n in GENIE_SET}; gp = max(gg, key=gg.get); V[i]['genie'] = V[i][gp]
            order = sorted(V[i], key=lambda n: -V[i][n].mean()); w, r = order[0], order[1]
            if V[i][w].mean() == 0: continue
            d, lo, hi = paired_diff(V[i][w], V[i][r])
            win.append(dict(budget=P, distance_m=x[i], winner=SHORT.get(w, w), winner_bps=V[i][w].mean(), runner_up=SHORT.get(r, r) if r != 'genie' else f'genie({SHORT[gp]})',
                            runner_bps=V[i][r].mean(), diff=d, diff_lo=lo, diff_hi=hi, separated=bool(lo > 0 or hi < 0),
                            winner_bps_per_power=V[i][w].mean() / float(P)))
        for a in names + ['genie']:
            A = [V[i][a] for i in range(len(x))]
            for b in ['genie', 'HNCSM v2', 'CSK802-8']:
                if a == b: continue
                r = paired_auc_diff(np.array(x), A, [V[i][b] for i in range(len(x))])
                aucs.append(dict(budget=P, A=SHORT.get(a, a), B=SHORT.get(b, b), auc_A=r[0], auc_A_lo=r[5], auc_A_hi=r[6], auc_B=r[1], diff=r[2], diff_lo=r[3], diff_hi=r[4]))
    w = pd.DataFrame(win); w.to_csv(os.path.join(OUT, 'efficiency_winners_paired.csv'), index=False)
    a = pd.DataFrame(aucs); a.to_csv(os.path.join(OUT, 'auc_paired.csv'), index=False); return w, a

# ---------------- B2: low light grid ----------------
def lowlight(el):
    z = np.load(os.path.join(SYM, 'lowlight.npz')); rows = []; x = np.array(LL_DIST)
    for bn, br in LL_BR.items():
        for bits in (8, 10, 12):
            V = [{n: G(z, f'{bn}|{bits}|{d}|eval', n) for n in SCH} for d in LL_DIST]
            for i, d in enumerate(LL_DIST):
                tu = {n: G(z, f'{bn}|{bits}|{d}|tune', n).mean() for n in GENIE_SET}; V[i]['genie'] = V[i][max(tu, key=tu.get)]
            fixed = [n for n in BASEL]; aucB = {n: auc(x, [v[n].mean() for v in V]) for n in fixed}; bestfix = max(aucB, key=aucB.get)
            e = el[(el.brightness == br) & (el.bits == bits)].iloc[0]
            for opp in ('genie', bestfix):
                r = paired_auc_diff(x, [v['HNCSM'] for v in V], [v[opp] for v in V])
                rows.append(dict(brightness=bn, bits=bits, e_LED_R=e.e_LED_R, e_LED_G=e.e_LED_G, e_LED_B=e.e_LED_B, e_per_DN=e.e_per_DN,
                                 auc_v1=r[0], auc_v1_lo=r[5], auc_v1_hi=r[6], opponent='genie' if opp == 'genie' else SHORT[opp],
                                 auc_opp=r[1], diff=r[2], diff_lo=r[3], diff_hi=r[4],
                                 v1_wins=bool(r[3] > 0), v1_loses=bool(r[4] < 0),
                                 auc_all=json.dumps({SHORT[k]: round(v) for k, v in sorted(aucB.items(), key=lambda kv: -kv[1])})))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'lowlight_grid.csv'), index=False); return df

def trow_radiant():
    z = np.load(os.path.join(SYM, 'trow.npz')); rows = []
    for tr in (0.0, 10e-6, 27e-6):
        for d in (2.0, 2.5):
            for n in SCH:
                m, lo, hi = boot_ci(G(z, f'{tr}|{d}|eval', n)); rows.append(dict(t_row_us=tr * 1e6, distance_m=d, scheme=SHORT[n], goodput=m, lo=lo, hi=hi))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'trow.csv'), index=False); t = pd.DataFrame(rows)
    z = np.load(os.path.join(SYM, 'radiant.npz')); rows = []; xs = np.round(np.arange(0.5, 3.51, 0.5), 2)
    for d in xs:
        for n in SCH:
            m, lo, hi = boot_ci(G(z, f'{d}|eval', n)); rows.append(dict(distance_m=d, scheme=SHORT[n], goodput=m, lo=lo, hi=hi))
    r = pd.DataFrame(rows); r.to_csv(os.path.join(OUT, 'radiant_equal.csv'), index=False)
    return t, r

if __name__ == '__main__':
    import sys
    parts = sys.argv[1:] or ['el', 'val', 'claims', 'll', 'sw', 'tr']
    el = electrons(); print(el.to_string())
    if 'val' in parts: print(validation().to_string())
    if 'claims' in parts: print(claims()[1].to_string())
    if 'll' in parts: print(lowlight(el).drop(columns='auc_all').to_string())
    if 'sw' in parts: w, a = sweeps(); print(w.to_string()); print(a.to_string())
    if 'tr' in parts: t, r = trow_radiant(); print(t.pivot_table(index='scheme', columns=['t_row_us', 'distance_m'], values='goodput').round(0).to_string()); print(r.pivot_table(index='scheme', columns='distance_m', values='goodput').round(0).to_string())
