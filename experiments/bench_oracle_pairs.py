"""benchmark-r5: oracle-corner paired margins v2 - X (both with genie/oracle corners), IMX174 P33, default 1/1500, 1/128,
run_phys seeds (results/phys_sym/review_or_sweep.npz; even sweep indices 2..14 = 1.0..4.0 m step 0.5; 3.25 m not run).
Paired CRN symbol bootstrap (experiments.stats.paired_diff, B=2000), native CRC and 48-bit blocks.
Also claims/E2 seeds (review_or_claims.npz, d2.5/d3.0 only; 3.25/3.5 m not run with oracle on these seeds).
Writes results/benchmark/oracle_pairs.csv (every pair) and results/benchmark/oracle_pairs_rank.csv (v2 oracle rank per distance).
Analysis only; no simulation."""
import os, pandas as pd
from experiments.bench_report import G, SCH, VARS, V2, DIST, OUT, ld, paired_diff

def main():
    zo = ld('review_or_sweep.npz'); rows, rk = [], []
    for i in range(2, 15, 2):
        k = f'distance_m|{i}|eval'; v = G(zo, k, V2)
        names = [n for n in SCH if n not in VARS and n != V2 and G(zo, k, n) is not None]
        for blk in (None, 48):
            for n in names:
                b = G(zo, k, n, blk); d = paired_diff(v, b)
                rows.append(dict(sensor='IMX174', budget='P33', corners='oracle', exposure='fixed 1/1500', brightness='1/128', seeds='sweep (run_phys)',
                                 distance_m=DIST[i], crc='48-bit' if blk else 'native', baseline=n, v2_bps=round(v.mean(), 1), baseline_bps=round(b.mean(), 1),
                                 diff=round(d[0], 1), lo=round(d[1], 1), hi=round(d[2], 1),
                                 verdict='v2 > X' if d[1] > 0 else ('v2 < X' if d[2] < 0 else 'n.s.')))
        means = {n: G(zo, k, n).mean() for n in names}
        rk.append(dict(seeds='sweep (run_phys)', distance_m=DIST[i], v2_oracle_bps=round(v.mean(), 1), v2_rank_native=1 + sum(m > v.mean() for m in means.values()),
                       best=max(means, key=means.get), best_bps=round(max(means.values()), 1)))
    zc = ld('review_or_claims.npz')   # claims/E2 seeds (audit_r1 'claims' = E2 d3.0 seeds), oracle, d2.5/d3.0
    for cn, dm in (('d2.5', 2.5), ('d3.0', 3.0)):
        k = f'{cn}|1/1500|1/128|eval'; v = G(zc, k, V2)
        if v is None: continue
        for blk in (None, 48):
            for n in [n for n in SCH if n not in VARS and n != V2 and G(zc, k, n) is not None]:
                b = G(zc, k, n, blk); d = paired_diff(v, b)
                rows.append(dict(sensor='IMX174', budget='P33', corners='oracle', exposure='fixed 1/1500', brightness='1/128', seeds='claims/E2',
                                 distance_m=dm, crc='48-bit' if blk else 'native', baseline=n, v2_bps=round(v.mean(), 1), baseline_bps=round(b.mean(), 1),
                                 diff=round(d[0], 1), lo=round(d[1], 1), hi=round(d[2], 1),
                                 verdict='v2 > X' if d[1] > 0 else ('v2 < X' if d[2] < 0 else 'n.s.')))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, 'oracle_pairs.csv'), index=False)
    pd.DataFrame(rk).to_csv(os.path.join(OUT, 'oracle_pairs_rank.csv'), index=False); return df

if __name__ == '__main__':
    d = main(); print(d[(d.distance_m.isin([3.0, 3.5])) & (d.crc == 'native')].to_string())
