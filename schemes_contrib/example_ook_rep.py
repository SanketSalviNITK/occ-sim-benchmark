"""Minimal example plugin: repetition-2 OOK. 30 bits, each sent on two data LEDs (majority = sum of soft values)."""
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
