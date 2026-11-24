read_liberty $::env(LIB_TT)
read_db out/04_pdn.odb
source scripts/setup_pnr.tcl
set_global_routing_layer_adjustment Metal2-Metal5 0.3
global_placement -skip_io -density 0.6
place_pins -hor_layers Metal3 -ver_layers Metal2
global_placement -density 0.6 -routability_driven
estimate_parasitics -placement
report_worst_slack -max
report_worst_slack -min
write_db out/05_gpl.odb
