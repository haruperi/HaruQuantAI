# ResultsStrategyConfig.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/ResultsStrategyConfig.jar`.
- SHA-256: `6409614e40da9c8afeee39bbde288ca87194eba4c77fbf1c7104d6c0f7dfba2d`.
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

### 1. `com.strategyquant.plugin.Results.impl.StrategyConfig`

```mermaid
classDiagram
    class Cb4d36ec58b93["StrategyConfigPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +containsResult()
    }
    class C7d04f3da7621["StrategyConfigServlet"] {
        -Log
        -LOCK_STRCONFIGSERVLET
        -rgProvider
        #execute()
    }
    class C180e0c3f58c3["AbstractResultsPlugin"]
    class C9ceba9ba4bac["IResultsGroupProvider"]
    class C92c3bb2ab146["StrategyConfig"]
    class C8900f90ae594["HttpJSONServlet"]
    C180e0c3f58c3 <|-- Cb4d36ec58b93 : declared extends
    Cb4d36ec58b93 ..> C7d04f3da7621 : field type
    C8900f90ae594 <|-- C7d04f3da7621 : declared extends
    C7d04f3da7621 ..> C9ceba9ba4bac : field type
    C7d04f3da7621 ..> C92c3bb2ab146 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cb4d36ec58b93` | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` (this JAR) | this diagram |
| `C7d04f3da7621` | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` (this JAR) | this diagram |
| `C180e0c3f58c3` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C9ceba9ba4bac` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | referenced external type |
| `C92c3bb2ab146` | [`com.strategyquant.tradinglib.strategyConfig.StrategyConfig`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | [`com.strategyquant.tradinglib.results.AbstractResultsPlugin`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / field declaration: `private com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet servlet;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String getKey();` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / method signature: `public boolean containsResult(com.strategyquant.tradinglib.ResultsGroup);` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin` / method signature: `public org.json.JSONObject getInitializationData() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / field declaration: `private static final java.lang.String LOCK_STRCONFIGSERVLET;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onLoadStrategySettings(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / field declaration: `private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | [`com.strategyquant.tradinglib.results.IResultsGroupProvider`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / method signature: `public com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | [`com.strategyquant.tradinglib.strategyConfig.StrategyConfig`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / field declaration: `private com.strategyquant.tradinglib.strategyConfig.StrategyConfig strategyConfig;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onLoadStrategySettings(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onLoadStrategySettings(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin extends com.strategyquant.tradinglib.results.AbstractResultsPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet servlet;
    public com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigPlugin();
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
<summary>com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String LOCK_STRCONFIGSERVLET;
    private static com.strategyquant.tradinglib.results.IResultsGroupProvider rgProvider;
    private com.strategyquant.tradinglib.strategyConfig.StrategyConfig strategyConfig;
    public com.strategyquant.plugin.Results.impl.StrategyConfig.StrategyConfigServlet(com.strategyquant.tradinglib.results.IResultsGroupProvider);
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onLoadStrategySettings(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onPrint(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
