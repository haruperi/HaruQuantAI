# Decision: Implement `sim` as a Brokers adapter

**Status:** Proposed
**Date:** 2026-08-14
**Supersedes:** the "where the mirror boundary sits" question in `docs/sim-live-parity-register.md`
**Affects:** `docs/PROJECT.md` §2.1.2 (Brokers), §2.1.x (Trading, Simulation), §5 workflows, `app/services/brokers`, `app/services/trading`, `app/services/simulator`

---

## 1. Decision

**Yes — implement the simulator as a first-class Brokers adapter (`BrokerId.SIM`), mirroring MT5 semantics.**

The recommendation rests on one reframing that resolves the apparent ownership conflict:

> **The sim adapter is a translation layer over the simulator engine, in exactly the same way the
> MT5 adapter is a translation layer over the `MetaTrader5` Python library.**

`MT5BrokerAdapter` does not implement order matching — it translates canonical DTOs into
`order_send` calls against an external system that does the matching, and maps the results back.
`SimBrokerAdapter` would do the identical thing against `app.services.simulator`. The external system
is in-process rather than over a socket; structurally, nothing else differs.

This means Brokers does **not** acquire "ownership of simulated fills." Simulation keeps the engine,
the matching, the pricing, the accounting, the ledger, and the journal. Brokers acquires exactly what
it already owns for every other provider: the adapter surface, DTO mapping, error mapping, capability
declaration, and connection lifecycle.

---

## 2. What the codebase already gives you

The investigation turned up more existing scaffolding than expected. This is substantially cheaper
than a from-scratch adapter.

| Asset | Location | Why it matters |
|---|---|---|
| `_UnsupportedAdapterBase` | `canonical_contracts/protocols.py` | Auto-implements the full protocol as canonical `BROKER_CAPABILITY_UNSUPPORTED` responses. You override only what sim supports — the ~58-method surface collapses to ~20 real implementations. |
| `conformance/fake.py` | `brokers/conformance/` | A working deterministic adapter fixture built on `_UnsupportedAdapterBase` with introspective method generation. **A direct structural precedent and starting skeleton.** |
| `run_adapter_conformance` | `conformance/suite.py` | FEAT-BRK-10 contract test kit. Sim would be validated by the same suite as MT5 — **this becomes your standing parity regression test.** |
| `_FACTORIES` registry | `_shared/factory.py` | Lazy adapter registration keyed by `BrokerId`. Sim is the only adapter needing `import_package=None, distribution=None` — no third-party dependency, no install extra. |
| `capabilities/matrix.py`, `dashboard.py` | `brokers/capabilities/` | Capability comparison across providers. You get a **sim-vs-MT5 capability diff view for free.** |
| `BROKER_ERROR_CATALOG` | `canonical_contracts/error_catalog.py` | GAP-070 (retcode mirroring) becomes "map sim conditions to `BrokerErrorCode`" — the same exercise MT5 already performs. |
| `environment_guards/permissions.py` | `brokers/environment_guards/` | Default-deny per (provider, account, environment). Sim inherits the same permission model. |
| `_shared/base.py`, `circuit_breaker.py`, `health.py`, `state.py` | `brokers/_shared/` | Connection state machine, circuit breaker, health reporting — inherited, not rebuilt. |

---

## 3. The critical design point: mutations vs the clock

The simulator engine takes two fundamentally different kinds of input, and only one of them is a
broker operation.

| Input | Live equivalent | Routes through |
|---|---|---|
| `submit_order`, `modify_order`, `cancel_order`, `close_position`, `modify_position` | broker mutations | **Trading → `SimBrokerAdapter` → engine** |
| `execute_tick(tick)` — clock advancement | *none — time passes by itself* | **Simulator → engine, directly** |
| SL/TP protective exits fired inside a tick | *broker-side server action* | **engine internally, surfaced as adapter-reported events** |

This split matters for three reasons:

1. **It makes GAP-010 smaller than originally framed.** Only the mutation path needs to move through
   Trading. `advance_run_timeline` keeps calling `engine.execute_tick` directly, and that is correct —
   there is no broker call that means "advance time."
2. **Protective exits should not route through Trading.** In live, when MT5's server closes a position
   on stop-loss, Trading learns about it by *reading state*, not by issuing a mutation. Sim must behave
   identically: the engine closes the position, and the adapter reports it on the next read.
3. **Two entry points into the engine, one mutation path.** This is a feature, not a leak — it mirrors
   the live topology exactly.

---

## 4. Design decisions to settle before implementation

### 4a · `BrokerId.SIM` as a distinct provider, parameterized by the provider it mirrors

Three options were considered:

| Option | Shape | Assessment |
|---|---|---|
| **A** | `BrokerId.SIM`, standalone | Clean identity, but risks drifting from MT5 semantics over time |
| **B** | `BrokerId.MT5` + `BrokerEnvironment.SIMULATION` | Maximal MT5 fidelity by construction; reuses `_map_symbol` etc. wholesale. But conflates provider identity with execution mode, and blocks a future cTrader sim |
| **C** ✅ | `BrokerId.SIM`, constructed as `SimBrokerAdapter(mirrors=BrokerId.MT5, context=...)` | Distinct identity, MT5 exactness now, second provider later without redesign |

**Recommend C.** The `mirrors` parameter selects which provider's mapping layer, error catalogue, and
capability set the adapter reproduces. For `mirrors=MT5` it delegates to
`brokers/metatrader/mapping.py` directly — the same `_map_symbol`, `_map_quote`, `_map_tick`
functions live uses. That is the strongest available guarantee of terminology parity: not "we
implemented the same fields," but *literally the same code*.

### 4b · Add `BrokerEnvironment.SIMULATION`

`BrokerEnvironment` is currently `LIVE | DEMO | TESTNET | SANDBOX`. Reusing `SANDBOX` would be
misleading. Add `SIMULATION = "simulation"`.

Consequence: Trading's `_validate_broker_selection` (`routing/dispatcher.py:293-302`) hard-codes two
environment rules — live route requires `live`, paper route forbids `live`. Add the third:
**sim route requires `SIMULATION`**, and `SIMULATION` is forbidden on every other route. Symmetrical
and fail-closed in both directions, exactly like the existing pair.

### 4c · Adapter lifecycle semantics

`connect()` cannot mean "open a socket." Proposed mapping:

| Method | Sim meaning |
|---|---|
| `connect()` | Bind the adapter to a run context (dataset + engine + clock). Fails if no context supplied. |
| `disconnect()` | Finalize the journal, release the run. |
| `is_connected()` | The run is active and the timeline is not exhausted. |
| `ping()` | Succeeds while connected — and becomes a **fault-injection point** for GAP-025. |
| `reconnect()` | Models broker connection loss and recovery — a realism feature you currently cannot test at all. |
| `refresh_session()` | No-op, or session-boundary revalidation. |

`reconnect()` is worth highlighting: modelling a mid-session broker disconnect is a genuine live
failure mode with no current sim representation. Making sim an adapter gives you that for free.

---

## 5. Ownership edits to `docs/PROJECT.md`

Four statements need revision. Line numbers are current as of this document.

### Edit 1 — §2.1.2 Brokers, **Owns** (line 175)

Append to the owned list:

> …capability discovery, transport-level flow control, **and the in-process simulation adapter
> (`BrokerId.SIM`), which translates canonical mutation and read operations into calls against the
> Simulation domain's public engine surface and maps its results back through the mirrored provider's
> canonical mapping layer. Brokers owns the adapter surface only; Simulation owns all matching,
> pricing, accounting, and journal behaviour behind it.**

### Edit 2 — §2.1.2 Brokers, **Boundaries** (line 176)

The current opening — *"Pure passthrough with zero business logic"* — is the statement that most
strains under this change. It should be preserved and scoped rather than weakened:

> Pure passthrough with zero business logic — no business validation (structural/transport validation
> only), no risk checks, no decision-making, no data enrichment, no business retry/replay… **The
> simulation adapter is held to the identical standard: it performs protocol translation only and
> contains no matching, pricing, accounting, or fill logic of its own. Every such decision is made by
> the Simulation domain behind the adapter, exactly as a live provider platform makes them behind a
> live adapter.**

This is the crux of the whole proposal. If the sim adapter ever grows fill logic, the boundary has
been violated and the parity guarantee is gone.

### Edit 3 — §2.1 Simulation, **Boundaries**

Simulation currently disclaims *"broker connections/adapters; Brokers owns them."* That stays true.
Add:

> Simulation exposes a public engine surface consumed by the Brokers-owned simulation adapter.
> Simulation constructs no adapter, imports nothing from Brokers on the execution path, and remains
> the sole owner of simulated matching, pricing, accounting, and journal evidence.

Note the direction of dependency: **Brokers → Simulation**, never the reverse. This is consistent
with Brokers depending only on Utils plus provider SDKs (line 441) — the Simulation engine simply
takes the place a provider SDK occupies for every other adapter.

### Edit 4 — §5, backtest workflow note (line 587)

Currently:

> **Note:** Brokers is not part of the backtest loop itself. It participates only upstream, when Data
> acquires or backfills the historical datasets… the backtest execution path never touches a live
> provider.

Revise to:

> **Note:** The backtest execution path never touches a **live** provider. Order mutations are
> dispatched through the Brokers-owned in-process simulation adapter (`BrokerId.SIM`,
> environment `SIMULATION`), which performs no network access. Brokers additionally participates
> upstream when Data acquires or backfills the historical datasets served to this workflow.

Also revise line 445 — Trading remains *"the single execution owner for `sim`, `paper`, and `live`
routes"* — that statement stays accurate and in fact becomes **more** true, since sim mutations would
now flow through Trading rather than bypassing it.

---

## 6. Pros, cons, risks

### Pros

1. **`simulation_dispatch` disappears from Trading entirely.** Route becomes genuinely the only
   difference. `TradingDependencies` loses a field; `_execute_request` loses its route branch.
2. **The conformance suite becomes a standing parity test.** Any divergence between sim and the
   adapter contract fails CI. This is the single strongest argument — parity stops being a thing you
   maintain by discipline and becomes a thing the build enforces.
3. **Closes five register items outright** — GAP-023 (capability validation), GAP-024 (receipt
   classification), GAP-026 (duplicated Risk port), GAP-071 (MT5 result shapes), GAP-073 (envelope
   flags).
4. **GAP-025 (`unknown_outcome` unreachable) closes naturally** — the adapter can return
   `BROKER_UNKNOWN_OUTCOME` like any provider, making the retry-lock path rehearsable.
5. **GAP-070 (retcodes) becomes the existing MT5 mapping exercise**, not a bespoke one.
6. **Capability dashboard gives you a sim-vs-MT5 diff view** without building anything.
7. **New realism surface for free** — connection loss, reconnect, ping failure, session refresh: live
   failure modes that currently have no sim representation at all.
8. **Sim inherits circuit breaker, health, and connection-state machinery** from `_shared/`.

### Cons and costs

1. **~20 real method implementations** (of ~58 protocol members). Not trivial, but bounded, and
   `conformance/fake.py` is a working skeleton.
2. **The adapter needs an injected run context** — a lifecycle no other adapter has. `connect()` means
   "bind to a run." This is the one genuinely novel piece of design.
3. **Async-over-sync wrapping.** The engine is synchronous; the contract is async. Trivial mechanically,
   but the `await` stays semantically empty until latency modelling (GAP-064) lands.
4. **`docs/PROJECT.md` ownership edits** — four statements, above.
5. **Two things currently named "sim" unify** — `EXECUTION_TARGET="sim"` (broker target in
   `tests/legacy/07_trading.py`) and `route="sim"` (Trading route). Good outcome, but it is a
   migration with call-site churn.
6. **Determinism pressure on the adapter layer.** Every mapping function must be pure and every
   timestamp must come from the simulated clock, never `datetime.now(UTC)`. Note that
   `metatrader/mapping.py` uses `datetime.now(UTC)` in `_map_quote` and `_map_tick` — those paths need
   a clock injection before reuse. **This is a real constraint on Edit 4a's "literally the same code"
   claim and should be verified early.**

### Primary risk

**The adapter becomes a second home for fill logic.** Every shortcut ("just compute the price here,
it's simpler") erodes the boundary that makes the whole design work. Mitigation: a lint rule or
architecture test asserting `brokers/simulation/` imports nothing from `simulator/execution`,
`simulator/accounting`, or `simulator/journal` — only the public package root.

---

## 7. Migration plan

### Phase A — Contract groundwork (small)
- Add `BrokerId.SIM` and `BrokerEnvironment.SIMULATION`
- Register in `_FACTORIES` with no external distribution
- Add the sim environment rule to `_validate_broker_selection`
- Apply the four `docs/PROJECT.md` edits
- **Gate:** `run_adapter_conformance` passes against a stub sim adapter built on `_UnsupportedAdapterBase`

### Phase B — Read surface (medium)
- Implement `MarketDataProvider` and `AccountProvider` methods against `engine.snapshot()` and the tick timeline
- Reuse `metatrader/mapping.py` with an injected clock (see Con 6)
- **Gate:** sim `get_symbol_info` / `get_quote` / `get_positions` return the same shapes as MT5 for the same inputs
- Delivers register items GAP-072, GAP-047

### Phase C — Mutation surface (medium)
- Implement `TradeExecutionProvider` against `SimTrader`
- Map every sim condition to a `BrokerErrorCode` / MT5 retcode
- **Gate:** conformance suite green; `classify_authority_response` produces sim receipts
- Delivers GAP-024, GAP-025, GAP-070, GAP-071

### Phase D — Calculation surface (medium)
- Implement `CalculationProvider` — `calculate_margin`, `calculate_profit`, `get_commission_estimate`
- Back it with the **cached** live MT5 values (GAP-034), not a reimplementation
- Delivers GAP-030, GAP-031, GAP-032

### Phase E — Cut over Trading (medium)
- Delete `simulation_dispatch` from `TradingDependencies`
- Remove the route branch in `_execute_request`
- Point `run_backtest` at `trading.submit_order`
- **Gate:** an identical `TradingRequest` differing only in `route` produces structurally identical
  envelopes on `sim` and `mt5`/demo
- Delivers GAP-010, GAP-011, GAP-012, GAP-013, GAP-020, GAP-021, GAP-022, GAP-026, GAP-027

### Phase F — Realism
Unchanged from the register's Phase 5, but now expressible as adapter behaviour: latency becomes
adapter-level delay, requote becomes an adapter-returned retcode, connection loss becomes
`reconnect()`.

---

## 8. Effect on the parity register

Adopting this decision changes `docs/sim-live-parity-register.md` as follows:

| Register phase | Change |
|---|---|
| Phase 0 (defects) | Unchanged — do first, independent of this decision |
| Phase 1 (path convergence) | **Reshaped** — becomes Phases A–E above |
| Phase 2 (MT5 calculations) | **Absorbed** into Phase D; GAP-034 cache remains a prerequisite |
| Phase 3 (symbol/account semantics) | Unchanged, but GAP-040/047 partly delivered by Phase B |
| Phase 4 (order model) | Unchanged |
| Phase 5 (realism) | Unchanged in substance; re-expressed as adapter behaviour |
| Phase 6 (surface mirroring) | **Largely absorbed** — GAP-070/071/072/073 fall out of Phases B–C |

Net: 41 items → roughly 30 remaining as distinct work, with the largest structural item replaced by a
better-scaffolded one.

---

## Appendix · Failure-parity taxonomy

The governing principle — *"anything that is a hard failure in live is a hard failure in sim"* — is
correct, and it needs one refinement to avoid being misapplied. Failures fall into three classes, and
only the first mirrors 1:1.

### Class 1 · Domain failures — mirror exactly

Things the market or broker can do: insufficient margin, invalid stops, market closed, requote,
invalid volume, trade disabled, volume limit. **These mirror 1:1 in code, message, and retcode.**
This is the core of the parity goal and the whole of WS-4/WS-5/WS-7 in the register.

### Class 2 · Simulator-integrity failures — fail closed, no live counterpart

Calculation-cache miss, broken journal hash chain, non-monotonic ticks, dataset checksum mismatch,
artifact write failure. Live has no cache and no journal, so "mirror live" gives no guidance here.

These fail closed **because reproducibility is a Simulation-owned guarantee**, not because live does
something equivalent. Stating the reason explicitly matters — otherwise the principle inverts later
into "live has no journal, so journal failures needn't be fatal in sim," which would be wrong.

**On the specific question: a calculation-cache miss on replay is a hard failure.** A silent re-fetch
means a replay can diverge from the original run while still claiming the same `request_hash`, which
would quietly destroy the meaning of every stored result.

### Class 3 · Live-infrastructure failures — simulatable, never spontaneous

Network timeout, broker unavailable, rate limit, ambiguous response, connection loss. These are real
live failures that sim must be **able** to produce — otherwise the `unknown_outcome` and retry-lock
paths stay untested (GAP-025) — but must never produce *by accident*, or determinism is gone.

**Rule:** Class 3 failures occur in sim only when explicitly injected by a seeded scenario, and every
injection is journalled so the run remains reproducible and auditable.
