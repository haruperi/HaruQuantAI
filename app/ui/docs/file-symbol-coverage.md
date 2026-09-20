# File Import — Add symbol coverage

## FILE-SYMBOL-001 — Add symbol
- Product/module/screen: SQX Data Manager / File import / Add symbol.
- Sources: internal/plugins/DataSourceFiles/add/{module.js,addPopup.html,DataSourceFilesAddCtrl.js},
  DataSourceFilesService.js; common/Batch1/libs.js:isSymbolNameValid.
- Trigger: File import > Add symbol, no selected row required.
- Controls: symbol name; start/end timestamp radios; broker filter/instrument chooser;
  disabled instrument details; swap draft; Add new instrument; Close/Save.
- Preconditions: valid instrument available. Validation: required source-pattern name,
  mock 128-character bound, unique across fixture/Dukascopy/TickDownloader/file records,
  selected instrument and writable storage. Invalid input keeps dialog/draft.
- Transitions: open -> edit -> save -> row; close/Escape -> no new symbol. Nested flows
  return to unchanged parent draft. Focus/keyboard loop uses active dialog only.
- Outcome: File import row, zero records, empty date range, saved instrument/broker/bar type;
  no historical prices invented. Timeframe remains unknown until a later import workflow.
- Mock operation: useFileSymbols.addSymbol (counterpart /dataSourceFiles/add).
- Persistence: sqx-file-symbols-v1, version 2 with lossless version 1 reads; separate from existing provider stores.
- Visual coverage: source section order and full controls, app theme/font, responsive scroll.
- Interaction coverage: names, radios, broker filter, selection, nested add/help, Close/Save.
- State coverage: save/cancel/reload, collisions and storage failure; implemented/tested.
- Gaps: native backend validation not available; finite/duplicate/storage protections are
  explicit mock rules. Main swap draft is not serialized by source symbol add and does
  not mutate shared instrument settings. Native numeric data/source IDs are represented
  by typed frontend labels rather than claimed backend-compatible IDs.

## FILE-INSTRUMENT-001 — chooser and nested Add instrument
- Product/module/screen: SQX Data Manager / Add symbol / instrument chooser and Add instrument.
- Sources: web/app/directives/instrumentChooser/{InstrumentChooser.js,instrumentChooser.html,
  addInstrumentPopup.html}, instrumentDetails/{InstrumentDetails.js,instrumentDetails.html}.
- Trigger: parent Add new instrument. Controls: broker, data type, name, description,
  point value, tick size/step, spread/slippage, distance, order multiplier/step, commission,
  swap, help, Close/Save. All broker profiles filter plus mtUse brokers and SQ default.
- Preconditions/validation: instrument identity unique; broker/type valid; finite source
  bounds, required name, optional description defaults 'not set'; broker postfix appended.
- Transitions: draft -> nested save -> custom instrument persisted and selected in parent;
  nested close returns unchanged parent. Parent cancellation retains independently saved
  instrument. Type selection adjusts numeric spinner increments, not entered values,
  consistent with donor's type-change watcher (defaults are applied on Add).
- Outcome/mock operation: useFileSymbols.addInstrument mirrors /instruments/addInstrument;
  subscriptions replaced with reactive store views. Custom instruments appear in Instruments.
- Persistence: version 3 file-symbol store with canonical typed commission and swap JSON objects.
- Visual/interaction/state: implemented; browser save/filter/reload and unit bounds checked.
- Gaps: starting universe uses four existing fixture instruments plus saved custom entries;
  missing seed specification fields use donor-shaped defaults, not invented real broker specs.
  Nested screens replace the active modal while preserving parent draft, preventing multiple
  active focus traps; no claim of native pixel-identical nested overlay behavior.

## FILE-COMMISSION-001 — default commission models
- Product/module/screen: SQX Data Manager / nested Add instrument / Default commissions model.
- Sources: instrumentDetails.js constants/listCommissionMethods; multiPropertyGrid and
  propertyGrid getValuesXml; extend/Snippets/SQ/Trading/Commissions/*.java.
- Trigger: nested instrument. Controls: None, Per trade, Size based, Percentage based,
  Stockpicker. Parameter fields follow model, including stockpicker unit/min/max selectors.
- Validation: source numeric ranges and option membership, finite values.
- Transitions: model switch resets that model's defaults; edits -> instrument Save.
- Outcome/mock operation: typed JSON configuration with explicit model and parameter fields;
  no live commission calculation or external call.
- Persistence: instrument record. Visual/interaction/state implemented; all model switching,
  persisted Stockpicker, numeric boundary and serialization tests pass.
- Gaps: runtime license/extension filtering unavailable; five bundled snippet models used.

## FILE-SWAP-001 — Swap and explanation
- Product/module/screen: SQX Data Manager / instrument details / Swap, Commission & Swap Explanation.
- Sources: web/app/directives/swapSettings/{swapSettings.js,swapSettings.html}.
- Trigger: details in parent/nested popup; Help opens source explanation.
- Controls: Use; money/points/percent; Long/Short; triple day; rollout time; Help/Close.
- Preconditions/validation: dependent controls disabled when Use off; signed finite amounts,
  valid time and day. Defaults disabled, money, zero amounts, Wednesday, 23:00.
- Transitions: toggle/edit; help -> return/focus; nested Save persists, parent changes draft-only.
- Outcome/mock operation: typed JSON fields use/type/long/short/tripleSwapOn/rolloutHour;
  no overnight accounting is performed. Persistence in nested instrument only.
- Visual/interaction/state implemented; help return, enabled edits and reload checked.
- Gaps: weekday list uses seven days; full backend constant payload unavailable.

## Explicit exclusions
Real file import, history decoding, broker CRUD, and trading calculations are separate workflows.
Global instrument mass-edit/delete/clone is implemented in the Instruments tab. Exchange/country/sector optional controls
are excluded because donor hides them with ng-show=false. No reachable Add symbol control
is intentionally left inert. The global Instruments workflow and shared catalogue are detailed
in [instruments coverage](instruments-coverage.md).

The chooser/editor is also reused by Mass import through FileSymbolDialog composition.
File names now check completed and active pending file-import results across providers.
Mass parent settings retain their draft through nested Add instrument/help. See
[file import coverage](file-import-coverage.md).
