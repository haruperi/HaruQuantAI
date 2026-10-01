# Dukascopy source

Feature: `FEAT-DM-DUKASCOPY_ACQUISITION`; requirement `FR-DATA-001`.
Status: integration candidate. See the parent DataSource registry for current
implementation limits and historical qualification references.

This paired package owns direct/CDN acquisition, its UI, focused tests and
existing offline example. Its manifest moved from the UI directory to this
source-owned location without changing package identity or resource ownership.
The provider now offers `add-symbol`, `download`, `dashboard`, and `disclaimer`
commands through the same authenticated host routes as the UI.

The Python user API exports exactly `add_symbol`, `download_data`, and
`show_disclaimer` through `__all__`, matching the three Dukascopy dropdown actions
and reference script. All other module-defined functions are internal, including
CLI and dashboard helpers. Host discovery retains a `prepare` attribute aliasing
internal `_prepare`; that framework hook is excluded from the user exports.

Start the normal app host first, then run from the repository root:

```powershell
uv run python app/plugin/DataSource/dukascopy.py add-symbol --symbol GBPUSD --type M1 --broker dukascopy
uv run python -m app.plugin.DataSource.dukascopy download --symbols GBPUSD --start 2026-09-29 --end 2026-09-29 --type M1 --cdn STANDARD
```

Use `--url` for a different host port and `HARU_CLIENT_PASSWORD` when credentials
are required. `--store` must match the running host's configured market root;
provider CLI commands do not open a separate database or impersonate another source.
Broker names resolve to actual catalog IDs/postfixes. Repeated registrations reuse
definitions. Missing-mode retries use received coverage rather than invented rows.

Standard acquisition retries 429/500/502/503/504 and transport failures, attempts
HTTP after unavailable HTTPS, and retains successfully decoded chunks when others
are unavailable. Multi-year requests are processed in bounded batches with finite
deadlines. CLI downloads return exit 2 for partial/empty results, exit 1 for command
failure, and exit 0 for complete results; statuses explain retained rows.

Canonical storage keeps UTC millisecond timestamps, rounded uint64 M1 volume and
combined tick-side volume. Default CLI/Python results follow the reference's
store-enabled branch and reconstruct canonical data. For source precision, use
`--result-representation provider --output prices.parquet` or pass
`result_representation="provider"` to `download_data`. This explicit option is a
host-custodied adaptation of the reference's storage-disabled return branch.

Provider chunks use plugin-local `dukascopy.provider_m1` / `dukascopy.provider_ticks`
v1 Arrow schemas: float64 prices and float32 source-rounded volumes. Existing-only
chunks are explicitly canonical; separate historical volumes cannot be recovered.
Mixed MISSING results preserve those origins. Raw resources carry producer/version,
schema and request/range provenance, survive producer removal, and use existing host
retention. Reads verify custody and return at most 2,000 rows. Result handles last
for the current host session; durable generic resource references remain readable.
Each resource has at most 100,000 rows and the existing store's 16 MiB byte limit.
The existing host-wide 4,096-resource inventory bound can reject very large raw
requests; request canonical results when raw resources are unnecessary. Provider
exports use float64 volume columns for a stable file schema across mixed chunks;
raw float32 values are exactly representable there. Python raw frames retain source
numeric dtypes and promote mixed uint64/float32 volumes as pandas does.

Canonical scans now match the installed reference Polars branch, including Monday
weekly labels and UTC aggregation before timezone conversion. Download-candles
retains the reference's separate pandas aggregation behavior. The required Polars
dependency already existed; no dependency was added.

The DataManager CLI now uses public routes and is owned by its workspace. Logs and
clear-log have no published host contract and fail explicitly. Full release and
exhaustive live CDN equivalence are not inferred from focused tests. Exact commands,
source-bound results and qualification limitations are recorded in
`.agents/logs/20261001_dukascopy_parity_cli/`.

Download dialogs validate eligibility when selected and submitted. Rendering an
open dialog does not reject its own newly started job; the workspace remains
visible while host-polled progress and complete/partial/failed status are shown.
The progress owner is `dukascopy`. A running Python host must be restarted to load
provider/transport edits; browser hot reload alone does not reload backend code.

Terminal progress displays retain the host outcome: partial coverage is labelled
partially completed, and empty results finished without data. Processing 100% does
not imply full market coverage. Finished Dukascopy displays clear after ten seconds;
a newer job is protected. Clearing is local presentation state only and retains
stored market data and backend records. Another job may start immediately.
