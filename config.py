"""Global reproducibility config. All sweeps derive per-condition seeds from SEED deterministically
(zlib.crc32, NOT Python's salted hash())."""
import zlib
SEED = 20261015
def cond_seed(sweep: str, index: int, base: int = SEED) -> int:
    return (base + zlib.crc32(sweep.encode()) + 7919 * index) % (2**31 - 1)
TUNE_SEED = SEED + 1_000_003     # held-out seeds for parameter tuning
GENIE_SEED = SEED + 2_000_029    # separate seeds for the adaptive-CSK genie's order selection
