"""benchmark-r6 additions: dual receiver is exactly CRN with the standard and oracle paths; Holm; sensitivity levels."""
import numpy as np, config
from channel import physical as ph

def test_dual_receiver_matches_detector_and_oracle():
    from experiments.revision_r6 import job
    a = (dict(distance_m=3.25, t_exp=1 / 1500), dict(brightness=1 / 128), 33.011, config.cond_seed('d3.25', 0, config.SEED), 0, 2, None)
    _, _, rd = job(('k',) + a + ('dual',))
    _, _, rs = job(('k',) + a + ('std',))
    c = dict(a[0], genie_corners=True)
    _, _, ro = job(('k', c) + a[1:] + ('std',))
    for n in rs:
        assert np.array_equal(rd[n]['err'], rs[n]['err'])
        assert np.array_equal(rd[n]['err_orc'], ro[n]['err'])

def test_holm_adjust():
    from experiments.r6_report import holm_adjust
    adj = holm_adjust([0.01, 0.04, 0.03, 0.005])
    assert np.allclose(adj, [0.03, 0.06, 0.06, 0.02])

def test_sens_levels_do_not_touch_defaults():
    from experiments.revision_r6 import SENS, _cfa
    assert len(SENS) == 10                                  # 9 Table-2 ASSUMED rows, lens split into f, N, focus; brightness via E2
    assert np.allclose(_cfa(1.0), ph.P['cfa']); assert np.allclose(_cfa(2.0).sum(1), 1)
    assert ph.P['brightness'] == 1 / 128 and ph.P['bits'] == 8 and ph.P['f_tx'] == 15.0 and ph.P['panel_mm'] == 65.0

def test_bootstrap_p_floor():
    from experiments.r6_report import boot
    m, lo, hi, p = boot(np.ones(50), B=1000); assert m == 1 and p == 1e-3
