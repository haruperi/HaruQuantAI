# HaruQuantAI Capability Catalog & Model

This document defines the capability-oriented contract for HaruQuantAI's spatiotemporal-composition runtime.

## Architectural principles

1. Features depend on versioned contracts, never another feature implementation.
2. Capabilities are narrow and identified as `<domain>.<capability>@<major>`.
3. Every reversible runtime effect is owned by a `FeatureScope` through `FeatureContext`.
4. Missing providers cause capability loss and `BLOCKED` consumers rather than structural process failure.
5. Deployment profiles define readiness criticality; feature packages do not declare themselves globally mandatory.
6. More than one enabled provider for the same capability is an error unless `[providers]` selects one explicitly.
7. Ordinary registry registration cannot overwrite an active provider. Replacement uses the explicit transactional path and generation-safe tokens.

## Implemented foundational capabilities

| Feature ID | Provides | Requires | Optional | Removal result |
| --- | --- | --- | --- | --- |
| `FEAT-BROKER-FEED_MOCK` | `broker.market-data@1` | — | — | Broker market data unavailable; required consumers block |
| `FEAT-DATA-RETRIEVE_BARS` | `data.historical-bars@1` | `broker.market-data@1` | `data.bar-cache@1` | Historical bars unavailable; required consumers block |
| `FEAT-SYS-PERSIST_STORAGE` | `system.storage@1` | — | — | Persistent storage unavailable; retained state stays on disk |

The broader domain catalog remains a roadmap. A capability is not considered implemented merely because its contract exists.

## Canonical deployment configuration

Only `[application].profile` is supported. Legacy `[profile]` syntax is rejected.

```toml
[application]
profile = "research"

[providers]
"broker.market-data@1" = "FEAT-BROKER-FEED_MOCK"

[features.FEAT-BROKER-FEED_MOCK]
enabled = true

[features.FEAT-DATA-RETRIEVE_BARS]
enabled = true
```

Provider-selection rules are deterministic:

- zero enabled providers → capability unavailable;
- exactly one enabled provider → automatically selected;
- more than one enabled provider → explicit `[providers]` selection required;
- an invalid, disabled, undiscovered, or incompatible selected provider fails reconciliation;
- an unselected overlapping provider is not mounted.

## Deployment profiles

The authoritative profile mapping lives in `app/composition/config.py`.

| Profile | Required capabilities |
| --- | --- |
| `research` | `data.historical-bars@1` |
| `backtest` | `data.historical-bars@1`, `system.clock@1` |
| `live` | `system.clock@1`, `broker.market-data@1`, `broker.execution@1`, `data.realtime-ticks@1`, `portfolio.positions@1`, `risk.approval@1`, `trading.execution@1` |

Unknown profiles fail closed. In particular, Live can never report ready while one of its safety capabilities is missing.

## Lifecycle semantics

A feature progresses through states including `PREPARING`, `ACTIVE`, `BLOCKED`, `STOPPING`, `STOPPED`, `FAILED_START`, and `FAILED_RUNTIME`.

When a provider is disabled, reconfigured, selected differently, or replaced, the reconciler stops and remounts its transitive required/optional consumers so they cannot retain stale provider objects. Required dependency cycles are rejected. Optional-only cycles do not make activation impossible.

Unexpected managed background-task failures transition the owner to `FAILED_RUNTIME`, dispose its scope, and stop dependent features.

## Transactional replacement

Replacement mounts into a staged scope. Before commit, any failure closes only that staged scope and leaves the old provider untouched. At commit, the staged provider bundle is atomically published with new generation tokens and the staged scope becomes the active scope. Old-scope cleanup occurs after commit; cleanup failure is reported as a post-commit warning rather than falsely described as rollback.

## Liveness and readiness

`SystemControlPlane` exposes transport-neutral diagnostics:

- `liveness()` reports whether the kernel/control shell is alive;
- `readiness()` checks all capabilities required by the selected profile;
- `capabilities()` reports active providers;
- `features()` reports lifecycle and dependency diagnostics.

An HTTP transport may map these methods to `/system/liveness`, `/system/readiness`, `/system/capabilities`, and `/system/features` without changing composition semantics.

## Physical removability

Pull requests run a feature-removal matrix for the current foundational provider features. The verifier physically deletes a feature in an isolated copy, runs formatting, linting, mypy, Import Linter, AST architecture checks and pytest, then asserts that the capability is absent, required consumers block, unrelated capabilities remain active, and the process remains structurally operable.
