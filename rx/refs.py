"""Colour references from corner pilots (TL=White, TR=Red, BL=Green, BR=Blue) + dark (gap) level."""
import numpy as np
PILOT_POS = {(0, 0): (1, 1, 1), (0, 7): (1, 0, 0), (7, 0): (0, 1, 0), (7, 7): (0, 0, 1)}
PILOT_SET = set(PILOT_POS)

def refs(samples, dark):
    R, G, B = samples[0, 7], samples[7, 0], samples[7, 7]
    M = np.stack([R - dark, G - dark, B - dark], 1)   # 3x3: column j = measured response to LED channel j
    return M, dark

def expected(color, M, dark):
    return dark + M @ np.asarray(color, float)

def on_metric(samples, M, dark):
    """Per-LED 'lit' soft value ~1 if any LED channel on, ~0 if off (crosstalk-inverted, max over channels)."""
    x = (samples - dark) @ np.linalg.pinv(M).T
    return np.clip(x, -0.5, 1.5).max(-1)

def classify(samples_list, palette, M, dark):
    E = np.stack([expected(c, M, dark) for c in palette])
    d = ((samples_list[:, None, :] - E[None]) ** 2).sum(-1)
    return d.argmin(1)
