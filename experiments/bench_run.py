"""Evaluate registered schemes (built-ins + schemes_contrib plugins) at one condition on the physical channel.
  .venv/bin/python -m experiments.bench_run --schemes "EXAMPLE OOK-rep2" "HNCSM v2" --distance 2.0 --frames 100 [--oracle]
Power is equalised over the schemes listed plus the paper line-up reference budget (--pref, default P33 = 33.011)."""
import argparse, numpy as np, config
from occbench import create, available
from experiments.common import power_scales
from experiments.phys_eval import eval_point_phys
from experiments.stats import sym_goodput
from channel import physical as ph

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('--schemes', nargs='*'); a.add_argument('--distance', type=float, default=2.0)
    a.add_argument('--t_exp', type=float); a.add_argument('--frames', type=int, default=100); a.add_argument('--pref', type=float, default=33.011)
    a.add_argument('--oracle', action='store_true'); a.add_argument('--list', action='store_true'); o = a.parse_args()
    if o.list: print('\n'.join(available())); raise SystemExit
    sch = [create(n) for n in (o.schemes or available())]; sc = power_scales(sch, o.pref, 'equal', False)[0]
    c = dict(distance_m=o.distance, yaw_deg=0.0, blur_sigma_px=0.0, lux=27.0, jitter=0.02, genie_corners=o.oracle)
    if o.t_exp: c['t_exp'] = o.t_exp
    rec = {}; eval_point_phys(sch, sc, c, o.frames, config.cond_seed('bench', 0), dict(ph.P), rec=rec)
    for s in sch:
        g = sym_goodput(rec[s.name]['err'], s.layers, ph.P['f_tx']); print(f'{s.name:40s} goodput {g.mean():8.1f} bps  BER {rec[s.name]["err"].mean():.4f}')
