# Source reassessment: workspaces 09–19

Audit date: 2026-10-30. This supplement supersedes source-availability assumptions in the linked active orders; retained historical evidence remains historical. It does not declare full-workflow parity or authorize copying Java implementations.

## Coverage and interpretation

All source locators below now use the consolidated `DONOR_REFERENCE_ROOT/` tree:
libraries in `internal/libs`, plugin implementations and assets in `internal/plugins`,
extensions in `internal/extend`, templates in `internal/ctemplate` or `internal/extend/Code`,
and web resources in `internal/web`. Temporary decompilation folders are no longer required.

Availability counts, method discovery and no-match findings below are retained from the
original audit, before consolidation. Consult [the current manifest](donor-source-manifest.json)
for copied Java files. A previous no-match result is not a claim that the copied tree lacks
that module. Behavioral findings and work-order gates remain unchanged by this path cleanup.
Source SHA-256 entries now identify the current copied files. Behavioral observations and method counts remain from the earlier audit; a relocated file with changed bytes requires revalidation before claiming parity. Original carrier provenance does not establish parity across builds.

## Module source records

### AppOptimizer

Owner: `09-AppOptimizer.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppOptimizer/module.js`; SHA-256 `4fb1412f336229a0d4a9d4a3d0f106ebae40a46ea5db40e349170ab38c8d72ef`.

### FitnessMethodWFResult

Owner: `09-AppOptimizer.md`. Readable Java matches: 1; primary frontend/settings files: 0.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/WFResult/FitnessMethodWFResult.java`; SHA-256 `9db2d16bd9392d448a2c578997148d0056acd5a6ca94f60acd4811a309755ac0`.
  - Declared callables: `FitnessMethodWFResult()`; `FitnessMethodWFResult(String databankColumnName)`; `getProduct()`; `getPreferredPosition()`; `initPlugin()`; `computeFitness(ResultsGroup results, byte direction, byte sampleType)`; `computeFitness(ResultsGroup results, byte direction, byte sampleType, boolean useRatioByTrades)`; `initFitnessFromXml(Element elSettings)`; `getFitnessType()`; `getFitnessKey()`; `getFitnessName()`; `getFitnessDatabankColumnName()`; `getUsedStatValues()`; `printWeightedGoals()`. Further methods remain in the named source.

**Inspected behavior:** metric lookup reads the first WalkForwardMatrixResult result; absent/empty WF results or missing metric return zero. Metric fitness is transformed by the selected databank column and clamped to [0,1]. Weighted mode sums enabled weights and accumulates with Java float rounding; exact zero weighted fitness falls back to NetProfit. XML weights/valueType/target defaults are 1/0/0. Enabled goals whose column lookup fails are skipped with logging. Undefined/zero-weight behavior and float precision need explicit target handling before granting full numerical parity.

### ResultsOptimizationProfile

Owner: `09-AppOptimizer.md`. Readable Java matches: 0; primary frontend/settings files: 9.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/directives/manageviews/ManageViewsService.js`; SHA-256 `084b19861cb1a36dbdc41c56c2ae259142b4cf089b47c17b61c724f4e5cffaaf`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/module.js`; SHA-256 `22c51cd05617791a2d4021c9fd87ecfcb857183c9532a3d7ab4484287a651d66`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/OptimizationProfileService.js`; SHA-256 `c5367f15d9e8b88b4165b3a367e46b9489187d83e1c3299ad6d7e3916632012e`.

### ResultsSequentialOptimization

Owner: `09-AppOptimizer.md`. Readable Java matches: 0; primary frontend/settings files: 6.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/module.js`; SHA-256 `2eb4ef83ef13c7d7766e3b472d582d0d3c09c46ba6172b5a6357bf0dd7927498`.

### ResultsSysParamPermutation

Owner: `09-AppOptimizer.md`. Readable Java matches: 0; primary frontend/settings files: 7.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/module.js`; SHA-256 `65051d2663967d13c0047294a6017a6bcefa233e075e63c9181ed74d83482587`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/services/SysParamPermutationService.js`; SHA-256 `9f4776f3d26df9d05a0f06dfc6764b7f7a8d08a38af4be0b95e40f928ceed2c6`.

### ResultsWalkForward

Owner: `09-AppOptimizer.md`. Readable Java matches: 0; primary frontend/settings files: 8.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/directives/manageviews/ManageViewsServiceWF.js`; SHA-256 `f6b67b4f989f3a486686be60b62dd97531f5d24df00b05298e556dc3907826c1`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/module.js`; SHA-256 `bb46372c13568ca5e8db16e3025d54843c9156272b4f65495f7bf906d0141957`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/WFResultsService.js`; SHA-256 `4bc61662f805f9658d5dbd25e823248363ba93fe35c11ccd42af3ec8995ad752`.

### SettingsOptimization

Owner: `09-AppOptimizer.md`. Readable Java matches: 3; primary frontend/settings files: 5.

- Source: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/optimization/OptimizationParams.java`; SHA-256 `d3023dcf05c2c799e3e0ecc681a14e71dfb105fc8d2832cd6a20059ee06bb3fe`.
  - Declared callables: `addParam(String string, byte by, boolean bl, double d, double d2, double d3, double d4)`; `addParam(Parameter parameter)`; `getTotalCombinations()`; `getValue(int n, String string)`; `verify()`; `getUsedCount()`; `prepareTestParameters(long l, short[] sArray)`; `clone()`.
- Source: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/optimization/OptimizationSettings.java`; SHA-256 `5d9ca17cd49b34d8fa36b157f663d067323b749e782c0a1afaae3677541c937c`.
  - Declared callables: `OptimizationSettings(String string)`; `setFromXML(Element element, Element element2)`; `verify()`; `verifyStandard()`; `transformToFullIndexes(short[] sArray)`; `clone()`; `isOptimizationConfigurable()`; `getProjectLogMessage()`.
- Source: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/optimization/ParametersSettings.java`; SHA-256 `48db2d1cdc5b29965c30d1c387787e0f1c758566c200229d65bdac787edd62b2`.
  - Declared callables: `ParametersSettings()`; `setFromXML(Element element, Element element2)`; `checkParamValid(double d, double d2, double d3)`; `checkTimeParamValid(int n, int n2, int n3)`; `createParameter(Variable variable, int n, int n2, int n3)`; `setFromXMLOptimConfig(String[] stringArray, String string, int n)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsOptimization/module.js`; SHA-256 `8596fd19bc745626fd8a92dd2b0a3fb36a12202e0e364bf63cefb171ec613c4d`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsOptimization/OptimizationService.js`; SHA-256 `98a8c8ebf2676a2d58f92cd0fb59baa9b1c5f9c8c5335959508b2e0990b94b0e`.

**Inspected behavior:** `OptimizationSettings.setFromXML` defaults maxOptimizations to 100; Source type 1 selects a single file and verifies existence. Optimization types 1 and 4 use SimpleOptimization; 2 and 3 use WalkForward; other types throw. Missing rankings WalkForward throws. WF type 2 makes each stop equal start and step zero. `verifyStandard` skips types 1/4; period 10 bounds starts/stops at 1..95; period 20 at 5..100000; otherwise 5..500000. Matrix steps are 1..95, 5..5000, or 5..50000 respectively, with derived step count limited to 1..100. Decompiled local typing is malformed in places; validate those expressions against signatures/bytecode before claiming parser parity.

### TaskOptimize

Owner: `09-AppOptimizer.md`. Readable Java matches: 5; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskOptimize/Optimize/OptimizeTask.java`; SHA-256 `26caafe1178441e13357a221840ecbb5ced4c4f609076ddd7691e855bba347ef`.
  - Declared callables: `OptimizeTask()`; `OptimizeTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `setDatabankFilter(Databank db)`; `newResult(ResultsGroup resultsGroup)`; `processMessage(String message)`; `step(int stepNumber)`; `newResult(ResultsGroup resultsGroup)`; `processMessage(String message)`; `step(int stepNumber)`; `onFinish(boolean success, StrategyBase optimizedStrategy, SequentialOptimizationResults results, ResultsGroup optimizedRG)`. Further methods remain in the named source.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskOptimize/Optimize/ConfigVerifier.java`; SHA-256 `e9c6eb823dc4fd602ef9865620ee9d22a25305c381f8a99c1823404fe48337ad`.
  - Declared callables: `verifyConfig(Element taskConfig)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskOptimize/Optimize/OptimizeTask.java`; SHA-256 `26caafe1178441e13357a221840ecbb5ced4c4f609076ddd7691e855bba347ef`.
  - Declared callables: `OptimizeTask()`; `OptimizeTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `setDatabankFilter(Databank db)`; `newResult(ResultsGroup resultsGroup)`; `processMessage(String message)`; `step(int stepNumber)`; `newResult(ResultsGroup resultsGroup)`; `processMessage(String message)`; `step(int stepNumber)`; `onFinish(boolean success, StrategyBase optimizedStrategy, SequentialOptimizationResults results, ResultsGroup optimizedRG)`. Further methods remain in the named source.
- Source: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/optimization/OptimizationEngine.java`; SHA-256 `8d0f750d2078c4afd1ff38251cf0dcc550391dae01c42eb1015d9d23a0aa3271`.
  - Declared callables: `OptimizationEngine(String string, StopPauseEngine stopPauseEngine, GridJob gridJob, String string2, ILastEventListener iLastEventListener)`; `OptimizationEngine(String string, StopPauseEngine stopPauseEngine, GridJob gridJob, String string2, ILastEventListener iLastEventListener, String string3)`; `optimize()`.
- Source: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/optimization/OptimizationSettings.java`; SHA-256 `5d9ca17cd49b34d8fa36b157f663d067323b749e782c0a1afaae3677541c937c`.
  - Declared callables: `OptimizationSettings(String string)`; `setFromXML(Element element, Element element2)`; `verify()`; `verifyStandard()`; `transformToFullIndexes(short[] sArray)`; `clone()`; `isOptimizationConfigurable()`; `getProjectLogMessage()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskOptimize/module.js`; SHA-256 `c21779e100e1db8e6fd8837561c4722f3134898669d8b6290d31094ccdfb7df1`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskOptimize/task.xml`; SHA-256 `521167b48c41eaa7d58504282a0c79665dad72e2d093a209243a6d9531ca2534`.

### AppPortfolioComposer

Owner: `10-AppPortfolioComposer.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/module.js`; SHA-256 `2ff7c77dacaeda23717c88b90c7b039efe2495fa7985d379c06d1d9d10fa152d`.

### PortfolioComposer

Owner: `10-AppPortfolioComposer.md`. Readable Java matches: 9; primary frontend/settings files: 16.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposer.java`; SHA-256 `f8bba096ac650d4eda0e700556d5a4af01c64db1dfb8f6b9b4105c30561ff456`.
  - Declared callables: `recalculate(String portfolioName, PortfolioComposerSettings settings, Double[] weights)`; `calculateExpectedShortfall(double mu, double sigma, double confidenceLevel)`; `addProfit(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitMap, Long2ObjectAVLTreeMap<Map<String, Double>> marginUsedMap, Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, long epochMillis, String strategy, double profit, double marginUsed)`; `calculateStandardDeviationLastNPeriods(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, String strategy, int n)`; `getAverageProfitPercentage(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, String strategy, int n)`; `getLastMarginUsed(Long2ObjectAVLTreeMap<Map<String, Double>> marginUsedMap, String strategy)`; `getAverageMarginUsed(Long2ObjectAVLTreeMap<Map<String, Double>> marginUsedMap, String strategy)`; `getCorrelation(Long2ObjectAVLTreeMap<Map<String, Double>> dailyProfitPercentageMap, String strategy1, String strategy2)`; `stop()`; `print(String log)`; `tradesModified()`; `reset()`; `toString()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerChart.java`; SHA-256 `df4be8ddc03fdef72008ffd92704ac953c4ffe9f88daf9c8f9d549136ba9d310`.
  - Declared callables: `PortfolioComposerChart(int nDataPoints)`; `toJsonString()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerJob.java`; SHA-256 `bfac110cfbd4368af46e56b80fabe5a64022ac66bb8ba2aba693f2d05e8b19fb`.
  - Declared callables: `PortfolioComposerJob(String jobID, Map<String, Serializable> params)`; `call()`; `messageReceived(GridMessage message)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerLog.java`; SHA-256 `d87fc3229922f26892781200e25c2e5496bb358036b6c88d420d5c936e859755`.
  - Declared callables: `PortfolioComposerLog(String resultName, PortfolioComposerSettings settings)`; `print(String log)`; `printNoNewLine(String log)`; `toString()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerPlugin.java`; SHA-256 `de7a60cee9102f5e416dfadbf9d3a21fc798dff8002aed3f2671f9c52f440b24`.
  - Declared callables: `getProduct()`; `getPreferredPosition()`; `initPlugin()`; `getHandler()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerResultsSender.java`; SHA-256 `e41b4519296ee455dc7bef98b8ba49b97b89f890d26aaacfdde3a21c3f9d1407`.
  - Declared callables: `PortfolioComposerResultsSender()`; `getData()`; `sendData(JSONObject data)`; `resetLastData()`; `progress(int pct, String message)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerServlet.java`; SHA-256 `f187bd2705b2e6be9db3e2cb2aa3fa20d1ca0000e8d16eb97f326ed7c6eb6aaf`.
  - Declared callables: `PortfolioComposerServlet()`; `execute(String command, Map<String, String[]> args, String method)`; `run()`; `run()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerSettings.java`; SHA-256 `33a042fa0d89a204a47ae4d820c8ffb7a2bb70c6c26b2376ce20b16ad39b53c7`.
  - Declared callables: `setSelectionTypeByString(String selectionType)`; `getDecimalsByFitness()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/Composer/PortfolioComposerSimulator.java`; SHA-256 `5f0f159ad80336a1d54a09716f378666f03e75bfb42f2b54cd84937d7d641e38`.
  - Declared callables: `start(SQProject project, PortfolioComposerSettings settings, PortfolioComposerResultsSender sender, StopPauseEngine stopPauseEngine, boolean autocomputation)`; `createJobsBatch(int jobsToCreate, GridClient gridClient)`; `processResult(ResultsGroup rg, JobDetails jobDetails)`; `onError(String errorMsg, Exception exception)`; `processJobResult(ResultsGroup rg, JobDetails jobDetails, ArrayList<ResultsGroup> simulationResults)`; `createBatch(int jobsToCreate, GridClient gridClient, long totalCombinations)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposerService.js`; SHA-256 `da13beb5619f3993db54ae0a3e359da52f7b022a4a779e7d4c81d81b993d84ff`.

### ResultsPortfolioComposerChart

Owner: `10-AppPortfolioComposer.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/module.js`; SHA-256 `82d94006323cf0beced65c9477d1a8832ffcc6e1dbf2b9cef3677ca16a6d3d2b`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/PortfolioComposerChartService.js`; SHA-256 `1be0c3701eaa13cbfda9393ad626e39b78ac83dd04a09f1f1c73cd8ac837e4ba`.

### ResultsPortfolioComposerLog

Owner: `10-AppPortfolioComposer.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/module.js`; SHA-256 `80534979161801d16b02aa844afab5eddd6105fb0a23677156d9dc86e1b30c08`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/PortfolioComposerLogService.js`; SHA-256 `57fa0e22c5ab335a90835e521329fe16c5a4c295c8e965ffd5f2885fd1f8dae5`.

### AppPortfolioMaster

Owner: `11-AppPortfolioMaster.md`. Readable Java matches: 1; primary frontend/settings files: 1.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/PortfolioMaster/PortfolioMasterAppPlugin.java`; SHA-256 `108a1c8324f15adc3836a59b0b105d27565bba7c29037545d8be60c80bbe5b03`.
  - Declared callables: `getName()`; `getProduct()`; `getPreferredPosition()`; `initPlugin()`; `getContextPath()`; `getAppCode()`; `getTooltip()`; `getProject()`; `getDefaultTaskType()`; `getDefaultTaskName()`; `disabledForSpecialTrial()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/module.js`; SHA-256 `f74d1bf3364d5d914be53c8f73ba599fc413ca462111ffa1b74c557b5c9e140f`.

### FitnessMethodExistingPortfolio

Owner: `11-AppPortfolioMaster.md`. Readable Java matches: 2; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/AutomaticPortfolioBuilder/bruteForce/PMPortfolioComputer.java`; SHA-256 `2437b38b62589ab92a0d3b587d2b19ae3edbcde0bd3b5d964a533d9f3283550d`.
  - Declared callables: `createPortfolio(ArrayList<ResultsGroup> results, String portfolioName, PortfolioMasterSettings settings)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/AutomaticPortfolioBuilder/genetic/PortfolioFitnessCache.java`; SHA-256 `403a229a7222043ec51f10ff6cc821cdc832e61ba7aa4a89bec3034718afc38c`.
  - Declared callables: `reset()`; `getFitness(int portfolioHashKey)`; `setFitness(int portfolioHashKey, double fitness)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolioService.js`; SHA-256 `0080c399e4f1aecf17fd87328b70b07063c6190f14641ba619ba3f60b4b109a7`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/module.js`; SHA-256 `c3efe697ca564cbfa5441aaa5e88c3d2ab37b2a58fd0a453c2a5d79d8781143d`.

### AppTaskManager

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppTaskManager/module.js`; SHA-256 `ef98b2ae51eb2d2f36b682f0fd470da479bdfa33f8682806d5076d8b0c27b32f`.

### SettingsAdvancedTM

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 5.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/addNewExitPopup.html`; SHA-256 `4d70be970791b9928e5c1dedb3dd405f0b36cdbef534428dc4246bf3288d6ae0`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/advancedTM.html`; SHA-256 `8630945107f2154c768c82e1048c1b176eeae1df51ca7c4e3cca62877de579b7`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/AdvancedTMCtrl.js`; SHA-256 `63d5caea9ece232638a6eda7c21dc09e13730042c9a8836a762d8213901d6fea`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/module.js`; SHA-256 `5e872e34f232b518579cf1877a6cde5e01886a7aa514cad4cd9e778374b15b19`.

### SettingsApplyMassConfig

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/applyMassConfig.html`; SHA-256 `46e966383bf6fa5100399b35969d49518ef98e8710bbae4bc0764ce87f8d11af`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/ApplyMassConfigCtrl.js`; SHA-256 `72b55f499e8d79ed034be804ae40918aa0f129edb034043d17ee9c3c546ffced`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/ApplyMassConfigService.js`; SHA-256 `b23b4f2886078c076d3c013e612ac1669a3555b61cf8a741640b338e1756cc20`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/module.js`; SHA-256 `0e75a5321b5f381fb3589e5e2329064dad899343183a71cd8bef2f8352a9f2f0`.

### SettingsAutomaticPortfolioBuilder

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 6.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/automaticPortfolioBuilder.html`; SHA-256 `b817857054180a17d723c6c4439278f1642b1a975350b510bafe4201f8f603b4`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/AutomaticPortfolioBuilderCtrl.js`; SHA-256 `be94a8d16aba7b64d6b9df2929c62ff1d3cd3ef045b5d744f7efe08c35f66505`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/AutomaticPortfolioBuilderService.js`; SHA-256 `6665b9fa2e4f488226a181a53acb994bb81f816b950752c754ba5cf677b8a784`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/module.js`; SHA-256 `896a81bb0dc76cf69d8f978a19b47e2d916ffe3bc6dd0e483133dddc94463f76`.

### SettingsAutomaticRetest

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 3.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/automaticRetest.html`; SHA-256 `326be2d2ea4c12b955f49c7063cef58b2b9bce9300b46217778aa02f70ce3cb4`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/module.js`; SHA-256 `c961f9624cd459e95f1ef4be70ea41990efcf7ec6effdf73474b9c7189de7316`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/SettingsAutomaticRetestCtrl.js`; SHA-256 `677fe0ca4912ac6d0cd4cc6a2037e732ac5e06eafda30a9babee17cafc8e1614`.

### SettingsCallExternalScript

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/module.js`; SHA-256 `51527cd717394f4dc59cc920ed2a0759f94e55d479e390efd46fc5fe38517d75`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/settingsCallExternalScript.html`; SHA-256 `135f4a641231d5ce890b43946ab5f9f7edae012e899301ea30465f61faf899ca`.

### SettingsClearDatabanks

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 3.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/clearDatabanks.html`; SHA-256 `499c410fe7c9b09bd2e22cfb66faecbff61fc64fca3f0243d8bb552682ec776f`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/module.js`; SHA-256 `71ae9736def471a376883f3b05c11eb3e1c24ffc2c08133844629da403129512`.

### SettingsCreatePortfolio

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/module.js`; SHA-256 `55e6b17cc4f0cc619f95b270b1956f03e71d449235a073918c3f2b7fd376994a`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/settingsCreatePortfolio.html`; SHA-256 `d20a8168a52949ccc3bf68c9a3d317d25daa7193130b32589d2bce1f028b7f54`.

### SettingsCustomAnalysis

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/module.js`; SHA-256 `6f2c6f662913707f32f7ee136f669f313a2d8c38e03b47a2aba1706967e46d1b`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/settingsCustomAnalysis.html`; SHA-256 `88d65b318ff314d7583439293d95a6da79a9651c996eac5da79c02d2ab2bb820`.

### SettingsDeleteFile

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/module.js`; SHA-256 `7c213dff55303b14936e6dbb92f53a844d491150e978a6ff48359309a1bd40c6`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/settingsDeleteFile.html`; SHA-256 `91310710b67d5872a19e9e1ff94d2feb193c94c2cdd11659bf1467fc0e10ec66`.

### SettingsFiltering

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsFiltering/module.js`; SHA-256 `cf647e3beb90a7cb4aa17f6ff611042a1949b16581ff23aee49b8e4d8090c4d0`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsFiltering/settingsFiltering.html`; SHA-256 `b28fe78973670766ad24301648e22dc6358e473671ea78e08885ccd3b802c7ae`.

### SettingsGoToTask

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/module.js`; SHA-256 `cc46e0368814378363250014cb4b7f1807c614f94de09bbb56ecdf5319d864bd`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/settingsGoToTask.html`; SHA-256 `9dd1b4be4f3e75997145bed69b1115a267fa8469b8ce4fd22e20cd494f9e8906`.

### SettingsLoadFromFiles

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/module.js`; SHA-256 `2a5fc315e183e28e308c6c7e5fb1e56375bbc516779a8f5b0e51b3d3bbc93e52`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/settingsLoadFromFiles.html`; SHA-256 `4a81ac0671f3f3ae5e0f552d98c8d0ea7748b477c6f99b106a759db4d2d0e711`.

### SettingsLogDatabankStats

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 8.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/directives/logDatabankStatsType.html`; SHA-256 `a9e3dae30275e1d23dbad95ac4af645bc359bae636123c301e302ea89633fa44`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/directives/LogDatabankStatsType.js`; SHA-256 `2bb57818386c38bed82e36f3f9f9f9e21270dbe3e4e33ae6deea78c9b08e6122`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/directives/LogDatabankStatsTypeCtrl.js`; SHA-256 `68de95d66c4f094084d272e5776b528d1ac6ef44a3f8dd54b840e9086db0adcd`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/module.js`; SHA-256 `04c3054e541c2328cdd041af51d8ceb2b57b7fd3081c37a8183cdb3c18f7e3d4`.

### SettingsNotification

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsNotification/module.js`; SHA-256 `ec3307048ce65e02f3a2a8a6cc1f2dd3a7fd11c78555b412c0b1eee978d46e68`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsNotification/settingsNotification.html`; SHA-256 `4928887bbadc7e52d302597719b9764291d4aac5397fa833b3aaf8ec8b631408`.

### SettingsSaveToFiles

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/module.js`; SHA-256 `c3135d0f90cd7b91cb2e3e6f306ba3b9ac7279714cd3d63746f332ac5523bc55`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/settingsSaveToFiles.html`; SHA-256 `fd48a957b04b7bc51424741bc310ea499fa9dd08573a0aef3dce6a3888d07983`.

### SettingsStopAndStart

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/module.js`; SHA-256 `c66e962ee43cf26cdb195d69fec102022aa880461a1951de100eb20f3a2932db`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/settingsStopAndStart.html`; SHA-256 `2de8963092233d9955b0cc37f2b96cba8e0220238a5c53e259017999ff4912f8`.

### SettingsUpdateData

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/module.js`; SHA-256 `43a60a97fdfce8653e07505c531aed8e8296f604a2be29157fa18d6e9ecd9ed8`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/settingsUpdateData.html`; SHA-256 `ba19ac1a28397220085e549781f61fdd3ed8acc9d72840423d08b518f19c82bc`.

### SettingsWaitFor

Owner: `12-AppTaskManager.md`. Readable Java matches: 0; primary frontend/settings files: 4.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/module.js`; SHA-256 `fd0d3bb8e2cb7010829516e6dbaa35a88f36f6f23c305d33629a4eb98294d247`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/settingsWaitFor.html`; SHA-256 `9b94c711d828f52b3f5a1760326d065b593f919fd6b25cc7b00e40b9a5efff45`.

### TaskApplyMassConfig

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/ApplyMassConfig/ApplyMassConfigTask.java`; SHA-256 `88cc1548016ce09dc7d3d6acf1a2b6ca793dfb218d2538149038ea9f585abde5`.
  - Declared callables: `ApplyMassConfigTask()`; `ApplyMassConfigTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/module.js`; SHA-256 `4a36fbe6fb1535e8fbc836f7a4534d8dcf55134e6a25bf1454fe565492f53af4`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/simpleSettings/SimpleApplyMassConfigCtrl.js`; SHA-256 `23e4da0ec66bcf5350eda52abf54761b28bc1d988d3829e6ec003c999088f523`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/simpleSettings/simpleSettings.html`; SHA-256 `46e966383bf6fa5100399b35969d49518ef98e8710bbae4bc0764ce87f8d11af`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/task.xml`; SHA-256 `2bb1209a0647274f99b6cc8ac6d89142957160c080376e2af8843a0e3def7f18`.

### TaskAutomaticPortfolioBuilder

Owner: `12-AppTaskManager.md`. Readable Java matches: 2; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/AutomaticPortfolioBuilder/AutomaticPortfolioBuilder.java`; SHA-256 `7707120aea6d5d3cf508c833feb0389d795b594e72c73dce5f1d87f25fc8b60e`.
  - Declared callables: `start(SQProject project, ProgressEngine progressEngine, PortfolioMasterSettings settings)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/AutomaticPortfolioBuilder/AutomaticPortfolioBuilderTask.java`; SHA-256 `50ef95ead47597cadbc84fb06cf11e2c41a1dbc8d9ab5dfdc8929a5b3970cd6f`.
  - Declared callables: `AutomaticPortfolioBuilderTask()`; `AutomaticPortfolioBuilderTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/module.js`; SHA-256 `9dc70ec65130166a3b75d055438202ae33cfb96991b819673a76b07d6d332ce9`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/simpleSettings/SimpleAutoPortfolioBuilderCtrl.js`; SHA-256 `7cb3ca741283414a904750864771c2127077496fee85c9cdaf0fb1b3d2735a99`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/simpleSettings/simpleSettings.html`; SHA-256 `0a6c813828a7c5f0fbe19dec90e0be7504093d26cfa2dfb50381f01c5006eed9`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/task.xml`; SHA-256 `2fde966ab5afc42dcf007fc65d61519f61a0cc82cde8b2dcb92b5916e03ef858`.

### TaskAutomaticRetest

Owner: `12-AppTaskManager.md`. Readable Java matches: 2; primary frontend/settings files: 5.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/AutomaticRetest/AutomaticRetestJob.java`; SHA-256 `9340d19c39713a99b6a59cecbb92dacc90f2c6a6697bcc848c4034a766d9ff0d`.
  - Declared callables: `AutomaticRetestJob(String jobID, Map<String, Serializable> params, StopPauseEngine stopPauseEngine, ILastEventListener lastEventListener)`; `call()`; `messageReceived(GridMessage message)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/AutomaticRetest/AutomaticRetestTask.java`; SHA-256 `5e82ae6f8898c25187477116a21b09e6091e14f1f1de5f3475ddac7c3e79748f`.
  - Declared callables: `AutomaticRetestTask()`; `AutomaticRetestTask(String projectName, ProgressEngine progressEngine)`; `beforeStart()`; `start()`; `messageReceived(GridMessage message)`; `run()`; `checkAllFinished()`; `processMessage(GridMessage message)`; `getType()`; `getPluginFolderName()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `getPreferredPosition()`; `getSettings()`. Further methods remain in the named source.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/module.js`; SHA-256 `b14b15881cc00c3ccfcc94552ce7c5dd008ef8229241fd773b9b4302673e05f1`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/simpleSettings/SimpleAutoRetestSettingsCtrl.js`; SHA-256 `0e636ec4aab187b0b84e9d983525e1304f323ae814505d59bf371731291977d3`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/simpleSettings/simpleSettings.html`; SHA-256 `234c98fe80d307e74f22a741354f1cb2465b55d6b7940fa5911022879fbfe914`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/task.xml`; SHA-256 `d74c1062bac64a7b1efa970104bd2c0a10279e05a2ed2493c1bf3ae0a70cebc4`.

### TaskCallExternalScript

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/CallExternalScript/CallExternalScript.java`; SHA-256 `fbdc739bf567d7cb3f888c66958ae450af2b317fea54f7cdc22afb796ca846f6`.
  - Declared callables: `CallExternalScript()`; `CallExternalScript(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `run()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/module.js`; SHA-256 `654b69ca0fca8782d16402fcf24549a2f3d762c4f0c986f4710e5175999a54e5`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/simpleSettings/SimpleCallExternalScriptSettingsCtrl.js`; SHA-256 `5d3227119368f1a2429a68e7fb9fe3eece645c9ad8deef85aa74547b9371e881`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/simpleSettings/simpleSettings.html`; SHA-256 `9eef6056b528ebae2cd64e785fcbdd2dee955a72458f69bbc17b73ecb783153e`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/task.xml`; SHA-256 `34c0048e0cff65a8208a7faa7ebbc77c9ba5a24209188e5ee882ad25c2ec79e3`.

### TaskCreatePortfolio

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/CreatePortfolio/CreatePortfolio.java`; SHA-256 `0bf15cbf684122b4ba5e764f9d967884a55f62dc3ab0eb06f23226d4ccc2ebf9`.
  - Declared callables: `CreatePortfolio()`; `CreatePortfolio(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/module.js`; SHA-256 `baa5901eab5d48e27d3418f3d451b9327aa75bee1cd0b5470d3df9dcc803ea2a`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/simpleSettings/SimpleCreatePortfolioSettingsCtrl.js`; SHA-256 `044912c1b37c2c542551be50d1398a2e97d0f8b325648deeb48fe526a51e4d65`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/simpleSettings/simpleSettings.html`; SHA-256 `97102968bef8b67b190e1586cae3b0c99925b3540178b6e6d6336a3ebef16995`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/task.xml`; SHA-256 `319f99428bc3297b40dbe06e75248248df67c4e4e98566405e1e18fce110b310`.

### TaskCustomAnalysis

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/CustomAnalysis/CustomAnalysisTask.java`; SHA-256 `28a7efcf2d35c20d835804942105fec196847cdd5c8b40afc42b2759a242dc31`.
  - Declared callables: `CustomAnalysisTask()`; `CustomAnalysisTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/module.js`; SHA-256 `0a0a186115c3853d715aae7da15f666cf3018fb28864213f4e764d4d25951385`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/simpleSettings/simpleSettings.html`; SHA-256 `2af34069872be309652b35232021b6ee72aac38b8032e9ebfc14292ee42d40cd`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/simpleSettings/SimpleSettingsCACtrl.js`; SHA-256 `cc570659788ccf923b4818e817d52e7e91057d4eb61b85f9b9db77ba888d002a`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/task.xml`; SHA-256 `02d69a28d4f65098d5969788fa1c84a872f5ede7d701647914055febd10c6e76`.

### TaskFiltering

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskFiltering/Filtering/FilteringTask.java`; SHA-256 `3131fb3eae2f31ce5c244918edb93be8c19b15cc0042a29892017ef97ccdf583`.
  - Declared callables: `FilteringTask()`; `FilteringTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskFiltering/module.js`; SHA-256 `e4b5da6dfcda2cdcda075943f5441f254caa906d864317b244424db62c675242`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskFiltering/simpleSettings/SimpleFilteringSettingsCtrl.js`; SHA-256 `99b284873c178be00c2a108ee90dce9f3e6c05ec3a7e8bc3a51db69f28b481d7`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskFiltering/simpleSettings/simpleSettings.html`; SHA-256 `d284effcb302c0ed4379b0072c726e3d49e46f736f3032837faa8c6eee28415d`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskFiltering/task.xml`; SHA-256 `2d20ba16f5331cd82b6986bfb5e747a7a5c2f77131801e3822a0b07fa17f044e`.

### TaskGoToTask

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskGoToTask/GoToTask/GoToTask.java`; SHA-256 `2f88c30a8527af2bd9e08067acf00a33081c8ff73c19234f63c01e1d06d530b4`.
  - Declared callables: `GoToTask()`; `GoToTask(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`; `getCustomValue(String key)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskGoToTask/module.js`; SHA-256 `c0c8e07ce0b20b5e88ae04f553aa6ad0acd736fb573b5d01dd055b07ea333d87`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskGoToTask/simpleSettings/SimpleGoToTaskSettingsCtrl.js`; SHA-256 `b2360a3d0446f38dc79dd13d400caeb7e0e65a4cf1e2c811e227f752b787b59e`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskGoToTask/simpleSettings/simpleSettings.html`; SHA-256 `7323aab26a71f51c53adb05ffe50eb9d2e9bb2da04bd96ec7d1f6c49ec2cd0db`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskGoToTask/task.xml`; SHA-256 `6f02d0568c9f8484aa5b980882041d082dd4c10eb10259be355a5a44ff2c5da0`.

### TaskLoadFromFiles

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/LoadFromFiles/LoadFromFiles.java`; SHA-256 `cda7750f2045819cb0e3377c47bd723ede5220e5219430f0c9401eff51331f2f`.
  - Declared callables: `LoadFromFiles()`; `LoadFromFiles(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/module.js`; SHA-256 `3e7397a734b754d9bbbb8bfe234982425ce0439485b292c8333b9bd1fa9ae805`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/simpleSettings/SimpleLoadFromFilesSettingsCtrl.js`; SHA-256 `b205ced710611053ce614b393608989804629fc1e0790735b6eeb20c99db122e`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/simpleSettings/simpleSettings.html`; SHA-256 `34f5e23f1dd6e4b9f188e045fb4c8a65d239dd0b2cf048de785d8d0e4593817a`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/task.xml`; SHA-256 `04f417507c5046672164c5797e48bf6e1a93013af24d2ab3f7d947d79fe3191b`.

### TaskLogDatabankStats

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/LogDatabankStats/LogDatabankStatsTask.java`; SHA-256 `e4a7b160ea044a1d872c0f6ede8bad12bd5690f2a0b4c8141b119aac181750ca`.
  - Declared callables: `LogDatabankStatsTask()`; `LogDatabankStatsTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/module.js`; SHA-256 `e160656a8201596c0b36df7b13044432aeccc32592ff5553c6d0d0de99186bad`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/simpleSettings/SimpleLogDatabankStatsSettingsCtrl.js`; SHA-256 `a771927e5531de7c98ffcfc727d51c0a2e823a4b7e752331ae58c90c4a48794f`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/simpleSettings/simpleSettings.html`; SHA-256 `64dfe2ec32995d7b389331b7165d24369f0403ae3a9ff809094b6620124c5b5f`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/task.xml`; SHA-256 `c4dd7269edd3725ff83c5db4e0bdc9dbd52c6134f4b643bc3d67730729fed049`.

### TaskManagerProjects

Owner: `12-AppTaskManager.md`. Readable Java matches: 2; primary frontend/settings files: 10.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/Projects/TMProjectsPlugin.java`; SHA-256 `ea8fcc27cf6b71acf4a0bcad5ee3da11196ea52e28326cab635c1e9b0e5dc5e8`.
  - Declared callables: `getHandler()`; `getProduct()`; `getPreferredPosition()`; `initPlugin()`; `call(String methodName, Object ... parameters)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/Projects/TMProjectsServlet.java`; SHA-256 `09244afbabf5b850a36304783e842907306686251838395c6ac1364403ff7ee8`.
  - Declared callables: `execute(String command, Map<String, String[]> parameterMap, String method)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/directives/tmProjectControl.html`; SHA-256 `cc75487257f347d137223f1e5502b4e9cf0e428da77df37e62445cef7d7c245b`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/directives/TMProjectControl.js`; SHA-256 `add28dc6d283796f5c0348b5697c4ec84b64101381c5a4d513c0a63b399c3cbf`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/directives/TMProjectControlCtrl.js`; SHA-256 `a175b4a5eb8c37c8337a620a66e593486b4fdf60c8a42ba9368eed0398b95bf4`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/module.js`; SHA-256 `c5958859543b75418a9611b02e6eec5718ef08a54650f4d79a6ce9b359f535c4`.

### TaskManagerTasks

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 11.

- Source: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/taskImpl/AbstractTask.java`; SHA-256 `43ea5a49a82e293afd5e8063358fe320fd882ebd2809aba448bb95c10f1e91a0`.
  - Declared callables: `AbstractTask(String string, ProgressEngine progressEngine)`; `getProduct()`; `getDefaultConfig(String string)`; `isActive()`; `setActive(boolean bl)`; `getCustomName()`; `setCustomName(String string)`; `setTitle(String string)`; `getTitle()`; `setConfigFileName(String string)`; `getTaskXMLFileName()`; `getSettingsData()`; `setConfig(Element element, boolean bl, boolean bl2)`; `getConfig()`. Further methods remain in the named source.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/copyFromTaskPopup.html`; SHA-256 `70b8ca9c1df3296e1d89a7a69e5e886a2147b40bc3a3af3f4153ab30c5b7953b`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/copyToTasksPopup.html`; SHA-256 `17a56026c0f742fcc28a4e5fc9ff68e1fe468002f60e85a54a201fd07682e6cb`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/directives/tmtask/tmtask.html`; SHA-256 `cb0a03f1ee469826ba3cdf11eb15d93501af61c7fdb3b5086e741d01118c1127`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/module.js`; SHA-256 `76735c18dd2cb2b8cdf7f2c5e836a95295a787513ef187943a7b20e835561ce9`.

### TaskNotification

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 5.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNotification/Notification/NotificationTask.java`; SHA-256 `a31530151095f265e5de116df22d5424bc6d570170fb236a2fcbc55131b40ea8`.
  - Declared callables: `NotificationTask()`; `NotificationTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNotification/module.js`; SHA-256 `d0a34ad25807b4d7a0bbaf07c84ca8e05f873c259a245c972dea53c14ade089b`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNotification/simpleSettings/SimpleNotificationSettingsCtrl.js`; SHA-256 `10f43010b2d1001e7b9f2a73bf2b5d748971c7ce24625f9503bb2a13ddc796a7`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNotification/simpleSettings/simpleSettings.html`; SHA-256 `b95a406a600a14c4bec0986ae7b198e0944d6d94c95cc1b5815093bd99dd9079`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNotification/task.xml`; SHA-256 `a94af7d688f6844f9445cd6f5b5594da976bb57eb2c682cb5d646ff7d799ca75`.

### TaskSaveToFiles

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/SaveToFiles/SaveToFiles.java`; SHA-256 `a79aea10d7cb0220f42c8ecf2251d57aa0db1536ab1a5fc2a2655002d60c9b26`.
  - Declared callables: `SaveToFiles()`; `SaveToFiles(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/module.js`; SHA-256 `c9cb10f6ec682184fb181a2135e8ec44444e2a4be6d18dc22a3fec805d24e732`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/simpleSettings/SimpleSaveToFilesSettingsCtrl.js`; SHA-256 `7db8fd26bc34fef62e33f1fb956dfc4b12dfc0a2661d7531e53889cd87a3b8dc`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/simpleSettings/simpleSettings.html`; SHA-256 `29abef3ac144bafeaf2e3c0d63cd5420badbe1b31df838bec2c30861c375c589`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/task.xml`; SHA-256 `755cdd93f3ea41aabccd1c46bc9ff6f6c6c3e8da229ea99177f21c859af200fd`.

### TaskStopAndStart

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/StopAndStart/StopAndStartTask.java`; SHA-256 `5c7ac14bb46405ac025c8ab7a4b4220bd6bdcad4c9fa828b3da871a77d523a6f`.
  - Declared callables: `StopAndStartTask()`; `StopAndStartTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/module.js`; SHA-256 `36a1806a4a0a12c874f75ad8de08410861fd5fbdf67b55534e790b8fe2d43f95`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/simpleSettings/simpleSettings.html`; SHA-256 `01e647c2e8b6d802f84e6ebcdd3308b0667813673cdbe47470939fae92d139e7`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/simpleSettings/SimpleStopAndStartSettingsCtrl.js`; SHA-256 `c6e359113323c88a8a1cae6b92957154e20e9be384e3976a8574f0a0fffdea50`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/task.xml`; SHA-256 `0339a8c062c5df2d9b8f2786f2a313fda6c63299c43a553f042614236ed02b95`.

### TaskUpdateData

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskUpdateData/UpdateData/UpdateDataTask.java`; SHA-256 `f820e5a1d16faccb4f22c6666827027c5a4ae9c4cd65100ba2952eebabb2e73c`.
  - Declared callables: `UpdateDataTask()`; `UpdateDataTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `run()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskUpdateData/module.js`; SHA-256 `6b5c46afbfefd93e18b12391ea927f4f359c9a2a0cbc67183737d986936d2664`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskUpdateData/simpleSettings/simpleSettings.html`; SHA-256 `aafc67860b1d0707c72c1f3af2ac7c979caa02efc259ee0304daf1812f572620`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskUpdateData/simpleSettings/SimpleUpdateDataSettingsCtrl.js`; SHA-256 `5f9eac23690046263e4dad65d48db57910a02875206b91404e2a9a544cf016ef`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskUpdateData/task.xml`; SHA-256 `d2e8ecbb6745db9d1872cdfb699fceb8593e943a2bf3b351e3286c2b7467bfc5`.

### TaskWaitFor

Owner: `12-AppTaskManager.md`. Readable Java matches: 1; primary frontend/settings files: 4.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskWaitFor/WaitFor/WaitForTask.java`; SHA-256 `66812a35a906a4ace9bd2619d10b090187aa72c7ff742fa0316b5698b24dac95`.
  - Declared callables: `WaitForTask()`; `WaitForTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `run()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `logTaskFinished(ProjectGlobalLog log)`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskWaitFor/module.js`; SHA-256 `3f0bab382c802eb24d4d63b29fcc84bd3408d35d061714a0a55053c0c59a4fc8`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskWaitFor/simpleSettings/simpleSettings.html`; SHA-256 `79ecc8e616093e029b8de22ff594518e0cea8c47c02718ff60103abe2bee6d79`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskWaitFor/simpleSettings/SimpleWaitForSettingsCtrl.js`; SHA-256 `38d8e2bcf3f08773093cf5978ebe455d0bab4e8c857641077bcf29750aec9263`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskWaitFor/task.xml`; SHA-256 `1310f5262061d691d6cb25fd3c9e4208eb9d47ff4c524e450df93d697fbfae72`.

### AppNeuralNetwork

Owner: `13-AppNeuralNetwork.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/module.js`; SHA-256 `f6583b2e635bbb7bb4b5d93967443003f4bf0bb81c32ba25c295a3cb1c0dc08d`.

### TaskNeuralNetworkTrainer

Owner: `13-AppNeuralNetwork.md`. Readable Java matches: 1; primary frontend/settings files: 1.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/NeuralNetworkTrainer/NeuralNetworkTrainerTask.java`; SHA-256 `55bb85d91af750d92fb6601394d69a576a76f5afbbbd1b94967b6550e7d9e680`.
  - Declared callables: `NeuralNetworkTrainerTask()`; `NeuralNetworkTrainerTask(String projectName, ProgressEngine progressEngine)`; `getType()`; `getName()`; `clone(String projectName, ProgressEngine progressEngine)`; `start()`; `getRunningStatus()`; `getPluginFolderName()`; `getPreferredPosition()`; `getSettings()`; `getUsedDatabanks()`; `getOutputDatabank()`; `getProduct()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/task.xml`; SHA-256 `0cf8b5e2eb9929ecc1f21c5bfba6afc97751b362ba2eaa92ef2ec707bae81041`.

**Inspected behavior:** `start()` is empty; `getRunningStatus()` returns 0; used/output databanks return null; settings are Data, Options, Rankings, Notes. This source does not implement a training algorithm. A feature-complete trainer would be a new product design, not a port of an observed donor trainer.

### AppGridControl

Owner: `14-AppGridControl.md`. Readable Java matches: 1; primary frontend/settings files: 1.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppGridControl/GridControl/GridControlAppPlugin.java`; SHA-256 `3c25bb56f76c182daa0d0e57b9af448c47a6405e3392fa1704977e465ed533bc`.
  - Declared callables: `getName()`; `getProduct()`; `getPreferredPosition()`; `initPlugin()`; `getContextPath()`; `getAppCode()`; `getTooltip()`; `getProject()`; `getDefaultTaskType()`; `getDefaultTaskName()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppGridControl/module.js`; SHA-256 `e06bdb9cd08473a6b65c6bee52edc583a0055739d18c3549dc63921a6871f7c3`.

### ServletGridControl

Owner: `14-AppGridControl.md`. Readable Java matches: 0; primary frontend/settings files: 0.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.


### AppGridTest

Owner: `15-AppGridTest.md`. Readable Java matches: 1; primary frontend/settings files: 1.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppGridTest/GridTest/GridTestAppPlugin.java`; SHA-256 `19c508b8144d9e2b53577a5d2b3464ab2a927e71cc63ff54e9d5119e4302912d`.
  - Declared callables: `getName()`; `getProduct()`; `getPreferredPosition()`; `initPlugin()`; `getContextPath()`; `getAppCode()`; `getTooltip()`; `getProject()`; `getDefaultTaskType()`; `getDefaultTaskName()`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppGridTest/module.js`; SHA-256 `8ab8c8d4a46f5c3e75bc5ee9981b362b1bbad8c23a763f65696bf60bc09d1eca`.

### AppDebugConsole

Owner: `16-AppDebugConsole.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppDebugConsole/module.js`; SHA-256 `6fc31f74c126449249cc7ecc5527e75a7c9486fcc8e8151c47c6800d4a8ed4b5`.

### AppMarketplace

Owner: `17-AppMarketplace.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppMarketplace/module.js`; SHA-256 `ea09b766ed8b526b55864dbf54318e9b9ea9342e342b9f723207b024295f0f78`.

### AppSQXBusiness

Owner: `18-AppBusiness.md`. Readable Java matches: 0; primary frontend/settings files: 1.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/module.js`; SHA-256 `04e3576aee5440496a31b48db1933d75f5c7072ad1bb5fa8a6bea5034f235902`.

### ServletMCP

Owner: `19-AppAI.md`. Readable Java matches: 0; primary frontend/settings files: 0.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.


### ServletSQAI

Owner: `19-AppAI.md`. Readable Java matches: 0; primary frontend/settings files: 2.

No matching plugin Java body was found in the bounded library/recovered-source search. This contribution may be frontend-only. Review its listed UI handlers and their actual backend dependencies before declaring a missing server; a similarly named core library class does not establish that dependency.

- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ServletSQAI/module.js`; SHA-256 `0244551ff80e4c4074dc4c4eab12daacb4952f6790a1864b73aec3bc20161d00`.
- Source: `DONOR_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`; SHA-256 `56a3cf0a35b491ad5e2c2a63f834109753c258f2db267890db6d08f90f95d07d`.
