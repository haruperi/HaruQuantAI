# Settings tabs — field-level reference (for UI tests)

> Signpost hub for the **field-level** (deep) reference of each settings tab: every configurable UI
> control with the identifiers a UI test needs — visible label, `ng-model` config key, `data-testid`,
> input type, default, and option/enum values. This complements the prose pages in
> [`../`](../README.md), which describe *what each tab does*; open a leaf here only when you need the
> exact controls of one tab.

Parent: [Settings tabs (prose)](../README.md) · [Overview index](../../README.md)

## How this is sourced

Each settings tab is an AngularJS web plugin under
`work_directory/StrategyQuant/internal/plugins/Settings*`. The leaf pages extract the tab's controls
from its `views/*.html` template (labels, `ng-model`, `data-testid`, input types, `ng-options`) and
its `*Ctrl.js` / `*Service.js` (defaults, enum/option lists), cross-checked against backend Java
where an enum's values live server-side. Each leaf names its exact source plugin.

Where a "panel" has no plain form controls, the leaf says so and documents the real mechanism instead
of inventing fields — e.g. JS-rendered data grids (block selection), `contenteditable` rich text
(Notes), shared directives (parameter ranges), or CSV/AlgoWizard-only features (OppositeBlocks,
multiple same-direction orders).

## Shared tabs (Build / Optimize / Retest)

| Tab | Field reference | Prose |
|-----|-----------------|-------|
| Data (symbols, timeframes, period, IS/OOS, precision) | [data.md](data.md) | [../data.md](../data.md) |
| Trading options (tab controls + built-in options) | [trading-options.md](trading-options.md) | [../trading-options.md](../trading-options.md) |
| Money management (tab controls + method picker) | [money-management.md](money-management.md) | [../money-management.md](../money-management.md) |
| ATM — Advanced Trade Management | [atm.md](atm.md) | [../atm.md](../atm.md) |
| Notes (contenteditable rich text) | [notes.md](notes.md) | [../notes.md](../notes.md) |

## Build tabs

| Tab | Field reference | Prose |
|-----|-----------------|-------|
| What to build | [what-to-build.md](what-to-build.md) | [../what-to-build.md](../what-to-build.md) |
| Building blocks (tab controls; grids) | [building-blocks.md](building-blocks.md) | [../building-blocks.md](../building-blocks.md) |
| Genetic options | [genetic-options.md](genetic-options.md) | [../genetic-options.md](../genetic-options.md) |
| Ranking (fitness + databank limits) | [ranking.md](ranking.md) | [../ranking.md](../ranking.md) |
| Parts to improve | [parts-to-improve.md](parts-to-improve.md) | [../parts-to-improve.md](../parts-to-improve.md) |

## Building-blocks advanced sub-panels

| Panel | Field reference | Prose |
|-------|-----------------|-------|
| Custom blocks | [custom-blocks.md](custom-blocks.md) | [../custom-blocks.md](../custom-blocks.md) |
| Parameter ranges (shared `blockConfig` directive) | [parameter-ranges.md](parameter-ranges.md) | [../parameter-ranges.md](../parameter-ranges.md) |
| External indicators (lives in Data Manager) | [external-indicators.md](external-indicators.md) | [../external-indicators.md](../external-indicators.md) |
| Indicators calibration | [indicators-calibration.md](indicators-calibration.md) | [../indicators-calibration.md](../indicators-calibration.md) |
| OppositeBlocks / negation (CSV + AlgoWizard) | [oppositeblocks.md](oppositeblocks.md) | [../oppositeblocks.md](../oppositeblocks.md) |
| Multiple orders, same direction (AlgoWizard) | [multi-orders.md](multi-orders.md) | [../multi-orders.md](../multi-orders.md) |
| Multiple exits generation (ATM generate mode) | [multiple-exits.md](multiple-exits.md) | [../multiple-exits.md](../multiple-exits.md) |

## Cross-checks

The Cross-checks tab's methods and their settings are cataloged in the snippets hub, not here:
[../../snippets/cross-checks.md](../../snippets/cross-checks.md) · prose: [../cross-checks.md](../cross-checks.md).

## Related

- Settings tabs (prose reference): [`../README.md`](../README.md)
- Snippet catalogs (methods behind the pickers): [`../../snippets/README.md`](../../snippets/README.md)
- Custom Projects & the task model: [`../../custom-projects.md`](../../custom-projects.md)
