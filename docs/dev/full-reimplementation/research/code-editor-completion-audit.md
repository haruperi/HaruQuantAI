# Code Editor completion audit

Date: 2026-10-30. Source HEAD: `bf6db55e92d70d8cabedd1871ed8c42b45a672f8`.
Working tree at audit start: clean. Owner approved the documentation-only
completion-specification plan, iteration 1, with `APPROVED: EXECUTE`.

Owning specification: [04-AppCodeEditor.md](../04-AppCodeEditor.md).
Donor root (`D` below): `data/reference-donor` relative to the repository root.
Plugin root (`P`): `D/internal/plugins`. Library root (`L`): `D/internal/libs`.
These are local source locators, not remote services to invoke.

## Consolidated command implementation update — 2026-10-30

The original tables below remain evidence of the pinned audit baseline, not a
current missing-feature checklist. Consolidated owner-approved iteration 2 now
implements all fourteen `WO-CE-COMMAND-GAPS` items; completed verification is
recorded in [Phase 4.7](../04-AppCodeEditor.md#phase-47-complete-editor-command-gaps--wo-ce-command-gaps).

| Prior missing boundary | Native target implementation |
| --- | --- |
| Save As/reload | `AppCodeEditor.save_as/reload_disk`, exclusive publication and explicit dirty authority |
| Catalogue/completion | `catalogue.py`, typed symbol/member and indicator descriptors, class-qualified identities |
| Code types/templates/subtypes | `templates.py`, typed `/code-types`, path filtering, order/MonteCarlo choices and indicator-derived signals |
| Export template authoring | `export_templates.py`; Python/pseudocode only, explicit extensions and path validation |
| Package compilation/jobs/cancellation | `compilation.py`, host JobManager thread pool, per-file results, progress and cooperative cancellation |
| Import repair | `import_repair.py`; unique candidates, explicit ambiguity selection and proposed-buffer delivery |
| Reconnect/restart diagnostics | Validated per-job/latest host-stored snapshots, interrupted orphan state, source hashes and stale-response guards |
| Reload all extensions | `registered` compilation scope; failed/missing workspace registrations are removed |
| Search/navigation/protection | Full search UI flags/scope, builtin/user filtering, versioned inventory, shared mutation authority and user clone mapping |
| Session recovery | Retained dirty missing-file buffers, visible warnings and fail-closed corrupt/duplicate state handling |

These are Python target contracts, not a claim of Java compiler, SQX archive,
trading-platform export or numerical parity. Cancellation cannot interrupt an
arbitrary import mid-execution; it waits and then stops the remaining work.
Batch tester suites, distribution/calibration and the other parent acceptance
orders remain outside this command-gap implementation.

## Evidence and limits

This audit inspects current Python/React sources, tests, donor JavaScript, and
already recovered Java. It does not execute donor code, download test data,
modify application databases, or establish numerical parity from source counts.
Recovered Java includes decompiler warnings; suspicious code must be checked
against the shipped JAR before a future work order relies on its exact behavior.

REA static analysis of `P/CodeEditorImportExport`, selecting
`ImportExportService.js` and `module.js`, produced parent evidence
`ev_ac93c3581ddbc2d02a2a7c20fed670d67ea45d69082ee563516864e30fc53331`.
Artifact SHA-256:
`f054795d885d4bb5e95eeb1d6a2e81b5e2a45a78ee4df13c17f71419b74da81a`.
Both selected JavaScript files parsed; seven inventoried files were outside that
analysis. Angular `BackendService` behavior and Java execution are not proven by
the static graph. Operation mappings below also use direct reads of the Java
servlets and current Python/React code; they are not inferred from REA call counts.

Source fingerprints (SHA-256 of file bytes):

| Path relative to D | SHA-256 |
| --- | --- |
| `internal/plugins/AppCodeEditor/module.js` | `f0aec6f431bdf6506fe06b9f9b503d05b2e5bfbe2f7cad97c2398c87fd3e39b9` |
| `internal/plugins/AppCodeEditor/CodeEditor/CodeEditorAppPlugin.java` | `788d38956460325d27b13f187fb393366462c48fa229f21ec877ae5514cf5c40` |
| `internal/plugins/ServletCodeEditor/CodeEditor/CodeEditorServlet.java` | `d58a26f1362c97e265741cb02b9bf1db61a6301a7ad3cf4d2159dd20d1b27fb8` |
| `internal/plugins/CodeEditorImportExport/ImportExport/ExtensionManager.java` | `db57458472d8368f03f6e14d7153e54328274bd64d0b2bdd811da1d74c69bc7b` |
| `internal/plugins/CodeEditorIndicatorTester/IndicatorTester/IndicatorTesterServlet.java` | `fba498c467eb93b7c5ef3cefec1b3435768d3b91eea64b23431086f646c03311` |
| `internal/libs/tradinglib/indicatorTester/IndicatorTesterConfig.java` | `8f94aac9d93edc60bd4992fbe280e3670d9a604ba4e631b04fe46800b12f7361` |
| `internal/libs/tradinglib/indicatorTester/IndicatorTester.java` | `79215ba800b982e8426936a8d99ec5036026d8543c056472efd57978d87d6c78` |

## Existing target coverage

`app/workspace/code_editor` contains 14 Python modules. Public entry points already
exist; creating differently named duplicate service engines would require an
explicit migration decision, compatibility mapping and owner approval.

| Responsibility | Existing implementation | Relevant tests and remaining limit |
| --- | --- | --- |
| Workspace/session | `editor.py:AppCodeEditor`; `routes.py:CodeEditor`; `http.py` | `test_editor.py`, `test_http.py`, `test_regressions.py`: tabs, dirty buffers, restart, session validation, forced close. Results still use broadly typed dictionaries. |
| File commands | `routes.py:CodeEditor`; `_common.py`; `_storage.py:atomic_write_batch` | `test_routes.py`, `test_regressions.py`: authorized paths, clone, rename/delete, dirty descendant remapping, rollback. Full donor command coverage is not established. |
| Compile/reload | `routes.py:compile_file/compile_all`; `registry.py`; `_common.py` | `test_unified_library.py`, `test_regressions.py`: current unsaved buffer, globals, inheritance, relative imports, full library compilation, tool registration. Synchronous Python compilation differs from donor asynchronous Java compilation. |
| Templates | `templates.py`, `_template_generators.py` | `test_templates.py`, template-parametrized regressions; 12 current generators. Java template/export variants are separate work. |
| Packages | `import_export.py:ImportExport` | `test_import_export.py`, package regressions: export/preview/import, rename collision avoidance, all-path preflight and reload. Current format is Python source ZIP with manifest; no Java `.sxp` compatibility claim. |
| Indicator execution | `indicator_tester.py`; `_indicator_data.py`; `_indicator_resolver.py` | `test_indicator_tester.py`, `test_regressions.py`, `test_unified_library.py`: historical data, non-finite gaps, multiple outputs, parameter defaults, ambiguity/path safety and saved config identity. Not donor batch reference-file parity. |
| Persistence | `_storage.py:StateStore` via `HostPersistence` | Isolated tests use a temporary database and Parquet history in `conftest.py`. Schema/lifecycle authority still needs reconciliation with host capability ownership before new persistence contracts. |
| HTTP and tools | `http.py`, `mcp.py`, registration from `app/main.py` | `test_http.py`: init/templates/history/errors/session/config restart and compiled MCP tool calls. No claim of strict public DTO completeness. |
| Live workspace UI | `app/web/workspaces/code_editor/CodeEditorWorkspace.tsx`, hooks, modals and CodeMirror `SourceCodeEditor.tsx` | Route `/codeeditor` in `app/web/shell/App.tsx`; `tests/e2e/code-editor-regressions.spec.ts` has intercepted browser regressions. These tests were read, not executed in this documentation stage. |
| Presentation | `indicator_test_presentation.ts` | Phase 4.1 committed in `31fc0d35`; 42 tests previously passed. Helper is not wired into a donor-style batch grid. |

Frontend `codeEditorClient.test.ts` tests request mapping with mocked fetch.
`codeEditor.test.ts` exercises the fixture-backed shell extension store; it must
not be cited as proof of live service integration. The existing Playwright tests
exercise rendered screens with intercepted requests, not a live Python service.

## AppCodeEditor registration boundary

`P/AppCodeEditor/module.js` registers the SQEDITOR navigation contribution.
`CodeEditor/CodeEditorAppPlugin.java` registers a program named `CodeEditor`,
context `/editor`, app code `SQEDITOR`, and an `open` call launching the donor
executable on a background thread. It supplies no generic workspace CRUD API.
The Python target already uses `/codeeditor` navigation and an embedded React
workspace. Do not create `CodeEditorService.execute(dict)` or launch the donor
executable as a substitute for target workspace behavior. Whether a separate
desktop-launch capability is needed remains a host integration contract.

## Complete servlet operation map

Direct inspection of each `execute` switch establishes **26 editor + 9 tester +
8 package = 43 commands**. The former client-literal-only inventory omitted
editor `list`, editor `getInfo`, and tester `calibrate`.
The table fields describe donor wire inputs/outputs, not approved new Python DTOs.
Success text and downstream JSON structures are not stable target error schemas.

### Editor: P/ServletCodeEditor

Read `services/CodeEditorService.js`, `CodeEditor/CodeEditorServlet.java`,
`CodeEditor/CodeEditorInfoSender.java`, `CodeEditor/CodeAutoCompleteManager.java`,
`CodeEditor/templates`, `CodeEditor/searchInFiles`, and their directive consumers
when specifying one of these operations. Command prefix is `codeeditor/`.

| Command | Observed input and result/effect | Current target match and missing boundary |
| --- | --- | --- |
| `editorAutocomplete` | No arguments; `CodeAutoCompleteManager.getData()` | CodeMirror Python language completion is present; donor symbol/member catalogue is not mapped. |
| `listCodeTypes` | No arguments; `items` of template-backed code types | Current template catalogue is a partial match; code-export types need specification. |
| `list` | `filter`, optional `dirs` default `Builtin,User`; tree `id,item` | `navigator(root_dir)` returns target tree. Builtin/user protection and filter equivalence need explicit mapping. |
| `getContent` | Existing `file`; `name,text,protected` | `open_file_tab(file_path, mode)` returns tab content. Target path protection metadata needs a typed contract. |
| `save` | Existing `file`, `data`; writes file | `save_file(file_path, content)` is present, including diagnostics. Preserve empty content. |
| `saveAs` | Destination `file`, `data`; writes destination | No dedicated Save As UI/service operation; collision, protection and tab identity require specification. |
| `compile` | Existing unprotected `file`, `data`; saves then starts asynchronous compiler, returns `Started.` | Current compile accepts unsaved Python source, imports/registers synchronously without saving that buffer. Preserve this explicit target behavior until a lifecycle adaptation is approved. |
| `compileAll` | No arguments; regenerates indicators, asynchronously compiles, invalidates autocomplete cache after success | Current synchronous `compile_all` exists. Progress, cancellation and registry publication are not specified. |
| `compilePlugin` | `file` must be directory; asynchronous plugin compile, result marks `plugin=true` | No equivalent Python package compile contract; do not invoke the Java compiler. |
| `stopCompilation` | No arguments; inspected method returns `Stopped.` without stopping a compiler | No target operation. Define real cancellation or explicit unsupported outcome; do not fake successful cancellation. |
| `listTemplates` | `file`; matching template `file,name,description` list | `list_templates` and preview exist; path-dependent Java export-template variants are not mapped. |
| `listIndicators` | No arguments; builtin/user indicator directory names | Canonical Python resolver/registry exists; dedicated typed UI catalogue endpoint is missing. |
| `createNew` | `name,type`; optional `indicator,orderActionType,mcType`; selects template and creates snippet, returns `file` | `create_new(template_type,name,category)` and 12 Python generators exist; subtype/indicator-derived signal compatibility needs mapping. |
| `createNewFile` | `name,file,template,ext,createCodeFile`; creates source or code-template file, returns `file` | `new_file(file_path,content)` exists; arbitrary Java/code export formats are not implemented. |
| `createNewTemplate` | `file` can contain comma-separated paths; creates code export templates | No current equivalent; requires export-template owner and supported format specification. |
| `createNewDir` | `name,file`; directory-relative creation, returns `file` | `new_dir(dir_path)` exists; retain target authorized-root policy. |
| `rename` | `name,file`; reject protected source, preserve extension, returns destination `file` | `rename_file(old_path,new_path)` exists with dirty descendant handling. Preserve target full-path input and test collisions/protection. |
| `delete` | `file`; recursive delete of unprotected target, returns deleted `files` | `delete_file(file_path)` exists. Only temporary snippet trees may be deleted by acceptance tests. |
| `reload` | Existing `file`; returns its path and refresh success | Reopening a target tab preserves its dirty buffer; this is not explicit disk reload. Define dirty-reload confirmation before adding it. |
| `clone` | `name,file`; no directories, rejects existing destination; builtin clone goes to user tree and rewrites class references | `clone(source_path,target_path)` rewrites Python class/self references. Builtin/user ownership mapping remains a contract item. |
| `findInFiles` | `text,caseSensitive,regex,wholeWord`; tree `id,item`, `text,matches` | `find_in_files(query,case_sensitive,regex,whole_word,search_dir)` exists and returns flat matches. UI currently exposes a smaller input surface. |
| `getInfo` | No arguments; republishes last failed compilation result | Current in-memory log history exists; reconnect/restart diagnostics delivery contract is missing. |
| `fixImports` | Existing unprotected `file`, `data`; writes source, adds discovered Java imports, optional returned `text` | Current compiler reports unresolved globals; no Python import-repair operation. Ambiguous symbols must not be silently imported. |
| `saveLastOpenedFiles` | Comma-separated `files`; trims, removes empty/duplicate paths and writes UTF-8 settings file | `sync_session(tabs,active_file)` persists richer target state through host storage. Retain rather than adding ad-hoc settings writes. |
| `loadLastOpenedFiles` | No arguments; `files` array read from settings | `init_workspace` restores tabs/buffers. Missing-file and corrupted-state handling need focused contract validation. |
| `reloadApp` | No arguments; reloads registered custom classes, not process restart | Per-file compile/register exists; no typed all-extension reload operation. Do not interpret this as restarting the host. |

Compiler result delivery uses `codeEditor` data with `compilationResult`; plugin
results also identify the plugin and file. Current HTTP responses are synchronous
`{status: 'success', data: ...}`. A future event adapter must define job identity,
ordering, terminal failures, reconnect behavior, timeout and lifecycle ownership
before changing this public contract. `StandardResponse` and `DomainError` exist
in `app/core/lib`, but wrappers alone do not supply missing typed domain results.

### Indicator tester: P/CodeEditorIndicatorTester

Read `IndicatorTester/IndicatorTesterServlet.java`, `IndicatorTestExecutor.java`,
`DownloadProgressPublisher.java`, `IndicatorTestsDownloader.java`, controller and
service JS, plus `L/tradinglib/indicatorTester/{IndicatorTesterConfig,IndicatorInfo,
IndicatorParameters,IndicatorTester,IndicatorsLoader}.java`.
Command prefix is `indyTester/`.

| Command | Observed input and result/effect | Current target match and missing boundary |
| --- | --- | --- |
| `listIndicators` | No arguments; per-output-buffer `indicators` records with name/value/className/shift/parameters | Canonical class/default resolution exists; batch descriptor/output-buffer catalogue is missing. |
| `createNewConfig` | `engine,barsToReserve`; resets config path, returns `xmlConfig` | `new_indy_test` is one indicator/history setup, not a suite. Typed suite schema and engine support required. |
| `addTests` | Comma-separated `indicators`, `xmlConfig`; updates suite, appends tests, returns `xmlConfig` | No batch equivalent. Define indicator/output identity and duplicate policy. |
| `loadConfig` | Optional `filePath`; load selected/remembered/default XML, returns `xmlConfig` | `load_test_config(config_id)` restores host-stored JSON by ID. XML interchange and remembered path are separate contracts. |
| `saveConfig` | `xmlConfig`, optional `filePath`; save/update remembered config | `save_test_config(test_id,name)` persists target JSON; frontend already calls it. No silent no-path save or new ad-hoc SQL is permitted. |
| `startTesting` | `xmlConfig`; update suite then start executor; reject already-running tests | Current `indicator_tester` is synchronous per-indicator execution. Batch job/state/error contracts missing. |
| `stopTesting` | No arguments; requests executor stop | No backend cancellation. Frontend response invalidation is not computation cancellation. |
| `downloadTests` | No arguments; reject while tester runs; start remote download, extract and update config | No current typed download capability. Source URL is historical plain HTTP; availability, trust, bounded transfer, archive validation, retry and host publication policy are unresolved. No URL was contacted. |
| `calibrate` | `projectName`, optional `taskName`, comma-separated `symbols,timeframes`, `engine`, optional/invalid `maxSteps` becomes -1; returns `calibrationResults`, logs project progress | No mapped target operation. Requires engine/project/calibration model and independent fixtures; donor rejects two AlgoCloud engines. Do not hardcode opaque engine integers as Python public policy. |

The donor XML sample exists at
`D/internal/user/settings/IndicatorTesterConfigs/IndicatorTester.xml`: empty
`Tests`, engine `MetaTrader4`, reserve `300`. Shared config creation takes caller
engine/reserve; failed/missing load falls back to those donor defaults. The target
single-history test currently defaults to reserve 50 and display count 150. These
are different workflows; do not silently change one to imitate the other.

`IndicatorInfo.getXML` emits `Test` attributes `use=true`, `indicator`, `parameters`,
`decimals=6`, empty `result`, metadata-derived `shift`, `fileName` and `exists`.
The JS presentation reader has a missing-shift fallback of 1; it is not a universal
indicator default. `IndicatorTestPresentation` requires caller-supplied shift.

The executor selects enabled tests; initializes an engine and reserve; sets
per-row filename existence; converts parameters; compares a selected output
buffer with decimals and shift; records `Passed`, `Failed - ...`, or `Skipped -
...`; attaches `Errors/Error` and `showGrid`; and saves config after rows.
`IndicatorTesterStatus` includes `percent,status,xmlConfig`.
`TestsDownloadStatus` includes progress/info/error and, on completion, config/path
fields; some donor payload slots mix booleans and strings. Typed target events
must replace that ambiguity deliberately. Empty-suite percentage, stop timing,
per-row terminal state and error codes need explicit acceptance cases.

`L/tradinglib/indicatorTester/IndicatorTester.java:checkPrecision` uses strict
`abs(actual-reference) < 10**(-decimals)`, applies output shift, and limits reported
differences. Current Python uses a fixed `difference > 0.0001` discrepancy rule,
accepts short reference lists, and reports computation `status='success'` even
when discrepancies exist. Neither this status nor merely calculating a chart
proves a donor reference test passed. A comparator order must specify aligned
timestamps, warmup, output selection, non-finite behavior, reference length,
precision boundary and independent expected values before changing calculation.

### Import/export: P/CodeEditorImportExport

Read `ImportExportService.js`, `ImportExport/ImportExportServlet.java`,
`ImportExport/ExtensionManager.java`, `ExtensionsFileMap.java` and overwrite UI
consumers. Command prefix is `/importexport/`.

| Command | Observed input and result/effect | Current target match and missing boundary |
| --- | --- | --- |
| `import` | Comma-separated archive `files`; installs ZIP entries; `newFiles` and `notImportedFiles[{name,reason}]` | `overwrite_confirm(archive_path,resolution_rules)` imports Python sources in one preflighted batch, returns extracted/skipped/reload results. No interactive session or Java interchange. |
| `export` | Comma-separated `files`, `targetPath`; reject blank list; ZIP entries relative to user data | `export(file_paths,archive_path,metadata)` packages existing `.py` files and manifest; accepts `.zip`/`.sxp` destinations. Same extension does not establish same contents. |
| `overwrite` | No arguments; resolves current conflict once | Batch rule `overwrite` only; no pending conflict/session identifier. |
| `overwriteAlways` | No arguments; resolves all later conflicts by overwrite | UI global overwrite currently supplies a rule for every preview item; not donor session state. |
| `skip` | No arguments; skip current conflict once | Batch rule `skip` only. |
| `skipAlways` | No arguments; skip later conflicts | UI merge maps every preview item to skip; not donor session state. |
| `cancel` | No arguments; cancel pending import | Closing modal does not cancel backend work. Define session cancellation and already-written-file effects before adding it. |
| `list` | `filter`; user extension tree `id,item` | Target navigator and archive preview exist; no identical user-only extension tree contract. |

Donor `ExtensionManager` protects builtin paths, publishes
`overwriteConfirmation {filePath}`, waits for a decision and cancels after about
60 seconds. It writes entries incrementally; current target preflights all paths
then uses exception-atomic publication (not power-loss-atomic across files).
Future target design must preserve authorized-root checks, reject traversal and
duplicates, define size/count/decompression bounds, and state exactly what can
remain written after cancellation or reload failure. Do not copy donor global
session state or weak archive boundaries as target architecture.

## Bounded implementation queue

The owner document specifies exact frontend paths, symbols, request invariants
and acceptance cases for three immediately reviewable fixes:

1. `WO-CE-CLIENT-DEFAULTS`: omitted/null parameters must reach backend as null;
   preserve explicit objects instead of injecting `{period: 14}`.
2. `WO-CE-TESTER-REQUEST-LIFECYCLE`: invalidate old runs before the next debounce,
   guard defaults rejection, and ignore responses after unmount. This does not
   add a backend cancellation capability.
3. `WO-CE-PACK-UI-CONTRACT`: remove inert controls, require explicit open source
   paths, state disk-based export and archive-controlled destinations, and
   invalidate preview when its archive path changes.

These are SPECIFIED target adaptations awaiting implementation-plan approval.
They do not release the parent full-workspace orders. After these slices, specify
typed existing DTOs/errors and host ownership before asynchronous commands,
suite persistence, import sessions, distribution and calibration. Each future
work order must list exact write paths, symbols, input validation order, result
and error types, effects/events, independent acceptance fixtures and dependencies.

## Extension inventory and reconciliation cohorts

Root: `D/internal/extend/Snippets/SQ`. Counts include support and package files;
they are not counts of independently executable indicators. No `app/extend`
directory exists at the audited HEAD. Current `app/include` and trading owners
must be audited first; catalogue paths in the owner document are reserved
descriptor locations, not permission to duplicate their runtime implementations.

| Category | Java files | Reconciliation cohort and prerequisites |
| --- | ---: | --- |
| Blocks | 670 | Split into the ten subgroups below, then indicator families; reconcile existing `app/include/blocks` first. |
| Calculators | 7 | AbstractCalculator, AverageCalculator, HighestCalculator, LowestCalculator, RSICalculator, StdDevCalculator, SumCalculator. Existing `app/include/calculators` has 9 Python files; audit warmup, tick replacement and state transitions before porting. |
| Functions | 4 | ComparatorByProfit, DailyEquityComputer, OrderFunctions, StatFunctions. Distinct trade/equity/statistics semantics; `Blocks/Functions` is a separate category. |
| Internal | 36 | Block/indicator foundations, rule composition, strategy/events, XML strategy and chart support; includes `package-info.java`. Requires ratified runtime/context/engine capabilities. |
| Trading | 6 | Five commission implementations under `Commissions`, plus `Scaling/NoScaling`. Reconcile `app/workspace/trading` and shared order contracts. |
| TradingOptions | 8 | DontTradeOnWeekends, ExitAtEndOfDay, ExitOnFriday, LimitTimeRange, MaxDistanceFromMarket, MaxTradesPerDay, MinMaxSLPT, UseInitialSLPT; specify clocks, boundary conditions and engine gates. |
| ExitMethods | 5 | ExitAfterBars, MoveSL2BE, ProfitTarget, StopLoss, TrailingStop; specify order/event timing, tick rounding and retained state. |
| MoneyManagement | 12 | ATRRiskBasedSizing, CryptoFixedAmount, CryptoFixedBalancePct, CryptoSizeByPrice, FixedAmount, FixedSize, PickerFixedAmount, PickerRiskFixedPctOfAccount, RiskFixedBalancePct, RiskFixedPctOfAccount, SimpleMartingaleMM, StocksSizeByPrice; specify equity/risk/lot units and rounding. |
| RiskManagement | 1 | AllowAllTrades; reconcile risk capability and call context before defining a target descriptor. |
| TALibIndicators | 1 | PercentRank/PercentRank.java; source presence does not authorize adding a TA-Lib dependency. |
| Utils | 1 | TimeDiffUtil; specify calendar/timezone/DST and return units. |
| **Total** | **751** | Every source identity must eventually map to retained behavior, an approved implementation, support-only classification, or an explicit approved exclusion. |

Blocks breakdown:

| Subgroup | Java files | Existing owner to inspect (not a parity assertion) |
| --- | ---: | --- |
| BarAndTime | 37 | `app/include/blocks/bar_time` |
| CandlePatterns | 7 | `app/include/blocks/indicators` and composition metadata |
| Comparisons | 27 | `app/include/blocks/comparisons` |
| Functions | 18 | `app/include/blocks/functions` |
| Indicators | 501 | `app/include/blocks/indicators` (91 Python files including support/init); split by donor family and output rather than create 501 copies |
| Order | 12 | `app/include/blocks/order`, shared contracts and trading workspace |
| Other | 5 | Existing types, variables and foundational blocks |
| OtherActions | 8 | Existing action modules and host effect capabilities |
| Price | 30 | `app/include/blocks/price` |
| StrategyControl | 25 | `app/include/blocks/strategy_control` |
| **Total** | **670** | Supports inventory accounting only |

Each cohort needs a per-definition ledger with donor path/hash, descriptor ID,
existing target symbol, parameter types/defaults/ranges, outputs/units, warmup,
shift/state, engine gates, exception/log behavior, and independent fixture IDs.
Inheritance and composition must be traced; matching names or counts are not
equivalence. Register metadata separately from formulas. Keep formulas in their
canonical owner; any move requires its own explicit approved path/compatibility
plan. Strategy execution and irreversible trading remain separately authorized.

Category inventory fingerprints below identify the complete source-path set and
file bytes without adding a third artifact. For each category, sort relative-to-D
POSIX paths lexicographically; concatenate UTF-8 lines
`<path>\t<SHA256(file bytes)>\n`; hash that UTF-8 stream with SHA-256.

| Category | Inventory SHA-256 |
| --- | --- |
| Blocks | `4c47c8c78683c927c76dd9a0b21ae756c7b468e2c33f6dcf32914d30bc6a62e9` |
| Calculators | `f573af819ac1a8782ed91ac4b5b25afe80c2c30f6a168f00ed3a457279863527` |
| Functions | `ffa385bdd72470060ee9739df85192ec30d69d38dd610e4805153eac302237f3` |
| Internal | `997a0063568b8fc99d628fe36d6f4a975804d19545d44a0c237b23d24dc6d10e` |
| Trading | `864eda5ba4ec1d22a9fd7ad28077987fdd86aa2a2b9723ede9b2e5186341ba0d` |
| TradingOptions | `5d90404800a3161ab52bc39027db3ee1161be8804509649d1630cc498614fd21` |
| ExitMethods | `43eec08b1c9b4b7a61de01c4f77070996249be1c29a4eab8ae95effb355ccda1` |
| MoneyManagement | `ed50ec8fe74b90ce6a88bf14a976fae2f4e4c0004f96ea8d26912f6718c55dab` |
| RiskManagement | `13039cb2e482a6936ee7f25ab0db69e62db11d7176d26f773834d7950e26e532` |
| TALibIndicators | `b2e73bec442080ca2c2330bb387993696f738cf7d33eb0e6ce9e4467e0544ec0` |
| Utils | `0e0d3aa3f995708f625ea98567fbce3dfa754a61f10ab8f0cfe01507223f4a8d` |

## Verification and completion gates

Baseline command executed during the audit:

```text
uv run python -m pytest tests/workspace/code_editor -q --no-cov
77 passed in 11.39s
```

Tests use the isolated store/history fixture; this is neither a coverage run nor
proof of the required 80% branch-aware coverage across retained Python source.
Phase 4.1's previously recorded 42 focused tests, 707 frontend tests, typecheck
and build results remain historical evidence at its implementation baseline.
Runtime/browser suites are not rerun for this documentation-only stage.

Before full completion can be recorded:

- Every operation above has an approved target mapping and success/failure tests;
  all three new commands are accounted for. No placeholder parent acceptance
  command may count as success merely because pytest/Vitest exits zero.
- Every extension source is reconciled in a per-definition cohort ledger;
  independent numerical/state fixtures and engine gates pass for retained logic.
- Existing service results/errors become explicit typed contracts without
  breaking clients; module documentation, visible requirement logging and strict
  typing meet the contributor constitution for changed Python modules.
- Host owns persisted schemas, jobs, event lifecycles and any remote transport.
  Compatibility/failure/cancellation and secret redaction are tested explicitly.
- Actual rendered workspace and Python API integration pass together using
  temporary snippet/database/history stores, alongside scoped unit tests,
  frontend typecheck/test/build and the required final coverage evidence.
- Owner document records exact commands, collected cases, residual warnings and
  approved exclusions. No broad READY labels or inventory counts replace this.

## Decisions and authority still needed later

No immediate product decision blocks the three SPECIFIED frontend orders.
Other orders first require engineering specifications, not generic owner input.
If evidence cannot resolve an engine compatibility policy, public DTO migration,
canonical ownership move or trusted test-data distribution, present a concrete
choice with effects in that order's implementation plan. Existing approval does
not authorize new host capabilities, dependencies, schema changes, live trading,
donor execution, or commits. This document is a completion specification stage;
the full implementation remains in progress.
