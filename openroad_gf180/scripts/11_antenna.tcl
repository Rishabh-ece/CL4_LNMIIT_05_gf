read_liberty $::env(LIB_TT)
read_db out/10_grt.odb
source scripts/setup_pnr.tcl
check_antennas -verbose
repair_antennas $::env(SCL)__antenna -iterations 3 -ratio_margin 10
check_placement -verbose
check_antennas -verbose
write_db out/11_ant.odb
