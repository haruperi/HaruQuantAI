# CustomProjects: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppTaskManager.jar](AppTaskManager.md) | 2 | `com.strategyquant.plugin.App.impl.TaskManager` |
| [ServletProject.jar](ServletProject.md) | 13 | `com.strategyquant.plugin.Servlet.impl.Project` |
| [TaskApplyMassConfig.jar](TaskApplyMassConfig.md) | 1 | `com.strategyquant.plugin.Task.impl.ApplyMassConfig` |
| [TaskCallExternalScript.jar](TaskCallExternalScript.md) | 2 | `com.strategyquant.plugin.Task.impl.CallExternalScript` |
| [TaskClearDatabanks.jar](TaskClearDatabanks.md) | 1 | `com.strategyquant.plugin.Task.impl.ClearDatabanks` |
| [TaskCreatePortfolio.jar](TaskCreatePortfolio.md) | 1 | `com.strategyquant.plugin.Task.impl.CreatePortfolio` |
| [TaskCustomAnalysis.jar](TaskCustomAnalysis.md) | 1 | `com.strategyquant.plugin.Task.impl.CustomAnalysis` |
| [TaskDeleteFile.jar](TaskDeleteFile.md) | 1 | `com.strategyquant.plugin.Task.impl.DeleteFile` |
| [TaskFiltering.jar](TaskFiltering.md) | 1 | `com.strategyquant.plugin.Task.impl.Filtering` |
| [TaskGoToTask.jar](TaskGoToTask.md) | 1 | `com.strategyquant.plugin.Task.impl.GoToTask` |
| [TaskLoadFromFiles.jar](TaskLoadFromFiles.md) | 1 | `com.strategyquant.plugin.Task.impl.LoadFromFiles` |
| [TaskLogDatabankStats.jar](TaskLogDatabankStats.md) | 1 | `com.strategyquant.plugin.Task.impl.LogDatabankStats` |
| [TaskManagerProjects.jar](TaskManagerProjects.md) | 2 | `com.strategyquant.plugin.TaskManager.impl.Projects` |
| [TaskNotification.jar](TaskNotification.md) | 1 | `com.strategyquant.plugin.Task.impl.Notification` |
| [TaskSaveToFiles.jar](TaskSaveToFiles.md) | 1 | `com.strategyquant.plugin.Task.impl.SaveToFiles` |
| [TaskStopAndStart.jar](TaskStopAndStart.md) | 1 | `com.strategyquant.plugin.Task.impl.StopAndStart` |
| [TaskUpdateData.jar](TaskUpdateData.md) | 2 | `com.strategyquant.plugin.Task.impl.UpdateData` |
| [TaskWaitFor.jar](TaskWaitFor.md) | 2 | `com.strategyquant.plugin.Task.impl.WaitFor` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppTaskManager/module.js`: title `Custom Projects`, app code `TASKMANAGER`, hidden registration `False`. SHA-256 `6468bc1d7354a4129047e7240493c71a0e928ec2c8e304f3766878ed3919cc89`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQDataLib.jar](../Shared/SQDataLib.md) - `Shared`.
- [SQPluginLib.jar](../Shared/SQPluginLib.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Shared task engines

Other workspaces canonically document engines relevant to custom-project research. The following are planning cross-links; exact runtime task registration/availability needs further tracing.

- [Generation](../Builder/TaskBuild.md)
- [Retesting](../Retester/TaskRetest.md)
- [Automatic retesting](../Retester/TaskAutomaticRetest.md)
- [Optimization](../Optimizer/TaskOptimize.md)
- [Portfolio construction](../PortfolioMaster/TaskAutomaticPortfolioBuilder.md)

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
