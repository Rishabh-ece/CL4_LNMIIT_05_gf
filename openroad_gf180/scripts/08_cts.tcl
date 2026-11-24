read_liberty $::env(LIB_TT)
read_db out/07_dpl.odb
source scripts/setup_pnr.tcl
estimate_parasitics -placement
repair_clock_inverters
configure_cts_characterization -max_cap 0.5e-12
clock_tree_synthesis -root_buf $::env(SCL)__clkbuf_16 -buf_list "$::env(SCL)__clkbuf_2 $::env(SCL)__clkbuf_4 $::env(SCL)__clkbuf_8" -sink_clustering_enable
set_propagated_clock [all_clocks]
estimate_parasitics -placement
repair_clock_nets -max_wire_length 0
detailed_placement -max_displacement {500 100}
check_placement -verbose
estimate_parasitics -placement
report_clock_skew
report_worst_slack -max
report_worst_slack -min
write_db out/08_cts.odb
