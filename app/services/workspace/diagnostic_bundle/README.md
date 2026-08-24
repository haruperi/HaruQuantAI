# Diagnostic Bundle

> **Feature ID:** `FEAT-WS-BUILD_DIAGNOSTICS`
> **Status:** `Implemented`

## Domain

`workspace`

## Provides

- `workspace.build-diagnostics@1`

## Required Capabilities

- `workspace.manage-workspaces@1`
- `workspace.configure-runtime@1`

## Optional Capabilities

- `workspace.secure-local-access@1`

## Configuration

None

## Purpose

Produce a redacted diagnostic bundle.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-WS-BUILD_DIAGNOSTIC_BUNDLE` | `diagnostic_bundle.py::__main__` Scenario 1 | `tests/services/workspace/diagnostic_bundle/test_diagnostic_bundle.py::test_ws_build_diagnostic_bundle` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.workspace.diagnostic_bundle.diagnostic_bundle
```

## Runtime Effects

- Collects application versions, runtime platform, and metadata schema version.
- Inspects workspace directory structures, SQLite integrity, and job execution states.
- Extracts recent structured log entries and workspace configuration.
- Recursively redacts all secret tokens, passwords, and absolute user filesystem paths.
- Assembles findings into a checksummed zip archive with structured JSON manifests.

## Persistent State

None

## Functional Requirements

- `FR-WS-BUILD_DIAGNOSTIC_BUNDLE`: The system shall produce a redacted diagnostic bundle containing versions, configuration shape, recent structured logs, job states, and integrity findings.

## Failure Behavior

- Uninitialized workspace directories or corrupt databases are recorded in integrity findings without throwing unhandled exceptions.
- Packaging failures or filesystem write errors raise `DIAGNOSTIC_BUNDLE_FAILED`.
- Removing this feature disables diagnostic bundle exports while normal workspace execution continues.

## Removal Behavior

Removing this feature makes diagnostic export unavailable while normal execution continues; requests requiring the removed capability return `CAPABILITY_UNAVAILABLE` and the domain continues loading. Physical removal deletes `app/services/workspace/diagnostic_bundle/` and `tests/services/workspace/diagnostic_bundle/`, removes the `workspace.diagnostic_bundle` entry point and the `workspace.build-diagnostics@1` capability key, and reverts registry statuses in `app/services/workspace/README.md` and `app/contracts/README.md`.
