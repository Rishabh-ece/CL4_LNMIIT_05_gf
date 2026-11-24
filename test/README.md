# CL-4 Testbench

This directory contains the Cocotb verification environment for the CL-4 four-digit combination lock (`tt_um_CL4_LNMIIT`).

The testbench drives the four button inputs and reset, then verifies the outputs:

- `unlock`
- `locked_out`
- `attempt_count`
- `state`

The verification is based on the requirements in **CL4-SPEC-001** and includes both RTL simulation and post-layout gate-level simulation (GLS).

For general Tiny Tapeout testing background, see the [Tiny Tapeout testing guide](https://tinytapeout.com/hdl/testing/).

## Files

| File | Purpose |
|---|---|
| `Makefile` | Defines RTL sources, simulator settings and test-module selection for RTL and GLS |
| `tb.v` | Verilog testbench wrapper that instantiates `tt_um_CL4_LNMIIT` |
| `test.py` | Main RTL Cocotb regression, including directed tests and a cycle-accurate reference model |
| `gls_test.py` | Post-layout GLS regression using the Tiny Tapeout external interface |
| `tb.gtkw` | GTKWave save file, if generated or maintained |

The RTL and GLS testbenches serve different purposes:

- **RTL (`test.py`):** Performs detailed functional verification, including internal-state checks, directed corner cases and randomized cycle-by-cycle reference-model comparison.
- **GLS (`gls_test.py`):** Verifies the hardened gate-level netlist through the external Tiny Tapeout interface. It does not depend on internal RTL hierarchy.

## Pin mapping used by the tests

The testbenches communicate with the Tiny Tapeout wrapper rather than directly with `combo_lock`.

| Signal | Pin | Direction |
|---|---|---|
| Button 0 | `ui_in[0]` | Input |
| Button 1 | `ui_in[1]` | Input |
| Button 2 | `ui_in[2]` | Input |
| Button 3 | `ui_in[3]` | Input |
| `unlock` | `uo_out[0]` | Output |
| `locked_out` | `uo_out[1]` | Output |
| `attempt_count[1:0]` | `uo_out[3:2]` | Output |
| `state[2:0]` | `uo_out[6:4]` | Output |

`uo_out[7]` and all `uio` pins are unused by the design and are checked to remain zero.

## Active design configuration

The current hardened design uses the following configuration:

| Parameter | Value |
|---|---:|
| `DEBOUNCE_CYCLES` | 16 |
| `MAX_ATTEMPTS` | 3 |
| `UNLOCK_CYCLES` | 4000 |
| `LOCKOUT_CYCLES` | 4000 |
| `INTERDIGIT_TIMEOUT_CYCLES` | 4000 |
| `CODE_VALUE` | `8'h9C` |
| `RST_SYNC` | 1 |
| Timer width | 12 bits |
| Clock frequency | 1 kHz |

The programmed code is **2-1-3-0**.

At a 1 kHz clock frequency, 4000 cycles correspond to 4 seconds.

## Setting up

1. Check that `PROJECT_SOURCES` in the `Makefile` lists all RTL source files and matches `source_files` in `info.yaml`:

   - `project.v`
   - `button_debounce.v`
   - `code_compare.v`
   - `combo_lock.v`
   - `entry_fsm.v`
   - `failure_counter.v`
   - `press_qualify.v`
   - `reset_sync.v`
   - `shared_time.v`

2. Check that `tb.v` instantiates `tt_um_CL4_LNMIIT`.

3. Check the installed Cocotb version:

   ```sh
   pip show cocotb
   ```

   The Makefile must select the Cocotb 2.x test-module variable:

   ```make
   COCOTB_TEST_MODULES = test
   ```

   For GLS, the Makefile must select `gls_test` when `GATES=yes`.

4. For GLS, load the project environment before running the simulation:

   ```sh
   source ~/ttsetup/venv/bin/activate
   ```

## Timing notes for writing tests

- A clean button press first sampled high at edge `j` changes the FSM state at edge `j + D + 1`.
- With the active configuration, `D = 16`.
- The testbench drives inputs on falling clock edges and samples after the relevant clock edge has settled.
- Hold a button long enough to pass the debounce qualification.
- Release a button long enough before pressing it again so that the release is qualified.
- Reset assertion is asynchronous. With `RST_SYNC=1`, reset deassertion is synchronized through the reset synchronizer.
- The inter-digit timeout, unlock interval and lockout interval are each 4000 cycles in the active configuration.
- F23 is specifically for `INTERDIGIT_TIMEOUT_CYCLES=0`; it is not applicable to the active `N=4000` configuration.

## How to run

Run the commands from the project's `test/` directory.

### 1. RTL simulation

```sh
cd ~/CL4/CL4_LNMIIT_05_gf/test
make -B sim
```

This runs the RTL Cocotb regression using `test.py`.

The RTL regression includes directed functional tests and a cycle-accurate reference model. The reference model compares the DUT behavior against the expected behavior during simulation.

### 2. Post-layout gate-level simulation

First load the GF180 environment:

```sh
source ~/ttsetup/venv/bin/activate
```

Then run:

```sh
make -B GATES=yes sim
```

This selects `gls_test.py` and simulates the hardened gate-level netlist using the GF180 standard-cell models.

The netlist used by the current Makefile is:

```text
test/gate_level_netlist.v
```


The GLS testbench checks the external Tiny Tapeout interface and does not rely on internal RTL signal names.

### 3. Checking simulation results

After each run, check the Cocotb summary and `results.xml`.

For the recorded project runs:

| Regression | Result |
|---|---|
| RTL regression | 34 passed, 0 failed, 1 intentional conditional skip |
| Post-layout GLS | 10 passed, 0 failed, 0 skipped |

The RTL skip is F23, which only runs with `INTERDIGIT_TIMEOUT_CYCLES=0`. The active configuration uses 4000 cycles.

## Verification plan coverage

The RTL testbench covers the following verification cases:

| Area | Verification IDs |
|---|---|
| Reset | F01, F02, F03, F35, F36 |
| Debounce | F04–F09 |
| Code entry | F10, F13, F24 |
| Unlock | F11, F12, F33 |
| Failure counter and lockout | F14–F19, F31, F34 |
| Inter-digit timeout | F21–F23 |
| Press qualification | F20, F32 |
| Outputs, state and interface | F25, F26, F28, F29 |
| Reference model and parameter configuration | F27, F30 |
| Illegal-state recovery | F39 |

F10/F11 and F16/F17 share Cocotb test functions, so the number of verification objectives is greater than the number of test functions.

### Gate-level verification coverage

The GLS testbench contains 10 directed tests:

| GLS ID | Test function | Verification objective |
|---|---|---|
| GLS-01 | `gls_reset_and_interface` | Reset values, output mapping and unused pins |
| GLS-02 | `gls_correct_code_and_unlock_duration` | Correct code entry and unlock duration |
| GLS-03 | `gls_wrong_digit_at_each_position` | Wrong digit at every position |
| GLS-04 | `gls_failure_counter_and_lockout_threshold` | Failure counter and lockout threshold |
| GLS-05 | `gls_lockout_duration_and_recovery` | Lockout duration and recovery |
| GLS-06 | `gls_input_ignored_during_lockout` | Inputs ignored during lockout |
| GLS-07 | `gls_debounce_short_pulse_and_held_button` | Short pulse rejection and held-button behavior |
| GLS-08 | `gls_simultaneous_buttons_rejected` | Simultaneous button rejection |
| GLS-09 | `gls_reset_during_partial_entry` | Reset during partial code entry |
| GLS-10 | `gls_interdigit_timeout` | Inter-digit timeout behavior |

The recorded GLS result is **10/10 passed**.

## Additional verification and signoff

The Cocotb tests are only one part of the verification process.

The following tool-flow checks are maintained separately:

| ID | Check | Tool / flow |
|---|---|---|
| N1 | RTL lint | Verilator |
| N2 | Synthesis checks | Yosys |
| N3 | Static timing analysis | OpenROAD / timing flow |
| N4 | Gate-level simulation | Icarus Verilog and Cocotb |

These checks are not all Cocotb test cases. Their reports and logs should be retained as project evidence.

## Waveform viewing

The Verilog testbench controls waveform generation through `$dumpfile` and `$dumpvars`.

Check the filename specified in `tb.v` before opening the generated waveform. The file extension alone does not guarantee whether the contents are VCD or FST.

For example:

```sh
gtkwave tb.fst
```

If the testbench generates a VCD file instead:

```sh
gtkwave tb.vcd
```

## Verification documentation

The complete verification details and results are maintained in:

- `verification.md` — detailed verification report, RTL cases, GLS cases and signoff status.
- `CL4_Verification_Tracker.xlsx` — case-by-case verification tracker, configuration and tool-flow checklist.

Both files should be kept updated alongside the RTL and testbench files.
