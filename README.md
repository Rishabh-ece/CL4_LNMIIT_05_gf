![GDS build](../../workflows/gds/badge.svg) ![Docs build](../../workflows/docs/badge.svg) ![Test](../../workflows/test/badge.svg) ![FPGA](../../workflows/fpga/badge.svg)

# CL-4 — Four-Digit Combination Lock ASIC

**CL4_LNMIIT_05** is a parameterized digital combination-lock controller implemented in Verilog for the Tiny Tapeout ASIC flow. It accepts a four-digit PIN through four independent push buttons, verifies the sequence, indicates a successful unlock, and temporarily locks out further input after consecutive incorrect attempts.

The project is developed by **Rishabh Agrawal and Ankit Mawle**.

- **Top-level Tiny Tapeout module:** `tt_um_CL4_LNMIIT`
- **Core controller:** `combo_lock`
- **HDL:** Verilog
- **Default PIN:** `2 → 1 → 3 → 0` (`8'h9C`)

> For the detailed architecture, interface description, and operating instructions, see the [project documentation](docs/info.md). For simulation and verification instructions, see [test/README.md](test/README.md).

---

## Features

- Four active-high button inputs, each with its own two-flop synchronizer and debounce filter.
- Symmetric press and release debouncing.
- One-cycle press events and qualification of simultaneous button presses.
- Parameterized four-digit PIN, fixed at synthesis time.
- Seven-state finite-state machine (FSM) for entry, failure, unlock, and lockout control.
- Configurable inter-digit timeout.
- Consecutive-failure tracking and automatic lockout.
- Registered `unlock` and `locked_out` status outputs.
- Exposes the attempt count and FSM state for observation and debugging.
- Cocotb functional regression with a cycle-accurate reference model and randomized stimulus.

## How it works

### 1. Button input conditioning

Each of the four asynchronous push-button inputs passes through an independent two-flop synchronizer followed by a debounce filter. A button transition is accepted only after the synchronized input has differed from its debounced level for `DEBOUNCE_CYCLES` consecutive cycles.

A confirmed low-to-high transition generates a one-cycle press pulse. Holding a button does not generate repeated presses; it must first be released and debounced low before it can be pressed again.

### 2. Press qualification and PIN comparison

The press-qualification block accepts a digit only when **exactly one** button produces a press pulse in a clock cycle. If two or more buttons produce pulses in the same cycle, that event is discarded.

The digit encoder maps `btn[0]` through `btn[3]` to digit values 0 through 3. The code comparator checks the digit against the expected PIN digit for the current FSM state.

### 3. Entry FSM

The controller uses the following seven states:

| State encoding | State | Function |
|---|---|---|
| `3'b000` | `IDLE` | Wait for the first digit |
| `3'b001` | `DIGIT2` | First digit accepted; wait for the second |
| `3'b010` | `DIGIT3` | Two digits accepted; wait for the third |
| `3'b011` | `DIGIT4` | Three digits accepted; wait for the fourth |
| `3'b100` | `UNLOCK` | Correct PIN entered |
| `3'b101` | `FAIL` | Wrong digit detected; one-cycle state |
| `3'b110` | `LOCKOUT` | Ignore button input during lockout |

A correct digit advances the FSM. A wrong digit sends it to `FAIL`, after which the failure counter is incremented and the next attempt starts from `IDLE`.

### 4. Unlock, timeout, and lockout

- **Successful entry:** After all four digits match, `unlock` is asserted for `UNLOCK_CYCLES` clock cycles.
- **Incorrect entry:** Each wrong digit counts as one failed attempt. After `MAX_ATTEMPTS` consecutive failures, the controller enters `LOCKOUT`.
- **Lockout:** `locked_out` remains asserted for `LOCKOUT_CYCLES` cycles. Button presses are ignored during this period, and the failure count is cleared when lockout ends.
- **Inter-digit timeout:** If the next digit is not entered within `INTERDIGIT_TIMEOUT_CYCLES`, a partial entry is abandoned and the FSM returns to `IDLE`. An abandoned entry does not count as a failure. Setting this parameter to 0 disables the timeout.

The unlock, lockout, and inter-digit timing functions share one 8-bit down-counter.

## Default configuration

The core controller's default parameters are:

| Parameter | Default | Description |
|---|---:|---|
| `DEBOUNCE_CYCLES` | `24` | Consecutive synchronized cycles required to accept a button transition |
| `MAX_ATTEMPTS` | `3` | Consecutive failures that trigger lockout |
| `UNLOCK_CYCLES` | `100` | Duration of the unlock state |
| `LOCKOUT_CYCLES` | `200` | Duration of the lockout state |
| `INTERDIGIT_TIMEOUT_CYCLES` | `250` | Maximum interval between accepted digits; 0 disables the timeout |
| `CODE_VALUE` | `8'h9C` | Four 2-bit PIN digits, most-significant digit first |
| `RST_SYNC` | `1` | Enables the two-flop reset synchronizer |

The default `CODE_VALUE = 8'h9C` represents:

| Entry order | Button | Digit |
|---:|---|---:|
| 1 | `btn[2]` | 2 |
| 2 | `btn[1]` | 1 |
| 3 | `btn[3]` | 3 |
| 4 | `btn[0]` | 0 |

All timer values are expressed in clock cycles. The clock period and resulting real-time durations depend on the selected implementation and clock configuration.

## Tiny Tapeout interface and pin mapping

The Tiny Tapeout wrapper is implemented in `src/project.v`. It connects the core controller to the Tiny Tapeout user I/O interface.

| Tiny Tapeout pin | Signal | Description |
|---|---|---|
| `ui[0]` | `BTN_0` | Button for digit 0 |
| `ui[1]` | `BTN_1` | Button for digit 1 |
| `ui[2]` | `BTN_2` | Button for digit 2 |
| `ui[3]` | `BTN_3` | Button for digit 3 |
| `uo[0]` | `LOCK_STATE` | Unlock status |
| `uo[1]` | `LOCKED_OUT_STATE` | Lockout status |
| `uo[2]` | `ATTEMPT_COUNT_0` | Failure count bit 0 |
| `uo[3]` | `ATTEMPT_COUNT_1` | Failure count bit 1 |
| `uo[4]` | `STATE_1` | FSM state bit 0 |
| `uo[5]` | `STATE_2` | FSM state bit 1 |
| `uo[6]` | `STATE_3` | FSM state bit 2 |
| `uo[7]` | — | Tied low |

The three state bits are routed to the three outputs labelled for the RGB pins in `info.yaml`; together they expose the binary FSM state. All bidirectional pins are unused and their output enables are tied low.

At the core level, `combo_lock` has the following interface:

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | Input | 1 | System clock |
| `rst_n` | Input | 1 | Active-low reset |
| `btn` | Input | 4 | Four asynchronous active-high buttons |
| `unlock` | Output | 1 | Unlock status |
| `locked_out` | Output | 1 | Lockout status |
| `attempt_count` | Output | 2 | Consecutive-failure count |
| `state` | Output | 3 | FSM state encoding |

## RTL source organization

The design is divided into small, reusable Verilog modules:

| File | Responsibility |
|---|---|
| `src/project.v` | Tiny Tapeout top-level wrapper and physical I/O mapping |
| `src/combo_lock.v` | Core integration and parameter declarations |
| `src/reset_sync.v` | Optional two-flop reset synchronizer |
| `src/button_debounce.v` | Per-button synchronizer and debounce filter |
| `src/press_qualify.v` | Exactly-one-press qualification and digit encoding |
| `src/code_compare.v` | Expected PIN digit selection and comparison |
| `src/entry_fsm.v` | Entry FSM and next-state control |
| `src/shared_time.v` | Shared 8-bit timer register |
| `src/failure_counter.v` | Consecutive-failure counter |

Project configuration is maintained in [info.yaml](info.yaml). The generated project datasheet is described in [docs/info.md](docs/info.md).

## Verification

The project uses **Cocotb 2.x** with Icarus Verilog for RTL simulation. The functional testbench is in `test/test.py` and includes a cycle-accurate Python reference model.

The verification plan covers:

- Reset assertion, release, and reset behaviour in every FSM state.
- Button synchronization, debounce latency, bounce rejection, and held-button behaviour.
- Correct PIN entry and wrong digits at every entry position.
- Unlock duration, failure counting, lockout threshold, lockout duration, and recovery.
- Simultaneous button presses and inter-digit timeout boundary conditions.
- FSM output decoding, state encoding, and illegal-state recovery.
- Unknown-value checks, parameter configurations, and cycle-by-cycle reference-model comparison.
- Randomized testing with button timing, bounce, and simultaneous presses.

The verification plan identifies functional requirements **F01–F36** and implementation checks **N1–N4**. The latter are separate tool-flow checks:

| ID | Check |
|---|---|
| N1 | Verilator RTL lint |
| N2 | Synthesis structure and flop-count checks |
| N3 | Static timing analysis |
| N4 | Optional gate-level simulation trace |

### Run RTL simulation

From the `test/` directory:

```sh
make -B
```

To check the Cocotb results:

```sh
python -m cocotb_tools.check_results results.xml
```

### Run gate-level simulation

After generating the gate-level netlist through the Tiny Tapeout hardening flow, place the powered GF180 netlist at `test/gate_level_netlist.v`. Then run:

```sh
make -B GATES=yes
```

If the GF180 PDK is installed in a non-default location:

```sh
make -B GATES=yes PDK_ROOT=/path/to/pdk
```

The RTL and gate-level test configurations use separate Cocotb test modules. See [test/README.md](test/README.md) for prerequisites, detailed commands, parameterized testing, and waveform instructions.

## Build and project documentation

Tiny Tapeout's GitHub Actions build the project artifacts and documentation using the configured project flow. The workflow badges at the top of this README report the repository's build, documentation, test, and FPGA workflow status.

Useful project links:

- [Project datasheet and operating instructions](docs/info.md)
- [Testbench and verification guide](test/README.md)
- [Tiny Tapeout project configuration](info.yaml)
- [Tiny Tapeout](https://tinytapeout.com/)
- [Tiny Tapeout documentation](https://tinytapeout.com/faq/)
- [Cocotb documentation](https://docs.cocotb.org/en/stable/)

---

## Acknowledgements

This project is developed as a digital design and ASIC implementation project using the Tiny Tapeout platform. Thanks to the Tiny Tapeout community and the open-source EDA ecosystem for making hands-on chip design and verification accessible.
