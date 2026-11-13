# CL-4 Initial RTL Verification and Synthesis Report

## 1. Project Information

- Project: CL-4 Four-Button Combination Lock
- Top Module: `tt_um_CL4_LNMIIT`
- Target PDK: GF180 (technology mapping pending)
- Verification Stage: Initial RTL linting and generic synthesis

## 2. Verilator Lint

Command:

```bash
verilator --lint-only -Wall --top-module tt_um_CL4_LNMIIT src/*.v
```

Result: **PASS**

Exit code: `0`

No lint warnings or errors were reported.

## 3. Yosys Initial Checks

Command:

```bash
yosys -p "read_verilog src/*.v; hierarchy -check -top tt_um_CL4_LNMIIT; proc; opt; check; stat"
```

Result: **PASS**

- Hierarchy check completed.
- Structural check reported zero problems.
- Initial synthesis statistics reported 131 cells.

## 4. Flattened Generic Synthesis

Command:

```bash
yosys -p "read_verilog src/*.v; hierarchy -check -top tt_um_CL4_LNMIIT; synth -top tt_um_CL4_LNMIIT -flatten; check; stat"
```

Result: **PASS**

- Flattened synthesis completed successfully.
- Structural check reported zero problems.
- Total generic cells: 356.
- Sequential cells: 55.
  - DFFE cells: 24.
  - DFF cells: 31.

## 5. Pending Work

- GF180 standard-cell technology mapping.
- Gate-level simulation (GLS).
- Timing analysis.
- Final specification compliance verification.

**Note:** These are preliminary generic synthesis results. They are not GF180-mapped area or timing results.
