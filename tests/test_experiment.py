import numpy as np, config
from experiments.common import wilson, eval_point, power_scales, rows_from, CRC_BITS
from tx.schemes import all_schemes, QCDStyle, CSK

def test_cond_seed_deterministic_and_unsalted():
    assert config.cond_seed('distance_m', 3) == config.cond_seed('distance_m', 3)
    assert config.cond_seed('distance_m', 3) != config.cond_seed('blur_sigma_px', 3)
    assert config.cond_seed('x', 0, 1) == (1 + __import__('zlib').crc32(b'x')) % (2**31 - 1)

def test_wilson():
    lo, hi = wilson(0, 1000); assert lo == 0 and 0.003 < hi < 0.004
    lo, hi = wilson(500, 1000); assert abs(lo - 0.469) < 0.002 and abs(hi - 0.531) < 0.002

def test_eval_reproducible_and_crn():
    s = [QCDStyle(), CSK(8)]; sc, _, _ = power_scales(s)
    cond = dict(distance_m=2.5)
    a = eval_point(s, sc, cond, 10, 123); b = eval_point(s, sc, cond, 10, 123)
    assert a == b
    # CRN: a scheme's result does not depend on which other schemes are evaluated alongside it
    c = eval_point([s[0]], sc, cond, 10, 123)
    assert c[s[0].name] == a[s[0].name]

def test_equal_power_scaling():
    s = all_schemes(); sc, P, pref = power_scales(s)
    for k in P: assert abs(P[k] * sc[k] - pref) < 1e-9 and sc[k] <= 1 + 1e-12

def test_crc_charge():
    s = [CSK(4)]; res = {s[0].name: {'all': [0, 0]}}
    r = rows_from(res, s, 10, 1.0, {})[-1]
    assert r['goodput_bps'] == (120 - CRC_BITS) * 30
