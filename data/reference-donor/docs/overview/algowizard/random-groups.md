# Random Groups

> Per-placeholder pools of candidate blocks that a random placeholder draws from instead of the global Building-blocks selection.

## What it is

Your choice of **Building blocks** in StrategyQuant is global — it applies to every entry and exit
condition the generator produces. A **random group** is a named set of candidate blocks that a
*specific* random placeholder (`RandomCondition`, `RandomValue`, or `RandomAction`) draws from
**instead of** that global selection.

This lets you constrain individual placeholders precisely. By default a placeholder has no group, so
it is generated from the global Building blocks. When you bind it to a group, only the blocks in that
group are eligible for that placeholder.

Random groups build on **strategy templates** — the XML rule trees, containing random placeholders,
that AlgoWizard edits and the Builder later fills. See
[Templates and placeholders](templates-and-placeholders.md) for that background.

Internally groups are persisted to `user/settings/blockGroups.xml` and are loaded/saved through the
AlgoWizard servlet endpoints `/algowizard/loadBlockGroups` and `/algowizard/saveBlockGroups`.

## How to create / configure it

1. Open **AlgoWizard**, click the **Customize** icon in the top toolbar to reach the **Random block
   groups** editor. By default there are no groups — creating them is up to you.
2. Click **Add group**, then fill in the group **name** and **type** (see below). A grid filter
   (`RandomGroupGridFilters`) lets you view groups by type.
3. A new group starts empty. Add candidate blocks with **Add block**, or **Copy & Paste** existing
   blocks from the AlgoWizard editor. Choosing blocks works exactly as in the editor — pick signals,
   or combine indicators, price values, and comparisons.
4. Click **Save**.

To use a group, go back to your strategy template and open (or add) the matching placeholder. In its
configuration, select your group in the **Random group** field. For example, a `RandomCondition`
named *RandomFromGroup1* bound to *Group 1* will be generated only from that group's blocks, while a
`RandomCondition` with no group is generated from the global Building blocks (and can use AND/OR
operators and multiple conditions, per **What to build → # of Conditions**).

## Group types, binding, and precedence

**Group types** — three, matching the placeholder families:

- **Conditions** — used by a `RandomCondition` placeholder, for trading-signal conditions.
- **Values** — used by a `RandomValue` placeholder, for price or numeric values (e.g. a stop/limit
  entry price).
- **Actions** — used by a `RandomAction` placeholder, for entry orders and other actions.

**Binding to a placeholder** — a placeholder binds to a group through its `#Group#` parameter, whose
`controlType` is `randomGroupId` and whose `randomGroupType` (`Conditions` | `Values` | `Actions`)
must match the group type. If no group is set, the placeholder falls back to the global Building-blocks
selection.

**Precedence and parameters** — when a placeholder uses a random group, the group's contents **take
precedence** over the global Building blocks; the group's blocks do **not** need to be selected in
**Builder settings → Building blocks**. Blocks are generated exactly as specified in the group:

- **Fixed** parameter values in a group's block are used as-is (e.g. `CCI(18) > 0` always uses 18).
- Only parameters explicitly **set to random** are randomized (e.g. an *RSI is rising* block with a
  random period can yield `RSI(20) is rising`, `RSI(50) is rising`, etc.).

So always set the parameters in a group's blocks to random when you want them generated randomly. For
short-side symmetry, add a matching `NegatedCondition` placeholder alongside the group-bound one so
the short entry mirrors the long entry.

## Related

- [AlgoWizard reference index](README.md)
- [Templates and placeholders](templates-and-placeholders.md)
- [Building blocks (settings)](../settings/building-blocks.md)
- [Custom blocks (AlgoWizard)](custom-blocks.md)
- [Concepts](../concepts.md)
- [Blocks catalog (onboarding)](../../onboard/04-builder/05-blocks-catalog.md)
