# Manage Watchlists — FEAT-WS-MANAGE_WATCHLISTS

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run.

## Purpose

Own the durable account-watchlist store for the workstation: standalone
`users`, `api_watchlists`, and `watchlist_items` tables (legacy-compatible
STRICT schema) with the exactly-one-default-per-account invariant, unique
(account, name), curated default seeding on first read, complete ordered
item-list replacement on update, and typed failures for name collisions,
default demotion/deletion, and missing watchlists. The service exposes the
operation-discriminated LIST / CREATE / UPDATE / DELETE capability consumed
by the Interfaces watchlist gateway; it owns no HTTP surface.

## Domain

workspace

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| ManageWatchlistsCapability | `workspace.manage-watchlists@1` |

## Required Capabilities

None. The store is self-contained SQLite.

## Optional Capabilities

None.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | path string or null | `null` | SQLite file; null uses a private in-memory database. |
| `auto_migrate` | boolean | `true` | Create/verify the schema on mount. |
| `default_account_id` | string | `"local"` | Standalone account applied until identity (G2) is ratified. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Opens one SQLite connection (file or in-memory) with foreign keys ON.
- Creates the `users`, `api_watchlists`, and `watchlist_items` tables when
  `auto_migrate` is enabled; creates the standalone account row on first
  use; seeds one curated default watchlist on the account's first LIST.
- Registers exactly one scope cleanup callback (`service.close`); repeated
  disposal is safe.

## Persistent State

`workspace.manage_watchlists` (schema version 1, RETAIN): the standalone
`users`, `api_watchlists`, and `watchlist_items` tables in the configured
SQLite database. Uninstall does not purge data; retention and any purge
follow explicit owner policy.

## Functional Requirements

| Requirement | Requirement statement | Usage-harness scenario |
| --- | --- | --- |
| FR-WS-WL-001 | Seed one curated default watchlist per fresh account on first LIST. | seeding invariant |
| FR-WS-WL-002 | Enforce unique (account, name) on create and rename. | uniqueness enforced |
| FR-WS-WL-003 | Enforce exactly one default per account on promote. | default promote |
| FR-WS-WL-004 | Reject deleting or demoting the current default. | default deletion blocked |
| FR-WS-WL-005 | Replace the complete ordered item list on update, preserving known asset classes. | item replacement |
| FR-WS-WL-006 | Scope every operation to the owning account. | account scoping |

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.workspace.manage_watchlists.manage_watchlists
```

## Failure Behavior

- Name collisions return `WORKSPACE_VALIDATION_FAILED` with the offending
  name and HTTP-equivalent 409.
- Deleting or demoting the current default returns
  `WORKSPACE_VALIDATION_FAILED` with remediation guidance.
- Unknown watchlist ids return `WORKSPACE_NOT_FOUND`.
- The SQLite connection is closed on scope disposal; failures surface as
  sqlite errors and never partially commit (transactional statements).

## Removal Behavior

Disabling or removing the feature withdraws exactly the
`workspace.manage-watchlists@1` capability: watchlist operations become
unavailable (the Interfaces gateway serves the stable 503
`CAPABILITY_UNAVAILABLE`), while the durable tables and their data remain
untouched (RETAIN) and unrelated workspace features stay active.
