"""Runtime: wall-clock per symbol per scheme and per channel/receiver stage (single process), with hardware info.
Instruments experiments.phys_eval by wrapping the stage functions (timing only; outputs unchanged).
  .venv/bin/python -m experiments.bench_runtime [frames]   -> results/benchmark/runtime.csv, runtime_hw.json"""
import os, sys, time, json, platform, subprocess, numpy as np, pandas as pd, config
from collections import defaultdict
import experiments.phys_eval as pe
from channel import physical as ph, presets_phys as pp
from experiments.review_r1 import lineup_r1
from experiments.common import power_scales
OUT = os.path.join(os.path.dirname(__file__), '..', 'results', 'benchmark')
T = defaultdict(float)

def wrap(mod, name, label):
    f = getattr(mod, name)
    def g(*a, **k):
        t = time.perf_counter(); r = f(*a, **k); T[label] += time.perf_counter() - t; return r
    setattr(mod, name, g)

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    wrap(pe.ph, 'render_mean_e', 'render (optics, PSF, CFA x QE)'); wrap(pe.ph, 'row_weights', 'rolling-shutter weights')
    wrap(pe.ph, 'capture', 'capture (noise, ADC)'); wrap(pe, 'find_corners', 'corner finder'); wrap(pe, 'rectify_and_sample', 'rectify + sample')
    wrap(pe, 'residual', 'frame-selection residual')
    rows = []; sch = lineup_r1(); sc = power_scales(sch, 33.011, 'equal', False)[0]
    for sensor, p, d in (('IMX174', dict(ph.P), 2.0), ('IMX219 (imx219f)', dict(pp.imx219(1 / 128), finder='scalefree', finder_k=pp.FINDER_K), 2.0)):
        for s in sch:
            T.clear(); dec = 0.0; f0 = s.decode
            def timed(*a, f0=f0):
                global dec
                t = time.perf_counter(); r = f0(*a); dec += time.perf_counter() - t; return r
            s.decode = timed
            t = time.perf_counter(); pe.eval_point_phys([s], {s.name: sc[s.name]}, dict(distance_m=d, yaw_deg=0.0, blur_sigma_px=0.0, lux=27.0, jitter=0.02), n, config.cond_seed('runtime', 0), p)
            tot = time.perf_counter() - t; s.decode = f0
            r = dict(sensor=sensor, distance_m=d, scheme=s.name, symbols=n, total_ms_per_symbol=1e3 * tot / n, **{f'{k} ms': 1e3 * v / n for k, v in T.items()}, **{'decode ms': 1e3 * dec / n})
            r['other ms'] = r['total_ms_per_symbol'] - sum(v for k, v in r.items() if k.endswith(' ms')); rows.append(r); print(sensor, s.name, round(r['total_ms_per_symbol'], 1), flush=True)
    df = pd.DataFrame(rows).round(2); os.makedirs(OUT, exist_ok=True); df.to_csv(os.path.join(OUT, 'runtime.csv'), index=False)
    cpu = next((l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')), platform.processor())
    hw = dict(cpu=cpu, logical_cpus=os.cpu_count(), mem_gb=round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2**30, 1), python=platform.python_version(),
              numpy=np.__version__, platform=platform.platform(), loadavg_at_end=os.getloadavg(), process='single process; numpy default threads',
              note='load average shows concurrent jobs, if any; timings are wall-clock')
    json.dump(hw, open(os.path.join(OUT, 'runtime_hw.json'), 'w'), indent=1); print(df.groupby('sensor').total_ms_per_symbol.describe())
