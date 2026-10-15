import numpy as np, pytest
from tx.schemes import all_schemes, HNCSM, HNCSMv2, HNCSMv2CS, QCDStyle, Nishimoto, NestedTexture
from channel.render import simulate
from rx.sampler import rectify_and_sample

SCHEMES = all_schemes()
IDS = [s.name for s in SCHEMES]

# must match README "Schemes" table
EXPECTED_LAYERS = {
    'HNCSM v2-CS': [('base', 48), ('enh', 72)],   # tuned delta=0.2, 2 bits/LED (results/tuned_params.json)
    'HNCSM v2': [('base', 48), ('enh', 36)],
    'HNCSM': [('base', 16), ('enh', 64)],
    'HNCSM base-only': [('base', 16)],
    'CSK-8': [('all', 180)], 'CSK-4': [('all', 120)], 'OOK-8x8': [('all', 60)],
    'QR/Aztec-style': [('all', 28)],
    'NestedTexture-inspired (Salvi22)': [('outer', 16), ('inner', 16)],
    'QCD-style-inspired (Vasantha22)': [('all', 48)],
    'Overlay-inspired (Nishimoto12)': [('L1', 12), ('L2', 24)],
}

def ideal_samples(drive):
    """Ideal channel: no blur/noise/crosstalk; sensor sees the LED drive exactly, dark = 0."""
    return drive.astype(float), np.zeros(3)

def test_all_schemes_listed():
    assert set(IDS) == set(EXPECTED_LAYERS)

@pytest.mark.parametrize('sch', SCHEMES, ids=IDS)
def test_layers_match_readme(sch):
    assert list(sch.layers) == EXPECTED_LAYERS[sch.name]

@pytest.mark.parametrize('sch', SCHEMES, ids=IDS)
def test_roundtrip_ideal(sch):
    rng = np.random.default_rng(1)
    for _ in range(50):
        b = list(rng.integers(0, 2, sch.nbits))
        d = sch.encode(b)
        assert d.shape == (8, 8, 3) and d.min() >= 0 and d.max() <= 1.0 + 1e-9  # per-channel drive in [0,1]
        assert list(sch.decode(*ideal_samples(d))) == b

@pytest.mark.parametrize('sch', SCHEMES, ids=IDS)
def test_roundtrip_full_channel_close_range(sch):
    rng = np.random.RandomState(2)
    for _ in range(20):
        b = list(rng.randint(0, 2, sch.nbits))
        img, c = simulate(sch.encode(b), distance_m=0.75, rng=rng)
        assert list(sch.decode(*rectify_and_sample(img, c))) == b

LAYERED = [s for s in SCHEMES if len(s.layers) == 2 and s.layers[0][0] == 'base']

@pytest.mark.parametrize('sch', LAYERED, ids=[s.name for s in LAYERED])
def test_hierarchy_base_independent_of_enh_content(sch):
    """Corrupt (randomise) the enhancement bits at TX: base must still decode exactly on the ideal channel."""
    rng = np.random.default_rng(3); nb = sch.layers[0][1]
    for _ in range(30):
        b = rng.integers(0, 2, sch.nbits); b2 = b.copy(); b2[nb:] = rng.integers(0, 2, sch.nbits - nb)
        out = sch.decode(*ideal_samples(sch.encode(list(b2))))
        assert list(out[:nb]) == list(b[:nb])

@pytest.mark.parametrize('sch', [s for s in LAYERED if 'v2' in s.name], ids=lambda s: s.name)
def test_hierarchy_graceful_on_channel(sch):
    """At 2.25 m the enhancement layer is broken but the base layer must still be (nearly) error-free."""
    rng = np.random.RandomState(4); nb = sch.layers[0][1]; eb = ee = 0; F = 40
    for _ in range(F):
        b = np.array(rng.randint(0, 2, sch.nbits)); img, c = simulate(sch.encode(list(b)), distance_m=2.25, rng=rng)
        o = np.array(sch.decode(*rectify_and_sample(img, c)))
        eb += (o[:nb] != b[:nb]).sum(); ee += (o[nb:] != b[nb:]).sum()
    assert eb / (nb * F) < 5e-3 and ee / ((sch.nbits - nb) * F) > 0.05

@pytest.mark.parametrize('cfg', [(0.1, 1), (0.2, 2), (0.3, 2)])
def test_joint_vs_sequential_decoder(cfg):
    """Joint ML and two-stage (base-first) decoding of v2-CS must agree exactly on the ideal channel and on
    near-noise-free captures."""
    j, s = HNCSMv2CS(*cfg, joint=True), HNCSMv2CS(*cfg, joint=False)
    rng = np.random.RandomState(5)
    for _ in range(20):
        b = list(rng.randint(0, 2, j.nbits)); d = j.encode(b)
        assert j.decode(*ideal_samples(d)) == s.decode(*ideal_samples(d)) == b
        img, c = simulate(d, distance_m=0.75, rng=rng); smp = rectify_and_sample(img, c)
        assert j.decode(*smp) == s.decode(*smp)


@pytest.mark.parametrize('cfg', [(0.1, 1), (0.2, 2), (0.3, 1), (0.3, 2)])
def test_v2cs_leak_is_power_neutral(cfg):
    s = HNCSMv2CS(*cfg)
    from tx.schemes import R, G, B
    for c in (R, G, B):
        for v in s.variants(c):
            assert np.isclose(v.sum(), 1.0) and v.min() >= 0

def test_v2cs_default_decoder_uses_leaked_templates():
    assert HNCSMv2CS(0.2, 2).joint is True
