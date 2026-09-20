# Data Manager Tools Coverage

Audit date: 2026-09-20
Reference: `C:/SQX_144_2953_win_20260601`

The active SQX Tools registration contains two actions. Both popup bodies and
their visible state rules are included below while retaining the HaruQuantAI
dark/light theme, typography, controls, and modal frame. Because the current app
has no native market-data backend, cloned history, review rows, charts, and
quality findings use deterministic browser-local mock data.

## DATA-TOOLS-TIMEZONE-001

- **Product/module:** SQX Data Manager / Tools
- **Screen:** Clone to Timezone
- **Source references:**
  `internal/plugins/DataManagerActions/cloneToTimezone/module.js`,
  `CloneToTimezoneCtrl.js`, `cloneToTimezone.html`,
  `internal/web/SQMANAGER/layout/LayoutCtrl.js`,
  `internal/plugins/DataManagerData/DMDataService.js`, and compiled
  `DataManagerData.jar` job metadata
- **Trigger:** Tools > Clone to timezone
- **Visible controls:** Source data symbol name, cloned symbol postfix,
  `{timeframe}` and `{cloneTime}` constants, fixed shift from -23 through 23,
  named timezone, Remove weekends, Close, Proceed, and shared Pause/Resume/Stop
- **Preconditions:** One or more selected datasets; no selected derived clone;
  no active provider, import, export, generic, or clone job
- **Validation rules:** Required postfix, known timezone/shift, safe generated
  identity, deterministic unique-name resolution, readable local storage
- **State transitions:** Open, configure, running, paused, resumed, stopped,
  failed, completed, and running restored as paused after reload
- **Expected outcome:** One derived definition per selected source with source
  lineage, chosen timezone or shift, optional weekend removal, copied metadata,
  shared progress, and completion in the trailing Status column
- **Related mock service operation:** `data.tools.clone.start`,
  `data.tools.clone.pause`, `data.tools.clone.resume`, `data.tools.clone.stop`
- **Persistence requirements:** `haru-data-tools-v1` stores settings, clone
  definitions, lineage, and current job
- **Implementation status:** Implemented
- **Verification status:** Visual: implemented in dark and light themes;
  interaction: automated; state behavior: automated
- **Evidence gaps/assumptions:** Native price transformation is backend-only and
  is represented by a deterministic metadata clone. Compiled backend behavior
  was inspected through registrations, templates, service calls, and `javap`.

## DATA-TOOLS-ANALYZE-001

- **Product/module:** SQX Data Manager / Tools
- **Screen:** View & Analyze with Data, Chart, and Analyze data quality tabs
- **Source references:**
  `internal/plugins/DataManagerActions/review/module.js`, `ReviewCtrl.js`,
  `review.html`, `styles.css`, nested `data`, `chart`, and `quality` controllers
  and templates, `internal/plugins/DataManagerData/DMDataService.js`, and compiled
  `DataManagerData.jar` review metadata
- **Trigger:** Tools > View & Analyze
- **Visible controls:** Read-only dataset metadata, View timeframe, Session,
  Data/Chart/Analyze data quality tabs, date jump, Skip, Edit line,
  Delete/Restore line, Save, Close, and unsaved-change confirmation
- **Preconditions:** The first eligible selected dataset has records and no Data
  Manager operation is active
- **Validation rules:** Supported timeframe/session, finite numeric edits, valid
  OHLC relationships, readable local storage, no active job at save time
- **State transitions:** Open, change projection, select row, edit, delete or
  restore, switch tabs with pending changes, save, keep editing, discard, reload
- **Expected outcome:** Stable virtualized data rows, a linked candlestick chart,
  and coherent gap/spike/bad-OHLC summaries and details based on the same saved
  browser-local sample
- **Related mock service operation:** `data.tools.review.read` and
  `data.tools.review.save`
- **Persistence requirements:** `haru-data-tools-v1` stores row mutations by
  dataset, timeframe, and session
- **Implementation status:** Implemented
- **Verification status:** Visual: implemented in dark and light themes;
  interaction: automated; state behavior: automated
- **Evidence gaps/assumptions:** Review data is capped at 1,000 deterministic
  rows and does not read or rewrite provider files. Chart is unavailable for
  Tick; quality analysis is unavailable for Tick and Intraday, matching SQX.

## Inclusion and exclusion register

| Item | Decision | Reason |
| --- | --- | --- |
| Two active Tools actions | Included | Active `DataManagerActionTools` registrations |
| Clone field structure and job controls | Included | Template, controller, service, and event evidence |
| Derived-definition lineage and reload | Included | Required for coherent frontend mock state |
| Review Data, Chart, and quality tabs | Included | Active nested controllers and templates |
| Row edit/delete/save/discard behavior | Included | Controller and service actions are observable |
| Native history-file transformation | Excluded | Backend-only; no native writer or price archive exists |
| Full historical data pagination | Excluded | Backend contract is unavailable; bounded virtualization is used |
| Provider contact or native data mutation | Excluded | Frontend-only mock boundary |
| Legacy SQX skin | Excluded | Current HaruQuantAI design system is authoritative |

## Verification mapping

- `src/domains/data/dataTools.test.ts`: selection, recursive-clone rejection,
  unique clone identities, deterministic review rows, validation, quality
  analysis, persistence, corruption recovery, and reload normalization.
- `tests/data-manager-tools.spec.ts`: popup entry, clone lifecycle, shared
  progress/status, reload, View & Analyze edits and persistence, discard prompt,
  all tabs, and Tick limitations.
- Manual browser inspection: Clone and View & Analyze in HaruQuantAI dark and
  light themes.
