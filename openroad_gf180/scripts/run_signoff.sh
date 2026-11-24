#!/usr/bin/env bash
# RCX at 3 interconnect corners, STA at 9 corners, IR drop. Run after run_pnr.sh.
set -euo pipefail
for RC in nom min max; do
  RC=$RC openroad -exit scripts/14_rcx.tcl 2>&1 | tee logs/14_rcx_$RC.log
done
for RC in nom min max; do
  for C in "tt $LIB_TT" "ss $LIB_SS" "ff $LIB_FF"; do
    set -- $C
    CORNER=${RC}_$1 RC=$RC LIB=$2 sta -no_splash -exit scripts/15_sta_signoff.tcl 2>&1 | tee logs/15_sta_${RC}_$1.log
  done
done
openroad -exit scripts/16_irdrop.tcl 2>&1 | tee logs/16_irdrop.log
echo; echo "=== Summary"; grep -H "worst slack" logs/15_sta_*.log; grep "Worstcase IR drop" logs/16_irdrop.log
