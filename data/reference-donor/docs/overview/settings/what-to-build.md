# What to build — Builder settings panel
> Defines *what kind* of strategy the Builder generates: its type, rule structure, trading direction, build mode, rule complexity, and Stop Loss / Profit Target.

**Field-level controls (for UI tests):** [fields/what-to-build.md](fields/what-to-build.md)

## What it configures

This is the first Builder settings panel and it sets the high-level shape of every
strategy that will be generated. You decide whether you are building a single-chart
strategy or a multi-chart one, what rule architecture (style) is used, whether the
Builder searches randomly or with genetic evolution, how complex the entry/exit rules
may become, and whether a Stop Loss and Profit Target are required. These choices frame
everything the other panels (Building blocks, Data, Ranking) then fill in.

## Main options

- **Strategy type**
  - **Simple strategy** — trades on one symbol and one timeframe.
  - **Multi-TF or multi-symbol strategy** — uses one or more additional charts alongside
    the main one (e.g. trade EURUSD/H1 while also reading EURUSD/H4 and GBPUSD/H1). Here
    you set only *how many* additional charts; the actual symbols/timeframes are chosen in
    the **Data** panel.
  - **Strategy from template** — generate using your own custom strategy template, so the
    architecture can differ from the standard SQ X strategies.
  - **Improve existing strategy** — pick an existing strategy and, via **Parts to improve**,
    regenerate only a chosen part (e.g. Long entry rule, Short exit rule, or order type
    Market / Stop / Limit).
- **Trading direction** — generate Long only, Short only, or both. You can also mark the
  entry and/or exit rules as **symmetrical** (Short rules are the reversed Long rules) or
  **non-symmetrical** (Long and Short rules generated independently). Entry and exit
  symmetry can be set separately.
- **Strategy style** (pop-up dialog) — choose the rule architecture: SQ3 (old) style,
  SQ X new-style signal rules, or SQ X with Fuzzy Logic. See [../concepts.md](../concepts.md).
- **Build mode** — **Random generation** or **Genetic evolution**. Selecting genetic mode
  reveals the extra **Genetic options** tab in the Builder.
- **Number of conditions** — min/max number of conditions generated per signal (rule).
  Fuzzy Logic strategies need a higher minimum (3+) to be effective.
- **Shift (lookback period)** — min/max number of bars back a condition may look
  (0 = current bar, 1 = previous bar). A small range (e.g. 0–5) is recommended; minimum
  shift of 1 avoids reading not-yet-final indicator values on the current bar.
- **Indicators period** — min/max period range used for generated indicators (must be > 1;
  keeping it modest, well under 100, is recommended).
- **Stop Loss & Profit Target options** — whether SL and PT are **mandatory**, their
  min/max values in pips, and a desired Risk/Reward ratio. If SL/PT are not mandatory, use
  another exit type (e.g. exit after X bars) so trades can still close.

For multi-TF / multi-symbol strategies the conditions, shift, and period ranges can be
configured separately for each chart.

## How it affects generation

These settings define the search space and skeleton of every candidate. The strategy type
and style fix the rule architecture; direction and symmetry decide how many independent
rule sets are produced; the condition/shift/period ranges bound how complex and how
far-looking each generated rule can be; and the SL/PT settings decide how trades are
protected and closed. The build mode determines whether the Builder streams fresh random
strategies or evolves a population toward the fitness defined in the **Ranking** panel. All
ranges are limits — the exact values are drawn randomly each time a strategy or condition
is generated.

## Related

- Parent: [../builder.md](../builder.md)
- Concepts (strategy style, build mode, shift, direction): [../concepts.md](../concepts.md)
- Sibling panels: [building-blocks.md](building-blocks.md) · [data.md](data.md) · [ranking.md](ranking.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md) · [../../onboard/04-builder/04-strategy-creation.md](../../onboard/04-builder/04-strategy-creation.md)
