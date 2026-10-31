"""Corner-finder dispatch (additive). Default (no 'finder' key in the preset) calls channel.physical.detect_corners(img)
unchanged, so every existing preset is byte-identical. p['finder'] = 'scalefree' sets the finder's bright-level floor
min_dn from the frame's own background noise instead of the fixed 8 DN:
    sigma = 1.4826 * MAD of the background-subtracted 4-px border (all channels), min_dn = max(k * sigma, q),
with k = p['finder_k'] (chosen on the disjoint 'cornertune-*' seeds, see experiments/bench_finder.py) and
q = p.get('finder_q', 1.0) DN (one 8-bit code: below this the image carries no signal)."""
import numpy as np
from channel import physical as ph

def scalefree_min_dn(img, k, q=1.0):
    f = img.astype(np.float32)
    b = np.concatenate([f[:4].reshape(-1, 3), f[-4:].reshape(-1, 3), f[:, :4].reshape(-1, 3), f[:, -4:].reshape(-1, 3)])
    d = b - np.median(b, 0); sigma = 1.4826 * float(np.median(np.abs(d)))
    return max(k * sigma, q)

def find_corners(img, p):
    if p.get('finder') == 'scalefree':
        return ph.detect_corners(img, min_dn=scalefree_min_dn(img, p['finder_k'], p.get('finder_q', 1.0)))
    return ph.detect_corners(img)
