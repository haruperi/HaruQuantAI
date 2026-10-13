# Strategy Config — Results tab

> Compare the module's current configuration against the settings that produced the strategy.

## What it shows

The Strategy Config tab shows the current configuration of the module side by side with the
configuration that was used in the strategy's last backtest. Any differences between the two are
highlighted in **red**, so you can quickly spot where your current settings diverge from the
settings that created this strategy.

## How it works

The tab is served by the `StrategyConfig` plugin at `/strategyconfig/`. Like every Results tab,
it obtains the strategy's locked `ResultsGroup` through an `IResultsGroupProvider`
(`DatabankResultsGroupProvider`) and reads the strategy XML configuration stored with the result,
then compares it field by field with the module's current configuration to produce the
difference view.

**Trading options** are one section whatever the engines of the two sides. Each side lists only
the options offered for its engine, the same set the Trading options settings tab shows
(`@ForEngine` on the option parameter, applied in `SettingsOptionsPlugin.getStrategyConfigSettings`).
An option neither engine has - for example *Use initial SL & PT* when both sides run on MetaTrader -
has no row. When the two sides run on different engines, an option only one of them has shows
`Not available for <engine>` on the other side (`StrategyConfig.print`), with the engine named as
the engine selection shows it, and counts as a difference.

## Options & settings

- **Apply Strategy Config** — a button that loads the settings from the strategy and applies
  them to the selected module, so you can reproduce the exact configuration that generated the
  strategy.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [source-code.md](source-code.md),
  [equity-chart.md](equity-chart.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/strategyconfig/`
