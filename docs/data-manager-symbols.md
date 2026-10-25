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

CSV imports and exports use the service's existing format, including JSON within
specification columns. Browser commission and swap settings are retained in the
nested contract fields when saving, cloning, or transferring symbols.
