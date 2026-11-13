# CL-4 Verification Plan

**DUT:** `combo_lock` (wrapped by `tt_um_CL4_LNMIIT`)  
**Specification:** CL4-SPEC-001, Revision 1.0  
**Verification methodology:** Directed and constrained-random simulation  
**Verification framework:** cocotb with a Python reference model  
**Target technology:** GF180MCU 180 nm

---

## 1. Verification overview

The goal is to show that the combination lock controller behaves as defined in CL4-SPEC-001.

The environment uses directed tests, a cycle-accurate Python reference model, randomized stimulus and static checks.

The signals monitored are:

- `state[2:0]`: current FSM state.
- `attempt_count[1:0]`: consecutive failure counter.
- `unlock`: unlock status.
- `locked_out`: lockout status.

All outputs are sampled after each rising clock edge has settled and are compared with the reference model.

## 2. Verification methodology

1. **Directed testing:** predefined input sequences check individual features and corner cases.
2. **Reference model:** an independent Python model of the behavior.
3. **Cycle-by-cycle comparison:** the DUT outputs are compared with the model after every clock edge.
4. **Randomized testing:** random button sequences, bounce and simultaneous presses.
5. **Parameter verification:** configuration-dependent tests are repeated with different parameter sets.
6. **Static checks:** lint, synthesis inspection and static timing analysis.

The testbench has four parts:

- **Driver:** generates clock, reset and button stimulus.
- **Monitor:** samples DUT outputs after the clock edges.
- **Reference model:** predicts the expected state and outputs.
- **Checker:** compares observed and expected values.

The DUT under simulation is the Tiny Tapeout wrapper `tt_um_CL4_LNMIIT`. Buttons are on `ui_in[3:0]`. Outputs are `uo_out[0]` (unlock), `uo_out[1]` (locked_out), `uo_out[3:2]` (attempt_count) and `uo_out[6:4]` (state).

## 3. Functional verification

The suite has 35 functional tests, grouped by feature.

### 3.1 Reset

| Test ID | Test name | Objective |
|---|---|---|
| F01 | `test_reset_values` | Check initial FSM state, outputs and failure counter after reset. |
| F02 | `test_reset_all_states` | Check reset priority in every reachable FSM state. |
| F03 | `test_reset_clears_debouncers` | Check synchronizer and debounce registers are cleared, including a button held through reset. |
| F35 | `test_reset_synchronizer` | Check the two-flop reset synchronizer timing when `RST_SYNC = 1`. |

When `RST_SYNC = 1`, the environment accounts for the two-flop reset synchronization latency. F35 is required only for that setting.

### 3.2 Button synchronization and debounce

| Test ID | Test name | Objective |
|---|---|---|
| F04 | `test_debounce_latency` | Check the exact latency of D + 1 edges from first sampled high to state change. |
| F05 | `test_press_exactly_D` | Check a press of exactly D cycles is accepted. |
| F06 | `test_reject_D_minus_1_pulse` | Check a pulse of D - 1 cycles is rejected (D > 1). |
| F07 | `test_button_bounce` | Check bounce before a stable high gives exactly one press. |
| F08 | `test_held_button_single_press` | Check a held button gives only one press. |
| F09 | `test_release_debounce` | Check release filtering and correct re-arming. |

### 3.3 Code entry and unlock

| Test ID | Test name | Objective |
|---|---|---|
| F10 | `test_correct_code_unlock` | Check correct four-digit codes enter UNLOCK. |
| F11 | `test_unlock_duration` | Check `unlock` stays high for exactly `UNLOCK_CYCLES`. |
| F12 | `test_unlock_clears_failure_count` | Check a successful entry clears the failure counter. |
| F13 | `test_wrong_digit_each_position` | Check a wrong digit at each of the four positions leads to exactly one FAIL cycle after the fourth digit, then IDLE, and never unlocks. |
| F24 | `test_button_mapping` | Check all four buttons map to the right digits at every code position. |

For F13, the plan covers all four wrong-digit positions. For wrong digits at positions 1 to 3 the test continues the entry and checks the verdict after digit 4. The tests use several `CODE_VALUE` settings, including a code with repeated digits.

### 3.4 Failure counter and lockout

| Test ID | Test name | Objective |
|---|---|---|
| F14 | `test_failure_count_increment` | Check each failure adds exactly 1 to the counter. |
| F15 | `test_lockout_threshold` | Check lockout starts on the `MAX_ATTEMPTS`-th failure, not before. |
| F16 | `test_count_during_lockout` | Check the count stays at `MAX_ATTEMPTS` throughout lockout. |
| F17 | `test_lockout_duration` | Check the exact lockout duration. |
| F18 | `test_input_ignored_during_lockout` | Check presses are discarded during lockout. |
| F19 | `test_recovery_after_lockout` | Check normal operation resumes immediately after lockout. |

### 3.5 Press qualification and timeout

| Test ID | Test name | Objective |
|---|---|---|
| F20 | `test_simultaneous_presses` | Check presses completing in the same cycle (all six pairs and all four) are not a digit. |
| F21 | `test_abandoned_attempt` | Check incomplete entries time out without changing the failure count. |
| F22 | `test_timeout_boundary` | Check a press in cycle N is accepted and a press in cycle N + 1 is judged in IDLE. |
| F23 | `test_timeout_disabled` | Check `N = 0` disables the timeout. |
| F32 | `test_press_during_fail` | Check a press during FAIL is discarded. |
| F33 | `test_press_at_unlock_end` | Check a press in the last UNLOCK cycle is discarded. |
| F34 | `test_held_across_lockout_end` | Check a button held through lockout end gives no delayed press. |

### 3.6 FSM and outputs

| Test ID | Test name | Objective |
|---|---|---|
| F25 | `test_output_decode` | Check `unlock` and `locked_out` equal the decode of `state` in every cycle. |
| F26 | `test_state_encoding` | Check each FSM state uses its specified encoding. |
| F28 | `test_no_unknown_outputs` | Check no X or Z appears on outputs after reset. |
| F29 | `test_port_interface` | Check module name, port names, directions and widths of `combo_lock`. |
| F31 | `test_illegal_state_recovery` | Check recovery from state `3'b111`, including the lockout case. |

For F31, record the hierarchical name of the state register, `st` in `U_entry_fsm`, and force it from the testbench.

## 4. Reference model and randomized verification

### 4.1 Cycle-accurate reference model

The Python model predicts the expected behavior. It covers:

- Button synchronizers and debounce counters.
- Press qualification.
- Digit storage and the full-code comparison at the fourth digit.
- FSM transitions and priority.
- Failure counting.
- Shared timer for unlock, lockout and timeout.
- Reset priority and registered outputs.

The model uses pre-edge values, as the specification's execution model does, so scheduling differences cannot cause false mismatches.

After every rising clock edge settles, these are compared:

```text
state
attempt_count
unlock
locked_out
```

Any mismatch reports the cycle number, the inputs, the expected outputs and the DUT outputs.

### 4.2 Randomized regression

- At least 100 random runs of 5000 cycles each.
- Random button press and release timing.
- Bounce sequences.
- Simultaneous presses.
- Random idle intervals and incomplete entries.
- Comparison on every cycle.
- A fixed random seed when reproducibility is needed.

Random runs at the operating values (4000-cycle timers) mostly stay in one timed state. The regression therefore also runs on the short-timer configurations below.

## 5. Parameter configurations

| Parameter | CFG-0 Default | CFG-1 Boundary | CFG-2 Repeated digit | CFG-3 Alternate code | CFG-4 Operating |
|---|---|---|---|---|---|
| `DEBOUNCE_CYCLES` | 16 | 1 | 4 | 8 | 16 |
| `MAX_ATTEMPTS` | 3 | 1 | 2 | 3 | 3 |
| `UNLOCK_CYCLES` | 4000 | 7 | 8 | 15 | 4000 |
| `LOCKOUT_CYCLES` | 4000 | 9 | 12 | 20 | 4000 |
| `INTERDIGIT_TIMEOUT_CYCLES` | 4000 | 0 | 10 | 10 | 4000 |
| `CODE_VALUE` | `8'h9C` | `8'h1B` | `8'h55` | `8'hE4` | `8'h9C` |
| `RST_SYNC` | 1 | 1 | 0 | 1 | 1 |

CFG-4 uses the declared operating values: 1 kHz clock, so D = 16 ms and each timer is 4 s. It currently equals CFG-0.

### Configuration objectives

- **CFG-0 and CFG-4:** baseline and operating-value verification.
- **CFG-1:** boundary testing with D = 1, `MAX_ATTEMPTS` = 1 and the timeout disabled.
- **CFG-2:** repeated digits, code 1-1-1-1.
- **CFG-3:** alternate code 3-2-1-0.

Together, the configuration-dependent tests cover at least three parameter sets besides the default. For operating values, the timeout must be 0 or at least D + 2.

## 6. Static checks and implementation verification

| Check ID | Tool / method | Acceptance criteria |
|---|---|---|
| N1 | Verilator | `verilator --lint-only -Wall` completes cleanly. Any waiver is justified locally. |
| N2 | Yosys synthesis | No inferred latches, multipliers or dividers. Flop count matches the formula below. |
| N3 | Static timing analysis | Setup and hold slack are at least 0 at every declared corner. |
| N4 | Gate-level simulation | Optional: reproduce the successful-entry trace on the synthesized netlist. |

### Expected flop count

The expected flop count follows from the RTL: the 12-bit timer and the 6 flops that store the first three digits (`entered_code[7:2]`) are included.

```text
4 x (3 + max(1, ceil(log2(D)))) + 23 + F + 2 x RST_SYNC
```

- D = `DEBOUNCE_CYCLES`.
- F = 1 when `MAX_ATTEMPTS` = 1, otherwise 2.
- `RST_SYNC` = 1 when the reset synchronizer is enabled.

At the operating values (D = 16, `MAX_ATTEMPTS` = 3, `RST_SYNC` = 1) this gives 55 flops. This figure must be confirmed by the synthesis report. Any difference from technology mapping must be documented.

### Static timing analysis

STA uses the declared clock period, input and output delays, and asynchronous-input constraints. It includes:

- At least one slow setup corner and one fast hold corner.
- Worst setup slack and worst hold slack.
- The corresponding corner for each.

## 7. Verification environment and execution

The environment uses cocotb with an RTL simulator such as Icarus Verilog or Verilator. See `test/README.md` for how to run it.

Record the following for each run:

- Simulator and cocotb versions.
- RTL source files and parameter overrides.
- Test names and results.
- Simulation logs and failure messages.
- Random seeds and regression results.

## 8. Acceptance criteria

The design is functionally verified when:

1. All mandatory tests F01 to F34 pass.
2. F35 passes when `RST_SYNC = 1`.
3. All required parameter configurations pass their applicable tests.
4. The reference model reports no mismatches.
5. At least 100 random tests of 5000 cycles each complete.
6. No unknown values appear on outputs after reset.

Implementation acceptance also needs:

- N1: clean lint report.
- N2: synthesis structure and flop count as in section 6.
- N3: non-negative setup and hold slack at all declared corners.

N4 is optional.

## 9. Verification evidence

| Evidence | Description |
|---|---|
| Testbench source | cocotb tests and utilities |
| Reference model | Independent Python behavioral model |
| Simulation logs | Compile logs, execution logs and results |
| Regression summary | Per-test and overall pass/fail summary |
| Parameter record | Exact parameter values used for each configuration |
| Lint report | Verilator output |
| Synthesis report | Yosys cell statistics and flop count |
| STA reports | Setup and hold reports for each declared corner |

## 10. Scope of this document

This document defines the verification strategy and acceptance criteria for CL-4. It is a plan and does not state that any simulation, regression, lint, synthesis or timing check has been completed.
