# MT5 import coverage and evidence

Task `FEAT-UI-DATA-MT5-IMPORT`; approved plan:
`docs/mt5-import-implementation-plan.md`. Reference installation:
`C:/SQX_144_2953_win_20260601`.

## Source and registration trace

`DataSourceMt5Api/module.js` registers `MT5 import` for Quant Data Manager.
`import/module.js` registers its single `Import data` command and opens
`Import data from MT5`. `importPopup.html` contains the active folder,
Fetch symbols, filter, Show types, grouped Symbol/Name table, Download range,
Data Availability Disclaimer, broker, postfix, Close and Start import controls.
Its installed/portable and Tick/M1 radio sections are commented out in this build.

`DataSourceMt5ApiImportCtrl.js` supplies the one-year initial range, active
Since last date preset, symbol grouping and selection, filter/category reloads,
eligible broker profiles, broker postfix, request construction and job actions.
`DataSourceMt5Api.js` names the symbol-loading and import calls. Read-only
`jar tf`/`javap` inspection of `DataSourceMt5Api.jar` confirms portable
source, M1 creation, path/name sorting, broker metadata, duplicate-name numbering,
date bounds and pause/continue/stop dispatch. The donor frontend uses
`importDataAction` while the compiled servlet dispatch table names
`downloadDataAction`; this unresolved donor mismatch is not reproduced.

The ribbon uses an exact local copy of `internal/web/img/metatrader5.png`.
Source and copied asset SHA256 are
`1FDE3A7DFA6841406D3290784FA1A6623D267D0E16A605BE594B75C1EF0C1AC0`.

## Inclusion and exclusion register

Included: the exact icon and command/title, all active popup controls, bounded
folder metadata validation, explicit Fetch symbols, deterministic categorized
fixtures, source path/name ordering, search and category filters, group/header/
row selection, M1 definitions, six date presets, broker/postfix behavior,
automatic duplicate numbering, synthetic coverage, shared progress controls,
partial sequential commits, pause/resume/stop/fail/complete states, reload as
paused, trailing status, provider-wide collision and operation guards, themes,
responsive layout, focus handling, storage failures and versioned persistence.

Excluded: the commented source/timeframe controls, native MT5 process and API
access, terminal database/HCC decoding, live broker inventory, real prices,
credentials, backend calls, native folder-handle persistence and MT5 export.
The 12-symbol catalogue and one synthetic sample per calendar day are bounded
mock metadata. Selecting a folder exposes path metadata only; file contents are
not read, MetaTrader is not started and no provider request is sent.

## Feature register

### MT5-IMPORT-001

- **product/screen**: SQX Data Manager / Import data from MT5
- **sources**: DataSourceMt5Api provider/import modules, popup template,
  controller, service, styles, compiled jar, shared date range and
  `internal/web/img/metatrader5.png`
- **trigger/controls**: MT5 import > Import data; folder/Select, Fetch symbols,
  search, Show types, grouped checkbox grid, From/To and six presets,
  disclaimer/link, broker, postfix, Close and Start import
- **preconditions/validation**: session-selected MT5-like folder metadata,
  fetched selection, valid ordered dates through today and mock availability,
  eligible broker, bounded postfix/selection, readable and writable storage,
  no active provider operation
- **transitions/outcome**: select, fetch, filter/group/select, configure, start,
  running, pause, resume, stop, fail, complete and reload; persistent M1 records
  receive synthetic coverage and shared progress/trailing status
- **mock operation/persistence**: `discoverMt5Folder`,
  `filterMt5Symbols`, `mt5Definitions`, `mt5ImportRanges`,
  `useMt5Import.start/advance/action`; `sqx-mt5-import-v1`
- **status**: visual implemented; interaction implemented; state implemented
- **verification/gaps**: focused domain/store and browser lifecycle tests,
  source-ribbon regression, exact icon hash and production build; bounded
  offline catalogue, no terminal execution, price decoding or live broker data

## Verification

Focused and full regression results are recorded in
`docs/mt5-import-walkthrough.md`. Overall Data Manager coverage remains
Partial while backend and native provider integration are absent.
