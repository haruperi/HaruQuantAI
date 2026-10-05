# SettingsBlocks.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar`.
- SHA-256: `34983dd20362d2b1c0645fe1dd87250f8c154bf8763904e61d736a509f72d31d`.
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

### 1. `com.strategyquant.plugin.Settings.impl.Blocks`

```mermaid
classDiagram
    class C171380b19a68["BlocksServlet"] {
        -Log
        -signalKeys
        #execute()
        +loadStockpickerDefaultBlocks()
    }
    class Cd3c81520bb52["BlocksSettingsPlugin"] {
        +Log
        -tabTitle
        -dataContext
        +getHandler()
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
    }
    class C249b5c671b1a["IServletPlugin"]
    class C27734eb41505["ISettingTabPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- C171380b19a68 : declared extends
    C27734eb41505 <|.. Cd3c81520bb52 : declared interface
    C249b5c671b1a <|.. Cd3c81520bb52 : declared interface
    Cd3c81520bb52 ..> C171380b19a68 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C171380b19a68` | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` (this JAR) | this diagram |
| `Cd3c81520bb52` | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` (this JAR) | this diagram |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C27734eb41505` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | class | non-nested |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / class declaration: `public class com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / field declaration: `private static final java.util.ArrayList<java.lang.String> signalKeys;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / field declaration: `private static final java.util.ArrayList<java.lang.String> signalKeys;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList() throws java.lang.Exception;`<br>`private java.lang.String onLoadFromFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveToFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`public java.lang.String loadStockpickerDefaultBlocks();` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onLoadFromFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveToFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList() throws java.lang.Exception;`<br>`private java.lang.String onLoadFromFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveToFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.json.JSONArray getOrderTypes(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getIndicators(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getPriceRanges(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getPriceValues(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getOperators(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getSimpleRules(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getOthers(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getExitTypes(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getFormulas(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getParameterSets(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / method signature: `private org.json.JSONArray getOrderTypes(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getIndicators(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getPriceRanges(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getPriceValues(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getOperators(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getSimpleRules(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getOthers(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getExitTypes(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getFormulas(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getParameterSets(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` / method signature: `private org.json.JSONArray getOrderTypes(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getIndicators(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getPriceRanges(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getPriceValues(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getOperators(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getSimpleRules(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getOthers(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getExitTypes(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getFormulas(org.jdom2.Element) throws java.lang.Exception;`<br>`private org.json.JSONArray getParameterSets(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / field declaration: `private static final java.lang.String tabTitle;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public java.lang.String getProduct();`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`private java.lang.String generateBlockDescription(org.jdom2.Element, org.jdom2.Element, org.jdom2.Element);`<br>`public java.lang.String getSettingName();`<br>`public java.lang.String getName();` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / field declaration: `private com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet servlet;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `private void fixSettings(org.jdom2.Element);`<br>`private void fixCustomBlocks(org.jdom2.Element);`<br>`private void disableVPBlocksIfInactive(org.jdom2.Element);`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`private java.lang.String generateBlockDescription(org.jdom2.Element, org.jdom2.Element, org.jdom2.Element);`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;`<br>`private void addBlocks(org.jdom2.Element, org.json.JSONArray, com.strategyquant.tradinglib.blocks.random.BlocksConfig);` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | [`com.strategyquant.tradinglib.task.settings.TaskSettingsData`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;`<br>`private void addBlocks(org.jdom2.Element, org.json.JSONArray, com.strategyquant.tradinglib.blocks.random.BlocksConfig);` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | [`com.strategyquant.tradinglib.blocks.random.BlocksConfig`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `private void addBlocks(org.jdom2.Element, org.json.JSONArray, com.strategyquant.tradinglib.blocks.random.BlocksConfig);` |
| `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet</summary>

```text
public class com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.util.ArrayList<java.lang.String> signalKeys;
    public com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onList() throws java.lang.Exception;
    private java.lang.String onLoadFromFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onSaveToFile(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private org.json.JSONArray getOrderTypes(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getIndicators(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getPriceRanges(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getPriceValues(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getOperators(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getSimpleRules(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getOthers(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getExitTypes(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getFormulas(org.jdom2.Element) throws java.lang.Exception;
    private org.json.JSONArray getParameterSets(org.jdom2.Element) throws java.lang.Exception;
    public java.lang.String loadStockpickerDefaultBlocks();
```

</details>

<details>
<summary>com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin</summary>

```text
public class com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin
    public static final org.slf4j.Logger Log;
    private static final java.lang.String tabTitle;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet servlet;
    public com.strategyquant.plugin.Settings.impl.Blocks.BlocksSettingsPlugin();
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    private void fixSettings(org.jdom2.Element);
    private void fixCustomBlocks(org.jdom2.Element);
    private void disableVPBlocksIfInactive(org.jdom2.Element);
    public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);
    private java.lang.String generateBlockDescription(org.jdom2.Element, org.jdom2.Element, org.jdom2.Element);
    public java.lang.String getSettingName();
    public java.lang.String getName();
    public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;
    private void addBlocks(org.jdom2.Element, org.json.JSONArray, com.strategyquant.tradinglib.blocks.random.BlocksConfig);
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
