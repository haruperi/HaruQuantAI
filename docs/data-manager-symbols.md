# Symbols workspace

The Data Manager Symbols tab uses the same `Symbols` service and database as the
headless CLI. The domain HTTP adapter lives in
`app/workspace/data_manager/http.py`; `app/main.py` only mounts its router.
All endpoints require a UI session and the host's data read/write scopes.

- Browse, search, sort, and filter the catalog; use Previous/Next and choose
  25, 50, or 100 rows per page. Selections persist across pages.
- Add Symbol opens the specification editor. The datasource suffix follows the
  CLI naming convention: `EURUSD` with `demo` becomes `EURUSD_demo`.
- Select one symbol to edit or clone it. Select multiple symbols for Mass Edit;
  only checked fields change. Double-click a row to edit it.
- Mass Delete removes selected symbols after confirmation. Each row also has a
  delete action. Errors are shown without removing unconfirmed rows locally.
- Save downloads selected symbols as CSV, or the full catalog if nothing is
  selected. Exports retain nested specification fields and can exceed 1,000 rows.
- Load accepts a CSV upload up to 10 MB. Valid rows are imported and skipped rows
  are reported. Existing names are skipped rather than overwritten.
- Refresh symbols reloads the persisted catalog.
- Select one or more rows and choose **Update from MT5** to refresh their saved
  specifications from the running MT5 Expert bridge. The button is disabled during
  the update. Updated rows appear after the host confirms the batch; failures retain
  the previous snapshot and display an error in the progress area.
- When the successfully loaded catalog contains no symbols, **Update from MT5**
  imports every symbol returned by the terminal, retaining the native MT5 names.
  The import is atomic, including catalogs larger than 1,000 entries. A populated
  catalog still requires selecting rows; an empty search result does not trigger
  import mode.

CSV imports and exports use the service's existing format, including JSON within
specification columns. Browser commission and swap settings are retained in the
nested contract fields when saving, cloning, or transferring symbols.
