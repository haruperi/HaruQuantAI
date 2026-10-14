# Host Platform Registry (`app/host`)

Status: Stage 0 (`P00`) reference qualification and evidence infrastructure active.
Host runtime services (`F01`) belong to Stage 1 (`1A`–`1G`) and are registered when their approved implementation plans execute.

[Project Charter](../../docs/PROJECT.md), [Architecture](../../docs/ARCHITECTURE.md),
[Evidence Procedure](../../docs/dev/evidence/README.md), and [AGENTS.md](../../AGENTS.md) govern authority.

## Registered feature

| Identity | Responsibility | Status |
| --- | --- | --- |
| `FEAT-HOST-EVIDENCE` | Host-governed reference manifests, fixtures, and clean-room ledger qualification in `tests/reference` | Implemented tooling (`Stage 0` / `P00`); static reference readiness verified; application runtime qualification belongs to owning Stage 1–7 features |
| `FEAT-HOST-PERSISTENCE` | Isolated SQLite WAL persistence and CRUD operations across all 25 operational database tables | Implemented runtime persistence (`Stage 1` / `1A`); WAL mode, schema DDL, and CRUD operations across host, data manager, and transport domains |

## Registered functional requirements

| Identity | Responsibility | Required logs |
| --- | --- | --- |
| `FR-HOST-EVIDENCE-ROOT-RESOLUTION` | Resolve explicit `SQX_REFERENCE_ROOT` and `HARUQUANTAI_ROOT` roots and contain relative locators without path traversal or fallback substitution. | DEBUG checks, INFO accepted roots, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-MANIFEST-VALIDATION` | Reject malformed, duplicate-key, nonfinite, oversized, or mistyped reference JSON; validate donor/repository manifest models. | DEBUG checks, INFO accepted counts, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-INVENTORY-RECONCILIATION` | Reconcile donor artifact SHA-256 fingerprints, repository reference document hashes, and exact directory counts (`internal/plugins`, `internal/libs/*.jar.enc`, `internal/extend/Snippets/SQ`). | DEBUG checks, INFO accepted totals, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-FIXTURE-VALIDATION` | Validate independent static/runtime fixture observations, exact outputs, UTC timestamps, source hashes, and provenance rules. | DEBUG checks, INFO accepted case counts, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-LEDGER-INTEGRITY` | Validate Draft 2020-12 schema v4, atomic `SQX145-EV-NNNNNN` records, monotonic ID allocation, source catalog bindings, reciprocal supersession/contradiction links, and pass artifacts. | DEBUG checks, INFO checked record counts, ERROR stable failure codes; structured `fr_id`; no physical paths or secret values. |
| `FR-HOST-EVIDENCE-OWNERSHIP-GATES` | Verify mapped `FEAT-*`, `FR-*`, and `DEC-*` identities against domain registries or explicit `proposed` status, and block premature runtime parity claims. | DEBUG checks, WARNING unresolved runtime authority, INFO checked mappings, ERROR stable failure codes; structured `fr_id`. |
| `FR-HOST-EVIDENCE-QUALIFICATION-CLI` | Execute offline evidence qualification by default and optional read-only `--check-donor` verification; emit structured outcome logs and nonzero exit codes on failure. | INFO start and completion status, ERROR failure diagnostics; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-CONNECT` | Establish SQLite connection with WAL journal mode, busy timeout, foreign key enforcement, and path containment. | DEBUG open and WAL status; ERROR connection failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-CREATE-SCHEMA` | Idempotently create and verify all 25 operational database tables. | DEBUG start; INFO completed table count; ERROR DDL failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-INSERT` | Parameterized record insertion across approved database tables. | DEBUG insert execution and lastrowid; ERROR constraint or table validation failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-READ-BY-PK` | Point query for single row by primary key or composite primary key. | DEBUG query and row match; ERROR query failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-LIST` | Parameterized record listing with filtering, ordering, and pagination bounds. | DEBUG query; INFO non-empty result count; ERROR query failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-UPDATE-BY-PK` | Atomic record update targeting primary key. | DEBUG update execution; WARNING 0 rows affected; ERROR execution failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-DELETE-BY-PK` | Parameterized record deletion targeting primary key. | DEBUG delete execution; WARNING 0 rows affected; ERROR execution failure; structured `fr_id`. |
| `FR-HOST-PERSISTENCE-DELETE-WHERE` | Parameterized record deletion targeting non-empty filter criteria. | DEBUG delete execution and affected count; ERROR execution failure; structured `fr_id`. |

## Ratified reference decisions

| Identity | Approved decision |
| --- | --- |
| `DEC-HOST-P00-AUTHORITY-RESTORATION` | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and owning `README.md` files define target authority; retained React UI surfaces do not establish backend availability or parity. |
| `DEC-HOST-P00-SCHEMA-EVOLUTION` | Strict schema version 4 binds `SQX_REFERENCE_ROOT` (`145-dev1`) and `HARUQUANTAI_ROOT`; atomic claims, classifications, limitations, source locations/hashes, target mappings, clean-room flags, and truthful validation states are mandatory. |
| `DEC-HOST-P00-REGISTRY-BOUNDARY` | Only `FEAT-HOST-EVIDENCE` is registered in `Stage 0`. Application features (`F01`–`F13`) remain `proposed` until their owning stage implementation plans ratify them in domain `README.md` files. |
| `DEC-HOST-P00-LOGGING-ADAPTER` | Reference tooling uses standard-library named loggers (`get_logger(__name__)`), structured `fr_id` extras, and stable redacted error codes without import-time I/O or handler mutation. |
| `DEC-HOST-P00-VALIDATION-DEPENDENCY` | Draft 2020-12 JSON Schema validation uses the locked `jsonschema` development dependency with format checking enabled. |
| `DEC-HOST-P00-BOUNDED-FIXTURES` | UTF-8 JSON reads reject duplicate keys, nonfinite numbers (`NaN`, `Infinity`), and payloads exceeding `4 MiB`. Relative forward-slash locators reject traversal (`..`), drive letters, UNC paths, and symlink escapes. |
| `DEC-HOST-P00-RELEASE-GATES` | Static SHA-256 hashes and directory/file counts require zero tolerance (`tolerance = 0`). Static qualification never establishes runtime execution or numerical parity. |
| `DEC-HOST-P00-MODULE-HEADING` | Every concrete Python module follows `docs/templates/PYTHON_MODULE.md` with five standardized docstring sections (`Description`, `Purpose`, `Key Capabilities`, `Python API Usage`, `CLI Usage`) and non-silent `FR-*` logging. |
| `DEC-HOST-SQX145-REFERENCE` | Logical root `SQX_REFERENCE_ROOT` (accepting `SQX_145_REFERENCE_ROOT` as environment alias) identifies the read-only SQX-145 reference installation. Record IDs follow `SQX145-EV-NNNNNN` monotonically without reuse. |
| `DEC-HOST-P00-CLOSURE-BOUNDARY` | Stage 0 (`P00`) qualifies reference infrastructure, donor artifact hashes, and clean-room ledger integrity. Stage 1–7 runtime implementation and numerical parity are gated by their respective stage plans. |
