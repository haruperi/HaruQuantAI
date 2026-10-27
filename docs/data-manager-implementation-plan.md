# Data Manager implementation plan

Status: implemented after the user explicitly instructed “Proceed to implement”. External acceptance gates 11, 44 and 62 remain open; see the functional coverage report.

Prepared: 2026-10-27. Scope: the 35 previously flagged items in the functional coverage review, preserving IDs for traceability. Historical file names, method names and transport labels in the pasted list are not design requirements; user-visible behavior determines whether work is needed. The other 39 items remain regression requirements, not rewrite targets.

Repository root: `C:/Users/rharu/AppDev/HaruQuantAI`. Every file below is relative to that root. Names marked **new** are proposed implementation locations derived from current code ownership, not names to reproduce from the pasted material; other names identify existing code to modify. A listed existing module is not permission for an unrelated refactor.

## Functionality-first rule and revision

A checklist item is an acceptance outcome, not an instruction to create a similarly named function, class, route or file. If current code already provides that outcome, verify it and leave it in place. If the UI is disconnected, repair the connection. Only add domain code for behavior that is actually absent.

**Removed from the previous draft:** dedicated BMF registration methods/routes, separate application/TickDownloader/Darwinex import wrapper methods/routes, a duplicate Data Manager connection API, generic job submission/logging wrappers and redundant job URL aliases, a second dataset-get wrapper, and the assumed second MT5 transport. These were unnecessary or premature implementation fragmentation.

For each proposed addition below, the named function must perform substantive missing work or be a necessary HTTP/UI boundary. A function that merely forwards to a working existing function with a different name is not part of this plan. Existing algorithms are not copied or moved simply to match the checklist structure.

**MT4 example:** keep `encode_hst_bytes()` and `encode_fxt_bytes()` where they are. The export operation reads the selected stored prices, validates the requested file options, calls the appropriate existing encoder directly, and delivers its bytes. There is no new `encode_mt4()` facade, no second codec, and no recreation of the old pasted action method. Encoder changes are allowed only if a verified option/compatibility defect requires them.

## Corrections and reuse established during planning

- Requirement 62 is missing an operational export workflow, not binary encoders. `app/workspace/brokers/files.py` already implements `encode_hst_bytes()`, `encode_fxt_bytes()`, `decode_hst_bytes()` and `decode_fxt_bytes()`. Reuse and independently validate these; do not create another MT4 codec module.
- Requirement 53 already has a workspace COT button, `updateCotIndicators()`, the HTTP endpoint, and `CustomData.update_cot()`. Start with verification and error/progress handling, not a second COT implementation.
- Requirement 44 is evaluated as importing actual history from the connected MT5 terminal. The existing bridge already provides that behavior in code; verify the complete flow first. The old Python-API label does not justify a second transport. No new adapter or dependency is planned.
- `scan_catalog(..., decode=True)` already reads canonical historical prices. `publish_frame()` and `FilePublication` already stage and publish data. Extend these paths instead of introducing another storage engine.
- Existing `JobManager`, `JobContext`, `Logs`, host WebSocket transport, and download job routes are the operation infrastructure. No second task queue, progress simulator or event bus.
- Requirements 09–11, 40, 43, 46, 49 and 53 were partly marked unverified. Implement only the specific integration gaps below; do not replace working clients simply because the initial audit lacked live evidence.

## File and size boundaries

The revised ceiling is **8 new runtime source files**, reduced from nine. These are bounded locations for demonstrably missing behavior, not files that must be created to satisfy the checklist. If the acceptance outcome can be met by extending current code cleanly, omit the proposed file and record that simpler placement. Each retained file must have a distinct responsibility that would otherwise enlarge an already broad module. No new feature package, framework, generic repository layer, or one-file-per-requirement scheme.

| New runtime file | Exact public owner / functions | Responsibility and approximate size budget |
|---|---|---|
| `app/host/vault.py` | `WindowsCredentialVault.store()`, `.resolve()`, `.revoke()` | OS credential storage behind the existing vault interface; 100–180 lines. |
| `app/workspace/data_manager/sources/connections.py` | `build_provider_testers()`, `test_provider_access()` | Provider-specific read/authentication/entitlement checks absent from the host tester registry; 160–260 lines. Existing host routes and metadata remain the API. |
| `app/workspace/data_manager/sources/files.py` | `preview_import()`, `import_files()`, `register_file_routes()` | Actual upload/staging, bounded parsing and canonical publication missing from the UI flow; 300–450 lines. Source/format options choose existing decoders within the same pipeline. No class or per-provider forwarding methods. |
| `app/workspace/data_manager/brokers/imports.py` | `parse_broker_records()`, `import_broker_records()`, `register_broker_import_routes()` | Shared JSON/XML normalization, selection/conflict handling and persistent broker imports; 220–350 lines. |
| `app/workspace/data_manager/data/review.py` | `DatasetReview.rows()`, `.chart()`, `.summary()`, `.save_changes()`, `.quality()`, `.index_for_date()`; `register_review_routes()` | Shared real-history queries and review/quality HTTP handlers; 350–500 lines. |
| `app/workspace/data_manager/data/exports.py` | `DataExports.export_csv()`, `.export_mt4()`, `.export_mt5()`, `.run_export()`; `register_export_routes()` | Stream real history to export artifacts; reuse MT4 encoders and existing UI format definitions; 300–450 lines. |
| `app/workspace/data_manager/data/transforms.py` | `clone_to_timezone()`, `shift_frame_clock()`, `register_transform_routes()` | Copy/shift job and lineage, using canonical publication; 180–300 lines. |
| `ui/app/plugins/data_source/Common/ProviderConnectionsDialog.tsx` | `ProviderConnectionsDialog()`, `loadConnections()`, `saveConnection()`, `testConnection()` | One connection CRUD/test dialog shared by providers; 180–280 lines. |

Size numbers are review budgets, not reasons to compress code. Exceeding a budget requires revising this plan before adding another file or broadening a module. No large new helper file is allowed as an unreviewed escape hatch.

Existing `app/workspace/data_manager/custom/feature.py` is about 927 lines, `app/workspace/data_manager/symbols/_helpers.py` about 834, `app/workspace/data_manager/sources/dukascopy.py` about 747, and `ui/app/workspace/DataManager/DataManager.tsx` already hosts many flows. They must not absorb the new ingestion/export/review implementations. Workspace changes are limited to wiring, selection, job subscriptions and invoking existing dialogs.

### Shared existing-file changes

These changes serve multiple numbered remedies; implement each once.

| Existing file | Exact existing or proposed symbols | Bounded change |
|---|---|---|
| `app/workspace/data_manager/__init__.py` | `create_router()` | Register the new route groups once. No business logic. |
| `app/host/persistence.py` | `HostPersistence.ensure_datasets_schema()`; **new** `ensure_broker_cost_schema()` | Add nullable dataset links/clock metadata and broker cost columns with idempotent additive migrations. No new parallel catalog tables. |
| `app/workspace/data_manager/data/storage.py` | `publish_frame()`; **new** `replace_range()` | Keep the existing publication protocol. Add bounded replacement of edited/deleted ranges using the same staged files and rollback journal. |
| `app/workspace/data_manager/sources/download_jobs.py` | existing `manager()`, `register_download_jobs()` | Extend owned operation kinds and restart reconciliation. Workers are submitted directly with existing `JobManager.submit_job()` and report through existing `Logs.record_progress()`. Keep existing URLs; no generic forwarding wrappers or aliases. |
| `app/main.py` | `create_app()` / its `lifespan()` | Wire the vault and default provider testers while preserving injected test doubles. Retain one lifecycle owner for jobs and adapters. |
| `ui/app/plugins/data_source/Common/historicalSourceStore.ts` | `useHistoricalSources.start()`, `.poll()`, `.action()`; **new** `.trackJob()` | Reuse job tracking for generic Data Manager operations without overwriting another active job. |
| `ui/app/workspace/DataManager/DataManager.tsx` | `DataManager()`, `selectCommand()`, `providerAction`, existing job effects | Wire operations and dialogs; remove timer-driven completion for replaced paths. Do not place new domain logic here. |

## Requirement-by-requirement remedies

### 09 — List external provider connections — partial

**Gap:** host metadata exists, but the Data Manager provider view is incomplete.

**Remedy:** list configured connections by provider, distinguish configured/enabled/connected/entitled states, and show which saved connection a download uses.

**Exact placement:**

- `app/host/transport.py`: existing `ServletConnection.list_connections()` and `_conn_route()` serve the existing `/api/v1/connections` API, using its existing provider filter. Extend the returned status only for verified runtime information. No duplicate `/data/connections` API.
- **New** `ui/app/plugins/data_source/Common/ProviderConnectionsDialog.tsx`: `ProviderConnectionsDialog()` and `loadConnections()` render the list.
- `ui/app/plugins/data_source/Common/HistoricalSourceDialog.tsx`: `HistoricalSourceDialog()` opens that dialog and accepts a `connection_id`.

**Done when:** saved provider records appear after restart; public/no-credentials feeds are clearly distinguished; disabled/missing connections cannot be shown as authenticated.

### 10 — Add/edit provider credentials — partial

**Gap:** credential editing, rotation and download use are not a complete workflow.

**Remedy:** upsert connection metadata, write secrets to the OS vault, retain only references in SQLite, and resolve those references when constructing provider clients. Keep secrets out of responses, browser persistence and logs.

**Exact placement:**

- **New** `app/host/vault.py`: `WindowsCredentialVault.store()`, `.resolve()`, `.revoke()`.
- `app/host/transport.py`: extend `Vault` protocol with `store()`; add `ServletConnection.update_connection()`; extend `_conn_route()` and `create_transport_router()` for `PUT /connections/{connection_id}`. Preserve reference ownership checks.
- `app/host/transport.py`: existing `ServletConnection.save_connection()` and proposed `update_connection()` own secret rotation and failed-save cleanup within the existing connection API. Resolve saved vault references in the existing client-construction path, not through another public connection service.
- `app/workspace/data_manager/sources/_helpers.py`: extend `make_client()` to accept resolved connection options; `app/workspace/data_manager/sources/_base.py`: extend `BaseSource._get_client()` to select the saved connection.
- `app/main.py`: `create_app()` uses the default vault only when an injected vault was not supplied.
- **New** `ui/app/plugins/data_source/Common/ProviderConnectionsDialog.tsx`: `saveConnection()` supports create/edit/rotate without reloading saved secret values.

**Done when:** create, edit, test, download and credential rotation use the same connection; failed updates preserve the prior usable connection. If the OS vault is unavailable, report that state instead of storing plaintext.

### 11 — Connectivity/authentication/subscription tests — partial

**Gap:** testers are injectable but not comprehensively registered; a socket ping is insufficient proof of feed access.

**Remedy:** configure read-only provider tests with separate network, authentication and entitlement outcomes. Public feeds report `authentication: not_required`; an unverifiable subscription reports `unknown`, never success.

**Exact placement:**

- **New** `app/workspace/data_manager/sources/connections.py`: `build_provider_testers()`, `test_provider_access()` use existing broker clients and a bounded representative read. Catalog discovery calls the selected client's existing `get_symbols()` / `get_symbol_info()` directly in `source_command()`, with no catalog facade.
- `app/host/transport.py`: `ServletConnection.test_connection()` retains timeout handling and accepts structured provider results while preserving the existing authenticated boolean contract.
- `app/main.py`: `create_app()` registers defaults, then overlays explicitly injected testers.
- **New** `ui/app/plugins/data_source/Common/ProviderConnectionsDialog.tsx`: `testConnection()` renders each result independently.

**Done when:** tests cover invalid credentials, denied entitlement, timeout, unreachable feeds and public feeds; live configured accounts complete a read-only smoke test. No synthetic prices or trading orders.

### 13 — Broker spread/commission defaults — partial

**Gap:** broker CRUD rejects custom cost models.

**Remedy:** persist validated broker defaults and apply them only when a symbol explicitly inherits profile costs. Preserve explicit symbol overrides and existing broker records.

**Exact placement:**

- `app/host/persistence.py`: **new** `HostPersistence.ensure_broker_cost_schema()` adds `spread_model_json` and `commission_model_json` to `datamgr_broker`, defaulting to inherited costs.
- `app/workspace/data_manager/brokers/_helpers.py`: extend `BrokerInfo`, `_FIELDS`, `_row()`, `_editable()`; add `validate_cost_models()` and `resolve_profile_costs()`.
- `app/workspace/data_manager/brokers/feature.py`: `Brokers.add()`, `.edit()`, `.load()`, `.save()` preserve those models.
- `app/workspace/data_manager/brokers/http.py`: `_broker_ui()` returns saved values; `_broker_save_route()` validates rather than rejects them.
- `ui/app/plugins/data_source/Catalogs/BrokerProfiles/brokerProfiles.ts`: existing model types/validation; `ui/app/plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient.ts`: `saveBroker()` serialization; `ui/app/plugins/data_source/Catalogs/BrokerProfiles/BrokerProfilesModal.tsx`: `save()` and model controls.
- **New** `app/workspace/data_manager/brokers/imports.py`: `import_broker_records()` applies the already exposed `use_profile_costs` option explicitly.

**Done when:** costs survive restart/export/import; inherited versus overridden costs are tested. This is configuration resolution, not a rewrite of backtesting commission calculations.

### 15 — Import broker instrument definitions from JSON/XML — partial

**Gap:** the JSON UI calls an absent route; XML normalization is absent.

**Remedy:** normalize both formats to one validated symbol payload, honor selection/postfix/conflict options, and return confirmed created/updated/failed identities matching the existing UI contract.

**Exact placement:**

- **New** `app/workspace/data_manager/brokers/imports.py`: `parse_broker_records()`, `import_broker_records()`, `register_broker_import_routes()`; routes `POST /brokers/import-preview` (nested `preview_broker_records()`) and `POST /brokers/{id}/import-symbols`.
- `app/workspace/data_manager/brokers/http.py`: `register_broker_routes()` registers that group.
- `app/workspace/data_manager/symbols/http.py`: reuse `symbol_updates()`; `app/workspace/data_manager/symbols/feature.py`: reuse `Symbols.add()` and `.edit()` with the existing transaction gateway.
- `ui/app/plugins/data_source/Catalogs/BrokerProfiles/BrokerRecordImportDialog.tsx`: `browse()` sends JSON/XML text to a server preview; `start()` imports the returned normalized records and keeps existing confirmed-result checks. `ui/app/plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient.ts` gains **new** `previewBrokerRecords()`; the backend importer owns parsing, so XML is not independently reimplemented in TypeScript.
- `ui/app/plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient.ts`: retain `importBrokerRecords()` contract.

**Done when:** selection, overwrite, duplicate, invalid numeric, wrong broker and partial-failure cases have tests. XML supports a documented versioned schema with rejected DTD/entities; it does not guess arbitrary vendor XML. See scope decisions below.

### 16 — Import broker session definitions from JSON/XML — partial

**Gap:** session imports have the same absent route and XML gap.

**Remedy:** reuse the importer from 15 with session-specific normalization, preserving intervals, timezone, holidays and broker assignment.

**Exact placement:** **new** `app/workspace/data_manager/brokers/imports.py`: `parse_broker_records()` and `import_broker_records(kind="sessions")`; `register_broker_import_routes()` adds `POST /brokers/{id}/import-sessions`. Reuse `app/workspace/data_manager/sessions/feature.py`: `Sessions.add()` / `.edit()` and `app/workspace/data_manager/sessions/_helpers.py`: existing `_row()` validates the domain fields through `Sessions.add()` / `.edit()`. Do not add a second UI-to-session mapper. UI remains `BrokerRecordImportDialog.browse()` / `.start()` and `importBrokerRecords()`.

**Done when:** round-trip holiday/timezone/interval fixtures match, invalid schedules fail visibly, system-profile protections remain, and committed identities match the response.

### 21 — Edit dataset properties, broker and session — partial

**Gap:** dataset PUT is absent, and session/symbol-definition links are not consistently persisted.

**Remedy:** validate and persist dataset links and editable metadata. Treat changing a display timezone separately from shifting historical timestamps. A symbol rename must move storage ownership safely, not just change a catalog label.

**Exact placement:**

- `app/workspace/data_manager/data/feature.py`: **new** `Data.edit()` for validated persistent edits; `Data.list()` returns the links.
- `app/workspace/data_manager/data/_helpers.py`: **new** `validate_dataset_updates()` and `resolve_dataset_links()`.
- `app/workspace/data_manager/data/http.py`: `register_data_routes()` adds `PUT /datasets/{dataset_id}` through **new** nested `edit_dataset()`.
- `app/host/persistence.py`: `ensure_datasets_schema()` adds nullable `symbol_definition_id` and `session_id` and clock metadata; backfill only unambiguous existing links.
- `app/workspace/data_manager/data/partition_files.py`: extend `FilePublication` only if a rename needs move/recovery metadata; use `dataset_lock()` for the operation.
- `ui/app/plugins/data_source/Common/dataManagerStore.ts`: `editDataset()` sends and consumes the saved links and confirmed identity.
- `ui/app/workspace/DataManager/DataManagerPanels.tsx`: `DatasetTable()` receives edit controls; add **new** `DatasetEditDialog()` in the same file to own form fields and `save()`. `ui/app/workspace/DataManager/DataManager.tsx`: `DataManager()` adds only dialog state and **new** `openDatasetEdit()` wiring, not form/business logic.

**Done when:** edited properties survive reload, missing links and duplicate destinations fail, and interruption cannot leave SQLite pointing at a partially renamed history directory.

### 23 — Register BMF/B3 futures symbols — missing workflow

**Gap:** the current UI does not complete registration of Brazilian futures through the existing catalogs.

**Remedy:** extend the generic symbol/dataset registration form and operation to accept exchange, contract code/expiry, pricing, broker and session. BMF/B3 is metadata on a futures contract, not a new registration service or data provider.

**Exact placement:**

- `app/workspace/data_manager/sources/http.py`: existing `create_dataset()` validates/persists the selected symbol definition and dataset with canonical fields and checks the persistence result. Repair its hard-coded category/date and obsolete fields as part of the general registration fix used by 24 as well. No `add_bmf()` method or `/datasets/bmf` route.
- `app/workspace/data_manager/data/_helpers.py`: the shared proposed `validate_dataset_updates()` validates applicable contract/exchange/expiry metadata; no separate forwarding validator solely named for BMF.
- `app/workspace/data_manager/symbols/feature.py`: existing `Symbols.add()` stores the specification; existing symbol fields/structured metadata carry exchange and pricing.
- `ui/app/plugins/data_source/FileImport/add/addPopup.tsx`: `AddPopup()` offers futures contract/exchange fields; `ui/app/plugins/data_source/FileImport/add/DataSourceFilesAddCtrl.ts`: existing `useFilesAdd()` submits the generic registration.
- `ui/app/plugins/data_source/FileImport/DataSourceFilesService.ts`: existing `filesService.addSymbolDefinition()` / `.addSymbol()` call confirmed generic operations; no `addBmf()` helper.
- Dataset `lineage_json` records exchange/expiry provenance. No separate futures catalog, download feed or continuous-contract rolling engine.

**Done when:** a BMF/B3 contract specification persists after reload and has zero bars until actual file/terminal history is imported. User-supplied unknown pricing is required explicitly, never invented.

### 24 — Add a definition from a local history file — partial

**Gap:** browser planning is not authoritative durable registration.

**Remedy:** server-side preview extracts available metadata; user confirms missing pricing/session/broker fields, then registers the symbol/dataset before ingestion. Failed imports leave an explicitly empty definition, not fabricated bar counts.

**Exact placement:** **new** `app/workspace/data_manager/sources/files.py`: `preview_import()` and `register_file_routes()` for actual file inspection; existing `app/workspace/data_manager/sources/http.py::create_dataset()` and `Symbols.add()` for registration; `ui/app/plugins/data_source/FileImport/DataSourceFilesService.ts`: `filesService.addSymbolDefinition()` / `.addSymbol()` become asynchronous confirmed operations; `ui/app/plugins/data_source/FileImport/add/DataSourceFilesAddCtrl.ts`: `useFilesAdd()` submits the server preview and confirmed values. Reuse existing `Symbols` service and `data` catalog schema.

**Done when:** restart retains the definition; guessed contract size is not silently treated as provider metadata; duplicate and invalid file handling is visible.

### 25 — Import CSV/TXT/archive history into Parquet — partial

**Gap:** the UI submits metadata to an absent route and swallows failure.

**Remedy:** submit actual file bytes plus the selected format, stage them for the job lifetime, parse/validate in bounded batches, normalize timestamps/prices, and publish using canonical storage. Support CSV/TXT and ZIP/GZIP containers; reject unknown archive formats explicitly.

**Exact placement:**

- **New** `app/workspace/data_manager/sources/files.py`: `preview_import()`, `import_files()`; private `_stage_upload()`, `_iter_input_files()`, `_parse_batches()`; `register_file_routes()` provides `POST /datasets/import` and `POST /datasets/import-preview`.
- `app/workspace/brokers/files.py`: reuse `parse_delimited_bars()`, `parse_delimited_ticks()`, `read_parquet_bars()`; extend parser arguments for saved column/date formats and add a batch iterator only where existing parsing requires it. Do not duplicate HST/FXT parsing.
- `app/workspace/data_manager/data/storage.py`: reuse `publish_frame()` and real coverage updates.
- `app/workspace/data_manager/sources/download_jobs.py`: existing `manager()` supplies `JobManager.submit_job()` directly; `import_files()` reports committed work through existing `JobContext` and `Logs` methods, without submission/logging facades.
- `ui/app/plugins/data_source/FileImport/fileImport.ts`: extend `ImportTask` to retain input file handles and format settings, not just timestamps; `ui/app/plugins/data_source/FileImport/fileImportStore.ts`: `useFileImports.start()` / `.advance()` / `.action()` become submit/poll/control operations.
- `ui/app/plugins/data_source/FileImport/import/DataSourceFilesImportCtrl.ts`: `useFilesImport()` retains the selected `File` until submission; `ui/app/plugins/data_source/FileImport/DataSourceFilesService.ts`: `filesService.start()` awaits confirmed submission.

**Done when:** known uploaded prices exactly match decoded stored history; invalid rows follow the chosen abort/skip policy; cancellation retains committed batches and removes staged temporary inputs when no longer needed; UI errors are not suppressed.

### 26 — Import directly from external trading applications — missing

**Gap:** no working application-history path.

**Proposed bounded scope:** MT4 local HST/FXT history and MT5 terminal history through the existing working integration. Other applications require an identified readable format/API before they can be promised.

**Exact placement:** **new** `app/workspace/data_manager/sources/files.py`: `import_files()` accepts application/format options and calls `decode_hst_bytes()` / `decode_fxt_bytes()` in existing `app/workspace/brokers/files.py`; MT5 delegates to remedy 44. Extend `ui/app/plugins/data_source/FileImport/import/importPopup.tsx`: `ImportPopup()` with application/source mode; `ui/app/plugins/data_source/FileImport/DataSourceFilesService.ts`: existing `filesService.start()` with application/format options; no separate forwarding method; `ui/app/plugins/data_source/Common/dataSourceRibbon.ts`: add application-import command; `DataManager.selectCommand()` wires the existing dialog.

**Done when:** application-history files/terminal reads reach the same canonical storage and job results as 25; the picker does not require a user-created intermediate CSV. No process-memory scraping or new trading-app framework.

### 28 — Bulk import across directories — partial

**Gap:** directory planning uses the incomplete single-file path and timer progress.

**Remedy:** submit a manifest of actual files, deterministic conflict policy, per-file results and one parent job. Reuse the importer from 25; do not create another mass-import engine.

**Exact placement:** **new** `app/workspace/data_manager/sources/files.py`: `import_files()` and `_iter_input_files()`; `ui/app/plugins/data_source/FileImport/massImport/DataSourceFilesMassImportCtrl.ts`: `useFilesMassImport()` preserves `File` handles/relative paths and submits the manifest; `ui/app/plugins/data_source/FileImport/fileImportStore.ts`: `useFileImports.start()` / `.advance()` / `.action()` render actual results. Existing `ui/app/plugins/data_source/FileImport/massImport/massImportPopup.tsx`: `MassImportPopup()` shows per-file outcomes.

**Done when:** nested directories, duplicate names, skip/replace/error policies and cancellation are covered with real uploads; successful file counts reflect commits.

### 38 — TickDownloader tick/minute ingestion — partial

**Gap:** archive reader exists; workspace import creates zero-bar local definitions and simulated completion.

**Remedy:** inspect the selected folder, read real ticks/minute files with existing parsers, register discovered datasets, and invoke the importer from 25.

**Exact placement:** **new** `app/workspace/data_manager/sources/files.py`: `import_files()` with TickDownloader source/format options; no dedicated wrapper; reuse `app/workspace/brokers/tick_downloader.py`: `TickDownloaderClient.get_bars()` / `.get_ticks()` for supported archive discovery/decoding. `ui/app/plugins/data_source/TickDownloader/DataSourceTDService.ts`: `tdService.importData()` / `.importDataAction()`; `ui/app/plugins/data_source/TickDownloader/import/DataSourceTDImportCtrl.ts`: `useDataSourceTDImport()` and `start()`; `ui/app/plugins/data_source/Common/dataManagerStore.ts`: `useTickDownloader.start()` / `.advance()` / `.action()` use confirmed backend jobs.

**Done when:** fixture folders produce exact stored tick/minute rows, date coverage and counts; empty folders and unavailable files fail without a success animation.

### 40 — Darwinex disclaimer — partial

**Gap:** a disclaimer component exists outside the active generic source flow.

**Remedy:** render that existing disclaimer in the active flow before registration/download when required. Reuse the current text and consent rules; do not author substitute provider legal terms.

**Exact placement:** `ui/app/plugins/data_source/Common/HistoricalSourceDialog.tsx`: `HistoricalSourceDialog()` / `submit()`; `ui/app/plugins/data_source/Darwinex/disclaimer/darwinexDisclaimerCtrl.ts`: reuse `useDarwinexDisclaimer()` for close behavior; consent state stays in `HistoricalSourceDialog()`; `ui/app/plugins/data_source/Darwinex/disclaimer/darwinexDisclaimerPopup.tsx`: reuse `DarwinexConsent` from its existing module export.

**Done when:** users can open/read the disclaimer from the actual dialog, required consent gates submission, and failed/cancelled requests do not falsely record a completed operation.

### 42 — Import already-downloaded Darwinex files — partial

**Gap:** the import command routes to an online source dialog rather than importing the selected downloaded folder.

**Remedy:** send the local Darwinex manifest to the shared file ingestion path and reuse the existing decoder.

**Exact placement:** **new** `app/workspace/data_manager/sources/files.py`: `import_files()` with Darwinex archive options; no dedicated wrapper; existing `app/workspace/brokers/darwinex.py`: reuse `decode_darwinex_dat()`. `ui/app/plugins/data_source/Darwinex/import/importPopupCtrl.ts`: `useImportPopup()` / `start()`; `ui/app/plugins/data_source/Darwinex/DarwinexService.ts`: existing `darwinexService.start()` submits those files to the shared pipeline; no new forwarding method; `DataManager.selectCommand()` distinguishes `darwinex-import` from online add/download.

**Done when:** selected local bid/ask files import with the network disabled and generate the expected canonical rows; malformed or mismatched pairs report precise failures.

### 43 — Discover/select Darwinex instruments — partial

**Gap:** the active dialog only accepts typed symbols despite an existing catalog client and selection component.

**Remedy:** load the authenticated provider catalog, allow filtering and multi-select, and retain typed entry as an explicit optional input.

**Exact placement:** `app/workspace/data_manager/sources/http.py`: existing `source_command()` handles the catalog action by calling the selected client's existing `DarwinexClient.get_symbols()` / `.get_symbol_info()` from `app/workspace/brokers/darwinex.py`; no additional catalog facade; `ui/app/plugins/data_source/Common/HistoricalSourceDialog.tsx`: `HistoricalSourceDialog()` consumes it; `ui/app/plugins/data_source/Darwinex/add/selectSymbolsPopup.tsx`: reuse `SelectSymbolsPopup()` with real catalog rows instead of fixtures.

**Done when:** displayed catalog rows come from the selected connection, selection is sent as provider symbols, and catalog failures are shown instead of fixture fallback.

### 44 — Import MT5 terminal history — verify existing behavior first

**Gap:** the previous plan incorrectly treated the pasted Python-API label as a reason to add a second transport. Actual historical reads already exist through the terminal bridge.

**Remedy:** verify that selecting an actual connected terminal, importing bars/ticks where supported, persisting the history and displaying failures works end to end. Repair only observed failures in that path.

**Exact placement:** existing `app/workspace/brokers/metatrader.py`: `MetaTraderClient.get_bars()` / `.get_ticks()`; existing `app/workspace/data_manager/sources/_helpers.py`: `make_client()`; existing `app/workspace/data_manager/sources/_base.py`: `BaseSource.download()`; existing `ui/app/plugins/data_source/Common/HistoricalSourceDialog.tsx`: `HistoricalSourceDialog()`. Extend existing `tests/workspace/data_manager/test_sources.py` and `ui/tests/e2e/data-manager-mt5-import.spec.ts` for that behavior.

**Done when:** actual terminal history reaches canonical storage, invalid/disconnected terminals fail visibly and UI progress reflects committed results. If this already passes, close the item with verification only. No new Python adapter, sidecar, transport selector, public forwarding method or dependency change. Direct SDK transport would require a separate explicit functional reason, not the old label.

### 46 — Equity usage conditions — partial

**Gap:** the existing conditions are not established in the active generic workflow.

**Remedy / exact placement:** `ui/app/plugins/data_source/Common/HistoricalSourceDialog.tsx`: `HistoricalSourceDialog()` / `submit()` render `EquityDataUsageConditions()` from existing `ui/app/plugins/data_source/SQData/Equity/add/dataUsageConditionsPopup.tsx` and enforce its existing consent rule. Preserve provider/source identity when the dialog changes.

**Done when:** opening the actual equity workflow presents the conditions and required acknowledgement; changing the provider cannot carry unrelated consent forward.

### 49 — Futures usage conditions — partial

**Gap:** the futures path has the same active-flow integration problem.

**Remedy / exact placement:** `ui/app/plugins/data_source/Common/HistoricalSourceDialog.tsx`: `HistoricalSourceDialog()` / `submit()` use existing `ui/app/plugins/data_source/SQData/Futures/add/dataUsageConditionsPopup.tsx`: `FuturesDataUsageConditions()`; same shared consent handling as 46, with futures-specific source identity.

**Done when:** active futures add/download routes present the intended conditions; no second terms component or invented text is introduced.

### 53 — COT historical updates — partial / primarily verification

**Gap:** initial audit did not establish live completion. The button/API/service are already present.

**Remedy:** verify the existing implementation first. Add job/error reporting only where the current synchronous operation prevents accurate user feedback; do not rewrite COT parsing or storage.

**Exact placement:** `app/workspace/data_manager/custom/feature.py`: existing `CustomData.update_cot()`; `app/workspace/data_manager/custom/http.py`: existing `update_cot()` inside `_custom_export_routes()` submits with existing `JobManager.submit_job()` from the existing `manager()` only if background execution is needed; `ui/app/plugins/data_source/Indicators/externalIndicatorsApiClient.ts`: existing `updateCotIndicators()` accepts the confirmed job/result contract; `ui/app/workspace/DataManager/DataManager.tsx`: extract the existing COT click handler to **new** `handleCotUpdate()` to track/refresh the result. New test cases go into existing `tests/workspace/data_manager/test_custom.py`, `tests/workspace/data_manager/test_custom_http.py` and `ui/tests/e2e/data-manager-external-indicators.spec.ts`.

**Done when:** fixture updates persist, repeated updates are idempotent, invalid years/provider failures remain visible, and a live COT request is documented. If all of this already passes, the remedy is tests/evidence only.

### 54 — Custom series file import — partial

**Gap:** backend errors are caught and followed by local simulated success; background execution also needs verification of staged input lifetime.

**Remedy:** make backend results authoritative, preserve date/time mappings, await format saves, and track actual jobs. Keep input files alive until workers finish.

**Exact placement:** `ui/app/plugins/data_source/Indicators/ExternalIndicatorImportDialog.tsx`: `start()`, `saveAs()`, `saveCurrent()`, `removeFormat()` await and display server outcomes; `ui/app/plugins/data_source/Indicators/externalIndicatorsStore.ts`: `useExternalIndicators.startImport()` / `.advance()` / `.action()` use `fetchExternalImportJob()` / `controlExternalImportJob()` from the existing API client. `app/workspace/data_manager/custom/http.py`: `import_custom_data()` forwards background/options correctly and uses job-owned staging; `app/workspace/data_manager/custom/feature.py`: reuse `CustomData.import_data()` / `._import_job()`; avoid enlarging this service with unrelated code.

**Done when:** backend rejection cannot create local success; split date/time fixtures import correctly; cancellation and restart preserve actual committed observations only.

### 57 — Custom series table and interactive chart — partial

**Gap:** the view is a limited table without a complete chart/pagination workflow.

**Remedy:** paginate stored observations and add a line chart using the already installed chart library. Table and chart use the same confirmed query/filter window.

**Exact placement:** `ui/app/plugins/data_source/Indicators/ExternalIndicatorViewDialog.tsx`: `ExternalIndicatorViewDialog()` plus **new internal functions** `loadPage()` and `renderSeriesChart()` with chart cleanup; `ui/app/plugins/data_source/Indicators/externalIndicatorsApiClient.ts`: extend `fetchExternalReview()` response with total/range metadata; `app/workspace/data_manager/custom/http.py`: `review_custom_data()`; `app/workspace/data_manager/custom/feature.py`: `CustomData.review_data()` returns consistent pagination totals. Extend `ui/app/plugins/data_source/Indicators/externalIndicators.css` for the existing modal.

**Done when:** more than 200 rows are reachable, multiple series can be selected, crosshair/zoom work on real observations, and stale requests cannot replace the current selection. No separate chart framework or new chart component file.

### 59 — Clone with shifted timestamps — partial

**Gap:** only local clone definitions are generated.

**Remedy:** run a real copy/transform job, publish the cloned history, and retain source/transform lineage. Fixed-hour shifts explicitly change timestamps; named-zone conversion preserves instants and changes display interpretation. These operations must not be conflated.

**Exact placement:** **new** `app/workspace/data_manager/data/transforms.py`: `clone_to_timezone()`, `shift_frame_clock()`, `register_transform_routes()` adds `POST /datasets/clone-timezone`; reuse `scan_catalog()`, `dataset_lock()` and `publish_frame()`. `ui/app/plugins/data_source/Tools/dataToolsStore.ts`: `useDataTools.startClone()` / `.advance()` / `.action()` submit/track real work using existing `cloneRemote()`; `ui/app/plugins/data_source/Tools/CloneTimezoneDialog.tsx`: `proceed()` awaits submission and removes mock wording; `ui/app/plugins/data_source/Tools/dataTools.ts`: `createCloneDefinitions()` becomes preview/name validation only.

**Done when:** stored clone rows and counts match expected shifts, original data is unchanged, timezone/DST behavior is explicit, names are unique, and cancelled/unpublished clones cannot appear completed. Add explicit clock-transform metadata so shifted labels cannot be mistaken for original UTC instants.

### 60 — CSV export of historical prices — partial

**Gap:** downloaded CSV prices come from the sample generator.

**Remedy:** export decoded stored history for the requested date/timeframe/session window, applying the existing header/token/delimiter options, and deliver an artifact only after successful writing.

**Exact placement:** **new** `app/workspace/data_manager/data/exports.py`: `DataExports.export_csv()`, `.run_export()`, `register_export_routes()` adds `POST /export` and an authenticated artifact retrieval route; reuse **new** `app/workspace/data_manager/data/review.py`: `DatasetReview.rows()` for selection semantics. `ui/app/plugins/data_source/Export/CsvExportDialog.tsx`: `CsvExportDialog.start()` calls `exportRemote()`; `ui/app/plugins/data_source/Export/dataExportStore.ts`: `.start()` / `.advance()` / `.action()` track backend jobs; `ui/app/plugins/data_source/Export/dataExport.ts`: retain format validation/rendering utilities but remove production calls to `samples()` and `csvArtifacts()` that fabricate history.

**Done when:** exported prices, row count, precision and boundaries match an independently read Parquet fixture; multi-file results have deterministic filenames; incomplete output is not downloadable as complete. Artifact cleanup is tied to job retention.

### 62 — Native MT4 FXT/HST export — missing workflow

**Gap:** the active workflow downloads a JSON manifest instead of native history files.

**Remedy:** feed stored bars into the existing HST/FXT encoders, validate requested options and header metadata, then return real binary artifacts. Explicitly reject unsupported tester models rather than claiming simulated ticks are real ticks.

**Exact placement:** **new** `app/workspace/data_manager/data/exports.py`: `DataExports.export_mt4()`; existing `app/workspace/brokers/files.py`: `encode_hst_bytes()` / `encode_fxt_bytes()` accept verified symbol/digits/server/spread fields where currently hard-coded. `ui/app/plugins/data_source/Export/Mt4ExportDialog.tsx`: `Mt4ExportDialog.start()` calls the shared export route; `ui/app/plugins/data_source/Export/dataExport.ts`: retire `mt4Manifest()` from production; `ui/app/plugins/data_source/Export/dataExportStore.ts`: artifact handling supports binary download URLs rather than only inline string content.

**Done when:** files have valid headers, lengths and records against an independent reference fixture/reader and import in a supported MT4 terminal/tester. Self round-trip through our own decoder alone is insufficient evidence of compatibility. No new codec module.

### 63 — MT5-format historical export — partial

**Gap:** CSV layout exists but values are generated samples.

**Remedy / exact placement:** **new** `app/workspace/data_manager/data/exports.py`: `DataExports.export_mt5()` emits import-compatible bar/tick CSV from canonical history with explicit spread/volume/time precision; `ui/app/plugins/data_source/Export/Mt5ExportDialog.tsx`: `Mt5ExportDialog.submit()` calls `exportRemote()`; `ui/app/plugins/data_source/Export/dataExport.ts`: remove production `mt5Artifact()` sample generation; `ui/app/plugins/data_source/Export/dataExportStore.ts`: use the same job/artifact lifecycle as 60/62.

**Done when:** exported bar/tick fixtures match the source and load into an MT5 custom symbol; real versus fixed spread restrictions are validated. This requirement is export, not automatic deployment into a running terminal.

### 64 — Review details and summary statistics — partial

**Gap:** the modal metadata is real-looking, but its detailed price rows are generated.

**Remedy / exact placement:** **new** `app/workspace/data_manager/data/review.py`: `DatasetReview.summary()` / `.rows()`; `register_review_routes()` adds `/datasets/{id}/review-data` and `/review-summary`. `ui/app/plugins/data_source/Tools/ViewAnalyzeDialog.tsx`: `ViewAnalyzeDialog()` loads actual summary/rows with loading/error/stale-request handling; `ui/app/plugins/data_source/Tools/dataToolsStore.ts`: use existing `fetchReviewRows()` and add `fetchReviewSummary()`; remove production `generateReviewRows()` calls from `ui/app/plugins/data_source/Tools/dataTools.ts`.

**Done when:** date range, count, extrema, volume and selected timeframe statistics agree with known stored fixtures and empty datasets remain empty.

### 65 — Candlestick review chart — partial

**Gap:** existing chart receives generated review data.

**Remedy / exact placement:** **new** `app/workspace/data_manager/data/review.py`: `DatasetReview.chart()` performs session-aware timeframe aggregation from actual history; `register_review_routes()` exposes the chart query. `ui/app/plugins/data_source/Tools/ViewAnalyzeDialog.tsx`: `ViewAnalyzeDialog()` shares the selected query with the chart; `ui/app/plugins/data_source/Tools/DataReviewChart.tsx`: `DataReviewChart()` keeps rendering and adds guarded loading/range updates. `app/workspace/data_manager/data/feature.py`: `Data.review_chart()` delegates to the shared review reader rather than growing a second implementation.

**Done when:** M1-to-H1/D1 OHLCV aggregation matches fixture calculations and chart/table selections agree. Tick data uses an explicitly labeled tick/line view if supported; no fabricated candlesticks.

### 66 — Raw historical bar table — partial

**Gap:** rows and edits are local/generated; remote methods target absent routes.

**Remedy / exact placement:** **new** `app/workspace/data_manager/data/review.py`: `DatasetReview.rows()`, `.index_for_date()`, `.save_changes()` and `register_review_routes()` provide the existing UI's review-data/index-for-date/save-changes contracts. `app/workspace/data_manager/data/storage.py`: **new** `replace_range()` removes deleted rows and writes edited rows through existing staged publication. `ui/app/plugins/data_source/Tools/ViewAnalyzeDialog.tsx`: `ReviewGrid()`, `save()`, `skip()` use confirmed pagination/edits; `ui/app/plugins/data_source/Tools/dataToolsStore.ts`: `fetchReviewRows()`, `saveRemoteReviewChanges()`, `getIndexForDate()` replace local review mutations.

**Done when:** later pages/date jumps work, edits/deletions survive reopening, counts/coverage update, stale saves conflict safely, and failed publication restores original history. Existing editing UI is preserved rather than silently left nonfunctional.

### 67 — Quality and gap analysis — partial

**Gap:** audit runs on sample rows and some quality routes do not exist.

**Remedy:** audit canonical history using timeframe and session/holiday expectations; report gaps, invalid OHLC, duplicate/out-of-order observations, nonfinite values and explicitly defined spike thresholds. Tick data has integrity/spread/staleness checks, not a fictitious fixed-cadence bar gap rule.

**Exact placement:** **new** `app/workspace/data_manager/data/review.py`: `DatasetReview.quality()` and private `expected_intervals()` / `classify_issues()`; `register_review_routes()` adds quality-summary/quality-details. Reuse existing `sessions` contracts and profiles. `ui/app/plugins/data_source/Tools/dataToolsStore.ts`: `fetchQualitySummary()` / `fetchQualityDetails()`; `ui/app/plugins/data_source/Tools/ViewAnalyzeDialog.tsx`: quality tab fetches paginated real issues; `ui/app/plugins/data_source/Tools/dataTools.ts`: retain presentation/types and remove production analysis of generated prices.

**Done when:** weekends, lunch pauses, holidays and DST do not create false missing-bar findings; planted errors are detected; totals cover the requested full dataset/window, not only the visible table page.

### 69 — Linked dataset selection/table/chart — partial

**Gap:** backend tab activation ignores the dataset context and returns null selection.

**Remedy / exact placement:** `app/workspace/data_manager/data/http.py`: `open_tab()` accepts the request/body, calls the shared `DatasetReview.chart()` query (which returns validated dataset metadata and real preview rows), and returns the existing typed selection/preview contract. No extra dataset-get facade or second price query implementation. `app/workspace/data_manager/data/http.py`: `datasets()` uses `request.app.state.persistence` instead of an implicit default service. `ui/app/workspace/DataManager/dataManagerWorkspaceClient.ts`: `openWorkspaceTab()` retains strict identity validation; `ui/app/workspace/DataManager/DataManager.tsx`: selection effects retain cancellation/stale-request guards; `ui/app/workspace/DataManager/DataManagerChart.tsx`: `DataManagerChart()` consumes the confirmed preview.

**Done when:** selecting a saved dataset links its own bars, switching quickly cannot show another dataset's data, deletion clears selection, and an unselected/empty dataset has an honest unavailable state.

### 70 — Live operation logs via WebSocket — partial

**Gap:** real source jobs log, but simulated import/export/tool flows do not have corresponding backend operations.

**Remedy / exact placement:** each real import/export/clone worker calls existing `app/workspace/data_manager/logs/feature.py`: `Logs.record_progress()` for all added operation kinds; reuse host WebSocket delivery from `app/host/transport.py`. `ui/app/workspace/DataManager/dataManagerLogClient.ts`: `subscribeDataLogStream()` validates the added operation events; `ui/app/workspace/DataManager/DataManager.tsx`: existing log subscription refreshes authoritative entries. `app/main.py`: construct `Logs` with the application's persistence/event dependencies where required instead of an unrelated default instance.

**Done when:** upload/import/export/clone/COT jobs emit matching IDs, progress and terminal outcomes, and reconnecting refreshes actual persisted history. Do not add another WebSocket endpoint or event bus.

### 71 — Accurate progress, errors and cancellation — partial

**Gap:** browser timers mark some operations complete independently of persisted work.

**Remedy / exact placement:** `app/workspace/data_manager/sources/download_jobs.py`: existing `manager()` / `register_download_jobs()` expose owned operation status and pause/resume/stop; submit directly with existing `JobManager.submit_job()`; workers use existing `JobContext.wait_if_paused()`, `.raise_if_cancelled()`, `.report_progress()`. `ui/app/plugins/data_source/Common/historicalSourceStore.ts`: `.trackJob()` / `.poll()` / `.action()` share actual job state. Replace timer completion in `ui/app/plugins/data_source/FileImport/fileImportStore.ts`, `ui/app/plugins/data_source/Export/dataExportStore.ts`, `ui/app/plugins/data_source/Tools/dataToolsStore.ts` and the custom-series import path. `ui/app/workspace/DataManager/DataManager.tsx`: `providerAction` and progress selection use the tracked operation ID.

**Done when:** stop reaches the worker, pause blocks the next batch, progress counts committed work, completion requires final publication, errors remain visible, and restart reconciliation never resumes a fictitious successful timer.

### 72 — Home counts and disk usage — partial

**Gap:** overview route is absent, several counters remain initialized zeros, and disk usage is not rendered.

**Remedy / exact placement:** `app/workspace/data_manager/data/feature.py`: `Data.overview()` reads actual symbols/sessions/baskets/datasets, derives active providers from configured/runtime state, and sums the canonical referenced files with path deduplication. `app/workspace/data_manager/data/_helpers.py`: **new** `catalog_storage_usage()` separates dataset bytes from filesystem capacity. `app/workspace/data_manager/data/http.py`: `register_data_routes()` adds **new** `home_overview()` at `GET /home/overview` using the request gateway. `ui/app/workspace/DataManager/DataManagerHome.tsx`: `DataManagerHome()`, `fetchOverview()` display `symbols_count`, stored bytes and available disk space with distinct labels; retain `instruments_count` only as a compatibility alias if needed. Extend existing `ui/app/workspace/DataManager/DataManagerDock.css` for these metric cards.

**Done when:** independent filesystem/SQLite counts match the endpoint and UI, shared paths are not double-counted, missing/inaccessible files are reported, and changing the selected host cannot return another gateway's totals.

### 73 — Offline fallback — partial

**Gap:** fetch errors retain memory without an explicit, persisted offline snapshot or stale indicator.

**Remedy:** retain the last successful non-secret home/catalog snapshot keyed by host/user; show when it was captured and that it is stale. Distinguish internet/provider loss from backend/host disconnection. Prevent offline mutation and never invent replacement prices.

**Exact placement:** `ui/app/workspace/DataManager/DataManagerHome.tsx`: **new internal functions** `loadCachedOverview()`, `saveCachedOverview()` and existing `fetchOverview()` / `fetchDatasets()`; `DataManagerHome()` renders offline/stale/retry state. `ui/app/workspace/DataManager/DataManager.tsx`: existing `useHostConnection()` handling supplies host state; `ui/app/plugins/data_source/Common/dataManagerStore.ts`: `syncRemoteDatasets()` preserves a validated read-only snapshot on transient failure. Extend existing CSS only.

**Done when:** reloading offline shows the last real counts/catalog with capture time, switching host/user cannot expose another snapshot, reconnection refreshes it, and mutations remain disabled without confirmation from the backend.

## Exact additional integration contracts

Routes belong to the existing `/api/v1/data` router except host connection metadata routes. Proposed nested function names in registrars are implementation locations, not separate modules.

- `app/workspace/data_manager/sources/files.py::register_file_routes()`: only `/datasets/import` and `/datasets/import-preview`. Source/format/options distinguish file, application history, TickDownloader and Darwinex inputs. All use `import_files()`; no synonymous per-source routes.
- Connections use existing `/api/v1/connections` routes in `app/host/transport.py`, adding only missing update support there. No parallel Data Manager connection API. Catalog retrieval extends existing `source_command()` at `/sources/{provider}/catalog`.
- `app/workspace/data_manager/brokers/imports.py::register_broker_import_routes()`: `/brokers/import-preview`, `/brokers/{id}/import-symbols` and `/brokers/{id}/import-sessions` (preview performs actual format normalization, not a wrapper around import).
- `app/workspace/data_manager/data/http.py::register_data_routes()`: `PUT /datasets/{id}`, `GET /home/overview`, corrected existing workspace routes. Existing `app/workspace/data_manager/sources/http.py::create_dataset()` handles general registration, including futures; no special BMF endpoint.
- `app/workspace/data_manager/data/review.py::register_review_routes()`: `/datasets/{id}/review-data`, `/review-summary`, `/review-chart`, `/index-for-date`, `/save-changes`, `/quality-summary`, `/quality-details`.
- `app/workspace/data_manager/data/exports.py::register_export_routes()`: `POST /export`; job-owned artifact download. Keep custom CSV format persistence in the existing browser store for now: requirement 61 is already met. Remove unused remote-format calls that target absent endpoints rather than building an unnecessary server registry.
- `app/workspace/data_manager/data/transforms.py::register_transform_routes()`: `POST /datasets/clone-timezone`.
- `app/workspace/data_manager/sources/download_jobs.py::register_download_jobs()`: extend existing `/download-jobs/{id}` and `/download-jobs/{id}/{action}` to the explicitly supported Data Manager operation kinds; deny unrelated job IDs. No redundant aliases.

## Retired production behavior and migration

These replacements are part of the remedies, so the application does not retain two competing implementations.

| Existing location | Planned change | Retained behavior |
|---|---|---|
| `ui/app/plugins/data_source/Export/dataExport.ts` | Remove production use of `samples()`, `csvArtifacts()`, `mt4Manifest()` and sample-driven `mt5Artifact()`. | Keep filename, format, range and option validation. Synthetic examples, if tests need them, stay in tests only. |
| `ui/app/plugins/data_source/Tools/dataTools.ts` | Remove production `generateReviewRows()` and sample-driven clone/review results. | Keep types, selection checks and naming previews. |
| `ui/app/plugins/data_source/FileImport/fileImportStore.ts`, `ui/app/plugins/data_source/Common/dataManagerStore.ts` | Replace timer-driven file/TD completion and browser-only imported counts with backend jobs/catalog. | Keep UI preferences, chosen formats and validated job IDs. Never serialize browser `File` objects into localStorage. |
| `ui/app/plugins/data_source/Tools/dataToolsStore.ts`, `ui/app/plugins/data_source/Export/dataExportStore.ts`, `ui/app/plugins/data_source/Indicators/externalIndicatorsStore.ts` | Replace local completion timers and fake result persistence with confirmed server outcomes. | Keep useful option/history presentation, with job-owned results. |
| `ui/app/plugins/data_source/Indicators/ExternalIndicatorImportDialog.tsx` | Remove catch-and-continue behavior after backend rejection. | Preserve the selected file/draft for retry. |
| `ui/app/workspace/DataManager/DataManager.tsx` | Remove interval effects for retired simulations once the corresponding real job path is connected. | Keep polling/subscriptions for real operations and unrelated working source flows. |

Legacy browser records are not silently inserted into SQLite as if they were real history. Preserve them as recoverable local drafts when possible, distinguish them from authoritative saved datasets, and require the original file for re-import. Existing real data and jobs retain their identities.

## Database, storage and compatibility decisions

1. Existing tables remain authoritative: `datamgr_symbols`, `datamgr_sessions`, `datamgr_broker`, `datamgr_datasets`, `host_entities`, custom-series tables and host jobs/logs. No duplicate instruments, connections or operation tables.
2. Dataset `symbol_definition_id` and `session_id` are nullable additive links. Preserve legacy records and retain unresolved legacy labels until an explicit user selection resolves them. Do not silently assign a default profile to ambiguous records.
3. Broker cost JSON columns have explicit inherited defaults. Existing cost objects and per-symbol overrides remain compatible.
4. Use `lineage_json` for source application, imported filenames, BMF exchange/expiry, source dataset and transform options. It is provenance, not a substitute for typed relational links.
5. All uploaded content and export artifacts have a job-owned staging/retention lifecycle. An asynchronous worker must never depend on a request-scoped temporary directory already deleted by the response.
6. Existing `publish_frame()` handles encoding, deduplication, coverage and staging. Review deletions use the same publication protocol through `replace_range()`; timezone clone output uses a distinct dataset-owned directory.
7. File names, timestamps, formats and requested ranges are bounded/validated before enqueueing; archive extraction does not write outside staging. Large files use bounded batches rather than browser-local price arrays or one giant JSON body.
8. Historical query semantics are shared across review/export/quality. A chart aggregation cannot silently differ from the exported session/timeframe query.

## Tests: exact placement and purpose

The proposed maximum is **8 new test files**, with existing tests extended where they already own the behavior. Do not create a test file for each checklist item.

| File | New or existing | Exact test functions / verification scope |
|---|---|---|
| `tests/host/test_vault.py` | New | `test_secret_rotation_preserves_prior_reference_on_save_failure()`, `test_vault_values_never_enter_public_metadata()`; OS boundary mocked for routine CI. |
| `tests/workspace/data_manager/test_connections.py` | New | `test_provider_access_distinguishes_authentication_and_entitlement()`, `test_provider_credentials_are_used_for_download()`, `test_connection_update_keeps_owned_references()`. |
| `tests/workspace/data_manager/test_file_imports.py` | New | `test_uploaded_prices_publish_exact_canonical_rows()`, `test_mass_import_reports_committed_files()`, `test_application_and_provider_archives_use_shared_ingestion()`, `test_import_cancel_cleans_staging_and_retains_commits()`. |
| `tests/workspace/data_manager/test_broker_imports.py` | New | `test_json_xml_import_share_validation()`, `test_import_conflicts_return_confirmed_identities()`, `test_profile_costs_preserve_symbol_overrides()`. |
| `tests/workspace/data_manager/test_data_review.py` | New | `test_review_reads_canonical_prices()`, `test_aggregation_matches_known_ohlcv()`, `test_session_aware_quality_excludes_closed_intervals()`, `test_review_edits_rollback_on_publication_failure()`. |
| `tests/workspace/data_manager/test_data_exports.py` | New | `test_csv_export_matches_source_window()`, `test_mt4_artifacts_match_independent_binary_fixture()`, `test_mt5_export_preserves_spread_and_volume()`, `test_incomplete_artifacts_are_not_downloadable()`. |
| `tests/workspace/data_manager/test_data_transforms.py` | New | `test_fixed_shift_publishes_copy_without_mutating_source()`, `test_named_zone_preserves_instants_across_dst()`, `test_cancelled_clone_never_reports_completion()`. |
| `ui/tests/unit/plugins/data_source/Common/ProviderConnectionsDialog.test.tsx` | New | `it('saves and tests the selected provider connection')`, `it('does not persist returned secrets')`, `it('shows denied or unknown entitlement accurately')`. |
| `tests/host/test_transport.py`, `tests/host/test_persistance.py`, `tests/host/test_main.py` | Existing | Extend connection PUT, additive migrations, dependency injection and shutdown/recovery cases. |
| `tests/workspace/data_manager/test_data.py`, `tests/workspace/data_manager/test_sources.py`, `tests/workspace/data_manager/test_brokers.py`, `tests/workspace/data_manager/test_custom_http.py`, `tests/workspace/data_manager/test_custom.py`, `tests/workspace/data_manager/test_logs.py`, `tests/workspace/data_manager/test_download_jobs.py` | Existing | Dataset links/BMF, home counts/workspace context, costs, COT, custom import failures, shared operation events/controls. |
| `tests/workspace/brokers/test_codecs.py` | Existing | Add independent HST/FXT header/record checks only where encoder changes are needed; don't replace existing SQ codec cases. |
| `ui/tests/unit/plugins/data_source/Export/dataExport.test.ts`, `ui/tests/unit/plugins/data_source/Tools/dataTools.test.ts`, `ui/tests/unit/plugins/data_source/historicalSourceStore.test.ts`, `ui/tests/unit/plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient.test.ts`, `ui/tests/unit/plugins/data_source/Indicators/externalIndicatorsApiClient.test.ts` | Existing | Replace assertions that accept fabricated completion/output with confirmed contract tests; retain utility-format validation tests. |
| `ui/tests/e2e/data-manager-file-import.spec.ts`, `ui/tests/e2e/data-manager-tickdownloader.spec.ts`, `ui/tests/e2e/data-manager-darwinex.spec.ts`, `ui/tests/e2e/data-manager-broker-profiles.spec.ts`, `ui/tests/e2e/data-manager-export.spec.ts`, `ui/tests/e2e/data-manager-tools.spec.ts`, `ui/tests/e2e/data-manager-external-indicators.spec.ts`, `ui/tests/e2e/data-manager-workspace.spec.ts`, `ui/tests/e2e/data-manager-log.spec.ts`, `ui/tests/e2e/home-landing.spec.ts` | Existing | Exercise real test-host routes and fixture-backed history; mock only external services/terminals. Verify reload persistence, cancellation, linked charts, offline/reconnect and provider conditions. |

Routine validation after each coherent change: focused tests, Python lint/type checks appropriate to changed files, frontend typecheck, and relevant existing browser tests. Final gate reruns the Data Manager/broker suite and Data Manager frontend suite. Live provider and terminal checks remain explicitly separate and require available credentials/installations; a skipped live check is not marked passed.

## Dependency order and review batches

| Batch | Requirements | Result to review before the next batch |
|---|---|---|
| 1. Shared contracts and catalog links | 21, 69, 72; common parts of 70–71 | Additive schema, real home metrics, corrected workspace selection, documented job contract. |
| 2. Connection lifecycle and provider access | 09, 10, 11, 40, 43, 46, 49 | One connection dialog, actual credential use/testing/catalog, provider conditions wired. |
| 3. Broker defaults/imports | 13, 15, 16 | Persistent costs and working JSON/XML import contracts. |
| 4. Local/application/provider-file ingestion | 23, 24, 25, 26, 28, 38, 42 | Actual files reach canonical storage, BMF registration, honest jobs/cancellation. |
| 5. Verify MT5 history | 44; MT5 part of 26 | End-to-end evidence for the existing terminal integration; fixes only for observed behavioral failures. |
| 6. Real review, edits and quality | 64, 65, 66, 67 | Canonical rows, consistent chart/table queries, safe mutations and session-aware audit. |
| 7. Clone and exports | 59, 60, 62, 63 | Persisted transforms and real CSV/MT4/MT5 artifacts. |
| 8. Custom series, offline state, final operation coverage | 53, 54, 57, 70, 71, 73 | Confirmed COT/custom imports, chart/pagination, complete logs/controls and offline snapshots. |

Logging/progress integration is implemented alongside each new operation, not delayed until batch 8. Batch 8 verifies the complete matrix.

## Explicit scope decisions for review before implementation

These are proposed boundaries, not hidden assumptions or requests to start coding.

- **External applications (26):** initial support is MT4 local history and MT5 terminal history using its existing integration. The original requirement names no other applications. Specific NinjaTrader/AmiBroker/etc. formats require examples and an added adapter entry in this plan; they are not covered by claiming support for arbitrary applications.
- **XML imports (15–16):** versioned HaruQuantAI symbol/session XML matching the JSON domain schema. Vendor-specific XML is added only against a named schema/sample; no best-effort silent interpretation.
- **BMF (23):** BMF/B3 futures registration plus normal file/terminal ingestion, not a new paid exchange feed or automatic continuous-futures rolling.
- **MT5 history (44):** verify the existing integration. The historical API label is not a transport mandate; no second adapter is planned.
- **MT4 (62):** HST v400/v401 and FXT v405 are the existing supported codec targets. Exact terminal/tester compatibility must be demonstrated; unsupported tester modes remain visibly unavailable.
- **Offline (73):** last-known non-secret dashboard/catalog state, read-only. Offline price editing, background offline downloads and browser copies of the entire price database are outside the requirement.
- **Commission defaults (13):** persist and resolve existing model shapes; no new commission model language or backtesting execution engine in this change.

## Completion and change control

All 35 gap IDs must retain an entry in this plan and the coverage report. Mark an item complete only after its acceptance checks pass against persistent data, not because a dialog or route exists. A requirement that only needed verification should close with evidence and no redundant implementation.

Removing unnecessary proposed functions/files is encouraged; record their existing-code replacement in this plan. Before adding runtime dependencies, creating source/test files beyond this inventory, or broadening a format/provider scope, update this plan with the exact file, symbol, missing behavior, reason and verification. This keeps the reviewed implementation surface explicit.

## Implemented locations and scope reconciliation

The detailed sections above preserve the approved design rationale. The following are the actual new runtime owners; these names implement missing work and were not copied from historical names:

| File | Actual implementation |
|---|---|
| `app/host/vault.py` | `WindowsCredentialVault.store/resolve/revoke`: OS-owned secret storage. Existing `ServletConnection.save_connection` now creates/updates and rotates references through this vault. |
| `app/workspace/data_manager/sources/connections.py` | `test_provider_access`, `build_provider_testers`: endpoint outcomes and actual bounded history access, with unknown subscription states. |
| `app/workspace/data_manager/sources/files.py` | `preview_import`, `import_files`: shared file parsing and batch publication; actual HTTP request handlers stage uploaded bytes and register jobs. |
| `app/workspace/data_manager/brokers/imports.py` | `parse_broker_records`, `import_broker_records`: versioned format interpretation and transactional record import using existing validators. |
| `app/workspace/data_manager/data/review.py` | `DatasetReview.frame/calendar/rows/summary/quality/save_changes`: actual queries, saved-session semantics and revision-checked mutations. |
| `app/workspace/data_manager/data/exports.py` | `DataExports.export_csv/export_mt4/export_mt5/run_export`: actual formats, job-owned artifacts and direct calls to existing MT4 encoders. |
| `app/workspace/data_manager/data/transforms.py` | `clone_to_timezone`: actual copied prices, explicit clock transform and lineage publication. |
| `ui/app/plugins/data_source/Common/ProviderConnectionsDialog.tsx` | `ProviderConnectionsDialog`: the one host connection editor. |

Existing owners handle the remaining work: `Data.edit/overview/clear/delete` in `data/feature.py`; catalog validation in `data/_helpers.py`; atomic publishing in `data/storage.py`; connection selection in `sources/http.py` and `_base.py`; shared jobs/restart reconciliation in `sources/download_jobs.py`; custom parsing/jobs in `custom`; existing frontend dialogs/stores now submit real work. Dataset properties stay in the existing `DataManagerPanels.tsx`.

Requirement 22 was rechecked during implementation: catalog retirement alone did not release cache files. `Data._remove_cached_files` now removes retired owned manifest files only when unreferenced; clear/delete integration tests cover that behavior. No recursive deletion or new cleanup module was introduced.

Verification: 428 backend tests, TypeScript check, 642 frontend tests, 13 browser checks and a real disposable OS-vault round trip passed. See the coverage report for exact evidence and remaining external acceptance. Eight runtime files and eight test files were added; no dependency additions or duplicate codecs/transports.

Current operational bounds: 25 MB uploaded bytes per request; native review pagination stays lazy. Resampling/session filters/edits/clone/export materialize the selected history. MT5 fixed spreads use points; pip conversion is not silently guessed. MT4 output uses supported bar timeframes and existing codec versions, with terminal acceptance still pending.

Commit-hook architecture correction: credential metadata, the vault protocol and `prepare_credentials` reside in the existing `app/host/vault.py`; `ServletConnection` retains connection persistence and diagnostics. This keeps `transport.py` below the enforced 1,000-line ceiling without adding another file.

## Market-data module consolidation

User-approved refactor: reusable market-data requests now live in `app/workspace/data_manager/data/history.py`; record conversion lives in `conversions.py`. `resolve_history_request` replaces the cross-module private `_route` name. CLI formatting moved from `_helpers.py` into existing `_cli.py`.

`app/include/data.py` is removed. All broker, application, example and test callers import their owning modules directly. The unused, inaccurate `DataBackend.call` protocol and unused `bars_to_df`/`ticks_to_df` aliases were removed. There are no old-path shims or legacy re-exports. The data package initializer is documentation-only, and workspace feature registration imports are deferred to router/CLI assembly.

Record columns, timestamps, dtype behavior, validation and backend execution semantics are preserved. Fresh-process tests verify that conversion/history imports do not initialize source packages, dataset services, host transport or FastAPI. Two runtime modules and one focused test module replace the old combined runtime module.
