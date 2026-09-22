# HaruQuantAI

HaruQuantAI is being rebuilt as a spatially composable quantitative research
workstation. The previous contracts/services/registry backend has been removed
so the replacement can be designed from a clean, enforceable foundation.

## Current repository state

```text
app/
|-- __init__.py
|-- kernel/   # retained standard-library composition/lifecycle primitives
`-- ui/       # retained React/TypeScript workstation prototype
```

There is currently no Python application entry point, persistence layer,
gateway, broker integration, simulator, or production plugin catalog. The UI is
still mock-backed and must not be interpreted as evidence of backend behavior.

The reset is intentional. Git history and `.agents/logs/` retain the removed
implementation and its task evidence.

## Architectural objective

The replacement backend must satisfy five laws:

1. **Locality of behavior:** one quantitative concept is implemented and
   described in one cohesive plugin file.
2. **Orthogonality:** installing, changing, disabling, or removing one plugin
   does not mutate unrelated plugins, the host, or UI source.
3. **Explicit typed interfaces:** collaboration uses immutable typed capability
   tokens and declared slots, never ambient globals or private imports.
4. **Hierarchical/algebraic composition:** one typed expression tree is shared
   by editors, generators, simulators, optimizers, and exporters.
5. **Schema-driven self-description:** plugin parameters, bounds, outputs, and
   generic presentation metadata are dynamically introspectable.

See [PROJECT.md](docs/PROJECT.md) for current scope and
[ARCHITECTURE.md](docs/ARCHITECTURE.md) for structural constraints.

## Retained Python checks

```powershell
uv sync
uv run pytest --no-cov tests/kernel tests/architecture tests/scripts -v
uv run python -m tests.examples.composition
uv run python -m tests.examples.logging_usage
uv run python scripts/ci_check.py
```

## UI development

```powershell
npm --prefix app/ui install
npm --prefix app/ui run dev
npm --prefix app/ui run typecheck
npm --prefix app/ui run test
npm --prefix app/ui run build
```

## Contributor workflow

All changes follow the repository plan/approval/execution/walkthrough/commit
gates in [AGENTS.md](AGENTS.md). Workspace and plugin implementation must follow the
canonical [implementation pipeline](docs/dev/workspace_plugin_implementation_pipeline.md) after the
replacement backend architecture is ratified.
