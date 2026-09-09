# Mandate Enforcement (`FEAT-AGT-ENFORCE_MANDATE`)

## Purpose

Deliver a focused, stateless, fail-closed authority-narrowing capability for Mandate Enforcement behind public capability `agentic.mandate@1`. Validate immutable mandate identity/integrity, half-open effective temporal interval (`effective_at <= now < expires_at`), objectives, enabled roles/features, environment/account/asset scope, and finite budgets. Structurally prevent or reject grants of broker credentials, order construction, Risk approval, kill-switch clearing, deployment, or receiver authority.

## Domain

`agentic`

## Provides

- `agentic.mandate@1`

## Required Capabilities

- `workspace.manage-accounts@1`
- `workspace.administer-settings@1`

## Optional Capabilities

None.

## Configuration

Strict configuration without ad-hoc keys. Unknown configuration keys fail closed with `ValueError`.

## Runtime Effects

- Pure stateless evaluation; registers scope disposal callback to release references.
- No workers, background tasks, leases, listeners, or timers created.

## Persistent State

None (`State ownership: None`). Feature does not own SQL tables or a private durable namespace.

## Failure Behavior

- Tampered digest fails closed with `INVALID` outcome.
- Future or expired interval returns `REFUSED`.
- Prohibited authority request returns `DENIED` with zero receiver calls.
- Missing configuration or unavailable dependency returns `UNAVAILABLE`.

## Removal Behavior

Disabling or unmounting the feature withdraws `agentic.mandate@1`. Unrelated Workspace, broker, and risk capabilities remain fully operational; only Agentic consumers requiring mandate validation fail closed.

## Evidence

Run the bounded offline usage demonstration with:

```powershell
uv run python -m app.services.agentic.enforce_mandate._usage
```

Acceptance evidence manifest:
`docs/dev/evidence/features/FEAT-AGT-ENFORCE_MANDATE/acceptance.json`
