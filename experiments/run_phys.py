"""Sweeps on the PHYSICAL channel (channel/physical.py + experiments/phys_eval.py). Same protocol as run.py:
equal average power (budget --pref in summed-drive units), CRN across schemes, CRC-8 per layer, Wilson 95% CIs, fixed
seeds, adaptive-CSK genie (OOK / CSK802-4 / CSK802-8) chosen on separate seeds; goodput = net bits x f_tx x (1 - FER).
Usage: python -m experiments.run_phys --pref 33.011 --tag _PHYS_P33 [--lowlight] [--sweeps distance_m,...]"""
import argparse, os, time, json, datetime, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from tx.schemes import all_schemes_phys, tuned_params
from experiments.common import power_scales, rows_from
from experiments.phys_eval import eval_point_phys
from experiments.run import git_hash, RES
from channel import physical as ph

DEFAULT = dict(distance_m=1.0, yaw_deg=0.0, blur_sigma_px=0.0, lux=27.0, jitter=0.02)
SWEEPS = {
    'distance_m': (list(np.round(np.arange(0.5, 5.01, 0.25), 2)), {}),
    'blur_sigma_px': ([0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6], {}),          # extra Gaussian blur on top of defocus+Airy
    'yaw_deg': ([0, 10, 20, 30, 40, 50, 60, 70, 75, 80], {}),
    'lux': ([0, 27, 149, 304, 1000, 5000, 20000], dict(distance_m=2.0)),     # 27/149/304 lux = QCD-OCC Table 2
    't_exp': ([1 / 8000, 1 / 4000, 1 / 2000, 1 / 1500, 1 / 1000, 1 / 500, 1 / 250], dict(distance_m=2.0)),
}
GENIE_SET = ['OOK-8x8', 'CSK802-4', 'CSK802-8']; GENIE_FRAMES = 300; CHUNK = 125
LOWLIGHT_BRIGHTNESS = 1 / 1024     # ASSUMED low-light preset: 8x dimmer LED than the default 1/128

def params(lowlight):
    p = dict(ph.P)
    if lowlight: p['brightness'] = LOWLIGHT_BRIGHTNESS
    return p

def job(a):
    sw, i, v, c0, n, seed, pref, cap, lowlight, genie = a
    cond = dict(DEFAULT); cond.update(SWEEPS[sw][1]); cond[sw] = float(v)
    sch = all_schemes_phys(); sc, P, _ = power_scales(sch, pref, 'equal', cap)
    if genie: sch = [s for s in sch if s.name in GENIE_SET]; seed = config.GENIE_SEED + seed - config.SEED
    pt_seed = config.cond_seed(sw, i, seed)
    # frames c0..c0+n of this point: per-frame seeds are cond_seed(..., f, pt_seed) so chunking does not change results
    res, st = eval_point_phys(sch, sc, cond, n, pt_seed, params(lowlight), f0=c0)
    return (sw, i, genie), res, st

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', type=int, default=1000); ap.add_argument('--seed', type=int, default=config.SEED)
    ap.add_argument('--sweeps', default=','.join(SWEEPS)); ap.add_argument('--tag', default='_PHYS')
    ap.add_argument('--pref', type=float, default=None); ap.add_argument('--cap', action='store_true')
    ap.add_argument('--lowlight', action='store_true')
    a = ap.parse_args(); tp = tuned_params(); pref = a.pref if a.pref is not None else tp.get('pref_power')
    sws = a.sweeps.split(','); jobs = []
    for sw in sws:
        for i, v in enumerate(SWEEPS[sw][0]):
            for c0 in range(0, a.frames, CHUNK): jobs.append((sw, i, v, c0, min(CHUNK, a.frames - c0), a.seed, pref, a.cap, a.lowlight, False))
            for c0 in range(0, GENIE_FRAMES, CHUNK): jobs.append((sw, i, v, c0, min(CHUNK, GENIE_FRAMES - c0), a.seed, pref, a.cap, a.lowlight, True))
    t = time.time()
    with Pool(os.cpu_count()) as p: out = p.map(job, jobs, chunksize=1)
    agg, stats = {}, {}
    for key, res, st in out:
        A = agg.setdefault(key, {k: {l: [0, 0] for l in v} for k, v in res.items()})
        for k, v in res.items():
            for l, (be, fe) in v.items(): A[k][l][0] += be; A[k][l][1] += fe
        S = stats.setdefault(key, {k: dict(lost=0, frames_per_symbol=0) for k in st})
        for k, v in st.items():
            for kk in v: S[k][kk] += v[kk]
    sch = all_schemes_phys(); sc, P, _ = power_scales(sch, pref, 'equal', a.cap); power = {k: P[k] * sc[k] for k in P}
    rate = ph.P['f_tx']; rows = []
    for sw in sws:
        for i, v in enumerate(SWEEPS[sw][0]):
            extra = dict(sweep=sw, value=float(v)); res = agg[(sw, i, False)]; r = []
            for s in sch:
                rr = rows_from(res, [s], a.frames, power[s.name], extra, rate)
                for x in rr: x.update(lost_symbols=stats[(sw, i, False)][s.name]['lost'], frames_per_symbol=stats[(sw, i, False)][s.name]['frames_per_symbol'] / a.frames)
                r += rr
            g = [s for s in sch if s.name in GENIE_SET]
            gr = [x for x in rows_from(agg[(sw, i, True)], g, GENIE_FRAMES, 1.0, extra, rate) if x['layer'] == 'TOTAL']
            pick = max(gr, key=lambda x: x['goodput_bps'])['scheme']
            gen = dict([x for x in r if x['scheme'] == pick and x['layer'] == 'TOTAL'][0]); gen.update(scheme='Adaptive-CSK genie', layer=f'TOTAL({pick})')
            rows += r + [gen]
    df = pd.DataFrame(rows); os.makedirs(RES, exist_ok=True)
    for sw in sws: df[df.sweep == sw].to_csv(os.path.join(RES, f'sweep_{sw}{a.tag}.csv'), index=False)
    meta = dict(channel='physical', lowlight=a.lowlight, brightness=params(a.lowlight)['brightness'], cap=a.cap, seed=a.seed,
                frames=a.frames, genie_frames=GENIE_FRAMES, genie_seed_base=config.GENIE_SEED, power_mode='equal', pref_power=pref,
                f_tx=rate, defaults=DEFAULT, git=git_hash(), sweeps=sws, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                elapsed_s=round(time.time() - t))
    json.dump(meta, open(os.path.join(RES, f'run_meta{a.tag}.json'), 'w'), indent=1); print(json.dumps(meta))

if __name__ == '__main__':
    main()
