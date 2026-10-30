/** Current project-module inventory, preserving original provenance cohorts. */
const files = import.meta.glob(["../../../common/project/**/*", "../../../workspaces/home/**/*", "../../../workspaces/results/**/*", "../../../workspaces/builder/**/*", "../../../workspaces/retester/**/*", "../../../workspaces/task_manager/**/*"], { eager: true, query: "?raw", import: "default" }) as Record<string, string>;
const roots: Record<string, string> = {
  "EnginePanel": "../../../workspaces/home/EnginePanel/",
  "ProjectResults": "../../../workspaces/home/ProjectResults/",
  "ProjectSettings": "../../../workspaces/home/ProjectSettings/",
  "ProjectWorkbench": "../../../common/project/",
  "ResultsChart": "../../../workspaces/results/ResultsChart/",
  "ResultsEquityChart": "../../../workspaces/results/ResultsEquityChart/",
  "ResultsOverview": "../../../workspaces/results/ResultsOverview/",
  "ResultsPortfolioCorrelation": "../../../workspaces/results/ResultsPortfolioCorrelation/",
  "ResultsProfileChart": "../../../workspaces/results/ResultsProfileChart/",
  "ResultsRobustnessTests": "../../../workspaces/results/ResultsRobustnessTests/",
  "ResultsSPOverview": "../../../workspaces/results/ResultsSPOverview/",
  "ResultsSourceCode": "../../../workspaces/results/ResultsSourceCode/",
  "ResultsStockpicker": "../../../workspaces/results/ResultsStockpicker/",
  "ResultsStrategyConfig": "../../../workspaces/results/ResultsStrategyConfig/",
  "ResultsTradeAnalysis": "../../../workspaces/results/ResultsTradeAnalysis/",
  "ResultsTradeList": "../../../workspaces/results/ResultsTradeList/",
  "ResultsTradelistViews": "../../../workspaces/results/ResultsTradelistViews/",
  "SettingsAdvancedTM": "../../../workspaces/task_manager/SettingsAdvancedTM/",
  "SettingsCrossChecks": "../../../workspaces/retester/SettingsCrossChecks/",
  "SettingsData": "../../../workspaces/home/SettingsData/",
  "SettingsMoneyManagement": "../../../workspaces/home/SettingsMoneyManagement/",
  "SettingsNotes": "../../../workspaces/home/SettingsNotes/",
  "SettingsOptions": "../../../workspaces/home/SettingsOptions/",
  "SettingsPanel": "../../../workspaces/home/SettingsPanel/",
  "SettingsRankings": "../../../workspaces/builder/SettingsRankings/"
};
export const projectFiles: Record<string, string> = {};
for (const [module, root] of Object.entries(roots)) {
  for (const [path, content] of Object.entries(files)) {
    if (path.startsWith(root)) projectFiles[`project/${module}/${path.slice(root.length)}`] = content;
  }
}
