# Local Access and Health

> **Feature ID:** `FEAT-WS-SECURE_LOCAL_ACCESS`
> **Status:** `Implemented`

## Domain

`workspace`

## Provides

- `workspace.secure-local-access@1`

## Required Capabilities

- `workspace.manage-workspaces@1`

## Optional Capabilities

- `workspace.configure-runtime@1`

## Configuration

None

## Purpose

Issue local credentials and report health/readiness.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-WS-ISSUE_LOCAL_SESSION` | `local_access_health.py::__main__` Scenario 1 | `tests/services/workspace/local_access_health/test_local_access_health.py::test_ws_issue_local_session` |
| `FR-WS-REPORT_SYSTEM_READINESS` | Scenario 2 | `test_ws_report_system_readiness` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.workspace.local_access_health.local_access_health
```

## Runtime Effects

- Issues ephemeral, cryptographically secure local-session tokens to verified launcher clients.
- Enforces default loopback binding and denies unauthenticated or non-loopback access attempts.
- Maintains in-memory active session tokens with expiration and immediate revocation support.
- Exposes runtime health checks functional prior to workspace initialization or readiness.
- Exposes complete system readiness verifying schema migration, recovery status, and worker capacity while redacting secrets and absolute user paths.

## Persistent State

None

## Functional Requirements

- `FR-WS-ISSUE_LOCAL_SESSION`: The system shall issue an ephemeral local-session token only to a launcher-connected client and shall bind the API to loopback by default.
- `FR-WS-REPORT_SYSTEM_READINESS`: The system shall expose health, readiness, build, schema, and worker-capacity status without disclosing secrets or absolute user paths.

## Failure Behavior

- Unconnected clients or missing session tokens raise `SESSION_DENIED`.
- Expired session tokens raise `SESSION_EXPIRED`.
- Non-loopback request sources without authorization raise `NON_LOOPBACK_ACCESS_DENIED`.
- Requests requiring complete readiness when degraded return `SYSTEM_NOT_READY` or unready status with redacted reasons.
- Removing this feature prevents interactive local session issuance while offline domain libraries remain usable.

## Removal Behavior

Removing this feature makes the local interactive endpoint unadvertised and prevents local session issuance while offline domain libraries remain usable; requests requiring the removed capability return `CAPABILITY_UNAVAILABLE` and the domain continues loading. Physical removal deletes `app/services/workspace/local_access_health/` and `tests/services/workspace/local_access_health/`, removes the `workspace.local_access_health` entry point and the `workspace.secure-local-access@1` capability key, and reverts registry statuses in `app/services/workspace/README.md` and `app/contracts/README.md`.
