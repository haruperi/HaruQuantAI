# Parameter ranges — field reference (for UI tests)

> The per-block "Parameter ranges" popup (shared `block-config` directive) used from Building blocks,
> plus the global Period/Shift ranges it falls back to on the What to build tab.

Source:
- `internal/web/app/directives/blockConfig/blockConfig.html` — the 3-tab popup body (directive
  `<block-config>`).
- `internal/web/app/directives/blockConfig/editParamPopup.html` — single-parameter editor (Min/Max/Step
  or Fixed value).
- `internal/web/app/directives/blockConfig/editParamSetPopup.html` — parameter-set editor.
- `internal/web/app/directives/blockConfig/BlockConfig.js`, `BlockConfigService.js` — grid wiring,
  `generationTypes` enum.
- `internal/plugins/SettingsBlocks/views/blockParametersPopup.html`,
  `internal/plugins/SettingsBlocks/views/possibleOptionsPopup.html` — the two modal shells that host
  `<block-config>` from the Building blocks tab.
- `internal/plugins/SettingsWhatToBuild/views/settings/conditionsAndPeriods/conditionsAndPeriods.html`
  — the **global** Period/Shift ranges these per-block ranges fall back to.

## Opening the popup

From `internal/plugins/SettingsBlocks/views/blocks.html`: double-clicking / clicking the "Parameters"
action link on a row in `blocksGrid`, `indicatorsGrid`, `stopLimitBlocksGrid`, `orderTypesGrid`, or
`exitTypesGrid` opens `blockParametersPopup.html` (`#blockParametersPopup`), which embeds
`<block-config selected-block="selectedBlock" complexities="config.complexities" />`. "Edit possible
options" flows (special/exit blocks) instead open `possibleOptionsPopup.html`
(`#possibleOptionsPopup`), which embeds the same directive per accordion item, optionally with
`disableParamSets`.

## `blockConfig.html` — tab structure

Tabs shown in `.quant-tabs .tabs-header`, driven by `selectedTab` (default `'sets'`):

| Tab (`data-item`) | Label | Shown when | `selectedTab` value |
|---|---|---|---|
| `parameter-sets-item` | Parameter sets | `selectedBlock.category != categories.orderTypes && !disableParamSets` | `sets` |
| `parameters-item` | Parameter values | always | `params` |
| `indicator-values-item` | Indicator values | `selectedBlock.indicatorMin != null` | `indicator-values` |

### "Parameter values" tab

| Control | Config key / grid | Type | Notes |
|---|---|---|---|
| Parameters grid | `parametersGridId` (`sqGrid`) | grid | Columns: Parameter name, Type, Generation, Possible values. Double-click a row → `editParamPopup`. |
| Apply to all blocks of the same indicator | `selectedBlock.onApplyToAll(true)` | button | Shown only when `selectedBlock.category == categories.signals`. |
| Reset to default | `selectedBlock.onResetToDefault(selectedBlock, true)` | button | |

### "Parameter sets" tab

| Control | Config key / grid | Type | Notes |
|---|---|---|---|
| Parameter sets grid | `parameterSetsGridId` (`sqGrid`) | grid | Columns: Set name, Possible values, Weight (spinner), delete (×). Last row is "Add new set" action link. Double-click a set row (not first/last) → `editParamSetPopup`. |
| Apply to all blocks of the same indicator | `selectedBlock.onApplyToAll(false)` | button | Signals category only. |
| Reset to default | `selectedBlock.onResetToDefault(selectedBlock, false)` | button | |

### "Indicator values" tab (only if `selectedBlock.indicatorMin != null`)

| Label | Config key (ng-model) | Type | Notes |
|---|---|---|---|
| Minimum | `selectedBlock.indicatorMin` | number spinner (`sqn-spinner`) | step 1 |
| Maximum | `selectedBlock.indicatorMax` | number spinner | step 1 |
| Step | `selectedBlock.indicatorStep` | number spinner | step 1 |
| Reset to default | `onResetMinMaxToDefault()` | button | Resets the three fields above to `originalIndicatorMin/Max/Step`. |

## `editParamPopup.html` — single parameter editor

| Control | Config key (ng-model) | Type | Notes |
|---|---|---|---|
| Generation mode | `selectedParam.generation` | button-group (2 buttons) | Values: `generationTypes.random` ("Randomly generated") / `generationTypes.fixed` ("Fixed value"). Disabled when `selectedParam.type == 'string'`. |
| Minimum source (numeric params) | `selectedParam.minValue` | button-group "Global"/"Custom" + spinner | "Global" sets `minValue = genMinValue`; "Custom" sets `selectedParam.customMinValue = true` and reveals a spinner (`min/max/step` bound to `originalMinValue/originalMaxValue/originalStep`). Only for `type in ('int','double')` and not `isCombo`, and only while `generation != fixed`. |
| Maximum source (numeric params) | `selectedParam.maxValue` | button-group "Global"/"Custom" + spinner | Same pattern as Minimum, mirrored. |
| Step (numeric params) | `selectedParam.step` | number spinner | step 1. |
| Available options (combo params) | `option.checked` per `selectedParam.options` | checkbox list | Shown when `selectedParam.isCombo && type != 'boolean'`. "All available charts" checkbox (`selectedParam.allCharts`) appears for the `#Chart#` / `paramType == 'data'` param and disables the individual option checkboxes. |
| Fixed value (string) | `selectedParam.fixedValue` | text input | Shown when `generation == fixed && type == 'string'`. |
| Fixed value (int/double) | `selectedParam.fixedValue` | number spinner | `min/max` bound to `selectedParam.minValue/maxValue`, `step` to `selectedParam.step`. |
| Fixed value (combo/boolean) | `selectedParam.fixedValue` | `<select>` | `ng-options="item.value as item.name for item in selectedParam.options"`. |

`generationTypes` enum (`BlockConfigService.js`): `{ random: 'random', fixed: 'fixed' }`.

Help text in the popup notes: *"Global Minimum and Maximum can be configured in What to build →
Additional build config"* — see the global fallback table below.

## `editParamSetPopup.html` — parameter set editor

| Control | Config key (ng-model) | Type | Notes |
|---|---|---|---|
| Set name | `selectedParamSet.name` | text input | |
| Delete set | `removeParamSet()` | button | Shown only when `selectedParamSet.action == 'Edit'`. |
| Parameters configuration grid | `setParamsGridId` (`sqGrid`) | grid | Columns: Name, Type, Generation, Possible values. Double-click a row → reuses `editParamPopup` for that parameter. |

## Global fallback ranges (What to build → Additional build config → "# of Conditions, Periods")

Source: `SettingsWhatToBuild/views/settings/conditionsAndPeriods/conditionsAndPeriods.html`. Per chart
complexity (`config.complexities[$index]`, repeated when `config.useDifferentSettings` is on):

| Label | Config key (ng-model) | Type | Notes |
|---|---|---|---|
| Global Indicators period — Min | `complexity.minPeriod` | number spinner | min 2, step 1. `data-testid="conditions-min-period"`. |
| Global Indicators period — Max | `complexity.maxPeriod` | number spinner | min 2, step 1. `data-testid="conditions-max-period"`. |
| Global Lookback period (Shift) — Max | `complexity.maxShift` | number spinner | min 0, max 1000, step 1. (Min not exposed — shift starts at 0.) |
| Use different settings for every chart | `config.useDifferentSettings` | checkbox | Shown only when `config.complexities.length > 1`. |

These are the "global ranges" a standard block's Period/Shift default to (per `../parameter-ranges.md`
precedence: custom-block ranges > per-block Building-blocks ranges > these global What-to-build
ranges).

## Related

- Prose page: [../parameter-ranges.md](../parameter-ranges.md)
- Fields hub: [README.md](README.md)
- Custom blocks (also expose Min/Max/Step per parameter): [custom-blocks.md](custom-blocks.md)
- Auto-computing indicator ranges: [indicators-calibration.md](indicators-calibration.md)
