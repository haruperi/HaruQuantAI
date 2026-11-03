# Parts to improve — field reference (for UI tests)

> Exact controls, `ng-model` bindings, defaults and `data-testid`s for the Parts to improve settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsPartsToImprove/` (`views/partsToImprove.html`, `PartsToImproveCtrl.js`, `PartsToImproveService.js`). Tab registered as `SettingsTab` id 6, `configElemName: PartsToImprove`, `dataItem: settings-partstoimprove`, task: `Build` only. The tab is shown only when **What to build → Strategy type = Improve existing strategy** (toggled by `WhatToBuildService.updateTabs()` via `SETTINGS_TAB_SHOW`, tab key `settings-partstoimprove`). No `testId` is set on the tab registration.

Each rule part has a LONG and a SHORT row. The SHORT row is auto-symmetric to LONG when the corresponding symmetry flag is set (symmetry is inherited from **What to build → Trading directions**, not editable here — see the "How it works" note in the template). Rows are enabled/disabled based on `config.direction` (enum `buildStrategyDirections`: `both`, `long`, `short`; default `both`). Action selects use `actions` (enum `improveActionTypes`: `addOrReplace="add-or-replace"`, `replace="replace"`, `add="add"`; default `addOrReplace`), rendered as `item.value as item.name for item in actions` with labels **Add or replace / Replace / Add**. Persisted under `PartsToImprove` (`EntryRules` / `OrderTypes` / `ExitRules` with `LongImprovement` / `ShortImprovement` `use` + `action` attributes).

## Entry rules

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| LONG (use) | `config.entryRules.long.use` | checkbox | `true` | `data-testid="settings-pti-entry-long"`. Disabled when direction = short. |
| LONG action | `config.entryRules.long.action` | `<select>` | `addOrReplace` | `data-testid="settings-pti-entry-long-action"`. Options: Add or replace / Replace / Add. Hidden when direction = short. |
| SHORT (use) | `config.entryRules.short.use` | checkbox | `true` | `data-testid="settings-pti-entry-short"`. Disabled when (direction = both && entry symmetry) or direction = long. |
| SHORT action | `config.entryRules.short.action` | `<select>` | `addOrReplace` | `data-testid="settings-pti-entry-short-action"`. Hidden when (both && symmetry) or long; shows "Symmetric to Long" text instead when symmetric. |

## Order types

Order-type rows have a "use" checkbox only (no action select). Text shows "Generate randomly" when used, else "Keep existing".

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| LONG (use) | `config.orderTypes.long.use` | checkbox | `true` | `data-testid="settings-pti-order-types-long"`. Disabled when direction = short. |
| SHORT (use) | `config.orderTypes.short.use` | checkbox | `true` | `data-testid="settings-pti-order-types-short"`. Disabled when direction = long. (Order types have no symmetry flag; short is always saved with its own `use`.) |

## Exit rules

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| LONG (use) | `config.exitRules.long.use` | checkbox | `true` | `data-testid="settings-pti-exit-long"`. Disabled when direction = short. |
| LONG action | `config.exitRules.long.action` | `<select>` | `addOrReplace` | `data-testid="settings-pti-exit-long-action"`. Options: Add or replace / Replace / Add. Hidden when direction = short. |
| SHORT (use) | `config.exitRules.short.use` | checkbox | `true` | `data-testid="settings-pti-exit-short"`. Disabled when (both && exit symmetry) or direction = long. |
| SHORT action | `config.exitRules.short.action` | `<select>` | `addOrReplace` | `data-testid="settings-pti-exit-short-action"`. Hidden when (both && symmetry) or long. |

## ATM - advanced exits

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Improve / generate (Ultimate version only) | `config.improveATM` | checkbox | `false` | `data-testid="settings-pti-atm"`. Persisted as `PartsToImprove[improveATM]`. Enabled only in Ultimate version (`$root.license.isUltimateVersion`); forced `false` otherwise. "How it works" link opens help. |

## Related

- Prose page: [../parts-to-improve.md](../parts-to-improve.md)
- Fields hub: [README.md](README.md)
