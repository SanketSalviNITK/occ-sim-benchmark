"""Scheme registry (additive; does not change any existing line-up or result).

Scheme interface (duck-typed, same as tx.schemes.Scheme):
  name   : str, unique
  layers : list[(layer_name, nbits)]; nbits = sum of layer sizes (<= 256)
  encode(bits: list[int]) -> np.ndarray (8, 8, 3) drive in [0, 1]; the 4 corner pilots (rx.refs.PILOT_POS) must be kept,
         because the finder and colour references use them. Power is equalised later by experiments.common.power_scales.
  decode(samples: np.ndarray (8, 8, 3), dark: np.ndarray (3,)) -> list[int] of length nbits
         samples = per-LED mean DN at the rectified LED centres; dark = gap level.
Register with @register (class) or register(factory, name); built-ins are registered lazily from the paper line-up.
Plugins are single .py files in schemes_contrib/ (or any directory passed to load_plugins)."""
import os, importlib.util, numpy as np
from rx.refs import PILOT_POS

_REG = {}; _BUILTINS = False

def register(obj=None, name=None):
    """Use as @register on a Scheme subclass (no-arg constructible) or register(factory, name='...')."""
    def _do(o):
        n = name or getattr(o, 'name', None) or o().name
        if n in _REG and _REG[n] is not o: raise ValueError(f'scheme name already registered: {n}')
        _REG[n] = o; return o
    return _do if obj is None else _do(obj)

def _builtins():
    global _BUILTINS
    if _BUILTINS: return
    _BUILTINS = True
    from experiments.review_r1 import lineup_r1
    for s in lineup_r1(): _REG.setdefault(s.name, (lambda s=s: s))

_LOADED_PLUGINS = set()

def load_plugins(path=None):
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'schemes_contrib')
    for f in sorted(os.listdir(path)) if os.path.isdir(path) else []:
        if f.endswith('.py') and not f.startswith('_'):
            key = os.path.join(path, f)
            if key in _LOADED_PLUGINS: continue
            sp = importlib.util.spec_from_file_location(f'schemes_contrib.{f[:-3]}', key)
            m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
            _LOADED_PLUGINS.add(key)

def available(builtins=True, plugins=True):
    if builtins: _builtins()
    if plugins: load_plugins()
    return sorted(_REG)

def create(name):
    if name not in _REG: available()
    return _REG[name]()

get = create

def check_scheme(s, trials=20, seed=0):
    """Interface + noiseless round-trip check: ideal samples (dark 0, identity colour response) must decode exactly."""
    assert isinstance(s.name, str) and s.name and s.layers and 0 < s.nbits <= 256
    rng = np.random.RandomState(seed)
    for _ in range(trials):
        b = list(rng.randint(0, 2, s.nbits)); d = np.asarray(s.encode(b), float)
        assert d.shape == (8, 8, 3) and d.min() >= 0 and d.max() <= 1, 'drive must be (8,8,3) in [0,1]'
        for p, c in PILOT_POS.items(): assert np.allclose(d[p], c), f'pilot {p} must stay {c}'
        o = list(s.decode(d, np.zeros(3)))
        assert len(o) == s.nbits and o == b, 'noiseless round-trip failed'
    return True
