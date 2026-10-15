"""Full channel: LED drive (8x8x3) -> captured camera image + ground-truth corners."""
import numpy as np, cv2
from .geometry import project_panel
from .optics import lambertian_gain, gaussian_blur
from .sensor import SensorParams, capture
from .ambient import nonuniform_field

SS = 4           # supersampling factor
PPL = 16         # canonical pixels per LED (panel texture)
LED_FILL = 0.6   # LED emitter diameter / pitch (5 mm LED on 8 mm pitch)

def panel_texture(drive):
    n = drive.shape[0]
    yy, xx = np.mgrid[0:PPL, 0:PPL] + 0.5
    disc = (((xx - PPL / 2) ** 2 + (yy - PPL / 2) ** 2) <= (LED_FILL * PPL / 2) ** 2).astype(np.float32)
    return np.repeat(np.repeat(drive.astype(np.float32), PPL, 0), PPL, 1) * np.tile(disc, (n, n))[:, :, None]

def simulate(drive, distance_m=1.0, yaw_deg=0.0, roll_deg=0.0, blur_sigma_px=0.0, ambient=0.03,
             sp=None, lambert_m=1.0, ambient_nonuniform=False, distance_jitter_frac=0.0, base_blur_px=0.5, corner_jitter_px=0.3, rng=np.random):
    sp = sp or SensorParams()
    n = drive.shape[0]
    tex = panel_texture(drive) * lambertian_gain(yaw_deg, lambert_m)
    if distance_jitter_frac > 0:   # hand-held / placement jitter; avoids exact integer-pitch (Bayer-phase-locked) points
        distance_m = distance_m * (1 + rng.uniform(-distance_jitter_frac, distance_jitter_frac))
    img_c = project_panel(distance_m, yaw_deg, 0.0, roll_deg, n) + rng.uniform(0, 1, 2)  # random sub-pixel phase
    lo = np.floor(img_c.min(0)) - 12
    size = (np.ceil(img_c.max(0)) + 12 - lo).astype(int)
    dst = (img_c - lo) * SS
    src = np.array([[0, 0], [n * PPL, 0], [n * PPL, n * PPL], [0, n * PPL]], np.float32)
    H = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    hi = cv2.warpPerspective(tex, H, (int(size[0] * SS), int(size[1] * SS)), flags=cv2.INTER_LINEAR)
    rad = cv2.resize(hi, (int(size[0]), int(size[1])), interpolation=cv2.INTER_AREA)
    rad = gaussian_blur(rad, np.hypot(base_blur_px, blur_sigma_px))
    amb = nonuniform_field(rad.shape[:2], ambient, rng) if ambient_nonuniform else ambient
    img = capture(rad, sp, amb, rng)
    corners_true = img_c - lo
    corners_est = corners_true + rng.normal(0, corner_jitter_px, corners_true.shape)  # finder-detection error
    return img, corners_est
