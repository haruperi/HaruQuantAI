# Ranking — field reference (for UI tests)

> Exact controls, `ng-model` bindings, defaults and `data-testid`s for the Ranking (Ranking & Filtering) settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsRankings/` (`views/ranking.html`, `RankingCtrl.js`, `RankingService.js`, and the `FitnessFunction/` sub-component). Tab registered as `SettingsTab` id 70, `testId: settings-tab-ranking`, `configElemName: Rankings`, tasks: `Build, Retest, Optimize, AutomaticRetest, NeuralNetworkTrainer`. Tab title is "Ranking & Filtering" for Build/Retest, otherwise "Ranking".

Visibility flags (set in `RankingCtrl.init`): `showMaxStrategies` = task ≠ Retest/AutomaticRetest; `showConditions` = task ∈ {Build, Retest, AutomaticRetest}; `showWFConditions` = task == Optimize. Many rows below appear only for specific task/optimization types (noted per row). All values persist under the `Rankings` element.

## Maximum top strategies to store (fieldset, only when `showMaxStrategies`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Maximum strategies/optimizations to store in databank | `config.maxStrategies` | number spinner | 500 | min 0, max 1000000, step 1, `updateOn: blur`. `data-testid="settings-ranking-max-strategies"`. Node `MaxStrategies`. |
| Don't save original strategy test | `config.wfDontSaveOriginalStr` | checkbox | `false` | id `wf-dont-save-original-str`, `data-testid="settings-ranking-wf-keep-original"`. Shown only when `showWFConditions`. Node `WalkForward/DontSaveOriginalStr`. |
| Don't save FAILED WF strategy | `config.wfDeleteFailedStr` | checkbox | `false` | id `wf-delete-failed-str`, `data-testid="settings-ranking-wf-delete-failed"`. Shown for WF optimization types. Node `WalkForward/DeleteFailedStr`. |

### Stop generation when (radio group `StopGenerationRadio`, hidden when `showWFConditions`)

Bound to `config.stopCondition.type`. Enum `buildStopConditionTypes`: `never="never"`, `passedCount="passed-count"`, `databankFull="databank-full"`, `timeLimit="time-limit"` (default `never`). Persisted as `StopCondition[type]` + attrs.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Never | `config.stopCondition.type` = `never` | radio | selected (default) | container `data-testid="settings-ranking-stop-never-select"` |
| Totally … strategies (that passed filters) were generated | `config.stopCondition.type` = `passedCount` | radio | — | container `data-testid="settings-ranking-stop-totally-select"` |
| ↳ passed strategies count | `config.stopCondition.passedStrategies` | number spinner | 1000 | min 1, max 1000000, step 1. `data-testid="settings-ranking-stop-totally-count"`. Enabled only when type = passedCount. |
| Databank is full (reached maximum capacity) | `config.stopCondition.type` = `databankFull` | radio | — | container `data-testid="settings-ranking-stop-databank-full-select"` |
| After … days/hours/minutes | `config.stopCondition.type` = `timeLimit` | radio | — | container `data-testid="settings-ranking-stop-time-limit-select"` |
| ↳ days | `config.stopCondition.days` | number spinner | 0 | min 0, step 1. `data-testid="settings-ranking-stop-days"` |
| ↳ hours | `config.stopCondition.hours` | number spinner | 0 | min 0, step 1, max 23. `data-testid="settings-ranking-stop-hours"` |
| ↳ minutes | `config.stopCondition.minutes` | number spinner | 0 | min 0, step 1, max 59. `data-testid="settings-ranking-stop-minutes"` |

> Also persisted on `StopCondition`: `restartCount` (default 5) — no control in this template.

## Strategy Quality ranking (fitness) — `<fitness-function>` sub-component

Template `FitnessFunction/fitnessFunction.html` (directive `fitnessFunction`, `FitnessFunctionCtrl`). Persisted as `Rankings/FitnessCriteria[method]` + `<Settings>`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Strategy Quality ranking — Use | `selectedMethod` → `fitness.method` | `<select>` | — (from loaded config) | Options: `method.value as method.name for method in methods`, where `methods = InitializationData().settings.Rankings.fitnessMethods` (backend-supplied ranking types, e.g. Net profit, SQN, Return/DD, custom). For Optimize, crosscheck-based methods are filtered out. Selecting a crosscheck method requires that cross check enabled. |
| Compute from | (per-method sub-template `ng-include`) | dynamic | — | Renders the `FitnessMethod` plugin template for the selected method (`ComputeFromStrategyResult`, `RetestOnAdditionalMarkets`, `MonteCarloRetest`, `MonteCarloManipulation`, …). Fields are method-specific and defined by each fitness-method plugin, not this tab. |

## Custom analysis (fieldset)

Persisted as `Rankings/CustomAnalysis[method|inputArgs|filter]`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Use | `config.caMethod` | `<select>` | `"none"` | Options `item.value as item.name for item in config.caAvailableMethods` — built from `InitializationData().settings.CustomAnalysis.methods` (only method types 20 and 30), plus a leading "None" (`value: "none"`). |
| Input args | `config.caInputArgs` | text | `""` | free text |
| Filter by results of custom analysis | `config.caFilter` | checkbox | `false` | id `ca-ranking-filter`, `data-testid="settings-ranking-ca-filter"` |

## Strategy filtering conditions (fieldset, only when `showConditions`)

Persisted under `Rankings` (`Conditions`, `DeleteFailedStrategies`, `ForceRunCrossChecks`, `DismissTooSimilarStrategies`, `AutomaticDismissal`).

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Delete FAILED strategies from databank | `config.deleteFailedStrategies` | checkbox | `false` | id `retest-delete-failed-str`, `data-testid="settings-ranking-delete-failed"`. Shown only for Retest/AutomaticRetest. |
| Automatic filters (configure gear) | `printAutomaticDismissalLabel()` + `onConfigureAutoDismissal()` | label + gear link | — | Shown for Build/Retest/AutomaticRetest. Gear opens `#autoDismissalPopup`; per-problem `strategyProblems[].dismiss` (default all `true`) + `autoFiltersWarning` (default `false`). |
| Dismiss similar strategies in databank (default, recommended) | `config.dismissTooSimilarStrategies` | checkbox | `true` | id `dismiss-too-similar-strategies`, `data-testid="settings-ranking-dismiss-similar"`. Shown only for Build. |
| Custom filters (conditions grid) | `config.condGridInstance` | `<conditions-grid>` | — | `custom-id="ranking-conditions"`, default sampleType In, general + WF-special columns. Persisted as `Conditions`. |
| Run crosschecks independently from Custom filters failure | `config.forceRunCrossChecks` | checkbox | `false` | id `ranking-run-crosschecks`, `data-testid="settings-ranking-run-crosschecks"`. Shown only for Retest/AutomaticRetest. |

## Fit to existing portfolio filter (fieldset, only when task == Build)

Persisted as `Rankings/FitPortfolio` + `Correlation`.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Existing portfolio databank | `config.fitPortfolio.databank` | `<select>` | `gedatabanks.existingPortfolio` | `data-testid="settings-ranking-fit-databank-select"`. Options `item.name for item in fitPortfolioDatabanks`. Shown only when `!isBuilder`. |
| Filter out strategies with correlation > … | `config.fitPortfolio.active` | checkbox | `false` | id `fit-portfolio-active`, `data-testid="settings-ranking-fit-active"`. |
| ↳ correlation config (gear) | `printFitPortfolioCorrelation()` + `onConfigureFitPortfolioCorrelation()` | label + gear link | — | Opens `#fitPortfolioCorrelationPopup`. Correlation defaults: `max` 0.3, `type` `ProfitLoss`, `period` 10, `allowNegative` true (config default; XML load default false), `addEmptyPeriods` false. |

## Walk-Forward / Optimize filter (right column, only when task == Optimize)

Enum `optimizations`: `simple=1`, `walk_fo=2`, `walk_fm=3`, `sequential=4`. Enum `simpleOptimizations`: `storeBest=10`, `storeAll=5`. `config.optimizationType` default `simple`; `config.simpleOptimizationType` default `storeBest`. WF conditions persisted under `Rankings/WalkForward/Conditions` with attributes.

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Set recommended WF conditions | `onLoadDefaultWFConditions()` | link | — | Shown for walk_fm / walk_fo. Loads backend default WF conditions (Replace/Add). |
| Robustness score must be > … % to pass | `config.thresholdPct` | number spinner | 80 | min 0, max 100, step 1. Shown for walk_fo (and used by walk_fm). Attr `thresholdPct`. |
| WF Matrix: area of … rows | `config.wfRobRows` | `<select>` | 3 | Options `wfRows = [2,3,4,5]`. walk_fm only. Attr `robCombRows`. |
| WF Matrix: … columns | `config.wfRobCols` | `<select>` | 3 | Options `wfColumns = [2,3,4,5]`. walk_fm only. Attr `robCombCols`. |
| WF Matrix: where at least … results | `config.wfRobComb` | `<select>` | 7 | Options `wfCombinations = [0..25]`. walk_fm only. Attr `robMinComb`. |
| WF custom filters (conditions grid) | `config.wfCondGridInstance` | `<conditions-grid>` | — | `custom-id="ranking-conditions-wf"`. Persisted as `WalkForward/Conditions`. |

## Related

- Prose page: [../ranking.md](../ranking.md)
- Fields hub: [README.md](README.md)
