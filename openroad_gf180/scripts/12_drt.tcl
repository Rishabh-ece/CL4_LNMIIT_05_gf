read_liberty $::env(LIB_TT)
read_db out/11_ant.odb
source scripts/setup_pnr.tcl
set_thread_count [exec nproc]
detailed_route -droute_end_iter 64 -or_seed 42 -verbose 1 -output_drc logs/drt.drc
check_antennas -verbose
write_db out/12_drt.odb
