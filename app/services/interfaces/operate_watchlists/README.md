# Operate Watchlists — FEAT-IFACE-OPERATE_WATCHLISTS

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run. The domain-level
> registry lives in `app/services/interfaces/README.md`.

## Purpose

Expose the account watchlist boundary for the Watchlists widget migration:
translate the ratified Interfaces watchlist contract (LIST / CREATE /
UPDATE / DELETE) onto the Workspace-owned manage-watchlists capability,
applying the standalone default account until the identity boundary (gap
G2) is ratified. The gateway never imports a Workspace implementation and
reports absence truthfully through the stable `CAPABILITY_UNAVAILABLE`
failure; workspace invariants (unique names, exactly-one-default, default
protection) surface as structured interface failures.

## Domain

interfaces

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| OperateWatchlistsCapability | `interfaces.operate-watchlists@1` |

## Required Capabilities

| Capability bundle | Runtime identifier |
| --- | --- |
| ManageWatchlistsCapability | `workspace.manage-watchlists@1` |

## Optional Capabilities

None.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `default_account_id` | string | `"local"` | Standalone account applied to every request until identity (G2) is ratified. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Resolves the required `workspace.manage-watchlists@1` provider through
  `FeatureContext`; absence fails the mount closed (`BLOCKED`).
- Runs no background tasks and holds no buffers; each request translates
  to exactly one provider operation.
- Registers exactly one scope cleanup callback (`gateway.close`) so later
  use fails closed; repeated disposal is safe.

## Persistent State

None. Durable watchlist state remains owned by the Workspace feature.

## Functional Requirements

| Requirement | Requirement statement | Usage-harness scenario |
| --- | --- | --- |
| FR-IFACE-OWL-001 | Serve LIST with the seeded default watchlist projected. | seeded LIST |
| FR-IFACE-OWL-002 | Serve CREATE and map name collisions to structured failures. | collision mapped |
| FR-IFACE-OWL-003 | Serve UPDATE and DELETE preserving workspace invariants. | invariants passthrough |
| FR-IFACE-OWL-004 | Fail closed with CAPABILITY_UNAVAILABLE after disposal. | disposal failure |

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.operate_watchlists.gateway
```

## Failure Behavior

- Missing `workspace.manage-watchlists@1` provider blocks activation
  (`CapabilityUnavailableError` during mount); the feature provides
  nothing.
- Workspace validation failures (name collisions, default demotion or
  deletion, unknown ids) map to structured `InterfaceFailure` envelopes
  carrying the workspace code and detail.
- Use after disposal returns `CAPABILITY_UNAVAILABLE`; repeated disposal
  is a no-op.

## Removal Behavior

Disabling or removing the feature withdraws exactly the
`interfaces.operate-watchlists@1` capability: the served watchlist routes
translate absence to the stable 503 `CAPABILITY_UNAVAILABLE` envelope
while the Workspace watchlist store and its data remain untouched and
unrelated Interfaces features stay active.
