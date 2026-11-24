read_liberty $::env(LIB_TT)
read_db out/13_fill.odb
read_sdc constraints/$::env(TOP).sdc
set_propagated_clock [all_clocks]
read_spef out/$::env(TOP).nom.spef
report_power
set_pdnsim_net_voltage -net VDD -voltage 3.3
set_pdnsim_net_voltage -net VSS -voltage 0
analyze_power_grid -net VDD
analyze_power_grid -net VSS
