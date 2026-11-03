# OppositeBlocks (negation control) — Building blocks deep dive
> Overrides how SQ negates blocks when it builds the opposite (Short) rule from the Long rule.

**Field-level controls (for UI tests):** [fields/oppositeblocks.md](fields/oppositeblocks.md)

**Applies to:** Build — a global configuration file, not a per-project UI control.

## What it configures

By default StrategyQuant generates **symmetrical Long and Short rules** using opposite comparisons —
this is called **negation**. SQ first creates the Long condition and negates it to produce the Short
condition, for example:

```
Long:  CCI(14) > 0
Short: CCI(14) < 0
```

Every block has a corresponding opposite block (`>` negates to `<`, `=` negates to `<>`, and so on).
These defaults are defined in the block's Java snippet code and are **not configurable from the UI** —
but you can override them with a configuration file.

## Main options

- **`\user\settings\OppositeBlocks.csv`** — create this file in your StrategyQuant installation to
  override the default negations (it doesn't exist by default; an `OppositeBlocks_example.csv` shows
  the full default list).
- **File format** — one `Block;OppositeBlock` pair per line, using the block **snippet code names**
  (visible in the CodeEditor). For example:
  ```
  Equals;NotEquals
  NotEquals;Equals
  ```
  makes `Equals (=)` negate to `NotEquals (<>)` and vice versa (Long `CCI(14) = 0` → Short
  `CCI(14) <> 0`).
- **Non-negating mappings** — you can map a block to itself to keep the same comparison in both
  directions:
  ```
  Equals;Equals
  NotEquals;NotEquals
  ```
  which produces Long and Short with the *same* comparison (e.g. both `CCI(14) = 0`).
- You must **restart StrategyQuant** after changing the file for changes to take effect.

## How it affects generation

Negation rules decide what the Short rule looks like relative to the Long rule for every generated
strategy. Overriding them lets you change SQ's assumptions about how a block "reverses" — useful when
the default opposite doesn't match your intended trading logic. Custom blocks have their own
per-block opposite handling in AlgoWizard (see [custom-blocks.md](custom-blocks.md)); this file
governs the global negation of standard blocks.

## Related

- Settings index: [README.md](README.md)
- Parent panel: [building-blocks.md](building-blocks.md)
- Per-block opposites for custom blocks: [custom-blocks.md](custom-blocks.md)
- Concepts (building block, Long/Short symmetry): [../concepts.md](../concepts.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
