# CryptoExchangePoloniex.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex/CryptoExchangePoloniex.jar`.
- SHA-256: `eee8d474a85f56652e1008344876c81c88f4f423b272c4f2423b59b0fd67efa7`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **2**; non-nested: **1**; nested/anonymous: **1**.
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

### 1. `com.strategyquant.plugin.CryptoExchange.impl.Poloniex`

```mermaid
classDiagram
    class Cc67247942ff0["CryptoExchangePoloniexPlugin"] {
        -availableSymbols
        +getName()
        +getSymbols()
        +clone()
        +download()
        +availableTimeframes()
        +convertTimeframe()
    }
    class Cdc5bf0b36300["Exchange"]
    Cdc5bf0b36300 <|-- Cc67247942ff0 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cc67247942ff0` | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` (this JAR) | this diagram |
| `Cdc5bf0b36300` | [`com.strategyquant.tradinglib.exchange.Exchange`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | class | non-nested |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | [`com.strategyquant.tradinglib.exchange.Exchange`](../Shared/SQTradingLib.md) | extends | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / class declaration: `public class com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin extends com.strategyquant.tradinglib.exchange.Exchange` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / field declaration: `private org.json.JSONArray availableSymbols;` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public org.json.JSONArray getSymbols() throws java.lang.Exception;`<br>`private com.strategyquant.datalib.data.io.VersatileData parseData(org.json.JSONArray);`<br>`public org.json.JSONArray availableTimeframes();` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public java.lang.String getName();`<br>`private long getEndOfTime(long, int, java.lang.String) throws java.lang.Exception;`<br>`private long getMinimalDate(java.lang.String);`<br>`public java.lang.String convertTimeframe(java.lang.String) throws java.lang.Exception;`<br>`public boolean checkSymbolExists(java.lang.String);`<br>`public com.strategyquant.tradinglib.exchange.SymbolInfo getSymbolInfo(java.lang.String);` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public org.json.JSONArray getSymbols() throws java.lang.Exception;`<br>`public void download() throws java.lang.Exception;`<br>`private long getEndOfTime(long, int, java.lang.String) throws java.lang.Exception;`<br>`public java.lang.String convertTimeframe(java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | [`com.strategyquant.tradinglib.exchange.IExchange`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public com.strategyquant.tradinglib.exchange.IExchange clone();` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | [`com.strategyquant.datalib.data.io.VersatileData`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `private com.strategyquant.datalib.data.io.VersatileData parseData(org.json.JSONArray);` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | [`com.strategyquant.tradinglib.exchange.SymbolInfo`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public com.strategyquant.tradinglib.exchange.SymbolInfo getSymbolInfo(java.lang.String);` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` | `java.lang.CloneNotSupportedException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` / class declaration: `class com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` (this JAR) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` / field declaration: `final com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin this$0;` |
| `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin` (this JAR) | type dependency | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1` / method signature: `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1(com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin</summary>

```text
public class com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin extends com.strategyquant.tradinglib.exchange.Exchange
    private org.json.JSONArray availableSymbols;
    public com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin();
    public java.lang.String getName();
    public org.json.JSONArray getSymbols() throws java.lang.Exception;
    public com.strategyquant.tradinglib.exchange.IExchange clone();
    public void download() throws java.lang.Exception;
    private long getEndOfTime(long, int, java.lang.String) throws java.lang.Exception;
    private long getMinimalDate(java.lang.String);
    private com.strategyquant.datalib.data.io.VersatileData parseData(org.json.JSONArray);
    public org.json.JSONArray availableTimeframes();
    public java.lang.String convertTimeframe(java.lang.String) throws java.lang.Exception;
    public boolean checkSymbolExists(java.lang.String);
    public com.strategyquant.tradinglib.exchange.SymbolInfo getSymbolInfo(java.lang.String);
    public java.lang.Object clone() throws java.lang.CloneNotSupportedException;
```

</details>

<details>
<summary>com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1</summary>

```text
class com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1 extends java.lang.Thread
    final com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin this$0;
    com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin$1(com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin);
    public void run();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
