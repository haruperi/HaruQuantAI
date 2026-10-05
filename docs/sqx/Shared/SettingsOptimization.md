# SettingsOptimization.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar`.
- SHA-256: `4bd3b12f7d40c41489b58ac67e6d90191080825446921bd0373a11c74a7eb40d`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **2**; non-nested: **2**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Settings.impl.Optimization`

```mermaid
classDiagram
    class Cf5dab81b5717["OptimizationServlet"] {
        -Log
        -LOCK_OPTSERVLET
        -instance
        +getInstance()
        #execute()
    }
    class Ca98b45c4af93["OptimizationSettingsPlugin"] {
        +Log
        -connectionContext
        +getHandler()
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +readSettings()
    }
    class C249b5c671b1a["IServletPlugin"]
    class C27734eb41505["ISettingTabPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- Cf5dab81b5717 : declared extends
    C27734eb41505 <|.. Ca98b45c4af93 : declared interface
    C249b5c671b1a <|.. Ca98b45c4af93 : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cf5dab81b5717` | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` (this JAR) | this diagram |
| `Ca98b45c4af93` | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` (this JAR) | this diagram |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C27734eb41505` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | class | non-nested |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / class declaration: `public class com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / field declaration: `private static final java.lang.String LOCK_OPTSERVLET;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onLoadStrategyToOptimize(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onLoadStrategy(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onGetNumberOfTests(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private long getAllStrategiesCombinations(java.lang.String, java.lang.String, org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onLoadStrategyToOptimize(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onLoadStrategy(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onGetNumberOfTests(java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `java.io.File` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `private long getSingleStrategyCombinations(java.io.File, org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `private long getSingleStrategyCombinations(java.io.File, org.jdom2.Element) throws java.lang.Exception;`<br>`private long getAllStrategiesCombinations(java.lang.String, java.lang.String, org.jdom2.Element) throws java.lang.Exception;`<br>`private long getCombinationsCount(com.strategyquant.tradinglib.ResultsGroup, org.jdom2.Element) throws java.lang.Exception;`<br>`private void changeSymmetry(org.jdom2.Element, org.jdom2.Element, boolean, org.json.JSONObject) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `private long getSingleStrategyCombinations(java.io.File, org.jdom2.Element) throws java.lang.Exception;`<br>`private long getAllStrategiesCombinations(java.lang.String, java.lang.String, org.jdom2.Element) throws java.lang.Exception;`<br>`private long getCombinationsCount(com.strategyquant.tradinglib.ResultsGroup, org.jdom2.Element) throws java.lang.Exception;`<br>`private void changeSymmetry(org.jdom2.Element, org.jdom2.Element, boolean, org.json.JSONObject) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `private long getCombinationsCount(com.strategyquant.tradinglib.ResultsGroup, org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `private void changeSymmetry(org.jdom2.Element, org.jdom2.Element, boolean, org.json.JSONObject) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` | [`com.strategyquant.tradinglib.Variables`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet` / method signature: `private boolean shouldSort(com.strategyquant.tradinglib.Variables);` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler connectionContext;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public java.lang.String getProduct();`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`public java.lang.String getSettingName();`<br>`public java.lang.String getName();` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`private void checkParameter(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `private void fixSettings(org.jdom2.Element);`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`private void checkParameter(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | [`com.strategyquant.tradinglib.task.settings.TaskSettingsData`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`private void checkParameter(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet</summary>

```text
public class com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_OPTSERVLET;
    private static com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet instance;
    public com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet();
    public static com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet getInstance();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);
    private java.lang.String onLoadStrategyToOptimize(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onLoadStrategy(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onGetNumberOfTests(java.util.Map<java.lang.String, java.lang.String[]>);
    private long getSingleStrategyCombinations(java.io.File, org.jdom2.Element) throws java.lang.Exception;
    private long getAllStrategiesCombinations(java.lang.String, java.lang.String, org.jdom2.Element) throws java.lang.Exception;
    private long getCombinationsCount(com.strategyquant.tradinglib.ResultsGroup, org.jdom2.Element) throws java.lang.Exception;
    private void changeSymmetry(org.jdom2.Element, org.jdom2.Element, boolean, org.json.JSONObject) throws java.lang.Exception;
    private boolean shouldSort(com.strategyquant.tradinglib.Variables);
```

</details>

<details>
<summary>com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin</summary>

```text
public class com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin
    public static final org.slf4j.Logger Log;
    private org.eclipse.jetty.servlet.ServletContextHandler connectionContext;
    public com.strategyquant.plugin.Settings.impl.Optimization.OptimizationSettingsPlugin();
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    private void fixSettings(org.jdom2.Element);
    public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);
    private void checkParameter(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;
    public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;
    public java.lang.String getSettingName();
    public java.lang.String getName();
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
