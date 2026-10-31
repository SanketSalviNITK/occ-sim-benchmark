# Adding a scheme to the OCC benchmark

A scheme is **one Python file** in `schemes_contrib/`. It is discovered automatically by `occbench.available()`. Nothing in the simulator needs to change.

## Interface
Schemes are duck-typed and use the same contract as `tx.schemes.Scheme`:

| Member | Contract |
|---|---|
| `name` | Unique string. It is the key in result files. |
| `layers` | List of `(layer_name, nbits)`. Goodput is computed per layer, with a CRC-8 per layer (`experiments.stats.sym_goodput`). Total bits must be ≤ 256. |
| `encode(bits)` | Returns an `(8, 8, 3)` drive in [0, 1]. **Keep the four corner pilots** (`rx.refs.PILOT_POS`: TL white, TR red, BL green, BR blue). The corner finder and the colour references depend on them. Start from `tx.schemes.base_drive()`. |
| `decode(samples, dark)` | `samples` is the `(8, 8, 3)` per-LED mean DN at the rectified LED centres, and `dark` is the gap level `(3,)`. Returns `nbits` bits. `rx.refs.refs`, `on_metric` and `classify` give crosstalk-inverted helpers. |

Do not scale power yourself. The harness equalises average power across all compared schemes (`experiments.common.power_scales`, mode `equal`), and every scheme sees the same payload and channel noise (common random numbers).

## Minimal example (`schemes_contrib/example_ook_rep.py`)
```python
from occbench import register
from tx.schemes import Scheme, DATA_POS, base_drive
from rx.refs import refs, on_metric

@register
class OOKRep2(Scheme):
    name = 'EXAMPLE OOK-rep2'
    layers = [('all', len(DATA_POS) // 2)]          # 60 data LEDs -> 30 bits
    def encode(self, bits):
        d = base_drive()
        for i, b in enumerate(bits):
            d[DATA_POS[2 * i]] = d[DATA_POS[2 * i + 1]] = (b, b, b)
        return d
    def decode(self, s, dark):
        M, dk = refs(s, dark); x = on_metric(s, M, dk)
        return [int(x[DATA_POS[2 * i]] + x[DATA_POS[2 * i + 1]] > 1.0) for i in range(self.nbits)]
```

## Check and run
```bash
.venv/bin/python -c "from occbench import create, check_scheme; print(check_scheme(create('EXAMPLE OOK-rep2')))"
.venv/bin/python -m experiments.bench_run --list
.venv/bin/python -m experiments.bench_run --schemes "EXAMPLE OOK-rep2" "HNCSM v2" --distance 2.0 --frames 100          # real corner detector
.venv/bin/python -m experiments.bench_run --schemes "EXAMPLE OOK-rep2" "HNCSM v2" --distance 2.0 --frames 100 --oracle # true corners
```
`check_scheme` checks the shapes and the pilots, and runs a noiseless round trip. `tests/test_plugin_api.py` is the template for a plugin test.

## Scope
- The registry is additive. The paper line-ups (`experiments.review_r1.lineup_r1`, `experiments.audit_r1.lineup`) are not changed by plugins, so published results stay byte-identical.
- To include a plugin in a full sweep, pass its name in the `only` list of a job in `experiments/review_r1.py`, or build a line-up from `occbench.create`.
- A fair comparison also needs the scheme's tunable parameters to be chosen on the **tune** seeds (`config.TUNE_SEED`), never on the eval seeds.
