# Settings Tabs — Detailed Reference

StrategyQuant X shows a task's configuration as **settings tabs** (the "Full settings"). The same tab
set is used whether you open the standalone Builder/Optimizer/Retester or configure the equivalent
task inside a [Custom Project](../custom-projects.md). This folder has one leaf page per tab.

**Some tabs are shared across tasks; some are specific to one task.** The matrix below shows which tab
appears for which task. (✓ = present, — = not applicable.)

Parent: [Custom Projects & the task model](../custom-projects.md) · [Overview index](../README.md)

> **Field-level reference (for UI tests):** each tab below also has a deep companion page listing its
> exact UI controls (label, `ng-model` key, `data-testid`, type, default, options) — see the
> [Settings fields hub](fields/README.md). Open a field page only when you need one tab's controls.

## Shared vs task-specific matrix

| Settings tab | Build | Optimize | Retest | Notes |
|--------------|:-----:|:--------:|:------:|-------|
| [Data](data.md) | ✓ | ✓ | ✓ | **Shared** — symbols, timeframes, period, IS/OOS split, precision |
| [Trading options](trading-options.md) | ✓ | ✓ | ✓ | **Shared** — sessions, time filters, order types, spreads, SL/PT caps |
| [Money management](money-management.md) | ✓ | ✓ | ✓ | **Shared** — position sizing |
| [ATM](atm.md) | ✓ | ✓ | ✓ | **Shared** — Advanced Trade Management (multiple/scale-out exits) |
| [Notes](notes.md) | ✓ | ✓ | ✓ | **Shared** — free-text notes stored with the project |
| [What to build](what-to-build.md) | ✓ | — | — | **Build-specific** — strategy type, style, direction, complexity, SL/PT |
| [Building blocks](building-blocks.md) | ✓ | — | — | **Build-specific** — which indicators/signals/operators the generator may use |
| [Genetic options](genetic-options.md) | ✓ | — | — | **Build-specific** (genetic mode) — population, generations, islands |
| [Ranking](ranking.md) | ✓ | ✓ | — | Build & Optimize — fitness/selection criteria + databank limits |
| [Cross-checks](cross-checks.md) | ✓ | — | ✓ | Build & Retest — robustness tests as filters (Build) or annotations (Retest) |
| [Parts to improve](parts-to-improve.md) | ✓ | — | — | **Build-specific** — when improving an existing strategy |

> The Optimizer adds its own optimization-range configuration (parameter ranges + optimization type);
> see [optimize-strategies.md](../tasks/optimize-strategies.md). The Retester's test configuration is the
> Cross-checks / robustness tests; see [retest-strategies.md](../tasks/retest-strategies.md).

## Core settings tabs

| Tab | Configures | Page |
|-----|-----------|------|
| **What to build** | Strategy type, entry/exit logic, SL/PT types, directions | [what-to-build.md](what-to-build.md) |
| **Building blocks** | Indicators, signals, operators available to the generator | [building-blocks.md](building-blocks.md) |
| **Data** | Symbols, timeframes, backtest period, IS/OOS split, precision | [data.md](data.md) |
| **Genetic options** | Population, generations, crossover/mutation, islands | [genetic-options.md](genetic-options.md) |
| **Trading options** | Sessions/time filters, order types, spreads, SL/PT limits | [trading-options.md](trading-options.md) |
| **Money management** | Position sizing applied to strategies | [money-management.md](money-management.md) |
| **ATM (Advanced Trade Management)** | Multiple exits / scale-out configuration | [atm.md](atm.md) |
| **Ranking** | Fitness/ranking criteria + databank storage limits | [ranking.md](ranking.md) |
| **Cross-checks** | Robustness tests applied during generation | [cross-checks.md](cross-checks.md) |
| **Parts to improve** | Which parts of an existing strategy to regenerate | [parts-to-improve.md](parts-to-improve.md) |
| **Notes** | Free-text notes saved with the project | [notes.md](notes.md) |

## Building-blocks deep dives

The Building blocks tab has several advanced configuration areas, each with its own page:

| Topic | Page |
|-------|------|
| Custom blocks (user-created blocks) | [custom-blocks.md](custom-blocks.md) |
| Configuring parameter ranges (standard & custom blocks) | [parameter-ranges.md](parameter-ranges.md) |
| External indicators | [external-indicators.md](external-indicators.md) |
| Indicators calibration | [indicators-calibration.md](indicators-calibration.md) |
| OppositeBlocks / negation | [oppositeblocks.md](oppositeblocks.md) |
| Multiple orders to the same direction | [multi-orders.md](multi-orders.md) |
| Multiple exits generation (scale-out / ATM) | [multiple-exits.md](multiple-exits.md) |

> For the concepts behind these (genetic programming, IS/OOS, fitness, robustness), see
> [../concepts.md](../concepts.md). Developer detail: [../../onboard/04-builder/](../../onboard/04-builder/README.md).
