# CL-4 testbench

This directory holds the [cocotb](https://docs.cocotb.org/en/stable/) testbench for the CL-4 4-digit combination lock (`tt_um_CL4_LNMIIT`). It drives the buttons and reset, then checks `unlock`, `locked_out`, `attempt_count` and `state` against the behavior in CL4-SPEC-001.

For general Tiny Tapeout testing background, see the [website](https://tinytapeout.com/hdl/testing/).

## Files

| File | Purpose |
|---|---|
| `Makefile` | Lists the RTL sources and selects the simulator and test module |
| `tb.v` | Verilog wrapper that instantiates `tt_um_CL4_LNMIIT` and dumps the waveform |
| `test.py` | cocotb tests (directed tests and the reference model) |

## Pin mapping used by the tests

The testbench talks to the Tiny Tapeout wrapper, not to `combo_lock` directly.

| Signal | Pin | Direction |
|---|---|---|
| `btn[0]` to `btn[3]` | `ui_in[0]` to `ui_in[3]` | input |
| `unlock` | `uo_out[0]` | output |
| `locked_out` | `uo_out[1]` | output |
| `attempt_count[1:0]` | `uo_out[3:2]` | output |
| `state[2:0]` | `uo_out[6:4]` | output |

`uo_out[7]` and all `uio` pins are not used by the design.

## Setting up

1. Check that `PROJECT_SOURCES` in [Makefile](Makefile) lists every RTL file, matching `source_files` in `info.yaml`:
   `project.v`, `button_debounce.v`, `code_compare.v`, `combo_lock.v`, `entry_fsm.v`, `failure_counter.v`, `press_qualify.v`, `reset_sync.v`, `shared_time.v`.
2. Check that [tb.v](tb.v) instantiates `tt_um_CL4_LNMIIT`.
3. Check the cocotb version with `pip show cocotb`. The Makefile and `test.py` must match it:
   - cocotb 2.x: `Clock(dut.clk, 10, unit="ns")` and `COCOTB_TEST_MODULES = test` in the Makefile.
   - cocotb 1.x: `Clock(dut.clk, 10, units="ns")` and `MODULE = test` in the Makefile.

## Timing notes for writing tests

- With the default parameters, `D = 16` and all timers are 4000 cycles. A full lockout test therefore needs a few thousand clock cycles per phase.
- A clean press first sampled high at edge `j` changes the FSM state at edge `j + D + 1`.
- Hold each button for at least `D` cycles, and release it for at least `D` cycles before pressing the same button again.
- Sample outputs after the clock edge has settled (for example, `await ReadOnly()`), and do not write inputs in the same time step after `ReadOnly`.
- Apply reset for at least `1 + 2 * RST_SYNC` clock edges.
- To test faster, override the parameters (shorter timers and a smaller `D`) in a separate configuration, and also run once at the real operating values.

## How to run

To run the RTL simulation:

```sh
cd test
make -B
```

A passing run ends with a cocotb summary that lists every test as `PASS`. Check `results.xml` for failures.

To run gate-level simulation, first harden your project, then copy the gate-level netlist from `../runs/wokwi/results/final/verilog/gl/tt_um_CL4_LNMIIT.v` to `gate_level_netlist.v` in this directory. Then run:

```sh
make -B GATES=yes
```

If you want the waveform in VCD format instead of FST, edit `tb.v` to use `$dumpfile("tb.vcd");` and run:

```sh
make -B FST=
```

This generates `tb.vcd` instead of `tb.fst`.

## Verification plan coverage

The tests map to the feature IDs in the verification plan (F01 to F35, plus N1 to N4):

| Area | IDs |
|---|---|
| Reset | F01, F02, F03, F35 |
| Debounce | F04 to F09 |
| Code entry | F10, F13, F24 |
| Unlock | F11, F12, F33 |
| Failure counter and lockout | F14 to F19, F34 |
| Inter-digit timeout | F21, F22, F23 |
| Press qualification | F20, F32 |
| Outputs, state and interface | F25, F26, F28, F29 |
| Reference model and parameter sets | F27, F30 |
| Illegal-state recovery | F31 |

Lint (N1), synthesis checks (N2) and static timing (N3) are not cocotb tests. Run them with Verilator, Yosys and the OpenROAD flow.

## How to view the waveform file

Using GTKWave:

```sh
gtkwave tb.fst tb.gtkw
```

Using Surfer:

```sh
surfer tb.fst
```
