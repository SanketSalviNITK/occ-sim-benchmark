import numpy as np
from experiments.stats import cluster_ber, sym_goodput, paired_diff, paired_auc_diff

def test_cluster_ber_wider_than_binomial_for_bursts():
    err = np.zeros((400, 144), np.uint8); err[:40, :16] = 1          # 40 bursty symbols
    ber, lo, hi = cluster_ber(err)
    assert np.isclose(ber, 640 / 57600)
    se_bin = np.sqrt(ber * (1 - ber) / 57600)
    assert (hi - lo) > 3 * 2 * 1.96 * se_bin * 0.5

def test_sym_goodput_layers_and_blocks():
    err = np.zeros((4, 96), np.uint8); err[0, 50] = 1
    g = sym_goodput(err, [('a', 48), ('b', 48)], 15)
    assert np.allclose(g, [40 * 15, 80 * 15, 80 * 15, 80 * 15])
    gb = sym_goodput(err, [('all', 96)], 15, block=48)
    assert np.allclose(gb, g)
    g1 = sym_goodput(err, [('all', 96)], 15)
    assert g1[0] == 0 and g1[1] == 88 * 15

def test_paired_diff_uses_pairing():
    r = np.random.RandomState(0); common = r.normal(0, 10, 500)
    a = common + 1.0; b = common
    m, lo, hi = paired_diff(a, b)
    assert np.isclose(m, 1.0) and lo > 0.99 and hi < 1.01            # paired: the common noise cancels

def test_paired_auc_diff_sign():
    x = np.array([0, 1, 2.]); A = [np.full(50, 10.), np.full(50, 10.), np.full(50, 10.)]
    B = [np.full(50, 5.), np.full(50, 5.), np.full(50, 5.)]
    a, b, d, lo, hi, *_ = paired_auc_diff(x, A, B)
    assert a == 20 and b == 10 and d == 10 and lo == 10 and hi == 10
