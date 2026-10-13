# Task settings XML - per-type reference

Each task's settings document (`<TaskType>-Task<N>.xml` inside `project.cfx`) has root
`<Settings>` (no attributes); its children are the sections owned by settings plugins
(`ISettingTabPlugin.getSettingName()`). Sections most tasks share: [shared-sections.md](shared-sections.md).

Starting points (copy -> edit, never from memory): `internal/plugins/Task<Type>/task.xml` (plugin
defaults, root `<Task><Settings>...`, take the `<Settings>` subtree; Build ships
`task_forex.xml` / `task_futures.xml` / `task_stockpicker.xml` instead, task_forex.xml ~14k lines =
the complete catalog of blocks and cross-checks) and entries inside `user/projects/*/project.cfx`.

No MonteCarlo or WalkForward task exists: both are cross-checks inside `<CrossChecks>`
([shared-sections.md](shared-sections.md#crosschecks--robustness-tests)); Walk-Forward is also an
`<Optimization>` mode ([optimize.md](optimize.md)).

## Registry

| `type=` | Page | Sections read |
|---|---|---|
| `Build` | [build.md](build.md) | Data, Notes, RiskMoneyManagement, Rankings, Options, CrossChecks, Blocks, WhatToBuild, PartsToImprove, ATMs |
| `Retest` | [retest.md](retest.md) | Data, Notes, RiskMoneyManagement, Rankings, Options, CrossChecks, Databanks, ATMs |
| `Optimize` | [optimize.md](optimize.md) | Data, Options, Notes, RiskMoneyManagement, Rankings, Optimization, ATMs |
| `AutomaticRetest` | [automatic-retest.md](automatic-retest.md) | Databanks, CustomData, RiskMoneyManagement, Options, CrossChecks, Rankings, ATMs |
| `Filtering` | [filtering.md](filtering.md) | Filtering + Databanks (Source/Target) |
| `ClearDatabanks` | [clear-databanks.md](clear-databanks.md) | ClearDatabanks |
| `GoToTask` | [go-to-task.md](go-to-task.md) | GoToTask |
| `StopAndStart` | [stop-and-start.md](stop-and-start.md) | StopAndStart |
| `CallExternalScript` | [call-external-script.md](call-external-script.md) | CallExternalScript |
| `LogDatabankStats` | [log-databank-stats.md](log-databank-stats.md) | LogDatabankStats |
| `SaveToFiles` | [save-to-files.md](save-to-files.md) | SaveToFiles |
| `LoadFromFiles` | [load-from-files.md](load-from-files.md) | LoadFromFiles |
| `CreatePortfolio` | [create-portfolio.md](create-portfolio.md) | CreatePortfolio + Input/Output |
| `DeleteFile` | [delete-file.md](delete-file.md) | DeleteFile |
| `WaitFor` | [wait-for.md](wait-for.md) | WaitFor |
| `UpdateData` | [update-data.md](update-data.md) | UpdateData |
| `Notification` | [notification.md](notification.md) | Notification |
| `CustomAnalysis` | [custom-analysis.md](custom-analysis.md) | CustomAnalysis, Databanks |
| `ApplyMassConfig` | [apply-mass-config.md](apply-mass-config.md) | ApplyMassConfig |
| `AutomaticPortfolioBuilder` | [automatic-portfolio-builder.md](automatic-portfolio-builder.md) | AutomaticPortfolioBuilder, Databanks |
| `NeuralNetworkTrainer` | [neural-network-trainer.md](neural-network-trainer.md) | Data, Options, Rankings, Notes |

## Gotchas (every task)

1. Inside project.cfx the root is `<Settings>`; plugin defaults / exported templates wrap it in `<Task type=...>`: unwrap when copying.
2. Most parsers auto-inject missing optional elements (`fixSettings`), but each page lists hard requirements.
3. Booleans are element text (`<X>true</X>`) or attributes (`use=`, `dismiss=`, `status=`), not interchangeable; mirror the examples.
4. Always keep a `<Databanks>` section (SQX injects the default if missing and rewrites the file).
5. Comparators XML-escaped (`&gt;`, `&gt;=`, ...); malformed `<Condition>`s are silently dropped.
