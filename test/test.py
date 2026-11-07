# SPDX-License-Identifier: Apache-2.0

"""

CL-4 combination lock - complete cocotb regression (one file, F01..F36).



Works on cocotb 2.x (uses unit="ns").  Two ways to run it:



  1. Tiny Tapeout wrapper (default, your current Makefile):

        TOPLEVEL = tb  ->  tb.user_project = tt_um_CL4_LNMIIT

     Only the default parameters (CFG-0) exist in this build.



  2. Directly on combo_lock (needed for the other parameter sets, F30):

        TOPLEVEL = combo_lock, and pass parameters with iverilog -P, e.g.

        COMPILE_ARGS += -Pcombo_lock.DEBOUNCE_CYCLES=1 ...

     and tell this file the same values through environment variables

        CL4_D, CL4_MAX_ATTEMPTS, CL4_UNLOCK_CYCLES, CL4_LOCKOUT_CYCLES,

        CL4_N, CL4_CODE, CL4_RST_SYNC

     The file detects which top level it got by looking for a `uo_out` port.



Conventions (all cycle numbers follow CL4-SPEC-001 section 1.2):

  * Inputs are driven on the FALLING clock edge, outputs are sampled on the

    FALLING clock edge.  Both are therefore race-free with respect to the

    rising edge that the design uses.

  * "edge k" = k-th rising edge counted by Tb.edge.  A button written just

    before a tick is first sampled high at edge j = Tb.edge + 1.

  * Reset model matches the instructor-selected architecture: asynchronous

    assertion through the reset synchronizer and all downstream resettable

    registers, with two-edge synchronous release when RST_SYNC=1.

  * A cycle-accurate reference model runs in lock-step on EVERY tick of EVERY

    test (F27, F25, F28 are therefore checked throughout the regression).



Every implemented Cocotb test states which plan item (F01..F36) it implements. N1-N4 are external tool-flow checks.

N1..N4 (lint, synthesis, STA, gate level) are tool flows, not cocotb tests.

"""



import collections

import os

import random



import cocotb

from cocotb.clock import Clock

from cocotb.triggers import FallingEdge, Timer



# ----------------------------------------------------------------------------

# Configuration (must match what was compiled into the DUT)

# ----------------------------------------------------------------------------

D = int(os.getenv("CL4_D", "24"))

MAXA = int(os.getenv("CL4_MAX_ATTEMPTS", "3"))

UNL = int(os.getenv("CL4_UNLOCK_CYCLES", "100"))

LOCK = int(os.getenv("CL4_LOCKOUT_CYCLES", "200"))

N = int(os.getenv("CL4_N", "250"))

CODE = int(os.getenv("CL4_CODE", "0x9C"), 0)

RS = int(os.getenv("CL4_RST_SYNC", "1"))



DIGITS = [(CODE >> 6) & 3, (CODE >> 4) & 3, (CODE >> 2) & 3, CODE & 3]

WRONGS = [b for b in range(4) if b != DIGITS[0]]  # wrong first digits



IDLE, DIGIT2, DIGIT3, DIGIT4, UNLOCK, FAIL, LOCKOUT, ILLEGAL = range(8)

STATE_NAMES = ["IDLE", "DIGIT2", "DIGIT3", "DIGIT4", "UNLOCK", "FAIL",

               "LOCKOUT", "ILLEGAL"]



N_RANDOM_TESTS = int(os.getenv("CL4_RANDOM_TESTS", "100"))

N_RANDOM_CYCLES = int(os.getenv("CL4_RANDOM_CYCLES", "5000"))

SEED = int(os.getenv("CL4_SEED", "20261107"))



TMO = dict(timeout_time=600, timeout_unit="sec")  # F27 runs 500,000 cycles at 1 ms/cycle





# ----------------------------------------------------------------------------

# Reference model - transliteration of spec section 7.1 (+6.3 debounce)

# ----------------------------------------------------------------------------

class RefModel:

    """Cycle-accurate model.  step(btn, rst_n) = one rising clock edge."""



    def __init__(self):

        # At simulation start raw active-low reset is held low. All

        # resettable registers are initialized by asynchronous assertion.

        self.rs1 = 0

        self.rs2 = 0

        self.known = False

        self._clear()



    def async_assert(self):

        """Asynchronously clear the reset synchronizer and every resettable block."""

        if RS:

            self.rs1 = 0

            self.rs2 = 0

        # internal_rst_n falls asynchronously (or follows rst_n directly

        # when RST_SYNC=0), so every child block's async-reset branch fires.

        self._clear()

        self.known = True



    def _clear(self):

        self.st = IDLE

        self.fail = 0

        self.tmr = 0

        self.unlock = 0

        self.locked_out = 0

        self.s1 = [0] * 4

        self.s2 = [0] * 4

        self.lvl = [0] * 4

        self.cnt = [0] * 4



    def force_state(self, v):

        self.st = v



    def outputs(self):

        return (self.st, self.fail, self.unlock, self.locked_out)



    def step(self, btn, rst_n):

        # reset path (pre-edge values)

        int_rst = self.rs2 if RS else rst_n

        self.rs2, self.rs1 = self.rs1, rst_n  # synchronizer, itself not reset

        if int_rst is None:

            self.known = False

            return

        if int_rst == 0:

            self._clear()

            self.known = True

            return

        if not self.known:

            return



        # debounce, using pre-edge values (6.3)

        press = [int(self.s2[i] and not self.lvl[i] and self.cnt[i] == D - 1)

                 for i in range(4)]

        for i in range(4):

            din = (btn >> i) & 1

            nlvl, ncnt = self.lvl[i], self.cnt[i]

            if self.s2[i] == self.lvl[i]:

                ncnt = 0

            elif self.cnt[i] == D - 1:

                nlvl = self.s2[i]

                ncnt = 0

            else:

                ncnt = self.cnt[i] + 1

            self.s2[i], self.s1[i] = self.s1[i], din

            self.lvl[i], self.cnt[i] = nlvl, ncnt



        valid = sum(press) == 1

        digit = press.index(1) if valid else 0



        st, fail, tmr = self.st, self.fail, self.tmr

        st_n, fail_n, tmr_n = st, fail, tmr

        if st in (IDLE, DIGIT2, DIGIT3, DIGIT4):

            if valid:

                if digit != DIGITS[st]:

                    st_n = FAIL

                elif st == DIGIT4:

                    st_n, tmr_n, fail_n = UNLOCK, (UNL - 1) & 0xFF, 0

                else:

                    st_n, tmr_n = st + 1, (N - 1) & 0xFF

            elif st != IDLE and N != 0:

                if tmr == 0:

                    st_n = IDLE

                else:

                    tmr_n = tmr - 1

        elif st == UNLOCK:

            if tmr == 0:

                st_n = IDLE

            else:

                tmr_n = tmr - 1

        elif st == FAIL:

            if fail >= MAXA - 1:

                st_n, tmr_n, fail_n = LOCKOUT, (LOCK - 1) & 0xFF, MAXA

            else:

                st_n, fail_n = IDLE, fail + 1

        elif st == LOCKOUT:

            if tmr == 0:

                st_n, fail_n = IDLE, 0

            else:

                tmr_n = tmr - 1

        else:  # illegal (101 is FAIL, 111 only)

            st_n = IDLE

        self.st, self.fail, self.tmr = st_n, fail_n, tmr_n

        self.unlock = int(st_n == UNLOCK)

        self.locked_out = int(st_n == LOCKOUT)





# ----------------------------------------------------------------------------

# Pin access layer (wrapper top or bare combo_lock)

# ----------------------------------------------------------------------------

Sample = collections.namedtuple(

    "Sample", "edge btn rst state att unlock lo")





def _width(handle):

    try:

        return len(handle)

    except TypeError:

        return 1





class Pins:

    def __init__(self, dut):

        self.dut = dut

        self.wrapper = hasattr(dut, "uo_out")

        self.core = dut.user_project.U_combo_lock if self.wrapper else dut



    def init(self):

        if self.wrapper:

            self.dut.ena.value = 1

            self.dut.uio_in.value = 0

            self.dut.ui_in.value = 0

        else:

            self.dut.btn.value = 0

        # Start deasserted so that the testbench can create a real 1->0

        # transition after the clock has started.  This guarantees that the

        # asynchronous reset blocks receive a negedge event at time zero.

        self.dut.clk.value = 0

        self.dut.rst_n.value = 1



    def drive(self, btn, rst):

        if self.wrapper:

            self.dut.ui_in.value = btn

        else:

            self.dut.btn.value = btn

        self.dut.rst_n.value = rst



    def read(self):

        """(state, att, unlock, locked_out) or None if any bit is X/Z."""

        try:

            if self.wrapper:

                v = int(self.dut.uo_out.value)

                return ((v >> 4) & 7, (v >> 2) & 3, v & 1, (v >> 1) & 1)

            return (int(self.dut.state.value), int(self.dut.attempt_count.value),

                    int(self.dut.unlock.value), int(self.dut.locked_out.value))

        except ValueError:

            return None



    @property

    def fsm_state_reg(self):  # hierarchical name for F31 (declare in design note)

        return self.core.U_entry_fsm.st





# ----------------------------------------------------------------------------

# Testbench object: clock, scoreboard, helpers

# ----------------------------------------------------------------------------

class Tb:

    def __init__(self, dut):

        self.dut = dut

        self.pins = Pins(dut)

        self.model = RefModel()

        self.btn = 0

        self.rst = 1

        self.edge = 0

        self.trace = []

        self.seen = collections.Counter()

        self.compared = 0



    # --- start-up ----------------------------------------------------------

    @classmethod

    async def create(cls, dut):

        tb = cls(dut)

        tb.pins.init()

        # Commit the initial HIGH reset level before starting the clock or

        # allowing a test to assert reset.  Without this time step, Icarus may

        # coalesce the initial HIGH and subsequent LOW writes, so no genuine

        # 1->0 edge reaches the asynchronous-reset logic.

        await Timer(1, unit="ns")



        cocotb.start_soon(Clock(dut.clk, 1, unit="ms").start(start_high=False))

        # Let the clock's initial value settle as a separate simulator event.

        # The test can now create a real raw-reset falling edge at any time.

        await Timer(1, unit="ns")

        return tb



    # --- stimulus ----------------------------------------------------------

    def set_btn(self, v):

        self.btn = v & 0xF

        self.pins.drive(self.btn, self.rst)



    def set_rst(self, v):

        old = self.rst

        self.rst = v

        self.pins.drive(self.btn, self.rst)

        # A raw reset falling edge asynchronously clears the synchronizer.

        # Its internal_rst_n output then asynchronously clears every child.

        if old == 1 and v == 0:

            self.model.async_assert()



    async def tick(self, n=1):

        for _ in range(n):

            b, r = self.btn, self.rst

            await FallingEdge(self.dut.clk)

            self._account(b, r)



    @property

    def last(self):

        return self.trace[-1]



    def mark(self):

        """Index of the newest sample (inclusive start for rle())."""

        return len(self.trace) - 1



    # --- scoreboard (F27/F25/F28 on every cycle) ---------------------------

    def _context(self):

        rows = self.trace[-8:]

        return "\n".join(

            "   edge %5d btn=%s rst=%d state=%s att=%s unlock=%s lo=%s" % (

                s.edge, format(s.btn, "04b"), s.rst,

                STATE_NAMES[s.state] if s.state is not None else "X",

                s.att, s.unlock, s.lo) for s in rows)



    def _account(self, btn, rst):

        self.edge += 1

        self.model.step(btn, rst)

        out = self.pins.read()

        if out is None:

            s = Sample(self.edge, btn, rst, None, None, None, None)

        else:

            s = Sample(self.edge, btn, rst, *out)

        self.trace.append(s)

        if not self.model.known:

            return

        # F28: no X/Z once reset has been applied

        assert out is not None, (

            "F28: X/Z on outputs after reset, edge %d\n%s" % (self.edge, self._context()))

        self.seen[s.state] += 1

        # F25: registered outputs equal the decode of state

        assert s.unlock == int(s.state == UNLOCK), (

            "F25: unlock != (state==UNLOCK) at edge %d\n%s" % (self.edge, self._context()))

        assert s.lo == int(s.state == LOCKOUT), (

            "F25: locked_out != (state==LOCKOUT) at edge %d\n%s" % (self.edge, self._context()))

        # F27: cycle-exact reference model

        exp = self.model.outputs()

        got = (s.state, s.att, s.unlock, s.lo)

        self.compared += 1

        assert got == exp, (

            "F27 MISMATCH at edge %d: inputs btn=%s rst_n=%d\n"

            "   expected (state,att,unlock,lo) = %s\n   DUT gave                       = %s\n"

            "   last cycles:\n%s" % (

                self.edge, format(btn, "04b"), rst,

                (STATE_NAMES[exp[0]],) + exp[1:], (STATE_NAMES[got[0]],) + got[1:],

                self._context()))



    def rle(self, mark, fn):

        out = []

        for s in self.trace[mark:]:

            v = fn(s)

            if out and out[-1][0] == v:

                out[-1][1] += 1

            else:

                out.append([v, 1])

        return [(v, n) for v, n in out]



    # --- helpers -----------------------------------------------------------

    async def reset(self, hold=None):

        hold = (1 + 2 * RS + 1) if hold is None else hold

        self.set_btn(0)

        self.set_rst(0)

        await self.tick(hold)

        self.set_rst(1)

        await self.tick(2 * RS + 2)

        self.expect(IDLE, 0, "after reset")



    async def expect_async_reset(self, why="async reset"):

        """Allow simulator updates to settle, then check outputs before a clock edge."""

        await Timer(1, unit="ns")

        out = self.pins.read()

        assert out is not None, "%s: X/Z on output immediately after reset assertion" % why

        diagnostics = []

        try:

            ir = int(self.pins.core.internal_rst_n.value)

            diagnostics.append("internal_rst_n=%d" % ir)

            assert ir == 0, "%s: internal_rst_n did not assert asynchronously (%s)" % (why, ", ".join(diagnostics))

        except AttributeError:

            pass

        try:

            fsm = self.pins.core.U_entry_fsm

            fsm_rst = int(fsm.rst_n.value)

            fsm_state = int(fsm.st.value)

            diagnostics.append("entry_fsm.rst_n=%d" % fsm_rst)

            diagnostics.append("entry_fsm.st=%d" % fsm_state)

            assert fsm_rst == 0, "%s: FSM reset pin is not low (%s)" % (why, ", ".join(diagnostics))

            assert fsm_state == IDLE, "%s: FSM state register did not asynchronously clear (%s)" % (why, ", ".join(diagnostics))

        except AttributeError:

            pass

        assert out == (IDLE, 0, 0, 0), (

            "%s: expected immediate (IDLE,0,0,0), got %s; %s" % (why, out, ", ".join(diagnostics)))



    def expect(self, state=None, att=None, why=""):

        s = self.last

        if state is not None:

            assert s.state == state, "%s: expected state %s, got %s (edge %d)\n%s" % (

                why, STATE_NAMES[state], STATE_NAMES[s.state], s.edge, self._context())

        if att is not None:

            assert s.att == att, "%s: expected attempt_count %d, got %d (edge %d)\n%s" % (

                why, att, s.att, s.edge, self._context())



    async def hold_until(self, mask, target, maxn=None):

        """Hold mask high until state == target; returns ticks used."""

        maxn = D + 10 if maxn is None else maxn

        self.set_btn(mask)

        for i in range(maxn):

            await self.tick(1)

            if self.last.state == target:

                return i + 1

        raise AssertionError("never reached %s (btn=%s)\n%s" % (

            STATE_NAMES[target], format(mask, "04b"), self._context()))



    async def tick_until(self, pred, maxn):

        for i in range(maxn):

            await self.tick(1)

            if pred(self.last):

                return i + 1

        raise AssertionError("condition not reached in %d ticks\n%s" % (maxn, self._context()))



    async def enter_digits(self, digs, start=0, gap=None, final_gap=None):

        """Press digits with exact D+1 latency check; returns entry edges."""

        gap = D + 2 if gap is None else gap

        final_gap = gap if final_gap is None else final_gap

        edges = []

        for k, b in enumerate(digs):

            pos = start + k

            target = pos + 1 if pos < 3 else UNLOCK

            n = await self.hold_until(1 << b, target)

            assert n == D + 2, "digit %d accepted after %d ticks, expected D+2=%d" % (

                pos, n, D + 2)

            edges.append(self.edge)

            self.set_btn(0)

            await self.tick(final_gap if k == len(digs) - 1 else gap)

        return edges



    async def fail_once(self, wrong, final_tick=True):

        n = await self.hold_until(1 << wrong, FAIL)

        assert n == D + 2, "wrong digit reached FAIL after %d ticks, expected %d" % (n, D + 2)

        self.set_btn(0)

        if final_tick:

            await self.tick(1)



    async def reach(self, target):

        """Reset, then drive the DUT to `target`; returns at the tick the state appears."""

        await self.reset()

        if target == IDLE:

            return

        if DIGIT2 <= target <= UNLOCK:

            await self.enter_digits(DIGITS[:target], gap=D + 2, final_gap=0)

        elif target == FAIL:

            await self.hold_until(1 << WRONGS[0], FAIL)

            self.set_btn(0)

        elif target == LOCKOUT:

            for k in range(MAXA):

                await self.fail_once(WRONGS[k % len(WRONGS)])

            self.expect(LOCKOUT, MAXA, "reach LOCKOUT")

            return

        else:

            raise ValueError(target)

        self.expect(target, None, "reach")





# ============================================================================

# F01 - F03  Reset

# ============================================================================

@cocotb.test(**TMO)

async def test_reset_values(dut):

    """F01: after reset state=IDLE, att=0, unlock=0, locked_out=0, no X/Z."""

    tb = await Tb.create(dut)

    tb.set_rst(0)

    await tb.expect_async_reset("F01 asynchronous assertion")

    await tb.tick(1 + 2 * RS)  # keep reset asserted across clock edges

    tb.set_rst(1)

    await tb.tick(2 * RS + 2)

    assert tb.model.known

    s = tb.last

    assert (s.state, s.att, s.unlock, s.lo) == (0, 0, 0, 0), "F01: %s" % (s,)

    if tb.pins.wrapper:

        assert int(dut.uo_out.value) >> 7 == 0, "uo_out[7] must be 0"

        assert int(dut.uio_oe.value) == 0 and int(dut.uio_out.value) == 0

    dut._log.info("F01 PASS")





@cocotb.test(**TMO)

async def test_reset_all_states(dut):

    """F02: reset wins from IDLE, DIGIT2-4, UNLOCK, FAIL and LOCKOUT."""

    tb = await Tb.create(dut)

    for target in (IDLE, DIGIT2, DIGIT3, DIGIT4, UNLOCK, LOCKOUT):

        await tb.reach(target)

        tb.set_rst(0)                       # assert between rising edges

        await tb.expect_async_reset("F02 reset from %s" % STATE_NAMES[target])

        await tb.tick(1 + 2 * RS)           # confirm values remain reset

        tb.expect(IDLE, 0, "F02 reset hold from %s" % STATE_NAMES[target])

        await tb.tick(2)

        tb.set_rst(1)

        await tb.tick(2 * RS + 2)

        dut._log.info("F02: reset from %s OK", STATE_NAMES[target])



    # FAIL lasts one cycle. With asynchronous assertion, pulling raw rst_n

    # low clears the synchronizer immediately; the FSM samples internal reset

    # on the very next rising edge, before FAIL can increment the counter.

    await tb.reset()

    tb.set_btn(1 << WRONGS[0])

    await tb.tick(D+2)

    tb.expect(FAIL, 0, "F02 FAIL setup")

    tb.set_rst(0)

    await tb.expect_async_reset("F02 reset from FAIL")

    await tb.tick(1)

    tb.expect(IDLE, 0, "F02 FAIL reset hold")

    tb.set_btn(0)

    await tb.tick(2)

    tb.set_rst(1)

    await tb.tick(2 * RS + 2)

    dut._log.info("F02 PASS (all seven states)")





@cocotb.test(**TMO)

async def test_reset_clears_debouncers(dut):

    """F03: a button held across reset gives exactly one press after release."""

    tb = await Tb.create(dut)

    for held, expect_fail in ((DIGITS[0], False), (WRONGS[0], True)):

        await tb.reset()

        tb.set_btn(1 << held)

        await tb.tick(2 * D + 12)             # press already consumed

        tb.set_rst(0)                         # button still held

        await tb.expect_async_reset("F03 debounce reset")

        await tb.tick(2 + 2 * RS)

        tb.expect(IDLE, 0, "F03 under reset")

        tb.set_rst(1)

        m = tb.edge + 1                       # first edge sampling rst_n high

        j = m + 2 * RS                        # first normal update (spec 7.3)

        change = j + D + 1

        await tb.tick(change - 1 - tb.edge)

        tb.expect(IDLE, 0, "F03 before debounce completes")

        await tb.tick(1)

        assert tb.edge == change

        tb.expect(FAIL if expect_fail else DIGIT2, 0, "F03 at edge j+D+1")

        await tb.tick(1)

        if expect_fail:

            if MAXA > 1:

                tb.expect(IDLE, 1, "F03 after FAIL")

            else:

                tb.expect(LOCKOUT, 1, "F03 after FAIL (MAX_ATTEMPTS=1)")

                await tb.tick(LOCK)

                tb.expect(IDLE, 0, "F03 lockout over")

        mk = tb.mark()

        tb.set_btn(1 << held)

        await tb.tick(min(10 * D, (N - 5) if N else 10 * D))   # keep holding

        extra = [s for s in tb.trace[mk:] if s.state == FAIL]

        assert not extra, "F03: second press produced while held"

        tb.expect(IDLE if expect_fail else DIGIT2,

                  (1 if MAXA > 1 else 0) if expect_fail else 0, "F03 hold")

        tb.set_btn(0)

    dut._log.info("F03 PASS")





# ============================================================================

# F04 - F09  Debounce

# ============================================================================

@cocotb.test(**TMO)

async def test_debounce_latency(dut):

    """F04: clean press first sampled high at edge j changes state at j+D+1."""

    tb = await Tb.create(dut)

    await tb.reset()

    for pos in range(4):

        prev = pos

        new = pos + 1 if pos < 3 else UNLOCK

        tb.set_btn(1 << DIGITS[pos])

        j = tb.edge + 1

        for _ in range(D + 2):

            await tb.tick(1)

            if tb.edge < j + D + 1:

                assert tb.last.state == prev, "F04: early change at edge %d (j=%d)" % (tb.edge, j)

            else:

                assert tb.edge == j + D + 1

                assert tb.last.state == new, "F04: no change at edge j+D+1=%d" % (j + D + 1)

        tb.set_btn(0)

        await tb.tick(D + 2)

    dut._log.info("F04 PASS (latency D+1 = %d edges, all 4 digits)", D + 1)





@cocotb.test(**TMO)

async def test_press_exactly_D(dut):

    """F05: a stable-high pulse of exactly D cycles registers once."""

    tb = await Tb.create(dut)

    await tb.reset()

    tb.set_btn(1 << DIGITS[0])

    j = tb.edge + 1

    mk = tb.mark()

    await tb.tick(D)

    tb.set_btn(0)

    await tb.tick(1)

    tb.expect(IDLE, None, "F05 edge j+D")

    await tb.tick(1)

    assert tb.edge == j + D + 1

    tb.expect(DIGIT2, 0, "F05 edge j+D+1")

    await tb.tick(min(3 * D, (N - 5) if N else 3 * D))

    tb.expect(DIGIT2, 0, "F05 no duplicate press")

    assert [v for v, _ in tb.rle(mk, lambda s: s.state)] == [IDLE, DIGIT2]

    dut._log.info("F05 PASS")





@cocotb.test(skip=(D < 2), **TMO)

async def test_reject_D_minus_1_pulse(dut):

    """F06: a pulse of D-1 cycles is filtered (D > 1)."""

    tb = await Tb.create(dut)

    for b in (DIGITS[0], WRONGS[0]):

        await tb.reset()

        mk = tb.mark()

        tb.set_btn(1 << b)

        await tb.tick(D - 1)

        tb.set_btn(0)

        await tb.tick(3 * D + 10)

        assert tb.rle(mk, lambda s: (s.state, s.att, s.unlock, s.lo))[-1][0] == (0, 0, 0, 0)

        assert [v for v, _ in tb.rle(mk, lambda s: s.state)] == [IDLE], "F06: pulse leaked"

    dut._log.info("F06 PASS")





@cocotb.test(skip=(D < 2), **TMO)

async def test_button_bounce(dut):

    """F07: >=3 bounce transitions before a stable high register exactly once."""

    tb = await Tb.create(dut)

    await tb.reset()

    b = 1 << DIGITS[0]

    h = [max(1, min(k, D - 1)) for k in (3, 5, 7, 2)]

    wave = [(1, h[0]), (0, 2), (1, h[1]), (0, 1), (1, h[2]), (0, 3), (1, h[3]), (0, 2)]

    mk = tb.mark()

    for lvl, n in wave:

        tb.set_btn(b if lvl else 0)

        await tb.tick(n)

    tb.set_btn(b)

    j = tb.edge + 1                       # first edge of the final stable-high run

    await tb.tick(D)

    tb.expect(IDLE, 0, "F07 before j+D+1")

    await tb.tick(1)

    assert tb.edge == j + D

    await tb.tick(1)

    assert tb.edge == j + D + 1

    tb.expect(DIGIT2, 0, "F07 at j+D+1")

    await tb.tick(8)

    for lvl, n in ((0, 3), (1, 2), (0, 2), (1, 1), (0, D + 6)):   # bouncing release

        tb.set_btn(b if lvl else 0)

        await tb.tick(n)

    assert [v for v, _ in tb.rle(mk, lambda s: s.state)] == [IDLE, DIGIT2], "F07: extra press"

    dut._log.info("F07 PASS")





@cocotb.test(**TMO)

async def test_held_button_single_press(dut):

    """F08: a button held for >=10*D cycles gives exactly one press."""

    tb = await Tb.create(dut)

    await tb.reset()

    mk = tb.mark()

    tb.set_btn(1 << DIGITS[0])

    await tb.tick(D + 2)

    tb.expect(DIGIT2, 0, "F08")

    await tb.tick(10 * D - (D + 2) if N == 0 or 10 * D < N - 5 else 5)

    tb.expect(DIGIT2, 0, "F08 during hold")

    if N:                              # keep holding through the timeout: still no re-press

        await tb.tick(N + 40)

        tb.expect(IDLE, 0, "F08 after timeout while still held")

    assert FAIL not in [v for v, _ in tb.rle(mk, lambda s: s.state)]

    assert [v for v, _ in tb.rle(mk, lambda s: s.state)][:2] == [IDLE, DIGIT2]

    tb.set_btn(0)

    dut._log.info("F08 PASS")





@cocotb.test(skip=(D < 2), **TMO)

async def test_release_debounce(dut):

    """F09: low for D-1 cycles does not re-arm; low for D cycles does."""

    tb = await Tb.create(dut)

    await tb.reset()

    b = DIGITS[0]

    tb.set_btn(1 << b)

    await tb.tick(D + 2)

    tb.expect(DIGIT2, 0, "F09 first press")

    mk = tb.mark()

    tb.set_btn(0)

    await tb.tick(D - 1)                   # short release

    tb.set_btn(1 << b)

    await tb.tick(D + 6)

    assert [v for v, _ in tb.rle(mk, lambda s: s.state)] == [DIGIT2], (

        "F09: short release re-armed the button")

    tb.set_btn(0)

    await tb.tick(D)                       # proper release

    tb.set_btn(1 << b)

    await tb.tick(D + 6)

    seq = [v for v, _ in tb.rle(mk, lambda s: s.state)]

    if DIGITS[1] != b:

        assert seq[:2] == [DIGIT2, FAIL] and seq.count(FAIL) == 1, "F09: seq %s" % seq

    else:

        assert seq[:2] == [DIGIT2, DIGIT3], "F09: seq %s" % seq

    dut._log.info("F09 PASS")





# ============================================================================

# F10 - F14  Code entry, unlock, failures

# ============================================================================

@cocotb.test(**TMO)

async def test_correct_code_unlock(dut):

    """F10 + F11: correct code walks IDLE..UNLOCK; unlock lasts UNLOCK_CYCLES."""

    tb = await Tb.create(dut)

    await tb.reset()

    mk = tb.mark()

    await tb.enter_digits(DIGITS, gap=D + 2, final_gap=0)

    tb.expect(UNLOCK, 0, "F10")

    await tb.tick(UNL + 5)

    seq = tb.rle(mk, lambda s: s.state)

    assert [v for v, _ in seq] == [IDLE, DIGIT2, DIGIT3, DIGIT4, UNLOCK, IDLE], seq

    assert dict(seq[4:5])[UNLOCK] == UNL, "F11: UNLOCK lasted %d" % seq[4][1]

    ul = tb.rle(mk, lambda s: s.unlock)

    assert [v for v, _ in ul] == [0, 1, 0] and ul[1][1] == UNL, "F11 unlock pulse %s" % ul

    dut._log.info("F10/F11 PASS (unlock = %d cycles)", UNL)





@cocotb.test(skip=(MAXA < 2), **TMO)

async def test_unlock_clears_failure_count(dut):

    """F12: entering UNLOCK clears attempt_count (from 1 and from 2)."""

    tb = await Tb.create(dut)

    for count in [c for c in (1, 2) if c <= MAXA - 1]:

        await tb.reset()

        for k in range(count):

            await tb.fail_once(WRONGS[k % len(WRONGS)])

            tb.expect(IDLE, k + 1, "F12 build-up")

        await tb.tick(D + 2)

        await tb.enter_digits(DIGITS, final_gap=0)

        tb.expect(UNLOCK, 0, "F12 UNLOCK entry")

        mk = tb.mark()

        await tb.tick(UNL + 5)

        assert all(v == 0 for v, _ in tb.rle(mk, lambda s: s.att)), "F12: att not 0 after unlock"

    dut._log.info("F12 PASS")





@cocotb.test(**TMO)

async def test_wrong_digit_each_position(dut):

    """F13: wrong digit at each position -> FAIL for one cycle -> IDLE, +1 failure."""

    tb = await Tb.create(dut)

    for pos in range(4):

        await tb.reset()

        if pos:

            await tb.enter_digits(DIGITS[:pos], gap=D + 2)

        mk = tb.mark()

        wrong = (DIGITS[pos] + 1) & 3

        await tb.hold_until(1 << wrong, FAIL)

        tb.expect(FAIL, 0, "F13 att during FAIL")

        tb.set_btn(0)

        await tb.tick(1)

        tb.expect(IDLE if MAXA > 1 else LOCKOUT, 1, "F13 after FAIL")

        await tb.tick(5)

        runs = tb.rle(mk, lambda s: s.state)

        assert [n for v, n in runs if v == FAIL] == [1], "F13 pos %d: FAIL runs %s" % (pos, runs)

        assert UNLOCK not in [v for v, _ in runs]

    dut._log.info("F13 PASS")





@cocotb.test(**TMO)

async def test_failure_count_increment(dut):

    """F14: each FAIL adds exactly 1, only when FAIL is left."""

    tb = await Tb.create(dut)

    await tb.reset()

    steps = min(2, MAXA - 1)

    for k in range(steps):

        await tb.hold_until(1 << WRONGS[k % 3], FAIL)

        tb.expect(FAIL, k, "F14 count must not change inside FAIL")

        tb.set_btn(0)

        await tb.tick(1)

        tb.expect(IDLE, k + 1, "F14 after FAIL")

        mk = tb.mark()

        await tb.tick(60)

        assert all(v == k + 1 for v, _ in tb.rle(mk, lambda s: s.att)), "F14: idle cycles changed count"

    dut._log.info("F14 PASS")





# ============================================================================

# F15 - F19, F34  Lockout

# ============================================================================

@cocotb.test(**TMO)

async def test_lockout_threshold(dut):

    """F15: lockout on the MAX_ATTEMPTS-th consecutive failure, not before."""

    tb = await Tb.create(dut)

    await tb.reset()

    for k in range(MAXA - 1):

        await tb.fail_once(WRONGS[k % 3])

        tb.expect(IDLE, k + 1, "F15 below threshold")

        assert tb.last.lo == 0

    await tb.hold_until(1 << WRONGS[(MAXA - 1) % 3], FAIL)

    tb.expect(FAIL, MAXA - 1, "F15 threshold FAIL")

    tb.set_btn(0)

    await tb.tick(1)

    tb.expect(LOCKOUT, MAXA, "F15 lockout")

    assert tb.last.lo == 1

    dut._log.info("F15 PASS (MAX_ATTEMPTS=%d)", MAXA)





@cocotb.test(**TMO)

async def test_lockout_count_and_duration(dut):

    """F16 + F17: attempt_count = MAX for the whole lockout, locked_out = LOCKOUT_CYCLES."""

    tb = await Tb.create(dut)

    await tb.reach(LOCKOUT)

    mk = tb.mark()

    await tb.tick(LOCK + 3)

    runs = tb.rle(mk, lambda s: (s.state, s.att, s.lo))

    assert runs[0] == ((LOCKOUT, MAXA, 1), LOCK), "F16/F17: lockout run %s" % (runs[:2],)

    assert runs[1][0] == (IDLE, 0, 0), "F16: count not cleared after lockout: %s" % (runs[1],)

    dut._log.info("F16/F17 PASS (lockout = %d cycles)", LOCK)





@cocotb.test(**TMO)

async def test_input_ignored_during_lockout(dut):

    """F18: the correct code during lockout does nothing and does not extend it."""

    tb = await Tb.create(dut)

    await tb.reach(LOCKOUT)

    mk = tb.mark()

    t = 0

    for k, b in enumerate(DIGITS):

        if t + (D + 2) + D + 3 >= LOCK:     # keep every press completing inside lockout

            break

        tb.set_btn(1 << b)

        await tb.tick(D + 2)

        t += D + 2

        if k < 3 and DIGITS[k + 1] == b:

            tb.set_btn(0)

            await tb.tick(D + 2)

            t += D + 2

    tb.set_btn(0)

    await tb.tick(LOCK - t + 3 * D)

    runs = tb.rle(mk, lambda s: s.state)

    assert runs[0] == (LOCKOUT, LOCK), "F18: lockout length changed: %s" % (runs[:2],)

    assert runs[1][0] == IDLE and len(runs) == 2, "F18: queued digits processed: %s" % runs

    assert UNLOCK not in tb.seen or tb.seen[UNLOCK] == 0

    dut._log.info("F18 PASS (%d digits pressed inside lockout)", k + 1)





@cocotb.test(**TMO)

async def test_recovery_after_lockout(dut):

    """F19: correct entry immediately after lockout unlocks."""

    tb = await Tb.create(dut)

    await tb.reach(LOCKOUT)

    await tb.tick_until(lambda s: s.state == IDLE, LOCK + 5)

    tb.expect(IDLE, 0, "F19 after lockout")

    await tb.enter_digits(DIGITS, final_gap=0)

    tb.expect(UNLOCK, 0, "F19")

    dut._log.info("F19 PASS")





@cocotb.test(skip=(LOCK < D + 13), **TMO)

async def test_held_across_lockout_end(dut):

    """F34: press completing inside lockout is discarded even if held across its end;

    a press completing after lockout ends is judged in IDLE."""

    tb = await Tb.create(dut)

    b = DIGITS[0]                        # correct first digit: would advance if mis-queued

    # (a) press completes mid-lockout, held through the end

    await tb.reach(LOCKOUT)

    L = tb.edge

    await tb.tick(LOCK - D - 12)         # first sample at L+LOCK-D-11 -> pulse in cycle L+LOCK-10

    tb.set_btn(1 << b)

    await tb.tick(10 + D + 1 + 3 * D)

    tb.expect(IDLE, 0, "F34(a)")

    assert tb.trace[-1].edge > L + LOCK + 2 * D

    # (b) pulse lands in the very last lockout cycle (tmr == 0)

    tb.set_btn(0)

    await tb.reach(LOCKOUT)

    L = tb.edge

    await tb.tick(LOCK - D - 2)          # first sample at L+LOCK-D-1 -> pulse in cycle L+LOCK

    tb.set_btn(1 << b)

    await tb.tick(D + 2)

    assert tb.edge == L + LOCK

    tb.expect(IDLE, 0, "F34(b) at edge L+LOCK")

    await tb.tick(3 * D)

    tb.expect(IDLE, 0, "F34(b) still held")

    # (c) debounce completes one cycle after lockout ends -> judged in IDLE

    tb.set_btn(0)

    await tb.reach(LOCKOUT)

    L = tb.edge

    await tb.tick(LOCK - D - 1)          # first sample at L+LOCK-D -> pulse in cycle L+LOCK+1

    tb.set_btn(1 << b)

    await tb.tick(D + 1)

    assert tb.edge == L + LOCK

    tb.expect(IDLE, 0, "F34(c) lockout over")

    await tb.tick(1)

    tb.expect(DIGIT2, 0, "F34(c) judged as first digit")

    tb.set_btn(0)

    dut._log.info("F34 PASS")





# ============================================================================

# F20, F32  Press qualification

# ============================================================================

@cocotb.test(**TMO)

async def test_simultaneous_presses(dut):

    """F20: presses completing in the same cycle are not a digit (all 11 subsets)."""

    tb = await Tb.create(dut)

    await tb.reset()

    mk = tb.mark()

    for mask in range(16):

        if bin(mask).count("1") < 2:

            continue

        tb.set_btn(mask)

        await tb.tick(D + 8)

        tb.set_btn(0)

        await tb.tick(D + 3)

        assert [v for v, _ in tb.rle(mk, lambda s: (s.state, s.att))] == [(IDLE, 0)], (

            "F20: mask %s advanced or failed" % format(mask, "04b"))

    # inside a timed state: the timer keeps counting and is not extended

    if N:

        await tb.reset()

        await tb.enter_digits(DIGITS[:1], final_gap=0)

        e0 = tb.edge

        mk = tb.mark()

        tb.set_btn(0b1001)

        await tb.tick(D + 8)

        tb.set_btn(0)

        await tb.tick(N + 3)

        runs = tb.rle(mk, lambda s: s.state)

        assert runs[0] == (DIGIT2, N), "F20: timer disturbed: %s" % (runs[:2],)

        assert runs[1][0] == IDLE and tb.last.att == 0

    dut._log.info("F20 PASS")





@cocotb.test(**TMO)

async def test_press_during_fail(dut):

    """F32: a press whose pulse falls in the FAIL cycle is discarded, not queued."""

    tb = await Tb.create(dut)

    await tb.reset()

    A, B = WRONGS[0], DIGITS[0]          # B is the correct first digit

    tb.set_btn(1 << A)

    await tb.tick(1)

    tb.set_btn((1 << A) | (1 << B))      # B first sampled one edge later -> pulse in FAIL cycle

    await tb.tick_until(lambda s: s.state == FAIL, D + 6)

    await tb.tick(1)

    if MAXA > 1:

        tb.expect(IDLE, 1, "F32 after FAIL")

    else:

        tb.expect(LOCKOUT, 1, "F32 after FAIL (MAX_ATTEMPTS=1)")

        await tb.tick(LOCK)

        tb.expect(IDLE, 0, "F32 lockout over")

    await tb.tick(3 * D)

    tb.expect(IDLE, 1 if MAXA > 1 else 0, "F32 nothing queued")

    tb.set_btn(0)

    await tb.tick(D + 3)

    await tb.enter_digits(DIGITS, final_gap=0)

    tb.expect(UNLOCK, 0, "F32 next entry starts from IDLE")

    dut._log.info("F32 PASS")





# ============================================================================

# F21 - F23  Inter-digit timeout

# ============================================================================

@cocotb.test(skip=(N == 0), **TMO)

async def test_abandoned_attempt(dut):

    """F21: timeout returns to IDLE, attempt_count unchanged (from 0 and from 2)."""

    tb = await Tb.create(dut)

    for pre in [p for p in (0, 2) if p <= MAXA - 1]:

        for k in (1, 2, 3):

            await tb.reset()

            for i in range(pre):

                await tb.fail_once(WRONGS[i % 3])

            await tb.tick(D + 2)

            await tb.enter_digits(DIGITS[:k], final_gap=0)

            tb.expect(k, pre, "F21 setup")

            mk = tb.mark()

            await tb.tick(N + 3)

            runs = tb.rle(mk, lambda s: (s.state, s.att))

            assert runs[0] == ((k, pre), N), "F21 k=%d pre=%d: %s" % (k, pre, runs[:2])

            assert runs[1][0] == (IDLE, pre), "F21: attempt count changed: %s" % (runs[1],)

    dut._log.info("F21 PASS")





@cocotb.test(skip=(N == 0 or N < D + 2), **TMO)

async def test_timeout_boundary(dut):

    """F22: press judged in cycle N is accepted; in cycle N+1 it is judged in IDLE."""

    tb = await Tb.create(dut)

    nxt = DIGITS[1]

    assert nxt != DIGITS[0], "F22 needs different 1st/2nd digit (no re-arm possible)"



    async def to_digit2():

        await tb.reset()

        await tb.enter_digits(DIGITS[:1], final_gap=0)   # returns at entering edge e0

        return tb.edge



    # run A: pulse in cycle N (also N-1) -> accepted as digit 2

    for delta, expect_state in ((-1, DIGIT3), (0, DIGIT3)):

        e0 = await to_digit2()

        await tb.tick(N + delta - D - 2)

        tb.set_btn(1 << nxt)

        await tb.tick(D + 1)

        assert tb.edge == e0 + N + delta - 1

        tb.expect(DIGIT2, 0, "F22 edge before judge")

        await tb.tick(1)

        assert tb.edge == e0 + N + delta

        tb.expect(expect_state, 0, "F22 press in cycle N%+d" % delta)

        tb.set_btn(0)

    # run B: pulse in cycle N+1 -> timeout first, then judged as first digit in IDLE

    e0 = await to_digit2()

    await tb.tick(N - D - 1)

    tb.set_btn(1 << nxt)

    await tb.tick(D)

    tb.expect(DIGIT2, 0, "F22 B before")

    await tb.tick(1)

    assert tb.edge == e0 + N

    tb.expect(IDLE, 0, "F22 B timeout")

    await tb.tick(1)

    tb.expect(FAIL, 0, "F22 B judged in IDLE as wrong first digit")

    await tb.tick(1)

    tb.expect(IDLE if MAXA > 1 else LOCKOUT, 1, "F22 B counted as failure")

    dut._log.info("F22 PASS")





@cocotb.test(skip=(N != 0), **TMO)

async def test_timeout_disabled(dut):

    """F23: with N=0 the FSM waits indefinitely in DIGIT2."""

    tb = await Tb.create(dut)

    await tb.reset()

    await tb.enter_digits(DIGITS[:1], final_gap=0)

    mk = tb.mark()

    await tb.tick(1000)

    assert [v for v, _ in tb.rle(mk, lambda s: (s.state, s.att))] == [(DIGIT2, 0)]

    await tb.enter_digits(DIGITS[1:], start=1, final_gap=0)

    tb.expect(UNLOCK, 0, "F23 completion")

    dut._log.info("F23 PASS")





# ============================================================================

# F24 - F26  Mapping, decode, encoding

# ============================================================================

@cocotb.test(**TMO)

async def test_button_mapping(dut):

    """F24: at each position every button is judged correctly (16 combinations)."""

    tb = await Tb.create(dut)

    for pos in range(4):

        for b in range(4):

            await tb.reset()

            if pos:

                await tb.enter_digits(DIGITS[:pos])

            if b == DIGITS[pos]:

                await tb.hold_until(1 << b, pos + 1 if pos < 3 else UNLOCK)

            else:

                await tb.hold_until(1 << b, FAIL)

            tb.set_btn(0)

    dut._log.info("F24 PASS")





@cocotb.test(**TMO)

async def test_output_decode(dut):

    """F25: unlock/locked_out == decode of state every cycle; no combinational btn path."""

    tb = await Tb.create(dut)

    rng = random.Random(SEED)

    for target in (IDLE, DIGIT2, UNLOCK, LOCKOUT):

        await tb.reach(target)

        for _ in range(20):

            before = tb.pins.read()

            tb.set_btn(rng.randrange(16))

            await Timer(1, unit="ns")

            assert tb.pins.read() == before, "F25: outputs reacted to btn between edges"

            await Timer(3, unit="ns")

            assert tb.pins.read() == before, "F25: outputs changed between rising edges"

            await tb.tick(1)

        tb.set_btn(0)

    assert tb.compared > 0

    dut._log.info("F25 PASS (%d cycles decode-checked in this test)", tb.compared)





@cocotb.test(**TMO)

async def test_state_encoding(dut):

    """F26: state output = 000,001,010,011,100,101,110 and never 111."""

    tb = await Tb.create(dut)

    for target in (IDLE, DIGIT2, DIGIT3, DIGIT4, UNLOCK, FAIL, LOCKOUT):

        await tb.reach(target)

        assert tb.last.state == target, "F26: %s != %d" % (STATE_NAMES[target], target)

    assert tb.seen[ILLEGAL] == 0, "F26: illegal encoding 111 observed"

    dut._log.info("F26 PASS")





# ============================================================================

# F28, F29  No-X and ports

# ============================================================================

@cocotb.test(**TMO)

async def test_no_unknown_outputs(dut):

    """F28: no X/Z after reset (checked every cycle by the scoreboard)."""

    tb = await Tb.create(dut)

    await tb.reset()

    await tb.enter_digits(DIGITS, final_gap=0)

    await tb.tick(UNL + 3)

    await tb.reach(LOCKOUT)

    await tb.tick(LOCK + 3)

    assert tb.compared > LOCK

    dut._log.info("F28 PASS (%d cycles checked)", tb.compared)





@cocotb.test(**TMO)

async def test_port_interface(dut):

    """F29: combo_lock port names/widths (extra-port check: use yosys, see notes)."""

    tb = await Tb.create(dut)

    core = tb.pins.core

    widths = {"clk": 1, "rst_n": 1, "btn": 4, "unlock": 1, "locked_out": 1,

              "attempt_count": 2, "state": 3}

    for name, w in widths.items():

        assert hasattr(core, name), "F29: port %s missing" % name

        assert _width(getattr(core, name)) == w, "F29: %s width %d != %d" % (

            name, _width(getattr(core, name)), w)

    if tb.pins.wrapper:

        for name in ("ui_in", "uo_out", "uio_in", "uio_out", "uio_oe"):

            assert _width(getattr(dut.user_project, name)) == 8, name

    dut._log.info("F29 PASS (names/widths); port DIRECTION and 'no extra ports' need a yosys check")





# ============================================================================

# F30  Parameter configuration sanity (repeat this test for each build)

# ============================================================================

@cocotb.test(**TMO)

async def test_parameter_configuration(dut):

    """F30: validate the parameter set for this elaborated build.



    A single elaborated DUT cannot change Verilog parameters at runtime. The

    full F30 matrix is completed by recompiling and rerunning this test for

    each required parameter set, with CL4_* environment values matching the

    compile-time overrides.

    """

    assert 1 <= D <= 32, "F30: DEBOUNCE_CYCLES must be in 1..32"

    assert 1 <= MAXA <= 3, "F30: MAX_ATTEMPTS must be in 1..3"

    assert 1 <= UNL <= 255, "F30: UNLOCK_CYCLES must be in 1..255"

    assert 1 <= LOCK <= 255, "F30: LOCKOUT_CYCLES must be in 1..255"

    assert 0 <= N <= 255, "F30: INTERDIGIT_TIMEOUT_CYCLES must be in 0..255"

    assert 0 <= CODE <= 255, "F30: CODE_VALUE must fit in 8 bits"

    assert RS in (0, 1), "F30: RST_SYNC must be 0 or 1"

    tb = await Tb.create(dut)

    await tb.reset()

    dut._log.info(

        "F30 PASS for this build: D=%d MAX_ATTEMPTS=%d UNLOCK=%d LOCKOUT=%d N=%d CODE=0x%02X RST_SYNC=%d; rerun with compile-time overrides for the full matrix",

        D, MAXA, UNL, LOCK, N, CODE, RS)





# ============================================================================

# F31  Illegal state recovery

# ============================================================================

@cocotb.test(**TMO)

async def test_illegal_state_recovery(dut):

    """F31: forcing st=111 returns to IDLE, fail/tmr unchanged, lockout still works."""

    tb = await Tb.create(dut)

    st_reg = tb.pins.fsm_state_reg

    core = tb.pins.core



    async def inject():

        st_reg.value = ILLEGAL

        tb.model.force_state(ILLEGAL)

        await Timer(1, unit="ns")



    # A) from IDLE with one failure on record (needs MAX_ATTEMPTS > 1)

    if MAXA > 1:

        await tb.reset()

        await tb.fail_once(WRONGS[0])

        tb.expect(IDLE, 1, "F31 A setup")

        await inject()

        assert tb.pins.read()[0] == ILLEGAL, "F31: forced value did not reach the state output"

        await tb.tick(1)

        tb.expect(IDLE, 1, "F31 A recovery")



    # B) injected during LOCKOUT: att stays MAX, tmr unchanged, next failure locks out again

    await tb.reset()

    await tb.reach(LOCKOUT)

    await tb.tick(min(30, LOCK - 5))

    tmr_before = int(core.tmr.value)

    await inject()

    await tb.tick(1)

    tb.expect(IDLE, MAXA, "F31 B recovery from LOCKOUT")

    assert tb.last.lo == 0

    assert int(core.tmr.value) == tmr_before, "F31: timer changed during illegal-state recovery"

    await tb.tick(D + 2)

    mk = tb.mark()

    await tb.hold_until(1 << WRONGS[0], FAIL)

    tb.set_btn(0)

    await tb.tick(1)

    tb.expect(LOCKOUT, MAXA, "F31 B: failure after upset must lock out (>= test)")

    await tb.tick(LOCK + 2)

    tb.expect(IDLE, 0, "F31 B end")

    dut._log.info("F31 PASS (forced %s)", "tb.user_project.U_combo_lock.U_entry_fsm.st"

                  if tb.pins.wrapper else "U_entry_fsm.st")





# ============================================================================

# F33  Press at end of UNLOCK

# ============================================================================

@cocotb.test(skip=(UNL < D + 3), **TMO)

async def test_press_at_unlock_end(dut):

    """F33: a press pulse in the last UNLOCK cycle is discarded."""

    tb = await Tb.create(dut)

    await tb.reset()

    await tb.enter_digits(DIGITS, final_gap=0)

    u = tb.edge

    tb.expect(UNLOCK, 0, "F33")

    await tb.tick(UNL - D - 2)                # first sample at u+UNL-D-1 -> pulse in cycle u+UNL

    tb.set_btn(1 << DIGITS[0])

    await tb.tick(D + 1)

    assert tb.edge == u + UNL - 1

    tb.expect(UNLOCK, 0, "F33 still unlocked")

    await tb.tick(1)

    assert tb.edge == u + UNL

    tb.expect(IDLE, 0, "F33 returned to IDLE, press discarded")

    assert tb.last.unlock == 0

    await tb.tick(3 * D)                      # button still held: nothing queued

    tb.expect(IDLE, 0, "F33 nothing queued")

    dut._log.info("F33 PASS")





# ============================================================================

# F35  Reset synchronizer

# ============================================================================

@cocotb.test(skip=(RS != 1), **TMO)

async def test_reset_synchronizer(dut):

    """F35: asynchronous assertion; synchronous two-edge deassertion."""

    tb = await Tb.create(dut)

    await tb.reach(DIGIT2)



    # Assertion: all resettable registers clear asynchronously, before clk.

    tb.set_rst(0)

    await tb.expect_async_reset("F35 asynchronous assertion")

    await tb.tick(1)

    tb.expect(IDLE, 0, "F35 reset remains asserted")



    # Deassertion remains synchronized: first normal update is at m+2.

    tb.set_btn(1 << DIGITS[0])

    await tb.tick(2)                         # keep raw reset low for two edges

    tb.set_rst(1)

    m = tb.edge + 1                          # first edge sampling rst_n high

    await tb.tick(D + 2)                     # through m+D+1

    assert tb.edge == m + D + 1

    tb.expect(IDLE, 0, "F35 before first normal update")

    await tb.tick(2)

    assert tb.edge == m + D + 3

    tb.expect(DIGIT2, 0, "F35 first normal update at m+2")

    tb.set_btn(0)



    # A one-cycle low pulse must still assert reset; release then takes two

    # synchronizer clock edges before normal operation resumes.

    await tb.reach(DIGIT2)

    tb.set_rst(0)

    await tb.expect_async_reset("F35 short asynchronous reset pulse")

    # Deassert before the next rising edge: the asynchronous assertion must

    # still be captured by rs1/rs2 and stretched into a synchronized reset.

    tb.set_rst(1)

    await tb.tick(2)

    tb.expect(IDLE, 0, "F35 synchronized release")

    dut._log.info("F35 PASS (asynchronous assertion, two-edge synchronous release)")





# ============================================================================

# F36  Short asynchronous reset pulse entirely between rising clock edges

# ============================================================================

@cocotb.test(skip=(RS != 1), **TMO)

async def test_short_async_reset_pulse(dut):

    """F36: a sub-cycle raw reset pulse is captured asynchronously by reset_sync."""

    tb = await Tb.create(dut)

    await tb.reach(DIGIT3)



    # Tb.tick() returns on a falling edge. Assert and release reset before

    # the next rising edge, proving assertion does not depend on clk.

    tb.set_rst(0)

    await tb.expect_async_reset("F36 pulse assertion")

    tb.set_rst(1)



    # rs1/rs2 were asynchronously cleared. Two rising edges shift the

    # deassertion through the synchronizer; the downstream logic resumes

    # normal updates only at the following edge (m+2 convention).

    await tb.tick(2)

    tb.expect(IDLE, 0, "F36 synchronized reset hold")

    await tb.tick(1)

    tb.expect(IDLE, 0, "F36 no spurious state after release")



    # Prove the DUT is operational again after synchronized release.

    await tb.hold_until(1 << DIGITS[0], DIGIT2)

    tb.expect(DIGIT2, 0, "F36 operation after reset pulse")

    dut._log.info("F36 PASS")





# ============================================================================

# F27  Randomised cycle-exact comparison (reference model runs everywhere,

#      this test adds the required >=100 x 5000-cycle random runs)

# ============================================================================

class RandomStim:

    def __init__(self, rng, model):

        self.rng, self.model = rng, model

        self.q = collections.deque()

        self.age = 0

        self.last_st = None



    def _m(self, mask, n, rst=1):

        self.q.extend([(mask, rst)] * max(0, int(n)))



    def _exp(self):

        st = self.model.st

        return DIGITS[st] if st < 4 else self.rng.randrange(4)



    def _wrong(self, d):

        return (d + self.rng.randrange(1, 4)) & 3



    def next(self):

        m = self.model

        if m.st != self.last_st:

            self.last_st, self.age = m.st, 0

        else:

            self.age += 1

        if not self.q:

            self._refill()

        return self.q.popleft()



    def _refill(self):

        r, rng, m = self.rng, self.rng, self.model

        pick = r.random()

        st = m.st if m.known else 0

        hold = D + rng.choice([0, 0, 1, 2, 5, 12])

        gap = rng.choice([D, D + 1, D + 3, 2 * D, 4, 1])

        if pick < 0.30:                                   # correct next digit

            b = self._exp()

            self._m(1 << b, hold); self._m(0, gap)

        elif pick < 0.42:                                 # wrong digit

            b = self._wrong(self._exp())

            self._m(1 << b, hold); self._m(0, gap)

        elif pick < 0.49:                                 # simultaneous presses

            mask = 0

            while bin(mask).count("1") < 2:

                mask = rng.randrange(16)

            self._m(mask, hold); self._m(0, gap)

        elif pick < 0.55:                                 # near-simultaneous

            a, b = rng.sample(range(4), 2)

            off = rng.randrange(1, 4)

            self._m(1 << a, off); self._m((1 << a) | (1 << b), hold); self._m(1 << b, off)

            self._m(0, gap)

        elif pick < 0.65 and 1 <= st <= 3 and N:          # land press around cycle N

            delta = rng.choice([-2, -1, 0, 0, 1, 1, 2])

            wait = N + delta - D - 2 - self.age

            if wait >= 0:

                self._m(0, wait)

            self._m(1 << self._exp(), hold); self._m(0, gap)

        elif pick < 0.72 and st in (UNLOCK, LOCKOUT, FAIL):  # land press near end of timed state

            total = UNL if st == UNLOCK else LOCK

            delta = rng.choice([-2, -1, 0, 0, 1, 2])

            wait = total + delta - D - 2 - self.age

            if wait >= 0:

                self._m(0, wait)

            self._m(1 << rng.randrange(4), hold + 20); self._m(0, gap)

        elif pick < 0.78:                                 # short / boundary pulse

            n = rng.choice([1, max(1, D - 1), D, D + 1, rng.randrange(1, D + 2)])

            self._m(1 << self._exp(), n); self._m(0, gap)

        elif pick < 0.85:                                 # bounce then stable

            b = 1 << self._exp()

            for _ in range(rng.randrange(1, 5)):

                self._m(b, rng.randrange(1, max(2, D))); self._m(0, rng.randrange(1, 4))

            self._m(b, hold + rng.randrange(0, 10))

            for _ in range(rng.randrange(0, 3)):          # bouncing release

                self._m(0, rng.randrange(1, max(2, D))); self._m(b, rng.randrange(1, 4))

            self._m(0, gap)

        elif pick < 0.89:                                 # long hold (+ glitch low)

            b = 1 << self._exp()

            self._m(b, rng.randrange(3 * D, 8 * D))

            if rng.random() < 0.5:

                self._m(0, rng.randrange(1, max(2, D))); self._m(b, rng.randrange(D, 3 * D))

            self._m(0, gap)

        elif pick < 0.96:                                 # idle

            self._m(0, rng.choice([rng.randrange(1, 40), N + 5 if N else 30]))

        else:                                             # asynchronous-style reset pulse

            self._m(rng.randrange(16) if rng.random() < 0.5 else 0, rng.randrange(1, 6), rst=0)

            self._m(0, 2)





@cocotb.test(**TMO)

async def test_cycle_exact_reference_model(dut):

    """F27: >= N_RANDOM_TESTS runs of N_RANDOM_CYCLES cycles vs the reference model."""

    tb = await Tb.create(dut)

    visited = collections.Counter()

    for it in range(N_RANDOM_TESTS):

        seed = SEED * 1000 + it

        rng = random.Random(seed)

        await tb.reset()

        stim = RandomStim(rng, tb.model)

        try:

            for _ in range(N_RANDOM_CYCLES):

                mask, rst = stim.next()

                if mask != tb.btn:

                    tb.set_btn(mask)

                if rst != tb.rst:

                    tb.set_rst(rst)

                await tb.tick(1)

                visited[tb.last.state] += 1

        except AssertionError as e:

            raise AssertionError("F27 random run %d (seed %d) failed:\n%s" % (it, seed, e))

        if it % 10 == 0:

            dut._log.info("F27: random run %d/%d ok", it + 1, N_RANDOM_TESTS)

    names = {STATE_NAMES[k]: v for k, v in sorted(visited.items())}

    dut._log.info("F27 state coverage over random runs: %s", names)

    for s in (DIGIT2, DIGIT3, DIGIT4, UNLOCK, FAIL, LOCKOUT):

        assert visited[s] > 0, "F27: random stimulus never reached %s (weak stimulus)" % STATE_NAMES[s]

    dut._log.info("F27 PASS (%d runs x %d cycles, %d cycles compared in total)",

                  N_RANDOM_TESTS, N_RANDOM_CYCLES, tb.compared)
