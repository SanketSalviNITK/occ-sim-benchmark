"""Main sweeps. Equal average optical power (default) or peak-constrained (--power peak); CRN across schemes;
per-layer CRC-8 charge; Wilson 95% CIs; adaptive-CSK genie selected on separate seeds.
Usage: python -m experiments.run [--frames 1000] [--seed S] [--power equal|peak] [--sweeps distance_m,...] [--quick]"""
import argparse, os, time, json, subprocess, datetime, numpy as np, pandas as pd
from multiprocessing import Pool
import config
from tx.schemes import all_schemes, CSK, OOK, tuned_params
from experiments.common import power_scales, eval_point, rows_from

DEFAULT = dict(distance_m=1.0, yaw_deg=0.0, blur_sigma_px=0.0, ambient=0.03)
SWEEPS = {
    'distance_m': (list(np.round(np.arange(0.5, 5.01, 0.25), 2)), {}),
    'blur_sigma_px': ([0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6], {}),
    'yaw_deg': ([0, 10, 20, 30, 40, 50, 60, 70, 75, 80], {}),
    # M1: ambient at 2.5 m with non-uniform light (gradient + hotspot)
    'ambient': ([0.0, 0.03, 0.1, 0.2, 0.4, 0.6], dict(distance_m=2.5, ambient_nonuniform=True)),
}
RES = os.path.join(os.path.dirname(__file__), '..', 'results')
GENIE_SET = ['OOK-8x8', 'CSK-4', 'CSK-8']; GENIE_FRAMES = 300

def job(a):
    sw, i, v, frames, seed, mode, pref = a
    cond = dict(DEFAULT); cond.update(SWEEPS[sw][1]); cond[sw] = float(v)
    sch = all_schemes(); sc, P, _ = power_scales(sch, pref, mode)
    power = {k: P[k] * sc[k] for k in P}
    extra = dict(sweep=sw, value=float(v))
    res = eval_point(sch, sc, cond, frames, config.cond_seed(sw, i, seed))
    rows = sum((rows_from(res, [s], frames, power[s.name], extra) for s in sch), [])
    g = [s for s in sch if s.name in GENIE_SET]   # genie order selection on separate seeds
    gres = eval_point(g, sc, cond, GENIE_FRAMES, config.cond_seed(sw, i, config.GENIE_SEED + seed - config.SEED))
    gr = [r for r in rows_from(gres, g, GENIE_FRAMES, 1.0, extra) if r['layer'] == 'TOTAL']
    pick = max(gr, key=lambda r: r['goodput_bps'])['scheme']
    gen = dict([r for r in rows if r['scheme'] == pick and r['layer'] == 'TOTAL'][0]); gen.update(scheme='Adaptive-CSK genie', layer=f'TOTAL({pick})')
    return rows + [gen]

def git_hash():
    try: return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=os.path.dirname(RES), text=True).strip() + \
        ('-dirty' if subprocess.check_output(['git', 'status', '--porcelain'], cwd=os.path.dirname(RES), text=True).strip() else '')
    except Exception: return 'unknown'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', type=int, default=1000); ap.add_argument('--seed', type=int, default=config.SEED)
    ap.add_argument('--power', default='equal', choices=['equal', 'peak']); ap.add_argument('--quick', action='store_true')
    ap.add_argument('--sweeps', default=','.join(SWEEPS)); ap.add_argument('--tag', default=''); ap.add_argument('--pref', type=float, default=None, help='fixed average-power budget (overrides tuned pref); scales may exceed 1 (LED overdrive; sensor saturation is modelled)')
    a = ap.parse_args(); frames = 20 if a.quick else a.frames
    tp = tuned_params(); pref = (a.pref if a.pref is not None else tp.get('pref_power')) if a.power == 'equal' else None
    sws = a.sweeps.split(',')
    jobs = [(sw, i, v, frames, a.seed, a.power, pref) for sw in sws for i, v in enumerate(SWEEPS[sw][0])]
    t = time.time()
    with Pool(os.cpu_count()) as p: rows = sum(p.map(job, jobs), [])
    df = pd.DataFrame(rows); os.makedirs(RES, exist_ok=True); tag = a.tag or ('' if a.power == 'equal' else '_peak')
    for sw in sws: df[df.sweep == sw].to_csv(os.path.join(RES, f'sweep_{sw}{tag}.csv'), index=False)
    meta = dict(seed=a.seed, frames=frames, genie_frames=GENIE_FRAMES, genie_seed_base=config.GENIE_SEED, power_mode=a.power,
                pref_power=pref, tuned=tp, git=git_hash(), sweeps=sws, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                elapsed_s=round(time.time() - t))
    json.dump(meta, open(os.path.join(RES, f'run_meta{tag}.json'), 'w'), indent=1)
    print(json.dumps(meta))

if __name__ == '__main__':
    main()
