# TaskRetest.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar`.
- SHA-256: `1e1b514c469b07e5aa5a50895caaf1bdfe7323abe7817e810dfe22077eb50193`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **4**; non-nested: **2**; nested/anonymous: **2**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `Retester` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.Task.impl.Retest`

```mermaid
classDiagram
    class C0f287be7937f["RetestJob"] {
        +Log
        -backtestRunner
        -project
        +call()
        +messageReceived()
    }
    class Cc2acf006d555["RetestTask"] {
        +Log
        -LOCK_RETEST_TASK
        -projectRunInfo
        +beforeStart()
        +start()
        #progressStatusChanged()
        +onStatusChanged()
    }
    class Ce0cb23611851["StockDto"]
    class C2d5349dc1f49["GridClient"]
    class C729a56512564["GridJob"]
    class C044e39d2df83["BacktestRunner"]
    class C1295ffcc9568["ILastEventListener"]
    class C7126b816a5a1["IProgressStatusListener"]
    class C8241bc919d95["SQProject"]
    class Ce44d386802cb["AbstractTask"]
    C729a56512564 <|-- C0f287be7937f : declared extends
    C0f287be7937f ..> C044e39d2df83 : field type
    C0f287be7937f ..> C8241bc919d95 : field type
    Ce44d386802cb <|-- Cc2acf006d555 : declared extends
    C7126b816a5a1 <|.. Cc2acf006d555 : declared interface
    C1295ffcc9568 <|.. Cc2acf006d555 : declared interface
    Cc2acf006d555 ..> Ce0cb23611851 : field type
    Cc2acf006d555 ..> C2d5349dc1f49 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Ce0cb23611851` | [`com.strategyquant.datalib.basket.StockDto`](../Shared/SQDataLib.md) | referenced external type |
| `C2d5349dc1f49` | [`com.strategyquant.gridlib.client.GridClient`](../Shared/SQGridLib2.md) | referenced external type |
| `C729a56512564` | [`com.strategyquant.gridlib.client.GridJob`](../Shared/SQGridLib2.md) | referenced external type |
| `C0f287be7937f` | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` (this JAR) | this diagram |
| `Cc2acf006d555` | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` (this JAR) | this diagram |
| `C044e39d2df83` | [`com.strategyquant.tradinglib.backtestrunner.BacktestRunner`](../Shared/SQTradingLib.md) | referenced external type |
| `C1295ffcc9568` | [`com.strategyquant.tradinglib.project.ILastEventListener`](../Shared/SQTradingLib.md) | referenced external type |
| `C7126b816a5a1` | [`com.strategyquant.tradinglib.project.IProgressStatusListener`](../Shared/SQTradingLib.md) | referenced external type |
| `C8241bc919d95` | [`com.strategyquant.tradinglib.project.SQProject`](../Shared/SQTradingLib.md) | referenced external type |
| `Ce44d386802cb` | [`com.strategyquant.tradinglib.taskImpl.AbstractTask`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | class | non-nested |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | class | non-nested |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` | class | nested/anonymous |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.gridlib.client.GridJob`](../Shared/SQGridLib2.md) | extends | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / class declaration: `public class com.strategyquant.plugin.Task.impl.Retest.RetestJob extends com.strategyquant.gridlib.client.GridJob<com.strategyquant.tradinglib.backtestrunner.BacktestResult>` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.tradinglib.backtestrunner.BacktestRunner`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / field declaration: `private com.strategyquant.tradinglib.backtestrunner.BacktestRunner backtestRunner;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.tradinglib.project.SQProject`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / field declaration: `private com.strategyquant.tradinglib.project.SQProject project;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / field declaration: `private java.lang.String strategyName;`<br>`private java.lang.String note;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `java.io.Serializable` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.tradinglib.project.StopPauseEngine`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.tradinglib.project.ILastEventListener`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.backtestrunner.BacktestResult call() throws java.lang.Exception;`<br>`public java.lang.Object call() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.tradinglib.backtestrunner.BacktestResult`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public com.strategyquant.tradinglib.backtestrunner.BacktestResult call() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | [`com.strategyquant.gridlib.client.GridMessage`](../Shared/SQGridLib2.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public void messageReceived(com.strategyquant.gridlib.client.GridMessage);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestJob` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` / method signature: `public java.lang.Object call() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.taskImpl.AbstractTask`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / class declaration: `public class com.strategyquant.plugin.Task.impl.Retest.RetestTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask implements com.strategyquant.tradinglib.project.IProgressStatusListener,com.strategyquant.tradinglib.project.ILastEventListener` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.project.IProgressStatusListener`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / class declaration: `public class com.strategyquant.plugin.Task.impl.Retest.RetestTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask implements com.strategyquant.tradinglib.project.IProgressStatusListener,com.strategyquant.tradinglib.project.ILastEventListener` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.project.ILastEventListener`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / class declaration: `public class com.strategyquant.plugin.Task.impl.Retest.RetestTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask implements com.strategyquant.tradinglib.project.IProgressStatusListener,com.strategyquant.tradinglib.project.ILastEventListener` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private static final java.lang.String LOCK_RETEST_TASK;`<br>`private java.util.ArrayList<java.lang.String> databankRecordKeys;`<br>`private java.lang.String jobGroupID;`<br>`private java.lang.String lastSettingsXml;`<br>`private java.lang.String caInputArgs;`<br>`private java.lang.String currentBasketDatabankRecordKey;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`private java.util.Map<java.lang.String, java.io.Serializable> getParams(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;`<br>`private void printNewStrategyToLog(com.strategyquant.gridlib.client.JobDetails, java.lang.String, java.lang.String, com.strategyquant.tradinglib.backtestrunner.DurationStats);`<br>`public java.lang.String getType();`<br>`public java.lang.String getPluginFolderName();`<br>`public java.lang.String getName();`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public java.lang.String[] getSettings();`<br>`public void setLastEvent(java.lang.String);`<br>`public java.lang.String getProduct();` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.ProjectRunInfo`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.ProjectRunInfo projectRunInfo;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.Databank inputDatabank;`<br>`private com.strategyquant.tradinglib.Databank outputDatabank;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `protected com.strategyquant.tradinglib.Databank[] getUsedDatabanks();`<br>`protected com.strategyquant.tradinglib.Databank getOutputDatabank();` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.ArrayList<java.lang.String> databankRecordKeys;`<br>`private java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition> conditions;`<br>`private java.util.ArrayList<com.strategyquant.tradinglib.crosscheck.ICrossCheck> crossChecks;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.util.concurrent.atomic.AtomicInteger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.concurrent.atomic.AtomicInteger lastFinishedIndex;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.gridlib.client.GridClient`](../Shared/SQGridLib2.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.gridlib.client.GridClient gridClient;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.CommissionsMethod`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.CommissionsMethod commission;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.SwapMethod`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.SwapMethod swap;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.exception.TaskErrorInfo`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.exception.TaskErrorInfo taskErrorInfo;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.options.TradingOptions`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.options.TradingOptions tradingOptions;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.ATM`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.ATM atm;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.conditions.Condition`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition> conditions;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.crosscheck.ICrossCheck`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.ArrayList<com.strategyquant.tradinglib.crosscheck.ICrossCheck> crossChecks;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.util.Timer` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.Timer jobsCreationTimer;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.CustomAnalysisMethod`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private com.strategyquant.tradinglib.CustomAnalysisMethod caMethod;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.util.List` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.List<com.strategyquant.datalib.basket.StockDto> currentBasketStocks;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.datalib.basket.StockDto`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / field declaration: `private java.util.List<com.strategyquant.datalib.basket.StockDto> currentBasketStocks;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.datalib.basket.StockDto`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private com.strategyquant.plugin.Task.impl.Retest.RetestJob createJobForStock(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.datalib.basket.StockDto) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestTask() throws java.lang.Exception;`<br>`public com.strategyquant.plugin.Task.impl.Retest.RetestTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public boolean beforeStart() throws java.lang.Exception;`<br>`private void initializeBacktestData() throws java.lang.Exception;`<br>`public void start() throws java.lang.Exception;`<br>`private synchronized void createSerialJobs() throws java.lang.Exception;`<br>`private synchronized void submitNextJob() throws java.lang.Exception;`<br>`private synchronized boolean createNewBatch(int) throws java.lang.Exception;`<br>`private com.strategyquant.plugin.Task.impl.Retest.RetestJob createJobForStock(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.datalib.basket.StockDto) throws java.lang.Exception;`<br>`private java.util.Map<java.lang.String, java.io.Serializable> getParams(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;`<br>`private void initParams() throws org.jdom2.JDOMException, java.io.IOException, java.lang.Exception;`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`static boolean access$100(com.strategyquant.plugin.Task.impl.Retest.RetestTask, int) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.project.ProgressEngine`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `public com.strategyquant.plugin.Task.impl.Retest.RetestTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `com.strategyquant.plugin.Task.impl.Retest.RetestJob` (this JAR) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private com.strategyquant.plugin.Task.impl.Retest.RetestJob createJobForStock(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.datalib.basket.StockDto) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private com.strategyquant.plugin.Task.impl.Retest.RetestJob createJobForStock(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.datalib.basket.StockDto) throws java.lang.Exception;`<br>`private java.util.Map<java.lang.String, java.io.Serializable> getParams(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private java.util.Map<java.lang.String, java.io.Serializable> getParams(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.io.Serializable` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private java.util.Map<java.lang.String, java.io.Serializable> getParams(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `org.jdom2.JDOMException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private void initParams() throws org.jdom2.JDOMException, java.io.IOException, java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | `java.io.IOException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private void initParams() throws org.jdom2.JDOMException, java.io.IOException, java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.gridlib.client.GridMessage`](../Shared/SQGridLib2.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `protected void processMessage(com.strategyquant.gridlib.client.GridMessage);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.gridlib.client.JobDetails`](../Shared/SQGridLib2.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private void printNewStrategyToLog(com.strategyquant.gridlib.client.JobDetails, java.lang.String, java.lang.String, com.strategyquant.tradinglib.backtestrunner.DurationStats);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.backtestrunner.DurationStats`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `private void printNewStrategyToLog(com.strategyquant.gridlib.client.JobDetails, java.lang.String, java.lang.String, com.strategyquant.tradinglib.backtestrunner.DurationStats);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask` | [`com.strategyquant.tradinglib.project.ProjectGlobalLog`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` / method signature: `public void logTaskFinished(com.strategyquant.tradinglib.project.ProjectGlobalLog);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` | [`com.strategyquant.gridlib.client.IGridMessageListener`](../Shared/SQGridLib2.md) | implements | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` / class declaration: `class com.strategyquant.plugin.Task.impl.Retest.RetestTask$1 implements com.strategyquant.gridlib.client.IGridMessageListener` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` (this JAR) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` / field declaration: `final com.strategyquant.plugin.Task.impl.Retest.RetestTask this$0;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` (this JAR) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` / method signature: `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1(com.strategyquant.plugin.Task.impl.Retest.RetestTask);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` | [`com.strategyquant.gridlib.client.GridMessage`](../Shared/SQGridLib2.md) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$1` / method signature: `public void messageReceived(com.strategyquant.gridlib.client.GridMessage);` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` | `java.util.TimerTask` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` / class declaration: `class com.strategyquant.plugin.Task.impl.Retest.RetestTask$2 extends java.util.TimerTask` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` (this JAR) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` / field declaration: `final com.strategyquant.plugin.Task.impl.Retest.RetestTask this$0;` |
| `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` | `com.strategyquant.plugin.Task.impl.Retest.RetestTask` (this JAR) | type dependency | `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2` / method signature: `com.strategyquant.plugin.Task.impl.Retest.RetestTask$2(com.strategyquant.plugin.Task.impl.Retest.RetestTask);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Task.impl.Retest.RetestJob</summary>

```text
public class com.strategyquant.plugin.Task.impl.Retest.RetestJob extends com.strategyquant.gridlib.client.GridJob<com.strategyquant.tradinglib.backtestrunner.BacktestResult>
    public static final org.slf4j.Logger Log;
    private com.strategyquant.tradinglib.backtestrunner.BacktestRunner backtestRunner;
    private com.strategyquant.tradinglib.project.SQProject project;
    private java.lang.String strategyName;
    private java.lang.String note;
    public com.strategyquant.plugin.Task.impl.Retest.RetestJob(java.lang.String, java.util.Map<java.lang.String, java.io.Serializable>, com.strategyquant.tradinglib.project.StopPauseEngine, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;
    public com.strategyquant.tradinglib.backtestrunner.BacktestResult call() throws java.lang.Exception;
    public void messageReceived(com.strategyquant.gridlib.client.GridMessage);
    public java.lang.Object call() throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Task.impl.Retest.RetestTask</summary>

```text
public class com.strategyquant.plugin.Task.impl.Retest.RetestTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask implements com.strategyquant.tradinglib.project.IProgressStatusListener,com.strategyquant.tradinglib.project.ILastEventListener
    public static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_RETEST_TASK;
    private com.strategyquant.tradinglib.ProjectRunInfo projectRunInfo;
    private com.strategyquant.tradinglib.Databank inputDatabank;
    private com.strategyquant.tradinglib.Databank outputDatabank;
    private java.util.ArrayList<java.lang.String> databankRecordKeys;
    private int lastProcessedIndex;
    private java.util.concurrent.atomic.AtomicInteger lastFinishedIndex;
    private com.strategyquant.gridlib.client.GridClient gridClient;
    private java.lang.String jobGroupID;
    private long jobCount;
    private double slippage;
    private double minDistance;
    private com.strategyquant.tradinglib.CommissionsMethod commission;
    private com.strategyquant.tradinglib.SwapMethod swap;
    private int dismissBadStrategies;
    private boolean warningsBadStrategies;
    private com.strategyquant.tradinglib.exception.TaskErrorInfo taskErrorInfo;
    private com.strategyquant.tradinglib.options.TradingOptions tradingOptions;
    private com.strategyquant.tradinglib.ATM atm;
    private java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition> conditions;
    private int retestBatchSize;
    private int originalRetestBatchSize;
    private long projectStartTime;
    private boolean useCrossChecks;
    private boolean evaluateAllCrossChecks;
    private java.util.ArrayList<com.strategyquant.tradinglib.crosscheck.ICrossCheck> crossChecks;
    private boolean deleteFailedStrategies;
    private boolean forceRunCrossChecks;
    private boolean singleThreadedOptimizations;
    private java.lang.String lastSettingsXml;
    private java.util.Timer jobsCreationTimer;
    private int backtestMode;
    private boolean createsSubJobs;
    private com.strategyquant.tradinglib.CustomAnalysisMethod caMethod;
    private java.lang.String caInputArgs;
    private boolean caFilter;
    private java.lang.String currentBasketDatabankRecordKey;
    private int currentBasketStockIndex;
    private java.util.List<com.strategyquant.datalib.basket.StockDto> currentBasketStocks;
    public com.strategyquant.plugin.Task.impl.Retest.RetestTask() throws java.lang.Exception;
    public com.strategyquant.plugin.Task.impl.Retest.RetestTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;
    public boolean beforeStart() throws java.lang.Exception;
    private void recognizeCustomAnalysisMethod();
    private void loadRecordKeys();
    private void recognizeBacktestMode();
    private void initializeBacktestData() throws java.lang.Exception;
    private void computeOptimalBatchSize();
    public void start() throws java.lang.Exception;
    private synchronized void createSerialJobs() throws java.lang.Exception;
    private synchronized void submitNextJob() throws java.lang.Exception;
    private synchronized boolean createNewBatch(int) throws java.lang.Exception;
    private com.strategyquant.plugin.Task.impl.Retest.RetestJob createJobForStock(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.datalib.basket.StockDto) throws java.lang.Exception;
    private void updateBasketIndex(int);
    private java.util.Map<java.lang.String, java.io.Serializable> getParams(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;
    private void initParams() throws org.jdom2.JDOMException, java.io.IOException, java.lang.Exception;
    protected void progressStatusChanged(int);
    private void retestFinished();
    public void onStatusChanged(int);
    protected void processMessage(com.strategyquant.gridlib.client.GridMessage);
    protected void checkAllFinished();
    private void printNewStrategyToLog(com.strategyquant.gridlib.client.JobDetails, java.lang.String, java.lang.String, com.strategyquant.tradinglib.backtestrunner.DurationStats);
    public java.lang.String getType();
    public java.lang.String getPluginFolderName();
    public java.lang.String getName();
    public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;
    public int getPreferredPosition();
    public java.lang.String[] getSettings();
    protected int getRunningStatus();
    protected com.strategyquant.tradinglib.Databank[] getUsedDatabanks();
    protected com.strategyquant.tradinglib.Databank getOutputDatabank();
    public void logTaskFinished(com.strategyquant.tradinglib.project.ProjectGlobalLog);
    public void setLastEvent(java.lang.String);
    public java.lang.String getProduct();
    static int access$000(com.strategyquant.plugin.Task.impl.Retest.RetestTask);
    static boolean access$100(com.strategyquant.plugin.Task.impl.Retest.RetestTask, int) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Task.impl.Retest.RetestTask$1</summary>

```text
class com.strategyquant.plugin.Task.impl.Retest.RetestTask$1 implements com.strategyquant.gridlib.client.IGridMessageListener
    final com.strategyquant.plugin.Task.impl.Retest.RetestTask this$0;
    com.strategyquant.plugin.Task.impl.Retest.RetestTask$1(com.strategyquant.plugin.Task.impl.Retest.RetestTask);
    public void messageReceived(com.strategyquant.gridlib.client.GridMessage);
```

</details>

<details>
<summary>com.strategyquant.plugin.Task.impl.Retest.RetestTask$2</summary>

```text
class com.strategyquant.plugin.Task.impl.Retest.RetestTask$2 extends java.util.TimerTask
    final com.strategyquant.plugin.Task.impl.Retest.RetestTask this$0;
    com.strategyquant.plugin.Task.impl.Retest.RetestTask$2(com.strategyquant.plugin.Task.impl.Retest.RetestTask);
    public void run();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
