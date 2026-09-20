# File import workflow coverage

Reference root: `C:/SQX_144_2953_win_20260601/internal/`. Product: SQX Data Manager,
DataSourceFiles plugin. HaruQuantAI inherits its existing font, colors, dark/light theme,
modal frame and responsive scrolling. Source/controller behavior is distinguished from
backend behavior inferred for the mock. Overall Data Manager remains Partial.

## FILE-IMPORT-001 — Single-file import
- Screen/entry: File import > Import one data file; `Data import for 'SYMBOL'`.
- Sources: plugins/DataSourceFiles/import/{module.js,importPopup.html,DataSourceFilesImportCtrl.js};
  DataSourceFilesService.js; SQMANAGER/timezones.csv.
- Registration/product: DataSourceFiles import plugin, priority 10,
  `datamanager-datasource-files-import`, SQX Data Manager.
- Controls: Browse/read-only filename, timezone, timeframe (auto/Intraday/list), format,
  Save/Save as/Delete, skip rows/columns, separator, date pattern/example, error radios,
  205px preview with per-column mappings, Close/Start Import.
- Preconditions: first selected eligible File import dataset; no clone, no active data job.
  Wrong/missing selection gives shared-bar feedback. File objects remain transient.
- Validation: supported UTF-8 file, bounded size/rows/columns; nonnegative integer skips;
  all columns assigned, unique semantic types, date plus OHLC or bid/ask; strict calendar,
  numeric prices/volume and consistent high/low or bid/ask; supported timeframe.
- Transitions: choose -> detect -> preview -> edit -> queue; Close/Escape discard draft;
  malformed content either fails the task or is counted/skipped per error option;
  zero valid records never produces a successful import.
- Outcome: parsed timestamp summaries update only the actual target, row counts/date range,
  timeframe and timezone; no provider request, upload or native source-file write.
- Mock operations: readImportFile/detectFormat/previewRows/parseImport/importedRecord and
  useFileImports.start, corresponding to importGetInfo/importGetOverview/import.
- Persistence: custom formats, last timezone, results and normalized pending tasks in
  sqx-file-import-v1. No absolute file paths, raw CSV or price arrays persisted.
- Implementation: visual / interaction / state all implemented within mock boundary.
- Verification: fileImport.test.ts and single-file/custom-mapping/error/recovery browser
  cases; dark desktop and narrow light screenshots reviewed. Live app refreshed.
- Gaps/assumptions: backend format catalogue/date constants are compiled/unavailable;
  three explicitly named common mock presets, common timeframe/date options and heuristic
  detection are not claimed as exact backend results. Full installed timezone labels/IDs
  copied, plus app UTC alias; no timezone conversion. Donor source filters selection and
  then accidentally replaces it, and paints multiple rows for one target; those defects
  are not reproduced. Clone selection is structurally guarded but no clone UI is included.

## FILE-IMPORT-002 — Saved data formats
- Screen/entry: single-file Save/Save as/Delete -> New data format or delete confirmation.
- Sources: import/newFormatPopup.html and DataSourceFilesImportCtrl.js format callbacks;
  DataSourceFilesService.js importSaveNewDataFormat/importUpdateDataFormat/importDeleteDataFormat.
- Controls: Name, Close, Save; delete confirmation; predefined actions disabled.
- Preconditions: complete valid mapping. Validation: nonempty unique name <=80 chars,
  protected predefined/Custom names, <=100 custom formats; successful storage write.
- Transitions: save custom -> persist/update; Save as -> name dialog -> save -> return;
  delete -> confirm -> Custom; cancel/Escape -> unchanged parent configuration.
- Outcome: reusable separator/skips/date/mappings; protected presets cannot be deleted.
- Mock operations: useFileImports.saveFormat/deleteFormat.
- Persistence: sqx-file-import-v1.formats. Storage failure keeps the dialog and old data.
- Implementation: visual / interaction / state implemented.
- Verification: format creation/update/delete/cancel/protection/reload exercised by unit
  and browser scenarios. Keyboard Tab stays in active single-file dialog.
- Gap: source name policy is server-owned; bounded unique names are mock validation.

## FILE-MASS-001 — Folder/Mass import
- Screen/entry: File import > Import multiple files from a folder -> Mass import.
- Sources: massImport/{module.js,massImportPopup.html,DataSourceFilesMassImportCtrl.js},
  DataSourceFilesService.js; source ID datamanager-datasource-files-mass-import.
- Controls: folder Select, timezone, timeframe D1 default, date pattern ddMMyyyy default,
  stockgroup checkbox, fixed CSV layout, overwrite/skip/numbered-copy radios, timestamp
  convention, postfix; existing full chooser/broker filter/details/Add instrument/help;
  Close/Save. Postfix appears alongside timestamp settings.
- Preconditions: browser folder selection, valid instrument and no active provider job.
- Validation: UTF-8 CSV/TSV/text extensions, fixed comma-separated values without header;
  OHLCV or tick Date/Ask/Bid/Volume; folder/file bounds, source symbol pattern, postfix,
  duplicate filename stems; overwrite limited to File import records; readable storage.
- Transitions: choose -> configure -> parse in stable relative-path order -> queue;
  skip existing -> leave untouched; create -> next numeric suffix; overwrite -> replace
  target summary using chosen instrument/bar convention; Close cancels pending read.
- Outcome: actual parsed counts/ranges in new or existing file records; optionally named
  stock group populated only by completed imports and usable in Data sources filter.
- Mock operations: massSymbol/emptyFileRecord/parseImport/useFileImports.start; counterpart
  /dataSourceFiles/massImport. Shared FileSymbolDialog composes folder settings while
  retaining its independently saved instrument editor and source explanation.
- Persistence: results/groups/tasks in sqx-file-import-v1; instruments in existing
  sqx-file-symbols-v1. Browser folder FileList must be reselected for a new import.
- Implementation: visual / interaction / state implemented.
- Verification: folder fixture browser scenario covers validation, instrument/help,
  postfix, group/table filter, overwrite/skip/numbered copy, reload and unchanged source
  bytes. Rule tests cover provider collision and deterministic names. Dark live popup reviewed.
- Gaps: recursion uses browser relative paths; empty directories unavailable. Native group
  naming unavailable, so folder label with collision-safe numeric suffix is used. All skipped
  produces actionable feedback instead of an empty job. Ambiguous same stems require create.

## FILE-IMPORT-003 — Shared progress, result persistence and limits
- Screen/entry: Start Import or Mass import Save -> existing shared progress bar and trailing
  unlabeled status column after Hide. Sources: source importAction and massImport callbacks.
- Controls: shared Pause all / Resume all / Stop all. No duplicate progress panel.
- Preconditions: one active operation across generic data jobs, Dukascopy, TickDownloader,
  file import. Pending names reserved against provider/add-symbol collisions.
- Validation: complete persisted shape, identities, states, timestamp ordering, group bounds,
  quota write before UI success; unreadable storage preserved and blocks writes.
- Transitions: running/paused/resumed/cancelled/failed/completed; reload running -> paused.
  Each completed file commits atomically. Stop discards unfinished new rows; completed files
  and group members remain. Failure identifies file/row and leaves that target unchanged.
- Outcome: completed counts/date ranges/status; completion summary counts files skipped and
  invalid rows ignored. Old completed records retain Completed status after later jobs.
- Mock operations: useFileImports.advance/action, provider operation guards.
- Persistence: job plans store normalized timestamps and target metadata, enough to resume
  without file access. LocalStorage quota failure leaves previous saved snapshot unchanged;
  failed in-memory job exposes error (reload recovers last successfully persisted state).
- Implementation: visual / interaction / state implemented; no real ingestion backend.
- Verification: 10 file-import unit cases cover parser and atomic/cancel/fail/reload/quota
  lifecycle; browser provider regressions and new import scenarios validate shared controls.
- Limits: 10 MiB/file, 50 MiB/folder, 500 files, 100k data rows/file, 100 columns,
  50 preview rows, 200k tracked timestamps total, 100 formats, 1000 groups, 10000 records.
  Bounds fail explicitly; file content is never silently truncated for imported counts.
- Merge assumption: timestamps are unique record keys, including ticks (same-timestamp ticks
  collapse in this mock). Reimport deduplicates known keys. Unknown seeded history remains an
  opaque count/range and is not claimed to have deduplicated overlap. Mass overwrite replaces
  that coverage. Validated prices are not stored; no chart-ready price series is claimed.

## Inclusion / exclusion register
| ID | Decision | Reason / evidence |
| --- | --- | --- |
| FILE-IMPORT-001/002/003 | Include | Reachable single-file, formats and lifecycle |
| FILE-MASS-001 | Include | Reachable folder workflow including stockgroup outcome |
| FILE-INSTRUMENT-001 | Reuse | Previously audited chooser/add/details/commissions/swap/help |
| FILE-APP-EXCLUDED | Remove | Owner explicitly excluded SQX application-data migration; menu, union, icon and placeholder route removed |
| FILE-NATIVE-EXCLUDED | Exclude | Native filesystem service, binary formats, Java ingestion, real DST conversion and provider access absent from mock scope |
| FILE-CANCEL-GAP | Mock adaptation | Donor calls missing importCancel/cancelMassImport methods; coherent local lifecycle supplied |
| FILE-GROUP-CRUD | Exclude | General manual stockgroup management is unrelated; imported groups are visible/filterable |

No screen is counted complete merely for having a route. Backend interoperability and native
runtime pixel parity remain unverified. This register describes the included frontend mock.
