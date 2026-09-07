# Operate Settings — FEAT-IFACE-OPERATE_SETTINGS

> Runtime-validated feature specification. `scripts/validate_feature_docs.py`
> checks this document against `manifest.py` on every run. The domain-level
> registry lives in `app/services/interfaces/README.md`.

## Purpose

Expose the system settings and administrator boundary over the external
interface: translate the ratified Interfaces settings contract (READ_SYSTEM /
UPDATE_SYSTEM / READ_MANIFEST / READ_CREDENTIALS / UPDATE_CREDENTIAL /
READ_BRIDGE_RUNTIME) onto the Workspace-owned administer-settings capability.
The gateway never imports a Workspace implementation and reports absence
truthfully through the stable `CAPABILITY_UNAVAILABLE` failure; workspace
validation and persistence outcomes surface as structured interface failures.

## Domain

interfaces

## Provides

| Capability bundle | Runtime identifier |
| --- | --- |
| OperateSettingsCapability | `interfaces.operate-settings@1` |

## Required Capabilities

| Capability bundle | Runtime identifier |
| --- | --- |
| AdministerSettingsCapability | `workspace.administer-settings@1` |

## Optional Capabilities

None.

## Configuration

None.

## Runtime Effects

- Resolves the required `workspace.administer-settings@1` provider through
  `FeatureContext`; absence fails the mount closed (`BLOCKED`).
- Runs no background tasks and holds no buffers; each request translates
  to exactly one provider operation.
- Registers exactly one scope cleanup callback (`gateway.close`) so later
  use fails closed; repeated disposal is safe.

## Persistent State

None. Durable settings state remains owned by the Workspace feature.

## Failure Behavior

- Missing `workspace.administer-settings@1` provider blocks activation
  (`CapabilityUnavailableError` during mount); the feature provides
  nothing.
- Workspace validation failures map to structured `InterfaceFailure`
  envelopes carrying the workspace code and detail.
- Use after disposal returns `CAPABILITY_UNAVAILABLE`; repeated disposal
  is a no-op.

## Removal Behavior

Disabling or removing the feature withdraws exactly the
`interfaces.operate-settings@1` capability: served settings routes translate
absence to the stable 503 `CAPABILITY_UNAVAILABLE` envelope while the
Workspace settings store and its tables remain untouched and unrelated
Interfaces features stay active.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.interfaces.operate_settings._usage
```
