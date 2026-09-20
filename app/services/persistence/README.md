# Persistence

> **Package:** `app/services/persistence/`
> **Status:** `Missing`
> **Last updated:** `2026-09-20`
> **Domain ID:** `D-PERSISTENCE`

This README is the domain's single source of truth for its boundary, feature and FR registry,
domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence,
and deletion behavior. Reference-product evidence is a requirement source, never implementation
evidence.

`PROJECT.md` owns system scope and cross-domain behavior. `ARCHITECTURE.md` owns universal
structure and runtime constraints. `AGENTS.md` owns contributor workflow. The
[Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md) owns the
complete single-file feature delivery checklist.

## Code-aligned implementation convention

Backend features use the simplified modular-monolith layout:

```text
app/services/persistence/
|-- README.md
|-- __init__.py
|-- workspace.py
|-- database.py
|-- artifacts.py
|-- databanks.py
|-- migrations.py
|-- retention.py
|-- parquet_store.py
`-- snapshots.py

app/contracts/persistence.py
app/services/persistence/persistence.py
tests/services/persistence/<feature>/
tests/examples/02_persistence.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/persistence.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

The domain layout follows a two-tier architectural structure:
1. **Core Persistence Services:** Modules implementing core storage infrastructure for artifacts, databanks, forward migrations, retention policies, partitioned columnar Parquet series, snapshots, and SQLite database lifecycles (`database.py`, `artifacts.py`, `databanks.py`, `migrations.py`, `retention.py`, `parquet_store.py`, `snapshots.py`). All schema, parameterized SQL, and transactions for this domain live in `app/services/persistence/persistence.py`.
2. **Domain-Specific Persistence Drivers:** In accordance with `ARCHITECTURE.md` Rule 7 (*"SQL/schema/transactions live only in app/services/persistence/<domain>.py"*), persistence modules serving other domains (such as `app/services/persistence/workspace.py` providing `persistence.workspace@1`) encapsulate consuming domain SQL schemas, transactions, atomic CAS transitions, and test isolation via `HARUQUANTAI_DB_PATH`.

A feature may be stateless, but it never accepts an unrestricted database connection. Every completed feature contributes a deterministic, offline, secret-safe example to `tests/examples/02_persistence.py`.

---

## 1. Purpose and boundary

### Purpose

Own durable mechanics, SQLite control-plane schemas and transactions, immutable artifact catalog/lineage, portable artifact package bundles, databanks, memberships, ranking storage, similarity deduplication, persisted column views, partitioned columnar Parquet time-series, and reference-safe retention.

### Owns

- SQLite WAL control-plane mechanics, foreign keys, busy timeouts, and forward migrations.
- Artifact catalog, content hashes (SHA-256), lineage graphs, staging, atomic publication, and portable package bundles (`.zip` container format with manifest and checksum integrity).
- Databank membership, annotations, copy/move/clear, deterministic ranking, bounded capacity admission/eviction, similar-strategy dismissal filtering, and persisted column view configurations (`.vw` projection schemas).
- Partitioned columnar market data time-series engine (Parquet/Zstd).
- Point-in-time database hot snapshots and backups (`VACUUM INTO`).
- Reference-safe retention and purge planning.

### Does not own

- Metric mathematical formulas, strategy quality policy, or task scheduling.
- Domain semantic decisions merely because their rows are stored.
- Direct UI layout rendering or transport protocols (owned by UI / Gateway).

### Shared contracts

The public boundary is `app/contracts/persistence.py`. Counterparty status never authorizes a
private implementation import.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `persistence.database@1` | `DatabaseService` | `1` | SQLite lifecycle and transactions |
| Missing | `persistence.artifacts@1` | `ArtifactStore` | `1` | Immutable artifact catalog and lineage |
| Missing | `persistence.databanks@1` | `DatabankStore` | `1` | Databanks, memberships, annotations, and ranking |
| Missing | `persistence.migrations@1` | `MigrationService` | `1` | Forward schema migration and compatibility |
| Missing | `persistence.retention@1` | `RetentionService` | `1` | Reference-safe retention and purge planning |
| Missing | `persistence.parquet@1` | `ParquetStoreService` | `1` | Partitioned columnar market data storage engine |
| Missing | `persistence.snapshots@1` | `SnapshotService` | `1` | Atomic point-in-time database hot snapshots and backups |

### Persisted-state ownership

Semantic state remains feature-owned although database mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `persistence.v1` | `FEAT-PERSISTENCE-DATABASE` and registry peers | `sqlite` | Retain versioned records until explicit policy permits purge | `persistence.database@1` |

---

## 2. Feature registry and dependency direction

| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-PERSISTENCE-DATABASE` | SQLite lifecycle and transactions | `app/services/persistence/database.py` | `persistence.database@1` | None | Missing |
| `FEAT-PERSISTENCE-ARTIFACTS` | Immutable artifact catalog, lineage, and packaging | `app/services/persistence/artifacts.py` | `persistence.artifacts@1` | `persistence.database@1` | Missing |
| `FEAT-PERSISTENCE-DATABANKS` | Databanks, memberships, annotations, ranking, similarity dismissal, and column views | `app/services/persistence/databanks.py` | `persistence.databanks@1` | `persistence.database@1` | Missing |
| `FEAT-PERSISTENCE-MIGRATIONS` | Forward schema migration and compatibility | `app/services/persistence/migrations.py` | `persistence.migrations@1` | `persistence.database@1` | Missing |
| `FEAT-PERSISTENCE-RETENTION` | Reference-safe retention and purge planning | `app/services/persistence/retention.py` | `persistence.retention@1` | `persistence.artifacts@1` | Missing |
| `FEAT-PERSISTENCE-PARQUET` | Partitioned columnar market data store | `app/services/persistence/parquet_store.py` | `persistence.parquet@1` | None | Missing |
| `FEAT-PERSISTENCE-SNAPSHOTS` | Point-in-time database hot snapshots and backups | `app/services/persistence/snapshots.py` | `persistence.snapshots@1` | `persistence.database@1` | Missing |

> **Note on Domain Persistence Drivers:** Physical modules implementing cross-domain persistence (such as `app/services/persistence/workspace.py` providing `persistence.workspace@1`) are registered under their consuming domain's capability lifecycle while executing within the persistence physical boundary.

Dependencies point to public contracts, never implementation modules:

```mermaid
flowchart LR
    Consumer["Consuming feature"] --> Contract["Versioned public capability"]
    Provider["D-PERSISTENCE feature"] --> Contract
    Provider --> Context["FeatureContext-managed effects"]
    Provider --> Persistence["Domain persistence boundary"]
```

Removing one module and registry entry withdraws only its capability. Required consumers become
attributed `BLOCKED`; operation-gated consumers refuse only the affected operation. Retained
state is never purged implicitly.

---

## 3. Domain workflows

### `WF-PERSISTENCE-PUBLISH` — Atomically publish and catalog an artifact

- **Lead owner:** `FEAT-PERSISTENCE-ARTIFACTS`
- **Participants:** Domain producer, database, artifact filesystem, and lineage catalog.
- **Input boundary:** Contained staged payload, schema/media type, producer/run metadata, and parent identities.
- **Output boundary:** Validated immutable artifact identity and catalog receipt.
- **Failure boundary:** Validation/hash/promotion/catalog failure rolls back visibility; staged data remains quarantined or is safely cleaned.
- **Acceptance:** `ATW-PERSISTENCE-PUBLISH-001`

---

## 4. Feature specifications

The following contract applies to every registered feature; domain-specific semantics are in
Section 9.

### `database.py` — `FEAT-PERSISTENCE-DATABASE`

> **Feature ID:** `FEAT-PERSISTENCE-DATABASE` (representative registry entry)
> **Status:** `Missing`
> **Owner module:** `app/services/persistence/database.py`

#### Purpose

Provide sqlite lifecycle and transactions. Other registry entries follow the same lifecycle and
evidence obligations without merging their responsibilities into this module.

#### Capability declarations

- **Provides:** `persistence.database@1`
- **Requires:** None
- **Optional / operation-gated:** only capabilities explicitly declared by the feature; absence
  returns a typed unavailable result and does not silently substitute behavior.

#### Configuration and limits

Each owner module defines a slotted immutable `<Feature>Config`. No reference sample value is
promoted to a default without product approval.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject unknown/incompatible versions |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Must be positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject nonpositive/unbounded values |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability publication | `FeatureContext.provide(...)` | Withdrawn with feature scope |
| Tasks/subscriptions/resources | Managed `FeatureContext` API | Cancel/close in reverse order; failed start unwinds all effects |
| Durable mutation | Focused persistence protocol | Transaction rollback; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/persistence.py`
- **Namespace:** `persistence.v1`
- **Schema version:** `1` initially; forward migrations only
- **Retention and purge:** retain lineage-bearing records; purge only by explicit, reference-safe policy

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `database.py` | SQLite lifecycle and transactions; config, service, lifecycle, `SPEC`, factory | `DatabaseService` |
| Missing | `artifacts.py` | Immutable artifact catalog, lineage, and packaging; config, service, lifecycle, `SPEC`, factory | `ArtifactStore` |
| Missing | `databanks.py` | Databanks, memberships, annotations, ranking, similarity, and views; config, service, lifecycle, `SPEC`, factory | `DatabankStore` |
| Missing | `migrations.py` | Forward schema migration and compatibility; config, service, lifecycle, `SPEC`, factory | `MigrationService` |
| Missing | `retention.py` | Reference-safe retention and purge planning; config, service, lifecycle, `SPEC`, factory | `RetentionService` |
| Missing | `parquet_store.py` | Partitioned columnar market data time-series engine; config, service, lifecycle, `SPEC`, factory | `ParquetStoreService` |
| Missing | `snapshots.py` | Point-in-time database hot snapshots and backups; config, service, lifecycle, `SPEC`, factory | `SnapshotService` |
| Missing | `tests/examples/02_persistence.py` | Offline primary-purpose evidence | one `example_<NN>_<feature_slug>()` per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-PERSISTENCE-CONCURRENCY_INSERT` | Repeated insertion by canonical content identity is idempotent under concurrency. | Concurrent insert test |
| Missing | `FR-PERSISTENCE-COPY_MOVE` | Copy adds membership; move atomically adds target and removes source without duplicating content. | Rollback fixtures |
| Missing | `FR-PERSISTENCE-DETERMINISTIC_RANKING` | Ranking defines metric/version/scope/nulls/ties and evaluates deterministically. | Golden admission table |
| Missing | `FR-PERSISTENCE-SAFE_PURGE` | Purge refuses referenced content and requires an explicit audited operation. | Reference graph test |
| Missing | `FR-PERSISTENCE-SIMILARITY_FILTER` | Configurable similarity filtering compares candidate strategy metrics against databank members and dismisses redundant candidates or replaces lower-fitness members. | Boundary tolerance fixtures (`SQX144-EV-000006`) |
| Missing | `FR-PERSISTENCE-CAPACITY_EVICTION` | Bounded databank capacity enforces deterministic admission gating and evicts the lowest-ranked strategy when capacity is exceeded and candidate fitness is superior. | Capacity boundary test |
| Missing | `FR-PERSISTENCE-PARQUET_STORE` | Partitioned columnar Parquet store provides partitioned storage (`symbol/timeframe/year.parquet`), idempotent upserts, and time-bounded range reads for bars and tick streams. | Parquet time-range benchmarks |
| Missing | `FR-PERSISTENCE-PACKAGE_BUNDLE` | Artifact store provides packaging and unpacking of portable strategy bundles with manifest verification, checksum integrity, and lineage preservation. | Package round-trip fixtures |
| Missing | `FR-PERSISTENCE-COLUMN_VIEWS` | Persisted column views configure visible metric projections, sample scopes (IS, OOS, Full), sub-results, and display formats for databank inspection. | View schema validation test |

#### Removal behavior

Physical removal withdraws the feature's capability and cancels its managed effects. Stored
artifacts remain readable by schema-aware tooling; operations requiring the missing capability
return an attributed unavailable result. Reinstall may resume only after schema and version checks.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/persistence.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/persistence.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence

| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-PERSISTENCE-001` | SQLite WAL stores control-plane metadata; Parquet/Zstd stores large immutable columns. | Storage topology | Owner-ratified E-T01 |
| Open | `DEC-PERSISTENCE-002` | Proprietary .sqx/.cfx byte compatibility is not claimed; open portable artifact bundles are supported. | Interoperability | Legal versioned fixtures |
| Accepted | `DEC-PERSISTENCE-003` | Similar-strategy dismissal evaluates configurable percentage tolerances on Net Profit, Trades, and Drawdown, retaining higher fitness. | Databank deduplication | Grounded in `SQX144-EV-000006` and E-O07 |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; a filename, bundled
sample value, or third-party function name is not proof of runtime semantics.

---

## 7. Tests and definition of done

```text
tests/services/persistence/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/02_persistence.py
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [ ] Stable feature and requirement IDs have one owner.
- [ ] Public contracts and exact `FeatureSpec` dependencies exist.
- [ ] Registration is explicit; imports have no runtime effects.
- [ ] Happy, invalid, boundary, unavailable, lifecycle, persistence, and removal tests pass.
- [ ] Numerical or stateful behavior has deterministic golden/fault fixtures.
- [ ] One offline usage example exists per completed feature.
- [ ] Domain status reflects repository evidence, not reference-product evidence.
- [ ] Architecture and full qualification gates pass.

---

## 8. Change process

1. Update this README and identify the exact feature/requirement scope.
2. Update `app/contracts/persistence.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/persistence.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Enable foreign keys, a bounded busy timeout, and short transactions. Raw connections never escape. Artifact writes stage inside an approved root, close and validate, hash, atomically promote, then catalog (`FR-PERSISTENCE-CONCURRENCY_INSERT`, `FR-PERSISTENCE-PACKAGE_BUNDLE`). Copy/move changes membership, not immutable strategy content (`FR-PERSISTENCE-COPY_MOVE`). Databank admission strictly enforces bounded capacity (`FR-PERSISTENCE-CAPACITY_EVICTION`) and deterministic ranking (`FR-PERSISTENCE-DETERMINISTIC_RANKING`). Configurable similarity dismissal compares trade count, net profit, and drawdown within specified tolerances (e.g. ±5%) and retains higher fitness (`FR-PERSISTENCE-SIMILARITY_FILTER`, `SQX144-EV-000006`); it is implemented only as a named configurable profile (E-O07), never as a universal constant. Market data time-series are stored in partitioned columnar Parquet files with Zstd compression (`FR-PERSISTENCE-PARQUET_STORE`, `DEC-PERSISTENCE-001`). Databank views persist column projections, metrics, and sample scopes independently of underlying rows (`FR-PERSISTENCE-COLUMN_VIEWS`). Database reset/drop/truncate is not recovery.
