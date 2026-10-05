# Shared: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [SQDataLib.jar](SQDataLib.md) | 195 | `com.strategyquant.datalib`, `com.strategyquant.datalib.bartype`, `com.strategyquant.datalib.bartype.impl`; 23 additional packages |
| [SQGridLib2.jar](SQGridLib2.md) | 81 | `com.strategyquant.gridlib`, `com.strategyquant.gridlib.classLoader`, `com.strategyquant.gridlib.client`; 12 additional packages |
| [SQJobsLib.jar](SQJobsLib.md) | 11 | `com.strategyquant.jobslib`, `com.strategyquant.jobslib.databank` |
| [SQPluginLib.jar](SQPluginLib.md) | 18 | `com.strategyquant.pluginlib`, `com.strategyquant.pluginlib.annotations`, `com.strategyquant.pluginlib.program` |
| [SQTradingLib.jar](SQTradingLib.md) | 945 | `com.strategyquant.indicatorTester`, `com.strategyquant.tradinglib`, `com.strategyquant.tradinglib.applyMassConfig`; 123 additional packages |
| [SQWebGUILib.jar](SQWebGUILib.md) | 34 | `com.strategyquant.webguilib`, `com.strategyquant.webguilib.config`, `com.strategyquant.webguilib.init`; 4 additional packages |
| [SQWizardBusiness.jar](SQWizardBusiness.md) | 24 | `com.strategyquant.wizard.desktop`, `com.strategyquant.wizard.desktop.indicators`, `com.strategyquant.wizard.desktop.loader`; 3 additional packages |
| [ConnectionLiveTest.jar](ConnectionLiveTest.md) | 3 | `com.strategyquant.plugin.Connection.impl.LiveTest` |
| [ConnectionMT4.jar](ConnectionMT4.md) | 7 | `com.strategyquant.plugin.Connection.impl.MT4` |
| [ConnectionTest.jar](ConnectionTest.md) | 3 | `com.strategyquant.plugin.Connection.impl.Test` |
| [CrossCheckMonteCarloManipulation.jar](CrossCheckMonteCarloManipulation.md) | 2 | `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation` |
| [CrossCheckMonteCarloRetest.jar](CrossCheckMonteCarloRetest.md) | 7 | `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest` |
| [CrossCheckOptProfileSysParamPermutation.jar](CrossCheckOptProfileSysParamPermutation.md) | 2 | `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation` |
| [CrossCheckRetestOnAdditionalMarkets.jar](CrossCheckRetestOnAdditionalMarkets.md) | 4 | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets` |
| [CrossCheckRetestWithHigherPrecision.jar](CrossCheckRetestWithHigherPrecision.md) | 4 | `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision` |
| [CrossCheckSequentialOptimization.jar](CrossCheckSequentialOptimization.md) | 2 | `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization` |
| [CrossCheckWalkForwardMatrix.jar](CrossCheckWalkForwardMatrix.md) | 1 | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix` |
| [CrossCheckWalkForwardOptimization.jar](CrossCheckWalkForwardOptimization.md) | 1 | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization` |
| [CrossCheckWhatIf.jar](CrossCheckWhatIf.md) | 2 | `com.strategyquant.plugin.CrossCheck.impl.WhatIf` |
| [FitnessMethodExistingPortfolio.jar](FitnessMethodExistingPortfolio.md) | 4 | `com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio` |
| [FitnessMethodStrategyResult.jar](FitnessMethodStrategyResult.md) | 4 | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult` |
| [FitnessMethodWFResult.jar](FitnessMethodWFResult.md) | 3 | `com.strategyquant.plugin.FitnessMethod.impl.WFResult` |
| [HomeAbout.jar](HomeAbout.md) | 2 | `com.strategyquant.plugin.Home.impl.About` |
| [LoaderSQ3.jar](LoaderSQ3.md) | 5 | `com.strategyquant.plugin.Loader.impl.SQ3` |
| [LoaderSQ4.jar](LoaderSQ4.md) | 1 | `com.strategyquant.plugin.Loader.impl.SQ4` |
| [ProjectConditionCyclesCount.jar](ProjectConditionCyclesCount.md) | 1 | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount` |
| [ProjectConditionDuration.jar](ProjectConditionDuration.md) | 0 | No compiled classes |
| [ProjectConditionGoToActivated.jar](ProjectConditionGoToActivated.md) | 1 | `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated` |
| [ProjectConditionGoToEvaluated.jar](ProjectConditionGoToEvaluated.md) | 1 | `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated` |
| [ProjectConditionResultsCount.jar](ProjectConditionResultsCount.md) | 1 | `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount` |
| [ProjectConditionRunTime.jar](ProjectConditionRunTime.md) | 1 | `com.strategyquant.plugin.ProjectCondition.impl.RunTime` |
| [ProjectOptimizer.jar](ProjectOptimizer.md) | 0 | No compiled classes |
| [ProjectRetester.jar](ProjectRetester.md) | 0 | No compiled classes |
| [SaverHTML.jar](SaverHTML.md) | 1 | `com.strategyquant.plugin.Saver.impl.HTML` |
| [SaverPDF.jar](SaverPDF.md) | 1 | `com.strategyquant.plugin.Saver.impl.PDF` |
| [SaverSQ3.jar](SaverSQ3.md) | 2 | `com.strategyquant.plugin.Saver.impl.SQ3` |
| [SaverStrategyTrades.jar](SaverStrategyTrades.md) | 1 | `com.strategyquant.plugin.Saver.impl.StrategyTrades` |
| [ServletConnection.jar](ServletConnection.md) | 2 | `com.strategyquant.plugin.Servlet.impl.Connection` |
| [ServletConstants.jar](ServletConstants.md) | 2 | `com.strategyquant.plugin.Servlet.impl.Constants` |
| [ServletDatabankViews.jar](ServletDatabankViews.md) | 0 | No compiled classes |
| [ServletIndicatorTester.jar](ServletIndicatorTester.md) | 0 | No compiled classes |
| [ServletMCP.jar](ServletMCP.md) | 1 | `com.strategyquant.plugin.Servlet.impl.MCP` |
| [ServletProjectOld.jar](ServletProjectOld.md) | 0 | No compiled classes |
| [ServletRenameTool.jar](ServletRenameTool.md) | 4 | `com.strategyquant.plugin.Servlet.impl.RenameTool` |
| [ServletStrategy.jar](ServletStrategy.md) | 3 | `com.strategyquant.plugin.Servlet.impl.Strategy` |
| [ServletYahoo.jar](ServletYahoo.md) | 0 | No compiled classes |
| [SettingsAdvancedTM.jar](SettingsAdvancedTM.md) | 2 | `com.strategyquant.plugin.Settings.impl.AdvancedTM` |
| [SettingsApplyMassConfig.jar](SettingsApplyMassConfig.md) | 1 | `com.strategyquant.plugin.Settings.impl.ApplyMassConfig` |
| [SettingsAutoRetestData.jar](SettingsAutoRetestData.md) | 1 | `com.strategyquant.plugin.Settings.impl.AutoRetestData` |
| [SettingsBlocks.jar](SettingsBlocks.md) | 2 | `com.strategyquant.plugin.Settings.impl.Blocks` |
| [SettingsCallExternalScript.jar](SettingsCallExternalScript.md) | 1 | `com.strategyquant.plugin.Settings.impl.CallExternalScript` |
| [SettingsClearDatabanks.jar](SettingsClearDatabanks.md) | 1 | `com.strategyquant.plugin.Settings.impl.ClearDatabanks` |
| [SettingsCreatePortfolio.jar](SettingsCreatePortfolio.md) | 1 | `com.strategyquant.plugin.Settings.impl.CreatePortfolio` |
| [SettingsCrossChecks.jar](SettingsCrossChecks.md) | 2 | `com.strategyquant.plugin.Settings.impl.CrossChecks` |
| [SettingsCustomAnalysis.jar](SettingsCustomAnalysis.md) | 1 | `com.strategyquant.plugin.Settings.impl.CustomAnalysis` |
| [SettingsData.jar](SettingsData.md) | 1 | `com.strategyquant.plugin.Settings.impl.Data` |
| [SettingsDatabanks.jar](SettingsDatabanks.md) | 0 | No compiled classes |
| [SettingsDeleteFile.jar](SettingsDeleteFile.md) | 1 | `com.strategyquant.plugin.Settings.impl.DeleteFile` |
| [SettingsFiltering.jar](SettingsFiltering.md) | 1 | `com.strategyquant.plugin.Settings.impl.Filtering` |
| [SettingsGoToTask.jar](SettingsGoToTask.md) | 1 | `com.strategyquant.plugin.Settings.impl.GoToTask` |
| [SettingsLoadFromFiles.jar](SettingsLoadFromFiles.md) | 1 | `com.strategyquant.plugin.Settings.impl.LoadFromFiles` |
| [SettingsLogDatabankStats.jar](SettingsLogDatabankStats.md) | 1 | `com.strategyquant.plugin.Settings.impl.LogDatabankStats` |
| [SettingsMoneyManagement.jar](SettingsMoneyManagement.md) | 1 | `com.strategyquant.plugin.Settings.impl.MoneyManagement` |
| [SettingsNotes.jar](SettingsNotes.md) | 1 | `com.strategyquant.plugin.Settings.impl.Notes` |
| [SettingsNotification.jar](SettingsNotification.md) | 3 | `com.strategyquant.plugin.Settings.impl.Notification` |
| [SettingsOptimization.jar](SettingsOptimization.md) | 2 | `com.strategyquant.plugin.Settings.impl.Optimization` |
| [SettingsOptions.jar](SettingsOptions.md) | 2 | `com.strategyquant.plugin.Settings.impl.Options` |
| [SettingsPartsToImprove.jar](SettingsPartsToImprove.md) | 1 | `com.strategyquant.plugin.Settings.impl.PartsToImprove` |
| [SettingsRankings.jar](SettingsRankings.md) | 2 | `com.strategyquant.plugin.Settings.impl.Rankings` |
| [SettingsSaveToFiles.jar](SettingsSaveToFiles.md) | 1 | `com.strategyquant.plugin.Settings.impl.SaveToFiles` |
| [SettingsStopAndStart.jar](SettingsStopAndStart.md) | 1 | `com.strategyquant.plugin.Settings.impl.StopAndStart` |
| [SettingsUpdateData.jar](SettingsUpdateData.md) | 1 | `com.strategyquant.plugin.Settings.impl.UpdateData` |
| [SettingsWaitFor.jar](SettingsWaitFor.md) | 1 | `com.strategyquant.plugin.Settings.impl.WaitFor` |
| [SettingsWhatToBuild.jar](SettingsWhatToBuild.md) | 2 | `com.strategyquant.plugin.Settings.impl.WhatToBuild` |
| [SettingsWhatToRetest.jar](SettingsWhatToRetest.md) | 1 | `com.strategyquant.plugin.Settings.impl.WhatToRetest` |

## Workspace registration evidence

No App registration assigned here. This is a shared research grouping.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

No cross-group reference resolved within the scoped archives. This is not proof of runtime independence.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
