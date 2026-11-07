
# Makefile
# Tiny Tapeout CL-4 project

# --------------------------------------------------
# Default configuration
# --------------------------------------------------

SIM ?= icarus
FST ?= -fst
TOPLEVEL_LANG ?= verilog

SRC_DIR = $(PWD)/../src

PROJECT_SOURCES = project.v \
                  button_debounce.v \
                  code_compare.v \
                  combo_lock.v \
                  entry_fsm.v \
                  failure_counter.v \
                  press_qualify.v \
                  reset_sync.v \
                  shared_time.v

# --------------------------------------------------
# RTL SIMULATION
# --------------------------------------------------

ifneq ($(GATES),yes)

SIM_BUILD = sim_build/rtl

VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

# Full RTL verification suite
COCOTB_TEST_MODULES = test

# --------------------------------------------------
# GATE-LEVEL SIMULATION
# --------------------------------------------------

else

SIM_BUILD = sim_build/gl

COMPILE_ARGS += -DGL_TEST
COMPILE_ARGS += -DFUNCTIONAL
COMPILE_ARGS += -DUSE_POWER_PINS
COMPILE_ARGS += -DSIM
COMPILE_ARGS += -DUNIT_DELAY=\#1

# GF180 PDK simulation libraries
VERILOG_SOURCES += $(PDK_ROOT)/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog/primitives.v

VERILOG_SOURCES += $(PDK_ROOT)/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/verilog/gf180mcu_fd_sc_mcu7t5v0.v

# Synthesized gate-level netlist
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

# Gate-level external-interface verification
COCOTB_TEST_MODULES = test_gl

endif

# --------------------------------------------------
# COMMON CONFIGURATION
# --------------------------------------------------

# Include RTL directory
COMPILE_ARGS += -I$(SRC_DIR)

# Testbench
VERILOG_SOURCES += $(PWD)/tb.v

TOPLEVEL = tb

# --------------------------------------------------
# Cocotb Makefile
# --------------------------------------------------

include $(shell cocotb-config --makefiles)/Makefile.sim
