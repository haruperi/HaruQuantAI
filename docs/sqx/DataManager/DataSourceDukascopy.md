# DataSourceDukascopy.jar

[Workspace/group index](README.md)  |  [All workspaces](../README.md)

## Scope and provenance

- Artifact: `SQX_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DataSourceDukascopy.jar`.
- SHA-256: `df1d953afd25874724953ac4793cc856698960f41a30e29db60ec02fc1502cf4`.
- Inspected: 2026-10-05; generation timestamp `2026-10-05T19:04:16.344170+00:00`.
- Archive class entries: **6**; non-nested: **4**; nested/anonymous: **2**.
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

### 1. `com.strategyquant.plugin.DataSource.impl.Dukascopy`

```mermaid
classDiagram
    class C0d87b1750ea6["DukasExport"] {
        -dateFrom
        -dateTo
        -targetFolder
        +getDateFrom()
        +setDateFrom()
        +getDateTo()
        +setDateTo()
    }
    class Cfa7f43d9ba41["DukasServlet"] {
        -formaterDate
        -Log
        -canceled
        #execute()
    }
    class Cd0eb906fffa0["DukasServletPlugin"] {
        -dukasServlet
        -dataContext
        +getProduct()
        +getPreferredPosition()
        +initPlugin()
        +getHandler()
        +call()
    }
    class C98149440b9fc["LastSymbolDates"] {
        -symbol
        -dateFrom
        -dateTo
    }
    class C1b6b4448b67b["IProgram"]
    class C249b5c671b1a["IServletPlugin"]
    class C8900f90ae594["HttpJSONServlet"]
    class C210d9b760f82["Serializable"]
    C8900f90ae594 <|-- Cfa7f43d9ba41 : declared extends
    C249b5c671b1a <|.. Cd0eb906fffa0 : declared interface
    C1b6b4448b67b <|.. Cd0eb906fffa0 : declared interface
    Cd0eb906fffa0 ..> Cfa7f43d9ba41 : field type
    C210d9b760f82 <|.. C98149440b9fc : declared interface
```

| Diagram identifier | Exact type | Location |
| --- | --- | --- |
| `C0d87b1750ea6` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport` (this JAR) | this diagram |
| `Cfa7f43d9ba41` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` (this JAR) | this diagram |
| `Cd0eb906fffa0` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` (this JAR) | this diagram |
| `C98149440b9fc` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` (this JAR) | this diagram |
| `C1b6b4448b67b` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | referenced external type |
| `C249b5c671b1a` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | referenced external type |
| `C8900f90ae594` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | referenced external type |
| `C210d9b760f82` | `java.io.Serializable` (not resolved in scoped archives) | referenced external type |

## Complete class inventory

| Fully qualified class | Kind | Entry |
| --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` | class | nested/anonymous |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` | class | nested/anonymous |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | class | non-nested |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` | class | non-nested |

## Declared relationships and evidence locations

Every row is supported by the named class declaration/member in `javap -p`, inside the artifact recorded above. Signature dependencies may include return, parameter, generic-argument and throws types; they do not imply execution.

| Declaring class | Referenced type | Relationship | Narrow inspection location |
| --- | --- | --- | --- |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport` / field declaration: `private java.lang.String targetFolder;`<br>`private java.lang.String symbol;`<br>`private java.lang.String filenamePrefix;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport` / method signature: `public java.lang.String getTargetFolder();`<br>`public void setTargetFolder(java.lang.String);`<br>`public java.lang.String getSymbol();`<br>`public void setSymbol(java.lang.String);`<br>`public java.lang.String getFilenamePrefix();`<br>`public void setFilenamePrefix(java.lang.String);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | [`com.strategyquant.webguilib.servlet.HttpJSONServlet`](../Shared/SQWebGUILib.md) | extends | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `org.joda.time.format.DateTimeFormatter` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / field declaration: `org.joda.time.format.DateTimeFormatter formaterDate;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / field declaration: `private static final org.slf4j.Logger Log;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `org.slf4j.Logger` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `static org.slf4j.Logger access$200();` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / field declaration: `private java.lang.String availableDataResponse;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onGetParallelDownload();`<br>`private java.lang.String onSetParallelDownload(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onGetDataList();`<br>`private java.lang.String onAddData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onAddCancel() throws java.lang.Exception;`<br>`private java.lang.String onUpdateAll();`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;`<br>`private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static java.lang.String access$002(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.lang.String);`<br>`static java.lang.String access$100(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onSetParallelDownload(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>);`<br>`private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`static void access$300(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;`<br>`private java.lang.String onSetParallelDownload(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;`<br>`private java.lang.String onAddCancel() throws java.lang.Exception;`<br>`private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | [`com.strategyquant.tradinglib.dukascopy.ImportInfo`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void sanitizeDates(com.strategyquant.tradinglib.dukascopy.ImportInfo, boolean, com.strategyquant.datalib.SymbolData);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | [`com.strategyquant.datalib.SymbolData`](../Shared/SQDataLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void sanitizeDates(com.strategyquant.tradinglib.dukascopy.ImportInfo, boolean, com.strategyquant.datalib.SymbolData);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | [`com.strategyquant.tradinglib.dukascopy.CdnInfo`](../Shared/SQTradingLib.md) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `org.apache.http.client.ClientProtocolException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `java.io.IOException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `java.lang.IllegalStateException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `org.jdom2.JDOMException` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` / method signature: `private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` / class declaration: `class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1 extends java.lang.Thread` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` / field declaration: `final com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1` / method signature: `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` | `java.lang.Thread` (not resolved in scoped archives) | extends | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` / class declaration: `class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2 extends java.lang.Thread` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` / field declaration: `final java.util.Map val$args;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` | `java.util.Map` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` / method signature: `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` / field declaration: `final com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet this$0;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2` / method signature: `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.util.Map);` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | [`com.strategyquant.tradinglib.servlet.IServletPlugin`](../Shared/SQTradingLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | [`com.strategyquant.pluginlib.program.IProgram`](../Shared/SQPluginLib.md) | implements | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` (this JAR) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / field declaration: `private com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet dukasServlet;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | `org.eclipse.jetty.servlet.ServletContextHandler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / field declaration: `private org.eclipse.jetty.servlet.ServletContextHandler dataContext;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / method signature: `public java.lang.String getProduct();`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | `java.lang.Exception` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / method signature: `public void initPlugin() throws java.lang.Exception;`<br>`public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | `org.eclipse.jetty.server.Handler` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / method signature: `public org.eclipse.jetty.server.Handler getHandler();` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` | `java.lang.Object` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin` / method signature: `public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` | `java.io.Serializable` (not resolved in scoped archives) | implements | `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` / class declaration: `public class com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates implements java.io.Serializable` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` / field declaration: `java.lang.String symbol;` |
| `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` | `java.lang.String` (not resolved in scoped archives) | type dependency | `com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates` / method signature: `public com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates(java.lang.String, long, long);` |

## Inspected declaration reference

These are structural API/member declarations, not proprietary implementation bodies. Private members and nested classes are retained to make diagram omissions explicit; declarations do not prove behavior.

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport
    private long dateFrom;
    private long dateTo;
    private java.lang.String targetFolder;
    private java.lang.String symbol;
    private java.lang.String filenamePrefix;
    public com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasExport();
    public long getDateFrom();
    public void setDateFrom(long);
    public long getDateTo();
    public void setDateTo(long);
    public java.lang.String getTargetFolder();
    public void setTargetFolder(java.lang.String);
    public java.lang.String getSymbol();
    public void setSymbol(java.lang.String);
    public java.lang.String getFilenamePrefix();
    public void setFilenamePrefix(java.lang.String);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet extends com.strategyquant.webguilib.servlet.HttpJSONServlet
    org.joda.time.format.DateTimeFormatter formaterDate;
    private static final org.slf4j.Logger Log;
    private boolean canceled;
    private java.lang.String availableDataResponse;
    public com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet();
    private void preloadAvailableDataResponse();
    protected java.lang.String execute(java.lang.String, java.util.Map<java.lang.String, java.lang.String[]>, java.lang.String) throws java.lang.Exception;
    private java.lang.String onGetParallelDownload();
    private java.lang.String onSetParallelDownload(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private java.lang.String onGetDataList();
    private java.lang.String onAddData(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    private void _onAdd(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onAddCancel() throws java.lang.Exception;
    private java.lang.String onUpdateAll();
    private java.lang.String onUpdateSelected(java.util.Map<java.lang.String, java.lang.String[]>);
    private java.lang.String onImportData(java.util.Map<java.lang.String, java.lang.String[]>);
    private void sanitizeDates(com.strategyquant.tradinglib.dukascopy.ImportInfo, boolean, com.strategyquant.datalib.SymbolData);
    private void fillCdnInfos(com.strategyquant.tradinglib.dukascopy.CdnInfo, java.lang.String) throws org.apache.http.client.ClientProtocolException, java.io.IOException, java.lang.IllegalStateException, org.jdom2.JDOMException;
    private java.lang.String onImportDataAction(java.util.Map<java.lang.String, java.lang.String[]>) throws java.lang.Exception;
    static java.lang.String access$002(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.lang.String);
    static java.lang.String access$100(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet);
    static org.slf4j.Logger access$200();
    static void access$300(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.util.Map);
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1</summary>

```text
class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1 extends java.lang.Thread
    final com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet this$0;
    com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$1(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2</summary>

```text
class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2 extends java.lang.Thread
    final java.util.Map val$args;
    final com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet this$0;
    com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet$2(com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet, java.util.Map);
    public void run();
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin implements com.strategyquant.tradinglib.servlet.IServletPlugin,com.strategyquant.pluginlib.program.IProgram
    private com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet dukasServlet;
    private org.eclipse.jetty.servlet.ServletContextHandler dataContext;
    public com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServletPlugin();
    public java.lang.String getProduct();
    public int getPreferredPosition();
    public void initPlugin() throws java.lang.Exception;
    public org.eclipse.jetty.server.Handler getHandler();
    public java.lang.Object call(java.lang.String, java.lang.Object...) throws java.lang.Exception;
```

</details>

<details>
<summary>com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates</summary>

```text
public class com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates implements java.io.Serializable
    java.lang.String symbol;
    long dateFrom;
    long dateTo;
    public com.strategyquant.plugin.DataSource.impl.Dukascopy.LastSymbolDates(java.lang.String, long, long);
```

</details>

## Validation and unresolved gaps

Archive hash and complete class inventory were checked against the inspected local artifact. Declaration extraction accounts for every inventoried class. Documentation/link/diagram structural verification is recorded in the master index and task walkthrough; no SQX runtime validation was performed.

The canonical reimplementation ledger/schema are absent, so no evidence IDs or validation-passed ledger claims are created. This is a donor structural reference. Exact behavior, default values, failure semantics, algorithms, runtime calls and target architectural choices require separate research. No aggregation/composition or cardinalities are inferred.
