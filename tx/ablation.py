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
