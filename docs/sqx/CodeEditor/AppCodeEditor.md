# AppCodeEditor.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar`.
- SHA-256: `55e2e1254d7ac8ed935e40eb09007d3f369279156077c98986fa00b9f463dc08`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **2**; nested/anonymous: **1**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

The `CodeEditor` folder is a navigation/research grouping, not an exclusive backend owner. Shared consumers may use this JAR.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.App.impl.CodeEditor`

```mermaid
classDiagram
    class C90f46d208b19["CodeEditorAppPlugin"] {
        +Log
        +getName()
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getContextPath()
        +getAppCode()
    }
    class C0a03f02fb540["CodeEditorAppPluginException"] {
    }
    class C1b6b4448b67b["IProgram"]
    class C71ae2af47347["IAppPlugin"]
    class C4bc2cd7a4e9d["Exception"]
    C71ae2af47347 <|.. C90f46d208b19 : declared interface
    C1b6b4448b67b <|.. C90f46d208b19 : declared interface
    C4bc2cd7a4e9d <|-- C0a03f02fb540 : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C90f46d208b19` | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` (this JAR) | this diagram |
| `C0a03f02fb540` | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C71ae2af47347` | [`com.strategyquant.tradinglib.plugindef.app.IAppPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C4bc2cd7a4e9d` | `java.lang.Exception` (not resolved in scoped archives) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | class | non-nested |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` | class | nested/anonymous |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | [`com.strategyquant.tradinglib.plugindef.app.IAppPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` / class declaration: `public class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin implements com.strategyquant.tradinglib.plugindef.app.IAppPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` / class declaration: `public class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin implements com.strategyquant.tradinglib.plugindef.app.IAppPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` / method signature: `public java.lang.String getName();`<br>`public java.lang.String getProduct();`<br>`public java.lang.String getContextPath();`<br>`public java.lang.String getAppCode();`<br>`public java.lang.String getTooltip();`<br>`public java.lang.String getProject();`<br>`public java.lang.String getDefaultTaskType();`<br>`public java.lang.String getDefaultTaskName();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` / class declaration: `class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` (this JAR) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` / field declaration: `final com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin this$0;` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin` (this JAR) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` / method signature: `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1(com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin);` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException` | `java.lang.Exception` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException` / class declaration: `public class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException extends java.lang.Exception` |
| `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException` / method signature: `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException(java.lang.String);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin</summary>

```text
public class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin implements com.strategyquant.tradinglib.plugindef.app.IAppPlugin,com.strategyquant.pluginlib.program.IProgram
    public static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin();
    public java.lang.String getName();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public java.lang.String getContextPath();
    public java.lang.String getAppCode();
    public java.lang.String getTooltip();
    public java.lang.String getProject();
    public java.lang.String getDefaultTaskType();
    public java.lang.String getDefaultTaskName();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1</summary>

```text
class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1 extends java.lang.Thread
    final com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin this$0;
    com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1(com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException</summary>

```text
public class com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException extends java.lang.Exception
    com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPluginException(java.lang.String);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
