# CL-4 Verification Report

**DUT:** `tt_um_CL4_LNMIIT` / `combo_lock`  
**Specification:** CL4-SPEC-001  
**Target:** GF180MCU (180 nm), post-layout gate-level netlist  
**Verification:** Cocotb RTL regression and post-layout GLS regression  
**Report updated:** 24 November 2026

## 1. Verification summary

| Verification layer | Test cases | Result | Status |
|---|---:|---:|---|
| RTL Cocotb regression | 35 test functions; F01–F36 and F39 (37 case IDs) | 34 passed, 1 conditionally skipped in the recorded default build | **DONE** |
| Post-layout GLS | 10 external-interface tests | 10 passed, 0 failed, 0 skipped | **DONE** |
| RTL reference-model checking | Included cycle-by-cycle in the RTL regression; dedicated randomized campaign F27 | Completed as recorded for the project | **DONE** |
| Lint / synthesis / hardening | Project flow | Reported completed for the project | **DONE** |
| Timing / physical signoff | Project flow | Marked completed per the user's project-completion instruction; retain the final tool reports as evidence | **DONE** |

**Important interpretation:** F23 is not a failed test. Its decorator skips it when `N != 0`; the active configuration has `N=4000`. F23 is the separate `N=0` configuration test. The RTL file contains 35 Cocotb test functions, with F10/F11 and F16/F17 sharing functions, and F39 retaining the illegal-state recovery objective that was previously labelled F31. F31 is now the follow-up complete-failure-entry case.

## 2. Active design configuration

| Parameter | Value |
|---|---:|
| DEBOUNCE_CYCLES (D) | 16 |
| MAX_ATTEMPTS | 3 |
| UNLOCK_CYCLES | 4000 |
| LOCKOUT_CYCLES | 4000 |
| INTERDIGIT_TIMEOUT_CYCLES (N) | 4000 |
| CODE_VALUE | `8'h9C` (digits 2, 1, 3, 0) |
| RST_SYNC | 1 |
| Timer width | 12 bits |
| Clock | 1 kHz |

At 1 kHz, 4000 clock cycles correspond to 4 seconds.

## 3. RTL verification cases

The RTL testbench uses a cycle-accurate reference model. It checks the design on every sampled cycle for state, attempt count, unlock, and lockout outputs. F25 output-decode checks and F28 no-X/Z checks are also enforced in the testbench scoreboard where applicable.

| Case | Cocotb test function | Verification objective | Status in active build |
|---|---|---|---|
| F01 | `test_reset_values` | Reset values: After reset: IDLE, attempt_count=0, unlock=0, locked_out=0; no X/Z.  | DONE |
| F02 | `test_reset_all_states` | Reset from every FSM state: Reset overrides IDLE, DIGIT2, DIGIT3, DIGIT4, UNLOCK, FAIL and LOCKOUT. | DONE |
| F03 | `test_reset_clears_debouncers` | Debouncer reset behavior: Button held across reset must produce exactly one qualified press after release. | DONE |
| F04 | `test_debounce_latency` | Debounce latency: A clean press changes state at the specified j+D+1 edge. | DONE |
| F05 | `test_press_exactly_D` | Exactly-D pulse: A stable-high pulse of exactly D cycles is accepted once. | DONE |
| F06 | `test_reject_D_minus_1_pulse` | Reject D−1 pulse: A D−1-cycle pulse is filtered. | DONE |
| F07 | `test_button_bounce` | Button bounce: Multiple bounce transitions before stable high result in one press. | DONE |
| F08 | `test_held_button_single_press` | Held button: A button held for at least 10×D cycles generates one press only. | DONE |
| F09 | `test_release_debounce` | Release debounce: A D−1-cycle low interval does not re-arm; a D-cycle release does. | DONE |
| F10 | `test_correct_code_unlock` | Correct code entry: Correct four-digit sequence traverses IDLE→DIGIT2→DIGIT3→DIGIT4→UNLOCK. | DONE |
| F11 | `test_correct_code_unlock` | Unlock duration: UNLOCK remains asserted for exactly UNLOCK_CYCLES. | DONE |
| F12 | `test_unlock_clears_failure_count` | Successful-entry counter clear: Entering UNLOCK clears attempt_count after prior failures. | DONE |
| F13 | `test_wrong_digit_each_position` | Wrong digit at each position: Mismatch in any position is not judged before digit four. | DONE |
| F14 | `test_failure_count_increment` | Failure count increment: Each complete wrong code increments the failure counter exactly once. | DONE |
| F15 | `test_lockout_threshold` | Lockout threshold: Lockout begins on the MAX_ATTEMPTS-th consecutive failure. | DONE |
| F16 | `test_lockout_count_and_duration` | Counter during lockout: attempt_count remains MAX_ATTEMPTS throughout lockout. | DONE |
| F17 | `test_lockout_count_and_duration` | Lockout duration: LOCKOUT lasts exactly LOCKOUT_CYCLES. | DONE |
| F18 | `test_input_ignored_during_lockout` | Ignore input during lockout: Correct-code button activity during lockout is ignored and does not extend lockout. | DONE |
| F19 | `test_recovery_after_lockout` | Recovery after lockout: Correct code is accepted after lockout expires. | DONE |
| F20 | `test_simultaneous_presses` | Simultaneous button presses: All 11 multi-button subsets are rejected; timer behavior is checked in a timed state. | DONE |
| F21 | `test_abandoned_attempt` | Abandoned entry timeout: Partial entry times out to IDLE without changing attempt_count. | DONE |
| F22 | `test_timeout_boundary` | Timeout boundary: A press judged in cycle N is accepted; one judged in N+1 is processed from IDLE. | DONE |
| F23 | `test_timeout_disabled` | Timeout disabled (N=0): With N=0, partial entry waits indefinitely and can still be completed. | SKIPPED (N=0-only) |
| F24 | `test_button_mapping` | Button mapping: All four button values are checked at every code position. | DONE |
| F25 | `test_output_decode` | Output decode / registered behavior: unlock and locked_out decode from state; outputs do not change between active clock edges. | DONE |
| F26 | `test_state_encoding` | FSM state encoding: Checks encodings 000 through 110 and that 111 is not observed in normal operation. | DONE |
| F27 | `test_cycle_exact_reference_model` | Random cycle-exact regression: Reference model compares outputs cycle-by-cycle during at least 100 runs × 5000 cycles. | DONE |
| F28 | `test_no_unknown_outputs` | No X/Z outputs: No unknown/high-impedance outputs after reset during exercised operation. | DONE |
| F29 | `test_port_interface` | Port interface: Checks core port names/widths and wrapper port widths; direction/no-extra-port checks require Yosys. | DONE |
| F30 | `test_parameter_configuration` | Parameter configuration sanity: Checks legal parameter ranges for the elaborated build; full matrix requires separate compile/run per parameter set. | DONE |
| F31 | `test_followup_failure_complete_entry` | Follow-up failure entry: Each consecutive failure is a fresh complete four-digit entry; lockout occurs at threshold. | DONE |
| F32 | `test_press_during_fail` | Press during FAIL: A press qualifying in the FAIL cycle is discarded and is not queued. | DONE |
| F33 | `test_press_at_unlock_end` | Press at end of UNLOCK: A press pulse in the final UNLOCK cycle is discarded. | DONE |
| F34 | `test_held_across_lockout_end` | Press across lockout end: Press completing during lockout is discarded even if held across expiry; a press completing after expiry is judged in IDLE. | DONE |
| F35 | `test_reset_synchronizer` | Reset synchronizer: Asynchronous assertion and two-edge synchronous deassertion are checked. | DONE |
| F36 | `test_short_async_reset_pulse` | Short asynchronous reset pulse: A sub-cycle reset pulse between clock edges is captured and reset release is synchronized. | DONE |
| F39 | `test_illegal_state_recovery` | Illegal-state recovery: Forced illegal state 111 returns to IDLE; checks failure/timer retention and lockout behavior. | DONE |

### RTL execution notes

- The recorded default RTL regression result is **34 passed, 0 failed, 1 skipped**.
- F23 is skipped at `N=4000` by design (`skip=(N != 0)`). To execute F23, compile the DUT with `N=0` and set the matching `CL4_N=0` environment value.
- F06, F07 and F09 are skipped only when `D < 2`; they are enabled for `D=16`.
- F12 is skipped only when `MAX_ATTEMPTS < 2`; it is enabled for `MAX_ATTEMPTS=3`.
- F33 is skipped only when `UNLOCK_CYCLES < D+3`; it is enabled for the active values.
- F34 is skipped only when `LOCKOUT_CYCLES < D+13`; it is enabled for the active values.
- F35 and F36 are skipped only when `RST_SYNC != 1`; they are enabled for `RST_SYNC=1`.
- F30 validates the currently elaborated parameter set. Its source explicitly states that a complete parameter matrix requires separate compile-and-run invocations for each configuration. The active configuration check is marked done; do not interpret that single run as evidence that every possible parameter combination was built.
- F29 checks names and widths in Cocotb. The source comments that port direction and absence of extra ports require a Yosys check.

## 4. Gate-level simulation (GLS) verification cases

The GLS testbench intentionally uses only the TinyTapeout external interface. It does not depend on internal RTL hierarchy, which may change after synthesis.

| Case | GLS test function | Verification objective | Status |
|---|---|---|---|
| GLS-01 | `gls_reset_and_interface` | Reset and interface: Reset state, output mapping, unused output pins and stable status. | DONE |
| GLS-02 | `gls_correct_code_and_unlock_duration` | Correct code and unlock duration: Correct 2-1-3-0 code unlocks; unlock duration is exactly 4000 cycles. | DONE |
| GLS-03 | `gls_wrong_digit_at_each_position` | Wrong digit at each position: Mismatch at each of four positions; failure verdict occurs only after digit four. | DONE |
| GLS-04 | `gls_failure_counter_and_lockout_threshold` | Failure counter and threshold: Three consecutive wrong entries increment once each and enter lockout at threshold. | DONE |
| GLS-05 | `gls_lockout_duration_and_recovery` | Lockout duration and recovery: Lockout lasts 4000 cycles, clears the count, then correct code is accepted. | DONE |
| GLS-06 | `gls_input_ignored_during_lockout` | Input ignored during lockout: Correct-code activity during lockout is ignored and not queued. | DONE |
| GLS-07 | `gls_debounce_short_pulse_and_held_button` | Debounce short pulse and held button: D−1 pulse rejected; long-held button accepted once. | DONE |
| GLS-08 | `gls_simultaneous_buttons_rejected` | Simultaneous buttons: Two buttons asserted together do not qualify as a digit. | DONE |
| GLS-09 | `gls_reset_during_partial_entry` | Reset during partial entry: Reset clears partial entry; subsequent correct code succeeds. | DONE |
| GLS-10 | `gls_interdigit_timeout` | Inter-digit timeout: Abandoned partial entry returns to IDLE without incrementing failure count. | DONE |

### GLS execution result

**Recorded result: 10 tests, 10 passed, 0 failed, 0 skipped.**

The GLS run used the fixed hardened-netlist configuration listed in Section 2. The simulation checks the `uo_out` state/attempt/lockout/unlock mapping, unused outputs, reset behavior, correct and incorrect code entry, debounce, simultaneous presses, lockout, recovery, and inter-digit timeout.

The GLS suite is a directed post-layout external-interface regression. It complements the larger RTL reference-model/random regression; it does not replace the RTL-only internal-state, illegal-state-injection, or cycle-exact model checks.

## 5. Tool-flow and signoff checklist

| Item | Status | Notes |
|---|---|---|
| RTL functional regression | DONE | Recorded 34 pass / 0 fail / 1 intentional conditional skip |
| RTL randomized reference-model campaign (F27) | DONE | Test source defaults to 100 runs × 5000 cycles; execution evidence should retain the actual run log and seed |
| Verilator lint | DONE | Reported clean in project progress |
| Synthesis / netlist generation | DONE | Hardened netlist available at `runs/wokwi/final/pnl/tt_um_CL4_LNMIIT.pnl.v` |
| GF180 standard-cell models | DONE | Used by the GLS setup |
| Post-layout GLS | DONE | 10/10 tests passed |
| Timing analysis / STA | DONE | Marked complete per project-completion instruction; archive the final STA report |
| Physical signoff / final implementation | DONE | Marked complete per project-completion instruction; archive final flow reports |

## 6. Reproduction commands

Run from the project's `test/` directory.

**RTL regression**
```bash
make -B sim
```

**Post-layout GLS**
```bash
source ~/ttsetup/env.sh
make -B GATES=yes sim
```

Use the project's Makefile and environment setup so that the RTL or gate-level test module and GF180 model files are selected correctly.

## 7. Evidence to retain in the repository

Recommended files under `docs/` or the repository root:

- `verification.md` — this report.
- `CL4_Verification_Tracker.xlsx` — case-by-case tracker and summary.
- RTL Cocotb regression log showing discovered, passed, failed and skipped counts.
- GLS log showing 10/10 pass.
- Verilator lint log.
- Synthesis and hardening reports, including the final netlist path.
- Final STA and physical implementation/signoff reports.

## 8. Completion statement

The RTL regression, directed post-layout GLS regression, lint, synthesis/hardening, timing analysis and physical signoff are marked **DONE** in this project report, as requested. The one RTL skip is an intentional configuration guard: F23 applies only to `N=0`, while the active hardened configuration uses `N=4000`. Keep the underlying run logs and final tool reports in the repository so that each completed item is independently auditable.
