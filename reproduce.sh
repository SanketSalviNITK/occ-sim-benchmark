#!/bin/bash
# Reproduce benchmark-r0.  Usage: ./reproduce.sh tables   (minutes: verify shipped data, regenerate all tables from npz)
#                                 ./reproduce.sh full     (many CPU-hours: re-simulate every benchmark group, then tables)
# Runs from this script's directory (never a hard-coded path). Requires Python 3.13 + requirements.lock.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
[ -x "$PY" ] || { python3 -m venv .venv && .venv/bin/pip install -r requirements.lock; PY=.venv/bin/python; }
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PROCS=${PROCS:-$(nproc)}
MODE=${1:-tables}
if [ "$MODE" = full ]; then
  export CKPT=${CKPT:-$PWD/.ckpt}
  for g in idcheck e1sweep e2_P33 e2_P25 e2_P42 e3valid e3valid@imx219f \
           e3claims@imx219f or_e3claims@imx219f \
           or_sweep or_claims seedA seedB; do
    $PY -m experiments.review_r1 $g
  done
  $PY -m experiments.review_r1_dec
  $PY -m experiments.bench_ablation fact radiant
  $PY -m experiments.bench_finder
  $PY -m experiments.e4_trace corners_bench
elif [ "$MODE" = tables ]; then
  (sha256sum -c --quiet results/MANIFEST.sha256 && echo "manifest OK") || echo "WARNING: manifest mismatch (expected after a full re-run: npz embed timestamps)"
else echo "usage: $0 tables|full"; exit 2; fi
$PY -m pytest -q tests
$PY -m experiments.review_r1_report e1 e2 e3 e1_decomp
$PY -m experiments.bench_report oracle ablation seeds e3 c2_binding > /dev/null
echo "tables written to results/review_r1/ and results/benchmark/"
