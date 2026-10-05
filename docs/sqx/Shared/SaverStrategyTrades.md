# SaverStrategyTrades.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades/SaverStrategyTrades.jar`.
- SHA-256: `cac2b8ccfbbda049ccfbbdfa016488fde36dc5ea4ca93ddaba07eb39b75f2e35`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **1**; non-nested: **1**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Saver.impl.StrategyTrades`

```mermaid
classDiagram
    class C68f7a7d92a8a["StrategyTradesSaverPlugin"] {
        +Log
        +extensions
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getFileExtensions()
        +call()
    }
    class C1b6b4448b67b["IProgram"]
    class C28a2142c6554["ISaverPlugin"]
    C28a2142c6554 <|.. C68f7a7d92a8a : declared interface
    C1b6b4448b67b <|.. C68f7a7d92a8a : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C68f7a7d92a8a` | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](SQPluginLib.md) | referenced external type |
| `C28a2142c6554` | [`com.strategyquant.tradinglib.results.file.ISaverPlugin`](SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | [`com.strategyquant.tradinglib.results.file.ISaverPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / class declaration: `public class com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin implements com.strategyquant.tradinglib.results.file.ISaverPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](SQPluginLib.md) | implements | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / class declaration: `public class com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin implements com.strategyquant.tradinglib.results.file.ISaverPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / field declaration: `public static final java.lang.String[] extensions;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String[] getFileExtensions();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;`<br>`public void save(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;`<br>`public void save(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public void save(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public void save(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | [`com.strategyquant.tradinglib.results.file.ISaverPlugin`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public com.strategyquant.tradinglib.results.file.ISaverPlugin clone();` |
| `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `java.lang.CloneNotSupportedException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin</summary>

```text
public class com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin implements com.strategyquant.tradinglib.results.file.ISaverPlugin,com.strategyquant.pluginlib.program.IProgram
    public static final org.slf4j.Logger Log;
    public static final java.lang.String[] extensions;
    public com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public java.lang.String[] getFileExtensions();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
    public void save(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private boolean shouldShowControlOrders();
    public com.strategyquant.tradinglib.results.file.ISaverPlugin clone();
    public java.lang.Object clone() throws java.lang.CloneNotSupportedException;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
