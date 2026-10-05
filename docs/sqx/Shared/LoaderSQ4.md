# LoaderSQ4.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar`.
- SHA-256: `4a22421e5c16dc07a0d7da0ea3d5116e71b46a3751001df8a03392ee8c3b86a9`.
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

### 1. `com.strategyquant.plugin.Loader.impl.SQ4`

```mermaid
classDiagram
    class Cf394dba3547d["SQ4LoaderPlugin"] {
        +Log
        +extensions
        -xmlOutputter
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getFileExtensions()
    }
    class Cdee1d566d0b0["ILoaderPlugin"]
    Cdee1d566d0b0 <|.. Cf394dba3547d : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cf394dba3547d` | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` (this JAR) | this diagram |
| `Cdee1d566d0b0` | [`com.strategyquant.tradinglib.results.file.ILoaderPlugin`](SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | [`com.strategyquant.tradinglib.results.file.ILoaderPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / class declaration: `public class com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin implements com.strategyquant.tradinglib.results.file.ILoaderPlugin` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / field declaration: `public static final java.lang.String[] extensions;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.String[] getFileExtensions();`<br>`public com.strategyquant.tradinglib.ResultsGroup load(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup loadSQWFile(java.lang.String, boolean, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup loadSQ4File(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private void loadDailyEquityDataOldFormat(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadDailyEquityData(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `org.jdom2.output.XMLOutputter` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / field declaration: `private org.jdom2.output.XMLOutputter xmlOutputter;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.ResultsGroup load(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup loadSQWFile(java.lang.String, boolean, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup loadSQ4File(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private void loadLastSettings(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadOptimizationProfile(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadCrossCheckData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadResultsData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadDailyEquityDataOldFormat(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadDailyEquityData(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadOrders(com.strategyquant.tradinglib.OrdersList, java.util.jar.JarFile) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.ResultsGroup finishLoad(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `public com.strategyquant.tradinglib.ResultsGroup load(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup loadSQWFile(java.lang.String, boolean, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup loadSQ4File(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;`<br>`private void loadLastSettings(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadOptimizationProfile(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadCrossCheckData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadResultsData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.ResultsGroup finishLoad(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `java.util.jar.JarFile` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `private int recognizeVersion(java.util.jar.JarFile, java.util.jar.JarEntry);`<br>`private void loadLastSettings(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadOptimizationProfile(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadCrossCheckData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadResultsData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadDailyEquityDataOldFormat(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadDailyEquityData(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadOrders(com.strategyquant.tradinglib.OrdersList, java.util.jar.JarFile) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `java.util.jar.JarEntry` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `private int recognizeVersion(java.util.jar.JarFile, java.util.jar.JarEntry);` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `private void fixOldSettingsResultKeys(org.jdom2.Element);` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `java.io.IOException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `private void loadLastSettings(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;`<br>`private void loadOptimizationProfile(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | [`com.strategyquant.tradinglib.Result`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `private void loadDailyEquityDataOldFormat(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;`<br>`private void loadDailyEquityData(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | [`com.strategyquant.tradinglib.OrdersList`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` / method signature: `private void loadOrders(com.strategyquant.tradinglib.OrdersList, java.util.jar.JarFile) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin</summary>

```text
public class com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin implements com.strategyquant.tradinglib.results.file.ILoaderPlugin
    public static final org.slf4j.Logger Log;
    public static final java.lang.String[] extensions;
    private org.jdom2.output.XMLOutputter xmlOutputter;
    public com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public java.lang.String[] getFileExtensions();
    public com.strategyquant.tradinglib.ResultsGroup load(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;
    private com.strategyquant.tradinglib.ResultsGroup loadSQWFile(java.lang.String, boolean, java.lang.String) throws java.lang.Exception;
    private com.strategyquant.tradinglib.ResultsGroup loadSQ4File(java.lang.String, boolean, java.lang.String, java.lang.String) throws java.lang.Exception;
    private int recognizeVersion(java.util.jar.JarFile, java.util.jar.JarEntry);
    private void fixOldSettingsResultKeys(org.jdom2.Element);
    private void loadLastSettings(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;
    private void loadOptimizationProfile(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.io.IOException, java.lang.Exception;
    private void loadCrossCheckData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;
    private void loadResultsData(com.strategyquant.tradinglib.ResultsGroup, java.util.jar.JarFile) throws java.lang.Exception;
    private void loadDailyEquityDataOldFormat(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;
    private void loadDailyEquityData(com.strategyquant.tradinglib.Result, java.lang.String, java.util.jar.JarFile) throws java.lang.Exception;
    private void loadOrders(com.strategyquant.tradinglib.OrdersList, java.util.jar.JarFile) throws java.lang.Exception;
    public com.strategyquant.tradinglib.ResultsGroup finishLoad(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
