# DataSourceSQEquityData.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/DataSourceSQEquityData.jar`.
- SHA-256: `4775cfdc7055c32fb6368e60d4e755f8e1c1e71945b316994b0db3038251107c`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **5**; non-nested: **2**; nested/anonymous: **3**.
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

### 1. `com.strategyquant.plugin.DataSource.impl.SQEquityData`

```mermaid
classDiagram
    class C8d605cfe6a2a["SQEquityDataPlugin"] {
        -servlet
        -dataContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +call()
    }
    class C7398371c2d84["SQEquityDataServlet"] {
        -JOB_PREFIX
        -Log
        -canceled
        #execute()
    }
    class C1b6b4448b67b["IProgram"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C249b5c671b1a <|.. C8d605cfe6a2a : declared interface
    C1b6b4448b67b <|.. C8d605cfe6a2a : declared interface
    C8d605cfe6a2a ..> C7398371c2d84 : field type
    C8900f90ae594 <|-- C7398371c2d84 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C8d605cfe6a2a` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` (this JAR) | this diagram |
| `C7398371c2d84` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` | class | nested/anonymous |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` | class | nested/anonymous |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / field declaration: `private com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet servlet;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / field declaration: `private static final java.lang.String JOB_PREFIX;`<br>`private java.lang.String exchangesResponse;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetExchanges() throws java.lang.Exception;`<br>`private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onAddCancel() throws java.lang.Exception;`<br>`private void subscriptionCheck(java.lang.String[], boolean) throws java.lang.Exception;`<br>`private java.lang.String onLookup(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdate() throws java.lang.Exception;`<br>`private java.lang.String performUpdate(java.util.ArrayList<com.strategyquant.datalib.DataInfo>) throws java.lang.Exception;`<br>`private java.lang.String onVerifySubscription(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateAll() throws java.lang.Exception;`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private static java.lang.String lambda$performUpdate$2(com.strategyquant.datalib.DataInfo);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onLookup(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onVerifySubscription(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static void access$000(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetExchanges() throws java.lang.Exception;`<br>`private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddCancel() throws java.lang.Exception;`<br>`private void subscriptionCheck(java.lang.String[], boolean) throws java.lang.Exception;`<br>`private java.lang.String onLookup(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdate() throws java.lang.Exception;`<br>`private java.lang.String performUpdate(java.util.ArrayList<com.strategyquant.datalib.DataInfo>) throws java.lang.Exception;`<br>`private java.lang.String onVerifySubscription(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onUpdateAll() throws java.lang.Exception;`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / method signature: `private java.lang.String performUpdate(java.util.ArrayList<com.strategyquant.datalib.DataInfo>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | [`com.strategyquant.datalib.DataInfo`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / method signature: `private java.lang.String performUpdate(java.util.ArrayList<com.strategyquant.datalib.DataInfo>) throws java.lang.Exception;`<br>`private boolean isDownloadAllowed(com.strategyquant.datalib.DataInfo);`<br>`private static java.lang.String lambda$performUpdate$2(com.strategyquant.datalib.DataInfo);`<br>`private static boolean lambda$performUpdate$1(com.strategyquant.datalib.DataInfo);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | [`com.strategyquant.datalib.historyData.dto.TickerDto`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` / method signature: `private static com.strategyquant.datalib.historyData.dto.TickerDto lambda$_onAdd$0(com.strategyquant.datalib.historyData.dto.TickerDto);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` / class declaration: `class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` / field declaration: `final java.util.Map val$args;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` / field declaration: `final com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` | [`com.strategyquant.datalib.data.InstrumentValueEvaluator`](../Shared/SQDataLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` / class declaration: `class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2 implements com.strategyquant.datalib.data.InstrumentValueEvaluator` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` / field declaration: `final com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` / method signature: `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` | [`com.strategyquant.datalib.historyData.dto.TickerDto`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` / method signature: `public double getTickStep(com.strategyquant.datalib.historyData.dto.TickerDto);`<br>`public double getTickSize(com.strategyquant.datalib.historyData.dto.TickerDto);`<br>`public double getPointValue(com.strategyquant.datalib.historyData.dto.TickerDto);`<br>`public byte getInstrumentType(com.strategyquant.datalib.historyData.dto.TickerDto);`<br>`public java.lang.String getDescriptions(com.strategyquant.datalib.historyData.dto.TickerDto);`<br>`public double getOrderSizeMultiplier(com.strategyquant.datalib.historyData.dto.TickerDto);`<br>`public double getOrderSizeStep(com.strategyquant.datalib.historyData.dto.TickerDto);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2` / method signature: `public java.lang.String getDescriptions(com.strategyquant.datalib.historyData.dto.TickerDto);` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | [`com.strategyquant.datalib.data.BatchProgressController`](../Shared/SQDataLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / class declaration: `class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3 implements com.strategyquant.datalib.data.BatchProgressController` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / field declaration: `final org.json.JSONObject val$progress;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | `java.util.Set` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / field declaration: `final java.util.Set val$symbolsSet;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / field declaration: `final java.lang.String[] val$symbols;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / method signature: `public void updateProgress(int, int, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / field declaration: `final com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3` / method signature: `public void updateProgress(int, int, java.lang.String) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    private com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet servlet;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final java.lang.String JOB_PREFIX;
    private static final org.slf4j.Logger Log;
    private boolean canceled;
    private java.lang.String exchangesResponse;
    public com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onGetExchanges() throws java.lang.Exception;
    private java.lang.String onAdd(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onAddCancel() throws java.lang.Exception;
    private void subscriptionCheck(java.lang.String[], boolean) throws java.lang.Exception;
    private java.lang.String onLookup(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onUpdate() throws java.lang.Exception;
    private java.lang.String performUpdate(java.util.ArrayList<com.strategyquant.datalib.DataInfo>) throws java.lang.Exception;
    private boolean isDownloadAllowed(com.strategyquant.datalib.DataInfo);
    private java.lang.String onVerifySubscription(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onUpdateDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onUpdateAll() throws java.lang.Exception;
    private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private static java.lang.String lambda$performUpdate$2(com.strategyquant.datalib.DataInfo);
    private static boolean lambda$performUpdate$1(com.strategyquant.datalib.DataInfo);
    private static com.strategyquant.datalib.historyData.dto.TickerDto lambda$_onAdd$0(com.strategyquant.datalib.historyData.dto.TickerDto);
    static void access$000(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet, java.util.Map);
    static boolean access$100(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1</summary>

```text
class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1 extends java.lang.Thread
    final java.util.Map val$args;
    final com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet this$0;
    com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$1(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet, java.util.Map);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2</summary>

```text
class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2 implements com.strategyquant.datalib.data.InstrumentValueEvaluator
    final com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet this$0;
    com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$2(com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet);
    public double getTickStep(com.strategyquant.datalib.historyData.dto.TickerDto);
    public double getTickSize(com.strategyquant.datalib.historyData.dto.TickerDto);
    public double getPointValue(com.strategyquant.datalib.historyData.dto.TickerDto);
    public byte getInstrumentType(com.strategyquant.datalib.historyData.dto.TickerDto);
    public java.lang.String getDescriptions(com.strategyquant.datalib.historyData.dto.TickerDto);
    public double getOrderSizeMultiplier(com.strategyquant.datalib.historyData.dto.TickerDto);
    public double getOrderSizeStep(com.strategyquant.datalib.historyData.dto.TickerDto);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3</summary>

```text
class com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3 implements com.strategyquant.datalib.data.BatchProgressController
    final int val$batchSizeForUse;
    final org.json.JSONObject val$progress;
    final java.util.Set val$symbolsSet;
    final java.lang.String[] val$symbols;
    final com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet this$0;
    com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet$3();
    public void updateProgress(int, int, java.lang.String) throws java.lang.Exception;
    public boolean isCancel();
    public void finished();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
