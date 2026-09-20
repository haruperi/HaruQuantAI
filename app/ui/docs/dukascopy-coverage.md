# Dukascopy popup coverage and evidence

Stable feature ID: `FEAT-UI-DATA-DUKASCOPY-ADD`. Detailed machine-readable entry:
`DATA-DUKASCOPY-ADD-001` in [coverage.json](coverage.json). Module status remains Partial.

## Inclusion register

| ID | Surface | Included behavior | Visual | Interaction | State |
| --- | --- | --- | --- | --- | --- |
| DATA-DUKASCOPY-ADD-001 | Main popup | 725-row catalogue, source-order category rows, row/group/all selection, search and type filters, Tick/M1, broker and postfix, consent, close/save | Screenshot reviewed | Playwright passed | Save/reload passed |
| DATA-DUKASCOPY-MAP-001 | Conditional identify instruments | Broker instrument prefix matching, unresolved selection, SQ default, skip, mass actions, Back/save | Source-template reconstruction | Playwright passed for unresolved/skip/default | Mapping payload persisted |

Shared entry context for both surfaces: SQX/Data Manager; entry point is Dukascopy
menu > Add new Dukascopy symbol. Main source files are donor
`DataSourceDukascopy/add/{module.js,addPopup.html,addPopupCtrl.js,styles.css}`,
`DukascopyService.js`, and `dukascopy.csv`. Mapping additionally uses
`add/selectInstrumentsPopup.html`. Reference installation:
`C:/SQX_144_2953_win_20260601/internal/plugins/`.

Preconditions: bundled catalogue is valid; mapping requires a configured non-default
mock broker. Main validation requires selected symbols and explicit consent.
Mapping requires every symbol resolved or skipped and at least one non-skipped symbol.
Mock validation additionally rejects duplicate names and storage failure. Transitions:
open -> filter/select -> validate -> conditional mapping -> save/error -> close;
Back returns to the original selection and configuration. Filter changes rebuild
selection, consistent with the source controller clearing and rebuilding grid rows.
Reopening clears selection and consent while options stay within the mounted workspace.

Expected outcome / mock operation: `useDataManagerStore.addData` stores configured
symbol definitions with empty downloaded date ranges, zero records, selected precision,
postfix, broker, timezone and instrument mapping. Browser key `sqx-data-manager-v1`,
schema 1, persists definitions and mock broker metadata. No database or external request.

Verification: 3 Vitest catalogue cases; 4 focused popup browser scenarios and 1 existing
ribbon regression. Desktop and small viewport PNGs generated under ignored
`app/ui/test-results/` and visually inspected. Build passes. Full repository CI is
blocked by eight existing logging-lock conflicts in tests/test_main.py; lint, typing,
architecture and 93.95% coverage passed. This is not a claim of complete CI qualification.

## Exclusion register and gaps

- Live price downloads, network catalogue refresh and broker-management CRUD are
  separate workflows; none is initiated by this mock Add popup.
- No broker is fabricated. Conditional mapping is tested with an explicit browser fixture.
- Duplicate name rejection is a conservative, documented mock policy; native duplicate
  outcomes remain unverified. No silent overwrite occurs.
- Native runtime comparison is unavailable; visuals use the owner's screenshot and
  shipped HTML/CSS, behavior uses source controllers and inspected Java bytecode.
- Mapping visual parity is source-derived, not verified against a runtime screenshot.
- All 725 bounded catalogue rows render directly; observed browser tests are responsive.
  Virtualization was unnecessary at this fixed catalogue size and would complicate
  native table accessibility. No unbounded remote catalogue is loaded.
- Browser storage load corruption is preserved and blocks mutation rather than resetting
  stored work. Successful save-and-reload and write-failure paths have browser evidence;
  not every malformed browser-state permutation has a test.

## Iteration 2 presentation correction

The catalogue location is `data/market/dukascopy/dukascopy.csv`. The SQX reference
owns structure and behavior; HaruQuantAI owns fonts and active-theme appearance.
Dark/light screenshot review and theme inheritance checks pass. Current evidence:
3 catalogue unit cases and 6 browser scenarios, including existing ribbon regression.
The existing Python logging-lock qualification blocker remains unchanged.

## Download inclusion and evidence register

### DATA-DUKASCOPY-DOWNLOAD-001

- Product/module: SQX / Data Manager; screen: Download Dukascopy data.
- Sources: `DataSourceDukascopy/import/{module.js,importPopup.html,importPopupCtrl.js}`,
  `DataSourceDukascopy/{DukascopyService.js,style.css}`, shared
  `web/app/directives/dateRange/{DateRange.js,DateRangeCtrl.js,dateRange.html,styles.css}`.
- Entry: Dukascopy data > Download data for existing symbol.
- Controls: From/To, Since last date, Last 6 months/year/5 years/10 years/All time,
  missing-only/overwrite, Standard/CDN/Hong Kong, disclaimer, Close/Start, progress actions.
- Preconditions: selected eligible Dukascopy row(s); cloned and active rows rejected.
  Mixed selection is reduced to Dukascopy rows. One active mock download at a time.
- Validation: valid chronological dates, source bounds, per-symbol availability,
  selected targets, storage availability. Both fast modes require confirmation for every profile.
- Transitions: select -> configure -> confirm when applicable -> running -> paused /
  cancelled / completed / failed. Reload running -> paused. Resolved per-target modes determine
  deterministic speed; missing-only deduplicates and overwrite regenerates mock intervals.
- Expected outcome: exact selected IDs receive persisted simulated coverage and row
  progress; no external price history or provider requests.
- Mock operations: `useDukascopyDownloads.start/advance/action`.
- Persistence: `sqx-data-download-v1`, version 1, separate from existing definitions.
- Implementation: visual, interaction and state implemented within frontend scope.
- Verification: unit rules plus browser lifecycle, mixed/multiple selection, trial,
  validation, reload, cancellation and storage-error scenarios; dark/light screenshots.
- Gaps: native runtime appearance not observed; mock count/rate semantics are deliberately
  synthetic. Original fixture gaps are unknown. Source bounds use first row tick start,
  as the donor does, with per-target precision availability checked before simulation.

### DATA-DUKASCOPY-CDN-001

- Product/module: SQX / Data Manager; screen: StrategyQuant CDN Data Disclaimer.
- Source: `DataSourceDukascopy/import/cdnDisclaimerPopup.html`.
- Entry: disclaimer link in download popup; controls: Close/header close/Escape.
- Preconditions: download dialog open; validation: none (informational).
- Transitions: open disclaimer -> return to retained download form; focus returns to link.
- Outcome/mock operation: source-backed disclaimer text, local dialog state only.
- Persistence: none. Visual/interaction/state implemented; browser open/close/focus verified.
- Gap: rendered as a replacement panel within the modal rather than two stacked overlays;
  preserves the same nested navigation and draft state while avoiding competing focus traps.

### Explicit exclusions and source discrepancies

- QuantDataManager Pro upgrade controls are excluded because their product predicate is
  false for this SQX workflow; the donor's initial true flag is not copied as product truth.
- Real CDN/provider downloads, extraction, licensing and payments require a backend and
  remain excluded. Trial is the documented Starter mock profile mapping.
- The donor replaces its source-filtered selection with original rows when checking
  in-progress status; this bug is not reproduced. Eligibility remains source-safe.
- `settingsChanged()` is missing from the donor controller. Mode preference persistence
  is an explicit mock behavior matching the existing donor preference concept.
- Existing Python CI logging-lock failures remain a qualification blocker, not a UI pass.

### DATA-DUKASCOPY-FAST-001

- Product/module: SQX / Data Manager; screen: nested Fast Data Download warning.
- Sources: donor import/importPopupCtrl.js onStartImport; owner screenshot and broader
  all-profile warning/fallback requirement. Local DukascopyDownloadDialog.tsx,
  dukascopyDownload.ts and dataManagerStore.ts.
- Entry/preconditions: Start download with valid settings and CDN or Hong Kong selected.
- Controls: Close, Cancel, OK, Escape, bounded Tab focus; parent remains visible/inert.
- Validation: existing request/date checks run before warning and again before job start.
- Transitions: configure -> warning -> Cancel/Close/Escape returns unchanged draft;
  OK -> persisted running job -> standard fallback for unconfirmed availability.
- Outcome/mock service: useDukascopyDownloads.start resolves each target independently;
  advance uses slowest target mode for existing aggregate progress. No extra status panel.
- Persistence: optional resolvedModes in version-1 download job; requested preference
  retained separately. Legacy jobs derive routing on read, running jobs recover paused.
- Visual coverage: themed stacked dialog with dark/light screenshot evidence.
- Interaction coverage: both fast options, Starter/full profiles, cancel/Escape/focus,
  confirmation, standard bypass, storage errors verified by browser scenarios.
- State coverage: per-target routing, unknown/false availability fallback, explicit mock
  support, reload and completed job checked with unit/browser tests.
- Evidence gap/assumption: no live CDN capability manifest found in donor controller or
  CSV. fastDownloadAvailable is optional mock metadata only. Current catalogue targets
  lack it and therefore simulate standard downloads. No actual provider data is fetched.
- Exclusions: real availability discovery and package/range-level fallback require backend.

### DATA-DUKASCOPY-DISCLAIMER-001

- Product/module: SQX / Data Manager; screen: Dukascopy data disclaimer.
- Sources: DataSourceDukascopy/disclaimer/module.js, dukascopyDataDisclaimerCtrl.js,
  disclaimerPopup.html; implementation DataManager.tsx and dataSourceRibbon.ts.
- Entry: Dukascopy data > Dukascopy Data Disclaimer; stable dukascopy-information ID.
- Controls: Disclaimer heading, four original paragraphs, header close and footer Close.
- Preconditions/validation: none; no selected datasets or agreement required.
- Transitions: menu -> informational modal -> Close/header/Escape -> ribbon focus.
- Expected outcome: read provider disclaimer with unchanged data/operation state.
- Mock service: none (local presentation only). Persistence: none.
- Implementation: visual/interaction/state complete for this informational screen.
- Verification: browser checks in both themes, paragraph content/count, all close routes,
  focus return, no selection, no operation or local-storage mutation; build passed.
- Evidence gaps: native pixel dimensions not observed; application modal/theme retained.
- Exclusions: CDN disclaimer remains separate; no legal acceptance or backend operation.
