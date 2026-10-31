import numpy as np
from occbench import available, create, check_scheme
from experiments.common import power_scales
from experiments.phys_eval import eval_point_phys
from channel import physical as ph

def test_example_plugin_registered_and_roundtrips():
    names = available()
    assert 'EXAMPLE OOK-rep2' in names and 'HNCSM v2' in names and 'CSK802-8' in names
    s = create('EXAMPLE OOK-rep2'); assert s.nbits == 30 and check_scheme(s)

def test_example_plugin_runs_on_physical_channel():
    s = create('EXAMPLE OOK-rep2'); sc = power_scales([s], 33.011, 'equal', False)[0]; rec = {}
    eval_point_phys([s], sc, dict(distance_m=1.0, yaw_deg=0.0, blur_sigma_px=0.0, lux=27.0, jitter=0.02, genie_corners=True), 3, 123, dict(ph.P), rec=rec)
    assert rec[s.name]['err'].shape == (3, 30) and rec[s.name]['err'].mean() < 0.1

def test_registry_does_not_change_paper_lineup():
    from experiments.review_r1 import lineup_r1
    assert 'EXAMPLE OOK-rep2' not in [x.name for x in lineup_r1()]
