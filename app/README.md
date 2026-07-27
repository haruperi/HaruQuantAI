# App

> **Package path:** `app`
> **Status:** `Completed`
> **Last updated:** `2026-07-27`

## 1. Purpose and Boundary

The root App package exposes the fail-closed runtime-profile and execution-route
compatibility boundary used during system initialization. It owns no domain
business behavior, persistence, broker connection, trading decision, or execution
authority.

## 2. Final Package Structure

```text
app/
|-- __init__.py
|-- README.md
`-- runtime.py
```

### Feature Registry

| Status | Feature | Owning module | Public API and contracts | Requirements | Usage evidence |
|---|---|---|---|---|---|
| Completed | `FEAT-APP-01` Runtime Profile and Execution Route Validation | `runtime.py` | `validate_runtime_configuration(*, runtime_profile: str, execution_route: str) -> StandardResponse[None]`; package export in `app/__init__.py` | `FR-APP-001` through `FR-APP-004`; `docs/PROJECT.md` runtime-profile and execution-route compatibility policy | `tests/system/unit/test_runtime.py`; `tests/system/integration/test_runtime_initialization.py`; `tests/unit/test_runtime_coverage.py` |

The root App package is outside `app/services/<domain>`, so the service-domain
module-folder and numbered-usage-program rule does not apply. Its public API is
still documented here once and exported explicitly through `app.__all__`.

## 3. Public Contract

### `validate_runtime_configuration`

```python
validate_runtime_configuration(
    *,
    runtime_profile: str,
    execution_route: str,
) -> StandardResponse[None]
```

Validates the system-level compatibility policy without performing business I/O
or mutating runtime state. A compatible pair returns `status="success"` with raw
`data=None`. An unknown, non-canonical, or incompatible pair returns
`status="error"`, raw `data=None`, and the centrally registered
`SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE` code. Submitted values are never copied into
the response or logs.

The response metadata identifies
`app.runtime.validate_runtime_configuration`, generates a canonical request ID,
uses monotonic execution timing, declares `risk_level="none"`, and marks the
operation read-only with no file, database, trade, or network capability.

## 4. Functional Requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Failure | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-APP-001` | Accept only the four authoritative runtime-profile and execution-route pairs and return the shared five-field response. | `validate_runtime_configuration` | Monotonic clock read, request-ID generation, and bounded operational logging | None for a compatible pair | `tests/system/unit/test_runtime.py::test_validate_runtime_configuration_accepts_compatible_pair` |
| Completed | `FR-APP-002` | Return unknown, non-canonical, or incompatible values as a structured failure while preserving the established code and message. | `validate_runtime_configuration` | Same as `FR-APP-001` | `SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE` | `tests/system/unit/test_runtime.py::test_validate_runtime_configuration_rejects_incompatible_pair`; `test_validate_runtime_configuration_rejects_unknown_or_noncanonical_value` |
| Completed | `FR-APP-003` | Attach canonical operation identity, generated request identity, monotonic duration, static risk, and complete side-effect metadata. | `validate_runtime_configuration` | Monotonic clock read and request-ID generation | Response-contract validation failure propagates | `tests/system/unit/test_runtime.py::test_validate_runtime_configuration_accepts_compatible_pair` |
| Completed | `FR-APP-004` | Keep rejected submitted values out of the value-free error response, extensions, and logs. | `validate_runtime_configuration` | Bounded value-free warning log | `SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE` | `tests/system/unit/test_runtime.py::test_validate_runtime_configuration_does_not_expose_submitted_values` |

## 5. Verification

- `tests/system/unit/test_runtime.py` verifies accepted, incompatible, unknown,
  and non-canonical values, exact raw data placement, structured failure
  evidence, required metadata, and value-free output.
- `tests/system/integration/test_runtime_initialization.py` verifies the package
  export and explicit status handling at the system initialization boundary.
- `tests/unit/test_runtime_coverage.py` provides complete branch coverage for the
  focused root operation.
