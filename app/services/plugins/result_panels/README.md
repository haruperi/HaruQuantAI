# Plugin Result Panels

> **Feature ID:** `FEAT-PLUG-RENDER_RESULT_PANELS`
> **Status:** `Implemented`

## Domain

`plugins`

## Provides

- `plugins.render-result-panels@1`

## Required Capabilities

None

## Optional Capabilities

- `plugins.register-contributions@1`

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `allowed_bridge_operations` | `tuple[str, ...]` | `("READ_RESULTS", "QUERY_DATA", "RECEIVE_MESSAGES")` | Permitted bridge operations between sandboxed panel and platform. |
| `enforce_secure_content_source` | `bool` | `true` | When true, rejects unsafe URI schemes (e.g. `javascript:`) or credentials. |
| `max_panels_per_query` | `int` | `100` | Maximum number of panel descriptors returned in a single query. |

## Purpose

Isolate result-panel frontend bundles behind a narrow read-only bridge with strict sandboxed browser boundaries and no control-plane credentials.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-PLUG-SANDBOX_RESULT_PANELS` | `plugin_result_panels.py::__main__` Scenario 1 | `tests/services/plugins/result_panels/test_plugin_result_panels.py::test_plug_sandbox_result_panels` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.plugins.result_panels.plugin_result_panels
```

## Runtime Effects

- Manages in-memory sandboxed result panel descriptors.
- Validates content source URIs to prevent malicious scheme execution or credential leakage.
- Limits bridge operations to declared safe channels (`READ_RESULTS`, `QUERY_DATA`, `RECEIVE_MESSAGES`).

## Persistent State

None. This feature is stateless; panel descriptors are contributed dynamically by active plugins and registered in the workspace session.

## Failure Behavior

- Unknown panel resolution queries return `PLUGIN_VALIDATION_FAILED` (status 404).
- Insecure content sources or disallowed bridge operations return `PLUGIN_PERMISSION_DENIED` (status 403).
- Exceeding query limits returns `PLUGIN_VALIDATION_FAILED` (status 400).
- Internal execution errors return `PLUGIN_SANDBOX_EXECUTION_FAILED` (status 500).

## Removal Behavior

Removing this feature withdraws `plugins.render-result-panels@1`. Built-in analytics views continue functioning normally while plugin-provided custom panels become unavailable.

## Evidence

- Primary module executable usage harness: `app/services/plugins/result_panels/plugin_result_panels.py`
- Focused unit and feature tests: `tests/services/plugins/result_panels/`
