# Author - gsb
# only for educational purpose

#------------------------------------------------------------------------------
# A SDC is synopsys/standard Design Constraint file which tells the tools what timing the design has to be meet and
# what conditions the design will work in, Synthesis, place and route and STA all read it, so they all optimise and 
# check against the same targets.

# Note - The SDC holds no delays. Cell delays come from the .lib, wire delays come
# from estimates or the SPEF. STA combines all three to give slack.
#

# Version of sdc
#------------------------------------------------------------------------------
# Object access(if any)
#    Finding the ports, pins, cells and nets to constrain.
#      get_ports, get_pins, get_cells, get_nets
#      all_inputs, all_outputs, all_clocks
#------------------------------------------------------------------------------
# Clocks
create_clock -name clk -period 1000000 [get_ports clk]
set_clock_uncertainty 0.25 [get_clocks clk]
set_clock_transition 0.15 [get_clocks clk]

#------------------------------------------------------------------------------
# I/O timing
#    How much of the clock period is used outside the block.
#      set_input_delay         inputs arrive this long after the clock edge
#      set_output_delay        outputs must be ready this long before the next edge
set clk_port [get_ports $::env(CLOCK_PORT)]
set clk_idx [lsearch [all_inputs] $clk_port]
set inputs_no_clk [lreplace [all_inputs] $clk_idx $clk_idx]
set_input_delay [expr {0.2 * $::env(CLOCK_PERIOD)}] -clock clk $inputs_no_clk
set_output_delay [expr {0.2 * $::env(CLOCK_PERIOD)}] -clock clk [all_outputs]
#------------------------------------------------------------------------------
# Environment
#    What drives the inputs and what the outputs drive.
# set_driving_cell with a lib_cell as shown in below example - explore on why this is required,
# set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin ZN $inputs_no_clk
# set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_4 -pin ZN $clk_port
set_load 0.07291 [all_outputs]

#------------------------------------------------------------------------------
# 6. Design rules
#    Electrical limits the tools must fix.
#      set_max_transition      max slew
#      set_max_capacitance     max load on a driver
#      set_max_fanout          max number of loads on a net
set_max_fanout 10 [current_design]
set_max_transition 3 [current_design]
set_max_capacitance 0.2 [current_design]

#------------------------------------------------------------------------------
# 7. Timing exceptions
#    Paths that do not follow the default single-cycle rule.
#      set_false_path          path never needs to meet timing
#      set_multicycle_path     path is allowed more than one cycle
#      set_max_delay           explicit max delay on a path
#      set_min_delay           explicit min delay on a path
#------------------------------------------------------------------------------
# 9. Variation and margins
#    On-chip variation.
#      set_timing_derate -early 0.95 / -late 1.05   (+/- 5 %)
set_timing_derate -early 0.95
set_timing_derate -late 1.05
#------------------------------------------------------------------------------
# 10. Area and power
#    Mostly for synthesis and multi-voltage designs.
#      set_max_area
#      voltage domains, level shifters, isolation
#------------------------------------------------------------------------------
##### END OF FILE ##############
# NOTE - This is just a sample, many companies/Designers use their own format.

