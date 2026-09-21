# Kernel

`app/kernel/` is the retained standard-library-only composition and lifecycle
foundation. It is business-neutral and currently independent of any backend,
plugin catalog, persistence layer, gateway, or UI implementation.

## Current modules

| Module | Current responsibility |
|---|---|
| `capability.py` | Immutable typed `Capability[T]` keys and unavailable errors |
| `feature.py` | Immutable `FeatureSpec` and structural `Feature` protocol |
| `context.py` | Declared capability access, staged exports, managed resources/tasks/subscriptions |
| `bootstrapper.py` | Graph validation, deterministic activation intent, transactional startup, reverse cleanup |
| `events.py` | Exact-type in-process event delivery |
| `logging.py` | Bounded structured logging with explicit configuration lifecycle |

`__init__.py` remains empty or docstring-only. Consumers import the owning module
directly; no re-export surface is provided.

## Invariants

- Python standard library only.
- No business, plugin, schema, UI, persistence, transport, or external-integration
  types.
- No imports from outside `app.kernel` within the application package.
- No import-time I/O, worker/thread startup, or logging configuration.
- Capability publication is declared and staged before becoming visible.
- Acquired resources, tasks, and subscriptions are lifecycle-owned and cleaned up.
- Kernel behavior is covered by `tests/kernel/` and architecture checks.

## Reset status and pending decisions

The kernel is retained, not automatically ratified as the final implementation.
Before the new backend is built, the architecture plan must decide:

- whether `Runtime`, `Feature`, and `FeatureContext` become explicitly host-only;
- whether ambient `available_capabilities`/`has` inspection is removed;
- whether optional startup edges are replaced by operation-scoped optional slots;
- whether the generic event bus is removed in favor of explicit event-stream
  capabilities with failure isolation;
- whether concrete logging moves to host telemetry with an injected diagnostic
  sink;
- how canonical feature ordering and identity are enforced.

Until those decisions are approved, do not extend the kernel to support concrete
plugins or add plugin knowledge here.

## Verification

```powershell
uv run pytest --no-cov tests/kernel -v
uv run python -m tests.examples.composition
uv run python -m tests.examples.logging_usage
uv run python scripts/architecture_check.py app/kernel
```
