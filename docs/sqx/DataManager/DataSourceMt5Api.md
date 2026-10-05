# DataSourceMt5Api.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/DataSourceMt5Api.jar`.
- SHA-256: `d9868bb340541b513341d0fdef81a76823bb6b8c022face241a4d2de7424d37d`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **4**; non-nested: **2**; nested/anonymous: **2**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `DataManager` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.DataSource.impl.Mt5Api`

```mermaid
classDiagram
    class C972c8f4bae50["DataSourceMt5ApiPlugin"] {
        -dataContext
        -dataSourceFilesServlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +call()
        +getHandler()
    }
    class Cd6cb5a818ec8["DataSourceMt5ApiServlet"] {
        -serialVersionUID
        -formaterDate
        -Log
        #execute()
    }
    class C1b6b4448b67b["IProgram"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C249b5c671b1a <|.. C972c8f4bae50 : declared interface
    C1b6b4448b67b <|.. C972c8f4bae50 : declared interface
    C972c8f4bae50 ..> Cd6cb5a818ec8 : field type
    C8900f90ae594 <|-- Cd6cb5a818ec8 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C972c8f4bae50` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` (this JAR) | this diagram |
| `Cd6cb5a818ec8` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` | class | nested/anonymous |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / field declaration: `private com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet dataSourceFilesServlet;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | `org.joda.time.format.DateTimeFormatter` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / field declaration: `org.joda.time.format.DateTimeFormatter formaterDate;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String updateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onLoadAvailableSymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onImportData(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String addData(com.strategyquant.tradinglib.mt5api.Mt5ApiManager$Source, java.lang.String, java.lang.String, java.lang.String, int, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onImportAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String updateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onLoadAvailableSymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onImportData(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onImportAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static void access$000(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String updateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onLoadAvailableSymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String addData(com.strategyquant.tradinglib.mt5api.Mt5ApiManager$Source, java.lang.String, java.lang.String, java.lang.String, int, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onImportAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | [`com.strategyquant.tradinglib.mt5api.Mt5ApiManager$Source`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` / method signature: `private java.lang.String addData(com.strategyquant.tradinglib.mt5api.Mt5ApiManager$Source, java.lang.String, java.lang.String, java.lang.String, int, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` | `java.util.Comparator` (not resolved in scoped archives) | implements | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` / class declaration: `class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1 implements java.util.Comparator<org.json.JSONObject>` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` / field declaration: `final com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet);` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` / method signature: `public int compare(org.json.JSONObject, org.json.JSONObject);` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1` / method signature: `public int compare(java.lang.Object, java.lang.Object);` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` / class declaration: `class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2 extends java.lang.Thread` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` / field declaration: `final java.util.Map val$args;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` / method signature: `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` / field declaration: `final com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2` / method signature: `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet, java.util.Map);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet dataSourceFilesServlet;
    public com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final long serialVersionUID;
    org.joda.time.format.DateTimeFormatter formaterDate;
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String updateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onLoadAvailableSymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void _onImportData(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String addData(com.strategyquant.tradinglib.mt5api.Mt5ApiManager$Source, java.lang.String, java.lang.String, java.lang.String, int, java.lang.String) throws java.lang.Exception;
    private java.lang.String onImportAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    static void access$000(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet, java.util.Map);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1</summary>

```text
class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1 implements java.util.Comparator<org.json.JSONObject>
    final com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet this$0;
    com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$1(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet);
    public int compare(org.json.JSONObject, org.json.JSONObject);
    public int compare(java.lang.Object, java.lang.Object);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2</summary>

```text
class com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2 extends java.lang.Thread
    final java.util.Map val$args;
    final com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet this$0;
    com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet$2(com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet, java.util.Map);
    public void run();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
