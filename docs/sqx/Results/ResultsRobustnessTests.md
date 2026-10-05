# ResultsRobustnessTests.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar`.
- SHA-256: `ca78fea41989e25555b43f2042b775befbe015807c5bc3de4b8416e3909bc0d9`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **7**; non-nested: **7**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Results.impl.RobustnessTests`

```mermaid
classDiagram
    class Ca16ad29d22da["ConfidenceLevels"] {
        -Log
        +print()
    }
    class C359eaf926d8d["RTChart"] {
        -Log
        +print()
    }
    class C6766496d84fb["RiskOfRuins"] {
        -Log
        +print()
    }
    class C1f0cf995e4b2["RobustnessTestsServlet"] {
        -Log
        -LOCK_ROBTESTSERVLET
        -rtChart
        #execute()
    }
    class C952692b5c677["RobustnessTestsServletPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +containsResult()
    }
    class C180e0c3f58c3["AbstractResultsPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- C1f0cf995e4b2 : declared extends
    C1f0cf995e4b2 ..> Ca16ad29d22da : field type
    C1f0cf995e4b2 ..> C359eaf926d8d : field type
    C180e0c3f58c3 <|-- C952692b5c677 : declared extends
    C952692b5c677 ..> C1f0cf995e4b2 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Ca16ad29d22da` | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` (this JAR) | this diagram |
| `C359eaf926d8d` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` (this JAR) | this diagram |
| `C6766496d84fb` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` (this JAR) | this diagram |
| `C1f0cf995e4b2` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` (this JAR) | this diagram |
| `C952692b5c677` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` (this JAR) | this diagram |
| `C180e0c3f58c3` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

### 2. `com.strategyquant.plugin.Results.impl.RobustnessTests.views`

```mermaid
classDiagram
    class C41a6a31a0725["RTViews"] {
        -Log
        -manager
        -type
        +execute()
        #tryGetParam()
        +getViewByName()
    }
    class C350893788170["RTViewsManager"] {
        -Log
        -views
        -viewsFolder
        +loadViews()
        +getViews()
        +getView()
        +addView()
    }
    class Cba8587482cc6["DatabankTableView"]
    C41a6a31a0725 ..> C350893788170 : field type
    C350893788170 ..> Cba8587482cc6 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C41a6a31a0725` | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` (this JAR) | this diagram |
| `C350893788170` | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` (this JAR) | this diagram |
| `Cba8587482cc6` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Result, java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Result, java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`private org.json.JSONObject writeStats(int, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView, com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | [`com.strategyquant.tradinglib.Result`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Result, java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Result, java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Result, java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`private org.json.JSONObject writeStats(int, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView, com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `private org.json.JSONObject writeStats(int, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView, com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` | [`com.strategyquant.tradinglib.SQStats`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` / method signature: `private org.json.JSONObject writeStats(int, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView, com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` / method signature: `public org.json.JSONObject print(com.strategyquant.tradinglib.Result, java.lang.String, int, int);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | [`com.strategyquant.tradinglib.Result`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` / method signature: `public org.json.JSONObject print(com.strategyquant.tradinglib.Result, java.lang.String, int, int);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` / method signature: `public org.json.JSONObject print(com.strategyquant.tradinglib.Result, java.lang.String, int, int);`<br>`private com.strategyquant.tradinglib.equitychart.MainChartDataset createSeries(java.lang.String, com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues, int);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | [`com.strategyquant.tradinglib.equitychart.MainChartDataset`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` / method signature: `private com.strategyquant.tradinglib.equitychart.MainChartDataset createSeries(java.lang.String, com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues, int);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` | [`com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` / method signature: `private com.strategyquant.tradinglib.equitychart.MainChartDataset createSeries(java.lang.String, com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues, int);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.Result, java.lang.String, int, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | [`com.strategyquant.tradinglib.Result`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.Result, java.lang.String, int, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.Result, java.lang.String, int, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / method signature: `public org.json.JSONArray print(com.strategyquant.tradinglib.Result, java.lang.String, int, com.strategyquant.tradinglib.databank.DatabankTableView);`<br>`private org.json.JSONObject writeStats(int, double, double, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / method signature: `private org.json.JSONObject writeStats(int, double, double, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` | [`com.strategyquant.tradinglib.SQStats`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` / method signature: `private org.json.JSONObject writeStats(int, double, double, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private static final java.lang.String LOCK_ROBTESTSERVLET;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetMethods(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintChart(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintConfLevels(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintRiskOfRuinStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart rtChart;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels confidenceLevels;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins riskOfRuins;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews rtViews;`<br>`private com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews rtRRViews;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / field declaration: `private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / method signature: `public com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetMethods(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintChart(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintConfLevels(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintRiskOfRuinStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetMethods(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintChart(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintConfLevels(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrintRiskOfRuinStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / field declaration: `private com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet servlet;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String getKey();` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / method signature: `public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / field declaration: `private com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager manager;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / field declaration: `private java.lang.String type;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / method signature: `public com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews(java.lang.String, java.lang.String);`<br>`public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetColumns();`<br>`private java.lang.String onGetViews() throws java.lang.Exception;`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / method signature: `public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / method signature: `public java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetViews() throws java.lang.Exception;`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`protected java.lang.String[] tryGetParam(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews` / method signature: `public com.strategyquant.tradinglib.databank.DatabankTableView getViewByName(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `java.util.HashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / field declaration: `private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `java.util.HashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / method signature: `public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / field declaration: `private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;`<br>`private final java.lang.String viewsFolder;`<br>`private final java.lang.String fileExtension;`<br>`private java.lang.String type;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / method signature: `public com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager(java.lang.String, java.lang.String);`<br>`public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;`<br>`public void addView(java.lang.String) throws java.lang.Exception;`<br>`private void _addView(java.lang.String, boolean) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;`<br>`public void removeView(java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getViewFilePath(java.lang.String);` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / field declaration: `private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | [`com.strategyquant.tradinglib.databank.DatabankTableView`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / method signature: `public java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> getViews();`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView createDefaultView();`<br>`private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView getSelectedView();` |
| `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` / method signature: `public com.strategyquant.tradinglib.databank.DatabankTableView getView(java.lang.String) throws java.lang.Exception;`<br>`public void addView(java.lang.String) throws java.lang.Exception;`<br>`private void _addView(java.lang.String, boolean) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.databank.DatabankTableView updateView(java.lang.String) throws java.lang.Exception;`<br>`public void removeView(java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.databank.DatabankTableView getTableView(java.lang.String) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels();
    public org.json.JSONArray print(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Result, java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView);
    private org.json.JSONObject writeStats(int, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView, com.strategyquant.tradinglib.ResultsGroup);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart();
    public org.json.JSONObject print(com.strategyquant.tradinglib.Result, java.lang.String, int, int);
    private com.strategyquant.tradinglib.equitychart.MainChartDataset createSeries(java.lang.String, com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues, int);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins();
    public org.json.JSONArray print(com.strategyquant.tradinglib.Result, java.lang.String, int, com.strategyquant.tradinglib.databank.DatabankTableView);
    private org.json.JSONObject writeStats(int, double, double, com.strategyquant.tradinglib.SQStats, com.strategyquant.tradinglib.databank.DatabankTableView);
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_ROBTESTSERVLET;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart rtChart;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels confidenceLevels;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins riskOfRuins;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews rtViews;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews rtRRViews;
    private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onGetMethods(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onPrintChart(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onPrintConfLevels(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onPrintRiskOfRuinStats(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet servlet;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServletPlugin();
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
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews
    private static final org.slf4j.Logger Log;
    private com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager manager;
    private java.lang.String type;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews(java.lang.String, java.lang.String);
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
<summary>com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager</summary>

```text
public class com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager
    private static final org.slf4j.Logger Log;
    private java.util.HashMap<java.lang.String, com.strategyquant.tradinglib.databank.DatabankTableView> views;
    private final java.lang.String viewsFolder;
    private final java.lang.String fileExtension;
    private java.lang.String type;
    public com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager(java.lang.String, java.lang.String);
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
