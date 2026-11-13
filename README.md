![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# CL-4: 4-Digit Combination Lock Controller

A four-button, four-digit electronic combination lock, written in Verilog and built for [Tiny Tapeout](https://tinytapeout.com) on the GF180 (180 nm) process.

- Top module: `tt_um_CL4_LNMIIT`
- Core module: `combo_lock`
- Tile size: 1x1
- Clock: 1 kHz
- Authors: Rishabh Agrawal, Ankit Mawle (LNMIIT, Jaipur)
- Full project documentation: [docs/info.md](docs/info.md)

## What it does

You enter a 4-digit code using four push buttons (digit 0 to 3, one button per digit). The default code is **2 → 1 → 3 → 0**.

- **Correct code:** `unlock` goes high for 4 seconds, then the lock returns to idle.
- **Wrong code:** the lock shows a one-cycle FAIL and the attempt counter goes up by one.
- **3 wrong codes in a row:** the lock enters **lockout** for 4 seconds. Every button press is ignored, including the correct code, and `locked_out` stays high.
- **Walk away mid-entry:** if no next digit is pressed within 4 seconds, the partial entry is dropped. This is an *abandoned attempt* and does not count as a failure.

All buttons are synchronized and debounced independently, so noisy mechanical switches are fine.

## Pinout

| Pin | Name | Description |
|---|---|---|
| `ui[0]` | BTN_0 | Button for digit 0 (active high) |
| `ui[1]` | BTN_1 | Button for digit 1 (active high) |
| `ui[2]` | BTN_2 | Button for digit 2 (active high) |
| `ui[3]` | BTN_3 | Button for digit 3 (active high) |
| `uo[0]` | UNLOCK | High while the lock is open |
| `uo[1]` | LOCKED_OUT | High during lockout |
| `uo[2]` | ATTEMPT_COUNT_0 | Consecutive-failure count, bit 0 |
| `uo[3]` | ATTEMPT_COUNT_1 | Consecutive-failure count, bit 1 |
| `uo[4]` | STATE_0 | FSM state bit 0 (red) |
| `uo[5]` | STATE_1 | FSM state bit 1 (green) |
| `uo[6]` | STATE_2 | FSM state bit 2 (blue) |

`ui[7:4]`, `uo[7]` and all `uio` pins are unused. Fit a **pull-down resistor on every button line** so a released button reads 0. A floating input produces random presses.

`unlock` is a logic-level signal. Driving a lock solenoid, relay or LED needs an external driver.

## FSM states

The `state` output (`uo[6:4]`) shows the current FSM state:

| `state` | Name | Meaning |
|---|---|---|
| `000` | IDLE | Waiting for the first digit |
| `001` | DIGIT2 | First digit accepted |
| `010` | DIGIT3 | Two digits accepted |
| `011` | DIGIT4 | Three digits accepted |
| `100` | UNLOCK | Code correct, `unlock` = 1 |
| `101` | FAIL | Code wrong, lasts one cycle |
| `110` | LOCKOUT | Too many failures, `locked_out` = 1 |
| `111` | (illegal) | Unreachable; returns to IDLE on the next edge |

## How it works

```
btn[3:0] -> 2-FF sync -> debounce (x4) -> press_qualify -> code_compare -> entry_fsm -> unlock / locked_out
                                                                              |  ^
                                                              failure_counter +  + shared_timer
```

| Module | File | Role |
|---|---|---|
| `tt_um_CL4_LNMIIT` | `project.v` | Tiny Tapeout wrapper and pin mapping |
| `combo_lock` | `combo_lock.v` | Top-level integration, digit storage, parameter checks |
| `reset_sync` | `reset_sync.v` | Optional 2-flop reset synchronizer (`RST_SYNC`) |
| `button_debounce` | `button_debounce.v` | 2-FF synchronizer, symmetric debounce filter and one-cycle press pulse (one instance per button) |
| `press_qualify` | `press_qualify.v` | Accepts a cycle only if exactly one button press is present, and encodes it as a 2-bit digit |
| `code_compare` | `code_compare.v` | Compares the full 8-bit entered code with `CODE_VALUE` |
| `entry_fsm` | `entry_fsm.v` | Seven-state FSM, next-state logic, registered `unlock` and `locked_out` |
| `shared_timer` | `shared_time.v` | One 12-bit down-counter shared by the unlock, lockout and inter-digit timers |
| `failure_counter` | `failure_counter.v` | 2-bit consecutive-failure counter |

### Key design points

- **Debounce:** a button must differ from its debounced level for `D` consecutive cycles to change it, in both directions. A pulse shorter than `D` is filtered, and a held button gives exactly one press. A clean press first sampled at edge `j` changes the FSM state at edge `j + D + 1`.
- **Independent debouncers:** each button has its own filter, so two buttons pressed close together are never merged.
- **Simultaneous presses:** if two or more debounced presses complete in the same cycle, the cycle is not a digit. It is neither correct nor a failure.
- **Code check:** digits 1 to 3 are stored as they arrive, and the full 8-bit code is compared once, when the fourth digit arrives. A wrong code therefore enters FAIL after the fourth digit, rather than at the first wrong digit.
- **Failures never expire with time.** Only a successful unlock, the end of a lockout, or a reset clears the count.
- **During lockout** `attempt_count` stays at `MAX_ATTEMPTS`, input is ignored and the timer is not extended.
- **Lockout test** uses `fail >= MAX_ATTEMPTS - 1` rather than equality, so a corrupted counter cannot bypass lockout.
- **Registered outputs:** `unlock` and `locked_out` are driven directly from flip-flops loaded from the next state, so they always match the decoded `state`.

## Parameters

Set in `combo_lock`. Values outside the legal range are rejected at elaboration.

| Parameter | Value used | Legal range | Meaning |
|---|---:|---|---|
| `DEBOUNCE_CYCLES` (D) | 16 | 1 to 32 | Debounce window in clock cycles |
| `MAX_ATTEMPTS` | 3 | 1 to 3 | Consecutive failures before lockout |
| `UNLOCK_CYCLES` | 4000 | 1 to 4095 | Unlock duration |
| `LOCKOUT_CYCLES` | 4000 | 1 to 4095 | Lockout duration |
| `INTERDIGIT_TIMEOUT_CYCLES` (N) | 4000 | 0 to 4095 | Time allowed between digits; 0 disables the timeout |
| `CODE_VALUE` | `8'h9C` | any 8-bit value | Four 2-bit digits, first digit in bits [7:6] (`8'h9C` = 2, 1, 3, 0) |
| `RST_SYNC` | 1 | 0 or 1 | 1 passes `rst_n` through a 2-flop synchronizer |

At the 1 kHz clock set in `info.yaml`, one cycle is 1 ms:

| Quantity | Cycles | Wall-clock time |
|---|---:|---|
| Debounce window | 16 | 16 ms |
| Unlock | 4000 | 4 s |
| Lockout | 4000 | 4 s |
| Inter-digit window | 4000 | 4 s |

If you use a different clock, these durations scale with it. Choose the clock so that `D x clock period` is at least the bounce time of your switches. If `N` is not 0, keep `N >= D + 2`.

## How to use it

1. Apply `rst_n` low for a few clock cycles, then release it.
2. Press and hold each button for at least `D` cycles (16 ms at 1 kHz). A tap shorter than that is ignored.
3. Release a button for at least `D` cycles before pressing the same button again.
4. Enter the four digits in order, each within the inter-digit window of the previous one.
5. Watch `unlock` (`uo[0]`), `locked_out` (`uo[1]`), `attempt_count` (`uo[3:2]`) and `state` (`uo[6:4]`).

## Verification

The functional spec is [CL4-SPEC-001](docs/info.md), with a feature-by-feature verification plan (F01 to F35, plus lint, synthesis and timing checks). The plan includes a cycle-accurate reference model and at least 100 randomized tests of 5000 cycles each, with bounce and simultaneous presses.

Tests use [cocotb](https://www.cocotb.org/) and live in `test/`. To run them locally:

```sh
cd test
make
```

> **Status:** update this section as results come in. Do not mark an item as passing until the log shows it.

| Check | Status |
|---|---|
| Compile with all sources | not yet recorded |
| Verilator lint (`--lint-only -Wall`) | not yet recorded |
| Directed cocotb tests | not yet recorded |
| Reference-model and randomized regression | not yet recorded |
| Synthesis (latches, flop count) | not yet recorded |
| Static timing | not yet recorded |

## Build flow

The GitHub Actions in this repository build the ASIC with [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/), generate the documentation, run the tests and run the FPGA build.

To harden locally, see the [local hardening guide](https://www.tinytapeout.com/guides/local-hardening/).

## About Tiny Tapeout

Tiny Tapeout is an educational project that makes it easier and cheaper to get digital and analog designs manufactured on a real chip. Learn more at https://tinytapeout.com.

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Join the community](https://tinytapeout.com/discord)
- [Submit your design to the next shuttle](https://app.tinytapeout.com/)

## Repository

https://github.com/Rishabh-ece/CL4_LNMIIT_05_gf
