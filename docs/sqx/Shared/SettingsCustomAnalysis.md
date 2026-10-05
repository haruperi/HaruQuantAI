# SettingsCustomAnalysis.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar`.
- SHA-256: `2014e1848e5e44ee88dd0d785d6b6955ec420c510724db77eaee7a0ba31c616a`.
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

### 1. `com.strategyquant.plugin.Settings.impl.CustomAnalysis`

```mermaid
classDiagram
    class Cd51f861a69e5["CustomAnalysisPlugin"] {
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +readSettings()
        +getStrategyConfigSettings()
        +getSettingName()
        +getName()
    }
    class C27734eb41505["ISettingTabPlugin"]
    C27734eb41505 <|.. Cd51f861a69e5 : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cd51f861a69e5` | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` (this JAR) | this diagram |
| `C27734eb41505` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public java.lang.String getProduct();`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`public java.lang.String getSettingName();`<br>`public java.lang.String getName();` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | [`com.strategyquant.tradinglib.task.settings.TaskSettingsData`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin</summary>

```text
public class com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
    public com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);
    public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;
    public java.lang.String getSettingName();
    public java.lang.String getName();
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
