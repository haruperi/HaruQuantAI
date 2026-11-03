# Custom Blocks

> Build your own reusable block combinations visually in AlgoWizard — no coding required.

## What it is

A **custom block** is a user-defined combination of existing building blocks, stored and reused as a
single block. Instead of hoping the generator randomly assembles a meaningful condition from
primitive blocks (e.g. `CCI` + `IsLower (<)`), you package the meaningful combination once and use it
everywhere.

Example: the built-in signal *CCI is rising* is valid when `CCI(Period)[2] < CCI(Period)[1]`. You can
capture a stronger idea — *CCI rising for 3 bars* (`CCI(Period)[3] < CCI(Period)[2] < CCI(Period)[1]`)
— as one custom block that exposes just a single `Period` parameter, even though it uses three CCI
values internally.

Custom blocks reduce randomness by letting the generator work with signals that make real trading
sense. Historically such blocks required writing a Java snippet; since **Build 127** they can be
created visually in AlgoWizard with no coding. Because a custom block is composed from existing block
components, StrategyQuant already knows how to generate source code for it for your target platform.

Internally custom blocks carry the key prefix `CBlock_*`, are persisted to
`user/settings/customBlocks.xml`, and are loaded/saved through the AlgoWizard servlet endpoints
`/algowizard/loadCustomBlocks` and `/algowizard/saveCustomBlocks`.

## How to create / configure it

1. Open the embedded **AlgoWizard**, click **Customize** in the top menu, then switch to the
   **Custom blocks** tab. This is the custom-blocks management and edit panel. A grid filter lets you
   view **All**, **Standard**, or **AWCloud** blocks.
2. Click **Add block** and fill in the definition dialog:
   - **Block key** — the unique ID. Letters and numbers only; no spaces or special characters
     (e.g. `CCIRising3Bars`).
   - **Block name** — the label shown in the Building blocks selection (e.g. *CCI rising for 3 bars*).
   - **Block type** — see below.
3. The new block starts empty. Click **Add another condition** to open the standard block-chooser
   dialog (the same one used in the AlgoWizard editor) and assemble the internal logic — pick the
   indicator, set its shift, choose a comparison block, and set the compared value.
4. Add the parameters you want to expose (see *Parameters*), then bind them into the internal
   conditions.
5. Optionally define an **opposite block** for short-side symmetry (see *Opposite block*).
6. **Save**. The block is immediately usable both in the AlgoWizard editor and in a builder's
   Building blocks configuration.

## Block types, parameters, and the opposite block

**Block types** — two are supported:

- **Condition** — returns a true/false value for use in entry/exit conditions (usually a comparison).
  Appears in the **Signals** section of Building blocks.
- **Price level** — computes a price level for stop/limit orders. Appears in the **Stop / Limit Price
  Levels** section under the Stop / Limit Entry blocks category.

**Parameters** — the externally visible inputs of the block. Every custom block has a mandatory
**Chart** parameter. Add more with **Add parameter**; each has a name and a type
(`CustomBlockParamTypes`):

- **chart / data** — selects which chart (data) the indicators are computed from.
- **period** — for indicator periods; a distinct type so the generator limits it by the configured
  period range.
- **shift** — a bars-history index (0 = current bar, 1 = previous bar, …); a distinct type so the
  generator limits it by the configured shift range.
- **int, double, bool** — standard variable types.

A parameter left unused means its internal value stays fixed (e.g. a hard-coded period of 14 is never
randomized). To make it configurable, double-click a condition, click the blue **[…]** button next to
the value, and bind it to your parameter. Custom-block period/shift ranges take precedence over
Building blocks settings; set their Min/Max/Step all to zero to fall back to the global **What to
build** ranges — see [../settings/parameter-ranges.md](../settings/parameter-ranges.md).

**Opposite block** — strategies usually need symmetric long/short rules. If a custom block has no
opposite defined, it is simply reused as its own opposite (long and short would be identical). To get
a proper mirror (e.g. *CCI falling for 3 bars* as the opposite of *CCI rising for 3 bars*), click the
**Not set** link and create/choose the opposite block. On creation StrategyQuant **auto-negates** the
source block for you. This negation happens **only once** — later edits to the source are not
propagated automatically. To resync, open the *opposite* block and click **Negate from opposite
block**. See also [../settings/oppositeblocks.md](../settings/oppositeblocks.md).

## Related

- [AlgoWizard reference index](README.md)
- [Templates and placeholders](templates-and-placeholders.md)
- [Custom blocks — settings-tab view](../settings/custom-blocks.md)
- [Building blocks (settings)](../settings/building-blocks.md)
- [Opposite blocks (settings)](../settings/oppositeblocks.md)
- [Parameter ranges (settings)](../settings/parameter-ranges.md)
- [Concepts](../concepts.md)
- [Blocks catalog (onboarding)](../../onboard/04-builder/05-blocks-catalog.md)
