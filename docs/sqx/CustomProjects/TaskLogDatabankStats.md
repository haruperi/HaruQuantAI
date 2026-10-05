# TaskLogDatabankStats.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar`.
- SHA-256: `2a903db425c206f8ffaa3c22a97cca1f95fbde6379caf12f970c7954fd228188`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **1**; non-nested: **1**; nested/anonymous: **0**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `CustomProjects` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.Task.impl.LogDatabankStats`

```mermaid
classDiagram
    class C956f396d1f50["LogDatabankStatsTask"] {
        -logMessage
        -databank
        -logStats
        +getType()
        +getName()
        +clone()
        +start()
    }
    class Cf1cf5abc550f["Databank"]
    class Ce7e1597aada5["ConditionsChecker"]
    class Ce44d386802cb["AbstractTask"]
    Ce44d386802cb <|-- C956f396d1f50 : declared extends
    C956f396d1f50 ..> Cf1cf5abc550f : field type
    C956f396d1f50 ..> Ce7e1597aada5 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C956f396d1f50` | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` (this JAR) | this diagram |
| `Cf1cf5abc550f` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | referenced external type |
| `Ce7e1597aada5` | [`com.strategyquant.tradinglib.conditions.ConditionsChecker`](../Shared/SQTradingLib.md) | referenced external type |
| `Ce44d386802cb` | [`com.strategyquant.tradinglib.taskImpl.AbstractTask`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.taskImpl.AbstractTask`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / class declaration: `public class com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / field declaration: `private java.lang.String logMessage;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `public com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public java.lang.String getType();`<br>`public java.lang.String getName();`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;`<br>`public java.lang.String getPluginFolderName();`<br>`public java.lang.String[] getSettings();` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / field declaration: `private com.strategyquant.tradinglib.Databank databank;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `protected com.strategyquant.tradinglib.Databank[] getUsedDatabanks();`<br>`protected com.strategyquant.tradinglib.Databank getOutputDatabank();` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / field declaration: `private java.util.ArrayList<java.lang.Object[]> logStats;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;`<br>`private boolean checkConditions(com.strategyquant.tradinglib.ResultsGroup, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>);` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / field declaration: `private java.util.ArrayList<java.lang.Object[]> logStats;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.conditions.ConditionsChecker`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / field declaration: `private com.strategyquant.tradinglib.conditions.ConditionsChecker conditionsChecker;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `public com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask() throws java.lang.Exception;`<br>`public com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`private void init() throws java.lang.Exception;`<br>`public void start() throws java.lang.Exception;`<br>`private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.project.ProgressEngine`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `public com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.conditions.Condition`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;`<br>`private boolean checkConditions(com.strategyquant.tradinglib.ResultsGroup, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>);` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.conditions.IConditionValue`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;`<br>`private boolean checkConditions(com.strategyquant.tradinglib.ResultsGroup, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>);` |
| `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` | [`com.strategyquant.tradinglib.project.ProjectGlobalLog`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask` / method signature: `public void logTaskFinished(com.strategyquant.tradinglib.project.ProjectGlobalLog);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask</summary>

```text
public class com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask
    private java.lang.String logMessage;
    private com.strategyquant.tradinglib.Databank databank;
    private java.util.ArrayList<java.lang.Object[]> logStats;
    private com.strategyquant.tradinglib.conditions.ConditionsChecker conditionsChecker;
    public com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask() throws java.lang.Exception;
    public com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;
    public java.lang.String getType();
    public java.lang.String getName();
    public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;
    private void init() throws java.lang.Exception;
    public void start() throws java.lang.Exception;
    private void logStats(java.lang.String, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, com.strategyquant.tradinglib.conditions.IConditionValue, java.util.ArrayList<com.strategyquant.tradinglib.ResultsGroup>) throws java.lang.Exception;
    private boolean checkConditions(com.strategyquant.tradinglib.ResultsGroup, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>);
    protected int getRunningStatus();
    public java.lang.String getPluginFolderName();
    public int getPreferredPosition();
    public java.lang.String[] getSettings();
    protected com.strategyquant.tradinglib.Databank[] getUsedDatabanks();
    protected com.strategyquant.tradinglib.Databank getOutputDatabank();
    public void logTaskFinished(com.strategyquant.tradinglib.project.ProjectGlobalLog);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
