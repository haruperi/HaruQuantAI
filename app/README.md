# App

> **Package path:** `app`
> **Status:** `Completed`
> **Last updated:** `2026-07-23`

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
| Completed | `FEAT-APP-01` Runtime Profile and Execution Route Validation | `runtime.py` | `RuntimeConfigurationError`; `validate_runtime_configuration(*, runtime_profile: str, execution_route: str) -> None`; package exports in `app/__init__.py` | `docs/PROJECT.md` runtime-profile and execution-route compatibility policy; no separate `FR-APP-*` ID is assigned | `tests/system/unit/test_runtime.py`; `tests/system/integration/test_runtime_initialization.py` |

The root App package is outside `app/services/<domain>`, so the service-domain
module-folder and numbered-usage-program rule does not apply. Its public API is
still documented here once and exported explicitly through `app.__all__`.

## 3. Public Contract

### `RuntimeConfigurationError`

Raised when a runtime profile or execution route is unknown, non-canonical, or
an unsupported pairing.

### `validate_runtime_configuration`

```python
validate_runtime_configuration(
    *,
    runtime_profile: str,
    execution_route: str,
) -> None
```

Validates the system-level compatibility policy and fails closed with
`RuntimeConfigurationError`. It performs no I/O and mutates no runtime state.

## 4. Verification

- `tests/system/unit/test_runtime.py` verifies accepted, incompatible, unknown,
  and non-canonical values.
- `tests/system/integration/test_runtime_initialization.py` verifies the package
  export at the system initialization boundary.
