# Run once per corner: RC=nom, RC=min, RC=max
set rc $::env(RC)
read_lef $::env(SCL_DIR)/techlef/$::env(SCL)__$rc.tlef
read_lef $::env(CELL_LEF)
read_def out/$::env(TOP).def
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file $::env(RCX_DIR)/rules.openrcx.$::env(PDK).$rc -lef_res
write_spef out/$::env(TOP).$rc.spef
