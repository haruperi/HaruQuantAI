# Stockpicker Engine

> An AlgoCloud engine that trades a basket of symbols — ranking candidates each bar and picking the best to hold — edited in the Picker editor.

## What it is

**Stockpicker** is one of the two AlgoCloud (`CT`) engines. Instead of trading a single
symbol, a Stockpicker strategy works over a **multi-symbol basket**: it ranks the candidate
symbols and picks the best ones to hold, up to a maximum number of open positions.

A Stockpicker strategy is marked with the `pickerEditor="true"` attribute on the strategy
element, and always opens in the **Picker** editor mode.

## Rule tabs

The Picker editor replaces the standard entry/exit tabs with:

- **Long** — the condition for going long on a candidate.
- **Short** — the condition for going short on a candidate.
- **Position Score** — the ranking rule (also available as **Position Score Long** /
  **Position Score Short**).

The Position Score rule is of type `StockpickerPS`. It assigns:

- `PositionScore` — the ranking score used to compare candidate symbols.
- `MaxOpenPositions` — how many positions may be held at once.

## What you can do

- Define the Long and Short conditions that qualify a symbol as a candidate.
- Build the **Position Score** rule that scores and ranks candidates so the engine can pick
  the best ones.
- Configure options such as `PickerMaxOpenPositions` (the maximum number of open positions
  the picker will hold).
- Compose the usual blocks (indicators, price, comparisons, logical operators) into the
  Long / Short / Position Score conditions.
- Backtest the basket on demand from the editor.

## How it works

Each bar, the engine evaluates the Long/Short conditions across the basket, computes a
`PositionScore` for the qualifying candidates, ranks them, and holds up to
`MaxOpenPositions` of the top-ranked symbols. On the Java side this is executed by
`StockpickerBacktestEngine` (the picker counterpart to the standard `BacktestEngine`).

Which blocks are available for the Stockpicker engine is controlled by the `forEngine`
filter in the block catalog, using the short code `SP` (Stockpicker). A filter such as
`forEngine="SP,SA"` means the block is available only on the cloud engines. See
[config-xml.md](config-xml.md).

Blocks are grouped in the palette by category (Signals, CandlePatterns, BarAndTime,
StrategyControl, Comparisons, Other, Functions, Price, Indicators, Random Conditions,
Random Values, Custom blocks; action categories Close, OtherActions, Modify, Open,
RandomActions), shown regardless of the active tab.

## Platform notes

Stockpicker runs only on AlgoCloud. A desktop strategy can be moved over with the
`convertStrategyForAC` helper, but AlgoCloud only accepts cloud engines — *"Only Stockpicker
or Single Asset strategies are supported in AlgoCloud"*, and *"Template strategies are not
supported in AlgoCloud"*.

## Related

- [AlgoWizard reference index](README.md)
- [Platforms & engines](engines-and-platforms.md)
- [Editor modes](editor-modes.md)
- [Standard (desktop) engines](engine-standard.md) · [Single-asset (cloud) engine](engine-single-asset.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [AlgoWizard functional overview](../algowizard.md) · [Concepts](../concepts.md)
- [Developer/architecture onboarding](../../onboard/07-algowizard/README.md)
