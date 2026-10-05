# ServletStrategy.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar`.
- SHA-256: `03907ceeeaf800838cc8e17d458c4f6bb5c958c043489f517d043071705a7260`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **3**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Servlet.impl.Strategy`

```mermaid
classDiagram
    class Cc7a7cba18ccb["MyStrategy"] {
        +Period
        -count
        +Initialize()
        +OnBarUpdate()
        +callOnInit()
        +getATRValue()
    }
    class C884405185cd8["StrategyServlet"] {
        -Log
        -tradingEngine
        -instance
        +getInstance()
        #execute()
        +onList()
    }
    class Ceebccec50eb5["StrategyServletPlugin"] {
        -strategyContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
    }
    class C75c3b57e2c4b["StrategyBase"]
    class Ce89e51b821b1["TradingEngine"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C75c3b57e2c4b <|-- Cc7a7cba18ccb : declared extends
    C8900f90ae594 <|-- C884405185cd8 : declared extends
    C884405185cd8 ..> Ce89e51b821b1 : field type
    C249b5c671b1a <|.. Ceebccec50eb5 : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cc7a7cba18ccb` | `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` (this JAR) | this diagram |
| `C884405185cd8` | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` (this JAR) | this diagram |
| `Ceebccec50eb5` | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` (this JAR) | this diagram |
| `C75c3b57e2c4b` | [`com.strategyquant.tradinglib.StrategyBase`](SQTradingLib.md) | referenced external type |
| `Ce89e51b821b1` | [`com.strategyquant.tradinglib.engine.TradingEngine`](SQTradingLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` | [`com.strategyquant.tradinglib.StrategyBase`](SQTradingLib.md) | extends | `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy extends com.strategyquant.tradinglib.StrategyBase` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` / method signature: `public void Initialize() throws java.lang.Exception;`<br>`public void OnBarUpdate() throws java.lang.Exception;`<br>`public void callOnInit(com.strategyquant.tradinglib.engine.TradingSetup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` | [`com.strategyquant.tradinglib.engine.TradingSetup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` / method signature: `public void callOnInit(com.strategyquant.tradinglib.engine.TradingSetup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` | [`com.strategyquant.tradinglib.ChartData`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` / method signature: `public double getATRValue(com.strategyquant.tradinglib.ChartData, int, int) throws com.strategyquant.datalib.TradingException;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` | [`com.strategyquant.datalib.TradingException`](SQDataLib.md) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy` / method signature: `public double getATRValue(com.strategyquant.tradinglib.ChartData, int, int) throws com.strategyquant.datalib.TradingException;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` | [`com.strategyquant.tradinglib.engine.TradingEngine`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` / field declaration: `private com.strategyquant.tradinglib.engine.TradingEngine tradingEngine;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` / method signature: `protected java.lang.String execute(java.lang.String, org.json.JSONObject);`<br>`private java.lang.String onAdd(org.json.JSONObject);`<br>`public java.lang.String onList();`<br>`private java.lang.String onRemove(org.json.JSONObject);`<br>`private java.lang.String onStart(org.json.JSONObject);`<br>`private java.lang.String onStop(org.json.JSONObject);` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` | `org.json.JSONObject` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet` / method signature: `protected java.lang.String execute(java.lang.String, org.json.JSONObject);`<br>`private java.lang.String onAdd(org.json.JSONObject);`<br>`private java.lang.String onRemove(org.json.JSONObject);`<br>`private java.lang.String onStart(org.json.JSONObject);`<br>`private java.lang.String onStop(org.json.JSONObject);` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler strategyContext;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` / method signature: `public java.lang.String getProduct();` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy extends com.strategyquant.tradinglib.StrategyBase
    public int Period;
    private int count;
    public com.strategyquant.plugin.Servlet.impl.Strategy.MyStrategy();
    public void Initialize() throws java.lang.Exception;
    public void OnBarUpdate() throws java.lang.Exception;
    public void callOnInit(com.strategyquant.tradinglib.engine.TradingSetup) throws java.lang.Exception;
    public double getATRValue(com.strategyquant.tradinglib.ChartData, int, int) throws com.strategyquant.datalib.TradingException;
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private com.strategyquant.tradinglib.engine.TradingEngine tradingEngine;
    private static com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet instance;
    public com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet();
    public static com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet getInstance();
    protected java.lang.String execute(java.lang.String, org.json.JSONObject);
    private java.lang.String onAdd(org.json.JSONObject);
    public java.lang.String onList();
    private java.lang.String onRemove(org.json.JSONObject);
    private java.lang.String onStart(org.json.JSONObject);
    private java.lang.String onStop(org.json.JSONObject);
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler strategyContext;
    public com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServletPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
