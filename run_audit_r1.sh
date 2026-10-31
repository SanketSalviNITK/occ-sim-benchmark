#!/bin/bash
# Round-1 audit regeneration (run from a clean commit). Logs to results/audit_r1.log
set -e; cd "$(dirname "$0")"; PY=.venv/bin/python
$PY -m experiments.audit_r1 valid claims trow radiant lowlight
for P in 25:25.0 33:33.011 42:42.0 60:60.0; do
  $PY -m experiments.run_phys --pref ${P#*:} --tag _PHYS_P${P%%:*} --sweeps distance_m
done
echo ALLDONE
