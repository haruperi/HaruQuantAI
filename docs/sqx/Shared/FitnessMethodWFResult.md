# FitnessMethodWFResult.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar`.
- SHA-256: `67db6d1897747953524e8c79b180e1a0566599d337026aea8885d0cf6f3017fa`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **1**; nested/anonymous: **2**.
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

### 1. `com.strategyquant.plugin.FitnessMethod.impl.WFResult`

```mermaid
classDiagram
    class Cadff3e520e90["FitnessMethodWFResult"] {
        +Log
        +ComputeFromWFResult
        -databankColumnName
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +computeFitness()
    }
    class Cf6aa20b342be["FitnessMethodWFResult$Goal"]
    class C76653c322567["IFitnessFunction"]
    C76653c322567 <|.. Cadff3e520e90 : declared interface
    Cadff3e520e90 ..> Cf6aa20b342be : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cadff3e520e90` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` (this JAR) | this diagram |
| `Cf6aa20b342be` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` (this JAR) | another group in this JAR |
| `C76653c322567` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | class | non-nested |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1` | class | nested/anonymous |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` | class | nested/anonymous |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | implements | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / class declaration: `public class com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / field declaration: `public static final java.lang.String ComputeFromWFResult;`<br>`private java.lang.String databankColumnName;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult(java.lang.String);`<br>`public java.lang.String getProduct();`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;`<br>`public java.lang.String getFitnessKey();`<br>`public java.lang.String getFitnessName();`<br>`public java.lang.String getFitnessDatabankColumnName();`<br>`public java.lang.String printWeightedGoals();`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / field declaration: `private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal> weightedGoals;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;`<br>`public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();`<br>`private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal> cloneGoals();` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / field declaration: `private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal> weightedGoals;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal> cloneGoals();` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;`<br>`private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`public byte getFitnessType() throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;`<br>`private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public void initFitnessFromXml(org.jdom2.Element);` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | [`com.strategyquant.tradinglib.DatabankColumn`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `com.strategyquant.lib.snippets.NonexistingCustomClassException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | [`com.strategyquant.tradinglib.optimization.MetricForFitness`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction clone();` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` | `java.lang.CloneNotSupportedException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` / field declaration: `public java.lang.String statsValueName;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` / field declaration: `final com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult this$0;` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` / method signature: `private com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult);`<br>`com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult, com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1);` |
| `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal` / method signature: `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult, com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult</summary>

```text
public class com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
    public static final org.slf4j.Logger Log;
    public static final java.lang.String ComputeFromWFResult;
    private java.lang.String databankColumnName;
    private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal> weightedGoals;
    public com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult();
    public com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult(java.lang.String);
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;
    public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;
    private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;
    private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;
    public void initFitnessFromXml(org.jdom2.Element);
    public byte getFitnessType() throws java.lang.Exception;
    public java.lang.String getFitnessKey();
    public java.lang.String getFitnessName();
    public java.lang.String getFitnessDatabankColumnName();
    public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;
    public java.lang.String printWeightedGoals();
    public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();
    public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;
    public com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction clone();
    private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal> cloneGoals();
    public java.lang.Object clone() throws java.lang.CloneNotSupportedException;
```

</details>

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1</summary>

```text
class com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1
```

</details>

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal</summary>

```text
class com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal
    public byte valueType;
    public boolean use;
    public java.lang.String statsValueName;
    public double weight;
    public double target;
    final com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult this$0;
    private com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult);
    com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult, com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult$1);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
