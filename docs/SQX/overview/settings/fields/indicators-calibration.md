# Indicators calibration — field reference (for UI tests)

> "Calibrate indicators" popup reachable from the Building blocks tab, plus the auto-calibrate-before-
> start checkbox next to it.

Source:
- `internal/plugins/TaskBuild/indicatorsCalibration/indicatorsCalibrationPopup.html` — the popup
  (`#indicatorsCalibrationPopup`).
- `internal/plugins/TaskBuild/indicatorsCalibration/IndicatorsCalibrationPopupCtrl.js` — controller,
  grid setup, defaults.
- `internal/web/app/directives/indicatorsCalibrationButton/indicatorsCalibrationButton.html` — the
  launcher button, used as `<indicators-calibration-button>` from `SettingsBlocks/views/blocks.html`
  (line 78).
- `internal/plugins/SettingsBlocks/views/blocks.html` (lines 77-83) — the "calibrate before start"
  checkbox that sits next to the button.
- `internal/plugins/TaskBuild/module.js` — registers `IndicatorsCalibrationPopupCtrl` as a popup window
  plugin (`sqPluginProvider.addPopupWindow(...)`).

## Launcher (Building blocks tab, `random-options` row)

| Control | Config key (ng-model) / handler | Type | Notes |
|---|---|---|---|
| Calibrate indicators (button) | `showCalibrationPopup()` | button (`<indicators-calibration-button>`) | id `buttonCalibrateIndicators-30a`. Hidden when `gui.isStockPicker`. |
| calibrate before start | `gui.autoCalibrateBeforeStart` | checkbox | `ng-change="onCalibrateBeforeStartChanged()"` → `BlocksService.saveConfig()`. Default `false`. Hidden when `gui.isStockPicker`. Persisted as `calibrateBeforeStart` XML attribute (forced `false` for Stockpicker on save). |

## `#indicatorsCalibrationPopup` — "Calibrate indicators"

| Label | Config key (ng-model) | Type | Default | Notes |
|---|---|---|---|---|
| Use current step values | `config.stepType` = `"default"` | radio (`name="BBMaxStepsRadio"`) | selected by default (`useCalibrationMaxSteps=false` → `"default"`) | Current per-block step values are kept. |
| Use maximum **[N]** steps | `config.stepType` = `"custom"` | radio + nested spinner | — | Nested spinner: `config.maxSteps`, `ng-change="onSubchartsChange()"`, min 10, step 10. Default `calibrationMaxSteps` = **50**. |
| Calibrate now | `onCalibrate()` | button | — | Disabled while `calibrating`. Runs `BuildTaskService.calibrate(symbols, timeframes, maxSteps, engine, …)` against the main setup + subcharts' symbols/timeframes; `maxSteps` is `-1` unless `stepType=="custom"`. |
| Indicator output range values grid | `indicatorRangesGrid` (`sqGrid`) | grid | — | Columns: Indicator (45%), Minimum (17%, spinner), Maximum (17%, spinner), Step (17%, spinner). Populated from `BlocksService.indicators` + `BlocksService.stopLimitBlocks`, filtered to `group in ('Indicators','Stop/Limit Price Ranges')` and `returnType in ('number','pricerange')`, deduped by trailing key segment (skips `Number`/`FixedPips`). Default min/max shown as **100 / 200** when a block has none set yet; default step = `(max-min)/10` rounded, or `(max-min)/maxSteps` when no natural step is found. |
| Close without saving | `data-dismiss="modal"` | link | — | |
| Save | `onSave()` | button | — | Writes `gui.useCalibrationMaxSteps = (stepType=='custom')`, `gui.calibrationMaxSteps`, then calls `BlocksService.calibrateBlocks(gridData, callback)` which pushes the grid's min/max/step back onto the corresponding building blocks. |

Loading indicator: `#calibration-loading-overlay` shown while `calibrating`; spinner
`#calibration-spinner` (`spinner-key="indy-calibration-spinner"`).

There is also a headless entry point, `$rootScope.calibrateBeforeStart(...)`, invoked by the Builder at
project start when `gui.autoCalibrateBeforeStart` is true (and not Stockpicker) — it runs the same
calibrate+save flow without opening the popup.

## Related

- Prose page: [../indicators-calibration.md](../indicators-calibration.md)
- Fields hub: [README.md](README.md)
- Parent panel: [../building-blocks.md](../building-blocks.md)
- Precedence of these ranges vs. per-block/custom ranges: [parameter-ranges.md](parameter-ranges.md)
