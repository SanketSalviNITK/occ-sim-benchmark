"""Modulation schemes on an 8x8 RGB LED matrix. Each scheme: layers [(name, nbits)], encode(bits)->drive (8x8x3 in [0,1]),
decode(samples, dark)->bits. All schemes reserve the same 4 corner pilots (TL W, TR R, BL G, BR B) which double as
finder/colour references, so overhead is comparable. See README for assumptions behind re-implementations."""
import itertools, numpy as np
from rx.refs import PILOT_POS, PILOT_SET, refs, on_metric, classify

N = 8
W, R, G, B, K = (1, 1, 1), (1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0)
Y, C, Mg = (1, 1, 0), (0, 1, 1), (1, 0, 1)
DATA_POS = [(r, c) for r in range(N) for c in range(N) if (r, c) not in PILOT_SET]

def b2i(b): return int(''.join(map(str, b)), 2) if len(b) else 0
def i2b(v, n): return [int(x) for x in format(int(v), f'0{n}b')]

def base_drive():
    d = np.zeros((N, N, 3))
    for p, col in PILOT_POS.items(): d[p] = col
    return d

def best_codebook(npos, size, weight=None, iters=4000, seed=0):
    """Greedy/random search for a binary codebook with large minimum Hamming distance."""
    rng = np.random.default_rng(seed)
    if weight is None:
        cands = np.array(list(itertools.product([0, 1], repeat=npos)))
    else:
        cands = np.array([[1 if i in s else 0 for i in range(npos)] for s in itertools.combinations(range(npos), weight)])
    best, bestd = None, -1
    for _ in range(60):
        idx = [rng.integers(len(cands))]
        dmin = np.full(len(cands), npos + 1)
        for _ in range(size - 1):
            dmin = np.minimum(dmin, (cands != cands[idx[-1]]).sum(1))
            idx.append(int(np.argmax(dmin + rng.random(len(cands)) * 0.1)))
        cb = cands[idx]
        dd = min((cb[i] != cb[j]).sum() for i in range(size) for j in range(i + 1, size))
        if dd > bestd: best, bestd = cb, dd
    return best, bestd

class Scheme:
    name = ''; layers = []
    @property
    def nbits(self): return sum(n for _, n in self.layers)

# ---------------------------------------------------------------- baselines
class OOK(Scheme):
    """Binary spatial OOK (MIMO-OOK, LiCamIoT-like): white LED on/off, 1 bit per data LED."""
    name = 'OOK-8x8'; layers = [('all', len(DATA_POS))]
    def encode(self, bits):
        d = base_drive()
        for p, b in zip(DATA_POS, bits): d[p] = (b, b, b)
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); x = on_metric(s, M, dk)
        return [int(x[p] > 0.5) for p in DATA_POS]

class CSK(Scheme):
    """Per-LED colour keying with an RGB-cube palette (8 colours = 3 bits, or {K,R,G,B} = 2 bits).
    NOTE: RGB-LED 'digital CSK' approximation, not IEEE 802.15.7 CIE-xy CSK (see README)."""
    def __init__(self, order=8):
        self.order = order
        self.palette = [K, R, G, B, Y, C, Mg, W][:order] if order == 8 else [K, R, G, B]
        self.bps = int(np.log2(order)); self.name = f'CSK-{order}'
        self.layers = [('all', self.bps * len(DATA_POS))]
    def encode(self, bits):
        d = base_drive()
        for i, p in enumerate(DATA_POS): d[p] = self.palette[b2i(bits[i*self.bps:(i+1)*self.bps])]
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark)
        idx = classify(np.array([s[p] for p in DATA_POS]), self.palette, M, dk)
        return sum((i2b(i, self.bps) for i in idx), [])

HAM_G = np.array([[1,0,0,0,1,1,0],[0,1,0,0,1,0,1],[0,0,1,0,0,1,1],[0,0,0,1,1,1,1]])
HAM_H = np.array([[1,1,0,1,1,0,0],[1,0,1,1,0,1,0],[0,1,1,1,0,0,1]])
class QRStyle(Scheme):
    """QR/Aztec-style binary module code: 2x2 finder blocks in TL/TR/BL (incl. pilots), BR pilot, white modules,
    Hamming(7,4) FEC on 49 data modules -> 28 info bits, hard-decision syndrome decoding."""
    name = 'QR/Aztec-style'
    def __init__(self):
        fz = {(r, c) for r0, c0 in [(0, 0), (0, 6), (6, 0)] for r in (r0, r0+1) for c in (c0, c0+1)}
        self.finder = fz - PILOT_SET
        self.pos = [p for p in DATA_POS if p not in self.finder][:49]
        self.layers = [('all', 28)]
    def encode(self, bits):
        d = base_drive()
        for p in self.finder: d[p] = W
        cw = np.concatenate([(np.array(bits[i*4:(i+1)*4]) @ HAM_G) % 2 for i in range(7)])
        for p, b in zip(self.pos, cw): d[p] = (b, b, b)
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); x = on_metric(s, M, dk)
        cw = np.array([int(x[p] > 0.5) for p in self.pos]); out = []
        for i in range(7):
            v = cw[i*7:(i+1)*7].copy(); syn = (HAM_H @ v) % 2
            if syn.any():
                j = np.where((HAM_H.T == syn).all(1))[0]
                if len(j): v[j[0]] ^= 1
            out += list(v[:4])
        return out

QUADS = [(0, 0), (0, 4), (4, 0), (4, 4)]
def quad_positions(q):
    r0, c0 = q
    return [(r0+r, c0+c) for r in range(4) for c in range(4) if (r0+r, c0+c) not in PILOT_SET]

class NestedTexture(Scheme):
    """Re-implementation (from abstract) of Salvi & Geetha, IEEE Access 2022: each 4x4 quadrant = outer ring pattern
    (16-word codebook on ring LEDs) nested with an inner 2x2 pattern (16 words); outer and inner matched
    independently by minimum-distance template matching on soft on-values. 4 quads x (4+4) = 32 bits."""
    name = 'NestedTexture-inspired (Salvi22)'
    layers = [('outer', 16), ('inner', 16)]
    def __init__(self):
        self.ring = {q: [p for p in quad_positions(q) if not (q[0]+1 <= p[0] <= q[0]+2 and q[1]+1 <= p[1] <= q[1]+2)] for q in QUADS}
        self.inner = {q: [(q[0]+1, q[1]+1), (q[0]+1, q[1]+2), (q[0]+2, q[1]+1), (q[0]+2, q[1]+2)] for q in QUADS}
        self.cb_out, self.dout = best_codebook(11, 16, seed=1)
        self.cb_in = np.array(list(itertools.product([0, 1], repeat=4)))
    def encode(self, bits):
        d = base_drive()
        for k, q in enumerate(QUADS):
            for p, b in zip(self.ring[q], self.cb_out[b2i(bits[4*k:4*k+4])]): d[p] = (b, b, b)
            for p, b in zip(self.inner[q], self.cb_in[b2i(bits[16+4*k:16+4*k+4])]): d[p] = (b, b, b)
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); x = on_metric(s, M, dk); o, i = [], []
        for q in QUADS:
            v = np.array([x[p] for p in self.ring[q]]); o += i2b(((v - self.cb_out) ** 2).sum(1).argmin(), 4)
            v = np.array([x[p] for p in self.inner[q]]); i += i2b(((v - self.cb_in) ** 2).sum(1).argmin(), 4)
        return o + i

class QCDStyle(Scheme):
    """Re-implementation (QCD-inspired, from abstract) of Vasantha & Salvi, Appl. Sci. 2022: 2x2 'hadron' cells must be
    colour-neutral: each cell holds one R, one G, one B and one dark LED (24 arrangements, 16 used = 4 bits/cell).
    Cells containing a corner pilot are excluded -> 12 cells = 48 bits. Decoder: ML over the 16 arrangements using
    pilot-referenced expected colours (rotation-agnostic cell structure)."""
    name = 'QCD-style-inspired (Vasantha22)'
    layers = [('all', 48)]
    def __init__(self, subset='first16'):
        self.subset = subset
        self.cells = [(r, c) for r in range(0, 8, 2) for c in range(0, 8, 2) if (r, c) not in [(0, 0), (0, 6), (6, 0), (6, 6)]]
        perms = list(itertools.permutations([R, G, B, K]))
        if subset == 'first16': self.arr = perms[:16]
        elif subset == 'last16': self.arr = perms[-16:]
        else:  # 'maxdist-<seed>': greedy subset maximising min #LED positions that differ
            rng = np.random.default_rng(int(subset.split('-')[1])); idx = [int(rng.integers(24))]
            dist = lambda a, b: sum(x != y for x, y in zip(perms[a], perms[b]))
            while len(idx) < 16:
                rest = [i for i in range(24) if i not in idx]
                sc = [min(dist(i, j) for j in idx) + rng.random() * 0.1 for i in rest]
                idx.append(rest[int(np.argmax(sc))])
            self.arr = [perms[i] for i in idx]
    def _pos(self, cell): r, c = cell; return [(r, c), (r, c+1), (r+1, c), (r+1, c+1)]
    def encode(self, bits):
        d = base_drive()
        for k, cell in enumerate(self.cells):
            for p, col in zip(self._pos(cell), self.arr[b2i(bits[4*k:4*k+4])]): d[p] = col
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); out = []
        E = {col: dk + M @ np.array(col, float) for col in (R, G, B, K)}
        for cell in self.cells:
            v = np.array([s[p] for p in self._pos(cell)])
            cost = [sum(((v[j] - E[a[j]]) ** 2).sum() for j in range(4)) for a in self.arr]
            out += i2b(int(np.argmin(cost)), 4)
        return out

class Nishimoto(Scheme):
    """Overlay coding after Nishimoto et al. 2012 (GLOCOMW, doi:10.1109/GLOCOMW.2012.6477757), assumptions from the
    abstract-level description: monochrome intensity; layer-1 (low spatial frequency) = 1 bit per 2x2 block as block mean
    level; layer-2 (high spatial frequency) = zero-mean balanced +/- pattern inside each block (4 patterns = 2 bits)
    overlaid at lower amplitude. Intensity = 0.5 + 0.3*s1 + 0.2*s2 (levels 0,0.4,0.6,1). Blocks with corner pilots
    excluded -> 12 blocks. Distance-graded decoding: L1 from block mean (survives blur), L2 from residual correlation."""
    name = 'Overlay-inspired (Nishimoto12)'
    layers = [('L1', 12), ('L2', 24)]
    P2 = np.array([[1, 1, -1, -1], [-1, -1, 1, 1], [1, -1, 1, -1], [-1, 1, -1, 1]], float)
    def __init__(self, a1=0.3, a2=0.2):
        self.a1, self.a2 = a1, a2   # intensity = 0.5 + a1*s1 + a2*s2, a1 + a2 <= 0.5
        self.cells = QCDStyle().cells
    def _pos(self, cell): r, c = cell; return [(r, c), (r, c+1), (r+1, c), (r+1, c+1)]
    def encode(self, bits):
        d = base_drive()
        for k, cell in enumerate(self.cells):
            s1 = 2 * bits[k] - 1; s2 = self.P2[b2i(bits[12+2*k:14+2*k])]
            for p, v in zip(self._pos(cell), 0.5 + self.a1 * s1 + self.a2 * s2): d[p] = (v, v, v)
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark)
        wl = (s - dk).sum(-1) / max((M.sum(1)).sum(), 1e-6)   # luminance normalised to white pilot
        l1, l2 = [], []
        for cell in self.cells:
            v = np.array([wl[p] for p in self._pos(cell)]); m = v.mean()
            l1.append(int(m > 0.5)); l2 += i2b(int(np.argmax(self.P2 @ (v - m))), 2)
        return l1 + l2

# ---------------------------------------------------------------- proposed
class HNCSM(Scheme):
    """Hierarchical Nested Colour-Spatial Modulation. Base: per 4x4 quadrant a constant-weight (8 of 15) binary texture
    from a 16-word max-distance codebook (4 bits). Enhancement: each lit LED takes a colour from {W,R,G,B} (2 bits).
    Bits/frame = 4*4 + 4*8*2 = 80. Decoder: base by ML template match on on-values; enhancement by pilot-referenced
    nearest-colour on the LEDs the decoded texture says are lit."""
    PAL = [W, R, G, B]
    def __init__(self, base_only=False):
        self.base_only = base_only
        self.cb, self.dmin = best_codebook(15, 16, weight=8, seed=2)
        self.name = 'HNCSM base-only' if base_only else 'HNCSM'
        self.layers = [('base', 16)] + ([] if base_only else [('enh', 64)])
    def encode(self, bits):
        d = base_drive()
        for k, q in enumerate(QUADS):
            word = self.cb[b2i(bits[4*k:4*k+4])]; lit = [p for p, b in zip(quad_positions(q), word) if b]
            for j, p in enumerate(lit):
                d[p] = W if self.base_only else self.PAL[b2i(bits[16+16*k+2*j:16+16*k+2*j+2])]
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); x = on_metric(s, M, dk); base, enh = [], []
        for q in QUADS:
            pos = quad_positions(q); v = np.array([x[p] for p in pos])
            w = int(((v - self.cb) ** 2).sum(1).argmin()); base += i2b(w, 4)
            if not self.base_only:
                lit = [p for p, b in zip(pos, self.cb[w]) if b]
                idx = classify(np.array([s[p] for p in lit]), self.PAL, M, dk)
                enh += sum((i2b(i, 2) for i in idx), [])
        return base + enh


class HNCSMv2(Scheme):
    """HNCSM v2. Base layer = QCD-style colour-balanced 2x2 cells (one R, G, B, dark LED; 16 of 24 permutations =
    4 bits/cell, 12 non-pilot cells = 48 bits). Enhancement = per-LED intensity offset on each of the 3 lit LEDs of a
    cell: full (1.0) or dimmed (ALPHA) = 1 bit/LED = 36 bits. Total 84 bits/frame.
    Decoder: joint ML per cell; per-LED min over the two intensity levels is separable, so base = argmin over 16
    arrangements of sum_j min_a ||s_j - (dark + a*M c_j)||^2, and enhancement = the minimising level per lit LED.
    Hierarchy: dimming keeps chromaticity, so base (which colour where) survives when the intensity bits fail."""
    ALPHA = 0.5
    name = 'HNCSM v2'
    layers = [('base', 48), ('enh', 36)]
    def __init__(self):
        q = QCDStyle(); self.cells, self.arr, self._pos = q.cells, q.arr, q._pos
    def encode(self, bits):
        d = base_drive(); e = 48
        for k, cell in enumerate(self.cells):
            for p, col in zip(self._pos(cell), self.arr[b2i(bits[4*k:4*k+4])]):
                if col != K:
                    col = np.array(col, float) * (1.0 if bits[e] else self.ALPHA); e += 1
                d[p] = col
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); base, enh = [], []
        E = {col: [dk + a * (M @ np.array(col, float)) for a in (self.ALPHA, 1.0)] for col in (R, G, B, K)}
        for cell in self.cells:
            v = [s[p] for p in self._pos(cell)]; best = None
            for ai, a in enumerate(self.arr):
                c, lv = 0.0, []
                for j in range(4):
                    dd = [((v[j] - x) ** 2).sum() for x in E[a[j]]]; i = int(np.argmin(dd)); c += dd[i]
                    if a[j] != K: lv.append(i)
                if best is None or c < best[0]: best = (c, ai, lv)
            base += i2b(best[1], 4); enh += best[2]
        return base + enh


class HNCSMv2CS(Scheme):
    """HNCSM v2-CS. Base = QCD-style colour-balanced 2x2 cells (48 bits, identical to QCD-style/v2).
    Enhancement = colour shift within each lit LED's assigned primary, primary channel kept at FULL drive:
      bpl=1: {pure c, c + delta*next}                         (next primary cyclic R->G->B->R)
      bpl=2: {pure c, c + delta*next, c + delta*prev, c + delta*(next+prev)}
    so 36 (bpl=1) or 72 (bpl=2) enhancement bits. Leak adds delta (or 2*delta) of extra emitted power instead of
    reducing the primary (approximately equal-luminance only for small delta; see README). Decoder: joint per-cell ML
    over 16 arrangements x per-LED variants (separable min), base = arrangement, enh = variant index."""
    NEXT = {R: G, G: B, B: R}; PREV = {R: B, G: R, B: G}
    def __init__(self, delta=0.2, bpl=1, joint=True, subset='first16'):
        self.joint = joint
        q = QCDStyle(subset); self.cells, self.arr, self._pos = q.cells, q.arr, q._pos
        self.delta, self.bpl = delta, bpl
        self.name = f'HNCSM v2-CS (d={delta},{bpl}b' + (',joint)' if joint else ')')
        self.layers = [('base', 48), ('enh', 36 * bpl)]
    def variants(self, c):
        # power-neutral: leaked power is taken from the primary, so every variant has channel-sum 1
        c0, n, p = np.array(c, float), np.array(self.NEXT[c], float), np.array(self.PREV[c], float); d = self.delta
        v = [c0, (1 - d) * c0 + d * n]
        if self.bpl == 2: v += [(1 - d) * c0 + d * p, (1 - 2 * d) * c0 + d * (n + p)]
        return v
    def encode(self, bits):
        d = base_drive(); e = 48
        for k, cell in enumerate(self.cells):
            for p, col in zip(self._pos(cell), self.arr[b2i(bits[4*k:4*k+4])]):
                if col != K:
                    col = self.variants(col)[b2i(bits[e:e+self.bpl])]; e += self.bpl
                d[p] = col
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); base, enh = [], []
        E = {col: [dk + M @ v for v in self.variants(col)] for col in (R, G, B)}; E[K] = [dk]
        for cell in self.cells:
            v = [s[p] for p in self._pos(cell)]
            # per-LED, per-colour best variant cost (cache)
            cc = [{col: [((v[j] - x) ** 2).sum() for x in E[col]] for col in E} for j in range(4)]
            best = None
            for ai, a in enumerate(self.arr):
                # joint=True (default): base uses leaked templates (min over variants); joint=False: pure-primary templates first
                c = sum((min(cc[j][a[j]]) if self.joint else cc[j][a[j]][0]) for j in range(4))
                if best is None or c < best[0]: best = (c, ai)
            a = self.arr[best[1]]; base += i2b(best[1], 4)
            for j in range(4):
                if a[j] != K: enh += i2b(int(np.argmin(cc[j][a[j]])), self.bpl)
        return base + enh


import json, os
_TUNED = os.path.join(os.path.dirname(__file__), '..', 'results', 'tuned_params.json')

def tuned_params():
    """Tuned on held-out seeds by experiments/tune.py (equal budget for v2-CS, QCD-style and overlay)."""
    if os.path.exists(_TUNED):
        return json.load(open(_TUNED))
    return {'v2cs': {'delta': 0.2, 'bpl': 2}, 'qcd': {'subset': 'first16'}, 'overlay': {'a1': 0.3, 'a2': 0.2}}

def all_schemes(tuned=None):
    t = tuned or tuned_params()
    v = HNCSMv2CS(t['v2cs']['delta'], t['v2cs']['bpl']); v.name = 'HNCSM v2-CS'
    return [v, HNCSMv2(), HNCSM(), HNCSM(base_only=True), CSK(8), CSK(4), OOK(), QRStyle(), NestedTexture(),
            QCDStyle(**t['qcd']), Nishimoto(**t['overlay'])]


# ---------------------------------------------------------------- IEEE 802.15.7 CSK (physical channel)
# Design-rule constellations of IEEE Std 802.15.7 (CSK, clause 'CSK constellation design rules'), taken from the TG7
# example for band combination 110-010-000: I=(0.730,0.270), J=(0.190,0.780), K=(0.180,0.010); 4-CSK = {J, centroid,
# K, I}; 8-CSK points as listed (P802.15 contribution by Son/Bae/Rajagopal/Yokoi/Won, May 2010). The rule is affine, so
# the barycentric coordinates of each point in triangle IJK are transferred to the triangle of our LEDs (I->R, J->G, K->B).
_I, _J, _K = (0.730, 0.270), (0.190, 0.780), (0.180, 0.010)
CSK802_PTS = {4: [(0.190, 0.780), (0.367, 0.353), (0.180, 0.010), (0.730, 0.270)],
              8: [(0.190, 0.780), (0.187, 0.523), (0.370, 0.610), (0.519, 0.383), (0.180, 0.010), (0.244, 0.253),
                  (0.455, 0.140), (0.730, 0.270)]}

def _bary(pt, a, b, c):
    T = np.array([[a[0] - c[0], b[0] - c[0]], [a[1] - c[1], b[1] - c[1]]])
    l1, l2 = np.linalg.solve(T, np.array(pt) - np.array(c)); return np.array([l1, l2, 1 - l1 - l2])

def csk802_drives(order, xy_led, Iv):
    """Return per-symbol RGB drive (sum of drive = 1: constant total drive, the CSK constant-power constraint).
    Chromaticity mixing: weight in xy of LED j is proportional to its X+Y+Z = Y_j / y_j = a_j Iv_j / y_j."""
    out = []
    for pt in CSK802_PTS[order]:
        wI, wJ, wK = np.clip(_bary(pt, _I, _J, _K), 0, None)
        w = np.array([wI, wJ, wK])                                   # weights for R, G, B LEDs
        S = np.array([Iv[j] / xy_led[j][1] for j in range(3)])       # X+Y+Z per unit drive
        a = w / S; a = a / a.sum(); out.append(tuple(a))
    return out

class CSK802(Scheme):
    """IEEE 802.15.7 CIE-xy CSK (4 or 8) on each of the 60 data LEDs; ML decoding in sensor RGB space using
    pilot-referenced templates b + M a (M from the R/G/B pilots)."""
    def __init__(self, order=8):
        from channel.physical import P as PP
        self.order = order; self.bps = int(np.log2(order)); self.name = f'CSK802-{order}'
        self.palette = csk802_drives(order, PP['xy'], PP['Iv_cd'])
        self.layers = [('all', self.bps * len(DATA_POS))]
    def encode(self, bits):
        d = base_drive()
        for i, p in enumerate(DATA_POS): d[p] = self.palette[b2i(bits[i*self.bps:(i+1)*self.bps])]
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark)
        idx = classify(np.array([s[p] for p in DATA_POS]), self.palette, M, dk)
        return sum((i2b(i, self.bps) for i in idx), [])

class QCDOCC(Scheme):
    """Validation-only re-implementation of the QCD-OCC prototype frame (Vasantha & Salvi 2022, Table 1 + Sec. 3.1):
    48 data LEDs x 3 bits (RGB on/off = baryon colour model), the four corner 2x2 blocks are anchors (here: the shared
    corner pilots + the other 12 anchor LEDs white; anchor values are ASSUMED). Decoder: nearest colour."""
    name = 'QCD-OCC (paper frame)'
    PAL = [K, B, G, C, R, Mg, Y, W]   # bits b2 b1 b0 = R G B presence (Table 1)
    def __init__(self):
        anc = {(r, c) for r0, c0 in [(0, 0), (0, 6), (6, 0), (6, 6)] for r in (r0, r0 + 1) for c in (c0, c0 + 1)}
        self.anchor = anc - PILOT_SET; self.pos = [p for p in DATA_POS if p not in anc]
        assert len(self.pos) == 48
        self.layers = [('all', 144)]
    def encode(self, bits):
        d = base_drive()
        for p in self.anchor: d[p] = W
        for i, p in enumerate(self.pos): d[p] = self.PAL[b2i(bits[3*i:3*i+3])]
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark)
        idx = classify(np.array([s[p] for p in self.pos]), self.PAL, M, dk)
        return sum((i2b(i, 3) for i in idx), [])

class QCDOCCWin6(QCDOCC):
    """benchmark-r9 OPT-IN corrected QCD-OCC receiver (reviewer must-fix 2). Identical frame, encoder and nearest-colour
    decision; only the per-LED sampling window is 6x6 instead of 4x4 canonical px (G = 8 px per LED). Root cause of the
    r7/r8 ~1.5e-2 floor: at 2 m the LED pitch is ~4.2 sensor px and the lit disc ~2.5 px, so a 4x4 canonical window
    covers only ~2x2 sensor px, i.e. ~1 R and ~1 B Bayer site; Malvar-He-Cutler interpolation of the sparse R/B planes
    then gives a phase-dependent colour error that is proportional to signal (brightness-independent). R is worst
    (lowest QE x CFA response). Noise-free (no shot/read noise, no clipping) it alone gives 1.88e-2 BER, 77 % R-bit.
    The default QCDOCC is unchanged so all earlier numbers stay reproducible."""
    name = 'QCD-OCC (paper frame, win6 rx)'
    sample_win = 6

def all_schemes_phys(tuned=None):
    """Same line-up as all_schemes(), with the RGB-keying CSK baselines replaced by IEEE 802.15.7 CIE-xy CSK."""
    if tuned is None:
        f = _TUNED.replace('tuned_params.json', 'tuned_params_phys.json')
        tuned = json.load(open(f)) if os.path.exists(f) else None    # physical-channel held-out tuning (tune.py --channel physical)
    s = [x for x in all_schemes(tuned) if not x.name.startswith('CSK-')]
    return s[:4] + [CSK802(8), CSK802(4)] + s[4:]
