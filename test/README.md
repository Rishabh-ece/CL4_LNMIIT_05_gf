# CL-4 Testbench

The Cocotb testbench verifies the **CL-4 four-digit digital combination lock** (`tt_um_CL4_LNMIIT`), developed as a Tiny Tapeout project.

It drives the Tiny Tapeout wrapper instantiated in `../src/project.v` and checks the design's outputs through simulation. The testbench supports RTL simulation and gate-level simulation using the synthesized GF180 standard-cell netlist.

The functional behaviour is defined by the **CL-4 Specification (CL4-SPEC-001, Rev 1.0)**. The verification requirements are documented in the CL-4 Verification Plan (F01–F36, N1–N4).

All Cocotb functional tests are maintained in a single file, `test.py`.

For general testing guidance, refer to the [Tiny Tapeout Testing Guide](https://tinytapeout.com/hdl/testing/) and the [Cocotb Documentation](https://docs.cocotb.org/en/stable/).

## Files

| File | Purpose |
|---|---|
| `test.py` | Main Cocotb testbench containing the functional verification suite (F01–F36). |
| `tb.v` | Verilog testbench wrapper that instantiates `tt_um_CL4_LNMIIT` and generates waveform dumps. |
| `Makefile` | Configures Icarus Verilog, RTL source files, GF180 libraries, and Cocotb simulation. |
| `gate_level_netlist.v` | Synthesized gate-level netlist used for gate-level simulation. |

## DUT Interface

The testbench communicates with the Tiny Tapeout wrapper rather than directly instantiating `combo_lock`.

| Wrapper Signal | Description |
|---|---|
| `ui_in[3:0]` | Four button inputs (`BTN_0` to `BTN_3`). |
| `uo_out[0]` | Unlock status. |
| `uo_out[1]` | Lockout status. |
| `uo_out[3:2]` | Failure attempt count. |
| `uo_out[6:4]` | FSM state encoding. |
| `uo_out[7]` | Unused output, tied to logic 0. |
| `rst_n` | Active-low reset. |
| `clk` | System clock. |
| `ena` | Tiny Tapeout design enable. |

The remaining bidirectional interface signals (`uio_in`, `uio_out`, and `uio_oe`) are also connected through the testbench.

## Default Configuration

The Tiny Tapeout wrapper instantiates `combo_lock` using its default parameter values.

| Parameter | Default Value | Description |
|---|---:|---|
| `DEBOUNCE_CYCLES` (D) | 24 | Button debounce duration. |
| `MAX_ATTEMPTS` | 3 | Maximum consecutive failed attempts. |
| `UNLOCK_CYCLES` | 100 | Unlock duration in clock cycles. |
| `LOCKOUT_CYCLES` | 200 | Lockout duration in clock cycles. |
| `INTERDIGIT_TIMEOUT_CYCLES` (N) | 250 | Maximum interval between digit entries. |
| `CODE_VALUE` | `8'h9C` | Four-digit combination. |
| `RST_SYNC` | 1 | Enables reset synchronization. |

The default combination is **2 → 1 → 3 → 0**.

Tests executed through the Tiny Tapeout wrapper use these default parameter values. Testing other parameter configurations requires a separate simulation build that instantiates `combo_lock` directly.

## Prerequisites

The following tools are required:

- Icarus Verilog for RTL and gate-level simulation.
- Python 3.
- Cocotb 2.x.
- GF180 MCU PDK for gate-level simulation.
- GTKWave or Surfer (optional, for waveform inspection).

To check the installed Cocotb version:

```sh
pip show cocotb
```

## RTL Simulation

Run the following command from the `test/` directory:

```sh
make -B
```

The Makefile compiles the RTL source files listed in `PROJECT_SOURCES` and runs the Cocotb tests from `test.py`.

To check the simulation results using the Cocotb 2.x result checker:

```sh
python -m cocotb_tools.check_results results.xml
```

The verification suite covers the functional requirements F01–F36, including:

- Reset behaviour and reset synchronization.
- Button synchronization, debouncing, and press qualification.
- Correct and incorrect combination entry.
- Unlock operation and unlock duration.
- Failure counting and lockout threshold.
- Lockout duration and recovery.
- Inter-digit timeout and timeout boundary conditions.
- Simultaneous button presses and button-bounce handling.
- FSM state encoding and illegal-state recovery.
- Output decoding and interface verification.
- Parameter configuration checks.
- Cycle-accurate reference-model comparison.
- Randomized functional verification.

The reference model checks the expected behaviour of the design cycle by cycle during simulation.

Some tests are conditionally skipped depending on the configured parameter values.

The implementation checks N1–N4 are separate from the Cocotb functional regression:

| ID | Implementation Check |
|---|---|
| N1 | RTL lint |
| N2 | Synthesis checks |
| N3 | Static timing analysis |
| N4 | Gate-level verification trace |

## Gate-Level Simulation

First, harden the latest RTL design using the Tiny Tapeout flow.

After hardening, locate the generated powered GF180 gate-level netlist and copy it into the `test/` directory with the filename `gate_level_netlist.v`.

```sh
cp <path-to-generated-netlist>.v gate_level_netlist.v
```

Then run gate-level simulation:

```sh
make -B GATES=yes
```

When `GATES=yes`, the Makefile selects the GF180 standard-cell simulation libraries and the generated gate-level netlist instead of the original RTL source files.

If the GF180 PDK is installed in a non-default location, specify its root directory:

```sh
make -B GATES=yes PDK_ROOT=/path/to/pdk
```

**Note:** The existing `test.py` contains hierarchical references to internal RTL instances and registers, such as `U_combo_lock` and `U_entry_fsm`. These signals may not be accessible in the synthesized netlist because synthesis can flatten or optimize the RTL hierarchy.

Consequently, gate-level verification requires checking which internal signals remain accessible and adapting the relevant tests where necessary. A successful RTL regression does not automatically imply a successful gate-level regression.

Always generate the gate-level netlist from the latest RTL revision. Do not reuse a netlist generated from an older design version.

## Viewing Waveforms

The testbench generates an FST waveform file named `tb.fst` by default.

Using GTKWave:

```sh
gtkwave tb.fst tb.gtkw
```

Alternatively, use Surfer:

```sh
surfer tb.fst
```
