# Building blocks — field reference (for UI tests)

> The Building blocks tab's own controls (block-group accordions, filters, random/save buttons, calibration and external-indicator toggles). The actual catalog of selectable block snippets lives elsewhere — see link below.

Source: `internal/plugins/SettingsBlocks/` (`views/blocks.html`, `BlocksCtrl.js`, `services/BlocksService.js`). Tab registered as `SettingsTab` id 30, `testId: settings-tab-blocks`, `configElemName: Blocks`, task: `Build` only.

> The list of individual building-block snippets (signals, indicators, operators, order/exit types) is cataloged in [`../../snippets/building-blocks/README.md`](../../snippets/building-blocks/README.md). This page documents the **tab's own controls** — the block-group grids are rendered by JavaScript into `<div id="...Grid">` containers (not AngularJS form controls), so per-row block selection/weight is not enumerable as `ng-model` here; each grid's container `data-testid` is listed for locating it.

## Block group grids (JS-rendered, accordion / fieldset containers)

Each block-group grid is a `div` container populated by `BlocksService.init*Grid()`; rows carry per-block "use" checkboxes and weight columns managed inside the grid component. The left column is an accordion (`showBlocks(area)` toggles `gui.shownBlocks`, default `"signals"`); each header shows a live selected-count from `selectedCounts`.

| Group (legend) | Accordion key | Grid container id | data-testid | Count binding |
|---|---|---|---|---|
| Signals (Predefined conditions) | `signals` | `#blocksGrid` | `settings-blocks-signals-grid-btn` | `selectedCounts.blocks` |
| Indicators | `indicators` | `#indicatorsGrid` | `settings-blocks-indicators-grid-btn` | `selectedCounts.indicators` |
| Stop/Limit entry blocks | `stopLimitBlocks` | `#stopLimitBlocksGrid` | `settings-blocks-stoplimit-grid-btn` | `selectedCounts.stopLimitBlocks` |
| Order types | — (always shown) | `#orderTypesGrid` | `settings-blocks-order-types-grid-btn` | — |
| Exit types | — (always shown) | `#exitTypesGrid` | `settings-blocks-exit-types-grid-btn` | — |
| External indicators for timeframe(s) | — (hidden for Stockpicker) | `#customDataGridBB` | `settings-blocks-custom-data-grid-btn` | — |

`selectedCounts` initial values: `blocks: 0, indicators: 0, stopLimitBlocks: 0` (updated as blocks are selected).

## Signals / Indicators filter toolbars

Shown above the Signals and Indicators grids when that accordion is open. Filter state objects: `signalsFilter = { key: 'None' }`, `indicatorsFilter = { key: 'None' }` (defaults `'None'`). Buttons call `onFilterClick(category, key)`.

| Control | Type | Default | Options / notes |
|---|---|---|---|
| Reset | link (`onFilterClick(cat, 'None')`) | — | Clears filter to `'None'`. |
| Checked filter | toggle button (`key='Checked'`) | off | Shows only checked blocks. Active when `filter.key == 'Checked'`. |
| A … Z letter filters | button group | — | `filterButtonKeys = ['A'..'Z']` (26 letter buttons); active when `key == filter.key`. |

## Left-column action row (`.random-options`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Indicators calibration button | `<indicators-calibration-button>` component | button | — | Hidden for Stockpicker (`gui.isStockPicker`). Opens calibration config (separate component). |
| calibrate before start | `gui.autoCalibrateBeforeStart` | checkbox | `false` | id `ac-before-start`, `data-testid="settings-blocks-auto-calibrate"`. Persisted as `Blocks/Calibration[calibrateBeforeStart]` (forced `false` for Stockpicker). Hidden for Stockpicker. |
| Randomly choose 100 blocks | `onRandomChoice()` | button | — | Disabled when `!randomButtons.enabled` (default enabled `true`). |
| Add 10 random blocks | `onAddRandomBlocks()` | button | — | Disabled when `!randomButtons.enabled`. |
| Load settings (conditions-btn-load) | `onLoadSettings()` | button | — | Loads block settings from file (`cfx,sqb`). |
| Save settings (conditions-btn-save) | `onSaveSettings()` | button | — | Saves block settings to file (`sqb`). |

> Additional calibration state read/written by the service but with no direct control in this template: `gui.useCalibrationMaxSteps` (default `true`, persisted `Calibration[useMaxSteps]`) and `gui.calibrationMaxSteps` (default `50`, persisted `Calibration[maxSteps]`) — configured inside the indicators-calibration component/popup.

## External indicators panel (hidden for Stockpicker)

Legend shows `customDataTimeframes.list`. "Add new" (`addCDataIndy()`) opens the external-data indicator editor (separate window).

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Show all external indicators (also for not-matching Timeframes) | `gui.showAllCDataIndy` | checkbox | `false` | `data-testid="settings-blocks-show-all-external"`. Persisted as `Blocks/CustomData[showAll]`. |

## Popups

`views/blockParametersPopup.html` (`#blockParametersPopup`) and `views/possibleOptionsPopup.html` (`#possibleOptionsPopup`) configure a single block's parameter generation / possible-options sets (opened per block from the grids). These are per-block parameter editors; their field set depends on the selected block and is covered by the parameter-ranges documentation, not enumerable as fixed `ng-model`s here.

## Related

- Prose page: [../building-blocks.md](../building-blocks.md)
- Block snippet catalog: [../../snippets/building-blocks/README.md](../../snippets/building-blocks/README.md)
- Fields hub: [README.md](README.md)
