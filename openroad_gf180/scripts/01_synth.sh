#!/usr/bin/env bash
# Yosys synthesis to gf180mcu_fd_sc_mcu7t5v0 cells.  Run from the package root after: source env.sh
set -euo pipefail
mkdir -p out logs
yosys -l logs/synth.log -p "
read_liberty -lib $LIB_TT;
read_verilog -sv src/*.v;
hierarchy -check -top $TOP;
synth -top $TOP -flatten;
dfflibmap -liberty $LIB_TT -dont_use *__sdff*;
abc -liberty $LIB_TT -D $((CLOCK_PERIOD*1000)) -dont_use *__sdff* -dont_use ${SCL}__mux2_1 -dont_use ${SCL}__oai33_2;
setundef -zero;
hilomap -singleton -hicell ${SCL}__tieh Z -locell ${SCL}__tiel ZN;
splitnets;
opt_clean -purge;
insbuf -buf ${SCL}__buf_1 I Z;
check -assert;
tee -o logs/synth_stat.rpt stat -liberty $LIB_TT;
write_verilog -noattr -noexpr -nohex -nodec -defparam out/$TOP.nl.v"
