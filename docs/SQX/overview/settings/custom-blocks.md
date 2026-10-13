# Custom blocks — Building blocks deep dive
> Lets you combine existing blocks into your own reusable building block, so the generator uses signals that make real sense.

**Field-level controls (for UI tests):** [fields/custom-blocks.md](fields/custom-blocks.md)

**Applies to:** Build (as a Building-blocks option) — custom blocks are created in the embedded AlgoWizard editor.

## What it configures

Custom blocks let you create your own combination of blocks and store it as a single reusable block.
The value is in **decreasing randomness**: instead of hoping the generator randomly assembles a
meaningful condition from primitive blocks (like `CCI` and `IsLower (<)`), you define the meaningful
condition once (e.g. "CCI is rising for 3 bars") and expose it as one block with clean parameters.
Since Build 127 these can be created visually in AlgoWizard without any coding (previously this
required writing a Java snippet).

## Main options

Custom blocks are managed in **AlgoWizard → Customize → Custom blocks**. When you add a block you
define:

- **Block key** — a unique ID (letters and numbers only, no spaces or special characters).
- **Block name** — the name shown in the Building blocks selection.
- **Block type** — one of:
  - **Condition** — returns true/false; usable in entry/exit conditions (appears in the Signals
    section).
  - **Price level** — computes a price level for stop/limit orders (appears under Stop / Limit entry
    blocks).
- **Conditions / content** — build the block's logic using the standard block-picker dialog
  (indicators, comparisons, shifts), e.g. `CCI(Period)[3] < CCI(Period)[2] < CCI(Period)[1]`.
- **Parameters** — the externally visible parameters. Every block has a mandatory **Chart** parameter;
  you can add more, each with a type:
  - **chart** — which chart the indicator is computed from.
  - **period** — an indicator period; limited by the generator's period range boundaries.
  - **shift** — an index into bar history (0 = current bar, 1 = previous, …); limited by the shift
    range boundaries.
  - **int, double, bool** — standard variable types.
  - Bind a parameter into the block's conditions via the **[…]** button so the value is generated
    (e.g. a random period) rather than fixed.
- **Opposite block** — the block used for the opposite (Short) direction. If none is defined, the
  block is simply reused for both directions. You can create one from the **Not set** link;
  StrategyQuant negates the source block automatically on creation. This negation happens **only once**
  — after editing the source block, open its opposite and click **Negate from opposite block** to
  re-apply the negation.

## How it affects generation

Once saved, a custom block appears in the AlgoWizard editor and in the Builder's Building blocks
configuration, and the generator can use it like any built-in block. Because it is built from existing
block components, StrategyQuant already knows how to generate valid source code for the target trading
platform. Using custom blocks steers the generator toward conditions you consider meaningful, reducing
the noise of purely random combinations while keeping periods/shifts randomizable.

## Related

- Settings index: [README.md](README.md)
- Parent panel: [building-blocks.md](building-blocks.md)
- Setting parameter ranges for custom blocks: [parameter-ranges.md](parameter-ranges.md)
- Controlling negation globally: [oppositeblocks.md](oppositeblocks.md)
- The AlgoWizard editor: [../algowizard.md](../algowizard.md)
- Concepts (building block, signal, indicator): [../concepts.md](../concepts.md)
- Developer detail: [../../onboard/04-builder/05-blocks-catalog.md](../../onboard/04-builder/05-blocks-catalog.md)
