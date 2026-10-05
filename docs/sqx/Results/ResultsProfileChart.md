# ResultsProfileChart.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar`.
- SHA-256: `1c0cbb510a72e0b4515803886440ce10c11a6173b9e1ee9b8de46fa7feec84cd`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **2**; non-nested: **2**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Results.impl.ProfileChart`

```mermaid
classDiagram
    class C00e5876e32ea["ProfileChartPlugin"] {
        -dataContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +containsResult()
        +getKey()
    }
    class Caab7a493e802["ProfileChartServlet"] {
        -Log
        -LOCK_PROFILECHART
        -rgProvider
        #doGet()
        #execute()
        #executeBinary()
    }
    class C180e0c3f58c3["AbstractResultsPlugin"]
    class C9ceba9ba4bac["IResultsGroupProvider"]
    class C8900f90ae594["HttpJSONServlet"]
    C180e0c3f58c3 <|-- C00e5876e32ea : declared extends
    C8900f90ae594 <|-- Caab7a493e802 : declared extends
    Caab7a493e802 ..> C9ceba9ba4bac : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C00e5876e32ea` | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` (this JAR) | this diagram |
| `Caab7a493e802` | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` (this JAR) | this diagram |
| `C180e0c3f58c3` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C9ceba9ba4bac` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String getKey();` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / method signature: `public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin` / method signature: `public org.json.JSONObject getInitializationData();` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / field declaration: `private static final java.lang.String LOCK_PROFILECHART;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`protected byte[] executeBinary(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPaths(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onView(java.lang.String) throws java.lang.Exception;`<br>`private byte[] onFile(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / field declaration: `private final com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `public com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `jakarta.servlet.http.HttpServletRequest` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected void doGet(jakarta.servlet.http.HttpServletRequest, jakarta.servlet.http.HttpServletResponse) throws jakarta.servlet.ServletException, java.io.IOException;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `jakarta.servlet.http.HttpServletResponse` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected void doGet(jakarta.servlet.http.HttpServletRequest, jakarta.servlet.http.HttpServletResponse) throws jakarta.servlet.ServletException, java.io.IOException;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `jakarta.servlet.ServletException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected void doGet(jakarta.servlet.http.HttpServletRequest, jakarta.servlet.http.HttpServletResponse) throws jakarta.servlet.ServletException, java.io.IOException;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `java.io.IOException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected void doGet(jakarta.servlet.http.HttpServletRequest, jakarta.servlet.http.HttpServletResponse) throws jakarta.servlet.ServletException, java.io.IOException;` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`protected byte[] executeBinary(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onPaths(java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`protected byte[] executeBinary(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onView(java.lang.String) throws java.lang.Exception;`<br>`private byte[] onFile(java.lang.String) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;
    public java.lang.String getKey();
    public org.json.JSONObject getInitializationData();
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_PROFILECHART;
    private final com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;
    public com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);
    protected void doGet(jakarta.servlet.http.HttpServletRequest, jakarta.servlet.http.HttpServletResponse) throws jakarta.servlet.ServletException, java.io.IOException;
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    protected byte[] executeBinary(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onPaths(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onView(java.lang.String) throws java.lang.Exception;
    private byte[] onFile(java.lang.String) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
