# Home workspace registry

`FEAT-HOME-DASHBOARD` owns the welcome landing workspace, original local guides,
host-persisted recent project summaries, read-only release checks, About and
explicit diagnostics. Target contracts are implemented and verified with isolated
stores and controlled providers under the owner-approved Phase 2.1 plan.
Broader repository qualification remains incomplete; no donor parity is qualified.

## Functional requirements

| ID | Exact public signature | Logging |
| --- | --- | --- |
| `FR-HOME-INDEX` | `Home.index() -> dict[str, Any]` | INFO completion; project/content failures propagate. |
| `FR-HOME-RECENT` | `Home.get_recent_projects(limit: int = 10) -> list[dict[str, Any]]` | INFO count; WARNING invalid limits/rows; ERROR persistence failure without payload. |
| `FR-HOME-UPDATES` | `Home.check_updates() -> dict[str, Any]` | INFO state; WARNING provider/contract failures without URLs or bodies. |
| `FR-HOME-ABOUT` | `About.about() -> dict[str, Any]` | INFO completion; host values are not independently qualified build provenance. |
| `FR-HOME-DIAGNOSTICS` | `About.diagnostics() -> dict[str, Any]` | INFO host status; host probes own detailed telemetry. |
| `FR-HOME-CLI` | `HomeCLI.format_output(data: Mapping[str, Any]) -> str` | INFO completion; existing CLI owns output and logging setup. |

## Decisions and contracts

- `DEC-HOME-HOST-REUSE`: AppHost injects its existing ServletConstants,
  ResourceMonitor, SettingsManager and SessionManager. HostPersistence alone
  owns SQLite access. No new schema, worker, global service or mutable singleton.
- `DEC-HOME-RECENT-PROJECTION`: read host_entities with entity_type `project`
  and scope `workspace`; payload contains a nonblank name (maximum 200 characters)
  and a supported workspace identifier. Return only id, name, workspace and
  last_activity from the UTC updated_at_utc envelope. Order by updated_at_utc
  descending then entity_id ascending. Limit must be an integer in 1..100;
  bool is rejected. Invalid rows within the selected window are skipped with a
  warning and are not replaced from later windows. Persistence failures propagate.
  No records are seeded or written. Existing producers must adopt this summary
  contract. Cards navigate to a workspace; specific project reopening is pending
  an owning project capability.
- `DEC-HOME-OFFLINE-CONTENT`: homeContent.json under the matching UI Home folder
  is the single original local text catalog, consumed by Python and bundled by
  Vite. Source-tree deployments must retain this file at its repository-relative
  location; standalone backend packaging is outside this phase. Guides remain
  readable without a connected host. No donor assets, remote iframe, video or
  progress synchronization is included.
- `DEC-HOME-RELEASE-FEED`: HARUQUANTAI_RELEASE_FEED_URL is read at UI/CLI host
  composition into optional AppHost.Config.home_release_feed_url. Unset reports
  unavailable. A typed ReleaseSource delegates to context-managed HTTP clients:
  HTTPS only; no credentials, query, fragment or redirects; five-second total
  budget; no retries; at most 256 KiB decoded content; sixty-second per-instance
  result cache. No host token, license or project data is transmitted.
  JSON must contain exactly latest_version, published_at, changelog and
  release_url. Publication time requires a timezone, release_url is HTTPS, and
  versions are stable three-integer dotted values. No other version ordering
  is invented. The payload returns state/reason, current_version, latest_version,
  update_available (nullable), changelog, release_url, published_at and checked_at.
  Missing provider => unavailable; unsupported contracts => unsupported;
  HTTP/network/timeout => error. Only available state establishes update status.
  Notes render as text. No update download or installer exists. A production
  feed is not configured or independently verified by this feature.
- `DEC-HOME-ABOUT-PROVENANCE`: About projects application, version,
  build_timestamp and runtime from the host, with metadata_source `host-reported`.
  No license provider is registered; license reports unavailable with a reason.
  No donor entitlement, owner data, keys or hardware identifiers are exposed.
  Host version 1.0.0 and the project package version 2.1.0 remain distinct;
  independent build provenance is unresolved.
- `DEC-HOME-HTTP-BOUNDARY`: GET /home, /home/recent-projects?limit=10,
  /home/updates, /home/about and /home/diagnostics reuse host response envelopes,
  session verification and error handling. With host authentication enabled,
  settings:read protects ordinary reads and diagnostics:read protects diagnostics.
  Invalid query limits are 422, missing/expired session is 401, denied scope is
  403. Diagnostics runs only on request and delegates database/memory/storage
  probes (including host writeability probes) and configured workspace paths.
  UI requests cancel on session changes/unmount; private panels are hidden when
  disconnected. No update check is automatically sent on Home load.

## Evidence and remaining qualification

[home-inventory.json](../../../docs/dev/evidence/home-inventory.json) independently
pins the eight Home/About donor artifacts. The original P00 manifest remains
byte-identical. The validator merges both explicit inventories for source checks
and donor reconciliation, rejects conflicting pins, and validates owner-source
fingerprints. In the Home manifest, donor/encrypted/template totals describe its
bounded artifact list; plugin/snippet counts describe the shared reference cohort.

Controlled checks passed: 35 Home backend tests, two host/CLI integration tests,
13 Home inventory/ownership tests, 504 UI unit tests and five Home browser tests.
Home Python modules reached 100% branch-aware coverage in the full test run.
Repository-wide qualification still fails: 22 reference tests cannot load an
older missing document, application-wide coverage is 56.49% against an 80% floor,
and CI encounters an unrelated strict-typing error in host settings tests.
Thresholds and historical records have not been weakened to hide these results.

See [the ledger](../../../docs/dev/evidence/reimplementation.json) for atomic
source-backed observations and target decisions, and the approved plan/walkthrough
under `.agents/logs/20261021_152849_apphome_landing/`. Static donor artifacts do not
establish runtime parity. Historical evidence records 000005/000006 and one
manifest repository source already fail source/artifact resolution; this task
does not rewrite that history. Release/license availability and exact saved
project reopening remain explicitly limited as described above.
