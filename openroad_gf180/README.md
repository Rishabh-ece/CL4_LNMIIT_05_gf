# OpenROAD standalone place-and-route

Netlist to routed layout with OpenROAD, step by step, with one Tcl script per step.
Sign-off parasitic extraction (OpenRCX), STA (OpenSTA) and IR drop are included.
No TinyTapeout or LibreLane scripts.

Input: a gate-level netlist `out/$TOP.nl.v`. `scripts/01_synth.sh` (Yosys) makes it
from `src/$TOP.v`.

## Contents

| File | Purpose |
|---|---|
| `env.sh` | Design settings and PDK paths |
| `src/top.v` | Example design |
| `constraints/top.sdc` | Clock, I/O and design-rule constraints |
| `scripts/01_synth.sh` | Yosys synthesis -> `out/$TOP.nl.v` |
| `scripts/setup_pnr.tcl` | Shared by P&R steps: SDC, wire RC, routing layers Metal2–Metal5, dont_use cells |
| `scripts/pg_connect.tcl` | Connects VDD/VNW -> VDD and VSS/VPW -> VSS on every cell |
| `scripts/02_floorplan.tcl` … `13_fill.tcl` | One OpenROAD step each (table below) |
| `scripts/14_rcx.tcl` | Parasitic extraction, one RC corner -> SPEF |
| `scripts/15_sta_signoff.tcl` | Sign-off STA, one corner -> reports + SDF |
| `scripts/16_irdrop.tcl` | Power and IR drop |
| `scripts/run_pnr.sh` | Runs steps 02–13 in order (or from a given step) |
| `scripts/run_signoff.sh` | Runs 14 (×3), 15 (×9), 16 |

Each step reads the previous step's `out/NN_*.odb` and writes its own. Logs go to
`logs/NN_*.log`.

## 1. Install the PDK and tools (once)

```bash
pip install ciel
ciel enable --pdk-root $HOME/.ciel --pdk gf180mcuD 54435919abffb937387ec956209f9cf5fd2dfbee
# if other PDK update accordingly

pip install librelane==3.0.14
python3 -m librelane --pdk-root $HOME/.ciel --pdk gf180mcuD --dockerized
```

The last command opens a shell with `yosys`, `openroad` and `sta`.

Check:

```bash
which yosys openroad sta
```

## 2. Set up

```bash
cd openroad_gf180
source env.sh
```

For your own design:

1. Copy it to `src/<top>.v`.
2. Rename the SDC to `constraints/<top>.sdc`.
3. Edit these settings in `env.sh`, then run `source env.sh` again:
   - `TOP`
   - `CLOCK_PORT`
   - `CLOCK_PERIOD`
   - `DIE_AREA`
   - `CORE_AREA`

`CORE_AREA` must lie on the placement grid:

- x: multiples of 0.56 µm
- height: a multiple of 3.92 µm

## 3. Synthesise

```bash
./scripts/01_synth.sh
```

## 4. Place and route: all steps

```bash
./scripts/run_pnr.sh
```

Resume from a step after changing it:

```bash
./scripts/run_pnr.sh 08_cts
```

## 4b. Place and route: one step at a time

```bash
openroad -exit scripts/02_floorplan.tcl     2>&1 | tee logs/02_floorplan.log
openroad -exit scripts/03_tap.tcl           2>&1 | tee logs/03_tap.log
openroad -exit scripts/04_pdn.tcl           2>&1 | tee logs/04_pdn.log
openroad -exit scripts/05_gpl.tcl           2>&1 | tee logs/05_gpl.log
openroad -exit scripts/06_repair_design.tcl 2>&1 | tee logs/06_repair_design.log
openroad -exit scripts/07_dpl.tcl           2>&1 | tee logs/07_dpl.log
openroad -exit scripts/08_cts.tcl           2>&1 | tee logs/08_cts.log
openroad -exit scripts/09_rsz_timing.tcl    2>&1 | tee logs/09_rsz_timing.log
openroad -exit scripts/10_grt.tcl           2>&1 | tee logs/10_grt.log
openroad -exit scripts/11_antenna.tcl       2>&1 | tee logs/11_antenna.log
openroad -exit scripts/12_drt.tcl           2>&1 | tee logs/12_drt.log
openroad -exit scripts/13_fill.tcl          2>&1 | tee logs/13_fill.log
```

| Step | Does | Output | Expected (example design) |
|---|---|---|---|
| 02_floorplan | Die/core, rows, tie cells, routing tracks | 02_floorplan.odb/.def | `Added 36 rows of 345 site`, 36 % utilization |
| 03_tap | Well taps every 20 µm, endcaps | 03_tap.odb | 72 endcaps, 173 tapcells |
| 04_pdn | Metal1 rails, Metal4/Metal5 straps, VDD/VSS pins | 04_pdn.odb | `Inserting grid: stdcell_grid` |
| 05_gpl | Global placement, I/O pins (Metal3 H / Metal2 V), placement again | 05_gpl.odb | Overflow ≈ 0.10, slack printed |
| 06_repair_design | Input buffers, slew/cap/fanout repair | 06_rsz.odb | 17 input buffers, 8 buffers in 6 nets, violator list empty |
| 07_dpl | Legal placement | 07_dpl.odb | `check_placement` silent |
| 08_cts | Clock tree (clkbuf_16 root, clkbuf_2/4/8) | 08_cts.odb | skew 0.04 ns |
| 09_rsz_timing | Setup then hold repair | 09_rsz.odb | `No hold violations found`, tns 0 |
| 10_grt | Global routing, guides | 10_grt.odb, 10_grt.guide | overflow `0 / 0 / 0` |
| 11_antenna | Antenna check and diode repair | 11_ant.odb | 0 net, 0 pin violations |
| 12_drt | Detailed routing | 12_drt.odb | `Number of violations = 0` |
| 13_fill | Fill/decap cells, final views | 13_fill.odb, top.def, top.pnl.v, top.pwr.v | 786 filler instances |

## 5. Sign-off: extraction, STA at 9 corners, IR drop

```bash
./scripts/run_signoff.sh
```

Or run each part yourself:

```bash
for RC in nom min max; do
  RC=$RC openroad -exit scripts/14_rcx.tcl 2>&1 | tee logs/14_rcx_$RC.log
done

for RC in nom min max; do
  for C in "tt $LIB_TT" "ss $LIB_SS" "ff $LIB_FF"; do
    set -- $C
    CORNER=${RC}_$1 RC=$RC LIB=$2 sta -no_splash -exit scripts/15_sta_signoff.tcl 2>&1 | tee logs/15_sta_${RC}_$1.log
  done
done

openroad -exit scripts/16_irdrop.tcl 2>&1 | tee logs/16_irdrop.log
```

Outputs:

- SPEF files: `out/$TOP.{nom,min,max}.spef`
- Per-corner reports: `logs/sta_<corner>_{setup,hold,unconstrained,drv,skew}.rpt`
- Per-corner SDF: `out/$TOP.<corner>.sdf`

Pass criteria:

- every `worst slack` is ≥ 0
- every `logs/sta_*_drv.rpt` is empty
- the IR drop log shows `All PDN stripes ... are connected`
- worst IR drop is a few % of 3.3 V at most

## 6. View

```bash
openroad -gui
```

Then type in its Tcl console:

```tcl
read_db out/13_fill.odb
```

Use any step's `.odb` to see that stage.

## Notes

- **Failing corner:** the example design fails setup at the ss corner at 20 ns
  (about −13 to −14 ns). That is the design, not the flow. To fix it, raise
  `CLOCK_PERIOD` and re-run from synthesis.
- **Power grid:** the PDN pitch (153.6 / 153.18 µm) is the gf180mcuD default. On small
  dies you only get one or two straps. Lower `-pitch` in `04_pdn.tcl` if IR drop is
  high.
- **Detailed routing and min-area errors:** use a recent OpenROAD, such as the one in
  the LibreLane 3.0.14 container. The Feb 2024 OpenROAD routes with 0 DRT violations
  but adds no min-area patches at stacked vias. Magic DRC then reports M2.3/M3.3
  errors on the GDS; a newer OpenROAD fixes this.
- **Router flags:** `detailed_route` takes its layers from `set_routing_layers` (in
  `setup_pnr.tcl`). Newer OpenROAD rejects `-bottom_routing_layer`/`-top_routing_layer`.
- **More STA paths:** add `-group_path_count N` to `report_checks` (newer OpenSTA) to
  see more than one path per group.

