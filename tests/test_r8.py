"""benchmark-r8 additions: optional sigma_mult term (default off, byte-identical), side-stream property, correlation
modes, r8 job design, claim text."""
import os, numpy as np, pytest
from channel import physical as ph
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(ROOT, *p)

def _e(shape=(40, 48)):
    r = np.random.RandomState(3); return r.uniform(0, 3000, shape + (3,))

def test_sigma_mult_default_off():
    assert ph.P['sigma_mult'] == 0.0 and ph.P['sigma_mult_corr'] == 'pixel'

def test_sigma0_capture_byte_identical():
    e = _e(); p0 = {k: v for k, v in ph.P.items() if k not in ('sigma_mult', 'sigma_mult_corr')}
    a = ph.capture(e, np.random.RandomState(7), p0); b = ph.capture(e, np.random.RandomState(7), ph.P)
    c = ph.capture(e, np.random.RandomState(7), dict(ph.P, sigma_mult=0.0, sigma_mult_corr='frame'))
    assert np.array_equal(a, b) and np.array_equal(a, c)

def test_mult_gain_side_stream_and_modes():
    r = np.random.RandomState(11); st = r.get_state()
    g = ph._mult_gain((40, 48), r, dict(ph.P, sigma_mult=0.15))
    st2 = r.get_state(); assert st[2] == st2[2] and np.array_equal(st[1], st2[1])          # rng not advanced
    assert abs(g.mean() - 1) < 0.02 and abs(g.std() - 0.15) < 0.02 and g.min() >= 0
    gf = ph._mult_gain((40, 48), np.random.RandomState(11), dict(ph.P, sigma_mult=0.15, sigma_mult_corr='frame'))
    assert len(np.unique(gf[0::2, 0::2])) == 1 and len(np.unique(gf[1::2, 1::2])) == 1
    assert np.array_equal(gf[0::2, 1::2], gf[1::2, 0::2])                                    # both G sites share the G gain
    with pytest.raises(ValueError): ph._mult_gain((4, 4), r, dict(ph.P, sigma_mult=0.1, sigma_mult_corr='led'))

def test_sigma_changes_output():
    e = _e(); a = ph.capture(e, np.random.RandomState(7), ph.P)
    b = ph.capture(e, np.random.RandomState(7), dict(ph.P, sigma_mult=0.15)); assert not np.array_equal(a, b)

def test_r8_pipeline_sigma0_matches_e2():
    f = R('results/phys_sym/review_e2_P33.npz')
    if not os.path.exists(f): pytest.skip('review_e2_P33.npz missing')
    import config; from experiments import revision_r6 as R6
    z = np.load(f)
    _, _, rec = R6.job(('x', dict(distance_m=3.0, t_exp=1 / 1500), dict(brightness=1 / 128, sigma_mult=0.0), 33.011,
                        config.cond_seed('d3.0', 0, config.SEED), 0, 2, None, 'std'))
    assert len(rec) > 5
    for s, d in rec.items():
        for k, v in d.items(): assert np.array_equal(v, z[f'd3.0|1/1500|1/128|eval|{s}|{k}'][:2]), (s, k)

def test_r8_design():
    from experiments.revision_r8 import jobs_for
    J = jobs_for('mult'); assert len(J) == 7 * 3 * 2 and len(jobs_for('multfin')) == 6 * 3
    assert {j[2]['sigma_mult'] for j in J} == {0.0, 0.024, 0.05, 0.15}

def test_r8_sigma0_identity_csv():
    f = R('results/benchmark/r8/mult_sigma0_identity.csv')
    if not os.path.exists(f): pytest.skip('r8 mult not run')
    import pandas as pd; d = pd.read_csv(f); assert len(d) > 0 and d.identical.all()
