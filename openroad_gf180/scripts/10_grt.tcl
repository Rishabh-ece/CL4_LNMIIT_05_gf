read_liberty $::env(LIB_TT)
read_db out/09_rsz.odb
source scripts/setup_pnr.tcl
set_propagated_clock [all_clocks]
set_global_routing_layer_adjustment Metal2-Metal5 0.3
global_route -congestion_iterations 50 -congestion_report_file logs/grt_congestion.rpt -verbose
write_guides out/10_grt.guide
estimate_parasitics -global_routing
report_worst_slack -max
report_worst_slack -min
write_db out/10_grt.odb
