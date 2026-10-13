# Parameter ranges (standard & custom blocks) — Building blocks deep dive
> Controls the value ranges the generator uses when it creates a block's parameters, such as an indicator's Period and Shift.

**Field-level controls (for UI tests):** [fields/parameter-ranges.md](fields/parameter-ranges.md)

**Applies to:** Build — configured per block in the Building blocks settings.

## What it configures

When the generator creates a block (for example a CCI indicator) it also generates the values of its
parameters. For CCI the most important are **Period** and **Shift**. This page controls the min/max/
step ranges used for those generated values, both for standard (built-in) blocks and for
user-created [custom blocks](custom-blocks.md).

## Main options

- **Standard (built-in) blocks** — configured in **Builder → Building blocks**, per block:
  - By default a block's Period and Shift use the **globally set ranges** — the period and shift
    ranges configured in **Builder → What to build**.
  - You can switch a block to a **custom range** and define its own Min/Max/Step for that block only.
- **Custom blocks** — each custom block exposes its own externally visible parameters (Chart, Period,
  Shift, …). You can set **Min, Max and Step** for its Period and Shift parameters:
  - These values **take precedence** over the per-block Building-blocks settings above. For example,
    if a custom block defines Period range 33–66 step 3, the generator uses that.
  - To make a custom block fall back to the **global** What-to-build ranges instead, set all three of
    its Min, Max and Step to **zero** — this tells StrategyQuant to generate those values from the
    What to build configuration.

## How it affects generation

Parameter ranges bound every numeric value the generator can assign to a block, so they directly
shape the space of strategies that can be produced. Tightening or widening a range changes how
adventurous the generator is with indicator periods and bar shifts. The precedence order matters:
custom-block ranges win over per-block ranges, which in turn override the global ranges from What to
build — so check the most specific level when a value is not being generated as you expect.

## Related

- Settings index: [README.md](README.md)
- Parent panel: [building-blocks.md](building-blocks.md)
- Global period/shift ranges: [what-to-build.md](what-to-build.md)
- Creating custom blocks: [custom-blocks.md](custom-blocks.md)
- Auto-computing effective ranges: [indicators-calibration.md](indicators-calibration.md)
- Concepts (building block, indicator, period/shift): [../concepts.md](../concepts.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
