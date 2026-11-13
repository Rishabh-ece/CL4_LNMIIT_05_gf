<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

CL-4 is a parameterized 4-digit combination lock controller written in Verilog for Tiny Tapeout on the GF180 (180 nm) process. It reads a four-digit code from four independent push buttons, checks the entered sequence, and drives the unlock and lockout outputs. The default code is `2 → 1 → 3 → 0` (`CODE_VALUE = 8'h9C`).

### Architecture

```
btn[3:0] -> 2-FF sync -> debounce (x4) -> press_qualify -> code_compare -> entry_fsm -> unlock / locked_out
                                                                              |  ^
                                                              failure_counter +  + shared_timer
```

- **Button synchronizers**: each of the four buttons passes through its own 2-flop synchronizer before any other logic uses it.
- **Debounce filters**: each button has an independent filter. The debounced level changes only after the synchronized input has differed from it for `DEBOUNCE_CYCLES` consecutive clock cycles, in both directions. A completed 0 → 1 change produces a one-cycle press pulse. A held button gives exactly one press.
- **Press qualification and digit encoder**: a cycle counts as a digit only when exactly one button produces a press. Presses that complete in the same cycle are discarded, and they are neither correct nor a failure.
- **Digit storage and code comparator**: the first three digits are stored as they are accepted. When the fourth digit arrives, the full 8-bit entered code is compared with `CODE_VALUE`. Digits 1 to 3 are accepted without comparison.
- **Entry FSM**: a seven-state FSM (`IDLE`, `DIGIT2`, `DIGIT3`, `DIGIT4`, `UNLOCK`, `FAIL`, `LOCKOUT`). The code is judged in `DIGIT4`: a match goes to `UNLOCK`, a mismatch goes to `FAIL`.
- **Shared timer**: one 12-bit down-counter serves the inter-digit timeout, the unlock duration and the lockout duration. These uses are exclusive by state.
- **Failure counter**: a 2-bit counter of consecutive failed codes. After `MAX_ATTEMPTS` failures the FSM enters `LOCKOUT`. It does not expire with time. A successful unlock, the end of a lockout, or a reset clears it.
- **Output registers**: `unlock` and `locked_out` come straight from flip-flops loaded from the next state, so they always match the decoded `state`.

### FSM states

| `state[2:0]` | Name | Meaning |
|---|---|---|
| `000` | IDLE | Waiting for the first digit |
| `001` | DIGIT2 | First digit accepted |
| `010` | DIGIT3 | Two digits accepted |
| `011` | DIGIT4 | Three digits accepted; the fourth digit is compared |
| `100` | UNLOCK | Code correct, `unlock` = 1 |
| `101` | FAIL | Code wrong, lasts exactly one cycle |
| `110` | LOCKOUT | Too many failures, `locked_out` = 1 |
| `111` | (illegal) | Unreachable; returns to IDLE on the next edge |

### Parameters and timing

| Parameter | Value | Legal range |
|---|---:|---|
| `DEBOUNCE_CYCLES` | 16 | 1 to 32 |
| `MAX_ATTEMPTS` | 3 | 1 to 3 |
| `UNLOCK_CYCLES` | 4000 | 1 to 4095 |
| `LOCKOUT_CYCLES` | 4000 | 1 to 4095 |
| `INTERDIGIT_TIMEOUT_CYCLES` | 4000 | 0 to 4095 (0 disables the timeout) |
| `CODE_VALUE` | `8'h9C` | any 8-bit value |
| `RST_SYNC` | 1 | 0 or 1 |

The project clock is 1 kHz (`clock_hz: 1000` in `info.yaml`), so one cycle is 1 ms:

| Quantity | Cycles | Duration |
|---|---:|---|
| Debounce window | 16 | 16 ms |
| Unlock | 4000 | 4 s |
| Lockout | 4000 | 4 s |
| Inter-digit window | 4000 | 4 s |

A clean press first sampled high at edge `j` changes the FSM state at edge `j + D + 1`, where `D` is `DEBOUNCE_CYCLES`. If the timeout is enabled, it should be at least `D + 2` cycles.

### Clocking and reset

The design uses a single clock domain, and all state is clocked on the rising edge of `clk`. `rst_n` is active low. With `RST_SYNC = 1`, it passes through a two-flop reset synchronizer before it reaches the rest of the design. Reset clears the FSM, the failure counter, the timer, the stored digits, the outputs, and every button synchronizer and debouncer. A button held through reset produces one press after reset is released.

### Behavior summary

- A correct code asserts `unlock` for `UNLOCK_CYCLES`, then returns to IDLE and clears the failure count.
- A wrong code shows `FAIL` for one cycle and adds 1 to `attempt_count`.
- `MAX_ATTEMPTS` wrong codes in a row start a lockout of `LOCKOUT_CYCLES`. `attempt_count` stays at `MAX_ATTEMPTS` throughout, all button input is ignored (even the correct code), and the timer is not extended. When the lockout ends, the count clears and the first press is judged in IDLE.
- If the next digit does not arrive within the inter-digit window, the partial entry is dropped and the FSM returns to IDLE. This is an abandoned attempt and is not counted as a failure.
- Presses that arrive in `UNLOCK`, `FAIL` or `LOCKOUT` are discarded and never queued.

---

## How to test

### Pin mapping

| Pin | Signal | Direction | Description |
|---|---|---|---|
| `ui[0]` | BTN_0 | Input | Digit 0 button (active high) |
| `ui[1]` | BTN_1 | Input | Digit 1 button (active high) |
| `ui[2]` | BTN_2 | Input | Digit 2 button (active high) |
| `ui[3]` | BTN_3 | Input | Digit 3 button (active high) |
| `uo[0]` | UNLOCK | Output | High while the lock is open |
| `uo[1]` | LOCKED_OUT | Output | High during lockout |
| `uo[2]` | ATTEMPT_COUNT_0 | Output | Failure count, bit 0 |
| `uo[3]` | ATTEMPT_COUNT_1 | Output | Failure count, bit 1 |
| `uo[4]` | STATE_0 | Output | FSM state bit 0 (red) |
| `uo[5]` | STATE_1 | Output | FSM state bit 1 (green) |
| `uo[6]` | STATE_2 | Output | FSM state bit 2 (blue) |

`ui[7:4]`, `uo[7]` and all `uio` pins are unused. `clk` and `rst_n` are the standard Tiny Tapeout clock and reset.

### Operating the design

1. Apply the clock and hold `rst_n` low for at least `1 + 2 x RST_SYNC` rising clock edges (3 edges with `RST_SYNC = 1`), then release it.
2. Enter the code with the buttons. `btn[0]` to `btn[3]` are digits 0 to 3. For the default code, press `btn[2]`, `btn[1]`, `btn[3]`, `btn[0]` in that order.
3. Hold each button for at least `DEBOUNCE_CYCLES` (16 ms at 1 kHz). Release it for at least the same time before pressing the same button again.
4. Enter each next digit within the inter-digit window of the previous one (4 s at 1 kHz).
5. After a correct code, `unlock` goes high for 4 s, then the FSM returns to IDLE.
6. After three wrong codes in a row, `locked_out` goes high for 4 s and all button input is ignored.
7. Watch `state` (`uo[6:4]`) and `attempt_count` (`uo[3:2]`) to follow progress. With an RGB LED on `uo[4]` to `uo[6]`, its color shows the FSM state.

Because a wrong code is judged only after the fourth digit, `FAIL` appears after the fourth press, not at the first wrong digit.

The cocotb testbench is in the `test` directory. See `test/README.md` to run it. The verification plan is in [verification.md](verification.md).

## External hardware

- Four momentary push buttons, one per digit (0 to 3), connected to `ui[0]` to `ui[3]`.
- A pull-down resistor on every button line, so a released button reads 0. A floating input produces random presses.
- A 1 kHz clock source (the Tiny Tapeout clock) and the reset input.
- `unlock` and `locked_out` are logic-level outputs. An external driver is needed for relays, solenoids or high-current loads. LEDs on the outputs need series resistors.
- An optional RGB LED (with resistors) on `uo[4]` to `uo[6]` to show the FSM state.

No PMOD or other peripheral is required.
