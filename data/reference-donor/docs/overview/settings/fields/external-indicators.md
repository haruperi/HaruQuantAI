# External indicators — field reference (for UI tests)

> Defined/imported in **Data manager → External indicators**, then merely selected (checkbox + weight)
> in the Builder's Building blocks panel.

Source:
- `internal/plugins/DataManagerCustomData/customData.html`, `DMCustomDataCtrl.js`,
  `DMCustomDataService.js` — the list/management screen (Data Manager).
- `internal/plugins/DataManagerCustomData/add/customDataAdd.html`, `CustomDataAddCtrl.js` — Add/Edit
  form.
- `internal/plugins/DataManagerCustomData/import/customDataImport.html`, `CustomDataImportCtrl.js` —
  data import form (maps a file's columns to the indicator's value lines).
- `internal/plugins/SettingsBlocks/views/blocks.html` (lines ~108-123) and
  `internal/plugins/SettingsBlocks/services/BlocksService.js` (`initCustomDataGrid`, `addCDataIndy`,
  `onCDataIndyChange`) — the Building-blocks-side selection grid.
- `projects/libs/Plugins/src/com/strategyquant/plugin/Servlet/impl/Constants/ConstantsServlet.java`
  (lines 558-563) — server-side `customDataTypes` enum sent to the client.

> Note: this feature was previously called **Custom Data Indicators**; the plugin folder/ids still use
> `CustomData`/`cd` even though the UI label is "External indicators".

## Add / Edit external indicator (`customDataAdd.html`, modal `#customDataAddModal`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Name | `config.name` | text input | `null` | Disabled when editing (`actionName=='edit'`). |
| Return type | `config.type` | `<select>` | `customDataTypes[0].value` | Options from server `customDataTypes` constant: **Price** (`IndicatorValuePrice`), **Number** (`IndicatorValueNumber`), **Price range** (`IndicatorValuePriceRange`), **Signal** (`SignalValueBoolean`). |
| Indicator values (lines) — repeated per `config.values` (3 rows by default) | | | | |
| ↳ Value name | `value.name` (per row) | text input | `null` | Row label `#{{$index+1}}`. |
| ↳ MT4 code | `value.mt4` (per row) | text input | `null` | Optional per-platform source snippet, e.g. `iCustom(NULL, 0, "RVI", 10, 0, #Shift#)`. |
| ↳ MT5 code | `value.mt5` (per row) | text input | `null` | Optional. |
| ↳ EL code | `value.el` (per row) | text input | `null` | Optional (EasyLanguage / TradeStation). |
| Help | `openHelp()` | button | — | Opens external-indicators documentation. |
| Save | `onSave()` | button | — | |

`config.values` initializes with 3 empty rows (`{name:null, mt4:null, mt5:null, el:null}`); more can be
added/removed via `ng-repeat` controls not fully shown in the current template excerpt.

## Import data (`customDataImport.html`, modal `#customDataImportModal`)

| Label | Config key (ng-model) | Type | Default / notes |
|---|---|---|---|
| Data file | `dataDetails.importFile` | readonly text + Browse button (`openImportFilePicker()`) | required |
| Predefined file format | `dataDetails.fileFormat` | `<select>` (`fileFormats`) | `onReloadData()` on change; Save / Save as / Delete buttons alongside (`onSaveFormat`, `onSaveFormatAs`, `onDeleteFormat`) |
| Skip rows | `dataDetails.skipRows` | number spinner | min 0, step 1 |
| Skip columns | `dataDetails.skipCols` | number spinner | min 0, step 1 |
| Separator | `dataDetails.separator` | `<select>` (`separators`) | |
| Date format | `dataDetails.dateFormat` | `<sq-combo-input>` (`dateFormats`, `single="true"`) | example shown next to field |
| Data errors handling | `dataDetails.errorHandling` | radio group | `0` = "Stop import", `1` = "Ignore lines with errors" |
| Column mapping grid | `cdColumnsGrid` (`sqGrid`) | grid | maps file columns to `Value1`, `Value2`, … |
| Start Import | `onStartImport(importDataForm)` | button | |

## Selection grid inside Building blocks (`customDataGridBB`)

`SettingsBlocks/services/BlocksService.js` → `initCustomDataGrid()`. Columns (widths `[10, 30, '*', 80, 60]`):

| Column | Type | Notes |
|---|---|---|
| ID | text | hidden id column (`setFirstColumnAsId`) |
| Use | checkbox widget | `checkboxChecked` event → `onCheckboxChecked(customDataGrid, ..., categories.customData)` |
| Name | text | left-aligned |
| Timeframe | text | |
| Weight | float (2 decimals) spinner | `spinnerUpdated` event |

Empty-grid text: *"No custom data defined."* Sorting disabled.

Surrounding controls in `SettingsBlocks/views/blocks.html`:

| Control | Config key (ng-model) / handler | Type | Notes |
|---|---|---|---|
| Section legend | — | display | "External indicators for timeframe(s)" : `{{customDataTimeframes.list}}` |
| Add new | `addCDataIndy()` | link | Calls `AppService.performAction('SQMANAGER', "openCDataIndy", null)` — opens the Data Manager External-indicators editor (out of this panel). |
| Show all external indicators (also for not-matching Timeframes) | `gui.showAllCDataIndy` | checkbox | `ng-change="onCDataIndyChange()"` (calls `BlocksService.settingsChanged()` + `loadCustomData(true, ...)`). Section hidden entirely when `gui.isStockPicker`. |

## Related

- Prose page: [../external-indicators.md](../external-indicators.md)
- Fields hub: [README.md](README.md)
- Parent panel: [../building-blocks.md](../building-blocks.md)
- Matching timeframe requirement: [../data.md](../data.md)
