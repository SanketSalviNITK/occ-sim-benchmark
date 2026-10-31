import numpy as np
from channel import physical as ph, presets_phys as pp
from tx.ablation import HNCSMv2BaseOnly, BaseOnly2LevelDecoder, BaseOnlyLevel075
from tx.schemes import QCDStyle

def test_imx219_preset_is_additive():
    p = pp.imx219()
    assert ph.P['pixel_um'] == 5.86 and ph.P['f_mm'] == 6.0 and ph.P['bits'] == 8   # default untouched
    assert abs(p['t_row'] - 18.904e-6) < 1e-8 and p['pixel_um'] == 1.12 and p['bits'] == 10
    assert abs(ph.sensor_K(p) - 0.177) < 1e-9

def test_base_only_is_v2_cells_at_fixed_level():
    s = HNCSMv2BaseOnly(); q = QCDStyle('first16'); rng = np.random.RandomState(0)
    for _ in range(5):
        b = list(rng.randint(0, 2, 48)); assert np.array_equal(s.encode(b), q.encode(b))
    assert s.layers == [('base', 48)] and s.name.startswith('HNCSM')

def test_ablation_variants_roundtrip_ideal():
    from rx.refs import PILOT_POS
    rng = np.random.RandomState(1)
    for s in (HNCSMv2BaseOnly(), BaseOnly2LevelDecoder(), BaseOnlyLevel075()):
        b = list(rng.randint(0, 2, 48)); d = s.encode(b).astype(float)
        assert s.decode(d, np.zeros(3)) == b


def test_code_key_fallback(tmp_path):
    from experiments.review_r1 import code_key
    assert code_key(gh='abc123') == 'abc123'
    for d in ('tx', 'rx', 'channel', 'experiments', 'occbench'):
        (tmp_path / d).mkdir(); (tmp_path / d / 'm.py').write_text('x=1\n')
    k1 = code_key(root=str(tmp_path), gh='unknown')
    assert k1.startswith('src-') and k1 == code_key(root=str(tmp_path), gh='unknown')
    (tmp_path / 'rx' / 'm.py').write_text('x=2\n')
    assert code_key(root=str(tmp_path), gh='unknown') != k1
