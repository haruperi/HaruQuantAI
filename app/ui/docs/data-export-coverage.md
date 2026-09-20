# Data Manager Export Coverage

Audit date: 2026-09-20
Reference: `C:/SQX_144_2953_win_20260601`

The active SQX Export registration contains three actions. Their popup structure,
validation, and frontend job lifecycle are included below. HaruQuantAI retains its
own dark/light theme and typography. The current app has no export backend, native
path access, or complete price archive, so generated data is deterministic mock
data and native MT4 files are represented by an honest manifest.

## DATA-EXPORT-CSV-001

- **Product/module:** SQX Data Manager / Export to CSV
- **Screen:** Export data for selected record(s), including New file format and
  Delete file format prompts
- **Source references:**
  `internal/plugins/DataManagerActions/exportToCsv/module.js`,
  `ExportToCsvCtrl.js`, `ExportToCsvService.js`, `exportToCSV.html`,
  `newFormatPopup.html`, `styles.css`, `internal/web/QDM/help.txt`, and compiled
  `DataManagerData.jar` CSV format classes
- **Trigger:** Export tab > Export to CSV
- **Visible controls:** From/To, six presets, timeframe, session, target timezone,
  predefined/saved format, Save, Save as, Delete, Include header, header/template
  token insertion, directory display, prefix, computed suffix, Close, Export
- **Preconditions:** One or more selected rows containing a non-empty date range
  and records; no other active Data Manager job
- **Validation rules:** Bounded selected rows, date order and coverage, known
  session/timezone, safe prefix, supported format tokens, unique custom format
  names, readable local storage
- **State transitions:** Open, configure, save/delete format, running, paused,
  resumed, cancelled, failed, completed, reload running as paused
- **Expected outcome:** One bounded CSV browser download per selected dataset;
  progress appears in the shared strip and the job appears in the trailing Status
  column
- **Mock service operation:** `data.export.csv`, `data.export.pause`,
  `data.export.resume`, `data.export.stop`
- **Persistence:** `haru-data-export-v1` stores custom formats, last settings,
  artifact history, and current job; unfinished running work restores paused
- **Implementation status:** Implemented
- **Verification status:** Visual: implemented; interaction: automated;
  state behavior: automated
- **Evidence gaps/assumptions:** The compiled backend format catalog was inspected,
  but full backend source is unavailable. Each output contains at most 180
  deterministic mock rows. Browser download settings replace a native directory.

## DATA-EXPORT-MT4-001

- **Product/module:** SQX Data Manager / Export to MT4 (FXT & HST)
- **Screen:** Export to MetaTrader 4 FXT and HST for selected symbol
- **Source references:**
  `internal/plugins/DataManagerActions/exportToMT4/module.js`,
  `ExportToMT4Ctrl.js`, `ExportToMT4Service.js`, `exportToMT4.html`,
  `user/settings/DataConfig/mt4.properties`, and compiled MT4 export job classes
- **Trigger:** Export tab > Export MT4 (FXT & HST)
- **Visible controls:** From/To, six presets, 4 GB note, installation/data-folder
  selectors, server, specification symbol, MT4 name, timeframe, timezone,
  encoding, export mode, specification-file loader, property summary, Build 8xx+
  warning, Help, Close, Start export
- **Preconditions:** Exactly one selected dataset with records and Tick source
  precision; no active Data Manager job
- **Validation rules:** Date coverage, required output metadata/server, supported
  timeframe/mode, safe MT4 name, text-only bounded `KEY=value` properties file,
  readable local storage
- **State transitions:** Open, select folder metadata, load properties, configure,
  running, paused, resumed, cancelled, failed, completed, reload paused
- **Expected outcome:** A JSON browser download describing the requested native
  targets and properties, clearly marked `nativeCompatible: false`; shared
  progress and trailing Status update coherently
- **Mock service operation:** `data.export.mt4-manifest`
- **Persistence:** Same versioned export store; remembers safe display metadata,
  history, and job without retaining folder handles or reading arbitrary files
- **Implementation status:** Implemented with explicit native-binary exclusion
- **Verification status:** Visual: implemented; interaction: automated;
  state behavior: automated
- **Evidence gaps/assumptions:** The proprietary FXT/HST writer is compiled and
  server-side. No native binary is fabricated. Browser folder selectors expose
  metadata only.

## DATA-EXPORT-MT5-001

- **Product/module:** SQX Data Manager / Export to MT5 data (99% test)
- **Screen:** Export to MT5 data (99% history quality) for selected symbol,
  including overwrite confirmation
- **Source references:**
  `internal/plugins/DataManagerActions/exportToMT5/module.js`,
  `ExportToMT5Ctrl.js`, `ExportToMT5Service.js`, `exportToMT5.html`, and compiled
  MT5 export job classes
- **Trigger:** Export tab > Export to MT5 data (99% test)
- **Visible controls:** From/To, six presets, Tick/M1, fixed spread in points,
  fixed spread in pips, real tick spread, timezone, directory display, filename,
  `.csv` suffix, Close, Export, overwrite No/Yes
- **Preconditions:** Exactly one selected dataset with records and Tick or M1
  source precision; no active Data Manager job
- **Validation rules:** Date coverage, compatible timeframe/spread mode, spread
  between 0 and 1,000, safe filename, known timezone, readable storage
- **State transitions:** Open, configure, overwrite prompt when history collides,
  running, paused, resumed, cancelled, failed, completed, reload paused
- **Expected outcome:** One bounded MT5-shaped CSV browser download with tick or M1
  columns; shared progress and trailing Status update coherently
- **Mock service operation:** `data.export.mt5`
- **Persistence:** Same versioned export store; remembers last spread/timezone,
  artifact names, and current job
- **Implementation status:** Implemented
- **Verification status:** Visual: implemented; interaction: automated;
  state behavior: automated
- **Evidence gaps/assumptions:** The file contains deterministic mock rows rather
  than a provider price archive. Aggregated fixture labels beginning with Tick or
  M1 are treated as possessing that source precision.

## Inclusion and exclusion register

| Item | Decision | Reason |
| --- | --- | --- |
| Three registered Export actions | Included | Active `DataManagerActionExport` registrations |
| CSV built-in formats and token editor | Included | Template, controller, compiled format metadata |
| Custom CSV format persistence | Included | Controller/service behavior is observable |
| MT4 settings/property loader | Included | Template/controller plus shipped default properties |
| Native FXT/HST binary writer | Excluded | Compiled backend only; a browser mock cannot promise compatibility |
| MT5 CSV mock file | Included | Browser can produce a meaningful bounded CSV |
| Native output-directory writes | Excluded | Browser security boundary; normal downloads are used |
| Tools-tab Review action | Excluded | Registered under `DataManagerActionTools`, outside this task |
| Full historical prices/provider calls | Excluded | No backend and no market-data archive |

## Verification mapping

- `src/domains/data/dataExport.test.ts`: selection, presets, validation, format
  tokens, properties parsing, deterministic artifacts, persistence, reload,
  conflicts, and corruption.
- `tests/data-manager-export.spec.ts`: complete popup entry, custom-format prompt,
  browser downloads, MT4 properties, MT5 source constraints and overwrite prompt,
  shared progress, pause/resume, row Status, and reload.
- `tests/data-manager-source-ribbon.spec.ts`: exact Export labels and cross-tab
  selection/filter preservation.
