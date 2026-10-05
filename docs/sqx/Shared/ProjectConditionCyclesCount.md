# ProjectConditionCyclesCount.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar`.
- SHA-256: `b1bc4d71172494dbd135988f9d5192aa12c32414d15ac4753b827ed20b659059`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **1**; non-nested: **1**; nested/anonymous: **0**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

Shared component: a single canonical document is linked from relevant workspace indexes. Its presence here does not establish which workspaces load it at runtime.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount`

```mermaid
classDiagram
    class Cd56eeee7e16e["CyclesCountConditionPlugin"] {
        +Log
        -fields
        -comparator
        +getName()
        +getTitle()
        +getDescription()
        +getDescriptionFormat()
    }
    class C930244e123f1["IProjectCondition"]
    class C360519953328["ProjectConditionField"]
    C930244e123f1 <|.. Cd56eeee7e16e : declared interface
    Cd56eeee7e16e ..> C360519953328 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cd56eeee7e16e` | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` (this JAR) | this diagram |
| `C930244e123f1` | [`com.strategyquant.tradinglib.project.IProjectCondition`](SQTradingLib.md) | referenced external type |
| `C360519953328` | [`com.strategyquant.tradinglib.project.ProjectConditionField`](SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | [`com.strategyquant.tradinglib.project.IProjectCondition`](SQTradingLib.md) | implements | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / class declaration: `public class com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin implements com.strategyquant.tradinglib.project.IProjectCondition` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | [`com.strategyquant.tradinglib.project.ProjectConditionField`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / field declaration: `private static final com.strategyquant.tradinglib.project.ProjectConditionField[] fields;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | [`com.strategyquant.tradinglib.project.ProjectConditionField`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public com.strategyquant.tradinglib.project.ProjectConditionField[] getFields();` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / field declaration: `private java.lang.String comparator;`<br>`private java.lang.String lastCheckedValue;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public java.lang.String getName();`<br>`public java.lang.String getTitle();`<br>`public java.lang.String getDescription();`<br>`public java.lang.String getDescriptionFormat();`<br>`public java.lang.String getLastCheckedValue();`<br>`public java.lang.String getProduct();` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public void readSettings(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public void readSettings(org.jdom2.Element) throws java.lang.Exception;`<br>`public boolean isMet(com.strategyquant.tradinglib.project.SQProject, com.strategyquant.tradinglib.taskImpl.ISQTask) throws java.lang.Exception;`<br>`public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | [`com.strategyquant.tradinglib.project.SQProject`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public boolean isMet(com.strategyquant.tradinglib.project.SQProject, com.strategyquant.tradinglib.taskImpl.ISQTask) throws java.lang.Exception;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public boolean isMet(com.strategyquant.tradinglib.project.SQProject, com.strategyquant.tradinglib.taskImpl.ISQTask) throws java.lang.Exception;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | [`com.strategyquant.tradinglib.project.IProjectCondition`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public com.strategyquant.tradinglib.project.IProjectCondition clone();` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` | `java.lang.CloneNotSupportedException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin</summary>

```text
public class com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin implements com.strategyquant.tradinglib.project.IProjectCondition
    public static final org.slf4j.Logger Log;
    private static final com.strategyquant.tradinglib.project.ProjectConditionField[] fields;
    private java.lang.String comparator;
    private int value;
    private java.lang.String lastCheckedValue;
    public com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin();
    public java.lang.String getName();
    public java.lang.String getTitle();
    public java.lang.String getDescription();
    public java.lang.String getDescriptionFormat();
    public java.lang.String getLastCheckedValue();
    public com.strategyquant.tradinglib.project.ProjectConditionField[] getFields();
    public void readSettings(org.jdom2.Element) throws java.lang.Exception;
    public boolean isMet(com.strategyquant.tradinglib.project.SQProject, com.strategyquant.tradinglib.taskImpl.ISQTask) throws java.lang.Exception;
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public com.strategyquant.tradinglib.project.IProjectCondition clone();
    public java.lang.Object clone() throws java.lang.CloneNotSupportedException;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
