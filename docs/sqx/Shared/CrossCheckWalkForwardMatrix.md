# CrossCheckWalkForwardMatrix.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar`.
- SHA-256: `5022a6b0988f531f575ce94a1372c6f01274a9e619e60ea8392feac34ee1cee3`.
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

### 1. `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix`

```mermaid
classDiagram
    class C5d5f4ca278fe["WalkForwardMatrix"] {
        +Log
        -distributionUp
        -distributionDown
        +getName()
        +getShortName()
        +getDescription()
        +getPreferredPosition()
    }
    class C04861b02b3ff["WalkForwardCrossCheckMethod"]
    C04861b02b3ff <|-- C5d5f4ca278fe : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C5d5f4ca278fe` | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` (this JAR) | this diagram |
| `C04861b02b3ff` | [`com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod`](SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | [`com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod`](SQTradingLib.md) | extends | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / class declaration: `public class com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix extends com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | `com.strategyquant.lib.ValuesMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / field declaration: `private com.strategyquant.lib.ValuesMap paramTypesWFM;` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public java.lang.String getName();`<br>`public java.lang.String getShortName();`<br>`public java.lang.String getDescription();`<br>`protected com.strategyquant.lib.SettingsMap prepareSettings(java.lang.String, com.strategyquant.lib.SettingsMap, org.jdom2.Element, boolean) throws java.lang.Exception;`<br>`public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;`<br>`protected com.strategyquant.lib.SettingsMap prepareSettings(java.lang.String, com.strategyquant.lib.SettingsMap, org.jdom2.Element, boolean) throws java.lang.Exception;`<br>`public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | [`com.strategyquant.tradinglib.task.settings.TaskSettingsData`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;`<br>`protected com.strategyquant.lib.SettingsMap prepareSettings(java.lang.String, com.strategyquant.lib.SettingsMap, org.jdom2.Element, boolean) throws java.lang.Exception;`<br>`public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | `com.strategyquant.lib.SettingsMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `protected com.strategyquant.lib.SettingsMap prepareSettings(java.lang.String, com.strategyquant.lib.SettingsMap, org.jdom2.Element, boolean) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.crosscheck.ICrossCheck clone(com.strategyquant.lib.SettingsMap);` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | [`com.strategyquant.tradinglib.crosscheck.ICrossCheck`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public com.strategyquant.tradinglib.crosscheck.ICrossCheck clone(com.strategyquant.lib.SettingsMap);` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | [`com.strategyquant.tradinglib.engine.ChartSetups`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public com.strategyquant.tradinglib.engine.ChartSetups getChartSetups(com.strategyquant.tradinglib.ChartSetup);` |
| `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` | [`com.strategyquant.tradinglib.ChartSetup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix` / method signature: `public com.strategyquant.tradinglib.engine.ChartSetups getChartSetups(com.strategyquant.tradinglib.ChartSetup);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix</summary>

```text
public class com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix extends com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod
    public static final org.slf4j.Logger Log;
    private int distributionUp;
    private int distributionDown;
    private int maxSteps;
    private com.strategyquant.lib.ValuesMap paramTypesWFM;
    public com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix();
    public java.lang.String getName();
    public java.lang.String getShortName();
    public java.lang.String getDescription();
    public int getPreferredPosition();
    public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;
    protected com.strategyquant.lib.SettingsMap prepareSettings(java.lang.String, com.strategyquant.lib.SettingsMap, org.jdom2.Element, boolean) throws java.lang.Exception;
    public com.strategyquant.tradinglib.crosscheck.ICrossCheck clone(com.strategyquant.lib.SettingsMap);
    public com.strategyquant.tradinglib.engine.ChartSetups getChartSetups(com.strategyquant.tradinglib.ChartSetup);
    public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;
    public int getBadStrategyReason();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
