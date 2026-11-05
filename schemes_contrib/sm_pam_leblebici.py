"""SM-PAM-inspired (Leblebici et al., Physical Communication 2026).

Inspired by: A. T. Leblebici, S. Hassan, E. Panayirci, H. V. Poor, "Joint communication and
indoor positioning based on visible light in the presence of dimming," Phys. Commun. 78:103205,
2026. doi:10.1016/j.phycom.2026.103205  (arXiv:2508.04570)

Not a reproduction. Adaptations for this 8x8 RGB-LED camera-OCC harness:
  - Spatial modulation + M-ary PAM: the 60 data LEDs are partitioned into groups of N_g=4;
    per group one LED is active (index carries log2(N_g) bits) at one of M PAM intensity levels
    (log2(M) bits). Inactive LEDs in the group are off. Corner pilots kept.
  - Optical intensity levels are the positive PAM set {1,3,...,2M-1}/(2M-1) on white drive
    (paper uses bipolar electrical PAM + DC bias; here the camera sees intensity only).
  - Detection thresholds (and optionally M in {2,4,8}) are tuned on TUNE_SEED; equal average
    power across schemes is applied by the harness (experiments.common.power_scales), not here.
  - Positioning / radical-axis / dimming-coefficient estimation from the paper are out of scope;
    this plugin is the SM-PAM communication mapping only.
"""
import numpy as np
from occbench import register
from tx.schemes import Scheme, DATA_POS, base_drive, b2i, i2b
from rx.refs import refs, on_metric

def _levels(M):
    """Positive optical PAM levels in (0, 1], spaced as (2m-1)/(2M-1)."""
    return np.array([(2 * m - 1) / (2 * M - 1) for m in range(1, M + 1)], float)

def _default_thresholds(M):
    """Midpoints between consecutive levels (in intensity units)."""
    lv = _levels(M); return 0.5 * (lv[:-1] + lv[1:])

@register
class SMPAMLeblebici(Scheme):
    name = 'SM-PAM-inspired (Leblebici et al., PhyCom 2026, doi:10.1016/j.phycom.2026.103205)'
    def __init__(self, M=4, group=4, thresholds=None):
        assert group in (2, 4, 8) and (len(DATA_POS) % group) == 0
        assert M in (2, 4, 8)
        self.M = int(M); self.group = int(group)
        self.n_groups = len(DATA_POS) // group
        self.b_idx = int(np.log2(group)); self.b_pam = int(np.log2(M))
        self.b_grp = self.b_idx + self.b_pam
        self.levels = _levels(self.M)
        self.thresholds = np.asarray(thresholds if thresholds is not None else _default_thresholds(self.M), float)
        assert self.thresholds.shape == (self.M - 1,)
        self.layers = [('all', self.n_groups * self.b_grp)]
        self.groups = [DATA_POS[i * group:(i + 1) * group] for i in range(self.n_groups)]
    def set_thresholds(self, thr):
        self.thresholds = np.asarray(thr, float); assert self.thresholds.shape == (self.M - 1,)
    def encode(self, bits):
        d = base_drive()
        for g, pos in enumerate(self.groups):
            bb = bits[g * self.b_grp:(g + 1) * self.b_grp]
            idx = b2i(bb[:self.b_idx]); lev = b2i(bb[self.b_idx:])
            a = float(self.levels[lev])
            for j, p in enumerate(pos):
                d[p] = (a, a, a) if j == idx else (0.0, 0.0, 0.0)
        return d
    def decode(self, s, dark):
        Mref, dk = refs(s, dark); x = on_metric(s, Mref, dk)
        out = []
        for pos in self.groups:
            soft = np.array([x[p] for p in pos], float)
            idx = int(np.argmax(soft)); amp = float(soft[idx])
            # quantise amplitude against tuned thresholds
            lev = int(np.searchsorted(self.thresholds, amp))
            lev = max(0, min(self.M - 1, lev))
            out.extend(i2b(idx, self.b_idx)); out.extend(i2b(lev, self.b_pam))
        return out
