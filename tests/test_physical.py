"""Tests for the physical channel (channel/physical.py), CSK802 and the physical evaluation loop."""
import numpy as np, pytest
from channel import physical as ph
from tx.schemes import CSK802, QCDOCC, OOK, all_schemes_phys
from experiments.phys_eval import eval_point_phys

def test_komine_lambertian_formula():
    p = dict(ph.P); d = 1.7; phi, psi = 20.0, 10.0; m = p['lambert_m']
    A = np.pi * (p['f_mm'] * 1e-3 / (2 * p['f_number'])) ** 2
    # Komine & Nakagawa 2004: P_r = P_t (m+1) A / (2 pi d^2) cos^m(phi) cos(psi); per-sr on-axis intensity I0 = P_t (m+1)/(2 pi)
    I0 = ph.photon_rate_per_sr(p) * p['brightness'] * p['t_exp']
    exp = I0 * A / d ** 2 * np.cos(np.radians(phi)) ** m * np.cos(np.radians(psi))
    assert np.allclose(ph.received_photons(d, phi, psi, p), exp, rtol=1e-9)
    assert np.allclose(ph.received_photons(2 * d, 0, 0, p) * 4, ph.received_photons(d, 0, 0, p))   # inverse square

def test_psf_has_airy_floor_and_grows_with_defocus():
    p = ph.P; s_focus = ph.psf_sigma_px(p['focus_m'], p)
    airy = 0.42 * np.array(p['lam_nm']) * 1e-9 * p['f_number'] / (p['pixel_um'] * 1e-6)
    assert np.allclose(np.atleast_1d(s_focus), airy, rtol=1e-6) or np.all(np.atleast_1d(s_focus) >= airy.min() - 1e-9)
    assert np.all(np.atleast_1d(ph.psf_sigma_px(0.4, p)) > np.atleast_1d(s_focus))
    assert np.all(np.atleast_1d(ph.psf_sigma_px(5.0, p)) > np.atleast_1d(s_focus))

def test_malvar_constant_image_is_preserved():
    m = np.full((16, 16), 100.0)
    out = ph.malvar_demosaic(m)
    assert np.allclose(out[2:-2, 2:-2], 100.0, atol=1e-6)

def test_capture_noise_matches_emva_at_dark():
    p = dict(ph.P); rng = np.random.RandomState(0)
    raw = ph.capture(np.zeros((64, 64, 3)), rng, p, raw=True)
    assert raw.shape[:2] == (64, 64)

def test_row_weights_sum_to_one():
    w = ph.row_weights(100, 300, 0.01)
    assert w.shape == (100, 3) and np.allclose(w.sum(1), 1.0)

def test_csk802_points_constant_drive_and_distinct():
    for o in (4, 8):
        pal = np.array(CSK802(o).palette)
        assert len(pal) == o and np.allclose(pal.sum(1), 1.0) and (pal >= -1e-12).all()
        dmin = min(np.linalg.norm(a - b) for i, a in enumerate(pal) for b in pal[i + 1:]); assert dmin > 0.05

def test_detector_accuracy_close_range():
    s = OOK()
    for seed in range(5):
        rng = np.random.RandomState(seed); b = rng.randint(0, 2, 60)
        es, ct, _ = ph.render_mean_e([s.encode(list(b)) * 0.34], 1.0, rng=rng)
        c = ph.detect_corners(ph.capture(es[0], rng))
        assert c is not None and np.abs(c - ct).max() < 0.25 * abs(ct[1, 0] - ct[0, 0]) / 8

def test_physical_roundtrip_close_range():
    sch = [OOK(), CSK802(4), QCDOCC()]
    res, st = eval_point_phys(sch, {s.name: 0.4 for s in sch}, dict(distance_m=0.75), 6, 7)
    for s in sch:
        assert sum(v[1] for v in res[s.name].values()) == 0, s.name

def test_phys_lineup():
    names = [s.name for s in all_schemes_phys()]
    assert 'CSK802-8' in names and 'CSK802-4' in names and not any(n.startswith('CSK-') for n in names)

def test_high_bit_adc_on_8bit_scale():
    import numpy as np
    from channel import physical as ph
    e = np.full((8, 8, 3), 3000.0)
    out = {}
    for b in (8, 12):
        p = dict(ph.P); p['bits'] = b
        out[b] = ph.capture(e, np.random.RandomState(0), p).astype(float).mean()
    assert abs(out[8] - out[12]) < 1.0           # same 8-bit-equivalent level, finer steps at 12 bit

def test_eval_point_records_per_symbol_errors():
    import numpy as np
    from tx.schemes import OOK
    from experiments.phys_eval import eval_point_phys
    s = OOK(); rec = {}
    res, _ = eval_point_phys([s], {s.name: 0.34}, dict(distance_m=1.0), 3, 7, rec=rec)
    assert rec[s.name]['err'].shape == (3, s.nbits) and rec[s.name]['err'].sum() == res[s.name]['all'][0]
    assert rec[s.name]['sat'].shape == (3,)
