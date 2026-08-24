# Runtime Configuration

> **Feature ID:** `FEAT-WS-CONFIGURE_RUNTIME`
> **Status:** `Implemented`

## Domain

`workspace`

## Provides

- `workspace.configure-runtime@1`

## Required Capabilities

- `workspace.manage-workspaces@1` (initialized workspace access)

## Optional Capabilities

None

## Configuration

None

## Purpose

Validate settings, resource guards, launcher settings, and support profiles.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-WS-CONFIGURE_WORKSPACE` | `runtime_configuration.py::__main__` Scenario 1 | `tests/services/workspace/runtime_configuration/test_runtime_configuration.py::test_ws_configure_workspace` |
| `FR-WS-ENFORCE_STORAGE_GUARDS` | Scenario 2 | `test_ws_enforce_storage_guards` |
| `FR-WS-CONFIGURE_SERVER_RUNTIME` | Scenario 3 | `test_ws_configure_server_runtime` |
| `FR-WS-PUBLISH_RUNTIME_SUPPORT` | Scenario 4 | `test_ws_publish_runtime_support` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.workspace.runtime_configuration.runtime_configuration
```

## Runtime Effects

- Persists validated, versioned workspace settings in the
  `workspace_setting_versions` table of the workspace metadata database.
- Evaluates free-space and artifact-size guards for data import, backtest,
  and code-generation job admission without queueing over-limit jobs.
- Validates launcher/server bind, port, headless, authentication, and CPU /
  memory limit settings before UI launch (transient port probe, no server).
- Publishes the versioned runtime support profile and rejects unsupported
  host platforms.

## Persistent State

- Versioned workspace settings rows in the `workspace_setting_versions`
  table of the workspace metadata database (`workspace` namespace,
  schema version 1, retention `RETAIN`). No feature-owned migrations;
  the table is created by the workspace lifecycle base schema.

## Failure Behavior

- Invalid settings payloads raise `SETTINGS_VALIDATION_FAILED` with field
  errors and never increment the persisted settings version.
- Over-limit jobs receive a non-admitted guard decision reporting required
  versus available storage.
- Invalid or unavailable ports and non-loopback bindings without explicit
  opt-in plus `NONLOCAL_TOKEN` authentication fail before launch.
- Unsupported OS/architecture raises `RUNTIME_UNSUPPORTED` at startup.
- Removing this feature leaves workspace defaults readable while
  configuration changes and guarded job admission return
  `CAPABILITY_UNAVAILABLE`; the domain continues loading.

## Removal Behavior

Removing this feature makes configuration changes and guarded job admission
unavailable while workspace defaults remain readable; requests requiring the
removed capability return `CAPABILITY_UNAVAILABLE` and the domain continues
loading. Physical removal deletes `app/services/workspace/runtime_configuration/`
and `tests/services/workspace/runtime_configuration/`, removes the
`workspace.runtime_configuration` entry point and the
`workspace.configure-runtime@1` capability key, and reverts registry statuses
in `app/services/workspace/README.md` and `app/contracts/README.md`.
