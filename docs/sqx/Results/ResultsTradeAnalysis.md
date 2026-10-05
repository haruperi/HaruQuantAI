# ResultsTradeAnalysis.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/ResultsTradeAnalysis.jar`.
- SHA-256: `7c7ba403d569744e36cd88fa4e8e62640249db056c36171fe781e58e30a17816`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **3**; nested/anonymous: **0**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `Results` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.Results.impl.TradeAnalysis`

```mermaid
classDiagram
    class C5a2d8c6f1079["AnnualStatsComputer"] {
        +YEAR_ALL
        +twoDFormat
        +compute()
    }
    class C2d051b5ffcf6["TradeAnalysisPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +containsResult()
    }
    class Cba15badbe639["TradeAnalysisServlet"] {
        -Log
        -LOCK_TRADEANALYSISSERVLET
        -rgProvider
        #execute()
        +loadLastSettings()
        +getTypes()
    }
    class C1b6b4448b67b["IProgram"]
    class C81fcbc41b716["ResultsGroup"]
    class C180e0c3f58c3["AbstractResultsPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C180e0c3f58c3 <|-- C2d051b5ffcf6 : declared extends
    C1b6b4448b67b <|.. C2d051b5ffcf6 : declared interface
    C2d051b5ffcf6 ..> Cba15badbe639 : field type
    C8900f90ae594 <|-- Cba15badbe639 : declared extends
    Cba15badbe639 ..> C5a2d8c6f1079 : field type
    Cba15badbe639 ..> C81fcbc41b716 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C5a2d8c6f1079` | `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` (this JAR) | this diagram |
| `C2d051b5ffcf6` | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` (this JAR) | this diagram |
| `Cba15badbe639` | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C81fcbc41b716` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | referenced external type |
| `C180e0c3f58c3` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` | `java.text.DecimalFormat` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` / field declaration: `public java.text.DecimalFormat twoDFormat;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` / method signature: `public org.json.JSONArray compute(int, com.strategyquant.tradinglib.OrdersList, byte, byte);` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` | [`com.strategyquant.tradinglib.OrdersList`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` / method signature: `public org.json.JSONArray compute(int, com.strategyquant.tradinglib.OrdersList, byte, byte);` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin implements com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin implements com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / field declaration: `private com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet servlet;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String getKey();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / method signature: `public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / field declaration: `private static final java.lang.String LOCK_TRADEANALYSISSERVLET;`<br>`private static final java.lang.String SettingKey;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(java.util.Map<java.lang.String, java.lang.String[]>, com.strategyquant.tradinglib.OrdersList, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetAnnualStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / field declaration: `private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `public com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / field declaration: `private com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer statsComputer;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / field declaration: `public com.strategyquant.tradinglib.ResultsGroup rg;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(java.util.Map<java.lang.String, java.lang.String[]>, com.strategyquant.tradinglib.OrdersList, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetAnnualStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`public org.json.JSONArray loadLastSettings() throws java.lang.Exception;`<br>`public org.json.JSONArray getTypes() throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(java.util.Map<java.lang.String, java.lang.String[]>, com.strategyquant.tradinglib.OrdersList, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetAnnualStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `public org.json.JSONArray loadLastSettings() throws java.lang.Exception;`<br>`public org.json.JSONArray getTypes() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `private org.json.JSONObject printChart(java.util.Map<java.lang.String, java.lang.String[]>, com.strategyquant.tradinglib.OrdersList, java.lang.String) throws java.lang.Exception;`<br>`private org.json.JSONObject calculateAnnualStats(int, com.strategyquant.tradinglib.OrdersList, byte, byte);` |
| `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | [`com.strategyquant.tradinglib.OrdersList`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` / method signature: `private org.json.JSONObject printChart(java.util.Map<java.lang.String, java.lang.String[]>, com.strategyquant.tradinglib.OrdersList, java.lang.String) throws java.lang.Exception;`<br>`private org.json.JSONObject calculateAnnualStats(int, com.strategyquant.tradinglib.OrdersList, byte, byte);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer</summary>

```text
public class com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer
    public static final int YEAR_ALL;
    public java.text.DecimalFormat twoDFormat;
    public com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer();
    public org.json.JSONArray compute(int, com.strategyquant.tradinglib.OrdersList, byte, byte);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin implements com.strategyquant.pluginlib.program.IProgram
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet servlet;
    public com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup);
    public java.lang.String getKey();
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_TRADEANALYSISSERVLET;
    private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;
    private com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer statsComputer;
    private static final java.lang.String SettingKey;
    public com.strategyquant.tradinglib.ResultsGroup rg;
    public com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    public org.json.JSONArray loadLastSettings() throws java.lang.Exception;
    public org.json.JSONArray getTypes() throws java.lang.Exception;
    private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private org.json.JSONObject printChart(java.util.Map<java.lang.String, java.lang.String[]>, com.strategyquant.tradinglib.OrdersList, java.lang.String) throws java.lang.Exception;
    private java.lang.String onGetAnnualStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private org.json.JSONObject calculateAnnualStats(int, com.strategyquant.tradinglib.OrdersList, byte, byte);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
