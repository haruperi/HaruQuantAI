# ADR-0002: TradeRecord Schema Ownership

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-2

## Context

Three domains touch trade outcomes: Trading produces official execution records, Simulation produces simulated fills and journals, and Analytics consumes both to compute performance. The `TradeRecord` schema needed one owner, and the answer also determines dependency order — earlier V1 build-order documentation listed Analytics before Trading, which is impossible if Analytics consumes Trading's records.

## Decision

Trading owns `TradeRecord` (and `ExecutionReceipt`). Analytics owns only its derived report schemas (`PerformanceReport`, scorecards). Analytics sits after Trading and Simulation in dependency order.

## Options Considered

### Option A: Analytics owns a shared trade schema

**Pros:** One place defines "what a trade looks like" for reporting.
**Cons:** Inverts ownership — the consumer would dictate the producer's output; Trading's reconciliation-critical fields would be governed by a read-only domain; breaks the producer-owns-results rule (ADR-0007).

### Option B: A shared/neutral schema domain (e.g., in Utils)

**Pros:** No producer/consumer asymmetry.
**Cons:** Utils must stay business-neutral; putting trade semantics there violates its boundary.

### Option C: Trading owns TradeRecord; Analytics owns derived schemas (chosen)

**Pros:** Producer owns its result; reconciliation state lives with the reconciliation authority; consistent with contract ownership rules; fixes the dependency order cleanly.
**Cons:** Analytics must adapt when Trading versions the record — mitigated by the Section 5 versioning policy.

## Trade-off Analysis

The producer-owns-results rule keeps authority where the ground truth is created. Trading is the reconciliation authority; only it can assert what officially happened. Analytics derives, never defines.

## Consequences

- Dependency diagram places Analytics above Trading and Simulation.
- `TradeRecord` changes follow Trading's versioning; Analytics consumes via the documented contract only.
- Simulation's outcomes remain a separate contract (`SimulationResult`) owned by Simulation.

## Action Items

1. [ ] Define `TradeRecord` v1 fields in the Trading README.
2. [ ] Add producer–consumer compatibility tests once Analytics consumes it.
