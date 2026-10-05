# DataSourceYahoo.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/DataSourceYahoo.jar`.
- SHA-256: `30216203401f5014f82d67f53c965c812a83dd1a2dae700550a370698ce6016b`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **5**; non-nested: **4**; nested/anonymous: **1**.
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

### 1. `com.strategyquant.plugin.DataSource.impl.Yahoo`

```mermaid
classDiagram
    class C4f8f27e611fe["DataSourceYahooPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +call()
    }
    class C5156d8cc9762["DataSourceYahooServlet"] {
        -Log
        -canceled
        #execute()
    }
    class Cf7dbd430f2ec["YahooDataManager"] {
        +Log
        -instance
        +get()
        +addData()
        +downloadInfo()
    }
    class Cb00a5842204c["YahooSymbol"] {
        +symbol
        +name
        +exchange
    }
    class C1b6b4448b67b["IProgram"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C249b5c671b1a <|.. C4f8f27e611fe : declared interface
    C1b6b4448b67b <|.. C4f8f27e611fe : declared interface
    C4f8f27e611fe ..> C5156d8cc9762 : field type
    C8900f90ae594 <|-- C5156d8cc9762 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C4f8f27e611fe` | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` (this JAR) | this diagram |
| `C5156d8cc9762` | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` (this JAR) | this diagram |
| `Cf7dbd430f2ec` | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` (this JAR) | this diagram |
| `Cb00a5842204c` | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | class | nested/anonymous |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / field declaration: `private com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet servlet;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>, java.util.ArrayList<com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol>);`<br>`private java.lang.String onAddCancel() throws java.lang.Exception;`<br>`private java.util.ArrayList<java.lang.String> parseSymbols(java.lang.String);`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateAll();`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>, java.util.ArrayList<com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol>);`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`static void access$000(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddCancel() throws java.lang.Exception;`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / method signature: `private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>, java.util.ArrayList<com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol>);`<br>`private java.util.ArrayList<java.lang.String> parseSymbols(java.lang.String);`<br>`static void access$000(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` / method signature: `private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>, java.util.ArrayList<com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol>);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / class declaration: `class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / field declaration: `final java.util.Map val$args;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / field declaration: `final java.util.ArrayList val$yahooSymbols;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / field declaration: `final com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` / method signature: `public java.lang.String addData(java.lang.String, java.lang.String, byte, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getCookieCrumb() throws java.lang.Exception;`<br>`public com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol downloadInfo(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` / method signature: `public java.lang.String addData(java.lang.String, java.lang.String, byte, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String getCookieCrumb() throws java.lang.Exception;`<br>`public com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol downloadInfo(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager` / method signature: `public com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol downloadInfo(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol` / field declaration: `public java.lang.String symbol;`<br>`public java.lang.String name;`<br>`public java.lang.String exchange;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet servlet;
    public com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private boolean canceled;
    public com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>, java.util.ArrayList<com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol>);
    private java.lang.String onAddCancel() throws java.lang.Exception;
    private java.util.ArrayList<java.lang.String> parseSymbols(java.lang.String);
    private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onUpdateAll();
    private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>);
    static void access$000(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1</summary>

```text
class com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1 extends java.lang.Thread
    final java.util.Map val$args;
    final java.util.ArrayList val$yahooSymbols;
    final com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet this$0;
    com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet$1(com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet, java.util.Map, java.util.ArrayList);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager
    public static final org.slf4j.Logger Log;
    private static com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager instance;
    public com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager();
    public static synchronized com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager get();
    public java.lang.String addData(java.lang.String, java.lang.String, byte, java.lang.String, java.lang.String) throws java.lang.Exception;
    private java.lang.String getCookieCrumb() throws java.lang.Exception;
    public com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol downloadInfo(java.lang.String) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol
    public java.lang.String symbol;
    public java.lang.String name;
    public java.lang.String exchange;
    public com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
