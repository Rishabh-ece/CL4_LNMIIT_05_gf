# OpenSTA, one corner.  Needs env: LIB (Liberty file), CORNER (name for report files), TOP
read_liberty $::env(LIB)
read_verilog out/$::env(TOP).nl.v
link_design $::env(TOP)
read_sdc constraints/$::env(TOP).sdc
set f "-format full_clock_expanded -fields {slew cap input net fanout} -digits 3"
eval report_checks -path_delay max $f > logs/sta_$::env(CORNER)_setup.rpt
eval report_checks -path_delay min $f > logs/sta_$::env(CORNER)_hold.rpt
eval report_checks -unconstrained $f > logs/sta_$::env(CORNER)_unconstrained.rpt
report_check_types -max_slew -max_capacitance -max_fanout -violators > logs/sta_$::env(CORNER)_drv.rpt
report_wns
report_tns
report_worst_slack -max
report_worst_slack -min
