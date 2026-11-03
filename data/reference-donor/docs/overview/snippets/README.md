# Snippets — reference catalogs

> Hub for the full, code-faithful catalogs of SQX's **pluggable snippet types**. Each leaf page
> enumerates one snippet family with its display names, classes, and — where they apply — the exact
> configurable **parameters (default / min / max / step)**, so the pages double as a settings
> reference for UI tests. These are lookup tables; open only the leaf you need.

Parent: [Overview index](../README.md)

## What "snippets" are

Almost everything SQX offers in its pickers and settings panels — indicators, conditions, actions,
position-sizing methods, exit rules, robustness manipulations, databank columns, engine charts — is
a small Java **snippet** class loaded at startup from
`work_directory/StrategyQuant/internal/extend/Snippets/SQ/`. Each category has its own subfolder and
its own loader (`CustomClasses<T>` subclass). The set is **extensible**: a user snippet dropped into
the right folder appears in the UI exactly like the stock ones. The catalogs below document the
stock set shipped with SQX.

Most snippets declare their UI label and settings through annotations —
`@BuildingBlock` / `@ClassConfig` / `@Formula` (name + `display` template), `@Help` (tooltip), and
`@Parameter(name, defaultValue, minValue, maxValue, step)` fields (the configurable settings). A few
categories (Checkers, Calculators, Engine charts, Correlation series, Portfolio-master fitness) carry
no `@Parameter`s and are configured via their constructor instead — noted on each page.

## Strategy building blocks

Components used to compose strategy entry/exit rules, price/stop levels, and actions (569 blocks).

| Catalog | Count | Page |
|---------|------:|------|
| **Building blocks** (hub) | 569 | [building-blocks/README.md](building-blocks/README.md) |
| ├ Indicators (52 families) | 400 | [building-blocks/indicators.md](building-blocks/indicators.md) |
| ├ Price / volume series | 30 | [building-blocks/price.md](building-blocks/price.md) |
| ├ Bar & time conditions | 37 | [building-blocks/bar-and-time.md](building-blocks/bar-and-time.md) |
| ├ Comparisons / logic | 27 | [building-blocks/comparisons.md](building-blocks/comparisons.md) |
| ├ Strategy control (account/position) | 25 | [building-blocks/strategy-control.md](building-blocks/strategy-control.md) |
| ├ Functions (math/util) | 18 | [building-blocks/functions.md](building-blocks/functions.md) |
| ├ Order & other actions | 20 | [building-blocks/order-actions.md](building-blocks/order-actions.md) |
| ├ Candle patterns | 7 | [building-blocks/candle-patterns.md](building-blocks/candle-patterns.md) |
| └ Variables / constants | 5 | [building-blocks/variables.md](building-blocks/variables.md) |

## Trade management

How positions are sized, exited, and constrained.

| Catalog | Count | Page |
|---------|------:|------|
| **Money management / position sizing** | 12 | [money-management.md](money-management.md) |
| **Exit methods** | 5 | [exit-methods.md](exit-methods.md) |
| **Trading options** (always-active settings) | 8 | [trading-options.md](trading-options.md) |

## Robustness / retest

Manipulations and randomizations applied when stress-testing strategies.

| Catalog | Count | Page |
|---------|------:|------|
| **Cross-check methods** (Build/Retester robustness) | 9 | [cross-checks.md](cross-checks.md) |
| **What-If manipulations** | 15 | [whatif.md](whatif.md) |
| **Monte Carlo randomization** (manipulation + retest) | 5 + 9 | [monte-carlo.md](monte-carlo.md) |

## Formulas & generation internals

| Catalog | Count | Page |
|---------|------:|------|
| **Formulas** (price / range / SL-PT / size) | 19 | [formulas.md](formulas.md) |
| **Negaters** (how the Builder inverts blocks) | 15 | [negater.md](negater.md) |
| **Checkers & Calculators** (validation / math helpers) | 3 + 7 | [checker-calculators.md](checker-calculators.md) |

## Metrics, columns & charts

| Catalog | Count | Page |
|---------|------:|------|
| **Stats metrics** (Databank columns) | ~120 | [../stats-metrics.md](../stats-metrics.md) |
| **Databank columns — extra** (Trades + Walk-Forward) | 30 + 8 | [databank-columns-extra.md](databank-columns-extra.md) |
| **Trade Analysis charts** | 27 | [../results-tabs/trade-analysis-charts.md](../results-tabs/trade-analysis-charts.md) |
| **Engine charts** (live during runs) | 14 | [engine-charts.md](engine-charts.md) |
| **Correlation-of series** | 6 | [correlation-of.md](correlation-of.md) |
| **Portfolio Master fitness functions** | 3 | [portfolio-master-fitness.md](portfolio-master-fitness.md) |

## Assistant tools

`SQ/AITools/` is a snippet type with no stock catalog — every entry is user-authored. A class
extending `AITool` (`tradinglib/AITool.java`) becomes a tool the built-in AI assistant can call:
the class name is turned into the tool name (`SomeRiskReport` → `ext_some_risk_report`, the
`ext_` prefix keeps it from shadowing a builtin), `@Description`/`@Help` become the tool
description, the public `@Parameter` fields become the JSON input schema (`int`, `double`,
`boolean`, `String`; no `defaultValue` = required argument) and `run()` returns the answer.

`AITools` (`ailib/`) rebuilds the tool list every turn, so a snippet is callable
right after `compile_snippets` — only the externally served MCP transports, which build their list
once at startup, need a restart. A call gets `timeoutSeconds()` (120 by default) on its own daemon
thread and its answer is capped at 32 KB, the same cap as `run_python`. The Code Editor's
*New → AI tool* entry writes the starting file from
`internal/web/SQEDITOR/templates/SQ/AITools/AITools.tpl`.

User guide: [`../../sqai/ai-guide.html`](../../sqai/ai-guide.html) §10.

## Related

- Functional overview: [`../README.md`](../README.md)
- Builder (consumes building blocks): [`../builder.md`](../builder.md)
- Robustness tests / cross-checks (prose): [`../robustness-tests/README.md`](../robustness-tests/README.md)
- Results & Databank overview: [`../results-databank.md`](../results-databank.md)
