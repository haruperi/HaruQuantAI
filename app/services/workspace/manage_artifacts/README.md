# FEAT-WS-MANAGE_ARTIFACTS — Manage Artifacts

> **Feature ID:** `FEAT-WS-MANAGE_ARTIFACTS`
> **Status:** `Implemented` — terminal Executor evidence recorded; independent Reviewer authority pending.
> **Owner specification:** [`app/services/workspace/README.md`](../README.md) §4.3
> **Public contract:** [`app/contracts/workspace/artifacts.py`](../../../contracts/workspace/artifacts.py)

Publish and retain immutable artifact bytes: staged validation and atomic
content-addressed publication with custody receipts, bounded authorized
downloads that re-verify the immutable checksum, and reference/legal-hold
retention with admitted, audited custody maintenance.

## Purpose

Deliver the bounded behaviors of `FR-TRC-WS-MANAGE_ARTIFACTS-001/002/003`
and `NFR-TRC-WS-MANAGE_ARTIFACTS-001` through the declared public
capability `workspace.artifacts@1`. Public callers exchange semantic
artifact identities and bounded grants; host filesystem paths never cross
the public boundary, and no public artifact reference exists before
verified bytes and durable custody state agree.

## Domain

`workspace`

## Provides

`workspace.artifacts@1`

## Required Capabilities

`workspace.persistence@1`

## Optional Capabilities

`orchestration.resource-admission@1`

Publication and custody maintenance are heavy operations that must obtain
a finite resource-admission lease before touching the custody root. When
the admission provider is absent, or its decision is queued/refused,
those operations fail closed with the typed
`ArtifactAdmissionUnavailableError`; inspection, grant
authorization/resolution, and reference/hold operations remain available.

## Configuration

| Key | Type / default | Purpose |
| --- | --- | --- |
| `database_path` | `Path`, default `<repo>/data/database/haruquantai.db` | Shared workspace database holding the feature-owned namespace tables. |
| `custody_root` | `Path \| None`, default derived `artifacts/` beside the database | Filesystem custody root for staging and content-addressed objects; staging and objects share one root so publication uses an atomic same-volume rename. |
| `max_artifact_bytes` | `int`, default `67108864` (64 MiB) | Finite maximum accepted payload size; larger requests fail validation. |
| `staging_max_age_seconds` | `int`, default `3600` | Age after which `STAGING_INCOMPLETE` staging becomes eligible for admitted cleanup. |
| `cleanup_batch_limit` | `int`, default `100`, maximum `10000` | Bound on objects examined or removed by one reconciliation run. |
| `grant_max_ttl_seconds` | `int`, default `600`, maximum `86400` | Maximum download-grant lifetime. |

Unknown keys and out-of-range values fail closed during configuration
parsing.

## Persistent State

Namespace `workspace.manage_artifacts`, schema version 1, retention
policy `RETAIN`, executed only through `workspace.persistence@1`
(`_persistence.py` owns all feature SQL; no raw connections):

- `artifact_publications` — immutable published catalog rows carrying the
  custody receipt fields, idempotency fingerprint, and per-workspace
  custody sequence.
- `artifact_staging` — crash-classification staging rows
  (`STAGING_INCOMPLETE`, `BYTES_READY_METADATA_PENDING`).
- `artifact_references` — semantic references that retain artifacts.
- `artifact_retention_state` — revision-fenced mutable retention state
  (revision, legal hold) used for CAS and grant generations.
- `artifact_grants` — durable bounded download grants.

Custody and cleanup audit receipts are appended as immutable evidence
records through `PersistenceCapability.append_evidence`. Committed
artifacts are retained across deactivate/reactivate; purge requires
explicit separate authorization.

## Runtime Effects

- Registers `workspace.artifacts@1` on mount through `FeatureContext`;
  withdraws it when the owning `FeatureScope` closes (teardown is
  idempotent and never purges committed custody state).
- Creates and maintains the custody root's `staging/` and `objects/`
  directories; opens custody files only inside bounded operations.
- Acquires and releases `orchestration.resource-admission@1` leases
  around publication and reconciliation; releases are best-effort logged.
- Operational logging uses `app.composition.logging.get_logger` with
  bounded structured fields (ids, counts, stable error codes); payloads
  and host paths are never logged.

## Failure Behavior

Typed outcomes on the public contract (`WorkspaceError` subclasses with
stable error codes): `ArtifactValidationError`
(`ARTIFACT_VALIDATION_FAILED`) for path-like identities, bad hashes,
byte-count mismatches, invalid schema declarations, and size-cap
violations; `ArtifactPublicationConflictError`
(`ARTIFACT_PUBLICATION_CONFLICT`) for idempotency or identity conflicts;
`ArtifactNotFoundError` (`ARTIFACT_NOT_FOUND`); `ArtifactAccessDeniedError`
(`ARTIFACT_ACCESS_DENIED`) for wrong principal/account/workspace and
forged or stale-generation grants; `ArtifactGrantExpiredError`
(`ARTIFACT_GRANT_EXPIRED`); `ArtifactIntegrityError`
(`ARTIFACT_INTEGRITY`) when published bytes are missing, corrupt, or
symlinked (fail closed, never reported valid); and
`ArtifactAdmissionUnavailableError`
(`ARTIFACT_ADMISSION_UNAVAILABLE`) when heavy operations cannot obtain
admission.

Crash safety: publication validates, stages with fsync, re-verifies the
staged file, marks bytes-ready durably, renames atomically inside the
custody root, then commits metadata in one transaction. A crash before
the rename leaves recoverable staging that is never advertised; a crash
after the rename is finalized by retry or reconciliation; published
metadata with missing bytes fails closed as an integrity incident.

Platform note (Windows is the primary platform): staged files are
`os.fsync`-ed and publication uses `os.replace` (atomic within one
volume). A directory fsync is attempted best-effort and skipped where the
platform disallows it; the residual window is closed by restart
reconciliation instead of assuming POSIX semantics.

## Removal Behavior

Disabling or physically removing this feature withdraws only
`workspace.artifacts@1` and its scoped contributions: the capability
becomes unresolvable, dependent operations observe the declared
unavailable outcome, and unrelated capabilities remain usable. Committed
artifact bytes, namespace tables, and evidence records are retained; no
cross-provider substitute is selected and no implicit purge runs.
Re-adding the provider re-publishes the capability over the retained
state.

## Usage

```powershell
uv run --frozen python -m app.services.workspace.manage_artifacts._usage
```

The offline demonstration exercises publication with receipt/checksum
verification, idempotent replay, typed invalid-hash refusal, bounded
grant authorization and checksum-verified resolution, reference removal
with retention, and scope close with retained committed custody state.

## Evidence

Acceptance manifest:
[`docs/dev/evidence/features/FEAT-WS-MANAGE_ARTIFACTS/acceptance.json`](../../../../docs/dev/evidence/features/FEAT-WS-MANAGE_ARTIFACTS/acceptance.json).
