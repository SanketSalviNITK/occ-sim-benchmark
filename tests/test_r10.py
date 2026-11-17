"""benchmark-r10 additions: opt-in WS2812B PWM (channel/pwm.py) and integer drive codes (P['ws_quant']).
Defaults must reproduce benchmark-r9 arrays exactly; the PWM decomposition must equal the DC render when PWM is off."""
import os, numpy as np, pytest, config
from channel import physical as ph, pwm
from tx.schemes import all_schemes_phys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(ROOT, *p)

def _drives(d_scale=1.3, k=1):
    s = all_schemes_phys()[k]; r = np.random.RandomState(5)
    return [s.encode(list(r.randint(0, 2, s.nbits))) * d_scale for _ in range(3)]

def test_defaults_off():
    assert ph.P['pwm_hz'] is None and ph.P['ws_quant'] is False

def test_ws_quant_off_is_identity_and_codes():
    D = np.array([0.0, 0.2, 0.5, 1.0, 1.3])
    assert ph.ws_drive(D, ph.P) is D
    assert ph.ws_codes(D, dict(ph.P, brightness=1 / 128)).tolist() == [0, 0, 1, 2, 3]   # 255/128 = 1.99 code per unit drive
    assert ph.ws_codes(D, dict(ph.P, brightness=1 / 256)).tolist() == [0, 0, 0, 1, 1]   # 0.996 code per unit drive
    q = ph.ws_drive(D, dict(ph.P, ws_quant=True)); assert np.allclose(q * 255 / 128, np.round(D * 255 / 128))

def test_render_default_byte_identical():
    drv = _drives(); p0 = {k: v for k, v in ph.P.items() if k not in ('pwm_hz', 'ws_quant')}
    a, ca, ra = ph.render_mean_e(drv, 3.0, rng=np.random.RandomState(9), p=p0)
    b, cb, rb = ph.render_mean_e(drv, 3.0, rng=np.random.RandomState(9), p=ph.P)
    assert ra == rb and np.array_equal(ca, cb) and all(np.array_equal(x, y) for x, y in zip(a, b))

@pytest.mark.parametrize('d', [0.5, 3.0, 5.0])
def test_pwm_decomposition_equals_dc_render(d):
    drv = _drives(); p = dict(ph.P)
    es, ct, row0 = ph.render_mean_e(drv, d, rng=np.random.RandomState(9), p=p)
    X = pwm.prepare(drv, d, rng=np.random.RandomState(9), p=p)
    assert np.allclose(X.corners, ct) and X.row0 == row0 and X.shape == es[0].shape[:2]
    for ts in (-0.01, 0.001, 0.02):
        w = ph.row_weights(X.shape[0], row0, ts, p); e0 = sum(w[:, i, None, None] * es[i] for i in range(3))
        e1 = pwm.compose(X, pwm.row_factors(X, ts, None))
        assert np.abs(e1 - e0).max() <= 1e-5 * e0.max()

def test_prepare_consumes_rng_like_render():
    drv = _drives(); r1, r2 = np.random.RandomState(4), np.random.RandomState(4)
    ph.render_mean_e(drv, 3.0, rng=r1); pwm.prepare(drv, 3.0, rng=r2, p=dict(ph.P, pwm_hz=432.0))
    assert r1.randint(0, 2 ** 31) == r2.randint(0, 2 ** 31)

def test_side_phases_do_not_advance_rng():
    r = np.random.RandomState(11); st = r.get_state()
    f = pwm.side_phases(r, 64, dict(ph.P, pwm_hz=432.0)); st2 = r.get_state()
    assert st[2] == st2[2] and np.array_equal(st[1], st2[1])
    assert f.shape == (64,) and f.min() >= 0 and f.max() < 1 / 432.0

def test_cum_on_closed_form():
    Tp, on = 1.0, 0.25
    L = lambda u, v, phi: pwm._cum_on(v, phi, Tp, on) - pwm._cum_on(u, phi, Tp, on)
    assert np.isclose(L(0.0, 0.1, 0.0), 0.1) and np.isclose(L(0.0, 1.0, 0.0), 0.25) and np.isclose(L(0.3, 0.9, 0.0), 0.0)
    assert np.isclose(L(0.0, 10.0, 0.37), 2.5) and np.isclose(L(0.2, 0.4, 0.1), 0.15)   # on [0.1, 0.35]

@pytest.mark.parametrize('hz', [432.0, 2000.0])
def test_pwm_phase_average_equals_dc(hz):
    """Averaged over a uniform grid of LED phases the PWM row factors equal the DC row factors (duty x overlap)."""
    drv = _drives(); p = dict(ph.P, pwm_hz=hz); X = pwm.prepare(drv, 3.0, rng=np.random.RandomState(9), p=p)
    a0 = pwm.row_factors(X, 0.01, None); N = 2000
    m = sum(pwm.row_factors(X, 0.01, np.full(64, (k + 0.5) / N / hz)) for k in range(N)) / N
    nz = a0 > 1e-9; assert np.abs(m[nz] / a0[nz] - 1).max() < 0.01

def test_pwm_changes_capture_and_is_on_off():
    drv = _drives(); p = dict(ph.P, pwm_hz=432.0); X = pwm.prepare(drv, 3.0, rng=np.random.RandomState(9), p=p)
    a = pwm.row_factors(X, 0.01, pwm.side_phases(np.random.RandomState(1), 64, p)); a0 = pwm.row_factors(X, 0.01, None)
    assert not np.allclose(a, a0) and (a[a0 > 0] == 0).mean() > 0.3   # at 432 Hz and 1/1500 s most LEDs are off or ~3.5x

def _e2(): 
    f = R('results/phys_sym/review_e2_P33.npz')
    if not os.path.exists(f): pytest.skip('review_e2_P33.npz missing')
    return np.load(f)

def test_r10_default_std_pipeline_matches_e2():
    z = _e2(); from experiments import revision_r6 as R6
    _, _, rec = R6.job(('x', dict(distance_m=3.25, t_exp=1 / 500), dict(brightness=1 / 128, pwm_hz=None, ws_quant=False), 33.011,
                        config.cond_seed('d3.25', 0, config.SEED), 0, 2, None, 'std'))
    for s, d in rec.items():
        for k, v in d.items(): assert np.array_equal(v, z[f'd3.25|1/500|1/128|eval|{s}|{k}'][:2]), (s, k)

def test_r10_default_dual_pipeline_matches_r6_finder():
    f = R('results/phys_sym/r6_finder.npz')
    if not os.path.exists(f): pytest.skip('r6_finder.npz missing')
    z = np.load(f); from experiments import revision_r6 as R6
    _, _, rec = R6.job(('x', dict(distance_m=3.0, t_exp=1 / 1500), dict(brightness=1 / 128, pwm_hz=None, ws_quant=False), 33.011,
                        config.cond_seed('d3.0', 0, config.SEED), 0, 2, None, 'dual'))
    for s, d in rec.items():
        for k in ('err', 'err_orc', 'nfail', 'ngross'): assert np.array_equal(d[k], z[f'd3.0|1/1500|1/128|eval|{s}|{k}'][:2]), (s, k)

def test_r10_default_sweep_dual_matches_sweeps_p33():
    f = R('results/phys_sym/sweeps_PHYS_P33.npz')
    if not os.path.exists(f): pytest.skip('sweeps_PHYS_P33.npz missing')
    z = np.load(f); from experiments import revision_r6 as R6; from experiments.revision_r10 import ENTRIES
    _, _, rec = R6.job(('x', dict(distance_m=3.0), dict(pwm_hz=None), 33.011, config.cond_seed('distance_m', 10, config.SEED), 0, 2, list(ENTRIES), 'dual'))
    assert set(rec) == set(ENTRIES)
    for s, d in rec.items(): assert np.array_equal(d['err'], z[f'distance_m|10|eval|{s}|err'][:2]), s

def test_pwm_pipeline_crn_payloads_unchanged_and_output_differs():
    z = _e2(); from experiments import revision_r6 as R6
    _, _, rec = R6.job(('x', dict(distance_m=3.0, t_exp=1 / 1500), dict(brightness=1 / 128, pwm_hz=432.0), 33.011,
                        config.cond_seed('d3.0', 0, config.SEED), 0, 3, None, 'dual'))
    assert any(not np.array_equal(d['err'], z[f'd3.0|1/1500|1/128|eval|{s}|err'][:3]) for s, d in rec.items())
    assert all(d['ncand'].tolist() == [int(x) for x in d['ncand']] for d in rec.values())

def test_r10_design():
    from experiments.revision_r10 import jobs_for, ENTRIES
    from tx.schemes import all_schemes_phys
    assert ENTRIES == [s.name for s in all_schemes_phys()]
    J = jobs_for('c2pwm432'); assert len(J) == 2 * 4 * 2 and {j[2]['pwm_hz'] for j in J} == {432.0}
    assert len(jobs_for('c2quant')) == 2 * 2 * 4 * 2 and all(j[7] == 'dual' for j in J)
    assert {j[4] for j in J if j[0].startswith('d3.0') and j[0].endswith('eval')} == {config.cond_seed('d3.0', 0, config.SEED)}
    S = jobs_for('swfocus3'); assert len(S) == 19 and S[10][4] == config.cond_seed('distance_m', 10, config.SEED) and S[0][2] == dict(focus_m=3.0)
