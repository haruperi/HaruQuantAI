# App

> **Package path:** `app`
> **Status:** `Completed`
> **Last updated:** `2026-09-01`

## 1. Purpose and Boundary

The root App package houses the application substrate, service domains, kernel, composition engine, and executable runtime entrypoint (`app/main.py`).

## 2. Final Package Structure

```text
app/
|-- __init__.py
|-- main.py
|-- README.md
|-- composition/
|-- contracts/
|-- kernel/
`-- services/
```

### Executable Runtime Entrypoint

The main runtime execution entrypoint is `app/main.py`:
- `async_main(argv: Sequence[str] | None = None) -> int`: Main asynchronous CLI runtime entry point that initializes the composition engine, loads configuration, manages feature lifecycle, and handles clean shutdown.

## 3. Package Invariants

- `app/__init__.py` is pure docstring-only per `AGENTS.md`.
- Runtime configuration and validation is owned by `FEAT-WS-CONFIGURE_RUNTIME` under `app/services/workspace/runtime_configuration/`.
- Domain features reside strictly under `app/services/<domain>/<feature>/`.
- Cross-boundary contracts reside strictly under `app/contracts/`.

## 4. Verification

- `tests/architecture/test_application_import_smoke.py` verifies subprocess import of `app` and `app.main.async_main`.
- `tests/composition/` verifies the composition engine runtime and hot-reconfiguration.
- `tests/workspace/runtime_configuration/` verifies workspace runtime configuration validation and admission.
