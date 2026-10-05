# Historical Dataset Management

Feature: `FEAT-DATASET-MANAGEMENT`.
Owner: Data Manager -> Data, `HARUQUANTAI_ROOT/app/workspace/DataManager/Data/`.
Approval: version 1 Cohort A; owner message `APPROVED: EXECUTE`.

Feature responsibility: manage historical dataset identity, metadata, source/clone
relationships, visibility, selection, inspection, correction, quality, timezone
transformation, transfer and lifecycle. Instrument definitions, provider transport,
host jobs and persistent schemas retain their own owners.

## Implementation state and registry

Cohort A implements 13 synchronous Python operations over caller-supplied immutable
records. Each behavioral requirement owns its module, validation, result and logging.
`contracts.py` contains shared records only. `Data/__init__.py` explicitly exports
public operations and their input/result types; callers use package-level imports.
There is no manager framework, dispatcher or persistence adapter.

The table registers the approved feature roadmap. A means implemented target API;
B/C mean deferred, with no placeholder file or supported operation. B/C require a
new approved plan before implementation. Target tests do not establish SQX parity.

| FR | Own file | Contract / responsibility | SQX donor | Cohort |
| --- | --- | --- | --- | --- |
| `FR-DATASET-CATALOG-BROWSING` | `catalog_browsing.py` | Filter caller-supplied metadata by text, source, asset type, broker and group; explicit stable symbol/ID order; return dataset count. | `data.html`; `DMDataCtrl.js` filtering/grid | A |
| `FR-DATASET-SELECTION` | `selection.py` | Resolve stable IDs; exclude explicitly busy items; preserve requested order; reject unknown IDs; report excluded IDs. | Controller selection; service busy filter | A |
| `FR-DATASET-METADATA-EDITING` | `metadata_editing.py` | Validate rename, instrument association and broker-timezone compatibility; preserve ID and records; return changed metadata. Instrument facts are supplied, not fetched implicitly. | `dataEdit.html`; `onEditData` | A |
| `FR-DATASET-VISIBILITY` | `visibility.py` | Set explicit visible boolean; return metadata; no inversion based on UI column indices. | Controller checkbox; `onShowData` | A |
| `FR-DATASET-CLEARING` | `clearing.py` | Clear supplied series while retaining dataset identity/metadata; validate restrictions and source dependencies. | Delete popup; `onClearData` | A |
| `FR-DATASET-REMOVAL` | `removal.py` | Remove selected datasets from the supplied catalog after dependency/confirmation checks; report affected IDs. | Delete popup; `onRemoveData` | A |
| `FR-DATASET-RECORD-REVIEW` | `record_review.py` | Bounded pagination over stored records; rows, offset and total count. No timeframe resampling. | `onReviewData`, tick/OHLC listing | A |
| `FR-DATASET-DATE-NAVIGATION` | `date_navigation.py` | Return first record index with time >= requested time, or count at end; binary search with no duration estimate. | `onGetIndexForDate`, `seekReader` | A |
| `FR-DATASET-CHART-REVIEW` | `chart_review.py` | Return bounded chart-ready time/price or OHLC values; no rendering, smoothing or undocumented preview sampling. | `onReviewChart`, stock-data helpers | A |
| `FR-DATASET-RECORD-CORRECTION` | `record_correction.py` | Apply validated replacements/deletions by record index; preserve order; recalculate coverage/counts. Duplicate timestamps remain individually addressable. | `onSaveDataChanges`, worker `$4` | A |
| `FR-DATASET-QUALITY-ANALYSIS` | `quality_analysis.py` | Stored-bar checks with explicit interval/session-hour inputs; report gap/low/high/spike precedence, counts and detail rows. | Quality UI; `QualityChecker`, `DataProblemEvaluator` | A |
| `FR-DATASET-TIMEZONE-CLONING` | `timezone_cloning.py` | Clone metadata and records using explicit timezone options, target-local weekend filtering and explicit parent ID; reject clone-of-clone. | Clone action; `CloneToTimezoneJob`, `DataCloner` | A |
| `FR-DATASET-CSV-EXPORT` | `csv_export.py` | Stream stored ticks/bars to caller-provided text writer; explicit columns, separator, header and date bounds. Do not claim all SQX format compatibility. | CSV handlers/exporter/formats/items | A |
| `FR-DATASET-XML-TRANSFER` | `xml_transfer.py` | Metadata-only donor XML import/export, identity remapping and overwrite choices; concrete schema and safe parser first. | `onSave`, `onLoad`, `onConfirm` | B |
| `FR-DATASET-UPDATES` | `updates.py` | Selected/all updates through bounded provider capabilities; explicit overlap and normalization policy. | Update handlers/provider dispatch | B |
| `FR-DATASET-BMF-SETUP` | `bmf_setup.py` | Lookup/eligibility, agreement and dataset setup through an approved provider. | `addBrPopup.html`, controller, futures service | B |
| `FR-DATASET-JOB-CONTROL` | `job_control.py` | Owner-scoped submission/cancellation and supported lifecycle controls through host jobs. | Global and per-job action handlers | B |
| `FR-DATASET-PROGRESS` | `progress.py` | Correlated job progress, completion/failure and subscriber cleanup through the host transport. | Controller WebSocket processing; publishers | B |
| `FR-DATASET-MT4-EXPORT` | `mt4_export.py` | Verified terminal-compatible artifacts through isolated output paths. | MT4 handlers and job | B |
| `FR-DATASET-MT5-EXPORT` | `mt5_export.py` | Verified Tick/M1 outputs and approved spread handling. | MT5 handlers/job/exporter | B |
| `FR-DATASET-TIMEFRAME-TIMEZONE-CATALOGS` | `time_catalogs.py` | Expose approved timezone/timeframe catalogs; registration is owner-controlled. | `onAddTimeframe`, `onListTimezones` | B |
| `FR-DATASET-AUXILIARY-EXPORT` | `auxiliary_export.py` | Resolve purpose and contracts before deciding whether to implement. | `exportTick`, `exportM1`, `exportCDN` | B, research gate |
| `FR-DATASET-WORKSPACE-REGISTRATION` | `workspace_registration` (extension undecided) | Register Data workspace and actions with an actual shell contract. | `module.js`, servlet plugin | C |
| `FR-DATASET-WORKSPACE-PRESENTATION` | `workspace_presentation` (extension undecided) | Actual grid/dialog presentation and event bindings. | HTML/CSS and controller | C |

## Inputs, timing, state and ordering

Operations execute immediately when called and return `StandardResponse`; errors
have safe codes, and callers inspect `is_success` before `unwrap()`. There is no
background work, event transport, persistent state, provider call or UI binding.

Construct `Dataset` and `Catalog` from trusted typed inputs. Constructors reject
invalid identities, timeframes, zones, record types, non-finite numbers, negative
volume and unordered records. Finite malformed OHLC remains inspectable by quality
analysis. Validation errors at construction raise `ValueError` or `TypeError`;
operation rejections use responses. UTC milliseconds must fit Python's datetime
range. Equal timestamps retain input order. Symbols are validated without trimming
or case normalization. Counts and coverage derive from records.

Browsing combines filters and sorts by symbol then stable ID. Selection preserves
requested ID order and reports busy exclusions; an unknown ID or duplicate request
rejects the whole request. Metadata changes preserve records and identity; populated
records cannot silently move to a different broker timezone. Visibility uses an
explicit boolean and has no hidden checkbox inversion.

Clear and remove validate the complete supplied catalog before returning a proposed
changed catalog. They reject unknown IDs, duplicate requests and restricted data.
Clearing retains metadata and clone relationships. A referenced source requires
`confirm_sources=True`. Removal also requires every dependent clone to be explicitly
selected; confirmation never creates a hidden cascade. Inputs remain unchanged.

Review and chart operations bound each page to 10,000 records. Zero count and offsets
beyond the end return empty pages. They expose stored records; requested derived
timeframes fail explicitly. Charts return price/OHLC tuples, not a renderer.
Navigation returns the first index with timestamp >= the supplied UTC millisecond
value, or record count at end. Correction uses indexes so equal-time ticks remain
individually addressable; invalid indexes, edit/delete conflicts, wrong record kinds,
bad replacement OHLC or resulting decreasing timestamps reject the entire edit.

Quality takes an explicit interval and same-day session hours in the dataset zone.
Ticks and overnight sessions are unsupported. Classification order is gap, low,
high, spike. Spike evaluation starts after 30 prior absolute ranges, uses >= five
times their mean, and updates history even after defective bars. A zero history
mean classifies a flat current bar as a spike. Percentages use total record count
and truncate to three decimals. Gap handling excludes current Sundays and uses
explicit cross-day opening/closing bounds; it is not an exchange calendar. Inverted
missing-time bounds produce no gap. Timestamp/range overflow returns an error.

Named-zone cloning preserves UTC instants; fixed integer shifts (-23..23) explicitly
change timestamps and retain source timezone metadata. Exactly one option is required.
Weekend filtering uses the resulting dataset's local date. Clones preserve duplicate
order and require unique ID/symbol and an original parent; clone-of-clone is rejected.
Unknown aliases, timestamp overflow and restricted parents fail explicitly.

CSV validates options before writing to a caller-owned text writer. It supports
stored tick/bar columns, optional symbol, chosen column order, one-character
separator, header, precision 0..15 and inclusive UTC date bounds. It preserves actual
volume, uses `\n` newlines and leaves writer ownership to the caller. Successful
exports and writer failures report side effects. Failure may leave partial output;
`rows_written` counts completed data rows, excludes the header, and cannot indicate
bytes written before a writer raised. No rollback is claimed.

## API example

```python
from io import StringIO

from app.workspace.DataManager.Data import (
    BarRecord,
    Dataset,
    export_csv,
    review_records,
)

history = Dataset(
    "eurusd",
    "EURUSD",
    "EURUSD",
    records=(BarRecord(0, 1.0, 1.2, 0.9, 1.1, 25.5),),
)
page = review_records(history, count=100)
if page.is_success:
    rows = page.unwrap().rows
with StringIO() as output:
    exported = export_csv(history, output)
    if exported.is_success:
        csv_text = output.getvalue()
```

## Evidence and parity boundaries

Donor mappings above are static observations inspected on 2026-10-05 through direct
text and Java bytecode. Confidence is high for inspected handlers/fields, bounded
for deeper algorithms and unverified for runtime equivalence. Source fingerprint
and narrow research notes are in approved plan version 1. No proprietary source is
copied into this implementation.

Target decisions deliberately differ from donor heuristics: lower-bound navigation,
index-based edits, atomic batches, explicit session hours, aware UTC cloning and
preserved CSV volume. Neither these choices nor passing target tests imply parity.

Missing `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `app/services/` and the two canonical
evidence JSON files prevent verified global requirement/decision mappings and ledger
registration. Do not allocate evidence IDs or invent replacements. This README owns
only this approved local feature registry and implementation state.

Before any compatibility claim, run isolated donor and target fixtures, retain exact
inputs/options/outputs, fingerprints and execution timestamps, and compare metadata,
ordering, errors and emitted events. Required donor fixtures include filter/selection
refresh races; referenced-source removal and partial batches; sparse/duplicate date
search; malformed bars and 29/30/31-bar spike boundaries; inferred versus supplied
sessions, Sundays and cross-day gaps; DST gaps/folds, fractional offsets and EETUS;
equal-time correction; CSV vendor layouts, spread/volume rounding, date endpoints
and partial-write failures. Providers, XML and platform artifacts need their own
schema/format fixtures and ratified host capabilities before Cohort B.

## Verification and telemetry

Every public FR logs its requirement ID and success/error outcome through existing
host logging. Operations call the logger and `StandardResponse` directly at their
return points; there are no success/failure wrappers. Completion logs bounded counts, rejection logs a safe code, and CSV
writer failures log ERROR with completed-row count. No record payload or writer
exception text is emitted. The host owns sink configuration.

Synthetic tests cover each module and shared contracts. An autouse fixture configures
only temporary logs, verifies requirement/outcome emissions, rejects database access,
and checks that failure secrets never reach telemetry. Inputs are immutable, and
CSV output is caller-owned. No live database, junction, provider or UI is changed.

Run focused checks with:

```powershell
uv run ruff check app/workspace tests/workspace
uv run ruff format --check app/workspace tests/workspace
uv run mypy --explicit-package-bases app/workspace tests/workspace
uv run pytest tests/workspace/DataManager/Data --no-cov
```

Repository qualification: `uv run python scripts/ci_check.py`.
Qualified on 2026-10-05: 67 feature tests and 219 repository tests passed;
Ruff, formatting and strict mypy passed. Repository branch-aware coverage is
86.92%; the new dataset modules measured 100%. Coverage is not semantic or parity
proof. Actual results and residual risks are recorded in the task walkthrough. Full feature
release remains blocked on Cohorts B/C; this is a bounded in-memory Python build.
