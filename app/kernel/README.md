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

## Ratified target; source remediation pending

The owner approved the target in [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
through `ARCH-FINALIZE-001`, iteration 2. The modules above remain unchanged;
their current tests do not establish compliance with every target requirement.

- Retain `Capability`, `FeatureSpec`, `Feature`, `FeatureContext`, and `Runtime`
  concepts and owning filenames. Runtime/context access serves host composition
  only; concrete plugins and workspaces receive typed operation bindings.
- Keep immutable capability identities and compatibility majors. Restrict reads
  and exports to declared slots; remove ambient capability enumeration and
  unrestricted inspection from consumer scopes. Reject conflicting contracts.
- Validate feature names, providers, enabled names, required dependency closure,
  and cycles before effects. Canonical identity breaks ties in required-edge
  startup ordering. Optional operation bindings do not add startup edges.
- Preserve staged publication and transaction-wide rollback. Failed or cancelled
  startup must unwind the partial component and previously activated components,
  withdraw bindings, and retain both the initiating and cleanup failures.
- Stop admission and drain/cancel consumers before provider withdrawal. Their
  bindings remain usable during cleanup. Reverse activation order works only for
  a validated fixed graph accounting for all active consumers; per-component
  `AsyncExitStack` LIFO is not sufficient by itself.
- Await asynchronous teardown, continue unrelated safe cleanup after failures,
  aggregate diagnostics, and keep shutdown idempotent. Report still-live consumers
  rather than claim successful withdrawal when they cannot quiesce.
- Move concrete logging to host telemetry and event delivery to explicit
  host-owned typed observation streams with bounded delivery and subscriber
  failure isolation. The kernel may accept a business-neutral diagnostic sink.
- Host provider replacement initially requires a controlled restart. Catalog
  refresh changes future selection, not the bindings of admitted operations.

The retained `events.py` currently propagates subscriber failures, and context
inspection, optional startup edges, and concrete logging dependencies still need
remediation. A separate source-stage plan must audit their consumers, tests, and
examples before approving exact migration/deletion paths. No source is removed
by this documentation ratification.

Plugin descriptors, schemas, catalog construction, algebra, and trading types
remain outside the kernel. Pure computations do not acquire lifecycle machinery;
run-local calculation state does not by itself require a host service lifecycle.

## Verification

```powershell
uv run pytest --no-cov tests/kernel -v
uv run python -m tests.examples.composition
uv run python -m tests.examples.logging_usage
uv run python scripts/architecture_check.py app/kernel
```
