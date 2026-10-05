# TaskManagerProjects.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar`.
- SHA-256: `6d07140b3c697f54bfebeb17f503347b341f1f10a36abc3ab21ba3793af9fd91`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **2**; non-nested: **2**; nested/anonymous: **0**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `CustomProjects` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.TaskManager.impl.Projects`

```mermaid
classDiagram
    class C5075626c0b0d["TMProjectsPlugin"] {
        +Log
        -dataContext
        -servlet
        +getHandler()
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
    }
    class Ce3bc5fa80dd0["TMProjectsServlet"] {
        -Log
        -FORBIDDEN_PROJECT_NAME_CHARS
        -RESERVED_PROJECT_NAME
        #execute()
    }
    class Cb01a7e55ea2e["ISQPlugin"]
    class C1b6b4448b67b["IProgram"]
    class C3d7572d63292["ProjectNameComparator"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    Cb01a7e55ea2e <|.. C5075626c0b0d : declared interface
    C249b5c671b1a <|.. C5075626c0b0d : declared interface
    C1b6b4448b67b <|.. C5075626c0b0d : declared interface
    C5075626c0b0d ..> Ce3bc5fa80dd0 : field type
    C8900f90ae594 <|-- Ce3bc5fa80dd0 : declared extends
    Ce3bc5fa80dd0 ..> C3d7572d63292 : field type
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C5075626c0b0d` | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` (this JAR) | this diagram |
| `Ce3bc5fa80dd0` | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` (this JAR) | this diagram |
| `Cb01a7e55ea2e` | [`com.strategyquant.pluginlib.ISQPlugin`](../Shared/SQPluginLib.md) | referenced external type |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C3d7572d63292` | [`com.strategyquant.tradinglib.project.ProjectNameComparator`](../Shared/SQTradingLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | class | non-nested |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | [`com.strategyquant.pluginlib.ISQPlugin`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / class declaration: `public class com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin implements com.strategyquant.pluginlib.ISQPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / class declaration: `public class com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin implements com.strategyquant.pluginlib.ISQPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / class declaration: `public class com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin implements com.strategyquant.pluginlib.ISQPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` (this JAR) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / field declaration: `private com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet servlet;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / class declaration: `public class com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `java.util.regex.Pattern` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / field declaration: `private static final java.util.regex.Pattern FORBIDDEN_PROJECT_NAME_CHARS;`<br>`private static final java.util.regex.Pattern RESERVED_PROJECT_NAME;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | [`com.strategyquant.tradinglib.project.ProjectNameComparator`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / field declaration: `private com.strategyquant.tradinglib.project.ProjectNameComparator projectNameComparator;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onListProjects() throws java.lang.Exception;`<br>`private java.lang.String onCreateProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onOpenProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRenameProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onCloneProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private static java.lang.String normalizeProjectName(java.lang.String);`<br>`private static void validateProjectName(java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAddTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetAvailableTasks() throws java.lang.Exception;`<br>`private java.lang.String onMoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRenameTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onCloneTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onActivateTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void tryUpdateProjectConfig(com.strategyquant.tradinglib.project.SQProject, java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onModifySymbolsList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onModifySymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String resolveMarketOpenSessionForSymbol(java.lang.String);`<br>`private void parseSymbols(org.jdom2.Element, java.util.List<java.lang.String>);`<br>`private void modifySymbols(org.jdom2.Element, org.jdom2.Element, org.json.JSONArray, java.util.List<java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onCreateProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onOpenProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRenameProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onCloneProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onMoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRenameTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onCloneTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onActivateTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void tryUpdateProjectConfig(com.strategyquant.tradinglib.project.SQProject, java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onModifySymbolsList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onModifySymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onListProjects() throws java.lang.Exception;`<br>`private java.lang.String onCreateProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onOpenProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onSaveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRenameProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onCloneProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private static void validateProjectName(java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onAddTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRemoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetAvailableTasks() throws java.lang.Exception;`<br>`private java.lang.String onMoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onRenameTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onCloneTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onActivateTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onModifySymbolsList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onModifySymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void modifySymbols(org.jdom2.Element, org.jdom2.Element, org.json.JSONArray, java.util.List<java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | [`com.strategyquant.tradinglib.project.SQProject`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `private void tryUpdateProjectConfig(com.strategyquant.tradinglib.project.SQProject, java.util.Map<java.lang.String, java.lang.String[]>);` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `org.jdom2.Element` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `private void updateSessions(org.jdom2.Element, org.json.JSONArray);`<br>`private void parseSymbols(org.jdom2.Element, java.util.List<java.lang.String>);`<br>`private void updateSpreadInCrossCheckRetestHigherPrecision(org.jdom2.Element, double) throws org.jdom2.JDOMException, java.io.IOException;`<br>`private void modifySymbols(org.jdom2.Element, org.jdom2.Element, org.json.JSONArray, java.util.List<java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `org.json.JSONArray` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `private void updateSessions(org.jdom2.Element, org.json.JSONArray);`<br>`private void modifySymbols(org.jdom2.Element, org.jdom2.Element, org.json.JSONArray, java.util.List<java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `java.util.List` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `private void parseSymbols(org.jdom2.Element, java.util.List<java.lang.String>);`<br>`private void modifySymbols(org.jdom2.Element, org.jdom2.Element, org.json.JSONArray, java.util.List<java.lang.String>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `org.jdom2.JDOMException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `private void updateSpreadInCrossCheckRetestHigherPrecision(org.jdom2.Element, double) throws org.jdom2.JDOMException, java.io.IOException;` |
| `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` | `java.io.IOException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet` / method signature: `private void updateSpreadInCrossCheckRetestHigherPrecision(org.jdom2.Element, double) throws org.jdom2.JDOMException, java.io.IOException;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin</summary>

```text
public class com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin implements com.strategyquant.pluginlib.ISQPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    public static final org.slf4j.Logger Log;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    private com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet servlet;
    public com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsPlugin();
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet</summary>

```text
public class com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    private static final java.util.regex.Pattern FORBIDDEN_PROJECT_NAME_CHARS;
    private static final java.util.regex.Pattern RESERVED_PROJECT_NAME;
    private com.strategyquant.tradinglib.project.ProjectNameComparator projectNameComparator;
    public com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onListProjects() throws java.lang.Exception;
    private java.lang.String onCreateProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onOpenProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onSaveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onRemoveProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onRenameProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onCloneProject(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private static java.lang.String normalizeProjectName(java.lang.String);
    private static void validateProjectName(java.lang.String) throws java.lang.Exception;
    private java.lang.String onAddTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onRemoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onGetAvailableTasks() throws java.lang.Exception;
    private java.lang.String onMoveTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onRenameTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onCloneTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onActivateTask(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void tryUpdateProjectConfig(com.strategyquant.tradinglib.project.SQProject, java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onModifySymbolsList(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onModifySymbols(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void updateSessions(org.jdom2.Element, org.json.JSONArray);
    private java.lang.String resolveMarketOpenSessionForSymbol(java.lang.String);
    private void parseSymbols(org.jdom2.Element, java.util.List<java.lang.String>);
    private void updateSpreadInCrossCheckRetestHigherPrecision(org.jdom2.Element, double) throws org.jdom2.JDOMException, java.io.IOException;
    private void modifySymbols(org.jdom2.Element, org.jdom2.Element, org.json.JSONArray, java.util.List<java.lang.String>) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
