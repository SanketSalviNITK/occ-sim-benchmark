"""Reviewer-requested ablation (review_vtc.md M1). Additive module: no existing scheme is changed.

HNCSMv2BaseOnly = the HNCSM v2 transmitter with the enhancement layer removed: same 12 colour-balanced 2x2 cells and the
same 16 permutations ('first16') as HNCSM v2, every lit LED at one fixed level (1.0 before the equal-power scale), 48 base
bits + the usual CRC. Decoder = ML over the 16 arrangements at that single level (no intensity hypothesis).
NOTE: this is QCD-style with the 'first16' subset; the physical line-up's QCD-style uses the tuned 'maxdist-0' subset,
so the two differ only in the permutation subset."""
from tx.schemes import QCDStyle

class HNCSMv2BaseOnly(QCDStyle):
    name = 'HNCSM v2-base-only'
    layers = [('base', 48)]
    def __init__(self): super().__init__('first16')

# ---- decomposition variants (diagnostic only; NOT part of lineup_r1) -------------------------------------------------
import numpy as np
from tx.schemes import R, G, B, K, refs, i2b, base_drive, b2i

class BaseOnly2LevelDecoder(HNCSMv2BaseOnly):
    """Same transmitter as v2-base-only (all lit LEDs at 1.0); decoder = HNCSM v2's joint ML with the per-LED level
    hypothesis {0.5, 1.0} (min over levels), base bits only. Isolates v2's decoder from its enhancement signalling."""
    name = 'HNCSM v2-base-only [2-level dec]'
    ALPHA = 0.5
    def decode(self, s, dark):
        M, dk = refs(s, dark); out = []
        E = {col: [dk + a * (M @ np.array(col, float)) for a in (self.ALPHA, 1.0)] for col in (R, G, B, K)}
        for cell in self.cells:
            v = [s[p] for p in self._pos(cell)]
            cost = [sum(min(((v[j] - x) ** 2).sum() for x in E[a[j]]) for j in range(4)) for a in self.arr]
            out += i2b(int(np.argmin(cost)), 4)
        return out

class BaseOnlyLevel075(HNCSMv2BaseOnly):
    """v2-base-only with every lit LED at 0.75 (= v2's mean lit level), pilots at full drive, so the native power and
    hence the equal-power scale equal v2's; single-level ML at 0.75. Isolates v2's pilot-to-data brightness ratio."""
    name = 'HNCSM v2-base-only [lit 0.75]'
    LV = 0.75
    def encode(self, bits):
        d = base_drive()
        for k, cell in enumerate(self.cells):
            for p, col in zip(self._pos(cell), self.arr[b2i(bits[4*k:4*k+4])]): d[p] = np.array(col, float) * self.LV
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); out = []
        E = {col: dk + self.LV * (M @ np.array(col, float)) for col in (R, G, B, K)}
        for cell in self.cells:
            v = np.array([s[p] for p in self._pos(cell)])
            cost = [sum(((v[j] - E[a[j]]) ** 2).sum() for j in range(4)) for a in self.arr]
            out += i2b(int(np.argmin(cost)), 4)
        return out
