# ADR-0005: Paper Route Ownership

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-5

## Context

Paper trading needs to validate the full live path without risking funds. The question was whether "paper" is a separate execution engine (like Simulation), a distinct domain, or a variant of the live route.

## Decision

Paper is a Trading route flag using demo-account credentials supplied by Data. Paper and live follow the identical execution path to MT5; the routing difference is credentials only.

## Options Considered

### Option A: Paper as an internal simulated executor

**Pros:** No broker dependency for paper runs.
**Cons:** Would duplicate Simulation's fill modelling; paper results would not validate real broker interaction, latency, or rejection behaviour — the main reason paper trading exists.

### Option B: Paper as its own domain or separate code path in Trading

**Pros:** Explicit separation from live code.
**Cons:** Two execution paths that must be kept behaviourally identical by discipline rather than by construction; divergence risk is exactly the bug class paper trading is meant to catch.

### Option C: Same path, demo credentials (chosen)

**Pros:** Paper validates the exact production path against a real MT5 demo environment; zero code divergence by construction; credential selection sits with Data, which already owns credential resolution (ADR-0003).
**Cons:** Paper requires broker/demo availability; runtime gates must still distinguish routes for safety controls (`ALLOW_LIVE_MUTATIONS` applies to live).

## Trade-off Analysis

The value of paper trading is fidelity. Only Option C guarantees that what passes on paper is the same code, contracts, and gates that will run live. The residual risk — misrouting live credentials into a paper run — is owned by Data's credential resolution and covered by profile/route compatibility gating (Section 6).

## Consequences

- No paper-specific execution code exists anywhere.
- `RUNTIME_PROFILE=paper` must pair with `EXECUTION_ROUTE=paper`; mismatches fail closed at initialization.
- Risk applies the same gates on paper as on live, making paper a true governance rehearsal.

## Action Items

1. [ ] Document demo-credential resolution and isolation in the Data README.
2. [ ] Add an integration test proving paper and live produce identical `OrderIntent`s for the same approved decision.
