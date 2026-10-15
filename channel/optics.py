"""LED emission + optical blur."""
import numpy as np, cv2

def lambertian_gain(view_angle_deg, m=1.0):
    """Relative radiance toward camera for Lambertian order m (radiance of a Lambertian
    emitter is angle-independent for m=1; generalized-Lambertian LEDs: cos^(m-1))."""
    return max(np.cos(np.radians(view_angle_deg)), 0.0) ** max(m - 1.0, 0.0)

def gaussian_blur(img, sigma_px):
    if sigma_px <= 0.05:
        return img
    k = int(2 * np.ceil(3 * sigma_px) + 1)
    return cv2.GaussianBlur(img, (k, k), sigma_px, borderType=cv2.BORDER_REPLICATE)
