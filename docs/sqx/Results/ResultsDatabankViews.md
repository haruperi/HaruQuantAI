# ResultsDatabankViews.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/ResultsDatabankViews.jar`.
- SHA-256: `22fe5655735ae9dda9226304966ea67c38f47b1ef7244d5dfed0c9249a61ed20`.
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

### 1. `com.strategyquant.plugin.Results.impl.DatabankViews`

```mermaid
classDiagram
    class Cd83e8f7ad64b["DatabankViewsPlugin"] {
        -dataContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
    }
    class C9d9260e84407["DatabankViewsServlet"] {
        -Log
        #execute()
    }
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C249b5c671b1a <|.. Cd83e8f7ad64b : declared interface
    C8900f90ae594 <|-- C9d9260e84407 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cd83e8f7ad64b` | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` (this JAR) | this diagram |
| `C9d9260e84407` | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` (this JAR) | this diagram |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` / method signature: `public java.lang.String getProduct();` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onGetColumns();`<br>`private java.lang.String onUpdateRecentColumns(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onGetViews();`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onChangeView(java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onUpdateRecentColumns(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onChangeView(java.util.Map<java.lang.String, java.lang.String[]>);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.Results.impl.DatabankViews.DatabankViewsServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);
    private java.lang.String onGetColumns();
    private java.lang.String onUpdateRecentColumns(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onGetViews();
    private java.lang.String onAddView(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onUpdateView(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onRemoveView(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onChangeView(java.util.Map<java.lang.String, java.lang.String[]>);
    private void sendDataUpdate();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
