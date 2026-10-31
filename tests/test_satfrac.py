import numpy as np
from experiments.phys_eval import sat_fraction

def test_sat_fraction_in_unit_interval():
    rng = np.random.RandomState(0)
    for _ in range(200):
        roi = rng.exponential(rng.uniform(10, 1e5), size=(20, 20))
        f = sat_fraction(roi, 7863.0)
        assert 0.0 <= f <= 1.0

def test_sat_fraction_old_bug_case():
    # peak far above sat_e/0.15: unlit-but-saturated pixels must not enter the numerator
    roi = np.full((10, 10), 8000.0); roi[0, 0] = 1e6
    f = sat_fraction(roi, 7863.0)
    assert f == 1.0  # only the single lit pixel counts, and it is saturated
    roi2 = np.zeros((4, 4)); assert sat_fraction(roi2, 7863.0) == 0.0
