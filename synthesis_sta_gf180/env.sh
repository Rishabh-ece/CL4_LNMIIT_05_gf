# Source this in every new shell:  source env.sh
# ---- edit these ----
export PDK_ROOT=${PDK_ROOT:-$HOME/.ciel}
export PDK=${PDK:-gf180mcuD}
export TOP=tt_um_CL4_LNMIIT                 # top module name (file must be src/$TOP.v)
export CLOCK_PORT=clk          # clock input port
export CLOCK_PERIOD=1000000         # ns
# ---- PDK paths (no need to edit) ----
export SCL=gf180mcu_fd_sc_mcu7t5v0
export SCL_DIR=$PDK_ROOT/$PDK/libs.ref/$SCL
export LIB_TT=$SCL_DIR/lib/${SCL}__tt_025C_3v30.lib
export LIB_SS=$SCL_DIR/lib/${SCL}__ss_125C_3v00.lib
export LIB_FF=$SCL_DIR/lib/${SCL}__ff_n40C_3v60.lib
