"""Per-symbol statistics for the physical channel (audit r1, B3/B5).
- cluster_ber: BER with a symbol(frame)-cluster bootstrap CI (bit errors within a symbol are correlated).
- sym_goodput: per-symbol net goodput contribution (layers or fixed-size CRC blocks), so that mean = goodput.
- paired_diff: paired (CRN) bootstrap CI of mean(A) - mean(B) over the SAME symbol indices.
- paired_auc_diff: paired bootstrap of the trapezoid AUC difference over a distance grid; symbols are resampled
  independently per grid point (points use independent seeds) but jointly for A and B (CRN)."""
import numpy as np

CRC_BITS = 8
B_DEFAULT = 2000

def cluster_ber(err, B=B_DEFAULT, seed=0):
    err = np.asarray(err); F = err.shape[0]; per = err.reshape(F, -1).sum(1); nb = err.reshape(F, -1).shape[1]
    r = np.random.RandomState(seed); idx = r.randint(0, F, (B, F))
    bs = per[idx].sum(1) / (F * nb)
    return per.sum() / (F * nb), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

def sym_goodput(err, layers, rate, block=None):
    """err: F x nbits bit-error matrix. layers: [(name, n)]. block: if set, the payload is re-segmented into blocks of
    `block` bits each charged a CRC-8 (last block may be shorter), ignoring the scheme's own layering."""
    err = np.asarray(err); F, n = err.shape
    seg = [(i, min(i + block, n)) for i in range(0, n, block)] if block else \
          [(a, a + m) for a, m in zip(np.cumsum([0] + [m for _, m in layers])[:-1], [m for _, m in layers])]
    g = np.zeros(F)
    for a, b in seg:
        g += max(b - a - CRC_BITS, 0) * rate * (err[:, a:b].sum(1) == 0)
    return g

def boot_ci(x, B=B_DEFAULT, seed=0):
    x = np.asarray(x, float); r = np.random.RandomState(seed); idx = r.randint(0, len(x), (B, len(x)))
    m = x[idx].mean(1); return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

def paired_diff(a, b, B=B_DEFAULT, seed=0):
    """CI of mean(a - b) with a, b per-symbol values on the same CRN symbols."""
    a = np.asarray(a, float); b = np.asarray(b, float); assert a.shape == b.shape
    return boot_ci(a - b, B, seed)

def auc(x, y): return float(np.trapezoid(y, x))

def paired_auc_diff(x, A, Bm, B=B_DEFAULT, seed=0):
    """x: grid; A, Bm: lists (per grid point) of per-symbol goodput arrays (paired within a point).
    Returns (auc_A, auc_B, diff, lo, hi, auc_A_lo, auc_A_hi)."""
    r = np.random.RandomState(seed); da = np.zeros(B); aa = np.zeros(B); ab = np.zeros(B)
    ma, mb = [], []
    for k, (a, b) in enumerate(zip(A, Bm)):
        a = np.asarray(a, float); b = np.asarray(b, float); idx = r.randint(0, len(a), (B, len(a)))
        ma.append(a[idx].mean(1)); mb.append(b[idx].mean(1))
    ma, mb = np.array(ma), np.array(mb)                       # points x B
    ra = np.trapezoid(ma, x, axis=0); rb = np.trapezoid(mb, x, axis=0); d = ra - rb
    A0 = auc(x, [np.mean(a) for a in A]); B0 = auc(x, [np.mean(b) for b in Bm])
    return A0, B0, A0 - B0, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), float(np.percentile(ra, 2.5)), float(np.percentile(ra, 97.5))
