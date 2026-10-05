# ServletConnection.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar`.
- SHA-256: `7e254197a8e29bad9601b7235af0e58ef696c159508c96170465c847b48cd54b`.
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

### 1. `com.strategyquant.plugin.Servlet.impl.Connection`

```mermaid
classDiagram
    class C40950a50aaa4["ConnectionServlet"] {
        -Log
        -connManager
        -instance
        +getInstance()
        #execute()
        +onList()
    }
    class C42eec2186297["ConnectionServletPlugin"] {
        -connectionContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
    }
    class C001b68001ef7["ConnectionManager"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- C40950a50aaa4 : declared extends
    C40950a50aaa4 ..> C001b68001ef7 : field type
    C249b5c671b1a <|.. C42eec2186297 : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C40950a50aaa4` | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` (this JAR) | this diagram |
| `C42eec2186297` | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` (this JAR) | this diagram |
| `C001b68001ef7` | [`com.strategyquant.tradinglib.connection.ConnectionManager`](SQTradingLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` | [`com.strategyquant.tradinglib.connection.ConnectionManager`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` / field declaration: `private com.strategyquant.tradinglib.connection.ConnectionManager connManager;` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` / method signature: `protected java.lang.String execute(java.lang.String, org.json.JSONObject);`<br>`private java.lang.String onAdd(org.json.JSONObject);`<br>`public java.lang.String onList();`<br>`private java.lang.String onListPlugins();`<br>`private java.lang.String onRemove(org.json.JSONObject);`<br>`private java.lang.String onEdit(org.json.JSONObject);`<br>`private java.lang.String onConnect(org.json.JSONObject);`<br>`private java.lang.String onDisconnect(org.json.JSONObject);`<br>`private java.lang.String onIsActive(org.json.JSONObject);` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet` / method signature: `protected java.lang.String execute(java.lang.String, org.json.JSONObject);`<br>`private java.lang.String onAdd(org.json.JSONObject);`<br>`private java.lang.String onRemove(org.json.JSONObject);`<br>`private java.lang.String onEdit(org.json.JSONObject);`<br>`private java.lang.String onConnect(org.json.JSONObject);`<br>`private java.lang.String onDisconnect(org.json.JSONObject);`<br>`private java.lang.String onIsActive(org.json.JSONObject);` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler connectionContext;` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` / method signature: `public java.lang.String getProduct();` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private com.strategyquant.tradinglib.connection.ConnectionManager connManager;
    private static com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet instance;
    public com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet();
    public static com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet getInstance();
    protected java.lang.String execute(java.lang.String, org.json.JSONObject);
    private java.lang.String onAdd(org.json.JSONObject);
    public java.lang.String onList();
    private java.lang.String onListPlugins();
    private java.lang.String onRemove(org.json.JSONObject);
    private java.lang.String onEdit(org.json.JSONObject);
    private java.lang.String onConnect(org.json.JSONObject);
    private java.lang.String onDisconnect(org.json.JSONObject);
    private java.lang.String onIsActive(org.json.JSONObject);
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler connectionContext;
    public com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServletPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
