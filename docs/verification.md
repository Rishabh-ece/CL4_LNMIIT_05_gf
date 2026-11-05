
# CL-4 Verification Plan

**DUT:** `combo_lock`  
**Specification:** CL4-SPEC-001, Revision 1.0  
**Verification Methodology:** Directed and Constrained-Random Simulation  
**Verification Framework:** Cocotb / Python Reference Model  
**Target Technology:** GF180MCU 180 nm  

---

## 1. Verification Overview

The objective of CL-4 verification is to ensure that the combination lock controller behaves according to the functional and timing requirements defined in CL4-SPEC-001.

The verification environment uses directed testing, a cycle-accurate Python reference model, randomized stimulus, and functional checks to validate the design.

The primary signals monitored during verification are:

- `state[2:0]` – Current FSM state.
- `attempt_count[1:0]` – Consecutive failure counter.
- `unlock` – Unlock status output.
- `locked_out` – Lockout status output.

All outputs are sampled after each rising clock edge has settled and are compared against the expected reference-model values.

## 2. Verification Methodology

The verification strategy consists of the following stages:

1. **Directed Testing:** Apply predefined input sequences to verify individual features and corner cases.
2. **Reference Model:** Implement an independent Python model of the specified CL-4 behavior.
3. **Cycle-by-Cycle Comparison:** Compare the DUT outputs against the reference model after every clock edge.
4. **Randomized Testing:** Generate random button sequences, bouncing inputs, and simultaneous presses.
5. **Parameter Verification:** Repeat configuration-dependent tests using different parameter combinations.
6. **Static Checks:** Perform RTL linting, synthesis inspection, and static timing analysis.

The testbench follows a driver-monitor-checker approach:

- **Driver:** Generates clock, reset, and button stimulus.
- **Monitor:** Samples DUT outputs after clock edges.
- **Reference Model:** Predicts the expected state and output values.
- **Checker:** Compares the observed DUT outputs with the expected values.

## 3. Functional Verification

The functional verification suite contains 35 test cases organized according to the major design features.

### 3.1 Reset Verification

| Test ID | Test Name | Verification Objective |
|---------|-----------|------------------------|
| F01 | `test_reset_values` | Verify initial FSM state, outputs, and failure counter after reset. |
| F02 | `test_reset_all_states` | Verify reset priority in every reachable FSM state. |
| F03 | `test_reset_clears_debouncers` | Verify synchronizer and debounce registers are cleared, including a button held through reset. |

Reset is synchronous and active-low. When `RST_SYNC=1`, the verification environment accounts for the two-flop reset synchronization latency.

### 3.2 Button Synchronization and Debounce

| Test ID | Test Name | Verification Objective |
|---------|-----------|------------------------|
| F04 | `test_debounce_latency` | Verify exact press recognition latency of D+1 edges. |
| F05 | `test_press_exactly_D` | Verify acceptance of a press lasting exactly D cycles. |
| F06 | `test_reject_D_minus_1_pulse` | Verify rejection of a pulse shorter than D cycles. |
| F07 | `test_button_bounce` | Verify bouncing inputs do not generate additional presses. |
| F08 | `test_held_button_single_press` | Verify a continuously held button generates only one press. |
| F09 | `test_release_debounce` | Verify release filtering and correct button re-arming. |

These tests validate the four independent button synchronizers and debounce filters.

### 3.3 Code Entry and Unlock

| Test ID | Test Name | Verification Objective |
|---------|-----------|------------------------|
| F10 | `test_correct_code_unlock` | Verify correct four-digit combinations enter UNLOCK. |
| F11 | `test_unlock_duration` | Verify unlock remains HIGH for exactly `UNLOCK_CYCLES`. |
| F12 | `test_unlock_clears_failure_count` | Verify successful entry clears the failure counter. |
| F13 | `test_wrong_digit_each_position` | Verify incorrect digits at all four positions generate FAIL. |
| F24 | `test_button_mapping` | Verify correct mapping of all four button inputs to digits. |

Testing includes different `CODE_VALUE` settings and combinations containing repeated digits.

### 3.4 Failure Counter and Lockout

| Test ID | Test Name | Verification Objective |
|---------|-----------|------------------------|
| F14 | `test_failure_count_increment` | Verify each failed attempt increments the counter exactly once. |
| F15 | `test_lockout_threshold` | Verify lockout begins on the MAX_ATTEMPTS-th failure. |
| F16 | `test_count_during_lockout` | Verify failure count remains at MAX_ATTEMPTS throughout lockout. |
| F17 | `test_lockout_duration` | Verify exact lockout duration. |
| F18 | `test_input_ignored_during_lockout` | Verify button presses are discarded during lockout. |
| F19 | `test_recovery_after_lockout` | Verify normal operation resumes after lockout expires. |

### 3.5 Press Qualification and Timeout

| Test ID | Test Name | Verification Objective |
|---------|-----------|------------------------|
| F20 | `test_simultaneous_presses` | Verify simultaneous button presses are rejected as invalid digits. |
| F21 | `test_abandoned_attempt` | Verify incomplete entries time out without counting as failures. |
| F22 | `test_timeout_boundary` | Verify correct digit acceptance at cycle N and handling at cycle N+1. |
| F23 | `test_timeout_disabled` | Verify N=0 disables the inter-digit timeout. |
| F32 | `test_press_during_fail` | Verify presses during FAIL are discarded. |
| F33 | `test_press_at_unlock_end` | Verify presses during the final UNLOCK cycle are discarded. |
| F34 | `test_held_across_lockout_end` | Verify a button held through lockout does not generate a delayed press. |

### 3.6 FSM and Output Verification

| Test ID | Test Name | Verification Objective |
|---------|-----------|------------------------|
| F25 | `test_output_decode` | Verify registered outputs correspond to the current FSM state. |
| F26 | `test_state_encoding` | Verify all seven FSM states use their specified encodings. |
| F28 | `test_no_unknown_outputs` | Verify no X/Z values appear on externally visible outputs after reset. |
| F29 | `test_port_interface` | Verify top-level module name, port names, directions, and widths. |
| F31 | `test_illegal_state_recovery` | Verify recovery from illegal state 3'b111. |
| F35 | `test_reset_synchronizer` | Verify two-flop reset synchronization when RST_SYNC=1. |

F35 is conditional and is required when the reset synchronizer is enabled.

## 4. Reference Model and Randomized Verification

### 4.1 Cycle-Accurate Reference Model

An independent Python reference model is used to predict the expected behavior of the combination lock controller.

The model follows the specified execution algorithm, including:

- FSM state transitions.
- Button press qualification.
- Debounce timing.
- Code comparison.
- Failure counting.
- Unlock and lockout timers.
- Inter-digit timeout.
- Reset priority.
- Registered output behavior.

The reference model uses pre-edge values and the specified operation priority to avoid mismatches caused by incorrect simulation scheduling.

After every rising clock edge settles, the following signals are compared:

```text
state
attempt_count
unlock
locked_out
```

Any mismatch must report the cycle number, input values, expected outputs, and actual DUT outputs.

### 4.2 Randomized Regression

Randomized testing is performed to expose corner cases that may not be covered by directed tests.

The regression requirements are:

- At least 100 randomized test runs.
- Each test runs for 5000 clock cycles.
- Random button activation and release timing.
- Button bounce sequences.
- Simultaneous button presses.
- Random idle intervals and incomplete entries.
- Comparison against the reference model on every cycle.

A fixed random seed should be used when reproducibility is required.

## 5. Parameter Configurations

Verification is performed using the following parameter configurations.

| Parameter | CFG-0 Default | CFG-1 Boundary | CFG-2 Repeated Digit | CFG-3 Alternate Code |
|-----------|---------------|----------------|---------------------|----------------------|
| `DEBOUNCE_CYCLES` | 24 | 1 | 4 | 8 |
| `MAX_ATTEMPTS` | 3 | 1 | 2 | 3 |
| `UNLOCK_CYCLES` | 100 | 7 | 8 | 15 |
| `LOCKOUT_CYCLES` | 200 | 9 | 12 | 20 |
| `INTERDIGIT_TIMEOUT_CYCLES` | 250 | 0 | 10 | 10 |
| `CODE_VALUE` | `8'h9C` | `8'h1B` | `8'h55` | `8'hE4` |
| `RST_SYNC` | 1 | 1 | 0 | 1 |

### Configuration Objectives

- **CFG-0:** Baseline verification using specification defaults.
- **CFG-1:** Boundary testing with D=1, MAX_ATTEMPTS=1, and disabled timeout.
- **CFG-2:** Verification of repeated digits using the combination 1-1-1-1.
- **CFG-3:** Verification using an alternate combination 3-2-1-0.

At least three additional legal configurations besides the defaults must be covered collectively by the configuration-dependent tests.

**CFG-4 – Operating Configuration:** The actual designer-declared operating values must be entered before final verification sign-off. These values are currently TBD.

For operating configurations, the inter-digit timeout must be either zero or at least D+2 cycles.

## 6. Static Checks and Implementation Verification

In addition to functional simulation, the following implementation checks are required.

| Check ID | Tool / Method | Acceptance Criteria |
|----------|---------------|-------------------|
| N1 | Verilator | `verilator --lint-only -Wall` must complete cleanly. Any waiver must be locally justified. |
| N2 | Yosys Synthesis | No inferred latches, multiplier cells, or divider cells. Flop count must match the specified formula. |
| N3 | Static Timing Analysis | Setup slack and hold slack must be greater than or equal to zero at all declared PVT corners. |
| N4 | Gate-Level Simulation | Optional reproduction of the successful-entry reference trace on the synthesized netlist. |

### Synthesis Flop Count

The expected flop count is calculated using:

```text
4 × (3 + max(1, ceil(log2(D)))) + 13 + F + 2 × RST_SYNC
```

Where:

- D = DEBOUNCE_CYCLES
- F = 1 when MAX_ATTEMPTS = 1; otherwise F = 2.
- RST_SYNC = Reset synchronizer enable.

Any differences due to technology mapping must be documented.

### Static Timing Analysis

STA must be performed using the declared clock period, input/output delays, and asynchronous input constraints.

The analysis must include:

- At least one slow setup corner.
- At least one fast hold corner.
- Worst-case setup slack.
- Worst-case hold slack.
- Corresponding PVT corner information.

Both setup and hold slack must be non-negative at every declared corner.

## 7. Verification Environment and Execution

The verification environment uses Cocotb with a supported RTL simulator such as Icarus Verilog or Verilator.

The testbench is responsible for generating clock and reset signals, driving button inputs, sampling DUT outputs, and comparing the observed results against the Python reference model.

The execution environment should record:

- Simulator and Cocotb versions.
- RTL source files and parameter overrides.
- Test names and individual results.
- Simulation logs and failure messages.
- Random seeds and regression results.

## 8. Acceptance Criteria

The CL-4 design is considered functionally verified when:

1. All mandatory functional tests F01–F34 pass.
2. F35 passes when `RST_SYNC=1`.
3. All required parameter configurations pass their applicable tests.
4. The cycle-accurate reference model reports no mismatches.
5. At least 100 randomized tests of 5000 cycles each complete successfully.
6. No unknown values appear on externally visible outputs after reset.

Implementation acceptance additionally requires:

- N1: Clean lint report.
- N2: Synthesis structure and flop count satisfy requirements.
- N3: Non-negative setup and hold slack at all declared corners.

N4 is optional unless separately required.

## 9. Verification Evidence and Reports

The following evidence must be maintained for project documentation and final submission:

| Evidence | Description |
|----------|-------------|
| Testbench source | Cocotb test files and supporting utilities |
| Reference model | Independent Python behavioral model |
| Simulation logs | Compile logs, execution logs, and test results |
| Regression summary | Individual test status and overall pass/fail summary |
| Coverage report | Functional coverage of required states, transitions, and scenarios |
| Parameter record | Exact parameter values used for each configuration |
| Lint report | Verilator lint output |
| Synthesis report | Yosys cell statistics and flop count |
| STA reports | Setup and hold timing reports for declared corners |

The hierarchical name of the FSM state register must also be recorded for F31 illegal-state testing.

---

## 10. Verification Status

This document defines the verification strategy and acceptance criteria for the CL-4 combination lock controller.

It is a verification plan and does not indicate that the RTL simulation, randomized regression, lint, synthesis, or timing checks have already been completed.

Final verification status will be updated based on actual simulation results and implementation reports.


