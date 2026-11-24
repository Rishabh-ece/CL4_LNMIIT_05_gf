read_lef $::env(TECH_LEF)
read_lef $::env(CELL_LEF)
read_liberty $::env(LIB_TT)
read_verilog out/$::env(TOP).nl.v
link_design $::env(TOP)
read_sdc constraints/$::env(TOP).sdc
initialize_floorplan -site GF018hv5v_mcu_sc7 -die_area $::env(DIE_AREA) -core_area $::env(CORE_AREA)
insert_tiecells $::env(SCL)__tiel/ZN -prefix TIE_ZERO_
insert_tiecells $::env(SCL)__tieh/Z -prefix TIE_ONE_
make_tracks Metal1 -x_offset 0.28 -x_pitch 0.56 -y_offset 0.28 -y_pitch 0.56
make_tracks Metal2 -x_offset 0.28 -x_pitch 0.56 -y_offset 0.28 -y_pitch 0.56
make_tracks Metal3 -x_offset 0.28 -x_pitch 0.56 -y_offset 0.28 -y_pitch 0.56
make_tracks Metal4 -x_offset 0.28 -x_pitch 0.56 -y_offset 0.28 -y_pitch 0.56
make_tracks Metal5 -x_offset 0.45 -x_pitch 0.90 -y_offset 0.45 -y_pitch 0.90
report_design_area
write_db out/02_floorplan.odb
write_def out/02_floorplan.def
