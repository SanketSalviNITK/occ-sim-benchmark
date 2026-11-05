"""Receiver front-end: homography rectification from (estimated) finder corners, per-LED sampling."""
import numpy as np, cv2
G = 8  # canonical px per LED after rectification
WIN = 4  # central sampling window (canonical px) per LED

def rectify_and_sample(img, corners, n=8, win=None):
    """win: central sampling window in canonical px (default WIN = 4; benchmark-r9 opt-in QCD-OCC-win6 uses 6)."""
    src = np.array([[0, 0], [n * G, 0], [n * G, n * G], [0, n * G]], np.float32)
    H = cv2.getPerspectiveTransform(src, corners.astype(np.float32))
    can = cv2.warpPerspective(img.astype(np.float32) / 255.0, H, (n * G, n * G),
                              flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    c = can.reshape(n, G, n, G, 3)
    h = (WIN if win is None else int(win)) // 2
    samples = c[:, G//2-h:G//2+h, :, G//2-h:G//2+h, :].mean(axis=(1, 3))      # LED centres
    # dark/ambient reference: median of a 4-px image border strip around the ROI (panel surround).
    # (inter-LED gaps were tried first but are contaminated by blur once LED pitch < ~3 px)
    f = img.astype(np.float32) / 255.0
    dark = np.median(np.concatenate([f[:4].reshape(-1, 3), f[-4:].reshape(-1, 3),
                                     f[:, :4].reshape(-1, 3), f[:, -4:].reshape(-1, 3)]), axis=0)
    return samples, dark
