# Editor Modes

> AlgoWizard opens each strategy in one of three editor layouts — Simple, Full, or Picker — chosen automatically from the strategy's shape.

## What it is

When AlgoWizard loads a strategy it picks an **editor mode** (`EditorTypes` enum):

- **simple** — a streamlined, guided layout for straightforward strategies.
- **full** — the complete editor with no restrictions.
- **picker** — the Stockpicker-specific layout.

The mode is selected on load, not chosen freely by the user; it follows from the
strategy's attributes and structure.

## How the mode is chosen

Loading applies this decision order:

1. If the strategy is a Stockpicker (`pickerEditor`) → **Picker**.
2. Else if it is a single-asset strategy → **Simple** (single-asset always opens Simple).
3. Else if `checkSimpleCompatibility` passes → **Simple**.
4. Otherwise → **Full**.

## Simple mode

Simple mode is offered only for "simple-compatible" strategies. `checkSimpleCompatibility`
requires all of:

- Exactly the canonical rules named **Trading signals**, **Long entry**, **Short entry**,
  **Long exit**, **Short exit** (plus an optional **Explore** rule) — no more, no fewer.
- Only basic action keys: `EnterAtMarket`, `EnterReverseAtMarket`, `EnterAtStop`,
  `EnterAtLimit`, `ClosePosition`.
- **No advanced stop-loss features** — no move-SL-to-breakeven, no trailing stop, no
  formula-based or price-level SL / PT.

Single-asset cloud strategies always open in Simple mode regardless of the above.

Simple mode presents a guided layout with Wizard **Steps**:

1. Long entry
2. Short entry
3. Long exit
4. Short exit
5. Money management
6. Finish

Its description notes that *"you can switch to Full editor for complete functionality."*

## Full mode

Full mode is the complete editor. It imposes none of the Simple-mode restrictions and
supports:

- Arbitrary rules and events (beyond the canonical five).
- Advanced exits (move-to-breakeven, trailing stops, formula / price-level SL & PT).
- Variables and the full action set.

Any strategy that is not simple-compatible (and is not a Stockpicker) opens here.

## Picker mode

Picker mode is used for Stockpicker strategies. It replaces the standard entry/exit rule
tabs with **Long**, **Short**, and **Position Score** tabs. See
[engine-stockpicker.md](engine-stockpicker.md).

## Rule tabs by mode

- **Simple / Full:** Trading signals, Long entry, Short entry, Long exit, Short exit
  (+ optional Explore). Note the signals tab is **"Trading signals"**, not just "Signals"
  — "Signals" alone is a block-palette category, a different thing.
- **Picker:** Long, Short, Position Score.

## Related

- [AlgoWizard reference index](README.md)
- [Platforms & engines](engines-and-platforms.md)
- [Standard (desktop) engines](engine-standard.md)
- [Stockpicker engine](engine-stockpicker.md)
- [Single-asset (cloud) engine](engine-single-asset.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [AlgoWizard functional overview](../algowizard.md) · [Concepts](../concepts.md)
- [Developer/architecture onboarding](../../onboard/07-algowizard/README.md)
