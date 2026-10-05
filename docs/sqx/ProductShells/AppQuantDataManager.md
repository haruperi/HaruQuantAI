# AppQuantDataManager.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/AppQuantDataManager/AppQuantDataManager.jar`.
- SHA-256: `234080d1be94dfc801ede5b8fe287a2142b1d152da4d4a18cad37a6f8fc4cad3`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **3**; non-nested: **2**; nested/anonymous: **1**.
- Inspection: ZIP entry/manifest enumeration and `javap -p` declarations for every listed class.
- Repository source HEAD: `8a92c705183a6702eaf62037ccb202ed028aa899`; review state: generated, pending owner review.
- Installed SQX build number is unverified. No method bodies are reproduced.
- Confidence: high for declared structure; workspace ownership inferred except where registration evidence is separately stated. Runtime reachability, call order, formulas and parity remain unverified.

Product-shell grouping: these registrations are not assumed to be standalone user workspaces.

Target mapping: no verified owning HaruQuantAI feature/requirement/decision IDs are assigned by this document. Register or resolve ownership through the normal repository plan before implementation.

## Diagram reading guide

`Parent <|-- Child` means declared inheritance; `Interface <|.. Class` means declared implementation. Interface extension uses the inheritance arrow. `A ..> B : field type` is a declared type dependency, not composition, object ownership or a runtime call. External nodes are referenced types, not fabricated local implementations. Selected fields/method names aid navigation: `+` is public, `#` protected and `-` private. Diagram method names omit parameter/return types and collapse overloads; use the exact inspected declarations below before implementing an API.

Detailed graphs include non-nested classes in package-sized groups of at most 12. Nested/anonymous classes are inventoried and their declarations/relationships are retained below, but omitted from overview graphs. Relationships not drawn for readability remain in the complete declaration-relationship table. Constructors, synthetic bridges and overloads may be collapsed in diagram member lists only. Standard `java.lang.Object` inheritance is omitted from diagrams.

## UML class diagrams

### 1. `com.strategyquant.plugin.App.impl.QuantDataManager`

```mermaid
classDiagram
    class C04a7eec50fe8["QuantDataManagerAppPlugin"] {
        +Log
        -dataContext
        +timeOfLastDisplayedPopupBanner
        +getName()
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
    }
    class Ce50a76d88f7c["QuantDataManagerServlet"] {
        -Log
        #execute()
    }
    class C71ae2af47347["IAppPlugin"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    C71ae2af47347 <|.. C04a7eec50fe8 : declared interface
    C249b5c671b1a <|.. C04a7eec50fe8 : declared interface
    C8900f90ae594 <|-- Ce50a76d88f7c : declared extends
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C04a7eec50fe8` | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` (this JAR) | this diagram |
| `Ce50a76d88f7c` | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` (this JAR) | this diagram |
| `C71ae2af47347` | [`com.strategyquant.tradinglib.plugindef.app.IAppPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | class | non-nested |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` | class | nested/anonymous |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | [`com.strategyquant.tradinglib.plugindef.app.IAppPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / class declaration: `public class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin implements com.strategyquant.tradinglib.plugindef.app.IAppPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / class declaration: `public class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin implements com.strategyquant.tradinglib.plugindef.app.IAppPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / field declaration: `public static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `java.lang.Thread` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / field declaration: `private java.lang.Thread t;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / method signature: `public java.lang.String getName();`<br>`public java.lang.String getProduct();`<br>`public java.lang.String getContextPath();`<br>`public java.lang.String getAppCode();`<br>`public java.lang.String getTooltip();`<br>`public java.lang.String getProject();`<br>`public java.lang.String getDefaultTaskType();`<br>`public java.lang.String getDefaultTaskName();` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` / class declaration: `class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` (this JAR) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` / field declaration: `final com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin this$0;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` (this JAR) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` / method signature: `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1(com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin);` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` / class declaration: `public class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private synchronized java.lang.String onBannerClicked(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private synchronized java.lang.String onBannerClicked(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private synchronized java.lang.String onBannerClicked(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin</summary>

```text
public class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin implements com.strategyquant.tradinglib.plugindef.app.IAppPlugin,com.strategyquant.tradinglib.servlet.IServletPlugin
    public static final org.slf4j.Logger Log;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public static long timeOfLastDisplayedPopupBanner;
    private java.lang.Thread t;
    public com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin();
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
    private void startBannerPublisher();
    public org.eclipse.jetty.server.Handler getHandler();
```

</details>

<details>
<summary>com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1</summary>

```text
class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1 extends java.lang.Thread
    final com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin this$0;
    com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1(com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet</summary>

```text
public class com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    private static final org.slf4j.Logger Log;
    public com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private synchronized java.lang.String onBannerClicked(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
