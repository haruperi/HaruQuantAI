# Operate Identity — FEAT-IFACE-OPERATE_IDENTITY

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run. The domain-level
> registry lives in `app/services/interfaces/README.md`.

## Purpose

Expose the account identity boundary over the external interface: translate
the ratified Interfaces identity contract (REGISTER / LOGIN / ME / LOGOUT)
onto the Workspace-owned manage-accounts capability, applying the default
principal when unspecified. The gateway never imports a Workspace
implementation and reports absence truthfully through the stable
`CAPABILITY_UNAVAILABLE` failure; workspace registration and authentication
outcomes surface as structured interface failures.

## Domain

interfaces

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| OperateIdentityCapability | `interfaces.operate-identity@1` |

## Required Capabilities

| Capability bundle | Runtime identifier |
| --- | --- |
| ManageAccountsCapability | `workspace.manage-accounts@1` |

## Optional Capabilities

None.

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `default_principal` | string | `"trader"` | Fallback principal identity when unspecified. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Resolves the required `workspace.manage-accounts@1` provider through
  `FeatureContext`; absence fails the mount closed (`BLOCKED`).
- Runs no background tasks and holds no buffers; each request translates
  to exactly one provider operation.
- Registers exactly one scope cleanup callback (`gateway.close`) so later
  use fails closed; repeated disposal is safe.

## Persistent State

None. Account and session state remain owned by the Workspace feature.

## Failure Behavior

- Missing `workspace.manage-accounts@1` provider blocks activation
  (`CapabilityUnavailableError` during mount); the feature provides
  nothing.
- Workspace validation failures (duplicate registration, invalid credentials,
  expired sessions) map to structured `InterfaceFailure` envelopes
  carrying the workspace code and detail.
- Use after disposal returns `CAPABILITY_UNAVAILABLE`; repeated disposal
  is a no-op.

## Removal Behavior

Disabling or removing the feature withdraws exactly the
`interfaces.operate-identity@1` capability: served auth routes translate
absence to the stable 503 `CAPABILITY_UNAVAILABLE` envelope while the
Workspace account store and its tables remain untouched and unrelated
Interfaces features stay active.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.operate_identity.gateway
```
