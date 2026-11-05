"""benchmark-r9: opt-in QCD-OCC-win6 receiver; default receiver unchanged."""
import os, numpy as np, pandas as pd
from channel import physical as ph
from tx.schemes import QCDOCC, QCDOCCWin6
import rx.sampler as S

R9 = os.path.join(os.path.dirname(__file__), '..', 'results', 'benchmark', 'r9')

def _frame(seed=3):
    s = QCDOCC(); rng = np.random.RandomState(seed); bits = rng.randint(0, 2, 144); d = s.encode(list(bits))
    p = dict(ph.P); p.update(brightness=1 / 512, f_tx=25.0)
    es, ct, _ = ph.render_mean_e([d, d, d], 2.0, 0, 0, 27.0, rng, p, None, 0.02)
    return ph.capture(es[0], rng, p), ct, bits

def test_default_window_unchanged():
    img, ct, _ = _frame()
    a = S.rectify_and_sample(img, ct); b = S.rectify_and_sample(img, ct, win=S.WIN); c = S.rectify_and_sample(img, ct, win=None)
    assert S.WIN == 4 and all(np.array_equal(x, y) for x, y in zip(a, b)) and all(np.array_equal(x, y) for x, y in zip(a, c))

def test_variant_is_opt_in():
    assert not hasattr(QCDOCC(), 'sample_win') and QCDOCCWin6.sample_win == 6
    assert QCDOCCWin6().name != QCDOCC.name and np.array_equal(QCDOCCWin6().encode([1, 0, 1] * 48), QCDOCC().encode([1, 0, 1] * 48))

def test_r9_tables():
    d = pd.read_csv(os.path.join(R9, 'qcd_win6_crn.csv'))
    assert d.old_identical_to_shipped.all() and len(d) == 26
    c = pd.read_csv(os.path.join(R9, 'qcd_win6_c2.csv'))
    assert c.old_identical_to_e2.all() and (c.v2_rank_native == 1).all() and (c.binding_shipped == c.binding_replaced).all()
    nf = pd.read_csv(os.path.join(R9, 'qcd_floor_noisefree.csv'))
    assert (nf[~nf.bayer_demosaic].ber == 0).all() and (nf[(nf.win == 4) & nf.bayer_demosaic].ber > 0.015).all()
