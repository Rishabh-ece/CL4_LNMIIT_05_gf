# Sign-off STA for one corner: LIB = .lib file, RC = nom|min|max, CORNER = name used in report files
read_liberty $::env(LIB)
read_verilog out/$::env(TOP).pnl.v
link_design $::env(TOP)
read_spef out/$::env(TOP).$::env(RC).spef
read_sdc constraints/$::env(TOP).sdc
set_propagated_clock [all_clocks]
set f "-fields {slew cap input net fanout} -format full_clock_expanded -digits 3"
eval report_checks -path_delay max $f > logs/sta_$::env(CORNER)_setup.rpt
eval report_checks -path_delay min $f > logs/sta_$::env(CORNER)_hold.rpt
eval report_checks -unconstrained $f > logs/sta_$::env(CORNER)_unconstrained.rpt
report_check_types -max_slew -max_capacitance -max_fanout -violators > logs/sta_$::env(CORNER)_drv.rpt
report_clock_skew > logs/sta_$::env(CORNER)_skew.rpt
report_worst_slack -max
report_worst_slack -min
report_tns
write_sdf -divider . out/$::env(TOP).$::env(CORNER).sdf
