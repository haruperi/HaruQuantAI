# Darwinex coverage and evidence

Task FEAT-UI-DARWINEX; approved plan: docs/darwinex-implementation-plan.md.
Reference installation: `C:/SQX_144_2953_win_20260601`.

## Source and registration trace
Provider priority 10; actions add/import/download priorities 0/10/20; source data.
SQMANAGER LayoutCtrl registers Darwinex outside the SQX-only Equity/Futures conditional.
Add dynamically includes the instrument mapping template and refreshes mtUse brokers on open.
Filter refresh clears selections. LICENSE_CHANGED is observed by add/download controllers.
The free-data consent directive supplies the visible provider-specific confirmation text.
DateRange directive implements six presets; sinceLast uses individual stored target coverage.

The installed CSV was copied unchanged to data/market/darwinex/darwinex.csv: 328 eight-field rows.
SHA256: 6ABEAE36E8A0921056159B68CBA5A83E6313E8A82B91E99B59CBFA47D42CE42F.
Two dates have single-digit month components; parser accepts d.M.yyyy and dd.MM.yyyy.
Read-only javap bytecode confirms DarwinexDataManager's catalogue path, TICK creation and
DarwinexServlet's direct child/root folder log.gz discovery. No donor code was executed or modified.

Service contracts: downloadGetDataList returns data.data; downloadAddData posts postfix/symbols/
broker/instruments; importLoadAvailableSymbols accepts path and returns symbols; importData posts
path/comma-separated symbols/postfix; downloadData posts dateFrom/dateTo/dateType/overwrite plus
symbols/darwinexSymbols/datesTo/uSymbols. importDataCancel/importDataAction/downloadDataAction map
to local job controls. Normalized frontend target IDs replace fragile parallel comma lists.
The mock store serializes definitions, requests, committed intervals and progress, but never file bytes.

## Inclusion and exclusion register
Included: all three current dropdown actions, conditional broker mapping, consent, selection,
validation, presets, both redownload modes, available/restricted download template, persistent mock
jobs, cross-provider reservations, theme/focus behavior and trailing row status.
Excluded: actual provider traffic/credentials/purchases, native filesystem access and compressed
price decoding (frontend-only), unrelated broker-profile authoring, generated duplicate screens.
Separate disclaimer uses DataSourceDarwinexNotUsed and a Dukascopy action ID, so no fourth menu item
was added. Active free-data consent remains. Unused import progress callback is not a separate UI.
Corrected source defects: mapping's stray DukascopyService reference and download's mixed-source filter.
Approved mock difference: Full/Starter exposes both license template states; no real licensing claim.

## Feature register

### DARWINEX-ADD-001

- **product**: SQX / Data Manager / DataSourceDarwinex
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **persistence**: sqx-darwinex-v1 definitions, job, ranges, folder display name and postfix; reload running as paused; raw files not stored
- **screen**: Add Darwinex data
- **sources**: ["internal/plugins/DataSourceDarwinex/module.js", "internal/plugins/DataSourceDarwinex/add/module.js", "internal/plugins/DataSourceDarwinex/add/addPopup.html", "internal/plugins/DataSourceDarwinex/add/addPopupCtrl.js", "internal/plugins/DataSourceDarwinex/add/styles.css", "internal/plugins/DataSourceDarwinex/DarwinexService.js", "internal/plugins/DataSourceDarwinex/darwinex.csv", "internal/web/app/directives/freeDataDisclaimer/freeDataDisclaimer.html"]
- **trigger**: Darwinex Tick Data > Add Darwinex data
- **controls**: ["328-row symbol catalogue", "symbol filter", "row/header checkboxes", "symbol/range sorting", "broker", "postfix", "free-data consent", "Save", "Close"]
- **preconditions**: ["readable catalogue/storage", "no active provider job"]
- **validation**: ["selection", "consent", "valid broker and mappings", "unique valid global names", "bounded selections/postfix", "successful storage write"]
- **transitions**: ["open resets selection/consent", "filter clears selection", "broker applies postfix/notice", "mapping if non-default", "queue", "pause/resume/stop/fail/complete", "reload"]
- **outcome**: empty TICK definitions added atomically; availability dates are not downloaded coverage
- **mockOperation**: parseDarwinex/darwinexDefinitions/useDarwinex.start(add)
- **verification**: {"visual": "dark desktop and light narrow screenshots inspected", "interaction": "catalogue/consent/filter/mapping browser tests passed", "state": "atomic commit/reload/storage unit and browser tests passed"}
- **gaps**: Native runtime not observed. Raw numeric catalogue fields retained without unverified financial interpretation; category is Tick data. Broker preference resets to default on reopen; persisted definitions retain selected broker.

### DARWINEX-MAPPING-001

- **product**: SQX / Data Manager / DataSourceDarwinex
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **persistence**: sqx-darwinex-v1 definitions, job, ranges, folder display name and postfix; reload running as paused; raw files not stored
- **screen**: Add Darwinex data - identify instruments
- **sources**: ["internal/plugins/DataSourceDarwinex/add/selectInstrumentsPopup.html", "internal/plugins/DataSourceDarwinex/add/addPopupCtrl.js"]
- **trigger**: Save with non-default mtUse broker
- **controls**: ["broker explanation", "per-symbol matching instrument/default/skip", "mass default", "mass skip", "Back", "Save"]
- **preconditions**: ["selected catalogue symbols", "consent", "configured mtUse broker"]
- **validation**: ["all mappings resolved", "at least one not skipped", "selected mapping belongs to broker", "unique names"]
- **transitions**: ["prefix auto-match or unresolved", "mass action only unresolved", "Back retains parent selection", "save configured definitions"]
- **outcome**: correct instrument and broker timezone stored per included symbol
- **mockOperation**: darwinexDefinitions with broker and mappings
- **verification**: {"visual": "source layout implemented in themed modal", "interaction": "unresolved/skip/default/Back browser scenario passed", "state": "mapping and name rules tested offline"}
- **gaps**: Default mock has no configured brokers; tests seed isolated fixture. Stray donor DukascopyService call/label intentionally corrected to Darwinex.

### DARWINEX-IMPORT-001

- **product**: SQX / Data Manager / DataSourceDarwinex
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **persistence**: sqx-darwinex-v1 definitions, job, ranges, folder display name and postfix; reload running as paused; raw files not stored
- **screen**: Import data from Darwinex
- **sources**: ["internal/plugins/DataSourceDarwinex/import/module.js", "internal/plugins/DataSourceDarwinex/import/importPopup.html", "internal/plugins/DataSourceDarwinex/import/importPopupCtrl.js", "internal/plugins/DataSourceDarwinex/DarwinexService.js", "internal/plugins/DataSourceDarwinex/style.css", "internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar:DarwinexServlet.onImportLoadAvailableSymbols"]
- **trigger**: Darwinex Tick Data > Import data from a Darwinex folder
- **controls**: ["readonly folder", "Select browser directory", "300px checkbox Symbol grid", "postfix", "Close", "Start import"]
- **preconditions**: ["session-selected folder metadata", "no conflicting job"]
- **validation**: ["one folder", "safe relative paths", "at most 20000 files/1000 symbols", "direct log.gz discovery", "selection", "global duplicate names", "storage"]
- **transitions**: ["select folder", "discover direct child symbol folders or known root symbol", "choose symbols", "queue", "pause/resume/stop/fail/complete", "reload requires folder reselect"]
- **outcome**: mock imported definitions with zero decoded ticks; source files unchanged
- **mockOperation**: discoverDarwinex/useDarwinex.start(import)
- **verification**: {"visual": "running-app import screenshot reviewed", "interaction": "folder selection, duplicates, stop, retry and remembered folder browser scenario passed", "state": "direct/root/deep/case-sensitive discovery unit checks and persistence tests passed"}
- **gaps**: Browser cannot expose empty folders or restore native file access; metadata only, no native gzip tick decoding. Compiled discovery was verified with javap; backend import decoding remains excluded.

### DARWINEX-DOWNLOAD-001

- **product**: SQX / Data Manager / DataSourceDarwinex
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **persistence**: sqx-darwinex-v1 definitions, job, ranges, folder display name and postfix; reload running as paused; raw files not stored
- **screen**: Download Darwinex data for symbol/multiple
- **sources**: ["internal/plugins/DataSourceDarwinex/download/module.js", "internal/plugins/DataSourceDarwinex/download/downloadPopup.html", "internal/plugins/DataSourceDarwinex/download/downloadPopupCtrl.js", "internal/plugins/DataSourceDarwinex/DarwinexService.js", "internal/web/app/directives/dateRange/DateRangeCtrl.js", "internal/web/app/directives/dateRange/dateRange.html"]
- **trigger**: Darwinex Tick Data > Download data for existing symbols
- **controls**: ["From/To", "six date presets", "missing/overwrite radios", "Close", "Start download", "restricted license message/upgrade link"]
- **preconditions**: ["selected Darwinex records", "no clones", "no active job", "Full mock profile to start"]
- **validation**: ["valid ordered dates through today", "per-target availability and last date", "known target IDs", "storage"]
- **transitions**: ["select eligible rows", "configure dates/policy", "start", "pause/resume/stop/fail/complete", "reload paused", "profile changes affect available controls"]
- **outcome**: synthetic intervals update only selected Darwinex records; one shared progress bar and trailing statuses
- **mockOperation**: darwinexTargets/darwinexDownloadRanges/useDarwinex.download,advance,action
- **verification**: {"visual": "download dark screenshot reviewed; responsive styles share frame", "interaction": "mixed-selection isolation, all six presets, invalid dates, overwrite and restricted profile browser scenario passed", "state": "per-target sinceLast, clone rejection, missing/overwrite deduplication and reload unit tests passed"}
- **gaps**: Full/Starter is approved mock entitlement mapping: donor forces fullLicense=true on event despite restricted template. Source mixed-provider filtering bug corrected. One synthetic sample per calendar day, not actual ticks; unknown catalogue availability falls back to existing start or today.

## Verification

37 affected unit tests and 33 browser scenarios passed, including six Darwinex unit tests and five
Darwinex browser scenarios. Production build passed. Python CI: lint/format/type/architecture passed;
101 tests passed, eight startup tests failed on the pre-existing data/logs/.logging.lock; coverage 93.95%.
Native runtime pixel parity is not claimed. All frontend writes are local mock state.
