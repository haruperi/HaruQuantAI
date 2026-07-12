# ADR-0006: Live/Paper Runtime Orchestration Ownership

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-6

## Context

The live/paper evaluation loop spans five domains: Data (market state, snapshots), Indicators, Strategy (signals/intents), Risk (approval), and Trading (execution). Someone must own the runtime loop that coordinates them. Candidates were Strategy (it "runs" the strategy) and Trading (it owns execution).

## Decision

Trading owns runtime coordination for live/paper evaluation, invoking only the public APIs of Data, Indicators, Strategy, and Risk. Strategy owns strategy evaluation and proposal generation only. Trading's execution phase begins only after an independent Risk approval, and Trading cannot approve its own decisions.

## Options Considered

### Option A: Strategy owns the runtime loop

**Pros:** Intuitive — the strategy "decides when to act".
**Cons:** Strategy would need broker awareness, scheduling, gate handling, and reconciliation context — dragging execution concerns into a domain that must stay deterministic and testable in isolation; blurs the proposal/execution split that Risk governs.

### Option B: A separate orchestrator domain

**Pros:** Clean separation of coordination from execution.
**Cons:** A twelfth domain whose only job is calling five others; every workflow gains a hop; ownership of failure handling becomes ambiguous between orchestrator and Trading.

### Option C: Trading owns the loop (chosen)

**Pros:** The domain that must react to gates, kill switch, and broker state also drives the cadence; Strategy stays a pure evaluator (same code in backtest and live); mirrors ADR-0004 where Simulation orchestrates the historical loop for the sim world.
**Cons:** Trading is large — it must be held to coordinating via public APIs only, never absorbing other domains' logic.

## Trade-off Analysis

The symmetry with Simulation is the strongest argument: Simulation orchestrates the historical loop, Trading orchestrates the live/paper loop, and both invoke the identical evaluation chain. The independence requirement is preserved because Risk remains structurally outside Trading — approval tokens are issued by Risk and merely consumed by Trading.

## Consequences

- Strategy is invocable by both Simulation (historical) and Trading (live/paper) with no runtime awareness.
- Trading's boundary explicitly states it coordinates but does not own other domains' decisions.
- Kill-switch enforcement during in-flight execution lands in Trading; kill-switch state stays canonical in Risk.

## Action Items

1. [ ] Specify the runtime loop (scheduling, triggers, backoff) in the Trading README.
2. [ ] Dependency audit: Trading imports only public APIs of the four coordinated domains.
