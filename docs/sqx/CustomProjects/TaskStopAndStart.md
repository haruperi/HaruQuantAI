# TaskStopAndStart.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar`.
- SHA-256: `1179ec5df70066f2f0bfdc60458ec3a656c074f514c5ccffc707fbce7387c99a`.
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

### 1. `com.strategyquant.plugin.Task.impl.StopAndStart`

```mermaid
classDiagram
    class C5ff1da104c99["StopAndStartTask"] {
        -conditions
        -skipToFirstProject
        -logMessage
        +getType()
        +getName()
        +clone()
        +start()
    }
    class C930244e123f1["IProjectCondition"]
    class C3d7572d63292["ProjectNameComparator"]
    class Ce44d386802cb["AbstractTask"]
    Ce44d386802cb <|-- C5ff1da104c99 : declared extends
    C5ff1da104c99 ..> C930244e123f1 : field type
    C5ff1da104c99 ..> C3d7572d63292 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C5ff1da104c99` | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` (this JAR) | this diagram |
| `C930244e123f1` | [`com.strategyquant.tradinglib.project.IProjectCondition`](../Shared/SQTradingLib.md) | referenced external type |
| `C3d7572d63292` | [`com.strategyquant.tradinglib.project.ProjectNameComparator`](../Shared/SQTradingLib.md) | referenced external type |
| `Ce44d386802cb` | [`com.strategyquant.tradinglib.taskImpl.AbstractTask`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.taskImpl.AbstractTask`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / class declaration: `public class com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / field declaration: `private java.util.ArrayList<com.strategyquant.tradinglib.project.IProjectCondition> conditions;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.project.IProjectCondition`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / field declaration: `private java.util.ArrayList<com.strategyquant.tradinglib.project.IProjectCondition> conditions;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / field declaration: `private java.lang.String logMessage;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / method signature: `public com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public java.lang.String getType();`<br>`public java.lang.String getName();`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`private java.lang.String getNextProjectName();`<br>`public java.lang.String getPluginFolderName();`<br>`public java.lang.String[] getSettings();` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.project.ProjectNameComparator`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / field declaration: `private com.strategyquant.tradinglib.project.ProjectNameComparator projectNameComparator;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / method signature: `public com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask() throws java.lang.Exception;`<br>`public com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public void start() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.project.ProgressEngine`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / method signature: `public com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / method signature: `public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / method signature: `protected com.strategyquant.tradinglib.Databank[] getUsedDatabanks();`<br>`protected com.strategyquant.tradinglib.Databank getOutputDatabank();` |
| `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` | [`com.strategyquant.tradinglib.project.ProjectGlobalLog`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask` / method signature: `public void logTaskFinished(com.strategyquant.tradinglib.project.ProjectGlobalLog);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask</summary>

```text
public class com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask extends com.strategyquant.tradinglib.taskImpl.AbstractTask
    private java.util.ArrayList<com.strategyquant.tradinglib.project.IProjectCondition> conditions;
    private boolean skipToFirstProject;
    private java.lang.String logMessage;
    private com.strategyquant.tradinglib.project.ProjectNameComparator projectNameComparator;
    public com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask() throws java.lang.Exception;
    public com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;
    public java.lang.String getType();
    public java.lang.String getName();
    public com.strategyquant.tradinglib.taskImpl.ISQTask clone(java.lang.String, com.strategyquant.tradinglib.project.ProgressEngine) throws java.lang.Exception;
    public void start() throws java.lang.Exception;
    private java.lang.String getNextProjectName();
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
