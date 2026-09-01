# Plugin Analysis Boundary

> **Feature ID:** `FEAT-PLUG-ISOLATE_ANALYSIS`
> **Status:** `Implemented`

## Domain

`plugins`

## Provides

- `plugins.isolate-analysis@1`

## Required Capabilities

None

## Optional Capabilities

- `plugins.sandbox-permissions@1`

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `max_input_handles` | `int` | `50` | Maximum number of input handles accepted in a single analysis request. |
| `enforce_staged_output_schema` | `bool` | `true` | When true, successful analysis output requires valid staged artifact metadata. |
| `max_parameter_bytes` | `int` | `1048576` | Maximum size in bytes of the JSON-encoded parameters payload. |

## Purpose

Constrain plugin analysis, metric, and filter execution by providing immutable read-only input handles and returning schema-validated staged output without direct database mutation.

## Requirements and Usage Scenarios

| Requirement | Harness scenario | Unit test |
| --- | --- | --- |
| `FR-PLUG-PASS_ARTIFACT_HANDLES` | `plugin_analysis_boundary.py::__main__` Scenario 1 | `tests/services/plugins/analysis_boundary/test_plugin_analysis_boundary.py::test_plug_pass_artifact_handles` |

Run the executable usage demonstration:

```bash
uv run python -m app.services.plugins.analysis_boundary.plugin_analysis_boundary
```

## Runtime Effects

- Validates that all supplied input handles are strictly read-only (`read_only=True`).
- Enforces parameter payload limits and handle counts to protect process memory.
- Produces schema-validated staged artifact outputs; direct persistent database mutation is prevented.

## Persistent State

None. This feature is stateless; output artifacts remain staged and are managed by consuming analytics workflows.

## Failure Behavior

- Exceeding the maximum handle limit or parameter byte limit returns `PLUGIN_VALIDATION_FAILED`.
- Non-read-only input handles return `PLUGIN_PERMISSION_DENIED`.
- Execution errors return `PLUGIN_SANDBOX_EXECUTION_FAILED`.
- Missing capability requests return `CAPABILITY_UNAVAILABLE`.

## Removal Behavior

Removing this feature withdraws `plugins.isolate-analysis@1`. Built-in analytics operations continue running; third-party analysis plugin execution becomes unavailable.

## Evidence

- Primary module executable usage harness: `app/services/plugins/analysis_boundary/plugin_analysis_boundary.py`
- Focused unit and feature tests: `tests/services/plugins/analysis_boundary/`
