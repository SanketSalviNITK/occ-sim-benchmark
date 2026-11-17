"""benchmark-r10 revision experiments (additive; every new behaviour is OPT-IN, defaults reproduce benchmark-r9).
Re-uses the job function of experiments.revision_r6 (same chunking / checkpoint / CRN scheme) in 'dual' mode: every
candidate frame is decoded with the shared finder AND with oracle corners on the SAME captured image, and finder
failures / gross corner errors are recorded. Per-symbol arrays -> results/r10/sym/r10_<group>.npz, run metas ->
results/r10/run_meta_R10_<group>.json, chunks checkpointed in $CKPT/r10_<group>/.
C2 cell (all C2 groups): IMX174 preset, P33 (pref 33.011), 65 mm panel on axis, default optics unless stated, lux 27,
d in {3.0, 3.25} m, exposures T_EXPS = {1/4000, 1/1500, 1/500, 1/250} (1/1500 = C2 default; the others give the
per-scheme tuned exposure, chosen on the tune split), canonical claims/E2 seeds cond_seed('d<d>', 0, SEED) (eval 1000)
and cond_seed('d<d>', 0, TUNE_SEED) (tune 200) -> CRN-paired with results/phys_sym/review_e2_P33.npz (same payloads,
camera phase, noise draws). Full line-up (lineup_r1, 13 schemes incl. the two diagnostic extras).
Groups:
  c2pwm432  : WS2812B PWM 432 Hz (classic WS2812B, measured), brightness 1/128, DC drive levels (continuous codes)
  c2pwm2k   : WS2812B PWM 2000 Hz (WS2812C/D, WS2812B-V5), brightness 1/128
  c2quant   : integer 8-bit WS2812B codes (no PWM, DC), brightness 1/128 and 1/256
  c2pwm432q : PWM 432 Hz + integer codes, brightness 1/128 (the most hardware-like combination)
  c2focus3  : focus_m = 3.0 (other parameters default, DC, continuous codes), brightness 1/128
  swpwm432  : all 11 benchmark entries, run_phys distance grid 0.5..5.0 m step 0.25, run_phys seeds
              cond_seed('distance_m', i, SEED), eval 1000, default exposure 1/1500, brightness 1/128, PWM 432 Hz
              -> CRN-paired with results/phys_sym/sweeps_PHYS_P33.npz (detector) and review_or_sweep.npz (oracle)
  swpwm2k   : same, PWM 2000 Hz
  swfocus3  : same, focus_m = 3.0 (DC)
  swgs      : same, t_row = 0 (global shutter; the default 27.4 us rolling shutter switched off), std receiver
  c2radiant : RADIANT-equal budget (experiments.audit_r1.scales_for 'radiant', pref 33.011) at the C2 points 3.0 / 3.25 m,
              1/1500, 1/128, claims/E2 eval seeds (1000 symbols) -> CRN-paired with review_e2_P33.npz (equal summed drive)
  swdc      : same, no option (benchmark-r9 DC model): oracle corners and finder error rates on the 19 sweep points;
              its detector arrays must equal sweeps_PHYS_P33.npz (identity check in experiments.r10_report allentry)
Usage: OMP_NUM_THREADS=1 PROCS=8 python -m experiments.revision_r10 c2pwm432 c2pwm2k c2quant c2focus3 swpwm432 swfocus3"""
import os, sys, json, time, datetime, pickle, hashlib, numpy as np
from multiprocessing import Pool
import config
from experiments.review_r1 import code_key, DIST
from experiments.run import git_hash, RES
from experiments.revision_r6 import _ijob, CHUNK
from experiments.audit_r1 import T_EXPS

OUT = os.path.join(RES, 'r10'); SYM = os.path.join(OUT, 'sym')
C2_D = {'d3.0': 3.0, 'd3.25': 3.25}
ENTRIES = ['HNCSM v2-CS', 'HNCSM v2', 'HNCSM', 'HNCSM base-only', 'CSK802-8', 'CSK802-4', 'OOK-8x8', 'QR/Aztec-style',
           'NestedTexture-inspired (Salvi22)', 'QCD-style-inspired (Vasantha22)', 'Overlay-inspired (Nishimoto12)']   # = all_schemes_phys()
PWM_432, PWM_2K = 432.0, 2000.0     # Hz: cpldcpu WS2812Tester findings (WS2812B, measured); cpldcpu 2020 blog (WS2812C/D) / WS2812B-V5
C2_GROUPS = {
    'c2pwm432':  {'1/128': dict(brightness=1 / 128, pwm_hz=PWM_432)},
    'c2pwm2k':   {'1/128': dict(brightness=1 / 128, pwm_hz=PWM_2K)},
    'c2quant':   {'1/128': dict(brightness=1 / 128, ws_quant=True), '1/256': dict(brightness=1 / 256, ws_quant=True)},
    'c2pwm432q': {'1/128': dict(brightness=1 / 128, pwm_hz=PWM_432, ws_quant=True)},
    'c2focus3':  {'1/128': dict(brightness=1 / 128, focus_m=3.0)},
}
SW_GROUPS = {'swpwm432': dict(pwm_hz=PWM_432), 'swpwm2k': dict(pwm_hz=PWM_2K), 'swfocus3': dict(focus_m=3.0),
             'swdc': {}, 'swgs': dict(t_row=0.0)}   # swdc: benchmark-r9 DC model, dual receiver (oracle + finder rates on the sweep seeds; detector must equal sweeps_PHYS_P33)

def jobs_for(group):
    J = []   # (key, cond, pmod, pref, seed, n, only, mode)
    if group in C2_GROUPS:
        for bn, pm in C2_GROUPS[group].items():
            for cn, d in C2_D.items():
                for tn, t in T_EXPS.items():
                    k = f'{cn}|{tn}|{bn}'; c = dict(distance_m=d, t_exp=t)
                    J.append((k + '|eval', c, dict(pm), 33.011, config.cond_seed(cn, 0, config.SEED), 1000, None, 'dual'))
                    J.append((k + '|tune', c, dict(pm), 33.011, config.cond_seed(cn, 0, config.TUNE_SEED), 200, None, 'dual'))
    elif group in SW_GROUPS:
        for i, d in enumerate(DIST):
            J.append((f'distance_m|{i}|eval', dict(distance_m=float(d)), dict(SW_GROUPS[group]), 33.011,
                      config.cond_seed('distance_m', i, config.SEED), 1000, list(ENTRIES), 'std' if group == 'swgs' else 'dual'))
    elif group == 'c2radiant':
        for cn, d in C2_D.items():
            J.append((f'{cn}|1/1500|1/128|eval', dict(distance_m=d, t_exp=1 / 1500), dict(brightness=1 / 128), 33.011,
                      config.cond_seed(cn, 0, config.SEED), 1000, list(ENTRIES), 'radiant'))
    else: raise KeyError(group)
    return J

def _job10(a):
    key, cond, pm, pref, seed, c0, n, only, mode = a
    if mode == 'radiant':
        from experiments.audit_r1 import job as ajob
        return ajob((key, cond, pm, pref, 'radiant', False, seed, c0, n, only))
    from experiments.revision_r6 import job
    return job(a)

def _ij10(a): return a[0], _job10(a[1])

def run(group, procs):
    t = time.time(); J = jobs_for(group); work = []
    for key, cond, pm, pref, seed, N, only, mode in J:
        for c0 in range(0, N, CHUNK): work.append((key, cond, pm, pref, seed, c0, min(CHUNK, N - c0), only, mode))
    ck = os.path.join(os.environ.get('CKPT', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.ckpt')), 'r10_' + group); os.makedirs(ck, exist_ok=True)
    gh = os.environ.get('R6_CODE_KEY') or code_key()
    fn = lambda w: os.path.join(ck, hashlib.sha1((gh + repr(w)).encode()).hexdigest() + '.pkl')
    todo = [w for w in work if not os.path.exists(fn(w))]
    print(group, len(work), 'chunks,', len(work) - len(todo), 'already checkpointed', flush=True)
    with Pool(procs) as pl:
        for i, (j, r) in enumerate(pl.imap_unordered(_ij10, list(enumerate(todo)), chunksize=1)):
            w = todo[j]; pickle.dump(r, open(fn(w) + '.tmp', 'wb')); os.replace(fn(w) + '.tmp', fn(w))
            if i % 20 == 0: print(group, i + 1, '/', len(todo), round(time.time() - t), 's', flush=True)
    out = [pickle.load(open(fn(w), 'rb')) for w in work]
    out.sort(key=lambda x: (x[0], x[1])); arr = {}
    for key, c0, rec in out:
        for s, d in rec.items():
            for f, v in d.items(): arr.setdefault(f'{key}|{s}|{f}', []).append(v)
    arr = {k: np.concatenate(v) for k, v in arr.items()}
    os.makedirs(SYM, exist_ok=True); np.savez_compressed(os.path.join(SYM, f'r10_{group}.npz'), **arr)
    meta = dict(group=group, git=git_hash(), code_key=gh, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_s=round(time.time() - t), procs=procs,
                jobs=[dict(key=j[0], cond=j[1], pmod=j[2], pref=j[3], seed=j[4], symbols=j[5], only=j[6], mode=j[7]) for j in J])
    json.dump(meta, open(os.path.join(OUT, f'run_meta_R10_{group}.json'), 'w'), indent=0)
    print(group, 'done', meta['elapsed_s'], 's', flush=True)

if __name__ == '__main__':
    procs = int(os.environ.get('PROCS', '7'))
    for g in sys.argv[1:]: run(g, procs)
