# Single-Asset (Cloud) Engine

> An AlgoCloud engine that trades one symbol — the cloud counterpart of a desktop strategy — and always opens in the Simple editor.

## What it is

**Single-asset** is one of the two AlgoCloud (`CT`) engines. It trades a **single symbol**,
just like a desktop strategy, but runs on the AlgoCloud platform rather than on a desktop
trading engine.

A single-asset strategy is marked with the `singleAsset="true"` attribute on the strategy
element. It **always opens in the Simple editor** mode, regardless of its structure.

## Rule tabs

A single-asset strategy uses the same standard rule tabs as a desktop strategy:

- **Trading signals** — the signal rule that evaluates all trading conditions.
- **Long entry** — opens a long trade.
- **Short entry** — opens a short trade.
- **Long exit** — closes a long trade.
- **Short exit** — closes a short trade.
- **Explore** *(optional)*.

Because it opens in Simple mode, its guided layout follows the Wizard **Steps**: Long entry,
Short entry, Long exit, Short exit, Money management, Finish. Note the signals tab is
**"Trading signals"**, not just "Signals" (which is a block-palette category).

## What you can do

- Build the signal rule combining conditions (indicators, price, comparisons, logical
  operators) into long/short entry and exit signals.
- Define entry actions with the basic order types (`EnterAtMarket`, `EnterReverseAtMarket`,
  `EnterAtStop`, `EnterAtLimit`) and exit with `ClosePosition`.
- Set money management (position sizing, stops and targets).
- Backtest on demand from the editor.

Because single-asset always opens in Simple mode, the advanced exit features
(move-SL-to-breakeven, trailing stop, formula/price-level SL & PT) and arbitrary
rules/events of the Full editor are not part of this layout. As the Simple editor notes,
*"you can switch to Full editor for complete functionality."*

## How it works

The single-asset engine trades one symbol using the standard signal-based rule
architecture: the **Trading signals** rule computes long/short entry & exit signals and the
entry/exit rules act on them.

Which blocks are available is controlled by the `forEngine` filter in the block catalog,
using the short code `SA` (Single-asset). A filter such as `forEngine="SP,SA"` means the
block is available only on the cloud engines. See [config-xml.md](config-xml.md).

Palette categories (Signals, CandlePatterns, BarAndTime, StrategyControl, Comparisons,
Other, Functions, Price, Indicators, Random Conditions, Random Values, Custom blocks; action
categories Close, OtherActions, Modify, Open, RandomActions) are shown regardless of the
active tab.

## Platform notes

Single-asset runs only on AlgoCloud. A desktop strategy can be converted with the
`convertStrategyForAC` helper, but AlgoCloud only accepts cloud engines — *"Only Stockpicker
or Single Asset strategies are supported in AlgoCloud"*, and *"Template strategies are not
supported in AlgoCloud"*.

## Related

- [AlgoWizard reference index](README.md)
- [Platforms & engines](engines-and-platforms.md)
- [Editor modes](editor-modes.md)
- [Standard (desktop) engines](engine-standard.md) · [Stockpicker engine](engine-stockpicker.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [AlgoWizard functional overview](../algowizard.md) · [Concepts](../concepts.md)
- [Developer/architecture onboarding](../../onboard/07-algowizard/README.md)
