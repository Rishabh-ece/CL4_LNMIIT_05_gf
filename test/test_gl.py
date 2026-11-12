
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


async def cycles(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")


@cocotb.test()
async def test_gate_level_smoke(dut):

    # Initialize inputs
    dut.clk.value = 0
    dut.rst_n.value = 1
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    cocotb.start_soon(
        Clock(dut.clk, 1, unit="ms").start()
    )

    # Wait for clock to start
    await FallingEdge(dut.clk)

    # Assert reset asynchronously
    dut.rst_n.value = 0

    # Allow asynchronous reset to propagate
    await Timer(1, unit="ns")

    # Check reset before clock edge
    out = int(dut.user_project.uo_out.value)

    assert (out & 0x7F) == 0, (
        f"Async reset failed: uo_out={out:08b}"
    )

    assert int(dut.user_project.uio_out.value) == 0
    assert int(dut.user_project.uio_oe.value) == 0

    # Hold reset
    await cycles(dut, 5)

    # Release reset
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1

    # Allow synchronizer and downstream logic to recover
    await cycles(dut, 5)

    # Check reset state
    out = int(dut.user_project.uo_out.value)

    state = (out >> 4) & 0x7
    attempts = (out >> 2) & 0x3
    unlock = out & 1
    locked_out = (out >> 1) & 1

    assert state == 0
    assert attempts == 0
    assert unlock == 0
    assert locked_out == 0

    # Enter correct code: CODE_VALUE = 8'h9C
    # Binary digits: 10, 01, 11, 00
    # Button mapping: 2, 1, 3, 0

    for digit in [2, 1, 3, 0]:

        await FallingEdge(dut.clk)
        dut.ui_in.value = 1 << digit

        await cycles(dut, 26)

        await FallingEdge(dut.clk)
        dut.ui_in.value = 0

        await cycles(dut, 26)

    # Check unlock
    out = int(dut.user_project.uo_out.value)

    unlock = out & 1
    state = (out >> 4) & 0x7

    assert unlock == 1, (
        f"Correct code failed to unlock: uo_out={out:08b}"
    )

    assert state == 4, (
        f"Expected UNLOCK state (100), got {state:03b}"
    )

    dut._log.info("Gate-level smoke test PASSED")
