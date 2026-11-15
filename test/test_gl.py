# SPDX-License-Identifier: Apache-2.0
"""
CL-4 post-layout gate-level functional regression.

This testbench intentionally checks only the TinyTapeout external interface.
It does not depend on RTL hierarchy or internal signal names, which are not
stable after synthesis and physical implementation.

Fixed configuration in the hardened netlist:
    DEBOUNCE_CYCLES          = 16
    MAX_ATTEMPTS             = 3
    UNLOCK_CYCLES            = 4000
    LOCKOUT_CYCLES           = 4000
    INTERDIGIT_TIMEOUT       = 4000
    CODE_VALUE               = 8'h9C (digits 2, 1, 3, 0)
    RST_SYNC                 = 1

Run from test/:
    source ~/ttsetup/env.sh
    make -B GATES=yes

This is a directed GLS regression, not a replacement for the larger RTL
reference-model/random regression in test.py.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

# Values must match the parameters compiled into the hardened netlist.
D = 16
MAX_ATTEMPTS = 3
UNLOCK_CYCLES = 4000
LOCKOUT_CYCLES = 4000
INTERDIGIT_TIMEOUT = 4000
CODE_DIGITS = (2, 1, 3, 0)

IDLE = 0
DIGIT2 = 1
DIGIT3 = 2
DIGIT4 = 3
UNLOCK = 4
FAIL = 5
LOCKOUT = 6


def decode_status(value):
    """Decode TinyTapeout uo_out: state[6:4], attempts[3:2], lock[1], unlock[0]."""
    return {
        "state": (value >> 4) & 0x7,
        "attempts": (value >> 2) & 0x3,
        "locked_out": (value >> 1) & 1,
        "unlock": value & 1,
    }


class CL4GLS:
    def __init__(self, dut):
        self.dut = dut

    async def start(self):
        self.dut.clk.value = 0
        self.dut.rst_n.value = 1
        self.dut.ena.value = 1
        self.dut.ui_in.value = 0
        self.dut.uio_in.value = 0
        cocotb.start_soon(
            Clock(self.dut.clk, 10, unit="ns").start(start_high=False)
        )
        await FallingEdge(self.dut.clk)

    async def tick(self, count=1):
        for _ in range(count):
            await RisingEdge(self.dut.clk)
            # Let nonblocking assignments and gate delays settle.
            await Timer(2, unit="ns")

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.ui_in.value = 0
        self.dut.rst_n.value = 0
        await Timer(2, unit="ns")
        self.check_status(
            IDLE, 0, 0, 0, "asynchronous reset assertion"
        )
        await self.tick(4)
        await FallingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        # RST_SYNC=1: allow the synchronizer and downstream logic to release.
        await self.tick(5)
        self.check_status(IDLE, 0, 0, 0, "after reset release")
        self.check_unused_outputs()

    def raw_status(self):
        return int(self.dut.uo_out.value)

    def status(self):
        return decode_status(self.raw_status())

    def check_status(
        self,
        state=None,
        attempts=None,
        locked_out=None,
        unlock=None,
        context="",
    ):
        got = self.status()
        expected = {
            "state": state,
            "attempts": attempts,
            "locked_out": locked_out,
            "unlock": unlock,
        }
        for key, value in expected.items():
            if value is not None:
                assert got[key] == value, (
                    f"{context}: {key} expected {value}, got {got[key]}; "
                    f"uo_out=0b{self.raw_status():08b}, decoded={got}"
                )

    def check_unused_outputs(self):
        assert int(self.dut.uio_out.value) == 0, "uio_out must remain zero"
        assert int(self.dut.uio_oe.value) == 0, "uio_oe must remain zero"
        assert (self.raw_status() & 0x80) == 0, "uo_out[7] must remain zero"

    async def set_buttons(self, mask):
        await FallingEdge(self.dut.clk)
        self.dut.ui_in.value = mask & 0x0F

    async def press(self, digit, hold=None, release=None):
        """Apply one button press and fully debounce its release."""
        hold = D + 4 if hold is None else hold
        release = D + 4 if release is None else release
        await self.set_buttons(1 << digit)
        await self.tick(hold)
        await self.set_buttons(0)
        await self.tick(release)

    async def enter(self, digits=CODE_DIGITS):
        # Release between the first three digits, but return immediately after
        # the fourth digit is accepted so timed-state duration can be measured
        # from its entry edge.
        for digit in digits[:3]:
            await self.press(digit)
        await self.set_buttons(1 << digits[3])
        await self.tick(D + 2)

    async def wrong_entry(self, wrong_position=0):
        """Drive a complete wrong code and return while the one-cycle FAIL is visible."""
        digits = list(CODE_DIGITS)
        digits[wrong_position] = (digits[wrong_position] + 1) & 0x3
        for digit in digits[:3]:
            await self.press(digit)
        # Do not include the normal release interval here: FAIL lasts one cycle.
        await self.set_buttons(1 << digits[3])
        await self.tick(D + 2)


async def new_test(dut):
    tb = CL4GLS(dut)
    await tb.start()
    await tb.reset()
    return tb


@cocotb.test()
async def gls_reset_and_interface(dut):
    """Reset, output mapping, unused output pins, and known status."""
    tb = CL4GLS(dut)
    await tb.start()
    await tb.reset()

    for _ in range(20):
        await tb.tick()
        tb.check_unused_outputs()
        status = tb.status()
        assert status["state"] == IDLE
        assert status["attempts"] == 0
        assert status["unlock"] == 0
        assert status["locked_out"] == 0


@cocotb.test()
async def gls_correct_code_and_unlock_duration(dut):
    """Correct 2-1-3-0 code unlocks and unlock lasts exactly 4000 cycles."""
    tb = await new_test(dut)
    await tb.enter()

    tb.check_status(UNLOCK, 0, 0, 1, "correct code")

    await tb.tick(UNLOCK_CYCLES - 1)
    tb.check_status(UNLOCK, 0, 0, 1, "last unlock cycle")

    await tb.tick(1)
    tb.check_status(IDLE, 0, 0, 0, "unlock expiry")


@cocotb.test()
async def gls_wrong_digit_at_each_position(dut):
    """A mismatch in any of the four positions fails only after digit four."""
    tb = await new_test(dut)

    for position in range(4):
        if position:
            await tb.reset()

        digits = list(CODE_DIGITS)
        digits[position] = (digits[position] + 1) & 0x3

        for index, digit in enumerate(digits[:3]):
            await tb.press(digit)
            tb.check_status(
                index + 1, 0, 0, 0,
                f"wrong-position-{position}, collected digit {index + 1}"
            )

        await tb.set_buttons(1 << digits[3])
        await tb.tick(D + 2)

        tb.check_status(
            FAIL, 0, 0, 0,
            f"wrong-position-{position}, FAIL"
        )

        await tb.tick(1)
        tb.check_status(
            IDLE, 1, 0, 0,
            f"wrong-position-{position}, count increment"
        )

        await tb.set_buttons(0)
        await tb.tick(D + 4)


@cocotb.test()
async def gls_failure_counter_and_lockout_threshold(dut):
    """Three consecutive wrong entries cause lockout; count increments once each."""
    tb = await new_test(dut)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        await tb.wrong_entry(wrong_position=(attempt - 1) % 4)

        tb.check_status(
            FAIL, attempt - 1, 0, 0,
            f"attempt {attempt} FAIL"
        )

        await tb.tick(1)

        if attempt < MAX_ATTEMPTS:
            await tb.set_buttons(0)
            await tb.tick(D + 4)
            tb.check_status(
                IDLE, attempt, 0, 0,
                f"attempt {attempt} complete"
            )
        else:
            tb.check_status(
                LOCKOUT, MAX_ATTEMPTS, 1, 0,
                "lockout threshold"
            )


@cocotb.test()
async def gls_lockout_duration_and_recovery(dut):
    """Lockout lasts exactly 4000 cycles, clears count, then accepts correct code."""
    tb = await new_test(dut)

    for attempt in range(MAX_ATTEMPTS):
        await tb.wrong_entry(wrong_position=attempt)
        await tb.tick(1)

        if attempt < MAX_ATTEMPTS - 1:
            await tb.set_buttons(0)
            await tb.tick(D + 4)

    tb.check_status(
        LOCKOUT, MAX_ATTEMPTS, 1, 0,
        "lockout entry"
    )

    await tb.tick(LOCKOUT_CYCLES - 1)
    tb.check_status(
        LOCKOUT, MAX_ATTEMPTS, 1, 0,
        "last lockout cycle"
    )

    await tb.tick(1)
    tb.check_status(
        IDLE, 0, 0, 0,
        "lockout expiry"
    )

    await tb.enter()
    tb.check_status(
        UNLOCK, 0, 0, 1,
        "recovery after lockout"
    )


@cocotb.test()
async def gls_input_ignored_during_lockout(dut):
    """Correct-code button activity during lockout is ignored and not queued."""
    tb = await new_test(dut)

    for attempt in range(MAX_ATTEMPTS):
        await tb.wrong_entry(wrong_position=attempt)
        await tb.tick(1)

        if attempt < MAX_ATTEMPTS - 1:
            await tb.set_buttons(0)
            await tb.tick(D + 4)

    tb.check_status(
        LOCKOUT, MAX_ATTEMPTS, 1, 0,
        "lockout entry"
    )

    # Apply the correct sequence well before lockout expiry.
    for digit in CODE_DIGITS:
        await tb.press(digit)

    tb.check_status(
        LOCKOUT, MAX_ATTEMPTS, 1, 0,
        "inputs ignored during lockout"
    )

    await tb.tick(LOCKOUT_CYCLES + 2)
    tb.check_status(
        IDLE, 0, 0, 0,
        "lockout expires without queued input"
    )


@cocotb.test()
async def gls_debounce_short_pulse_and_held_button(dut):
    """A D-1 pulse is rejected; a stable press is accepted only once when held."""
    tb = await new_test(dut)

    await tb.set_buttons(1 << CODE_DIGITS[0])
    await tb.tick(D - 1)
    await tb.set_buttons(0)
    await tb.tick(D + 5)

    tb.check_status(
        IDLE, 0, 0, 0,
        "short pulse rejected"
    )

    await tb.set_buttons(1 << CODE_DIGITS[0])
    await tb.tick(10 * D)

    tb.check_status(
        DIGIT2, 0, 0, 0,
        "held button accepted once"
    )

    await tb.tick(2 * D)

    tb.check_status(
        DIGIT2, 0, 0, 0,
        "held button does not repeat"
    )


@cocotb.test()
async def gls_simultaneous_buttons_rejected(dut):
    """Two buttons asserted together do not qualify as a valid digit."""
    tb = await new_test(dut)

    await tb.set_buttons((1 << 1) | (1 << 2))
    await tb.tick(D + 8)

    await tb.set_buttons(0)
    await tb.tick(D + 8)

    tb.check_status(
        IDLE, 0, 0, 0,
        "simultaneous buttons rejected"
    )


@cocotb.test()
async def gls_reset_during_partial_entry(dut):
    """Asserting reset during a partial code clears entry progress."""
    tb = await new_test(dut)

    await tb.press(CODE_DIGITS[0])
    tb.check_status(
        DIGIT2, 0, 0, 0,
        "partial entry"
    )

    await tb.reset()
    tb.check_status(
        IDLE, 0, 0, 0,
        "reset clears partial entry"
    )

    await tb.enter()
    tb.check_status(
        UNLOCK, 0, 0, 1,
        "correct entry after reset"
    )


@cocotb.test()
async def gls_interdigit_timeout(dut):
    """An abandoned partial entry returns to IDLE without counting a failure."""
    tb = await new_test(dut)

    await tb.press(CODE_DIGITS[0])
    tb.check_status(
        DIGIT2, 0, 0, 0,
        "partial entry"
    )

    await tb.tick(INTERDIGIT_TIMEOUT + 2)

    tb.check_status(
        IDLE, 0, 0, 0,
        "inter-digit timeout"
    )
