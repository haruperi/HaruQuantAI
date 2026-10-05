# FitnessMethodStrategyResult.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar`.
- SHA-256: `d873f8b2800a34cf815706a98f8951fc80981406e9fccf95a0ebc671c0ee023e`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **4**; non-nested: **2**; nested/anonymous: **2**.
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

### 1. `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult`

```mermaid
classDiagram
    class C633673c3ed9f["FitnessMethodStrategyResult"] {
        +Log
        -dataContext
        -databankColumnName
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +computeFitness()
    }
    class C17750fea9d07["FitnessMethodStrategyResultServlet"] {
        -Log
        #execute()
    }
    class C3c0a91958e1c["FitnessMethodStrategyResult$Goal"]
    class C76653c322567["IFitnessFunction"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C76653c322567 <|.. C633673c3ed9f : declared interface
    C249b5c671b1a <|.. C633673c3ed9f : declared interface
    C633673c3ed9f ..> C3c0a91958e1c : field type
    C8900f90ae594 <|-- C17750fea9d07 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C633673c3ed9f` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` (this JAR) | this diagram |
| `C3c0a91958e1c` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` (this JAR) | another group in this JAR |
| `C17750fea9d07` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` (this JAR) | this diagram |
| `C76653c322567` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | class | non-nested |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1` | class | nested/anonymous |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` | class | nested/anonymous |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | implements | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / class declaration: `public class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / class declaration: `public class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / field declaration: `private java.lang.String databankColumnName;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult(java.lang.String);`<br>`public java.lang.String getProduct();`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;`<br>`public java.lang.String getFitnessKey();`<br>`public java.lang.String getFitnessName();`<br>`public java.lang.String getFitnessDatabankColumnName();`<br>`public java.lang.String printWeightedGoals();`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / field declaration: `private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal> weightedGoals;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;`<br>`public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();`<br>`private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal> cloneGoals();` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / field declaration: `private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal> weightedGoals;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal> cloneGoals();` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;`<br>`private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`public byte getFitnessType() throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;`<br>`private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public void initFitnessFromXml(org.jdom2.Element);` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | [`com.strategyquant.tradinglib.DatabankColumn`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `com.strategyquant.lib.snippets.NonexistingCustomClassException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | [`com.strategyquant.tradinglib.optimization.MetricForFitness`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction clone();` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` | `java.lang.CloneNotSupportedException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` / field declaration: `public java.lang.String statsValueName;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` / field declaration: `final com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult this$0;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` / method signature: `private com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult);`<br>`com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult, com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1);` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1` (this JAR) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal` / method signature: `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult, com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1);` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` / class declaration: `public class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList() throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList() throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult</summary>

```text
public class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin
    public static final org.slf4j.Logger Log;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private java.lang.String databankColumnName;
    private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal> weightedGoals;
    public com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult();
    public com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult(java.lang.String);
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;
    public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;
    private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte, boolean) throws java.lang.Exception;
    private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;
    public void initFitnessFromXml(org.jdom2.Element);
    public org.eclipse.jetty.server.Handler getHandler();
    public byte getFitnessType() throws java.lang.Exception;
    public java.lang.String getFitnessKey();
    public java.lang.String getFitnessName();
    public java.lang.String getFitnessDatabankColumnName();
    public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws com.strategyquant.lib.snippets.NonexistingCustomClassException;
    public java.lang.String printWeightedGoals();
    public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();
    public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;
    public com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction clone();
    private java.util.ArrayList<com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal> cloneGoals();
    public java.lang.Object clone() throws java.lang.CloneNotSupportedException;
```

</details>

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1</summary>

```text
class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1
```

</details>

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal</summary>

```text
class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal
    public byte valueType;
    public boolean use;
    public java.lang.String statsValueName;
    public double weight;
    public double target;
    final com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult this$0;
    private com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult);
    com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$Goal(com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult, com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResult$1);
```

</details>

<details>
<summary>com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet</summary>

```text
public class com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onList() throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
