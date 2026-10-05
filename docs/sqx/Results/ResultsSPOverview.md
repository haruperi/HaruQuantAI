# ResultsSPOverview.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/ResultsSPOverview.jar`.
- SHA-256: `68c7cadc03dcd867ff506c74654b427e4de3d38f027ddcb458500ef60b99d34b`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **5**; non-nested: **2**; nested/anonymous: **3**.
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

### 1. `com.strategyquant.plugin.Results.impl.SPOverview`

```mermaid
classDiagram
    class Ca1e77f75e8ce["SPOverviewPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +containsResult()
    }
    class C3c370acec916["SPOverviewServlet"] {
        -Log
        -LOCK_SPOVERVIEWSERVLET
        -rgProvider
        #execute()
    }
    class C180e0c3f58c3["AbstractResultsPlugin"]
    class C9ceba9ba4bac["IResultsGroupProvider"]
    class C92c3bb2ab146["StrategyConfig"]
    class C8900f90ae594["HttpJSONServlet"]
    C180e0c3f58c3 <|-- Ca1e77f75e8ce : declared extends
    Ca1e77f75e8ce ..> C3c370acec916 : field type
    C8900f90ae594 <|-- C3c370acec916 : declared extends
    C3c370acec916 ..> C9ceba9ba4bac : field type
    C3c370acec916 ..> C92c3bb2ab146 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Ca1e77f75e8ce` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` (this JAR) | this diagram |
| `C3c370acec916` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | this diagram |
| `C180e0c3f58c3` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C9ceba9ba4bac` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | referenced external type |
| `C92c3bb2ab146` | [`com.strategyquant.tradinglib.strategyConfig.StrategyConfig`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` | class | nested/anonymous |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` | class | nested/anonymous |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / field declaration: `private com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet servlet;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String getKey();` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / method signature: `public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / field declaration: `private static final java.lang.String LOCK_SPOVERVIEWSERVLET;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / field declaration: `private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | [`com.strategyquant.tradinglib.strategyConfig.StrategyConfig`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / field declaration: `private com.strategyquant.tradinglib.strategyConfig.StrategyConfig strategyConfig;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.json.JSONObject getStats(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `private org.json.JSONObject getStats(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `private org.json.JSONObject getStats(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `java.util.List` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `private void copyData(java.util.List<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>, org.json.JSONArray, double, boolean, boolean);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `private void copyData(java.util.List<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>, org.json.JSONArray, double, boolean, boolean);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` / method signature: `private void copyData(java.util.List<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>, org.json.JSONArray, double, boolean, boolean);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` / field declaration: `public java.lang.String symbol;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` / method signature: `public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet, java.lang.String);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` / field declaration: `final com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet this$0;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` / method signature: `public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet, java.lang.String);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` | `java.util.Comparator` (not resolved in scoped archives) | implements | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` / class declaration: `public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL implements java.util.Comparator<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` / field declaration: `final com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet this$0;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` / method signature: `public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` / method signature: `public int compare(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock, com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL` / method signature: `public int compare(java.lang.Object, java.lang.Object);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` | `java.util.Comparator` (not resolved in scoped archives) | implements | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` / class declaration: `public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume implements java.util.Comparator<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` / field declaration: `final com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet this$0;` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` / method signature: `public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` / method signature: `public int compare(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock, com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock);` |
| `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume` / method signature: `public int compare(java.lang.Object, java.lang.Object);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet servlet;
    public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup);
    public java.lang.String getKey();
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_SPOVERVIEWSERVLET;
    private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;
    private com.strategyquant.tradinglib.strategyConfig.StrategyConfig strategyConfig;
    public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private org.json.JSONObject getStats(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;
    private void copyData(java.util.List<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>, org.json.JSONArray, double, boolean, boolean);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock</summary>

```text
class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock
    public java.lang.String symbol;
    public double pl;
    public double volume;
    public long trades;
    final com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet this$0;
    public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet, java.lang.String);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL</summary>

```text
public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL implements java.util.Comparator<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>
    final com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet this$0;
    public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByPL(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet);
    public int compare(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock, com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock);
    public int compare(java.lang.Object, java.lang.Object);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume</summary>

```text
public class com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume implements java.util.Comparator<com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock>
    final com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet this$0;
    public com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$StockComparatorByVolume(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet);
    public int compare(com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock, com.strategyquant.plugin.Results.impl.SPOverview.SPOverviewServlet$SPStock);
    public int compare(java.lang.Object, java.lang.Object);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
