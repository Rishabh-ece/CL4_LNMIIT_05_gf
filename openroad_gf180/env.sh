# ---- edit these ----
export PDK_ROOT=${PDK_ROOT:-$HOME/.ciel}
export PDK=${PDK:-gf180mcuD}
export TOP=tt_um_CL4_LNMIIT
export CLOCK_PORT=clk
export CLOCK_PERIOD=1000000                       # ns
export DIE_AREA="0 0 200 150"                # um
export CORE_AREA="3.36 3.92 196.56 145.04"   # um, site-aligned (0.56 x 3.92)
# ---- derived ----
export SCL=gf180mcu_fd_sc_mcu7t5v0
export SCL_DIR=$PDK_ROOT/$PDK/libs.ref/$SCL
export TECH_LEF=$SCL_DIR/techlef/${SCL}__nom.tlef
export CELL_LEF=$SCL_DIR/lef/$SCL.lef
export CELL_GDS=$SCL_DIR/gds/$SCL.gds
export CELL_SPICE=$SCL_DIR/spice/$SCL.spice
export LIB_TT=$SCL_DIR/lib/${SCL}__tt_025C_3v30.lib
export LIB_SS=$SCL_DIR/lib/${SCL}__ss_125C_3v00.lib
export LIB_FF=$SCL_DIR/lib/${SCL}__ff_n40C_3v60.lib
export RCX_DIR=$PDK_ROOT/$PDK/libs.tech/openlane
export MAGICRC=$PDK_ROOT/$PDK/libs.tech/magic/$PDK.magicrc
export NETGEN_SETUP=$PDK_ROOT/$PDK/libs.tech/netgen/${PDK}_setup.tcl
export LIB=$LIB_TT     # default corner for scripts that take LIB
