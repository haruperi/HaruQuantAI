# DataManagerInstruments.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/DataManagerInstruments.jar`.
- SHA-256: `8703d07e0f552af045ee4af196a533a8469e18bafe7bc9afa88044b48dc012a8`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **2**; nested/anonymous: **1**.
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

### 1. `com.strategyquant.plugin.DataManager.impl.Instruments`

```mermaid
classDiagram
    class C934622d94f07["InstrumentsServlet"] {
        -Log
        #execute()
    }
    class C503563e9b4c2["InstrumentsServletPlugin"] {
        -instrumentsServlet
        -dataContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +call()
    }
    class C1b6b4448b67b["IProgram"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- C934622d94f07 : declared extends
    C249b5c671b1a <|.. C503563e9b4c2 : declared interface
    C1b6b4448b67b <|.. C503563e9b4c2 : declared interface
    C503563e9b4c2 ..> C934622d94f07 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C934622d94f07` | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` (this JAR) | this diagram |
| `C503563e9b4c2` | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | class | non-nested |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` | class | nested/anonymous |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / class declaration: `public class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / method signature: `static org.slf4j.Logger access$000();` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onClone(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String printCommission(java.lang.String);`<br>`private java.lang.String printSwap(java.lang.String);`<br>`private boolean checkFilter(com.strategyquant.datalib.InstrumentInfo, java.lang.String) throws com.strategyquant.datalib.data.DataException;`<br>`private java.lang.String onListInstruments();`<br>`private java.lang.String onListAliases();`<br>`private java.lang.String onAddInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onEditInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onMassEditInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private boolean getBoolean(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onRemoveInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private void removeInstrumentsAsync(java.lang.String[]);`<br>`private java.lang.String onAddAlias(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onEditAlias(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onRemoveAlias(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onLoad(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onSave(java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onClone(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onEditInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onMassEditInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private boolean getBoolean(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);`<br>`private java.lang.String onRemoveInstrument(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onAddAlias(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onEditAlias(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onRemoveAlias(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onLoad(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onSave(java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | [`com.strategyquant.datalib.InstrumentInfo`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / method signature: `private boolean checkFilter(com.strategyquant.datalib.InstrumentInfo, java.lang.String) throws com.strategyquant.datalib.data.DataException;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | [`com.strategyquant.datalib.data.DataException`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` / method signature: `private boolean checkFilter(com.strategyquant.datalib.InstrumentInfo, java.lang.String) throws com.strategyquant.datalib.data.DataException;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` / class declaration: `class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` / field declaration: `final java.lang.String[] val$instruments;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` / method signature: `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1(com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet, java.lang.String[], int);` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` / field declaration: `final com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet this$0;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1` / method signature: `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1(com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet, java.lang.String[], int);` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / class declaration: `public class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / class declaration: `public class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / field declaration: `private com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet instrumentsServlet;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet</summary>

```text
public class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onClone(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String printCommission(java.lang.String);
    private java.lang.String printSwap(java.lang.String);
    private boolean checkFilter(com.strategyquant.datalib.InstrumentInfo, java.lang.String) throws com.strategyquant.datalib.data.DataException;
    private java.lang.String onListInstruments();
    private java.lang.String onListAliases();
    private java.lang.String onAddInstrument(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onEditInstrument(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onMassEditInstrument(java.util.Map<java.lang.String, java.lang.String[]>);
    private boolean getBoolean(java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String);
    private java.lang.String onRemoveInstrument(java.util.Map<java.lang.String, java.lang.String[]>);
    private void removeInstrumentsAsync(java.lang.String[]);
    private java.lang.String onAddAlias(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onEditAlias(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onRemoveAlias(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onLoad(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onSave(java.util.Map<java.lang.String, java.lang.String[]>);
    static org.slf4j.Logger access$000();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1</summary>

```text
class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1 extends java.lang.Thread
    final java.lang.String[] val$instruments;
    final int val$total;
    final com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet this$0;
    com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet$1(com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet, java.lang.String[], int);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin</summary>

```text
public class com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    private com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet instrumentsServlet;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServletPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
