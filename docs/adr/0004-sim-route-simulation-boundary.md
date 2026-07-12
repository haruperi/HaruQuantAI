# ADR-0004: Trading `sim` Route vs Simulation Boundary

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-4

## Context

Backtests must exercise the same governed path as live trading, or their results prove nothing about production behaviour. That raises a boundary question: when Trading formulates an order intent on the `sim` route, who executes it and who owns the resulting fills and state?

## Decision

Simulation consumes `OrderIntent`s from the Trading `sim` route and owns all fill models and simulated state. Simulation is the broker analogue for the sim route, exactly as MT5 owns its own state on the live route. Live and sim share identical trading operations and intents.

## Options Considered

### Option A: Trading owns simulated fills too

**Pros:** One execution owner for all routes, including outcomes.
**Cons:** Trading would contain a fill-model engine unrelated to live execution; live/sim asymmetry appears inside Trading; simulation determinism concerns leak into the live code path.

### Option B: Simulation bypasses Trading and executes strategy intents directly

**Pros:** Simpler backtest loop.
**Cons:** Backtests would skip order-intent formulation, idempotency, and route gating — results would not reflect the governed path, undermining the whole point of backtesting.

### Option C: Trading formulates intents on every route; Simulation executes sim intents (chosen)

**Pros:** Perfect structural symmetry — `OrderIntent` → broker (MT5) on live/paper, `OrderIntent` → Simulation on sim; backtests exercise Data → Indicators → Strategy → Risk → Trading exactly as production does; fill modelling stays in the domain built for determinism.
**Cons:** Simulation depends on Trading (sits above it), which surprised the intuitive "backtester is low-level" view.

## Trade-off Analysis

The broker-analogue framing resolves the boundary cleanly: whoever owns execution state on a route is "the broker" for that route. MT5 owns it on live; Simulation owns it on sim. Trading's job ends at dispatching a deterministic intent, identically on every route.

## Consequences

- `SYS-WF-001` (backtest) flows through the full governed chain including Trading(sim).
- Simulation depends on Data, Indicators, Strategy, Risk, and Trading in the dependency diagram.
- Fill models, slippage, and simulated account state never appear in Trading.
- No live side effects are possible from Simulation by construction.

## Action Items

1. [ ] Define the sim-route `OrderIntent` handoff in both READMEs.
2. [ ] Add a system integration test asserting identical intent shape across routes.
