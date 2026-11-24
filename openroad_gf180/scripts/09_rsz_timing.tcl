read_liberty $::env(LIB_TT)
read_db out/08_cts.odb
source scripts/setup_pnr.tcl
set_propagated_clock [all_clocks]
estimate_parasitics -placement
repair_timing -setup -setup_margin 0.05 -max_buffer_percent 50
repair_timing -hold -hold_margin 0.1 -max_buffer_percent 50
detailed_placement -max_displacement {500 100}
check_placement -verbose
estimate_parasitics -placement
report_worst_slack -max
report_worst_slack -min
report_tns
write_db out/09_rsz.odb
