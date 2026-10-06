# Host authority and P00 reference tooling

Status: P00 reference baseline; host runtime implementation is absent.

The host owns universal lifecycle, telemetry, identity/session authority, typed
capability discovery, transport, jobs and shared resource custody. Domain numerical
algorithms belong to their owning workspace/plugin. No service, active schema or
transport version is implemented or activated by this README.

[Project charter](../../docs/PROJECT.md) and [architecture](../../docs/ARCHITECTURE.md)
own product and structural authority. [Evidence procedure](../../docs/dev/evidence/README.md)
owns provenance. Current UI counterpart: `ui/app/host/README.md`.

## Registered P00 feature

| Identity | Responsibility | Status |
| --- | --- | --- |
| `FEAT-HOST-EVIDENCE` | Host-governed reference manifests, fixtures and qualification in tests/reference | Implemented tooling; static qualification recorded in walkthrough |

## Registered P00 requirements

| Identity | Python responsibility | Required logs |
| --- | --- | --- |
| `FR-HOST-EVIDENCE-ROOT-RESOLUTION` | `tests/reference/manifest.py`: typed `ReferenceRoots`, `resolve_roots()`; repository is explicit, donor root explicit/env, no machine-specific fallback. | DEBUG resolved logical labels; ERROR missing/invalid authority, never physical roots. |
| `FR-HOST-EVIDENCE-MANIFEST-VALIDATION` | `manifest.py`: typed artifact/manifest models and `load_manifest()`; bounded JSON, unique locators, valid hashes/counts/version/provenance. | DEBUG/INFO accepted counts; ERROR stable failure code. |
| `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION` | `manifest.py`: `verify_inventory()`; actual bytes/ZIP entries/resources against frozen manifest, exact cohorts and drift failures. | INFO counts/digests; ERROR mismatch logical locator, no data values. |
| `FR-HOST-EVIDENCE-FIXTURE-VALIDATION` | `tests/reference/fixtures.py`: typed `ReferenceFixture`/observation, `load_fixtures()`; static/runtime provenance, independent expected outputs, units/tolerance/failure metadata. | DEBUG/INFO accepted case IDs; ERROR schema/provenance failure. |
| `FR-HOST-EVIDENCE-LEDGER-INTEGRITY` | `tests/reference/validate.py`: `validate_evidence()`; current/history Draft schema, source relationships, IDs, clean-room flags, freshness, paths, executable-pass requirements. | INFO verification counts; ERROR bounded codes, never raw record content. |
| `FR-HOST-EVIDENCE-OWNERSHIP-GATES` | `validate.py`: `validate_ownership()`; active FR/FEAT/DEC ownership vs registry; proposals and missing owners retained as gaps; affected runtime qualification fails. | INFO disposition counts; WARNING gaps; ERROR attempted qualification without authority. |
| `FR-HOST-EVIDENCE-QUALIFICATION-CLI` | `validate.py`: `main()`; offline repository checks by default, explicit read-only `--check-donor`, return 0 valid baseline/1 invalid; typed issue results. | INFO lifecycle/summary; ERROR check failure, no silent CLI exit. |

Constructors and private helpers belong to their associated module FR. Python
reference utilities are tooling outside runtime app code. They configure no logging
or other I/O at import. A standard-library named logger is the approved temporary
adapter; API consumers explicitly configure handlers and the CLI configures them.

## Ratified decisions

Owner approved implementation plan version 1 with `APPROVED: EXECUTE` on 2026-10-06.

| Identity | Approved decision |
| --- | --- |
| `DEC-HOST-P00-AUTHORITY-RESTORATION` | Create reset-aware charter/architecture from inspected historical constraints. Current UI root is `ui/app`; backend paths are targets. Preserve SC-01..SC-05, host resource custody, exclusive domain ownership, typed slots and no peer SQL. Historical implemented labels, transport versions and active schemas confer no current authority. |
| `DEC-HOST-P00-HISTORICAL-EVIDENCE` | Archive the original 88-record ledger and its schema byte-for-byte at the exact historical paths below after clean-room/secret review. Keep original IDs, relationships and historical validation timestamps. Current ledger references the archive/commit/hash and allocates from 000089; historical passes never become fresh passes. |
| `DEC-HOST-P00-SCHEMA-EVOLUTION` | Current schema version 2 preserves atomic claim/source/location/fingerprint/classification/limitation/review/clean-room fields and strict extra-property rejection. Add host domain and descriptive identities, historical snapshot provenance, inspection method `bytecode_inspection`, and explicit static/runtime validation kind. Original schema version 1 remains unchanged in history. No broad removal of identifier or validation constraints. |
| `DEC-HOST-P00-REGISTRY-BOUNDARY` | Register only the new `FEAT-HOST-EVIDENCE` and its tooling FRs below in `app/host/README.md`. Map all 261 JAR/667 seed proposals and 17 resources to proposed owners without creating/ratifying other domain registries. Preserve current UI identities. `FEAT-HOST-JRT-FS` retains a JVM-only, no-Python-runtime disposition, not an implemented feature. |
| `DEC-HOST-P00-LOGGING-ADAPTER` | Until P01 restores the host logger, reference tools use an explicit standard-library named logger (as retained ci_check does). Expose/import `getLogger as get_logger` only in tooling; `logger = get_logger(__name__)`; no handlers/configuration at import. CLI configures logging explicitly. Verify structured FR event metadata with caplog. This is a bounded tooling exception, not approval for a host logging redesign. |
| `DEC-HOST-P00-VALIDATION-DEPENDENCY` | Add only dev dependencies `jsonschema>=4.26,<5` and `types-jsonschema>=4.25,<5` for full Draft 2020-12 validation and strict typing. Existing local jsonschema is 4.26.0 but undeclared/unlocked. Resolve/pin in uv.lock without upgrading unrelated direct dependencies. Solver failure or a required unrelated upgrade requires a plan iteration. No application dependency added. |
| `DEC-HOST-P00-BOUNDED-FIXTURES` | Reference JSON manifest/fixture reads are UTF-8, duplicate-key rejecting, maximum 4 MiB each, with explicit integer byte bounds. Validate root-relative forward-slash locators, containment after resolution, source/fixture fingerprints, versions, typed payloads and capture timestamps. Reject traversal, absolute/UNC/drive paths and resolved escapes; never write donor roots. These limits are target tooling decisions, not donor defaults. |
| `DEC-HOST-P00-RELEASE-GATES` | P00 releases reference infrastructure only. Static integer/count/hash/operation-order comparisons require exact equality; no blanket floating-point tolerance. Future numeric tolerances, dependency translations, activation/runtime tests and live effects need separately approved feature plans. Missing core behavior remains blocked; unavailable observed cases cannot be manufactured. |
| `DEC-HOST-P00-MODULE-HEADING` | Reconcile the sample heading in PYTHON_MODULE.md to `Key Capabilities:`; use the constitutional five-section docstring and descriptive FR labels in all concrete new Python modules. No change to contributor authority. |

## Future ownership and release boundaries

`FEAT-HOST-JRT-FS` is a proposed JVM-only disposition, not a registered implemented
Python feature. Other roadmap host FEAT/FR identities remain proposals until their
individual owner plans ratify complete behavior and contracts. No runtime plugin
registry is created by P00.

Shared databases, resource schemas, migrations, transactions and retention require
an explicitly ratified host capability. Plugins receive typed focused interfaces,
never raw connections or ad-hoc SQL authority. P00 opens no operational database.
Removing a future producer must preserve retained artifacts and unrelated behavior.

MainApp, AppSettings, CpuInfo and SQLib payload implementations remain unavailable.
Donor token logging and swallowed cleanup exceptions conflict with redaction and
non-silent failure authority; affected future translations need explicit decisions.
Do not fabricate settings precedence, CPU policy, product activation or startup.
