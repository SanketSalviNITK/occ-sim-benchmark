import numpy as np, cv2
from channel.sensor import SensorParams, capture
from channel.optics import gaussian_blur
from channel.geometry import project_panel, CameraIntrinsics

def test_bayer_pure_red():
    sp = SensorParams(); sp.crosstalk = np.eye(3); sp.read_noise_e = 0.0
    img = capture(np.tile([1.0, 0, 0], (32, 32, 1)), sp, ambient=0.0, rng=np.random.RandomState(0))
    c = img[8:24, 8:24].reshape(-1, 3).mean(0)
    assert c[0] > 150 and c[1] < 3 and c[2] < 3

def test_bayer_pure_blue_and_green():
    sp = SensorParams(); sp.crosstalk = np.eye(3); sp.read_noise_e = 0.0
    for ch in (1, 2):
        rad = np.zeros((32, 32, 3)); rad[..., ch] = 1
        c = capture(rad, sp, 0.0, np.random.RandomState(0))[8:24, 8:24].reshape(-1, 3).mean(0)
        assert c.argmax() == ch and np.delete(c, ch).max() < 3

def test_blur_kernel_normalised():
    img = np.zeros((61, 61, 3), np.float32); img[30, 30] = 1.0
    for s in (0.5, 1.0, 2.5, 5.0):
        out = gaussian_blur(img, s)
        assert np.allclose(out.sum((0, 1)), 1.0, atol=1e-4)
        # spread matches sigma
        yy, xx = np.mgrid[0:61, 0:61]; w = out[..., 0]
        var = (w * ((xx - 30) ** 2)).sum()
        assert abs(np.sqrt(var) - s) < 0.15 * s + 0.05
    assert gaussian_blur(img, 0.0) is img

def test_noise_statistics():
    level = 0.3; rad = np.full((200, 200, 3), level)
    sp8 = SensorParams(); sp8.bayer = False; sp8.crosstalk = np.eye(3)
    dn = capture(rad, sp8, 0.0, np.random.RandomState(1)).astype(float)
    e_mean = level * sp8.exposure_gain * sp8.full_well_e
    k = 255 / sp8.full_well_e
    exp_mean = e_mean * k
    exp_std = np.sqrt(e_mean + sp8.read_noise_e ** 2) * k
    exp_std_q = np.sqrt(exp_std ** 2 + 1 / 12)  # + quantisation
    assert abs(dn.mean() - exp_mean) < 0.05
    assert abs(dn.std() - exp_std_q) / exp_std_q < 0.05

def test_homography_identity_at_zero_angle():
    cam = CameraIntrinsics(f_px=1000.0)
    for d in (0.5, 1.0, 3.0):
        c = project_panel(d, 0, 0, 0, n=8, pitch_mm=8.0, cam=cam)
        side = 1000.0 * 64.0 / (d * 1000.0)
        exp = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * side / 2
        assert np.allclose(c, exp, atol=1e-9)
        src = np.array([[0, 0], [64, 0], [64, 64], [0, 64]], np.float32)
        H = cv2.getPerspectiveTransform(src, c.astype(np.float32))
        Hn = H / H[2, 2]
        assert np.allclose(Hn[[0, 1], [1, 0]], 0, atol=1e-6) and np.allclose(Hn[2, :2], 0, atol=1e-9)
        assert np.isclose(Hn[0, 0], side / 64) and np.isclose(Hn[1, 1], side / 64)

def test_yaw_foreshortening():
    c = project_panel(1.0, 60, 0, 0)
    w = c[:, 0].max() - c[:, 0].min()
    assert w < 0.6 * 64  # ~cos60 * 64 px

def test_lowlight_preset_and_dark_current():
    from channel.presets import low_light, PHOTO_E_PER_MS
    sp = low_light(1.0); sp.bayer = False; sp.crosstalk = np.eye(3)
    rad = np.full((150, 150, 3), 0.5)
    dn = capture(rad, sp, 0.0, np.random.RandomState(0)).astype(float)
    e = 0.5 * PHOTO_E_PER_MS + sp.dark_e
    assert abs(dn.mean() - e * sp.conversion_gain) < 0.3
    assert abs(dn.std() - np.sqrt(e + sp.read_noise_e ** 2) * sp.conversion_gain) / (np.sqrt(e + 9) * 1.5) < 0.06
    assert np.isclose(low_light(2.0).exposure_gain, 2 * low_light(1.0).exposure_gain)

def test_distance_jitter_changes_scale():
    from channel.render import simulate
    d = np.ones((8, 8, 3))
    _, c0 = simulate(d, distance_m=2.0, corner_jitter_px=0, rng=np.random.RandomState(1))
    _, c1 = simulate(d, distance_m=2.0, corner_jitter_px=0, distance_jitter_frac=0.02, rng=np.random.RandomState(1))
    w0 = c0[1, 0] - c0[0, 0]; w1 = c1[1, 0] - c1[0, 0]
    assert abs(w0 - 32.0) < 1e-6 and 0.97 * 32 < w1 < 1.03 * 32 and abs(w1 - 32) > 1e-6
