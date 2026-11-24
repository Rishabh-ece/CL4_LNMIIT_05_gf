#!/usr/bin/env bash
# Runs OpenROAD steps in order. Usage: ./scripts/run_pnr.sh [first_step]   e.g. ./scripts/run_pnr.sh 08_cts
set -euo pipefail
mkdir -p out logs
STEPS=(02_floorplan 03_tap 04_pdn 05_gpl 06_repair_design 07_dpl 08_cts 09_rsz_timing 10_grt 11_antenna 12_drt 13_fill)
start=${1:-02_floorplan}; go=0
for s in "${STEPS[@]}"; do
  [ "$s" = "$start" ] && go=1
  [ $go = 1 ] || continue
  echo "=== $s"
  openroad -exit scripts/$s.tcl 2>&1 | tee logs/$s.log
  if grep -q "^\[ERROR" logs/$s.log; then echo "Stopped: error in $s"; exit 1; fi
done
