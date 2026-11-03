# AlgoWizard donor responsibility map

Baseline: SQX installation `C:\SQX-145`, inspected 2026-11-03; Python source
baseline `ff0f8211`. Owner approved cleanup iteration 1 with `APPROVED: EXECUTE`.
This map governs ownership. It does **not** certify complete behavioral parity.
The earlier HSL expansion plan is set aside.

## Rules

1. One mapped responsibility has one implementation owner. HTTP routes and editor
   components delegate; they do not implement another owner's trading semantics.
2. Every new function/module needs a mapped requirement. Record necessary Python
   or host differences here and in the plan. No speculative capabilities.
3. Verify donor behavior before claiming parity. Record unavailable evidence as
   unknown. A matching filename, class count, or passing local test is insufficient.
4. Custom features require a separate proposal after parity qualification.
   Existing divergences remain visible until a specific removal/change is approved.
5. Consolidate duplication before adding layers. Configuration/examples are data.
   Do not move complexity elsewhere and report that alone as a reduction.

## Evidence and limits

- `internal/plugins/AppWizard/module.js`: navigation registration and iframe ID.
- `internal/plugins/AppWizard/AlgoWizardService.js`: `initEditor`,
  `awActionHandler`, `onRunBacktest`, `onStopBacktest`, `onLoadResultsData`,
  `getSourceCode`, and file/custom-resource handlers. Read directly.
- REA static JavaScript evidence:
  `ev_e7f6ca5d3e8e2346787e1727d29e7cb06034f7aad0016754088e9771e65ebba0`.
  Both plugin JavaScript files parsed; dynamic Angular/host calls remain partial.
  No donor runtime was executed.
- `javap -p` / `javap -c -p` inspected the plugin classes listed below. Bytecode
  confirms method names and calls; it does not establish all runtime behavior.
- `internal/web/AlgoWizard/index.html` loads the separate compiled Vue editor.
  `assets/index-C12ZW4O3.js.map` contains 268 distinct non-vendor source paths
  (127 TypeScript, 141 Vue; 256 distinct contents). Source-map entries are not an
  independently verified build-source inventory. Relevant embedded stores,
  schemas, XML helpers, and backtest actions were read; not all editor paths audited.
- `internal/libs/*.jar.enc` includes encrypted core libraries. Complete shared
  implementation, transitive dependency closure, and total source count are unknown.

## Responsibility owners

Python paths in this table are relative to `app/`. Contract files define data
only; they do not become second implementation owners. Several donor plugins
remain physically grouped under `workspace/algo_wizard` to preserve existing
integration. Grouping does not make them AlgoWizard business responsibilities.

| Donor reference | Responsibility / operations | Python implementation owner | Verification / status |
| --- | --- | --- | --- |
| `AppWizard/module.js`; `WizardAppPlugin` in `AppWizard.jar` | Navigation and host registration | Existing web workspace; `workspace/algo_wizard/routes.py` wires services | Plugin registration observed; cross-framework structure differs |
| `AlgoWizardService.initEditor`, `awActionHandler` | Host/editor coordination and action dispatch | `workspace/algo_wizard/workspace.py`; transport in `routes.py` | Workspace HTTP/acceptance tests; behavioral parity partial |
| `AlgoWizardServlet.onLoadFile`, `onSaveFile`, `onLoadExample` | Document exchange and examples | `workspace/algo_wizard/workspace.py`; `examples/*.json` | Workspace tests; HSL JSON replaces donor SQX/XML format |
| `AlgoWizardServlet.onLoadFile/onSaveFile`: shared loader, ZIP entry copy/write | Donor-native package read/write | `core/trading/strategy/files.py` | Copied donor examples and controlled archive tests; independent of HSL; production editor/API integration pending |
| `AlgoWizardRecentFiles.listJSON/save` | Recent files | `WizardService._record_recent_file`; host-owned storage | Existing file/restart tests; exact donor retention parity unqualified |
| `AlgoWizardBlocksTagCloud.listJSON/save` | Block usage preferences | No qualified current owner | Donor class observed; unimplemented parity gap, no new implementation in cleanup |
| `AlgoWizardServlet.onGetConfig`, `onValidate`, `onNegate`, `onNegateCustomBlock` | Authoring configuration and transforms | `workspace/algo_wizard/visual_blocks.py` | Visual-block tests; validation delegates to core |
| `AlgoWizardServlet.onSaveCustomBlocks/onLoadCustomBlocks`, `onSaveBlockGroups/onLoadBlockGroups` | Custom blocks and random groups | `workspace/algo_wizard/visual_blocks.py` coordinates existing block library | Visual-block tests; donor custom resource formats differ |
| `AlgoWizardServlet.onCheckResources/onResolveResources`, `onAddNewTimeframe` | Resource and timeframe coordination | `workspace/algo_wizard/visual_blocks.py` | Resource tests; full donor resolver parity unqualified |
| `AlgoWizardServlet.onBacktest/onStopBacktest/onGetBacktestResults` | Submit/cancel/read backtests | `workspace/algo_wizard/visual_blocks.py` delegates to `core/trading/backtest` | Visual-block tests; capability limits in `hsl-capabilities.md` |
| `AlgoWizardServlet.onSaveToRetester`; `ProjectEngine`, `Databank` calls | Retester handoff | `workspace/algo_wizard/workspace.py` | Workspace handoff tests; current host bundle is a format divergence |
| `ServletConstants/ConstantsServlet.onGetAll/onListCommissionMethods` | Catalogue/constants | `workspace/algo_wizard/catalogue.py` | Catalogue tests; shared entries from core HSL library |
| `ServletStrategy/StrategyServlet.onAdd/onList/onRemove/onStart/onStop` | Registered strategy lifecycle | `workspace/algo_wizard/strategies.py` | Strategy lifecycle tests; separate donor responsibility |
| `ServletAlgoCloud/AlgoCloudServlet.onImport` | Cloud import coordination | `workspace/algo_wizard/cloud_export.py` import methods | Cloud-export tests; no claim of actual AlgoCloud connectivity |
| `AlgoWizardService.getSourceCode` calls `/sourcecode/print` | Source generation coordination | `workspace/algo_wizard/cloud_export.py` export methods; existing core/extension renderers | Python/pseudocode/JSON supported; native targets blocked, not completed parity |
| `StrategyFileValidator.validate`, `StrategyChecker.strategyValid`, `StrategyFixer.fixStrategy` | Shared validation | `core/trading/strategy/hsl/validation.py`; schema in `models.py/value_models.py` | HSL document/validation tests; Python HSL is an explicit divergence |
| `StrategyBase.createXmlStrategy`, `IBacktester.run/stop`, `SQBacktester.getResultsGroup` | Shared compilation and execution | `core/trading/strategy/hsl/compiler.py`, core runtime and backtest owners | Core trading tests; donor core internals unavailable |
| `DataManager`, `SessionManager`, `TimeframeManager`, `ProjectCustomResources`, `CustomBlocks`, `RandomGroups` | Shared data/resources | Existing core data/block services and workspace data owners | Direct donor call sites verified; complete shared parity not established |
| `internal/web/AlgoWizard` embedded stores/components/XML helpers | Visual authoring state and interaction | `web/workspaces/algo_wizard` | Existing web tests; Vue-to-React implementation differs; unchanged in cleanup |

Contracts remain beside their consuming service:
`workspace_models.py`, `visual_blocks_models.py`, `strategies_models.py`, and
`cloud_export_models.py`. Shared catalogue contracts already live in core HSL.
`__init__.py` exposes existing package APIs; it owns no business logic.

## Explicit divergences and open gaps

- HSL JSON, Python AST validation, fingerprints, canonical native Python export,
  and revision-aware host storage are existing host choices, not literal SQX
  implementations. Retained; no new language or storage features in this cleanup.
- Export target discovery/rendering is co-located with cloud import despite the
  donor's separate source-code endpoint. HTTP contracts remain unchanged.
- The four existing examples are HaruQuant examples, not claimed donor copies.
  Cleanup changes their representation only. No replacement strategies invented.
- Richer strategy endpoints (get/status/revision behavior) remain existing
  divergences. Removal requires a separate plan.
- Tag-cloud behavior, resource resolution, backup flows, native exports, and
  execution gaps require separate parity work. See `hsl-capabilities.md`; fail-closed
  rejection is not evidence of feature completion.
- Python typed contracts and the existing response/logging host conventions are
  justified host differences. Shared response construction belongs to
  `core/lib/responses.py`; validation diagnostic formatting belongs to its validator.

## Cleanup inventory and qualification

Before: 18 workspace Python files, 5,573 physical lines; seven files are alias
modules with no independent implementation. Four example builders occupy 402 lines.
Five services repeat typed response construction; three repeat validation formatting.

Cleanup target: 11 Python files, four JSON resources, no replacement alias modules
or new production Python files. Direct core imports replace the deleted aliases.
Public HTTP routes, package-level exports, and persisted document formats remain.
Old alias-module import paths are intentionally removed; repository callers migrate.

Measured after cleanup: 11 workspace Python files / 4,836 physical lines (737
fewer); `workspace.py` falls from 986 to 526 lines. Across all changed application
Python files the net reduction is 689 lines after including the shared helpers and
documentation. The four JSON resources contain 943 lines, including serialized
schema defaults: this is removal of Python construction logic, not a claim that
the combined Python-plus-data text is smaller.

Qualification tests: `tests/workspace/algo_wizard`, affected retester cross-check
tests, `tests/extend/monte_carlo/test_retest_methods.py`, and
`tests/core/lib/test_responses.py`. Resource regression hashes are captured from
the pre-cleanup builder outputs, independently of the new loader. Full-suite and
coverage results, exact commands, final inventory, and residual failures are
reported in the approved task's chat walkthrough, not inferred here.

Further consolidation requires evidence of duplicated responsibility and an
approved plan. Eleven files is this cleanup's target, not a universal quota.

## Donor document file boundary (approved iteration 1)

Baseline `3fab40fd`; owner authorized the document file boundary with
`APPROVED: EXECUTE`. One new production module, `core/trading/strategy/files.py`,
owns native package contents. Existing HSL modules remain unchanged; the new
owner neither translates XML into HSL nor introduces another strategy language.

- `SqxEntry` holds a name, payload bytes, and optional original ZIP metadata.
  `SqxDocument` holds ordered entries and the archive comment. Strategy bytes
  and optional `lastSettings.xml` are projections of those entries, not copies
  that can drift apart. Missing settings are `None`; present empty settings are
  `b""`. XML text, unknown elements/attributes, comments, and numeric spelling
  survive unchanged because validated XML is never reserialized.
- `read_sqx` corresponds to the package-loading boundary. It reads entries without
  extraction, checks ZIP integrity and the `StrategyFile/Strategy` structure, and
  checks nonempty last-settings XML for well-formedness. It does not invoke or
  imitate the encrypted Loader, StrategyFixer, or legacy conversion routines.
- `write_sqx` corresponds to the observed archive-copy branch of `onSaveFile`:
  preserve entry order, unrelated payloads, archive comments, and original entry
  metadata where supported by Python's ZIP writer. Zero-valued file attributes
  are explicitly retained despite Python's default permission behavior. Save
  uses a temporary sibling and final replacement, preserving an existing file
  when validation or writing fails. This adds no host database schema.
- The supported preservation guarantee is entry payload bytes and tested ZIP
  metadata, not identical compressed archive bytes or ZIP signatures. Editing
  strategy XML does not qualify retained results for the edited strategy. Result
  freshness and the donor's backtested-save branch remain outside this boundary.
- Host differences: standard-library ZIP/XML types instead of Java ZIP/JDOM;
  atomic replacement instead of in-place archive rewrite; bounded reads of at
  most 4,096 entries / 256 MiB uncompressed. These are file-boundary controls,
  not new trading functionality. Encrypted entries, malformed/ambiguous packages,
  and unsupported legacy extensions are explicitly rejected with logged errors.
- Production UI, route registration, recent-file persistence, HSL conversion,
  validation semantics, and runtime execution remain outside this slice.

### Fixture provenance

Read-only originals: `C:\SQX-145\internal\web\AlgoWizard\examples\`.
Byte-for-byte copies are under `tests/core/trading/strategy/fixtures/`:

| Example | SHA-256 |
| --- | --- |
| `EMACross.sqx` | `98a7ccb03937e113cbaf6a50e883d0b14b4e33bb08cc851be6d3c3e36ebc3700` |
| `InsideBarBreakout.sqx` | `1dfb87f46b1ff52b5bd524b7b217a6f3bb783c83ab8441df87a7ac4e2420ff17` |

Both contain `META-INF/MANIFEST.MF` and `strategy_Portfolio.xml`, version
`3.9.130`, with no last-settings entry. Settings, opaque binary results, directory
entries, unknown resources, deliberate XML edits, metadata, corruption, and
failure preservation are qualified using controlled test packages. No user
strategy archives are included. Full donor validation and execution parity is
not established by these fixtures.
