# Yosys + OpenSTA standalone flow

Synthesis with Yosys and static timing analysis with OpenSTA, using the

## Contents

| File | Purpose |
|---|---|
| `env.sh` | Design settings (top, clock, period) and PDK paths |
| `src/top.v` | Example design (replace with yours) |
| `constraints/top.sdc` | Clock and I/O constraints, gf180mcuD design rules |
| `scripts/synth.sh` | Yosys synthesis -> `out/$TOP.nl.v` |
| `scripts/sta.tcl` | OpenSTA, one corner |
| `scripts/sta_all.sh` | Runs `sta.tcl` at tt, ss, ff |
| `out/` | Netlist |
| `logs/` | Logs and reports |

## 1. Install the PDK (once)

```bash
pip install ciel
ciel enable --pdk-root $HOME/.ciel --pdk gf180mcuD 54435919abffb937387ec956209f9cf5fd2dfbee
```

## 2. Get the tools (once)

Either install `yosys` and `sta` (OpenSTA) yourself, or use the LibreLane container,
which has both:

```bash
pip install librelane==3.0.14
python3 -m librelane --pdk-root $HOME/.ciel --pdk gf180mcuD --dockerized
```

Check:

```bash
which yosys sta
```

## 3. Set up

```bash
cd yosys_sta_gf180
source env.sh
```

For your own design:

1. Put it in `src/<top>.v`.
2. Edit `TOP`, `CLOCK_PORT` and `CLOCK_PERIOD` in `env.sh`.
3. Rename `constraints/top.sdc` to `constraints/<top>.sdc`.
4. Run `source env.sh` again.

## 4. Synthesise

```bash
./scripts/synth.sh
```

Output:

- `out/$TOP.nl.v`: gate-level netlist
- `logs/synth.log`: full Yosys log
- `logs/synth_stat.rpt`: cell count and area

Check:

```bash
grep -E "Number of cells|Chip area" logs/synth_stat.rpt
grep -c assign out/$TOP.nl.v          # must print 0
```

`check -assert` stops the run if any net is undriven or multi-driven.

## 5. Run timing at all three corners

```bash
./scripts/sta_all.sh
```

Or run one corner:

```bash
CORNER=tt LIB=$LIB_TT sta -no_splash -exit scripts/sta.tcl
```

Reports per corner (tt, ss, ff):

| File | What it shows |
|---|---|
| `logs/sta_<corner>_setup.rpt` | Worst setup path |
| `logs/sta_<corner>_hold.rpt` | Worst hold path |
| `logs/sta_<corner>_unconstrained.rpt` | Paths with no constraint (should be empty) |
| `logs/sta_<corner>_drv.rpt` | Max slew / cap / fanout violations |
| `logs/sta_<corner>.log` | wns, tns, worst setup and hold slack |

Check:

```bash
grep "worst slack" logs/sta_*.log     # pass: all >= 0
cat logs/sta_*_drv.rpt                # pass: no VIOLATED lines
```

## Corners

| Corner | Liberty file | Conditions |
|---|---|---|
| tt | `..._tt_025C_3v30.lib` | typical, 25 °C, 3.3 V |
| ss | `..._ss_125C_3v00.lib` | slow, 125 °C, 3.0 V |
| ff | `..._ff_n40C_3v60.lib` | fast, -40 °C, 3.6 V |

## Notes

- This is pre-layout STA: ideal clock, no wire parasitics. Treat setup slack as optimistic.
- If setup fails, increase `CLOCK_PERIOD` in `env.sh` (the SDC reads it), or change the RTL.
  Then re-run steps 4 and 5.
- A max-slew violation on an output port is normal at this stage. It comes from the
  72.91 fF output load in the SDC, and buffering during place and route fixes it.
