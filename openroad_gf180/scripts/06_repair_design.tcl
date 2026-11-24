read_liberty $::env(LIB_TT)
read_db out/05_gpl.odb
source scripts/setup_pnr.tcl
estimate_parasitics -placement
buffer_ports -inputs
repair_design -slew_margin 20 -cap_margin 20
repair_tie_fanout -separation 0 $::env(SCL)__tiel/ZN
repair_tie_fanout -separation 0 $::env(SCL)__tieh/Z
report_floating_nets -verbose
report_check_types -max_slew -max_capacitance -max_fanout -violators
write_db out/06_rsz.odb
