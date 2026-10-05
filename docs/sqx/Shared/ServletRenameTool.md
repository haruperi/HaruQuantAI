# ServletRenameTool.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/ServletRenameTool/ServletRenameTool.jar`.
- SHA-256: `ebe6f9347a0c34737dafa1df96f5c381ccc532d3c431940189de4952bd638388`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **4**; non-nested: **4**; nested/anonymous: **0**.
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

### 1. `com.strategyquant.plugin.Servlet.impl.RenameTool`

```mermaid
classDiagram
    class C0c430da188b2["RenameToolGenerator"] {
        -Log
        -NO_VALUE
        -strategyNumber
        +processStrategy()
    }
    class Ce87843eb33ee["RenameToolServlet"] {
        -Log
        -lockName
        #execute()
    }
    class C6636e0736a0d["RenameToolServletPlugin"] {
        -dataContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
    }
    class C88c3a20a1e96["RenameToolSettings"] {
        -Log
        -configFilePath
        +SN_Markets
        +load()
    }
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C8900f90ae594 <|-- Ce87843eb33ee : declared extends
    C249b5c671b1a <|.. C6636e0736a0d : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C0c430da188b2` | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` (this JAR) | this diagram |
| `Ce87843eb33ee` | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` (this JAR) | this diagram |
| `C6636e0736a0d` | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` (this JAR) | this diagram |
| `C88c3a20a1e96` | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` (this JAR) | this diagram |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` | class | non-nested |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / field declaration: `private static java.lang.String NO_VALUE;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / method signature: `private static java.lang.String getValue(java.util.HashMap<java.lang.String, java.lang.String>, java.lang.String);`<br>`private static java.lang.String getNumber(java.lang.String);`<br>`private static java.lang.String getStrategyId(java.lang.String);`<br>`private static java.lang.String getTimeRangeHour(org.jdom2.Element);` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | [`com.strategyquant.tradinglib.ResultsGroup`](SQTradingLib.md) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / method signature: `public static void processStrategy(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / method signature: `public static void processStrategy(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | `java.util.HashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / method signature: `private static java.lang.String getValue(java.util.HashMap<java.lang.String, java.lang.String>, java.lang.String);` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator` / method signature: `private static boolean isUsed(org.jdom2.Element);`<br>`private static java.lang.String getTimeRangeHour(org.jdom2.Element);` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](SQWebGUILib.md) | extends | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` / field declaration: `private static final java.lang.String lockName;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onRename(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onRename(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onRename(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](SQTradingLib.md) | implements | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` / class declaration: `public class com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` / method signature: `public java.lang.String getProduct();` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / field declaration: `private static final java.lang.String configFilePath;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_Markets;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_TimeFrames;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_OrderTypes;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_Indicators;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> MN_Markets;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> MN_TimeFrames;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / method signature: `private static void loadValues(org.jdom2.Element, java.lang.String, java.util.HashMap<java.lang.String, java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `java.util.LinkedHashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / field declaration: `public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_Markets;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_TimeFrames;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_OrderTypes;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_Indicators;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> MN_Markets;`<br>`public static java.util.LinkedHashMap<java.lang.String, java.lang.String> MN_TimeFrames;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / method signature: `private static void loadValues(org.jdom2.Element, java.lang.String, java.util.HashMap<java.lang.String, java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `java.util.HashMap` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / method signature: `private static void loadValues(org.jdom2.Element, java.lang.String, java.util.HashMap<java.lang.String, java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` / method signature: `private static void loadValues(org.jdom2.Element, java.lang.String, java.util.HashMap<java.lang.String, java.lang.String>) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator
    private static final org.slf4j.Logger Log;
    private static java.lang.String NO_VALUE;
    private static int strategyNumber;
    public com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolGenerator();
    public static void processStrategy(com.strategyquant.tradinglib.ResultsGroup) throws java.lang.Exception;
    private static java.lang.String getValue(java.util.HashMap<java.lang.String, java.lang.String>, java.lang.String);
    private static java.lang.String getNumber(java.lang.String);
    private static java.lang.String getStrategyId(java.lang.String);
    private static boolean isUsed(org.jdom2.Element);
    private static java.lang.String getTimeRangeHour(org.jdom2.Element);
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.lang.String lockName;
    public com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onRename(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolServletPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

<details>
<summary>com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings</summary>

```text
public class com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings
    private static final org.slf4j.Logger Log;
    private static final java.lang.String configFilePath;
    public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_Markets;
    public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_TimeFrames;
    public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_OrderTypes;
    public static java.util.LinkedHashMap<java.lang.String, java.lang.String> SN_Indicators;
    public static java.util.LinkedHashMap<java.lang.String, java.lang.String> MN_Markets;
    public static java.util.LinkedHashMap<java.lang.String, java.lang.String> MN_TimeFrames;
    public com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings();
    public static void load();
    private static void loadValues(org.jdom2.Element, java.lang.String, java.util.HashMap<java.lang.String, java.lang.String>) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
