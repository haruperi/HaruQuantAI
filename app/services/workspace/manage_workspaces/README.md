# Manage Workspaces

> **Feature ID:** `FEAT-WS-MANAGE_WORKSPACES`
> **Status:** `Implemented and verified`
> **Capability:** `workspace.manage-workspaces@1`

This root Workspace feature initializes or reopens a stable local workspace,
enforces one atomic writer fence while admitting explicit read-only sessions,
creates bounded checksummed backups, restores only after isolated verification,
and reconciles journalled publication crashes without deleting committed bytes.

## Public API

The canonical operation-discriminated contract is
`app/contracts/workspace/manage_workspaces.py`. Every request carries request,
actor, account, workspace, and optional expected-revision/fence context. The
provider is `ManageWorkspacesService.manage_workspaces`; legacy granular methods
remain compatibility adapters on the same provider rather than a second owner.

The package registers through the `haruquantai.features` entry-point group as
`workspace-manage-workspaces`. It has no feature dependencies. Mount registers
the capability and one scope-owned close callback; close releases only writer
fences acquired by that provider instance.

## Configuration

| Key | Type | Default | Bounds |
| --- | --- | --- | --- |
| `auto_migrate` | `bool` | `true` | exact boolean |
| `busy_timeout_seconds` | `float` | `5.0` | 0.1–60 |
| `staged_grace_period_seconds` | `float` | `86400.0` | 0–31536000 |
| `max_manifest_files` | `int` | `10000` | 1–100000 |
| `max_backup_bytes` | `int` | `10737418240` | 1–1099511627776 |

Unknown keys, implicit boolean/numeric coercions, and out-of-range values fail
closed. Manifest and configuration key parity is tested.

## Persistence and safety

The feature-local `_persistence.py` is the documented bootstrap owner for
`database/haruquantai.db`; SQLite connections never escape it. Schema version 2
retains the version-1 checksum and adds account scope, immutable artifact paths,
publication recovery records, request/audit metadata, and ordered migration
checksums. The filesystem layout is `database/`, `artifacts/objects/`, `staging/`,
`logs/`, `cache/`, `exports/`, and `backups/`.

Backup manifests cover the consistent SQLite snapshot and every catalogued
immutable artifact. File count, total bytes, canonical paths, regular-file
containment, member hashes, sizes, database integrity, workspace identity,
account scope, and catalogue references are checked before atomic restore
promotion. Checksum verification is mandatory even when an older compatibility
caller supplies `verify_checksums=False`.

Recovery acts only on journalled publications. Pre-promotion staging bytes are
discarded; promoted-but-uncatalogued bytes are retained as `ORPHANED` custody and
reported; committed references to missing or partial bytes fail as corruption.

## Operational logging

The feature emits structured events through
`app.composition.logging.get_logger`; it never configures handlers or global
logging. Events cover request admission/completion/failure, initialization/open,
fence acquisition/denial/release, schema verification, backup, restore, and
recovery. Records may contain opaque request/workspace IDs, operation, mode,
revision, bounded counts, stable error code, and exception type. They never
contain paths, workspace names, actor/account IDs, fence tokens, hashes,
manifest contents, recovery findings, or raw exception messages.

## Acceptance and usage

- `AT-WS-MANAGE_WORKSPACES-001`:
  `tests/services/workspace/manage_workspaces/test_traceability.py::test_trc_manage_workspaces_001`
- `AT-WS-MANAGE_WORKSPACES-002`:
  `tests/services/workspace/manage_workspaces/test_traceability.py::test_trc_manage_workspaces_002`
- `AT-WS-MANAGE_WORKSPACES-003`:
  `tests/services/workspace/manage_workspaces/test_traceability.py::test_trc_manage_workspaces_003`
- `ATN-WS-MANAGE_WORKSPACES-001`:
  `tests/services/workspace/manage_workspaces/test_lifecycle.py::test_trc_manage_workspaces_nfr_001`
- Logging hygiene:
  `tests/services/workspace/manage_workspaces/test_logging.py`

Run the bounded offline example with:

```powershell
uv run python -m app.services.workspace.manage_workspaces._usage
```

## Removal behavior

Removing this package and its entry point withdraws only
`workspace.manage-workspaces@1`. Consumers receive capability unavailability;
no substitute provider is selected. Existing workspace directories, databases,
immutable artifacts, and acceptance evidence remain unchanged until a separately
authorized retention/purge operation owns their disposition.

## Domain

`workspace`

## Provides

`workspace.manage-workspaces@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Purpose

Open, recover, back up, and restore one fenced local workspace while preserving
committed metadata and immutable artifact references.

## Runtime Effects

Mount registers `workspace.manage-workspaces@1` and one scope-owned close callback.
An admitted writer owns a bounded SQLite handle and writer fence until explicitly
closed; read-only sessions never acquire that fence.

## Failure Behavior

Invalid paths, stale fences, corrupt manifests, incompatible migrations, partial
publications, and failed restore verification return typed failures before an active
workspace is replaced. Cleanup does not delete committed bytes.

## Removal Behavior

Removal withdraws only `workspace.manage-workspaces@1`, releases provider-owned
resources, and retains workspace directories, databases, artifacts, and evidence.

## Persistent State

Namespace `workspace`, schema version 2, retention policy `RETAIN`: workspace
metadata, ordered migrations, leases, publication recovery, and backup manifests.
