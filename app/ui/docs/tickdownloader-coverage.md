# TickDownloader coverage register

## TD-IMPORT-001

- Product/module: SQX / Data Manager, TickDownloader import popup.
- Sources: internal/plugins/DataSourceTD/import/{module.js,importPopup.html,
  DataSourceTDImportCtrl.js}, DataSourceTDService.js, styles.css; read-only bytecode
  inspection of DataSourceTDServlet and TDDataManager in DataSourceTD.jar.
- Entry: TickDownloader import > Import TickDownloader data.
- Controls: read-only TickDownloader Installation field, Select directory chooser,
  header and row checkboxes, unsorted Symbol grid, postfix, Close, Start import.
- Preconditions: directory selected this browser session; file-backed subdirectories
  discovered under tickdata or directly selected directory. No real source content read.
- Validation: path shape, one root, 20,000 files, 1,000 symbols, nonempty selection,
  postfix length/characters, global name collisions, 10,000 definitions, storage success,
  and no other active data operation.
- Transitions: choose -> discover -> select -> validate -> running -> paused/completed/
  cancelled/failed. Reload running -> paused. New import requires folder reselection.
- Outcome: selected names plus postfix produce mock definitions and trailing row status;
  existing provider datasets and source files are unchanged. Empty history/zero records
  explicitly avoid fabricating native tick import results.
- Mock operations: discoverTD, validateTD, useTickDownloader.start/advance/action.
- Persistence: sqx-tickdownloader-v1, version 1; folder label, postfix, metadata-only job
  and definitions. No File objects, contents, absolute paths or external credentials.
- Implementation: visual implemented from templates, interaction implemented, state
  implemented within mock boundary. Shared progress only; status column after Hide.
- Verification: four unit cases and two import browser scenarios; folder picker fixture,
  empty symbols, selection, collision, postfix, pause/resume/reload, cancellation, initial
  storage failure and unchanged source file verified. Dark/light screenshots inspected.
  Existing Dukascopy browser regression passed; ribbon header expectation updated to
  include the previously added trailing status column.
- Gaps: no native runtime screenshot, no real history decoder. Browser FileList omits
  empty directories and its enumeration order may differ from native listFiles. One active
  metadata job is modeled; source importDataAction/importAction naming mismatch is not
  reproduced as an external request. Mid-progress storage failure is implemented but not
  independently browser-tested for TD (same pattern as verified Dukascopy failure).

## Inclusion/exclusion register

Included: every visible popup control, browse/discovery, selection, validation, simulated
lifecycle and persisted definitions. Browser directory chooser replaces the native picker.
Excluded: native filesystem browser, background access after reload, tick decoding, price
history ingestion, provider connections and modifying source files. These require a backend
and are outside this frontend-only workflow. No backend completeness or native pixel parity
is claimed. Required Python CI remains blocked by the pre-existing logging lock.
