# SettingsAutomaticPortfolioBuilder.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar`.
- SHA-256: `f3bdfb79409f2b8eaf179626cef9462733a669c34f0ea05fb15ddad1219171d7`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **2**; non-nested: **2**; nested/anonymous: **0**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `PortfolioMaster` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder`

```mermaid
classDiagram
    class C7bfe87da4dc8["SettingsAutomaticPortfolioBuilderPlugin"] {
        +Log
        -dataContext
        -servlet
        +getHandler()
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
    }
    class C63805f152015["SettingsAutomaticPortfolioBuilderServlet"] {
        -Log
        #execute()
        +getFitnessTypes()
        +sampleTypeKey()
    }
    class C249b5c671b1a["IServletPlugin"]
    class C27734eb41505["ISettingTabPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C27734eb41505 <|.. C7bfe87da4dc8 : declared interface
    C249b5c671b1a <|.. C7bfe87da4dc8 : declared interface
    C7bfe87da4dc8 ..> C63805f152015 : field type
    C8900f90ae594 <|-- C63805f152015 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C7bfe87da4dc8` | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` (this JAR) | this diagram |
| `C63805f152015` | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` (this JAR) | this diagram |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C27734eb41505` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | class | non-nested |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | [`com.strategyquant.tradinglib.task.settings.ISettingTabPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / class declaration: `public class com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / field declaration: `private com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet servlet;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public java.lang.String getProduct();`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`public java.lang.String getSettingName();`<br>`public java.lang.String getName();` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `private void fixSettings(org.jdom2.Element);`<br>`public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);`<br>`public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | [`com.strategyquant.tradinglib.taskImpl.ISQTask`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | [`com.strategyquant.tradinglib.task.settings.TaskSettingsData`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / class declaration: `public class com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getNumberOfPossiblePortfolios(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`public static java.lang.String sampleTypeKey(byte);` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getNumberOfPossiblePortfolios(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getNumberOfPossiblePortfolios(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`public org.json.JSONArray getFitnessTypes() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / method signature: `private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet` / method signature: `public org.json.JSONArray getFitnessTypes() throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin</summary>

```text
public class com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin implements com.strategyquant.tradinglib.task.settings.ISettingTabPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin
    public static final org.slf4j.Logger Log;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet servlet;
    public com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderPlugin();
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    private void fixSettings(org.jdom2.Element);
    public void readSettings(java.lang.String, com.strategyquant.tradinglib.taskImpl.ISQTask, org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData);
    public void getStrategyConfigSettings(org.jdom2.Element, org.json.JSONArray) throws java.lang.Exception;
    public java.lang.String getSettingName();
    public java.lang.String getName();
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet</summary>

```text
public class com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String getNumberOfPossiblePortfolios(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    public org.json.JSONArray getFitnessTypes() throws java.lang.Exception;
    public static java.lang.String sampleTypeKey(byte);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
