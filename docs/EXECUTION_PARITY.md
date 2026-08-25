# HaruQuantAI Unified Trading Execution Parity

> **Status:** Ratified architecture decision
> **Ratified:** 2026-08-25
> **Scope:** Runtime Risk, Trading, Simulator, Broker Connectivity, Portfolio, Analytics, Research, Interfaces, and UI sequencing where affected
> **Origin:** Restores the proven HaruQuantAI-V2 design intent: make simulation exercise the real trading lifecycle rather than maintain a parallel simulated trading lifecycle.

> [!IMPORTANT]
> This document is a ratified cross-domain architecture amendment. Until the large canonical registries in `docs/PROJECT.md`, `docs/dev/IMPLEMENTATION_ORDER.md`, `app/services/risk/README.md`, `app/services/trading/README.md`, `app/services/simulator/README.md`, and their ratified contract inventories are mechanically reconciled, the rules in this document **supersede conflicting statements only for the Trading/Simulation/Runtime-Risk ownership and sequencing described here**. No existing product `FEAT-*` or `FR-*` status changes merely because this decision is ratified.

---

## 1. Decision

HaruQuantAI shall implement **one governed Trading lifecycle with multiple execution authorities**.

Simulation is not a second implementation of trading. Historical simulation and paper execution must exercise the same Trading-owned business lifecycle, risk admission, order intent, operation state, protection, receipt, reconciliation, and execution-evidence semantics used by demo/live execution.

The authority changes by route; the business trading lifecycle does not.

```text
Strategy / authenticated manual action
                |
                v
          Runtime Risk
                |
                v
             Trading
                |
      one governed lifecycle
                |
     +----------+-----------+-----------+
     |                      |           |
     v                      v           v
Historical/Paper          Demo         Live
Simulator authority       Broker       Broker
     |                   authority    authority
     +----------+-----------+-----------+
                |
                v
      canonical Trading evidence
```

The design principle is:

> **One Trading lifecycle, multiple execution authorities.**

---

## 2. Route model

The product retains four useful operating contexts rather than conflating historical replay with forward paper trading:

| Route / mode | Time source | Execution authority | External capital mutation | Purpose |
| --- | --- | --- | --- | --- |
| `SIM` | deterministic simulation scheduler | Simulator | never | historical replay/backtest/what-if execution |
| `PAPER` | live/forward application clock with current market evidence | Simulator paper authority | never | forward paper trading through the same lifecycle |
| `DEMO` | live/forward application clock | Broker Connectivity demo authority | provider demo only | broker-realistic rehearsal |
| `LIVE` | live/forward application clock | Broker Connectivity live authority | explicitly authorized live account | production execution |

`SIM` and `PAPER` may use different Simulator profiles and clocks, but neither may bypass Trading to create an independent business order lifecycle.

Route-specific differences are allowed only where reality requires them: authority transport, time/deadline source, matching/fill mechanics, market microstructure, credentials, connectivity, and explicit safety gates. Business/risk gates must remain semantically paired.

---

## 3. Canonical ownership

### 3.1 Trading owns the business execution lifecycle

Trading owns the canonical semantics for all routes:

- approved executable request / trade-plan normalization;
- logical operation identity and idempotency;
- route and execution-authority selection;
- common business/risk gate ordering;
- canonical order lifecycle and order state;
- canonical deal/fill acceptance into execution history;
- canonical position projection derived from execution evidence;
- protective-order ownership and mutation policy;
- dispatch receipt classification, including unknown outcomes;
- retry blocking and reconciliation policy;
- session/operation recovery semantics;
- immutable execution journal and trace chain;
- execution evidence exposed to Analytics, Portfolio, Interfaces, and UI.

Trading may depend on capability contracts for an authority, but it must not import Simulator or Broker implementation internals.

### 3.2 Runtime Risk owns admission for every executable route

Runtime Risk remains the non-bypassable admission authority for any executable action that enters the common Trading lifecycle, including `SIM` when parity mode is requested.

Risk owns:

- route-appropriate risk profiles and limits;
- source-evidence validation;
- sizing approval / maximum executable size;
- stop and exposure checks;
- approval tokens where required;
- capacity reservation;
- kill-switch semantics;
- decision expiry and revalidation.

A simulation can intentionally use a simulation-specific risk profile, but it must not recreate a separate sizing/admission engine inside Simulator when the goal is execution parity.

### 3.3 Simulator owns execution mechanics, not a second trading business model

Simulator owns the deterministic historical/forward synthetic authority mechanics needed to emulate execution:

- run manifests, pinned inputs, deterministic seeds, and engine profiles;
- simulation scheduler / time authority;
- intrabar path and precision models;
- order matching mechanics;
- spread, slippage, commission, swap, and other simulation cost models;
- provider/venue semantic emulation;
- simulated authority-side pending-order and account state required to produce truthful authority evidence;
- deterministic fills/deals and authority snapshots;
- checkpoint/replay behavior;
- perturbation and distributed simulation mechanics;
- parity evidence and first-divergence diagnostics.

Simulator must receive a Trading-approved executable request through a public capability boundary and return authority evidence/receipts that Trading classifies into the canonical lifecycle.

### 3.4 Broker Connectivity owns demo/live authority transport

Broker Connectivity owns:

- provider connections and credentials;
- environment isolation;
- provider capability discovery;
- request/response adaptation;
- broker order transport;
- provider-truth reads and normalized provider events;
- demo/live session transport state.

Broker Connectivity does not decide business admission, construct a competing Trading lifecycle, or reinterpret Risk approval.

### 3.5 Portfolio is optional evidence for core Runtime Risk

Portfolio must **not** be a hard prerequisite for Runtime Risk itself.

Core Runtime Risk must be able to admit or reject a strategy/account action with Data, Strategy, Catalogue, and applicable Broker evidence even when Portfolio is absent.

Portfolio-aware allocation/budget governance is an optional/later Risk capability. When Portfolio exists it can supply allocation, portfolio exposure, rebalance, and budget evidence through versioned contracts. Removing Portfolio must not make base Runtime Risk or single-strategy Trading unavailable.

This breaks the previous circular product sequence:

```text
Trading -> Simulator -> Analytics -> Research -> Portfolio -> Risk -> Trading
```

and replaces it with an acyclic implementation core:

```text
Catalogue / Data / Strategy / Broker evidence
                   |
                   v
             Runtime Risk
                   |
                   v
                Trading
                   |
          authority contracts
              /          \
             v            v
        Simulator       Broker
```

Portfolio may later enrich Risk through an optional capability without becoming a prerequisite of the core Risk domain.

---

## 4. Contract migration rule

The current V3 planning contracts were authored before this decision and therefore contain duplicate lifecycle concepts. They must be reconciled before implementation of the affected product features.

### 4.1 Trading contracts become canonical across routes

The Trading contract family remains the canonical business lifecycle surface. The reconciled contract set must support `SIM`, `PAPER`, `DEMO`, and `LIVE` where applicable.

At minimum, route/mode and execution-authority records must be capable of representing all four contexts without inventing route-specific business state machines.

### 4.2 Existing Simulator lifecycle records are not a second canonical lifecycle

Current planned records such as `SimOrder`, `SimFill`, `SimPosition`, and `SimTrade` must not remain independent public business lifecycle authorities in parallel with `TradingOrder`, `TradingDeal`, and `TradingPositionProjection`.

During contract reconciliation they must be handled as follows:

| Current Simulator concept | Reconciled role |
| --- | --- |
| `SimOrder` | Simulator authority-side matching/pending evidence, private or explicitly authority-scoped; not a competing canonical Trading order |
| `SimFill` | Simulator authority fill/deal evidence returned to Trading; canonical accepted execution becomes Trading-owned deal/evidence |
| `SimPosition` | Simulator authority snapshot/evidence used for reconciliation; canonical application projection remains Trading-owned |
| `SimTrade` | deterministic simulation/result projection derived from canonical Trading execution evidence; it must not mutate an independent order/position state machine |
| `SizingDecision` | remove duplicate admission authority; use Runtime Risk sizing/approval for parity execution, with route-appropriate profiles |

Simulator may retain authority-local structures internally when required by matching mechanics, but their names, contracts, and tests must make the authority scope explicit and must prove they cannot bypass Trading.

### 4.3 No direct construction bypass

Simulator must not construct canonical Trading orders, deals, positions, approval decisions, or operation states by copying Trading private logic. It consumes public Trading/authority contracts only.

Likewise Trading must not duplicate Simulator matching/fill logic or Broker provider transport.

---

## 5. Gate parity

All four routes traverse the same semantic business/risk gate categories in the same lifecycle order where applicable:

1. request/intent validation;
2. unresolved-operation / idempotency guard;
3. current evidence validation;
4. Runtime Risk decision validation;
5. approved-size and capacity validation;
6. kill-switch validation;
7. execution-plan construction;
8. pre-dispatch authority recheck;
9. exactly-once dispatch attempt;
10. receipt classification;
11. execution-event application;
12. reconciliation when authority truth is incomplete or conflicts.

Route-specific safety gates are explicit deltas, not hidden branches. Examples include live-mutation authorization, broker credential/session readiness, simulator scheduler readiness, or historical-data completeness.

No route may skip a business/risk gate merely because it is simulated.

---

## 6. Time and deadline parity

The common Trading lifecycle must not hard-code wall-clock behavior that makes deterministic simulation impossible.

Deadline/time authority is injected:

- `SIM` uses deterministic scheduler time;
- `PAPER`, `DEMO`, and `LIVE` use the appropriate forward monotonic/wall-clock authority;
- timeout/expiry outcomes retain the same canonical semantic shape across routes;
- no production composition silently defaults an absent time authority.

This preserves deterministic replay while keeping the same Trading code path.

---

## 7. Revised implementation dependency order

This is the ratified dependency milestone order for the affected architecture. The UI-first horizontal shell remains allowed early against truthful mocks; its live de-mock gates follow producer readiness.

| Stage | Capability/domain milestone |
| ---: | --- |
| 0 | Foundation / composability substrate |
| 1 | UI-first workstation shell and truthful mock boundary |
| 2 | Workspace |
| 3 | Plugins |
| 4 | Catalogue |
| 5 | Broker Connectivity |
| 6 | Data |
| 7 | Strategy |
| 8 | Runtime Risk core |
| 9 | Trading core/common execution lifecycle |
| 10 | Simulator as `SIM`/`PAPER` execution authority |
| 11 | Analytics |
| 12 | Research |
| 13 | Portfolio |
| 14 | Portfolio-aware Runtime Risk extension and remaining portfolio-coupled gates |
| 15 | Orchestration |
| 16 | Interfaces live integration |
| 17 | Final UI de-mock and complete-system integration |

The key invariant is the relative core order:

```text
Strategy -> Runtime Risk -> Trading -> Simulator -> Analytics -> Research -> Portfolio
```

Broker Connectivity is available before the common execution lifecycle so Trading is designed against the same authority abstraction from the start; demo/live release remains independently safety-gated and disabled by default.

### 7.1 Risk split required by the new order

`FEAT-RISK-GOVERN_ALLOCATIONS` (or its reconciled successor) is portfolio-coupled and therefore belongs after Portfolio capability exists. It must not force all Runtime Risk implementation to wait for Portfolio.

Core Risk features—contracts, current risk calculation, kill-switch, admission, approval/capacity, and risk audit—are implemented before Trading.

### 7.2 Trading before Simulator does not require a concrete Simulator implementation

Trading is implemented and tested first against the versioned execution-authority capability contract plus deterministic fake/conformance authorities. Simulator later provides the real `SIM`/`PAPER` authority implementation.

This prevents a package dependency cycle while still making Simulator consume the canonical Trading execution semantics.

---

## 8. Required specification reconciliation

Before affected features are considered implementation-ready, the following canonical registries must be mechanically reconciled with this decision:

1. `docs/PROJECT.md`
   - remove hard `PORT -> RISK` from the core dependency graph;
   - remove the claim that Trading requires Simulator as a lower implementation layer;
   - describe Simulator and Broker as runtime execution-authority providers through contracts;
   - update `SYS-WF-004`, `SYS-WF-010`, `SYS-WF-011`, and parity/release wording so simulation uses the common Trading lifecycle.
2. `app/services/risk/README.md`
   - extend core admission applicability to parity simulation;
   - remove the claim that Simulator owns independent backtest sizing when parity execution is selected;
   - make Portfolio evidence optional for core Risk;
   - move portfolio-allocation governance to a later optional capability slice.
3. `app/services/trading/README.md`
   - make Trading explicitly canonical for `SIM`, `PAPER`, `DEMO`, and `LIVE` business execution semantics;
   - replace paper-vs-broker-only authority wording with the four-context authority model;
   - state that Simulator provides authority mechanics/evidence, not a separate lifecycle.
4. `app/services/simulator/README.md`
   - rewrite `FEAT-SIM-SIMULATE_ORDERS` ownership around authority matching/fill mechanics;
   - remove or reclassify duplicated canonical order/position lifecycle ownership;
   - remove duplicated sizing/admission authority in parity mode;
   - add explicit Trading authority-port consumption and route-parity acceptance criteria.
5. `app/contracts/{risk,trading,simulator}/`, `app/contracts/README.md`, generated schemas/TypeScript, and contract tests
   - reconcile the ratified v1 planning records before affected feature implementation;
   - regenerate deterministic contract artifacts;
   - preserve schema/version discipline rather than silently changing existing shapes.
6. `docs/dev/IMPLEMENTATION_ORDER.md`
   - move Broker/Runtime-Risk/Trading core milestones before Simulator;
   - move Simulator before Analytics/Research/Portfolio;
   - leave portfolio-aware Risk work after Portfolio;
   - relocate de-mock gates without duplicating any `FR-*` checkbox.

Until this reconciliation is complete, existing affected registries are planning artifacts with known architectural drift and must not be used to justify implementing a second Simulator-owned trading lifecycle.

---

## 9. Mandatory acceptance evidence

The reconciled implementation must eventually prove all of the following:

1. **Same approved request path:** equivalent strategy/manual intent plus equivalent risk evidence produces the same canonical Trading request shape independent of route-specific authority fields.
2. **Same business/risk gate sequence:** `SIM`, `PAPER`, `DEMO`, and `LIVE` execute the same registered business/risk gate categories and ordering.
3. **No size mutation after Risk:** Simulator and Broker authorities cannot increase or replace the Risk-approved executable quantity.
4. **Authority-only route delta:** switching route changes authority/time/safety behavior, not the Trading business state machine.
5. **Canonical receipt semantics:** accepted/rejected/unknown/partial/fill outcomes normalize into the same Trading receipt/operation semantics.
6. **Unknown-outcome safety:** no authority, including Simulator, permits blind mutation retry after an unknown outcome.
7. **Reconciliation parity:** authority order/deal/position evidence reconciles through the same Trading policy, with route-specific evidence adapters only.
8. **Deterministic simulation:** identical pinned simulation manifests and seed streams reproduce identical authority evidence and canonical Trading results.
9. **Risk independence from Portfolio:** core Runtime Risk starts and governs single-strategy/account actions when Portfolio is physically absent.
10. **Optional portfolio enrichment:** installing/removing Portfolio adds/removes only portfolio-aware risk/allocation capability; it does not break core Risk or Trading.
11. **Simulator removal:** removing Simulator makes `SIM`/`PAPER` authority unavailable while Broker-backed routes remain healthy when their dependencies exist.
12. **Broker removal:** removing Broker Connectivity makes `DEMO`/`LIVE` unavailable while Simulator-backed routes remain healthy.
13. **No reverse implementation imports:** all cross-domain collaboration remains through versioned capability contracts and composition wiring.
14. **Parity is falsifiable:** route parity claims are bounded by an explicit comparison envelope; empirical spread/slippage/latency equivalence is never claimed without evidence.

---

## 10. Non-goals

This decision does **not** require simulated fills to equal live fills. Real venues contain latency, queue position, liquidity, spread dynamics, slippage, rejects, outages, and undocumented behavior that historical replay may only model approximately.

The parity target is instead:

- same business lifecycle;
- same risk/admission semantics;
- same request and response contracts;
- same state-transition rules;
- same safety/idempotency/reconciliation policy;
- route-specific execution mechanics made explicit and measurable.

Simulation realism is improved by calibrating Simulator authority behavior against real broker evidence, not by cloning the Trading lifecycle inside Simulator.

---

## 11. Final architecture statement

The canonical mental model for HaruQuantAI is now:

```text
Strategy
   |
   v
Runtime Risk
   |
   v
Trading  <--- single business execution lifecycle
   |
   +-- SIM   ----> Simulator historical authority
   +-- PAPER ----> Simulator forward-paper authority
   +-- DEMO  ----> Broker demo authority
   +-- LIVE  ----> Broker live authority
   |
   v
Canonical execution evidence
   |
   +--> Analytics
   +--> Research
   +--> Portfolio
   +--> Interfaces / UI
```

Any future design that introduces a second route-specific business order lifecycle must be treated as an architecture regression unless this decision is explicitly superseded.