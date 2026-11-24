#!/usr/bin/env bash
# Run OpenSTA at tt, ss and ff.  Run from the package root after: source env.sh
set -euo pipefail
mkdir -p logs
CORNER=tt LIB=$LIB_TT sta -no_splash -exit scripts/sta.tcl 2>&1 | tee logs/sta_tt.log
CORNER=ss LIB=$LIB_SS sta -no_splash -exit scripts/sta.tcl 2>&1 | tee logs/sta_ss.log
CORNER=ff LIB=$LIB_FF sta -no_splash -exit scripts/sta.tcl 2>&1 | tee logs/sta_ff.log
