read_liberty $::env(LIB_TT)
read_db out/12_drt.odb
filler_placement "$::env(SCL)__fillcap_* $::env(SCL)__fill_*"
check_placement -verbose
source scripts/pg_connect.tcl
write_db out/13_fill.odb
write_def out/$::env(TOP).def
write_verilog out/$::env(TOP).pnl.v
write_verilog -include_pwr_gnd out/$::env(TOP).pwr.v
