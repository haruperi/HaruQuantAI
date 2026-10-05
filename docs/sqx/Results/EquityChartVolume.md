# EquityChartVolume.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/EquityChartVolume/EquityChartVolume.jar`.
- SHA-256: `5cf96acea98addb47b86d599117d0e97c77321230250ec94a18f05a3588da8a8`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **1**; non-nested: **1**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.EquityChart.impl.Volume`

```mermaid
classDiagram
    class C75e391431ee6["EquityChartVolume"] {
        -Auto
        -Size
        -Money
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +print()
    }
    class C192f9089a204["IEquityChartAddon"]
    C192f9089a204 <|.. C75e391431ee6 : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C75e391431ee6` | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` (this JAR) | this diagram |
| `C192f9089a204` | [`com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon`](../Shared/SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | [`com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / class declaration: `public class com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume implements com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `public java.lang.String getProduct();`<br>`public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`public java.lang.String getName();` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private double getVolume(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order, byte) throws java.lang.Exception;`<br>`private com.strategyquant.datalib.InstrumentInfo getInstrumentInfo(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order) throws java.lang.Exception;` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | [`com.strategyquant.tradinglib.equitychart.EquityChart`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | [`com.strategyquant.tradinglib.ResultsGroup`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private double getVolume(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order, byte) throws java.lang.Exception;`<br>`private byte getVolumeType(com.strategyquant.tradinglib.ResultsGroup, byte);`<br>`private com.strategyquant.datalib.InstrumentInfo getInstrumentInfo(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order) throws java.lang.Exception;` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | [`com.strategyquant.tradinglib.OrdersList`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | [`com.strategyquant.tradinglib.Order`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `private double getVolume(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order, byte) throws java.lang.Exception;`<br>`private com.strategyquant.datalib.InstrumentInfo getInstrumentInfo(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order) throws java.lang.Exception;` |
| `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` | [`com.strategyquant.datalib.InstrumentInfo`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume` / method signature: `private com.strategyquant.datalib.InstrumentInfo getInstrumentInfo(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume</summary>

```text
public class com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume implements com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon
    private static byte Auto;
    private static byte Size;
    private static byte Money;
    private static byte Off;
    public com.strategyquant.plugin.EquityChart.impl.Volume.EquityChartVolume();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public void print(com.strategyquant.tradinglib.equitychart.EquityChart, com.strategyquant.tradinglib.ResultsGroup, java.lang.String, com.strategyquant.tradinglib.OrdersList, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private double getVolume(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order, byte) throws java.lang.Exception;
    private byte getVolumeType(com.strategyquant.tradinglib.ResultsGroup, byte);
    private com.strategyquant.datalib.InstrumentInfo getInstrumentInfo(com.strategyquant.tradinglib.ResultsGroup, com.strategyquant.tradinglib.Order) throws java.lang.Exception;
    public java.lang.String getName();
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
