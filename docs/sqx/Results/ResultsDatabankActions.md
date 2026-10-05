# ResultsDatabankActions.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/ResultsDatabankActions.jar`.
- SHA-256: `2542b663f56004be15797da27f223903b78eea4a0208a28754d741737755cc74`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **2**; nested/anonymous: **1**.
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

### 1. `com.strategyquant.plugin.Results.impl.DatabankActions`

```mermaid
classDiagram
    class C4912fd651ac4["DatabankActionsPlugin"] {
        -dataContext
        -servlet
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +call()
    }
    class C3eef0042cf0c["DatabankActionsServlet"] {
        -Log
        -strategyConfig
        #execute()
    }
    class C1b6b4448b67b["IProgram"]
    class C249b5c671b1a["IServletPlugin"]
    class C92c3bb2ab146["StrategyConfig"]
    class C8900f90ae594["HttpJSONServlet"]
    C249b5c671b1a <|.. C4912fd651ac4 : declared interface
    C1b6b4448b67b <|.. C4912fd651ac4 : declared interface
    C4912fd651ac4 ..> C3eef0042cf0c : field type
    C8900f90ae594 <|-- C3eef0042cf0c : declared extends
    C3eef0042cf0c ..> C92c3bb2ab146 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C4912fd651ac4` | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` (this JAR) | this diagram |
| `C3eef0042cf0c` | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C92c3bb2ab146` | [`com.strategyquant.tradinglib.strategyConfig.StrategyConfig`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | class | non-nested |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / class declaration: `public class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / field declaration: `private com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet servlet;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / class declaration: `public class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | [`com.strategyquant.tradinglib.strategyConfig.StrategyConfig`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / field declaration: `private com.strategyquant.tradinglib.strategyConfig.StrategyConfig strategyConfig;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onCompareStrategies(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onExportDatabankToCSV(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void exportDatabankContents(com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onSaveStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static void access$000(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onCompareStrategies(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onExportDatabankToCSV(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onCompareStrategies(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onExportDatabankToCSV(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void exportDatabankContents(com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onSaveStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static void access$000(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / method signature: `private void exportDatabankContents(com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static void access$000(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | `com.strategyquant.lib.ValuesMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` / method signature: `private com.strategyquant.lib.ValuesMap buildAllParamTypes();` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / class declaration: `class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / field declaration: `final com.strategyquant.tradinglib.Databank val$databank;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | [`com.strategyquant.tradinglib.Databank`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / method signature: `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String);` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / field declaration: `final java.lang.String val$path;`<br>`final java.lang.String val$_strategiesSorted;`<br>`final java.lang.String val$view;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / method signature: `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String);` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / field declaration: `final com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet this$0;` |
| `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1` / method signature: `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin</summary>

```text
public class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet servlet;
    public com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet</summary>

```text
public class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private com.strategyquant.tradinglib.strategyConfig.StrategyConfig strategyConfig;
    public com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onCompareStrategies(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onExportDatabankToCSV(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void exportDatabankContents(com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;
    private java.lang.String onSaveStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onGetStrategyXml(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onGetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onSetStrategyParameters(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private com.strategyquant.tradinglib.Databank getDatabank(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private com.strategyquant.lib.ValuesMap buildAllParamTypes();
    static void access$000(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1</summary>

```text
class com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1 extends java.lang.Thread
    final com.strategyquant.tradinglib.Databank val$databank;
    final java.lang.String val$path;
    final java.lang.String val$_strategiesSorted;
    final boolean val$_useComma;
    final java.lang.String val$view;
    final com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet this$0;
    com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet$1(com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet, com.strategyquant.tradinglib.Databank, java.lang.String, java.lang.String, boolean, java.lang.String);
    public void run();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
