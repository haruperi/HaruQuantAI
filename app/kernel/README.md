# Kernel

`app/kernel/` is the standard-library-only capability binding and lifecycle
foundation. It has no product, plugin, persistence, transport, UI, event-delivery,
or logging implementation.

## Modules

| Module | Responsibility |
|---|---|
| `capability.py` | Immutable typed `Capability[T]` identity and unavailable errors |
| `feature.py` | Required-edge `FeatureSpec` and structural `Feature` protocol |
| `context.py` | Declared reads, staged exports, resources, tasks, and cleanup |
| `bootstrapper.py` | Preflight graph validation, canonical startup, rollback, and shutdown |

`__init__.py` is docstring-only. Consumers import owning modules directly.

## Enforced behavior

- Contexts resolve only capabilities declared in `FeatureSpec.requires` and
  publish only the exact `provides` set.
- Optional operation bindings are resolved outside startup; they do not create
  feature edges or ambient lookup APIs.
- The complete required graph is validated before startup effects. Feature-name
  order breaks ties deterministically.
- Startup publication is staged. Failure or cancellation unwinds the current
  component and every prior component in reverse dependency-safe order.
- Consumers close while provider bindings remain available. Providers are
  withdrawn after every scope has been given a cleanup attempt.
- Independent cleanup failures are retained and grouped; shutdown is idempotent.
- Business-neutral immutable diagnostics go to an injected sink. Sink failures
  cannot change lifecycle outcomes.

Host observation is owned by
[`app/host/telemetry.py`](../host/telemetry.py). Application composition begins
in [`app/host/bootstrap.py`](../host/bootstrap.py).

## Verification

```powershell
uv run pytest --no-cov tests/kernel tests/host -v
uv run python -m tests.examples.composition
uv run python -m tests.examples.telemetry_usage
uv run python scripts/architecture_check.py
```
