
<!--

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

-->

## How it works

CL-4 is a parameterized 4-digit combination lock controller designed using Verilog/SystemVerilog RTL for the SkyWater SKY130 standard-cell technology. It accepts a four-digit code through four independent push buttons, verifies the entered sequence, and controls the unlock and lockout outputs.

### Architecture

The design consists of the following blocks:

- **Button synchronizers** — Four independent 2-flop synchronizers convert the asynchronous button inputs into signals suitable for synchronous processing.
- **Debounce filters** — Each button has an independent debounce circuit. A transition is accepted only after the synchronized input differs from its debounced level for `DEBOUNCE_CYCLES` consecutive clock cycles. A valid press generates a one-cycle pulse.
- **Press qualification and digit encoder** — Accepts a digit only when exactly one button generates a press in a cycle. Simultaneous presses are discarded.
- **Code comparator** — Compares the encoded digit with the expected digit from the `CODE_VALUE` parameter. The default combination is `2 → 1 → 3 → 0`, represented by `8'h9C`.
- **Entry FSM** — A seven-state FSM consisting of `IDLE`, `DIGIT2`, `DIGIT3`, `DIGIT4`, `UNLOCK`, `FAIL`, and `LOCKOUT`. It tracks the entered digits and controls the lock operation.
- **Shared timer** — An 8-bit down-counter shared between inter-digit timeout, unlock duration, and lockout duration.
- **Failure counter** — A 2-bit counter that tracks consecutive incorrect digits. After `MAX_ATTEMPTS` failures, the controller enters LOCKOUT.
- **Output registers** — `unlock` and `locked_out` are registered outputs indicating the current lock condition.

### Default Parameters

| Parameter | Default Value |
|-----------|---------------|
| `DEBOUNCE_CYCLES` | 24 |
| `MAX_ATTEMPTS` | 3 |
| `UNLOCK_CYCLES` | 100 |
| `LOCKOUT_CYCLES` | 200 |
| `INTERDIGIT_TIMEOUT_CYCLES` | 250 |
| `CODE_VALUE` | `8'h9C` |
| `RST_SYNC` | 1 |

The clock period is designer-defined. All timing durations are specified in clock cycles.

### Clocking and Reset

The design uses a single clock domain with all state elements operating on the rising edge of `clk`. The reset `rst_n` is synchronous and active-low. When `RST_SYNC = 1`, it passes through a two-flop synchronizer before being used internally.

A correct combination asserts `unlock` for `UNLOCK_CYCLES`. Three consecutive incorrect attempts (by default) activate `locked_out` for `LOCKOUT_CYCLES`. An incomplete combination returns to IDLE after the inter-digit timeout without counting as a failure.

---

## How to test

### Input and Output Interface

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| `clk` | Input | 1 | System clock |
| `rst_n` | Input | 1 | Active-low reset |
| `btn` | Input | 4 | Four active-high push buttons |
| `unlock` | Output | 1 | Unlock status |
| `locked_out` | Output | 1 | Lockout status |
| `attempt_count` | Output | 2 | Consecutive failure count |
| `state` | Output | 3 | Current FSM state |

### Operating the Design

1. Apply the clock and assert `rst_n = 0` for at least `1 + 2 × RST_SYNC` rising clock edges. Release reset by setting `rst_n = 1`.
2. Press the buttons according to the required combination. `btn[0]`, `btn[1]`, `btn[2]`, and `btn[3]` represent digits 0, 1, 2, and 3, respectively.
3. Each button press must remain HIGH for at least `DEBOUNCE_CYCLES` synchronized cycles. Release the button for the same debounce duration before another press.
4. For the default combination, enter the sequence `btn[2] → btn[1] → btn[3] → btn[0]`.
5. On a correct entry, `unlock` becomes HIGH for 100 clock cycles before returning to IDLE.
6. On three consecutive incorrect digits, `locked_out` becomes HIGH for 200 clock cycles. Button inputs are ignored during this period.
7. The current FSM state and failure count can be observed through `state` and `attempt_count`.

The design can be simulated using Icarus Verilog or Verilator with a suitable testbench.

---

## External hardware

The design requires four momentary push buttons, one for each digit (0–3), along with a clock source and an active-low reset input.

Each button input requires an external pull-down resistor or an available pad pull-down to ensure a defined LOW state when released.

The `unlock` and `locked_out` signals are logic-level outputs. An external driver is required if they are used to control LEDs, relays, solenoids, or other loads.

No additional peripherals or PMOD modules are required for the basic RTL design.
