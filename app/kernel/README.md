# Kernel

`app/kernel/` is the standard-library-only capability binding and lifecycle
foundation. It has no product, plugin, persistence, transport, UI,
event-delivery, or logging implementation.

Authority: [`AGENTS.md`](../../AGENTS.md) — "Standard-library kernel."
Everything here must remain importable with no I/O, tasks, threads,
logging configuration, environment access, or resource acquisition.

## Modules

| Module | Responsibility |
|---|---|
| `capability.py` | Immutable typed `Capability[T]` identity and unavailable errors |
| `feature.py` | Required-edge `FeatureSpec` and structural `Feature` protocol |
| `context.py` | Declared reads, staged exports, resources, tasks, and cleanup |
| `bootstrapper.py` | Preflight graph validation, canonical startup, rollback, and shutdown |

`__init__.py` is docstring-only. Consumers import owning modules directly.

## Capability identity

`Capability[T]` is the single typed-slot primitive every host owner and
operation declares against. A capability is an immutable, hashable
`(name, major)` pair — displayed as `name@major` (for example
`host.catalog@1`). The phantom type parameter `T` exists only for static
typing: `require(token)` returns the declared provider type with no
runtime cast, and a major-version bump means a new binding contract, not
a mutation of the old one. Capabilities are compared structurally; the
kernel never centralizes a registry of them.

## Lifecycle semantics

- **Declaration over ambient lookup.** Contexts resolve only capabilities
  declared in `FeatureSpec.requires` and publish only the exact
  `provides` set. `require` fails closed (typed error, with attribution
  when a declared provider failed to start); `optional` resolves later
  and creates no startup edge.
- **Staged publication.** `provide` stages exports and
  `commit_exports` publishes them atomically when the feature's `start`
  completes; a partially started feature exports nothing.
- **Validate before effects.** The complete required graph is validated
  before any startup side effect. Feature-name order breaks ties
  deterministically.
- **Transactional startup.** Failure or cancellation unwinds the current
  component and every prior component in reverse dependency-safe order.
- **LIFO close.** Consumers close while their provider bindings remain
  available; providers are withdrawn only after every scope has had a
  cleanup attempt. `on_close` callbacks run in reverse registration
  order across all ownership kinds, and a failing callback cannot skip
  its siblings.
- **Failure containment.** Independent cleanup failures are retained and
  grouped; shutdown is idempotent. Business-neutral immutable diagnostics
  go to an injected sink, and sink failures cannot change lifecycle
  outcomes.

## Concurrency

A `Runtime` is single-use: one `__aenter__`/`__aexit__` pair. Features
start sequentially in dependency order. Feature contexts can spawn
tracked tasks (`spawn` cancels-and-awaits them at close); the kernel
itself starts no threads and owns no loop.

## What does not belong here

Product logic, plugin vocabulary or contracts, host owners, persistence,
transports, UI, and any import outside the standard library or
`app.kernel` itself (enforced as ARCH-004). Host observation is owned by
[`app/host/telemetry.py`](../host/telemetry.py); application composition
begins in [`app/host/bootstrap.py`](../host/bootstrap.py).

## Verification

```powershell
uv run pytest --no-cov tests/kernel -v
uv run python -m tests.examples.composition
uv run python -m tests.examples.telemetry_usage
uv run python scripts/architecture_check.py
```
