# ServletConstants.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar`.
- SHA-256: `0269ef64e3e4318025b53301ebb61eeef39c585f751ad4a5dd11425687928acf`.
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

### 1. `com.strategyquant.plugin.Servlet.impl.Constants`

```mermaid
classDiagram
    class Cf483e7a90b54["ConstantsServlet"] {
        -Log
        -instance
        -getAllResponse
        +getInstance()
        #execute()
    }
    class C0297a4cfa75e["ConstantsServletPlugin"] {
        -connectionContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
    }
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- Cf483e7a90b54 : declared extends
    C249b5c671b1a <|.. C0297a4cfa75e : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cf483e7a90b54` | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` (this JAR) | this diagram |
| `C0297a4cfa75e` | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` (this JAR) | this diagram |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` / field declaration: `private java.lang.String getAllResponse;` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onGetAll();`<br>`private java.lang.String onListCommissionMethods();` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` / method signature: `private org.json.JSONArray getCommissionMethodsJSON();` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler connectionContext;` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` / method signature: `public java.lang.String getProduct();` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet instance;
    private java.lang.String getAllResponse;
    public com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet();
    public static com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet getInstance();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);
    private java.lang.String onGetAll();
    private java.lang.String onListCommissionMethods();
    private org.json.JSONArray getCommissionMethodsJSON();
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler connectionContext;
    public com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServletPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
