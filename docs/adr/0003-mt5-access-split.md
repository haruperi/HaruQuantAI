# ADR-0003: MT5 Access Split Between Data and Trading

**Status:** Accepted
**Date:** 2026-07-12
**Deciders:** Haruperi (Owner)
**Source:** PROJECT.md OD-3

## Context

MetaTrader 5 is both the market/account data source and the order execution gateway. Two domains need it: Data (reads) and Trading (writes). Duplicating connection handling in both domains would fragment credential management, session lifecycle, and failure handling; giving Trading its own connection would also create a second path to the broker outside Data's facade.

## Decision

Data owns the MT5 connection lifecycle and credential resolution. Data's public broker capability is read-only. Data exposes a restricted `BrokerExecutionChannel` — a scoped write interface bound to the authenticated connection — and only Trading may use it, only for approved broker mutations.

## Options Considered

### Option A: Trading owns its own MT5 connection

**Pros:** Execution owner controls its transport end to end.
**Cons:** Two connection lifecycles and two credential resolvers; broker access no longer flows through one facade; harder to guarantee read-only behaviour elsewhere.

### Option B: Data owns everything including order dispatch

**Pros:** Single broker surface.
**Cons:** Data would perform trading mutations, violating its "no trading decision logic" boundary and blurring the Risk→Trading execution gate.

### Option C: Data owns the connection, Trading gets a restricted channel (chosen)

**Pros:** One connection lifecycle and credential owner; read/write split enforced structurally (the channel is the only mutation path, and only Trading holds it); paper/live differ only by credentials Data supplies (ADR-0005).
**Cons:** A cross-domain channel contract to design and test carefully; channel scope must be enforced, not assumed.

## Trade-off Analysis

Option C gives single ownership of the risky resource (broker session, secrets) while keeping mutation authority with the domain that is gated by Risk. The structural guarantee — no domain other than Trading can obtain a write capability — is worth the extra contract.

## Consequences

- Broker secrets never leave Data; Trading never resolves credentials.
- Connection, scope, or permission failure blocks mutations (fail closed).
- The channel is a first-class contract (`BrokerExecutionChannel` v1) with its own tests.
- Any future broker beyond MT5 slots in behind the same facade and channel shape.

## Action Items

1. [ ] Specify the channel's scoped operations and error taxonomy in the Data README.
2. [ ] Add a dependency-audit check that no domain other than Trading imports or receives the channel.
