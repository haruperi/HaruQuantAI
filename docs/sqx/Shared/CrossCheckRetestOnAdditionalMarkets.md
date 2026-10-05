# CrossCheckRetestOnAdditionalMarkets.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar`.
- SHA-256: `531c66823aef77bd1f04b344a9f5e1da9de842bbd17926d3844a91cfcc200e25`.
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

### 1. `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets`

```mermaid
classDiagram
    class Cb038a029d5b6["RetestOnAdditionalMarkets"] {
        -dataContext
        -SETTING_SLIPPAGES
        -SETTING_MIN_DISTANCES
        +clone()
        +getName()
        +getShortName()
        +getDescription()
    }
    class Cac007ded8052["RetestOnAdditionalMarketsServlet"] {
        -Log
        #execute()
    }
    class C2e508902bd31["RetestOnAdditionalMarkets$Goal"]
    class C48ebe6aea0c9["CrossCheckMethod"]
    class C76653c322567["IFitnessFunction"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C48ebe6aea0c9 <|-- Cb038a029d5b6 : declared extends
    C76653c322567 <|.. Cb038a029d5b6 : declared interface
    C249b5c671b1a <|.. Cb038a029d5b6 : declared interface
    Cb038a029d5b6 ..> C2e508902bd31 : field type
    C8900f90ae594 <|-- Cac007ded8052 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `Cb038a029d5b6` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` (this JAR) | this diagram |
| `C2e508902bd31` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` (this JAR) | another group in this JAR |
| `Cac007ded8052` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` (this JAR) | this diagram |
| `C48ebe6aea0c9` | [`com.strategyquant.tradinglib.crosscheck.CrossCheckMethod`](SQTradingLib.md) | referenced external type |
| `C76653c322567` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | class | non-nested |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` | class | nested/anonymous |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` | class | nested/anonymous |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.crosscheck.CrossCheckMethod`](SQTradingLib.md) | extends | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / class declaration: `public class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets extends com.strategyquant.tradinglib.crosscheck.CrossCheckMethod implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | implements | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / class declaration: `public class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets extends com.strategyquant.tradinglib.crosscheck.CrossCheckMethod implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / class declaration: `public class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets extends com.strategyquant.tradinglib.crosscheck.CrossCheckMethod implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / field declaration: `private static final java.lang.String SETTING_SLIPPAGES;`<br>`private static final java.lang.String SETTING_MIN_DISTANCES;`<br>`private static final java.lang.String SETTING_COMMISSIONS;`<br>`private static final java.lang.String SETTING_SWAPS;`<br>`private static final java.lang.String SETTING_USE_MAIN_TEST_DATE;`<br>`private static final java.lang.String ConditionsCheckAdditionalMarkets;`<br>`private static final java.lang.String ConditionsMinConds;`<br>`private static final java.lang.String ConditionsMinMarkets;`<br>`private java.lang.String databankColumnName;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public java.lang.String getName();`<br>`public java.lang.String getShortName();`<br>`public java.lang.String getDescription();`<br>`public java.lang.String getSettingName();`<br>`public boolean runTest(com.strategyquant.tradinglib.ResultsGroup, int, double, com.strategyquant.gridlib.client.GridJob, boolean, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup testWithThisSetup(com.strategyquant.lib.SettingsMap, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ChartSetup applyAdditionalChart(com.strategyquant.tradinglib.ChartSetup, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`public double getStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public boolean hasStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String printSpecialValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String getColumnTitle(java.lang.String, org.jdom2.Element, java.lang.Object...);`<br>`public java.lang.String getColumnTitleTemplate();`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte) throws java.lang.Exception;`<br>`public java.lang.String getFitnessKey();`<br>`public java.lang.String getFitnessName();`<br>`public java.lang.String getFitnessDatabankColumnName();`<br>`public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;`<br>`public java.lang.String printWeightedGoals() throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / field declaration: `private java.util.ArrayList<com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal> weightedGoals;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.util.ArrayList` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws java.lang.Exception;`<br>`public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` (this JAR) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / field declaration: `private java.util.ArrayList<com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal> weightedGoals;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.crosscheck.ICrossCheck`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public com.strategyquant.tradinglib.crosscheck.ICrossCheck clone(com.strategyquant.lib.SettingsMap);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `com.strategyquant.lib.SettingsMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public com.strategyquant.tradinglib.crosscheck.ICrossCheck clone(com.strategyquant.lib.SettingsMap);`<br>`private com.strategyquant.tradinglib.ResultsGroup testWithThisSetup(com.strategyquant.lib.SettingsMap, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public void fixSettings(org.jdom2.Element);`<br>`public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;`<br>`public double getStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`private int getMarketIndex(org.jdom2.Element, java.lang.Object...);`<br>`public boolean hasStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String printSpecialValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String getColumnTitle(java.lang.String, org.jdom2.Element, java.lang.Object...);`<br>`public void initFitnessFromXml(org.jdom2.Element);`<br>`public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.task.settings.TaskSettingsData`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;`<br>`public boolean runTest(com.strategyquant.tradinglib.ResultsGroup, int, double, com.strategyquant.gridlib.client.GridJob, boolean, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup testWithThisSetup(com.strategyquant.lib.SettingsMap, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ChartSetup applyAdditionalChart(com.strategyquant.tradinglib.ChartSetup, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`public double getStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public boolean hasStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String printSpecialValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte) throws java.lang.Exception;`<br>`private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public byte getFitnessType() throws java.lang.Exception;`<br>`public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws java.lang.Exception;`<br>`public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;`<br>`public java.lang.String printWeightedGoals() throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public boolean runTest(com.strategyquant.tradinglib.ResultsGroup, int, double, com.strategyquant.gridlib.client.GridJob, boolean, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ResultsGroup testWithThisSetup(com.strategyquant.lib.SettingsMap, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`protected boolean checkConditions(com.strategyquant.tradinglib.ResultsGroup, int);`<br>`protected boolean checkAdditionalMarketConditions(com.strategyquant.tradinglib.ResultsGroup, int);`<br>`public double getStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public boolean hasStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String printSpecialValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;`<br>`private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte) throws java.lang.Exception;`<br>`private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;`<br>`public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.gridlib.client.GridJob`](SQGridLib2.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public boolean runTest(com.strategyquant.tradinglib.ResultsGroup, int, double, com.strategyquant.gridlib.client.GridJob, boolean, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.project.ILastEventListener`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public boolean runTest(com.strategyquant.tradinglib.ResultsGroup, int, double, com.strategyquant.gridlib.client.GridJob, boolean, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.ChartSetup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `private com.strategyquant.tradinglib.ResultsGroup testWithThisSetup(com.strategyquant.lib.SettingsMap, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`private com.strategyquant.tradinglib.ChartSetup applyAdditionalChart(com.strategyquant.tradinglib.ChartSetup, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;`<br>`public com.strategyquant.tradinglib.engine.ChartSetups getChartSetups(com.strategyquant.tradinglib.ChartSetup);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.datalib.DataInfo`](SQDataLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `private long checkHistoryFrom(com.strategyquant.datalib.DataInfo, long);`<br>`private long checkHistoryTo(com.strategyquant.datalib.DataInfo, long);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public double getStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`private int getMarketIndex(org.jdom2.Element, java.lang.Object...);`<br>`public boolean hasStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String printSpecialValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;`<br>`public java.lang.String getColumnTitle(java.lang.String, org.jdom2.Element, java.lang.Object...);`<br>`public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.DatabankColumn`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.engine.ChartSetups`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public com.strategyquant.tradinglib.engine.ChartSetups getChartSetups(com.strategyquant.tradinglib.ChartSetup);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.optimization.MetricForFitness`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | [`com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction clone();` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` | `java.lang.CloneNotSupportedException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` / method signature: `public java.lang.Object clone() throws java.lang.CloneNotSupportedException;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` | [`com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener`](SQTradingLib.md) | implements | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` / class declaration: `class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1 implements com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` (this JAR) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` / field declaration: `final com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets this$0;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` (this JAR) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` / method signature: `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` / field declaration: `public java.lang.String statsValueName;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` (this JAR) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` / field declaration: `final com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets this$0;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets` (this JAR) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` / method signature: `private com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets);`<br>`com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets, com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1` (this JAR) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal` / method signature: `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets, com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1);` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` / class declaration: `public class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList() throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;` |
| `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onList() throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets</summary>

```text
public class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets extends com.strategyquant.tradinglib.crosscheck.CrossCheckMethod implements com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction,com.strategyquant.tradinglib.servlet.IServletPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private static final java.lang.String SETTING_SLIPPAGES;
    private static final java.lang.String SETTING_MIN_DISTANCES;
    private static final java.lang.String SETTING_COMMISSIONS;
    private static final java.lang.String SETTING_SWAPS;
    private static final java.lang.String SETTING_USE_MAIN_TEST_DATE;
    private static final java.lang.String ConditionsCheckAdditionalMarkets;
    private static final java.lang.String ConditionsMinConds;
    private static final java.lang.String ConditionsMinMarkets;
    private java.lang.String databankColumnName;
    private java.util.ArrayList<com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal> weightedGoals;
    public com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets();
    public com.strategyquant.tradinglib.crosscheck.ICrossCheck clone(com.strategyquant.lib.SettingsMap);
    public java.lang.String getName();
    public java.lang.String getShortName();
    public java.lang.String getDescription();
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.String getSettingName();
    public int getType();
    public int getPreferredPosition();
    public int getNumberOfSimulations();
    public boolean doesRetest();
    public boolean doesForEverySetup();
    public void fixSettings(org.jdom2.Element);
    public void readSettings(org.jdom2.Element, com.strategyquant.tradinglib.task.settings.TaskSettingsData) throws java.lang.Exception;
    public boolean runTest(com.strategyquant.tradinglib.ResultsGroup, int, double, com.strategyquant.gridlib.client.GridJob, boolean, com.strategyquant.tradinglib.project.ILastEventListener, java.lang.String) throws java.lang.Exception;
    private com.strategyquant.tradinglib.ResultsGroup testWithThisSetup(com.strategyquant.lib.SettingsMap, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;
    private com.strategyquant.tradinglib.ChartSetup applyAdditionalChart(com.strategyquant.tradinglib.ChartSetup, com.strategyquant.tradinglib.ChartSetup, java.lang.String) throws java.lang.Exception;
    private long checkHistoryFrom(com.strategyquant.datalib.DataInfo, long);
    private long checkHistoryTo(com.strategyquant.datalib.DataInfo, long);
    protected boolean checkConditions(com.strategyquant.tradinglib.ResultsGroup, int);
    protected boolean checkAdditionalMarketConditions(com.strategyquant.tradinglib.ResultsGroup, int);
    public double getStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;
    private int getMarketIndex(org.jdom2.Element, java.lang.Object...);
    public boolean hasStatsValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;
    public java.lang.String printSpecialValue(com.strategyquant.tradinglib.ResultsGroup, java.lang.String, org.jdom2.Element, java.lang.Object...) throws java.lang.Exception;
    public java.lang.String getColumnTitle(java.lang.String, org.jdom2.Element, java.lang.Object...);
    public java.lang.String getColumnTitleTemplate();
    public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;
    public double computeFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte, boolean) throws java.lang.Exception;
    private double getFitnessValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String, double, byte) throws java.lang.Exception;
    private double computeWeightedFitness(com.strategyquant.tradinglib.ResultsGroup, byte, byte) throws java.lang.Exception;
    public java.lang.String getFitnessKey();
    public java.lang.String getFitnessName();
    public void initFitnessFromXml(org.jdom2.Element);
    public byte getFitnessType() throws java.lang.Exception;
    public java.lang.String getFitnessDatabankColumnName();
    public java.util.ArrayList<com.strategyquant.tradinglib.DatabankColumn> getUsedStatValues() throws java.lang.Exception;
    public com.strategyquant.tradinglib.engine.ChartSetups getChartSetups(com.strategyquant.tradinglib.ChartSetup);
    public boolean doesCreateSubjobs();
    public java.lang.String printSettings(org.jdom2.Element) throws java.lang.Exception;
    public java.lang.String printWeightedGoals() throws java.lang.Exception;
    public java.util.ArrayList<com.strategyquant.tradinglib.optimization.MetricForFitness> getMetricsForFitness();
    public double getMetricValue(com.strategyquant.tradinglib.ResultsGroup, byte, byte, java.lang.String) throws java.lang.Exception;
    public int getBadStrategyReason();
    public com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction clone();
    public java.lang.Object clone() throws java.lang.CloneNotSupportedException;
    static void access$000(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets, int);
```

</details>

<details>
<summary>com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1</summary>

```text
class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1 implements com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener
    final com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets this$0;
    com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets);
    public void setProgress(int);
    public void increaseProgressStep();
```

</details>

<details>
<summary>com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal</summary>

```text
class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal
    public boolean use;
    public java.lang.String statsValueName;
    public double weight;
    public double target;
    public byte valueType;
    final com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets this$0;
    private com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets);
    com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$Goal(com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets, com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarkets$1);
```

</details>

<details>
<summary>com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet</summary>

```text
public class com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onList() throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
