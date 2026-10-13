# Standard (Desktop) Engines

> The ordinary desktop trading engines — MT4, MT5, Tradestation, MultiCharts, JForex — that trade a single symbol and open in the Simple or Full editor.

## What it is

A "Standard" strategy is one that targets the **desktop platform** (`SQ`) and one of the
desktop trading engines. There is no engine literally named "Standard" — the word simply
distinguishes these ordinary desktop engines from the AlgoCloud (`CT`) engines.

The desktop engines (the `Engines` enum) are:

- **MetaTrader 4**
- **MetaTrader 5 (netted)**
- **MetaTrader 5 (hedged)**
- **Tradestation**
- **MultiCharts**
- **JForex**

A desktop strategy trades a single symbol on the chosen platform, using the standard
signal-based rule architecture.

## Rule tabs

A standard strategy is edited through these rule tabs (in either the Simple or Full
editor):

- **Trading signals** — the special signal rule that evaluates all trading conditions and
  produces the entry/exit signals.
- **Long entry** — opens a long trade from the signals.
- **Short entry** — opens a short trade from the signals.
- **Long exit** — closes a long trade.
- **Short exit** — closes a short trade.
- **Explore** *(optional)* — an extra rule tab.

Note: the signals tab is **"Trading signals"** — not just "Signals". "Signals" on its own
is a block-palette *category*, which is a different thing (see below).

## What you can do

- Build the signal rule that combines conditions (indicators, price, comparisons, logical
  operators) into long/short entry and exit signals.
- Define entry actions using order types such as `EnterAtMarket`,
  `EnterReverseAtMarket`, `EnterAtStop`, `EnterAtLimit`, and exit with `ClosePosition`.
- In the **Full** editor, add advanced exits (move-SL-to-breakeven, trailing stops,
  formula- and price-level SL / PT), arbitrary rules/events, and variables.
- Set money management (position sizing, stops and targets, order settings).
- Backtest the strategy on demand from the editor.

## How it works

The signal-based rule architecture separates the trading conditions from the actions: the
**Trading signals** rule computes long/short entry & exit signals, and the entry/exit rules
then act on those signals. This avoids the ambiguity of the older direct IF-THEN style
where long and short (or entry and exit) conditions could be valid at the same time.

Which blocks are offered depends on the engine, via the `forEngine` filter in the block
catalog. Desktop engines are addressed with codes `MT4`, `MT5`, `TS`, `MC`, `JF`; a filter
like `forEngine="*,-SP,-SA"` means *all engines except the cloud ones*. See
[config-xml.md](config-xml.md).

Blocks are grouped in the palette by **category** — Signals, CandlePatterns, BarAndTime,
StrategyControl, Comparisons, Other, Functions, Price, Indicators, Random Conditions,
Random Values, and Custom blocks — plus action categories Close, OtherActions, Modify,
Open, RandomActions. These categories are shown regardless of which rule tab is active.

## Editor modes

A standard strategy opens in **Simple** mode if it is simple-compatible (the canonical five
rules, only basic actions, no advanced SL features), otherwise in **Full** mode. See
[editor-modes.md](editor-modes.md).

## Related

- [AlgoWizard reference index](README.md)
- [Platforms & engines](engines-and-platforms.md)
- [Editor modes](editor-modes.md)
- [Stockpicker engine](engine-stockpicker.md) · [Single-asset (cloud) engine](engine-single-asset.md)
- [config.xml — the available-blocks catalog](config-xml.md)
- [Templates & placeholders](templates-and-placeholders.md)
- [AlgoWizard functional overview](../algowizard.md) · [Concepts](../concepts.md)
- [Developer/architecture onboarding](../../onboard/07-algowizard/README.md)
