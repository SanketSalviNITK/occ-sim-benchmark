"""benchmark-r8 analysis (analysis only; reads results/phys_sym/*.npz, writes results/benchmark/r8/*.csv).
Same bootstrap conventions as experiments.r6_report (paired CRN symbol bootstrap, B = 10000, seed 0, IUT p for bindings).
  mult : C2 binding margin per sigma_mult x correlation x distance (r8_mult.npz; sigma = 0 = review_e2_P33.npz control),
         change vs sigma = 0 (joint bootstrap, same CRN symbols), per-scheme goodput and ranking, sigma = 0 byte-identity
         check, and finder diagnostics (r8_multfin.npz vs r6_finder.npz: gross-error / failure rates, detector vs oracle
         goodput, oracle-corner binding margin).
Usage: python -m experiments.r8_report mult"""
import os, sys, numpy as np, pandas as pd
from experiments.r6_report import Gr, boot, pairs, binding_p, verdict, _delta, B_R6, BSEED
from experiments.bench_report import V2, BO, SCH, VARS, COMP, ld, OUT as BOUT
from experiments.stats import sym_goodput

OUT = os.path.join(BOUT, 'r8'); os.makedirs(OUT, exist_ok=True)

def mult():
    from experiments.revision_r8 import MULT_D, MULT_S, MULT_C, mkey
    z, ze, zf, zm = ld('r8_mult.npz'), ld('review_e2_P33.npz'), ld('r6_finder.npz'), ld('r8_multfin.npz')
    names = [n for n in SCH if n not in VARS]
    cells = [('0', 'pixel')] + [(s, c) for s in MULT_S for c in MULT_C]
    rows, gp, chk, fin = [], [], [], []
    for cn in MULT_D:
        P0 = pairs(ze, lambda t, s: f'{cn}|{t}|1/128|{s}')
        pre0 = mkey('0', 'pixel') + '|'
        for k in [k for k in z.files if k.startswith(pre0 + cn + '|')]:
            chk.append(dict(distance=cn, key=k[len(pre0):], identical=bool(np.array_equal(z[k], ze[k[len(pre0):]]))))
        for s, c in cells:
            P = pairs(z, lambda t, ss, s=s, c=c: f'{mkey(s, c)}|{cn}|{t}|1/128|{ss}'); b = binding_p(P)
            dl = (0.0, 0.0, 0.0) if s == '0' else _delta(P, P0)
            k = f'{mkey(s, c)}|{cn}|1/1500|1/128|eval'; k0 = f'{cn}|1/1500|1/128|eval'
            g = {n: Gr(z, k, n) for n in names}; g0 = {n: Gr(ze, k0, n) for n in names}
            rk = sorted([n for n in names if n != BO], key=lambda n: -g[n].mean())
            rows.append(dict(sigma_mult=float(s), corr=('-' if s == '0' else c), distance=cn, **b, verdict=verdict(b['lo'], b['hi']),
                             delta_vs_sigma0=dl[0], d_lo=dl[1], d_hi=dl[2], v2_bps=g[V2].mean(), v2_rank_native=1 + rk.index(V2),
                             ranking_native=' > '.join(f'{n.split(" (")[0]} {g[n].mean():.0f}' for n in rk)))
            for n in names:
                m, lo, hi, _ = boot(g[n]); dm, dlo, dhi, _ = boot(g[n] - g0[n])
                gp.append(dict(sigma_mult=float(s), corr=('-' if s == '0' else c), distance=cn, scheme=n, goodput=m, lo=lo, hi=hi,
                               delta_vs_sigma0=dm, d_lo=dlo, d_hi=dhi))
            # finder diagnostics (dual receiver): sigma 0 from r6_finder (same seeds), sigma > 0 from r8_multfin
            zz, kf = (zf, k0) if s == '0' else (zm, k)
            if zz is None or f'{kf}|{V2}|ncand' not in zz: continue
            for n in names:
                nc, nf, ng = zz[f'{kf}|{n}|ncand'], zz[f'{kf}|{n}|nfail'], zz[f'{kf}|{n}|ngross']
                go = sym_goodput(zz[f'{kf}|{n}|err_orc'], SCH[n].layers, 15.0); gd = Gr(zz, kf, n)
                fin.append(dict(sigma_mult=float(s), corr=('-' if s == '0' else c), distance=cn, scheme=n, gross_frame=ng.sum() / nc.sum(),
                                det_fail_frame=nf.sum() / nc.sum(), detector_bps=gd.mean(), oracle_bps=go.mean(), finder_loss=go.mean() - gd.mean(),
                                std_vs_dual_err_identical=bool(np.array_equal(zz[f'{kf}|{n}|err'], z[f'{k}|{n}|err']))))
            vo = sym_goodput(zz[f'{kf}|{V2}|err_orc'], SCH[V2].layers, 15.0)
            PO = [(n, crc, vo - sym_goodput(zz[f'{kf}|{n}|err_orc'], SCH[n].layers, 15.0, blk)) for blk, crc in ((None, 'native'), (48, '48-bit')) for n in names if n not in (V2, BO)]
            bo = binding_p(PO); rows[-1].update(oracle_margin=bo['margin'], oracle_lo=bo['lo'], oracle_hi=bo['hi'], oracle_baseline=bo['baseline'], oracle_crc=bo['crc'])
    df = pd.DataFrame(rows); df['B'] = B_R6; df['boot_seed'] = BSEED
    _r2 = lambda d: d.round({c: 2 for c in d.columns if c != 'sigma_mult'})  # keep sigma 0.024 unrounded
    _r2(df).to_csv(os.path.join(OUT, 'mult_binding.csv'), index=False)
    g = pd.DataFrame(gp); g['B'] = B_R6; _r2(g).to_csv(os.path.join(OUT, 'mult_goodput.csv'), index=False)
    pd.DataFrame(chk).to_csv(os.path.join(OUT, 'mult_sigma0_identity.csv'), index=False)
    pd.DataFrame(fin).round(4).to_csv(os.path.join(OUT, 'mult_finder.csv'), index=False)
    return df.drop(columns=['ranking_native'])

if __name__ == '__main__':
    pd.set_option('display.width', 250)
    for g in sys.argv[1:]: print(globals()[g]().to_string())
