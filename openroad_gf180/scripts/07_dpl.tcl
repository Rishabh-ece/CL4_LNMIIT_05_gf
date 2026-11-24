read_liberty $::env(LIB_TT)
read_db out/06_rsz.odb
source scripts/setup_pnr.tcl
detailed_placement -max_displacement {500 100}
optimize_mirroring
check_placement -verbose
write_db out/07_dpl.odb
