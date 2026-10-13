# Genetic options — field reference (for UI tests)

> Exact controls, `ng-model` bindings and defaults for the Genetic options settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsGeneticOptions/` (`views/geneticOptions.html`, `SettingsGeneticOptionsCtrl.js`, `SettingsGeneticOptionsService.js`, `module.js`). Tab is registered as `SettingsTab` id 7, `testId: settings-tab-genetic`, `configElemName: WhatToBuild`, task: `Build` only — shown only when `WhatToBuild > BuildMode` has `generationType` = genetic evolution (visibility toggled by `checkIPSettings()` via the `SETTINGS_TAB_SHOW` event, tab key `genetic-options`).

All controls live under the config object `SettingsGeneticOptionsService.config`, bound in the controller as `$scope.config`. Persisted to XML under `WhatToBuild/BuildMode` (see "XML notes" column) — `saveSettings()` fully rebuilds this element on every change.

## Genetic options (fieldset)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Max # of Generations | `config.maxGenerations` | number spinner (`sqn-spinner`) | 10 | min 1, max 100000, step 10. `data-testid="settings-genetic-max-generations"` |
| Population Size (per island) | `config.populationSize` | number spinner | 5 | min 5, max 50000, step 10. `data-testid="settings-genetic-population-size"` |
| Crossover Probability | `config.crossoverProbability` | slider (`sq-slider`), `%` postfix | 50 | min 0, max 100, step 1, width 200. `data-testid="settings-genetic-crossover"` |
| Mutation Probability | `config.mutationProbability` | slider, `%` postfix | 20 | min 0, max 100, step 1, width 200. No `data-testid`. |

## Islands options (fieldset)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Islands (separate evolution) | `config.islands` | number spinner | 10 | min 1, max 100, step 1. `data-testid="settings-genetic-islands"` |
| Migrate every Xth generation, X = | `config.migrationModulo` | slider | 50 | min 3, max 100, step 1, width 150. No `data-testid`. |
| Population migration rate | `config.migrationRate` | slider, `%` postfix | 20 | min 0, max 20, step 1, width 150. No `data-testid`. |

## Initial population generation (fieldset)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Initial population size required (info line, not editable) | — (`{{config.populationSize * config.islands}}`) | computed display text | — | Not a control — read-only label showing `populationSize × islands`. |
| Use strategies from Initial population databank as evolution start | `config.initGenerationType` | checkbox | `1` (unchecked) | `ng-true-value="2"`, `ng-false-value="1"`. `data-testid="settings-genetic-init-from-databank"`. Help text: "Note - initial strategies from databank are not filtered." / "If not used or not enough, the rest will be generated." |
| Generated decimation coefficient | `config.decimationCoef` | slider (`value-align="right"`) | 1 | min 1, max 10, step 1, width 165. No `data-testid`. |

## Filter generated initial population (fieldset)

| Label | Config key | Type | Default | Options / notes |
|---|---|---|---|---|
| (conditions grid) | `config.condGridInstance` | `<conditions-grid>` component | — | `id="filter-grid"`, `custom-id="genetic-options-conditions"`, `after-init="afterCGInit"`, `on-refresh="onCGChange"`. Only strategies fulfilling these conditions are accepted into the randomly generated initial population. Grid is initialized with `sampleType = In` and populated with general databank columns (`SQConstants.getColumnsByType`); persisted as an XML `Conditions` child element, not a simple field — a UI test should treat it as its own widget (see the shared conditions-grid component, not documented per-field here). |

## "Fresh blood" (fieldset)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Detect same strategies in population and replace them with newly generated ones | `config.freshBloodReplaceSimilar` | checkbox | `true` | `data-testid="settings-genetic-fresh-similar"` |
| Replace **[select]**% of weakest strategies with newly generated every **[spinner]** generation(s) | `config.freshBloodReplaceWeakest` | checkbox | `true` | `data-testid="settings-genetic-fresh-weakest"`. Contains two nested inline controls (see next two rows), both only meaningful when this checkbox is on. |
| ↳ nested: weakest % select | `config.freshBloodWeakestPct` | `<select>` (`ng-options="value as value for value in [...]"`) | 10 | Options: `5, 10, 15, 20, 25, 30`. No separate `data-testid`. |
| ↳ nested: generations spinner | `config.freshBloodWeakestGenerations` | number spinner | 2 | min 1, max 500, step 1. No `data-testid`. |
| Show last generation databank - for island #1 only | `config.showLastGenerationDatabank` | checkbox | `false` | `data-testid="settings-genetic-show-last-gen"` |

## Evolution management (fieldset)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Start again when finished (continuous repeating evolution) | `config.evoRestartOnFinish` | checkbox | `true` | `data-testid="settings-genetic-restart-finish"`. Saved as `EvoRestartOnFinish[status]` attribute. |
| Restart evolution if fitness of **[select]** stagnates for **[spinner]** generation(s) | `config.evoRestartOnStagnation` | checkbox | `true` | `data-testid="settings-genetic-restart-stagnation"`. Saved as `EvoRestartOnStagnation[status]` attribute. Contains two nested inline controls (see next two rows), both only meaningful when this checkbox is on. |
| ↳ nested: fitness-sample select | `config.evoFitnessRestartType` | `<select>` (`ng-options="item.value as item.name for item in evoFitnessRestartTypes"`) | `sampleTypes.in` | Options (from `SettingsGeneticOptionsService.evoFitnessRestartTypes`): "In sample (whole)" = `sampleTypes.in`, "In sample (Training)" = `sampleTypes.ist`, "In sample (Validation)" = `sampleTypes.isv`. Displayed span text comes from `$scope.printEvoFitnessRestartType()`. No `data-testid`. Saved as `EvoRestartOnStagnation[fitnessType]` attribute. |
| ↳ nested: stagnation-generations spinner | `config.evoStagnationGenerations` | number spinner | 30 | min 3, max 500, step 1. No `data-testid`. Saved as `EvoRestartOnStagnation[generations]` attribute. |

## Config keys present in the service but not rendered in this template

These are read/written by `SettingsGeneticOptionsService` (so they round-trip through the XML) but have **no control** in `geneticOptions.html` — likely legacy, set elsewhere, or reserved:

| Config key | Default | XML location | Notes |
|---|---|---|---|
| `config.generationType` | — | `BuildMode[generationType]` attribute | Set on the **What to build** tab (build mode: random vs. genetic evolution); this tab only reads it to decide visibility. |
| `config.showAdvancedSettings` | `false` | `ShowAdvancedGeneticSettings` node | No visible toggle in the current template. |
| `config.evoTrainingValidationRatio` | 50 | `EvoInSamplePeriod[ratio]` attribute | No visible control in the current template. |

## Related

- Prose page: [../genetic-options.md](../genetic-options.md)
- Fields hub: [README.md](README.md)
