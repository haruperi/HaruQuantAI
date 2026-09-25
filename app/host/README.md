# Host boot-sequence reference

This document records the discovered StrategyQuant X (SQX) build **144.2953**
startup sequence and proposes HaruQuantAI ownership for a new implementation.
**Donor informs; specification owns.** No backend implementation, complete
internal call graph, or SQX parity is established by these tables.

The backend host implementation was removed at repository commit
`a6245a4430b0a341f2c4e838fb7f9647d564c59c`. The remaining `app/main.py` still
imports the removed bootstrapper. Older host-baseline descriptions elsewhere
must not be read as evidence that the reset backend works.

## Reading the tables

- **B01 onward:** before the 13 reported initialization stages.
- **I01-I13:** the exact initialization messages, in observed order.
- **A01 onward:** application serving, browser startup and deferred work.
- **Observed:** supported by inspected files, logs or bytecode. Static branches
  are not necessarily branches exercised in the recorded runs.
- **Partial:** the stage is observed, but the stated internals remain unknown.
- **Proposed:** a HaruQuantAI decision, not an SQX fact.

B/I/A identifiers are documentation labels, not SQX identifiers or registered
feature/requirement IDs. The B and A rows describe dependencies and milestones;
they do not impose a total ordering on asynchronous operations.

**Every target path in the tables is a proposal**, relative to
`HARUQUANTAI_ROOT`. A filename does not assert that a file exists or authorize
implementation. Desktop packaging, licensing, storage contracts and concrete
workspace/plugin ownership require their own approved specifications.
`<Concept>` and similar placeholders identify separately owned contributions.

The host assembles universal services and coordinates declared capabilities.
It must not contain a hard-coded list of quantitative concepts or their
algorithms. One startup stage is not necessarily one file. Quantitative
plugins keep behavior and schemas in their own cohesive files; the UI owns
presentation and local view state. See [architecture](../../docs/ARCHITECTURE.md),
[product scope](../../docs/PROJECT.md) and [workflow](../../AGENTS.md).

## B — Before initialization

| Step | Stage | SQX behavior and execution point | Proposed HaruQuantAI file / owner | Evidence |
| --- | --- | --- | --- | --- |
| B01 | Native process launch | Windows starts `StrategyQuantX.exe`. The inspected executable contains Go runtime and `sqlauncher` symbols; its full native instruction sequence is unresolved. | `app/main.py` plus an approved launcher/package | Observed / partial; S1 |
| B02 | Runtime configuration | `StrategyQuantX.config` supplies system-proxy, IPv4, Parallel GC, TLS name-service, native-access and `-Xms4g` options. These are installed values, not verified factory defaults; `-Xms` is initial heap. | `app/host/config.py`; Python/runtime-specific policy must be independently specified | Observed; S1, S2 |
| B03 | Embedded runtime loading | The running launcher process loads `j64/bin/server/jvm.dll`. The bundled runtime identifies Java 25.0.1. This is an in-process JVM, not a required separate `java.exe`. | Launcher/runtime packaging; `app/host/bootstrap.py` assembles target services | Observed; S1, S10 |
| B04 | Application bootstrap | A recorded startup stack contains `SQStarter.main → SQApp.main → MainApp.start → MainAppStandardImpl.startApp`. Complete core class bodies and dependency assembly were not inspected. | `app/main.py` → `app/host/bootstrap.py` | Observed stack / partial internals; S2 |
| B05 | Early desktop-control server | `MainAppWebServer` starts before Electron. The inspected configuration and session use port 5051; `/websocket/app` carries desktop control. Complete control-port collision behavior remains unresolved. | Proposed `app/host/control_server.py` | Observed / partial; S1-S3, S10 |
| B06 | Desktop shell launch | Java launches `StrategyQuantX_ui.exe` through Windows `cmd /c start`, passing product code, name, icon, control port and browser token. | Proposed `app/host/desktop.py` | Observed; S2, S4 (`Electron.start`) |
| B07 | Shell arguments, profile and window | Electron validates launch arguments, selects product-specific `userData`, reads `main-window-state.json`, applies display-aware geometry and creates the window. Renderer requests receive the supplied `browserToken` header. Complete server-side token validation is unresolved. | Proposed `app/desktop/main.js`, `app/desktop/window_state.js`; host session contract in `app/host/sessions.py` | Observed / partial; S3, S5 |
| B08 | Desktop handshake | Electron connects to `ws://127.0.0.1:<control-port>/websocket/app`. Java checks readiness up to 15 times with one-second sleeps; failure reaches an exit path. This establishes desktop readiness, not research-service readiness. | Proposed `app/desktop/control.js`, `app/host/desktop.py`, `app/host/startup.py` | Observed code and successful log path; S2-S5 |
| B09 | Startup diagnostics | After Electron readiness, the inspected backend log reports build, runtime arguments, CPU/memory and hardware identity information. Hardware-ID derivation is unknown. `-XX:+DisableAttachMechanism` appears in runtime arguments, but its injection point is unknown and does not prove a general anti-tampering subsystem. | `app/host/hardware.py`, `app/host/telemetry.py`; no hardware-binding implementation specified | Observed / partial; S2 |
| B10 | License-related screen | Both UI logs record loading `internal/web/app/licenseDialog.html`. They do not establish user interaction, exact database queries, cryptographic verification, hardware binding or offline/rejection behavior. | Proposed licensing owner and `app/ui/src/app/LicenseScreen.tsx`, only if target licensing is approved | Observed screen / partial internals; S3 |
| B11 | Initialization-screen transition | The license-related page is followed by `internal/web/app/layout/views/loadingScreen.html`; subsequent `loadingInfo` commands update progress. | `app/host/startup.py`; proposed `app/ui/src/app/BootScreen.tsx`; desktop command adapter | Observed; S3, S5 |

## I — Observed initialization stages

The stage names below preserve the emitted messages, including their trailing
ellipsis. Both inspected UI startup logs report this order. A progress message
does not prove every internal operation or the exact completion boundary.
`app/host/startup.py` is a proposed generic coordinator, not the implementation
home for all 13 stages or a fixed list of quantitative domain names.

| Step | Exact SQX stage name | Discovered behavior and unresolved details | Proposed HaruQuantAI file / owner | Evidence |
| --- | --- | --- | --- | --- |
| I01 | Initializing database & settings... | Stage observed. Settings artifacts exist; exact database opening, schema checking and migration order remain unresolved. | `app/host/settings.py`, proposed `app/host/storage.py`, and semantic owner adapters | Partial; S3 |
| I02 | Loading customizations... | Stage observed; the backend log reports successful customization loading. Complete discovery/application rules are unresolved. This is not automatically plugin discovery. | Proposed `app/host/customizations.py` and UI counterpart | Observed / partial; S2, S3 |
| I03 | Compiling snippets... | The backend log checks snippet changes and skips compilation when unchanged. A Python preparation/compiler equivalent and cache format are not established by this observation. | Proposed extension-preparation owner, potentially `app/workspace/CodeEditor/compiler.py`; concrete extensions remain local | Observed / partial; S2, S3 |
| I04 | Loading performance settings... | One run detects 12 logical CPUs and prepares 11 executors under core configuration `-1`. This does not establish a universal worker count or sizing rule. | `app/host/resources.py` | Observed; S2, S3 |
| I05 | Initializing building blocks... | Stage observed; the complete initialization algorithm is unresolved. | `app/plugins/<BuildingBlock>/plugin.py`; generic discovery in proposed `app/host/catalog.py` | Partial; S3 |
| I06 | Loading plugins... | `SQPluginManager` loads from `internal/plugins` and `user/extend/Plugins`, filters product applicability and calls `initPlugin()`. Target discovery/activation must use declared capabilities. | Proposed `app/host/catalog.py` and each `app/plugins/<Concept>/plugin.py` | Observed; S3, S6 |
| I07 | Initializing stats computer... | Stage observed; it does not establish formulas, the complete statistic inventory or initialization order within the stage. | Each `app/plugins/<Statistic>/plugin.py` | Partial; S3 |
| I08 | Initializing engines... | Stage observed; the full engine inventory and internal startup dependency order are unresolved. | Each `app/plugins/<Engine>/plugin.py` | Partial; S3 |
| I09 | Loading data... | Data loading is logged. One recorded startup also launches a background `SPY_benchmark.D` download; its overlap with other stages is not a serial dependency guarantee. Full loading scope remains unresolved. | Proposed `app/workspace/DataManager/startup.py` and declared data-provider plugins | Observed / partial; S2, S3 |
| I10 | Loading projects... | Project directories are enumerated, default projects checked via application plugins, and tasks initialized from configuration. Saved strategy restoration occurs later, after UI acknowledgment. | Proposed `app/workspace/CustomProjects/startup.py` and other owning workspace startup files | Observed; S2, S3, S7 |
| I11 | Initializing communication channels... | Stage observed; update-channel machinery is present. A global event-buffering gate or release-gate algorithm has not been established. | `app/host/events.py` plus owner-declared channels | Partial; S3, S8 |
| I12 | Checking data... | Stage observed. Exact checks, session-alignment rules, bar-integrity algorithms and failure policies remain unresolved. | Proposed `app/workspace/DataManager/validation.py` and owning validation plugins | Partial; S3 |
| I13 | Loading GUI... | Stage precedes application serving/navigation. SQX has generated web bundles and a resource-merging mechanism; rebuilding all bundles on every startup was not established. | Proposed `app/host/http_server.py` and frontend build tooling | Observed / partial; S2-S4, S9 |

## A — After initialization

These rows expand the work announced by I13 and the subsequent readiness
transition; they are not a second GUI-start operation. Browser requests and
deferred jobs can overlap. Conditional branches need not occur in every run.

| Step | Stage | SQX behavior and execution point | Proposed HaruQuantAI file / owner | Evidence |
| --- | --- | --- | --- | --- |
| A01 | Assemble application handlers | SQX assembles main commands, language and directory support, static/plugin resources and product-specific handlers. One recorded startup registers `/mcp`. | `app/host/http_server.py`; workspace/plugin-owned handlers; optional `app/plugins/MCP/plugin.py` | Observed; S2, S4 |
| A02 | Bind application server | A positive configured `WebServerPort` is attempted directly; otherwise SQX tries 8080-8090 inclusive. Automatic range exhaustion throws. The September 24 run falls back from 8080 to 8081; September 25 uses 8080. Selected port is saved as `WebServerPortUsed`. | `app/host/http_server.py`, `app/host/settings.py` | Observed code and fallback; S2-S4 |
| A03 | Navigate desktop window | Java sends title and URL directives; Electron navigates to the application endpoint. This server is distinct from the early control server. | Proposed `app/host/desktop.py`, `app/desktop/control.js` | Observed; S3-S5 |
| A04 | Initialize browser application | `SQUANT/index.html` loads shared JS batches and layout code and starts AngularJS. HaruQuantAI's retained frontend stack is a separate target choice. | Frontend entry/build files and `app/ui/src/app/App.tsx` | Observed; S9 |
| A05 | Connect live updates | The browser calls `/main/getWebSocketPort`, opens `/websocket/updates`, sends setup and establishes subscriptions. This is separate from Electron's desktop-control socket. | `app/ui/src/app/transport.ts`, `app/host/events.py` | Observed; S8 |
| A06 | Load browser initialization data | Route initialization loads plugin initialization data, constants, settings, language lists, app information, data metadata, columns, views and project configurations. Language resources and skins are then loaded on the shared-data branch. Promise-based operations may run concurrently. | `app/ui/src/app/HostConnection.tsx`, localization/theme files and semantic owner clients/handlers | Observed; S4 (`MainServlet.onLoadInitializationData`), S8, S9 |
| A07 | Assemble navigation and preload workspaces | Navigation comes from plugin registrations, present in generated `Batch1/libs.js`. Declared preloads are Builder, Retester, Optimizer, Portfolio Master, Data Manager, Results and AlgoWizard. The readiness predicate explicitly skips Results and AlgoWizard loaded checks; AlgoWizard has a separate asynchronous preload path. | Proposed `app/ui/src/app/preload.ts`, `app/ui/src/app/router.tsx`, and workspace-owned initialization | Observed; S8, S9 |
| A08 | Conditional introductory UI | First-run settings and other conditional notices may appear. Their presence can prevent immediate unobstructed standby. | Proposed `app/ui/src/app/FirstRunDialog.tsx` and owner-specific notices | Observed code branches; S9 |
| A09 | Browser readiness acknowledgment | After its preload predicate passes, `AppService.notifyAppLoaded()` schedules a three-second delay, fades the loading overlay and requests `/main/appLoaded`. No inspected evidence establishes a fallback that declares readiness without this condition. | `app/ui/src/app/HostConnection.tsx`, proposed `app/ui/src/app/BootScreen.tsx` | Observed; S8 |
| A10 | Record UI-ready milestone | `MainServlet.onAppLoaded()` sets `MainApp.AppLoaded`, invokes after-GUI listeners, reports loading time and notifies `BrowserGUI`. The recorded September 24 run reports 51 seconds; this is not a benchmark guarantee. | Proposed `app/host/startup.py` readiness state and HTTP handler | Observed; S2, S4 |
| A11 | Restore saved strategies | After acknowledgment, `ProjectEngine.loadStrategies()` asks project databanks to load saved strategies. Logs show individual databanks completing after `APP LOADED`. This is distinct from I10's project/configuration initialization. | Proposed databank owner, potentially `app/plugins/Databank/plugin.py`, and workspace restoration handlers | Observed; S2, S4, S7 |
| A12 | After-load notifications and synchronization | The handler checks snippet-compilation failures and important updates, invokes asynchronous stock-group and broker synchronization, and contains conditional first-run edition setup and priority adjustment. Broker synchronization does not establish live account/balance synchronization. | Extension owner; proposed `app/host/updates.py`, `app/plugins/StockGroups/plugin.py`, `app/plugins/BrokerProfiles/plugin.py`, `app/host/resources.py` | Observed code; selected job completions observed; S2, S4 |
| A13 | Interactive standby | The application can accept commands while services remain active. Logs show downloads, later data sweeping and periodic databank saving. No global all-restoration-complete signal or measurement that all workers are in `WAITING` was established. | `app/host/startup.py` plus independently owned job/resource lifecycles | Observed background activity; global readiness remains unresolved; S2 |

## Readiness and ownership boundaries

| Boundary | Meaning | Evidence limit / target decision |
| --- | --- | --- |
| Desktop ready | Electron can receive backend window commands. | Does not establish initialized research services. |
| UI ready | The browser's readiness condition has led to `/main/appLoaded`. | Does not wait for every workspace or all restored strategies. |
| Restoration accounted for | Required deferred operations have completed or have explicit failure/unavailable states. | Proposed HaruQuantAI criterion; no single equivalent SQX-wide signal verified. |
| Standby | User-directed research can be admitted according to its prerequisites. | Proposed interpretation; background maintenance may continue. |

Each owner should emit progress at its real execution point. Sending a UI
directive is not evidence that rendering completed. A proposed generic startup
coordinator can track started/completed/skipped/failed/deferred outcomes, but
must not simulate initialization by printing stage labels. These target states
are not claims about SQX's internal state-machine names.

The reset removed the host feature registry. This reference does not reinstate
its historical implementation status or register new feature, requirement or
decision IDs. Concrete ownership and capability contracts remain proposals.
The existing UI registry does not prove a working backend connection after reset.

## Source locators and limitations

Sources were inspected on **2026-09-25** in this task. All donor paths below
are relative to `SQX_REFERENCE_ROOT`; proposed target paths above are relative
to `HARUQUANTAI_ROOT`. No proprietary source text, credentials, personal data,
or machine-specific absolute paths are included. Descriptions are paraphrased
behavior, except the short stage labels and technical identifiers needed to
locate the observations. No decryption of core bootstrap classes was performed.

| Source | Exact logical artifact locator | Narrow location / inspection method |
| --- | --- | --- |
| S1 | `SQX_REFERENCE_ROOT/StrategyQuantX.exe`; `StrategyQuantX.config`; `j64/release`; `internal/AppSettings.txt` beneath the same root | Executable string/symbol inspection; configuration/runtime metadata reads. |
| S2 | `SQX_REFERENCE_ROOT/user/log/StrategyQuant/log_2026_09_24.log` | Lines 1-26: server/shell; 27-44: diagnostics; 61-86: initialization; 87-140: serving/readiness; 141-155: restoration and background activity. Sensitive values excluded from this document. |
| S3 | `SQX_REFERENCE_ROOT/user/log/StrategyQuantX_ui/log_2026_9_24.log`; `SQX_REFERENCE_ROOT/user/log/StrategyQuantX_ui/log_2026_9_25.log` | Lines 23-33: local screens; 34-72: all 13 progress messages; 73-79: title/navigation. Log reads; announcement order only. |
| S4 | `SQX_REFERENCE_ROOT/internal/libs/SQWebGUILib.jar` | `javap -p -c`: `Electron.start`, `waitingForElectron`; `AbstractUIWebServer.start`, `loadAllHandlers`; `MainServlet.onAppLoaded`, `onLoadInitializationData`, `notifyUIIfSnippetsCompilationFailed`; `AutoCompiler.compileSQFiles`. Static branch inspection. |
| S5 | `SQX_REFERENCE_ROOT/internal/electron/resources/app.asar::main.js` | In-memory ASAR read: lines 14-100 arguments/profile; 159-225 connection/recovery; 367-432 window state; 464-543 window creation/header/close handlers. |
| S6 | `SQX_REFERENCE_ROOT/internal/libs/SQPluginLib.jar` | `javap -p -c`: `SQPluginManager.initForProduct`, `loadFromFolder`, `_loadPlugins`. |
| S7 | `SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar` | `javap -p -c`: `ProjectEngine.loadAvailableProjects`, `checkDefaultProjects`, `initTasks`, `loadStrategies`. |
| S8 | `SQX_REFERENCE_ROOT/internal/web/app/sq-tools/` | `generalFunctions.js:568` readiness predicate; `sqbackend/services/AppService.js:519` readiness notification and `:593` AlgoWizard preload; `SQConstants.js:426` shared loads; `SQWebSocketService.js:12` connection. Static text reads. |
| S9 | `SQX_REFERENCE_ROOT/internal/web/SQUANT/`; `SQX_REFERENCE_ROOT/internal/web/common/Batch1/libs.js` | `index.html:23` bundles and `:40` preload list; `layout/module.js:22` route resolves; `layout/LayoutCtrl.js:116` preload and `:140` introductory UI; generated batch `:73800` readiness and `:76518` onward navigation contributions. |
| S10 | Running processes from `SQX_REFERENCE_ROOT/StrategyQuantX.exe` and `internal/electron/StrategyQuantX_ui.exe` | Read-only Windows process/module/listener inspection: embedded JVM, Electron process roles, ports 5051 and 8080. No restart or controlled cold-start experiment performed. |

Selected SHA-256 fingerprints captured during the earlier inspection:

| Source artifact | SHA-256 |
| --- | --- |
| `SQX_REFERENCE_ROOT/StrategyQuantX.exe` | `95a4edb8c743a2603c388153991ddd4c666fc81ba311053fbfaf221689f3d33b` |
| `SQX_REFERENCE_ROOT/internal/libs/SQWebGUILib.jar` | `3a319dc358d46207a0e4520c6dacb694039a3d5c35b0069c08a7e869aa6fd0af` |
| `SQX_REFERENCE_ROOT/internal/libs/SQPluginLib.jar` | `40c962d2087d68aadb4bc4a3b9bb2363a453cb57830fd672c50716d502e771c3` |
| `SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar` | `9796578273f36ced388b977bf08ff67c149a8897805b0bce00f7b8d3de6241f3` |
| `SQX_REFERENCE_ROOT/internal/electron/resources/app.asar` | `a463a5e64ba5686bdbb6cb96cc74642b8f924d2104d8745afc3239a5ccf97a84` |
| `SQX_REFERENCE_ROOT/user/log/StrategyQuant/log_2026_09_24.log` | `8fc92629fa59a0ce2d20f5256663d8fd0944f745865932a5bed37cee1c4ce000` |
| `SQX_REFERENCE_ROOT/user/log/StrategyQuantX_ui/log_2026_9_24.log` | `0d35edbbc60548c83fe699162d736a85c8ae995a1c7fbf25f8606e89d922e5ff` |
| `SQX_REFERENCE_ROOT/user/log/StrategyQuantX_ui/log_2026_9_25.log` | `4ab4d41f657db5ff3471f668817c303e3e7023bc1fef41c5dc8da3568137b7fd` |

The [evidence ledger](../../docs/dev/evidence/reimplementation.json) remains the
machine-readable donor authority. No records were added or rewritten for this
README. Historical records `SQX144-EV-000001`, `SQX144-EV-000012` and
`SQX144-EV-000013` need follow-up records for launcher/control-port evidence,
bundled navigation and readiness exclusions respectively; their historical
claims must not be silently rewritten. This document is a reviewable reference,
not an assertion that those ledger reconciliations or runtime validations passed.
