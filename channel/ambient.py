"""Ambient illumination (normalised to a full-on white LED = 1)."""
import numpy as np

def ambient_level(lux_ratio=0.03):
    return lux_ratio

def nonuniform_field(shape, level, rng):
    """Non-uniform ambient: random-direction linear gradient (0.4x..1.6x of level) plus a Gaussian hotspot
    (peak +1.5x level, sigma = 25% of the image) at a random position. Mean is ~1.2-1.4x level."""
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W] / max(H, W)
    th = rng.uniform(0, 2 * np.pi)
    g = np.cos(th) * (xx - xx.mean()) + np.sin(th) * (yy - yy.mean())
    g = 0.4 + 1.2 * (g - g.min()) / max(np.ptp(g), 1e-9)
    cy, cx = rng.uniform(0, 1, 2) * [yy.max(), xx.max()]
    hot = 1.5 * np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * 0.25 ** 2))
    return level * (g + hot)
