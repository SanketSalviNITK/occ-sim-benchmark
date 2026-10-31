#!/bin/bash
set -e
cd /workspace/occ_sim
PY=.venv/bin/python
$PY -m experiments.run_phys --pref 33.011 --tag _PHYS_P33
for P in 25 42 60; do $PY -m experiments.run_phys --pref $P --sweeps distance_m --tag _PHYS_P$P; done
for P in 15 25 33 42; do $PY -m experiments.run_phys --pref $P --cap --lowlight --sweeps distance_m --tag _PHYS_LL_P$P; done
$PY -m experiments.run_phys --pref 33 --cap --lowlight --sweeps t_exp --tag _PHYS_LL_P33X
echo ALLDONE
