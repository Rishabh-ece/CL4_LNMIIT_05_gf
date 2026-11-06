import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# CFG-0 defaults from the uploaded verification plan:
# D=24, MAX_ATTEMPTS=3, UNLOCK_CYCLES=100, LOCKOUT_CYCLES=200,
# INTERDIGIT_TIMEOUT_CYCLES=250, CODE_VALUE=8'h9C, RST_SYNC=1.
CLOCK_NS = 10
DEBOUNCE_WAIT = 35  # > D, allowing synchronizer/debounce latency
RESET_WAIT = 4      # accommodates the two-flop reset synchronizer

async def cycle(dut, count=1):
    for _ in range(count):
        await RisingEdge(dut.clk)
        # Sample after sequential/combinational updates have settled.
        await Timer(1, unit="ns")

def state(dut):
    return (int(dut.uo_out.value) >> 4) & 0b111

def attempts(dut):
    return (int(dut.uo_out.value) >> 2) & 0b11

def unlock(dut):
    return int(dut.uo_out.value) & 0b1

def locked_out(dut):
    return (int(dut.uo_out.value) >> 1) & 0b1

def check_reset_outputs(dut, context):
    value = int(dut.uo_out.value)
    assert ((value >> 4) & 0b111) == 0, f"{context}: FSM state is not IDLE"
    assert ((value >> 2) & 0b11) == 0, f"{context}: attempt_count is not zero"
    assert (value & 0b1) == 0, f"{context}: unlock is not zero"
    assert ((value >> 1) & 0b1) == 0, f"{context}: locked_out is not zero"

async def initialize(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await cycle(dut, RESET_WAIT)
    check_reset_outputs(dut, "during reset")
    dut.rst_n.value = 1
    await cycle(dut, RESET_WAIT)
    check_reset_outputs(dut, "after reset release")

async def press_button(dut, button):
    """Press one button long enough for CFG-0 debounce, then release it."""
    assert button in (0, 1, 2, 3)
    dut.ui_in.value = 1 << button
    await cycle(dut, DEBOUNCE_WAIT)
    dut.ui_in.value = 0
    await cycle(dut, DEBOUNCE_WAIT)

async def enter_correct_prefix(dut, digits):
    """Default CODE_VALUE=8'h9C is 2,1,3,0 (button indices)."""
    for button in digits:
        await press_button(dut, button)

async def reach_state(dut, target):
    # State encodings from CL4-SPEC-001 / RTL: IDLE=0, DIGIT2=1,
    # DIGIT3=2, DIGIT4=3, UNLOCK=4, FAIL=5, LOCKOUT=6.
    await initialize(dut)

    if target == 0:  # IDLE
        return
    if target == 1:
        await press_button(dut, 2)
    elif target == 2:
        await enter_correct_prefix(dut, [2, 1])
    elif target == 3:
        await enter_correct_prefix(dut, [2, 1, 3])
    elif target == 4:
        await enter_correct_prefix(dut, [2, 1, 3, 0])
    elif target == 5:
        # Wrong first digit: expected 2, send 0. FAIL lasts one cycle,
        # so detect it while the button is still being held.
        dut.ui_in.value = 1
        seen_fail = False
        for _ in range(DEBOUNCE_WAIT + 4):
            await cycle(dut, 1)
            if state(dut) == 5:
                seen_fail = True
                break
        dut.ui_in.value = 0
        assert seen_fail, f"Could not observe FAIL; state={state(dut)}"
        return
    elif target == 6:
        # Three wrong attempts; each wrong first digit is button 0.
        for _ in range(3):
            await press_button(dut, 0)
            # FAIL is one cycle and returns to IDLE or enters LOCKOUT.
            if state(dut) == 6:
                break
        assert state(dut) == 6, f"Could not reach LOCKOUT; state={state(dut)}"
        return
    else:
        raise ValueError(f"Unsupported state {target}")

    assert state(dut) == target, (
        f"Failed to reach state {target}; observed state={state(dut)}"
    )


@cocotb.test()
async def test_F02_reset_priority_in_every_fsm_state(dut):
    """F02: assert reset from each reachable FSM state and verify reset wins."""
    cocotb.start_soon(Clock(dut.clk, CLOCK_NS, unit="ns").start())

    state_names = {
        0: "IDLE",
        1: "DIGIT2",
        2: "DIGIT3",
        3: "DIGIT4",
        4: "UNLOCK",
        5: "FAIL",
        6: "LOCKOUT",
    }

    for target in range(7):
        await reach_state(dut, target)
        assert state(dut) == target, (
            f"F02 setup failed: expected {state_names[target]}, got {state(dut)}"
        )

        dut._log.info("F02: asserting reset from %s", state_names[target])
        dut.rst_n.value = 0
        await cycle(dut, RESET_WAIT)
        check_reset_outputs(dut, f"F02 reset from {state_names[target]}")

        # Release reset and reinitialize before setting up the next state.
        dut.ui_in.value = 0
        dut.rst_n.value = 1
        await cycle(dut, RESET_WAIT)
        check_reset_outputs(dut, f"F02 release after {state_names[target]}")

    dut._log.info("F02 PASS: reset priority verified from all seven FSM states")
