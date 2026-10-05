# ResultsWalkForward.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar`.
- SHA-256: `f6ac8d923375b7997431ac365e906e232bd7dc554601ba9cd98ed15c28e6abea`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **5**; non-nested: **5**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Results.impl.WalkForward`

```mermaid
classDiagram
    class C6e1d3ca3603e["WFParamsExport"] {
        -Log
        +toXlsx()
        +toCsv()
    }
    class C561f025770b2["WalkForwardPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +containsResult()
    }
    class Cc16033f6db3e["WalkForwardServlet"] {
        -Log
        -LOCK_WFSERVLET
        -rgProvider
        #execute()
        +printHtmlFormatedValue()
    }
    class Cd8e3eb6ebc25["WFViews"]
    class C180e0c3f58c3["AbstractResultsPlugin"]
    class C9ceba9ba4bac["IResultsGroupProvider"]
    class C8900f90ae594["HttpJSONServlet"]
    C180e0c3f58c3 <|-- C561f025770b2 : declared extends
    C561f025770b2 ..> Cc16033f6db3e : field type
    C8900f90ae594 <|-- Cc16033f6db3e : declared extends
    Cc16033f6db3e ..> Cd8e3eb6ebc25 : field type
    Cc16033f6db3e ..> C9ceba9ba4bac : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C6e1d3ca3603e` | `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` (this JAR) | this diagram |
| `C561f025770b2` | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` (this JAR) | this diagram |
| `Cc16033f6db3e` | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` (this JAR) | this diagram |
| `Cd8e3eb6ebc25` | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` (this JAR) | another group in this JAR |
| `C180e0c3f58c3` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C9ceba9ba4bac` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

### 2. `com.strategyquant.plugin.Results.impl.WalkForward.views`

```mermaid
classDiagram
    class Cd8e3eb6ebc25["WFViews"] {
        -Log
        -manager
        +execute()
        #tryGetParam()
        +getViewByName()
    }
    class C7819c56a9264["WFViewsManager"] {
        -Log
        -views
        -viewsFolder
        +loadViews()
        +getViews()
        +getView()
        +addView()
    }
    class Cba8587482cc6["DatabankTableView"]
    Cd8e3eb6ebc25 ..> C7819c56a9264 : field type
    C7819c56a9264 ..> Cba8587482cc6 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cd8e3eb6ebc25` | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` (this JAR) | this diagram |
| `C7819c56a9264` | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` (this JAR) | this diagram |
| `Cba8587482cc6` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` / method signature: `public void toXlsx(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`public void toCsv(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`private java.lang.String formatValue(com.strategyquant.tradinglib.databank.DatabankTableColumnEntry, java.lang.String, boolean);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` | [`com.strategyquant.tradinglib.WalkForwardResult`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` / method signature: `public void toXlsx(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`public void toCsv(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` / method signature: `public void toXlsx(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`public void toCsv(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` | [`com.strategyquant.tradinglib.databank.DatabankTableColumnEntry`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport` / method signature: `private java.lang.String formatValue(com.strategyquant.tradinglib.databank.DatabankTableColumnEntry, java.lang.String, boolean);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / field declaration: `private com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet servlet;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String getKey();` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / method signature: `public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / field declaration: `private static final java.lang.String LOCK_WFSERVLET;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onExport(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onGetConditions(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.jdom2.Element getConditionsEl(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int, int, int, int);`<br>`private org.json.JSONObject printRobustnessResult(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int) throws java.lang.Exception;`<br>`private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;`<br>`private synchronized java.lang.String onPrintTable(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`public java.lang.String printHtmlFormatedValue(com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.DatabankColumn, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / field declaration: `private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `public com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / field declaration: `private com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews views;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onExport(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onGetConditions(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onPrintTable(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onExport(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onGetConditions(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private synchronized java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private org.json.JSONObject printRobustnessResult(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int) throws java.lang.Exception;`<br>`private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;`<br>`private synchronized java.lang.String onPrintTable(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`public java.lang.String printHtmlFormatedValue(com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.DatabankColumn, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private org.jdom2.Element getConditionsEl(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int, int, int, int);`<br>`private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private org.jdom2.Element getConditionsEl(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int, int, int, int);`<br>`private boolean paramsChanged(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, int, int, int, int);`<br>`private org.json.JSONObject printRobustnessResult(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private boolean paramsChanged(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, int, int, int, int);`<br>`private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.conditions.Condition`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private boolean paramsChanged(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, int, int, int, int);`<br>`private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private org.json.JSONObject printRobustnessResult(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;`<br>`private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.WalkForwardResult`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;`<br>`private org.json.JSONArray printTable(com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private org.json.JSONArray printTable(com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `private org.json.JSONArray printTable(com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.SQStats`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `public java.lang.String printHtmlFormatedValue(com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.DatabankColumn, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | [`com.strategyquant.tradinglib.DatabankColumn`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` / method signature: `public java.lang.String printHtmlFormatedValue(com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.DatabankColumn, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` / field declaration: `private com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager manager;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` / method signature: `public com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews(java.lang.String);`<br>`public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetColumns();`<br>`private java.lang.String onGetViews() throws java.lang.Exception;`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` / method signature: `public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` / method signature: `public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetViews() throws java.lang.Exception;`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews` / method signature: `public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `java.util.HashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / field declaration: `private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `java.util.HashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / method signature: `public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / field declaration: `private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;`<br>`private final java.lang.String viewsFolder;`<br>`private final java.lang.String fileExtension;`<br>`public static final java.lang.String SettingsKey;`<br>`private final java.lang.String DefaultViewName;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / method signature: `public com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager(java.lang.String);`<br>`public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;`<br>`public void addView(java.lang.String) throws java.lang.Exception;`<br>`private void _addView(java.lang.String, boolean) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;`<br>`public void removeView(java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getViewFilePath(java.lang.String);` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / field declaration: `private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / method signature: `public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView createDefaultView();`<br>`private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getSelectedView();` |
| `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` / method signature: `public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;`<br>`public void addView(java.lang.String) throws java.lang.Exception;`<br>`private void _addView(java.lang.String, boolean) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;`<br>`public void removeView(java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport</summary>

```text
public class com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport();
    public void toXlsx(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);
    public void toCsv(java.lang.String, boolean, com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);
    private java.lang.String formatValue(com.strategyquant.tradinglib.databank.DatabankTableColumnEntry, java.lang.String, boolean);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet servlet;
    public com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;
    public java.lang.String getKey();
    public org.json.JSONObject getInitializationData() throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_WFSERVLET;
    private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;
    private com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews views;
    public com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onExport(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private synchronized java.lang.String onGetConditions(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private synchronized java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private org.jdom2.Element getConditionsEl(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int, int, int, int);
    private boolean paramsChanged(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>, int, int, int, int);
    private org.json.JSONObject printRobustnessResult(com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, java.lang.String, int) throws java.lang.Exception;
    private java.lang.String printConditionsTable(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.WalkForwardResult, org.jdom2.Element, java.util.ArrayList<com.strategyquant.tradinglib.conditions.Condition>) throws java.lang.Exception;
    private org.json.JSONObject printChart(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult, org.jdom2.Element, java.lang.String) throws java.lang.Exception;
    private synchronized java.lang.String onPrintTable(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private org.json.JSONArray printTable(com.strategyquant.tradinglib.WalkForwardResult, com.strategyquant.tradinglib.databank.DatabankTableView);
    public java.lang.String printHtmlFormatedValue(com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.DatabankColumn, java.lang.String) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews</summary>

```text
public class com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews
    private static final org.slf4j.Logger Log;
    private com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager manager;
    public com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews(java.lang.String);
    public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onGetColumns();
    private java.lang.String onGetViews() throws java.lang.Exception;
    private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager</summary>

```text
public class com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager
    private static final org.slf4j.Logger Log;
    private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;
    private final java.lang.String viewsFolder;
    private final java.lang.String fileExtension;
    public static final java.lang.String SettingsKey;
    private final java.lang.String DefaultViewName;
    public com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager(java.lang.String);
    public void loadViews();
    public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();
    public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;
    public void addView(java.lang.String) throws java.lang.Exception;
    private void _addView(java.lang.String, boolean) throws java.lang.Exception;
    public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;
    public void removeView(java.lang.String) throws java.lang.Exception;
    public com.strategyquant.tradinglib.databank.DatabankTableView createDefaultView();
    private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;
    private java.lang.String getViewFilePath(java.lang.String);
    public com.strategyquant.tradinglib.databank.DatabankTableView getSelectedView();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
