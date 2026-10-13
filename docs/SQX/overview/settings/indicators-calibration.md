# Indicators calibration — Building blocks deep dive
> Automatically sets each indicator's min/max/step to the effective value range seen on your data, so the generator never uses values that can't occur.

**Field-level controls (for UI tests):** [fields/indicators-calibration.md](fields/indicators-calibration.md)

**Applies to:** Build — configured in the Building blocks settings tab.

## What it configures

Calibration automatically sets up your building blocks to use values that are in an **effective
range** for your data. After calibration, each indicator's min/max/step reflect the useful range
given your Data settings, which can make the build more effective because values that would never
appear on the chart are not used.

## Main options

- **Calibrate now** — run calibration on demand.
- **Calibrate before start** — a switch in the Building blocks tab; when enabled, calibration runs
  automatically each time the project starts.
- **Steps settings** — configured in the *Calibrate indicators* popup; determines how the step value
  is computed.
- **Results table** — after calibration the computed values are shown per indicator; you can manually
  adjust them, then **Save** to write them into the building blocks.
- **Rounding** — by default results are rounded ("beautified") for readability. You can set
  `rounding=disabled` for more precise (less rounded) values.
- **Extended (multi-instance) calibration** — configured via `calibrationSettings.txt` in the
  **user/settings/** folder:
  - Runs multiple instances of the same indicator, each with different parameter settings, so the
    output values better reflect what is actually encountered during a build.
  - File format: comment lines start with `#`, empty lines are skipped, naming follows the Java
    snippet convention. You can set some or all parameters of an indicator; unspecified settings use
    defaults.
  - You can **disable computation of specific output buffers** to speed up calibration (e.g. disable
    ADX's middle line, which sits between +DI and -DI and doesn't affect results).

## How it affects generation

Calibration replaces guessed indicator ranges with ranges derived from your actual history data:
each indicator is run over the full history, its per-bar values are collected, and the effective
**min = mean − standard deviation** and **max = mean + standard deviation** are computed (the step
depends on your steps setting). Extended calibration uses several parameter instances so the ranges
cover the values the generator will really run into. Narrower, data-grounded ranges mean the
generator compares indicators against realistic numbers instead of impossible ones, which tends to
produce more meaningful strategies.

## Related

- Settings index: [README.md](README.md)
- Parent panel: [building-blocks.md](building-blocks.md)
- How ranges are used / precedence: [parameter-ranges.md](parameter-ranges.md)
- History data used for calibration: [data.md](data.md)
- Concepts (indicator, building block): [../concepts.md](../concepts.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
