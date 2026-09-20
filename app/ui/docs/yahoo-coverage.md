# Yahoo data coverage and evidence

Task `FEAT-UI-DATA-YAHOO`; approved plan: `docs/yahoo-data-implementation-plan.md`.
Reference installation: `C:/SQX_144_2953_win_20260601`.

## Source and registration trace

`DataSourceYahoo/module.js` registers the provider as `Yahoo`, using the `yahoo` CSS class and two
actions. `add/module.js` opens `Add Yahoo data`; its template accepts ticker text separated by comma,
semicolon or newline plus an optional data-name postfix. The controller resets both fields on open
and calls `yahoo/add`. Compiled `DataSourceYahoo.jar` inspection confirms the separator expression,
whitespace removal, live quote metadata lookup and D1 record creation.

`download/module.js` opens `Download Yahoo data for 'SYMBOL'` or `multiple`. The controller filters
the selected records to Yahoo, rejects clones and jobs already in progress, then calls the shared
date-range workflow. Its template supplies From/To, Since last date, Last 6 months, Last year,
Last 5 years, Last 10 years, All time, Add only missing data and Overwrite existing data.

The exact local `internal/web/img/dm-yahoo.png` asset is used by the ribbon. Its source and copied
asset SHA256 is `611ECAB10486A3F1F3538C54252FE3725D8E05992D9694A0040261ED0E1DB6BD`.

## Inclusion and exclusion register

Included: the concise Yahoo ribbon label and source icon, both dedicated dialogs, source wording and
controls, exact ticker parsing, bounded ticker resolution, postfix/name checks, D1 definitions,
Yahoo-only mixed selection, clone/in-progress rejection, six date presets, missing/overwrite
coverage, persistent jobs, pause/resume/stop/fail/complete recovery, shared progress, trailing row
status, cross-provider name and operation guards, themes, focus behavior and narrow layouts.

Excluded: Yahoo HTTP traffic, cookies/crumbs, current symbol inventory or prices, actual OHLCV bars,
retry/rate-limit behavior and backend endpoints. The nine-symbol catalogue and one-sample-per-day
coverage are deterministic mock metadata. They do not claim current Yahoo availability.

## Feature register

### YAHOO-ADD-001

- **product/screen**: SQX Data Manager / Add Yahoo data
- **sources**: DataSourceYahoo provider/Add module, template, controller, service, compiled jar and
  `internal/web/img/dm-yahoo.png`
- **trigger/controls**: Yahoo > Add Yahoo data; ticker textarea, postfix, Close and Save
- **preconditions/validation**: readable storage and no active job; recognized tickers, exact
  separators, bounded input/postfix, no duplicate input or globally reserved final names
- **transitions/outcome**: open/reset/edit/save, running/paused/cancelled/failed/completed/reload;
  persisted empty D1 Yahoo definitions with provider metadata
- **mock operation/persistence**: `parseYahooTickers`, `yahooDefinitions`, `useYahoo.startAdd`;
  `sqx-yahoo-data-v1`
- **status**: visual implemented; interaction implemented; state implemented
- **verification/gaps**: unit and browser lifecycle tests passed; bounded offline catalogue, no live
  lookup, native runtime was not executed

### YAHOO-DOWNLOAD-001

- **product/screen**: SQX Data Manager / Download Yahoo data for symbol or multiple
- **sources**: DataSourceYahoo Download module, template, controller and shared date-range directive
- **trigger/controls**: Yahoo > Download data for existing symbol; From/To, six presets,
  missing-only/overwrite, Close and Start download
- **preconditions/validation**: selected persisted Yahoo records, no clone or active target, valid
  ordered dates through today and within mock availability, writable storage
- **transitions/outcome**: configure/start/pause/resume/stop/fail/complete/reload; only selected Yahoo
  records receive synthetic coverage and trailing statuses
- **mock operation/persistence**: `yahooTargets`, `yahooDownloadRanges`, `useYahoo.startDownload`;
  `sqx-yahoo-data-v1` intervals and job
- **status**: visual implemented; interaction implemented; state implemented
- **verification/gaps**: mixed-provider selection, presets, overwrite, reload and storage failures
  passed; one synthetic sample per calendar day, no actual price data

## Verification

Focused results are recorded in `docs/yahoo-data-walkthrough.md`. Overall Data Manager coverage
remains Partial while backend and live-provider integration are absent.
