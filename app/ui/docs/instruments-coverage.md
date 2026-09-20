# Data Manager Instruments coverage

## DATA-INSTRUMENTS-EDITOR-001 — Add and Edit instrument
- Product/module: SQX Data Manager / Instruments.
- Screen or dialog: Instruments table; Add instrument; Edit instrument; Commission & Swap Explanation.
- Source evidence: `DataManagerInstruments/module.js`, `views/instruments.html`,
  `views/addInstrumentPopup.html`, `controllers/InstrumentsCtrl.js`,
  `services/InstrumentService.js`, `instrumentDetails/*`, and `swapSettings/*`.
- Trigger: Add Instrument, or double click an instrument row.
- Visible controls: broker, identity, description, data type, eight specification fields,
  five commission modes and conditional parameters, full swap settings, Help, Close, Save.
- Preconditions: writable local configuration; Edit requires a current row.
- Validation: safe unique identity, valid broker/type, finite bounded values, commission
  parameters, swap type/day/time. Edit locks broker and identity.
- State transitions: open, configure, nested help, validation error, saved, cancelled.
- Expected outcome and mock operation: add or replace one shared catalogue entry through
  `useFileSymbols.addInstrument/editInstrument`; every chooser and table reacts immediately.
- Persistence: `sqx-file-symbols-v1` version 2, migrated from version 1.
- Status: visual implemented; interaction implemented; state behavior implemented.
- Verification: `instruments.test.ts`, `data-manager-instruments.spec.ts`, File Symbol
  regression, dark Add screenshot and reload.
- Evidence gaps/assumptions: backend numeric IDs and optional hidden exchange/country/sector
  controls are excluded; the active donor template hides those fields.

## DATA-INSTRUMENTS-CLONE-001 — Clone instrument
- Product/module: SQX Data Manager / Instruments.
- Screen or dialog: Clone instrument.
- Source evidence: `actions/clone/module.js`, `CloneInstrumentCtrl.js`,
  `cloneInstrument.html`, `InstrumentService.js`, and compiled servlet metadata.
- Trigger: Clone Instrument with one or more selected rows; first selected is the source.
- Visible controls: target broker, target name, broker postfix, Close, Save.
- Preconditions: at least one selected instrument.
- Validation: final broker-qualified identity is safe and unique; storage is writable.
- State transitions: selection error, configure, validation error, saved, cancelled.
- Expected outcome and mock operation: deep copied specification saved through
  `useFileSymbols.addInstrument`; source remains unchanged.
- Persistence: version 2 instrument catalogue.
- Status: visual implemented; interaction implemented; state behavior implemented.
- Verification: end-to-end clone/default/copy/duplicate path and reload coverage.
- Evidence gaps/assumptions: native numeric broker identity is represented by the typed local profile.

## DATA-INSTRUMENTS-MASS-EDIT-001 — Edit one or many
- Product/module: SQX Data Manager / Instruments.
- Screen or dialog: Edit instrument for one selection; Mass-Edit instrument for many.
- Source evidence: `actions/massEdit/module.js`, `massEditInstrumentPopup.html`,
  `instrumentDetails.html`, `InstrumentsCtrl.js`, and compiled mass-edit endpoint.
- Trigger: Mass Edit Instrument.
- Visible controls: one opt-in checkbox for each mutable field, corresponding editors,
  commission, swap, Help, Close, Save.
- Preconditions: one or more selected rows.
- Validation: multi-edit requires at least one enabled field; resulting records are all
  validated before the atomic store write.
- State transitions: selection error, normal edit or mass edit, validation error, saved, cancelled.
- Expected outcome and mock operation: enabled values replace the same fields on every
  selected identity through `useFileSymbols.replaceInstruments`; other values are preserved.
- Persistence: version 2 seed overrides and custom records.
- Status: visual implemented; interaction implemented; state behavior implemented.
- Verification: pure patch tests, two-row browser edit, dark screenshot, reload.
- Evidence gaps/assumptions: no live engine consumers exist; changes affect frontend mock consumers.

## DATA-INSTRUMENTS-DELETE-001 — Row and mass delete
- Product/module: SQX Data Manager / Instruments.
- Screen or dialog: singular/plural Remove instrument confirmation.
- Source evidence: `InstrumentsCtrl.js`, shared `DataManagerActions/delete/module.js`,
  `InstrumentService.js`, and compiled remove endpoint.
- Trigger: row × or Mass Delete.
- Visible controls: confirmation message, No, Yes, and inline dependency/storage error.
- Preconditions: current row or one or more selected rows.
- Validation: a referenced instrument cannot be removed; mutation is atomic.
- State transitions: selection error, confirm, cancel, blocked, removed.
- Expected outcome and mock operation: custom records are removed and fixture identities are
  hidden through `useFileSymbols.removeInstruments` without breaking dataset references.
- Persistence: version 2 removal tombstones.
- Status: visual implemented; interaction implemented; state behavior implemented.
- Verification: row delete, selection clearing, referenced-delete rejection, reload.
- Evidence gaps/assumptions: conservative dependency rejection replaces uncertain native cascade behavior.

## DATA-INSTRUMENTS-TRANSFER-001 — Save and Load JSON
- Product/module: SQX Data Manager / Instruments.
- Screen or dialog: Save instruments, Load instruments, Overwrite confirm.
- Source evidence: shared Save/Load registrations, `InstrumentsCtrl.js`,
  `InstrumentService.js`, and compiled `DataManagerInstruments.jar` XML/load branches.
- Trigger: Save or Load toolbar action.
- Visible controls: selected count, filename, JSON file picker, Close/Download or Validate,
  and duplicate Cancel/Skip/Overwrite/Overwrite all.
- Preconditions: Save requires selection; Load requires one JSON file at most 2 MB.
- Validation: version/kind envelope, bounded input, complete valid instruments,
  known/local broker mapping, duplicate sequence completed before mutation.
- State transitions: selection/file error, browser download, staged parse, duplicate decisions,
  atomic import, cancelled.
- Expected outcome and mock operation: meaningful `Instruments.json` download or atomic
  `useFileSymbols.importInstruments` update; no native SQX files are changed.
- Persistence: canonical imported records and overrides in version 3; selected file stays transient.
- Status: visual implemented; interaction implemented; state behavior implemented.
- Verification: JSON round trip/malformed/wrong-kind/duplicate unit tests, browser download, overwrite,
  light Save screenshot, and reload.
- Evidence gaps/assumptions: browser download and explicit file selection replace native paths;
  imported broker metadata is mapped locally and does not create broker profiles.

## Inclusion and exclusion register
- Included: all six active toolbar actions, double-click Edit, row delete, table filters,
  visible-row selection, commissions, swap/help, JSON duplicate choices, and persistence.
- Excluded: hidden optional exchange/country/sector controls, compiled alias endpoints without
  active tab controls, native filesystem/broker writes, and real trading calculations.
- Dead/duplicate code: the former generic Add placeholder is retained only as an unreachable
  legacy dialog branch pending broader Data Manager cleanup; no active control invokes it.
