# What to build — field reference (for UI tests)

> Exact controls, `ng-model` bindings, defaults and `data-testid`s for the What to build settings tab and its "Additional build config" popups, extracted from the web plugin source.

Source: `internal/plugins/SettingsWhatToBuild/` (`views/whatToBuild.html`, `WhatToBuildCtrl.js`, `WhatToBuildService.js`, plus the sub-plugins under `views/settings/*` and the shared `views/additionalConfigPopup.html`). Tab registered as `SettingsTab` id 5, `testId: settings-tab-wtb`, `configElemName: WhatToBuild`, task: `Build` only.

The tab has two parts: (1) the **main body** (strategy type, output/improve databank) directly in `whatToBuild.html`, and (2) an **"Additional build config"** area listing sub-settings, each opened via a gear icon (`data-testid="build-config-gear-<name>"`) into the shared `#additionalConfigPopup` modal (`data-testid="additional-config-popup"`; Save button `data-testid="additional-config-save-btn"`). Each sub-setting is its own registered `WhatToBuildSettings` plugin with its own template — documented per section below.

## Main body — Output databank (only when NOT the standalone Builder, `ng-if="!isBuilder"`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Output databank | `config.outputDatabank` | `<select>` | `gedatabanks.results` (from `DatabankService.getTaskOutputDatabank()`) | `data-testid="settings-wtb-output-databank-select"`. Options: `item.name for item in databanks` (visible databanks). |

## Main body — Strategy type (radio group `StrategyTypeRadio`)

Enum `buildStrategyTypes`: `simple="simple"`, `multiTf="multi-tf"`, `template="template"`, `improve="improve"`. Bound to `config.strategyType` (default `simple`). Persisted as `StrategyType[type]`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Simple strategy [default] | `config.strategyType` = `strategyTypes.simple` | radio | selected (default) | — |
| Multi-TF or multi-symbol strategy | `config.strategyType` = `strategyTypes.multiTf` | radio | — | label `data-testid="settings-wtb-multitf-radio-label"` |
| ↳ additional charts | `config.additionalCharts` | number spinner | 1 | min 1, max 9, step 1. `data-testid="settings-wtb-additional-charts"`. Enabled only when strategyType = multiTf. |
| Strategy from template | `config.strategyType` = `strategyTypes.template` | radio | — | — |
| ↳ template file | `config.templateFile` | `<sq-combo-input>` (readonly, single) + Browse / Reload links | `''` | Browse opens file picker (`sqx,sq4`); Reload re-loads. |
| Improve existing strategy | `config.strategyType` = `strategyTypes.improve` | radio | — | container `data-testid="settings-wtb-strategy-type-improve"`. Disabled when data engine is `Stockpicker` or `Single-asset cloud strategy`. |

### Improve sub-options (shown only when strategyType = improve; radio group `ImproveStrategyRadio` → `config.improveType`)

Enum `buildImproveTypes`: `strategy="strategy"`, `databank="databank"` (default `strategy`). Persisted as `StrategyType[improveType]`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Select strategy file | `config.improveType` = `improveTypes.strategy` | radio | selected (default) | — |
| ↳ strategy file | `config.strategyFile` | `<sq-combo-input>` + Browse | `''` | Browse `data-testid="settings-wtb-browse-btn"`; picker ext `sqx,sq4,sqw,str`. |
| Improve all strategies in databank | `config.improveType` = `improveTypes.databank` | radio | — | radio `data-testid="settings-wtb-improve-source-databank"`; container `data-testid="settings-wtb-improve-all"` |
| ↳ improve databank | `config.improveDatabank` | `<select>` | `gedatabanks.strategiesToImprove` (Builder) / `gedatabanks.results` (Manager) | `data-testid="settings-wtb-improve-databank-select"`. Options `item.name for item in databanks`. |

## Additional build config — Build mode (sub-plugin `buildMode`, position 30)

Template `views/settings/buildMode/buildMode.html`. Radio group `GenerationTypeRadio` → `config.generationType`. Enum `buildGenerationTypes`: `geneticEvolution="genetic-evolution"`, `randomGeneration="random-generation"`. Reset default: `randomGeneration`. Persisted as `WhatToBuild/BuildMode[generationType]`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Genetic evolution | `config.generationType` = `generationTypes.geneticEvolution` | radio | — | container `data-testid="build-mode-genetic-evolution"`. Enables the [Genetic options](genetic-options.md) tab. |
| Random generation | `config.generationType` = `generationTypes.randomGeneration` | radio | selected (reset default) | container `data-testid="build-mode-random-generation"` |

## Additional build config — Trading directions (sub-plugin `tradingDirections`, position 10)

Template `views/settings/tradingDirections/tradingDirections.html`. Radio group `DirectionRadio` → `config.type`. Enum `buildStrategyDirections`: `both="both"`, `long="long"`, `short="short"`. Persisted as `MarketSides[type]` + `EntrySymmetry`/`ExitSymmetry` nodes. Hidden when strategyType = template.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Both (Long and Short) | `config.type` = `both` | radio | selected (default) | container `data-testid="trading-direction-both"` |
| Only Long | `config.type` = `long` | radio | — | container `data-testid="trading-direction-long"` |
| Only Short | `config.type` = `short` | radio | — | container `data-testid="trading-direction-short"` |
| Entry Symmetry | `config.entrySymmetry` | checkbox | `true` | id `config.entrySymmetry`. Enabled only when type = both. |
| Exit Symmetry | `config.exitSymmetry` | checkbox | `true` | id `config.exitSymmetry`. Enabled only when type = both. |

## Additional build config — Strategy style (sub-plugin `strategyArchitecture`, position 20, "Strategy style")

Template `views/settings/strategyArchitecture/strategyArchitecture.html`. Radio group `DirectionRadio` → `config.type`. Enum `strategyArchitectures`: `sq4="sq4"`, `sq4Fuzzy="sq4fuzzy"`, `sq3="sq3"`. Persisted as `StrategyType[architecture]` (+ `minTrue`/`maxTrue` when fuzzy). This setting is disabled/labelled "Stockpicker style" for Stockpicker engines.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| SQX Signals Style | `config.type` = `sq4` | radio | selected (reset default) | — |
| SQX Signals Style with Fuzzy Logic | `config.type` = `sq4Fuzzy` | radio | — | — |
| ↳ Min (% of true conditions) | `config.minTrue` | number spinner | 70 | min 5, max 95, step 1. Enabled only when type = sq4Fuzzy. |
| ↳ Max (% of true conditions) | `config.maxTrue` | number spinner | 70 | min 5, max 95, step 1. Validation: min ≤ max. |
| Old SQ3 Style | `config.type` = `sq3` | radio | — | — |

## Additional build config — # of Conditions, Periods (sub-plugin `conditionsAndPeriods`, position 30)

Template `views/settings/conditionsAndPeriods/conditionsAndPeriods.html`. Repeats over `config.complexities` (one block per chart; extra blocks only shown when `config.useDifferentSettings`). Values are stored per chart via `ComplexitiesService` (persisted under `Data` / `RulesComplexity/Chart` attributes, not under WhatToBuild). Defaults below are from `ComplexitiesService.resetComplexity()` (the popup "Reset to default"). Note `correctComplexities()` fills different fallbacks (maxConditions 2, minPeriod 15) when values are absent on load.

| Label | Config key (ng-model) | Type | Default (reset) | Options / notes |
|---|---|---|---|---|
| Conditions in entry rule — Min | `complexity.minConditions` | number spinner | 1 | min 0, max 30, step 1 |
| Conditions in entry rule — Max | `complexity.maxConditions` | number spinner | 4 | min 0, max 30, step 1 |
| Conditions in exit rule — Min | `complexity.minExitConditions` | number spinner | 1 | min 0, max 30, step 1 |
| Conditions in exit rule — Max | `complexity.maxExitConditions` | number spinner | 4 | min 0, max 30, step 1 |
| Global Indicators period — Min | `complexity.minPeriod` | number spinner | 2 | min 2, step 1. `data-testid="conditions-min-period"` |
| Global Indicators period — Max | `complexity.maxPeriod` | number spinner | 100 | min 2, step 1. `data-testid="conditions-max-period"` |
| Global Lookback period (Shift) — Max | `complexity.maxShift` | number spinner | `minShift + 2` (minShift 1, or 0 for Tradestation/MultiCharts) | min 0, max 1000, step 1. Warning shown when > 10. |
| Number of Exit Types — Max (main chart only, `$index==0`) | `complexity.maxExitTypes` | number spinner | 5 | min 0, max 30, step 1. (`minExitTypes` default 1 is not exposed; its Min spinner is commented out in template.) |
| Use different settings for every chart | `config.useDifferentSettings` | checkbox | `true` | id `useDifferentSettings`. Shown only when more than one chart. |

## Additional build config — Stop Loss (sub-plugin `stopLoss`, position 40)

Template `views/settings/stopLoss/stopLoss.html`. Persisted under `SLPTOptions` (SL* nodes). Defaults from `StopLossService.resetSettings()`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Stop loss is required | `config.required` | checkbox | `true` | id `slRequired`, container `data-testid="sl-required-checkbox"` |
| Fixed pips | `config.fixedPips` | checkbox | `true` | id `fixedPips` |
| ↳ Fixed pips — Min | `config.minPips` | number spinner | 1 | min 0, step 1 |
| ↳ Fixed pips — Max | `config.maxPips` | number spinner | 10 | min 0, step 1 |
| Percent | `config.percent` | checkbox | `true` | id `percent` |
| ↳ Percent — Min | `config.minPercent` | number spinner | 1 | min 0, step 1 |
| ↳ Percent — Max | `config.maxPercent` | number spinner | 10 | min 0, step 1 |
| ATR-based | `config.atrBased` | checkbox | `true` | id `atrBased` |
| ↳ ATR Multiple — Min | `config.minATRMultiple` | number spinner | 2 | min 0.1, max 100, step 0.1 |
| ↳ ATR Multiple — Max | `config.maxATRMultiple` | number spinner | 5 | min 0.1, max 1000, step 0.1 |
| ↳ ATR Period — Min | `config.minATRPeriod` | number spinner | 20 | min 2, max 1000, step 1 |
| ↳ ATR Period — Max | `config.maxATRPeriod` | number spinner | 30 | min 2, max 1000, step 1 |
| Use indicator levels | `config.indicatorBased` | checkbox | `false` | id `indyLevelBased` |

## Additional build config — Profit Target (sub-plugin `profitTarget`, position 50)

Template `views/settings/profitTarget/profitTarget.html`. Persisted under `SLPTOptions` (PT* nodes). Defaults from `ProfitTargetService.resetSettings()`. When "Use same ranges as SL" is on, the size fields bind to a mirror `guiConfig.*` and are disabled.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Profit target is required | `config.required` | checkbox | `true` | id `ptRequired`, container `data-testid="pt-required-checkbox"` |
| Use same ranges as for Stop loss | `config.sameAsSL` | checkbox | `false` | id `sameRanges`. Persisted inverted as `SeparatedSettings`. When on, disables all size fields below. |
| Fixed pips | `guiConfig.fixedPips` | checkbox | mirrors SL / `true` | id `fixedPips`, disabled when sameAsSL |
| ↳ Fixed pips — Min / Max | `guiConfig.minPips` / `guiConfig.maxPips` | number spinner | 1 / 10 | min 0, step 1 |
| Percent | `guiConfig.percent` | checkbox | `true` | id `percent`, disabled when sameAsSL |
| ↳ Percent — Min / Max | `guiConfig.minPercent` / `guiConfig.maxPercent` | number spinner | 1 / 10 | min 0, step 1 |
| ATR-based | `guiConfig.atrBased` | checkbox | `true` | id `atrBased`, disabled when sameAsSL |
| ↳ ATR Multiple — Min / Max | `guiConfig.minATRMultiple` / `guiConfig.maxATRMultiple` | number spinner | 2 / 5 | min 0.1, max 100 / 1000, step 0.1 |
| ↳ ATR Period — Min / Max | `guiConfig.minATRPeriod` / `guiConfig.maxATRPeriod` | number spinner | 20 / 30 | min 2, max 1000, step 1 |
| Use indicator levels | `config.indicatorBased` | checkbox | `false` | id `indyLevelBased` |
| Limit Risk-Reward (SL vs PT) ratio — Yes, Profit Target will be from | `config.limitRRRatio` | checkbox | `false` | id `limitRRRatio` |
| ↳ RR ratio from (%) | `config.rrRatioFrom` | number spinner | 50 | min 10, max 1000, step 10. Validation: from ≤ to. |
| ↳ RR ratio to (% of Stop loss size) | `config.rrRatioTo` | number spinner | 80 | min 10, max 1000, step 10 |

## Related

- Prose page: [../what-to-build.md](../what-to-build.md)
- Fields hub: [README.md](README.md)
