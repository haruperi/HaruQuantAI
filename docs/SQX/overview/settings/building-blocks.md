# Building blocks — Builder settings panel
> Selects the raw components — signals, indicators, operators, order types and exits — that the Builder is allowed to combine into strategy rules.

**Field-level controls (for UI tests):** [fields/building-blocks.md](fields/building-blocks.md)

## What it configures

Building blocks are the core components combined to create the rules and actions of every
generated strategy. On this panel you check which blocks the generator may use, optionally
weight them so favorites are chosen more often, and (for advanced use) edit each block's
parameter generation. Narrowing the selection to a focused group of indicators or to price
data only is a common way to steer what kind of strategies are produced.

## Main options

The panel is divided into four areas:

- **Signals / Indicators / Stop-Limit entry blocks** (the large left panel):
  - **Signals** — predefined complete conditions that combine an indicator with a
    comparison or property, e.g. "ADX is rising" or "CCI crossed above 0".
  - **Indicators** — indicators, price ranges and price values that are randomly combined
    with operators to form conditions.
  - **Stop / Limit entry blocks** — blocks used to compute the price of Stop or Limit
    pending orders.
- **Order types** — which order types may be generated: Market, Stop, Limit, Enter/Reverse.
- **Exit types** — the exit methods a strategy may use.
- **Custom data indicators** — external indicators imported into SQ X as data; valid only
  for the timeframe they were imported for.

Per-block controls:

- **Enable / disable** — check the blocks you want the generator to consider.
- **Weight** — for competing blocks (indicators/signals), a higher weight means a higher
  chance of being chosen.
- **Percentage** — for exits, the probability that a given exit method is used.

Advanced (per block, via the **Default** link next to a block):

- **Parameter values** — for each parameter (Chart, Computed From, Period, Shift, …) choose
  a fixed value or a random range / list of values.
- **Parameter sets** — define multiple sets mixing fixed and random parameters; sets compete
  (by weight) with the normal parameter definition to decide which is used.
- **Indicator values** — declare the expected value range of an indicator so it can be
  compared sensibly against random numbers.
- **Indicators calibration / Autocalibration** — set min/max/step for indicator values in one
  place; autocalibration computes these from the current market set in the **Data** panel.

## How it affects generation

The checked blocks define the vocabulary the Builder draws from when filling a strategy
template's random condition placeholders. Fewer, well-chosen blocks produce more focused
(and often better) strategies; weights and percentages bias which blocks and exits appear;
and the parameter/calibration settings bound the numeric ranges of each generated block so
values stay meaningful for the market being tested. Together with the condition/period/shift
ranges from **What to build**, this panel determines every rule the generator can express.

## Related

- Parent: [../builder.md](../builder.md)
- Concepts (building block, indicator, signal, template placeholders): [../concepts.md](../concepts.md)
- Sibling panels: [what-to-build.md](what-to-build.md) · [data.md](data.md) · [ranking.md](ranking.md)
- Developer detail: [../../onboard/04-builder/05-blocks-catalog.md](../../onboard/04-builder/05-blocks-catalog.md) · [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
