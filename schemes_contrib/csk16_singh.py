"""CSK-16-inspired (Singh et al., Physical Communication 2018).

Inspired by: R. Singh, T. O'Farrell, M. Biagi, J. P. R. David, "Coded color shift keying with
frequency domain equalization for low complexity energy efficient indoor visible light
communications," Phys. Commun. 31:160-168, 2018. doi:10.1016/j.phycom.2018.04.026

Not a reproduction. Adaptations for this 8x8 RGB-LED camera-OCC harness:
  - 16-CSK per data LED, IEEE 802.15.7-style constant-power constraint (drive sums to 1).
  - Constellation is redefined directly in camera RGB (stick-breaking lattice on the R+G+B=1
    simplex), not CIE-xy; ML decode uses the shared pilot colour references.
  - Corner pilots kept (finder + colour refs).
  - Optional rate-1/2 K=3 binary convolutional code (CC1/2) packs 118 info bits + 2
    termination bits into 60 LEDs x 4 coded bits = 240 (<= 256 bit budget).
  - Frequency-domain equalisation (FDE) is not applicable: each OCC symbol is a single camera
    frame with no temporal ISI to equalise.
"""
import numpy as np
from occbench import register
from tx.schemes import Scheme, DATA_POS, base_drive, b2i, i2b
from rx.refs import refs, classify

def _csk16_palette():
    """16 constant-power RGB drives covering the simplex (camera-RGB redesign of 16-CSK)."""
    out = []
    for i in range(4):
        for j in range(4):
            u, v = (i + 0.5) / 4.0, (j + 0.5) / 4.0
            r = u; g = (1.0 - u) * v; b = (1.0 - u) * (1.0 - v)
            s = r + g + b; out.append((r / s, g / s, b / s))
    return out

# Rate-1/2, constraint length K=3, generators g = (0b111, 0b101); hard-decision Viterbi.
_G = (0b111, 0b101)
_NSTATE = 4   # K-1 = 2 memory bits

def _encode_cc(bits):
    state, out = 0, []
    for b in bits:
        reg = ((state << 1) | int(b)) & 0b111
        out.extend(bin(reg & g).count('1') & 1 for g in _G)
        state = reg & 0b011
    return out, state

def _decode_cc(coded, n_info):
    """Hard Viterbi; len(coded) == 2*n_info (n_info includes any termination bits)."""
    assert len(coded) == 2 * n_info
    INF = 10 ** 9; pm = [0] + [INF] * (_NSTATE - 1); parents = []
    for t in range(n_info):
        r0, r1 = int(coded[2 * t]), int(coded[2 * t + 1]); npm = [INF] * _NSTATE; par = [None] * _NSTATE
        for s in range(_NSTATE):
            if pm[s] >= INF: continue
            for bit in (0, 1):
                reg = ((s << 1) | bit) & 0b111
                exp = [bin(reg & g).count('1') & 1 for g in _G]
                ns = reg & 0b011; cost = pm[s] + (exp[0] != r0) + (exp[1] != r1)
                if cost < npm[ns]: npm[ns] = cost; par[ns] = (s, bit)
        pm = npm; parents.append(par)
    s = int(np.argmin(pm)); bits = [0] * n_info
    for t in range(n_info - 1, -1, -1):
        s, bit = parents[t][s]; bits[t] = bit
    return bits

@register
class CSK16Singh(Scheme):
    name = 'CSK-16-inspired (Singh et al., PhyCom 2018, doi:10.1016/j.phycom.2018.04.026)'
    def __init__(self, coded=True):
        self.coded = coded; self.palette = _csk16_palette(); self.bps = 4
        self.n_led_bits = self.bps * len(DATA_POS)           # 240
        if coded:
            self.n_info = 118; self.layers = [('all', self.n_info)]   # +2 term -> 240 coded
        else:
            self.n_info = self.n_led_bits; self.layers = [('all', self.n_led_bits)]
    def encode(self, bits):
        if self.coded:
            coded, _ = _encode_cc(list(bits) + [0, 0])
            assert len(coded) == self.n_led_bits
        else:
            coded = list(bits)
        d = base_drive()
        for i, p in enumerate(DATA_POS):
            d[p] = self.palette[b2i(coded[i * self.bps:(i + 1) * self.bps])]
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark)
        idx = classify(np.array([s[p] for p in DATA_POS]), self.palette, M, dk)
        coded = sum((i2b(i, self.bps) for i in idx), [])
        if not self.coded: return coded
        return _decode_cc(coded, self.n_info + 2)[:self.n_info]
