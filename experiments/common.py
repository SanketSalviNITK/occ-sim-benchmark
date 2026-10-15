"""Shared evaluation core: equal-average-power normalisation, common random numbers (CRN), per-layer CRC charge,
Wilson confidence intervals."""
import numpy as np, config
from channel.render import simulate
from rx.sampler import rectify_and_sample

FPS = 30
CRC_BITS = 8          # every independently-decodable unit (layer) is charged a CRC-8
MAX_BITS = 256

def mean_power(sch, n=2000, seed=0):
    """Average emitted optical power per frame = mean over random payloads of the summed RGB drive of all 64 LEDs
    (pilots included)."""
    rng = np.random.RandomState(seed)
    return float(np.mean([sch.encode(list(rng.randint(0, 2, sch.nbits))).sum() for _ in range(n)]))

def power_scales(schemes, pref=None, mode='equal', cap=False):
    """mode='equal': scale every scheme's drive (incl. pilots) to the same average power pref (default: the lowest
    scheme's, so nothing clips). mode='peak': no scaling (peak drive <= 1 per channel)."""
    P = {s.name: mean_power(s) for s in schemes}
    if mode == 'peak': return {k: 1.0 for k in P}, P, None
    pref = pref if pref is not None else min(P.values())
    # cap=True: no overdrive above full LED drive -> schemes whose full-drive power is below the budget run at full drive
    return {k: (min(pref / v, 1.0) if cap else pref / v) for k, v in P.items()}, P, pref

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)

def eval_point(schemes, scales, cond, frames, seed):
    """CRN: frame f uses the same payload stream and the same channel-noise seed for every scheme."""
    res = {s.name: {l: [0, 0] for l, _ in s.layers} for s in schemes}   # layer -> [bit errors, frame errors]
    for f in range(frames):
        payload = np.random.RandomState(config.cond_seed('payload', f, seed)).randint(0, 2, MAX_BITS)
        cs = config.cond_seed('channel', f, seed)
        for s in schemes:
            b = payload[:s.nbits]
            img, c = simulate(s.encode(list(b)) * scales[s.name], rng=np.random.RandomState(cs), **cond)
            o = np.array(s.decode(*rectify_and_sample(img, c))); i = 0
            for l, n in s.layers:
                e = int((o[i:i+n] != b[i:i+n]).sum()); res[s.name][l][0] += e; res[s.name][l][1] += e > 0; i += n
    return res

def rows_from(res, schemes, frames, power, extra):
    rows = []
    for s in schemes:
        tot_g = tot_lo = tot_hi = 0.0; tot_e = 0
        for l, n in s.layers:
            be, fe = res[s.name][l]; lo, hi = wilson(fe, frames); net = max(n - CRC_BITS, 0)
            g = net * FPS * (1 - fe / frames); glo = net * FPS * (1 - hi); ghi = net * FPS * (1 - lo)
            tot_g += g; tot_lo += glo; tot_hi += ghi; tot_e += be
            rows.append(dict(extra, scheme=s.name, layer=l, bits_per_frame=n, net_bits=net, frames=frames,
                             ber=be / (n * frames), fer=fe / frames, fer_lo=lo, fer_hi=hi,
                             goodput_bps=g, goodput_lo=glo, goodput_hi=ghi))
        rows.append(dict(extra, scheme=s.name, layer='TOTAL', bits_per_frame=s.nbits, frames=frames,
                         net_bits=sum(max(n - CRC_BITS, 0) for _, n in s.layers), ber=tot_e / (s.nbits * frames),
                         goodput_bps=tot_g, goodput_lo=tot_lo, goodput_hi=tot_hi,
                         goodput_per_power=tot_g / power, power=power))
    return rows
