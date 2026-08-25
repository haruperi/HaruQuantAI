# HaruQuantAI Unified Trading Execution Parity

> **Status:** Ratified architecture decision; canonical documentation reconciled
> **Ratified:** 2026-08-25
> **Reconciled:** 2026-08-25
> **Scope:** Runtime Risk, Trading, Simulator, Broker Connectivity, Portfolio, Analytics, Research, Interfaces, UI, and implementation sequencing where affected
> **Origin:** Restores the proven HaruQuantAI-V2 design intent: simulation exercises the real Trading lifecycle rather than maintaining a parallel simulated trading lifecycle.

> [!IMPORTANT]
> This document is the cross-domain authority for Trading/Simulation/Runtime-Risk execution ownership. `docs/PROJECT.md`, `docs/dev/IMPLEMENTATION_ORDER.md`, and the Runtime Risk, Trading, and Simulator domain READMEs have been reconciled to it. No product `FEAT-*` or `FR-*` status changes merely because the architecture is ratified. Physical wire schemas/generated clients remain implementation artifacts and change only through their normal contract implementation/version process.

---

## 1. Decision

HaruQuantAI implements **one governed Trading lifecycle with multiple execution authorities**.

Simulation is not a second implementation of trading. Historical simulation and paper execution exercise the same Trading-owned business lifecycle, Runtime Risk admission, operation state, protection ownership, receipt classification, reconciliation, and execution-evidence semantics used by demo/live execution.

The authority changes by route; the business Trading lifecycle does not.

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
  SIM/PAPER                DEMO        LIVE
  Simulator               Broker      Broker
  authority              authority   authority
     |                      |           |
     +----------+-----------+-----------+
                |
                v
      canonical Trading evidence
```

> **One Trading lifecycle, multiple execution authorities.**

---

## 2. Route model

| Route / mode | Time source | Execution authority | External capital mutation | Purpose |
| --- | --- | --- | --- | --- |
| `SIM` | deterministic simulation scheduler | Simulator | never | historical replay/backtest/what-if execution |
| `PAPER` | live/forward application clock with current market evidence | Simulator paper authority | never | forward paper trading through the same lifecycle |
| `DEMO` | live/forward application clock | Broker Connectivity demo authority | provider demo only | broker-realistic rehearsal |
| `LIVE` | live/forward application clock | Broker Connectivity live authority | explicitly authorized live account | production execution |

`SIM` and `PAPER` may use different Simulator profiles and clocks, but neither may bypass Trading to create an independent business order lifecycle.

Route-specific differences are allowed only where reality requires them: authority transport, time/deadline source, matching/fill mechanics, market microstructure, credentials, connectivity, and explicit safety gates. Business/risk gates remain semantically paired.

---

## 3. Canonical ownership

### 3.1 Trading owns the business execution lifecycle

Trading owns canonical semantics for all four routes:

- executable request/trade-plan normalization;
- logical operation identity and idempotency;
- route and execution-authority selection;
- common business/risk gate ordering;
- canonical order lifecycle/state;
- canonical deal/fill acceptance into execution history;
- canonical position projection derived from execution evidence;
- protective-order ownership and mutation policy;
- receipt classification, including unknown outcomes;
- retry blocking and reconciliation policy;
- session/operation recovery semantics;
- immutable execution journal and trace chain;
- canonical execution evidence exposed to Analytics, Portfolio, Interfaces, and UI.

Trading may call an injected execution-authority capability but never imports Simulator or Broker implementation internals.

### 3.2 Runtime Risk owns admission for every executable route

Runtime Risk is the non-bypassable admission authority for executable actions entering the common Trading lifecycle, including `SIM` when parity execution is requested.

Risk owns:

- route/profile-appropriate risk limits;
- source-evidence validation;
- sizing approval / maximum executable size;
- stop and exposure checks;
- approval tokens where required;
- capacity reservation;
- kill-switch semantics;
- decision expiry/revalidation.

A simulation may use a simulation-specific risk profile, but Simulator must not recreate a separate executable sizing/admission engine.

### 3.3 Simulator owns execution mechanics, not a second business model

Simulator owns deterministic historical/forward synthetic authority mechanics:

- run manifests, pinned inputs/seeds/engine profiles;
- scheduler/time authority;
- intrabar path and precision models;
- matching and trigger mechanics;
- spread/slippage/commission/swap/cost models;
- target-runtime/provider semantic emulation;
- authority-side pending-order/fill/position state needed for truthful evidence;
- checkpoint/replay and perturbation/distribution mechanics;
- result projections, parity evidence, and first-divergence diagnostics.

Simulator receives Trading-approved executable work through a public capability boundary and returns authority evidence that Trading classifies/reconciles into canonical state.

### 3.4 Broker Connectivity owns demo/live authority transport

Broker Connectivity owns provider connections/credentials, environment isolation, capability discovery, request/response adaptation, broker transport, provider-truth reads/events, and demo/live transport/session state.

It does not decide business admission, construct canonical Trading state, or reinterpret Runtime Risk approval.

### 3.5 Portfolio is optional evidence, not a Runtime Risk prerequisite

Portfolio must not be a hard prerequisite for Runtime Risk.

Core Runtime Risk can admit/reject a strategy/account action with its required Data/Strategy/Catalogue/Broker evidence when Portfolio is physically absent.

Portfolio-aware allocation/budget governance uses **self-contained, immutable, versioned Portfolio evidence/projections submitted into Risk through receiver-owned public contracts**. Risk does not require a live Portfolio capability/provider to activate, query Portfolio private state, or import Portfolio implementation.

This avoids the previous cycle:

```text
Trading -> Simulator -> Analytics -> Research -> Portfolio -> Risk -> Trading
```

The implementation core is:

```text
Catalogue / Broker / Data / Strategy
                 |
                 v
           Runtime Risk
                 |
                 v
              Trading
                 |
          authority port
            /       \
           v         v
      Simulator    Broker
```

Portfolio later supplies bounded evidence to an already-complete Risk domain; this is integration, not a second Risk implementation phase.

---

## 4. Contract interpretation and migration rule

The whole-app contract-authoring foundation was created before this execution-parity decision. The semantic target is now reconciled, while physical schemas/generated clients remain implementation artifacts until their owning feature work updates them through the repository's normal contract process.

### 4.1 Trading contracts are canonical across routes

The Trading contract family is the canonical business lifecycle surface. Its implemented target must represent `SIM`, `PAPER`, `DEMO`, and `LIVE` without route-specific business state machines.

### 4.2 Simulator lifecycle records are authority/result evidence

Existing planned Simulator record identities are retained for traceability but have reconciled roles:

| Simulator concept | Reconciled role |
| --- | --- |
| `SimOrder` | Simulator authority-side matching/pending evidence; not a competing canonical Trading order |
| `SimFill` | Simulator authority fill evidence returned to Trading; accepted canonical execution becomes Trading-owned deal/evidence |
| `SimPosition` | Simulator authority snapshot/evidence used for reconciliation; canonical application projection remains Trading-owned |
| `SimTrade` | deterministic simulation/result projection derived from reconciled execution; not an independent mutable order/position state machine |
| `SizingDecision` | Simulator calculation/conformance evidence only; Runtime Risk owns executable sizing/approval |

Authority-local structures may exist where matching requires them, but contracts/tests must make the authority scope explicit and prove they cannot bypass Trading.

### 4.3 No direct construction bypass

Simulator must not construct canonical Trading operations/orders/deals/positions or Risk approvals by copying Trading/Risk private logic. Trading must not duplicate Simulator matching/fill logic or Broker provider transport.

---

## 5. Feature-level cycle avoidance

The domain workflow is intentionally reciprocal at runtime—Trading calls an authority provided by Simulator, while higher-level Simulator orchestration uses Trading—but the required feature-capability graph must remain acyclic.

The pattern is:

```text
Simulator authority feature
  provides simulator.execution-authority@N
  requires only its lower mechanics/data dependencies
            |
            v
Trading dispatch feature
  optionally consumes simulator.execution-authority@N
            |
            v
Higher Simulator run/result orchestration
  consumes Trading public capabilities
```

Therefore:

- Trading never requires the concrete Simulator package to activate; only routes that need Simulator require its authority provider.
- The Simulator authority provider must not require the higher-level Simulator runner that consumes Trading.
- Removing Simulator withdraws `SIM`/Simulator-backed `PAPER` while Broker-backed routes remain healthy.
- Removing Broker withdraws `DEMO`/`LIVE` while Simulator-backed routes remain healthy.

Portfolio-to-Risk interaction does not use a provider edge at all; it is bounded submitted evidence, so it cannot create a required cycle.

---

## 6. Gate parity

All routes traverse the same semantic business/risk categories in the same lifecycle order where applicable:

1. request/intent validation;
2. unresolved-operation/idempotency guard;
3. current evidence validation;
4. Runtime Risk decision validation;
5. approved-size/capacity validation;
6. kill-switch validation;
7. execution-plan construction;
8. pre-dispatch authority recheck;
9. exactly-once dispatch attempt;
10. receipt classification;
11. execution-event application;
12. reconciliation when authority truth is incomplete/conflicting.

Route-specific safety gates are explicit deltas, not hidden branches—for example live-mutation authorization, broker credential/session readiness, Simulator scheduler readiness, or historical-data completeness.

No route skips a business/risk gate merely because it is simulated.

---

## 7. Time and deadline parity

The common Trading lifecycle must not hard-code wall-clock behavior that makes deterministic simulation impossible.

Time/deadline authority is injected:

- `SIM` uses deterministic scheduler time;
- `PAPER`, `DEMO`, and `LIVE` use appropriate forward monotonic/wall-clock authority;
- timeout/expiry outcomes retain the same canonical semantic shape;
- no production composition silently defaults an absent time authority.

---

## 8. Ratified implementation order

The repository uses a **UI-first, dependency-ordered domain waterfall**. Waterfall is between domains; implementation remains incremental feature-by-feature inside the active domain.

| Stage | Target |
| ---: | --- |
| 0 | Shared Foundation: Contracts -> Kernel -> Composition |
| 1 | UI-first Workstation Construction (horizontal mock-backed exception; D-UI remains open) |
| 2 | Workspace |
| 3 | Plugins |
| 4 | Catalogue |
| 5 | Broker Connectivity |
| 6 | Data |
| 7 | Strategy |
| 8 | Runtime Risk — **complete entire domain**, including portfolio-aware operations against self-contained contract fixtures |
| 9 | Trading — complete common lifecycle before concrete Simulator integration |
| 10 | Simulator — real `SIM`/`PAPER` authority plus deterministic result engine |
| 11 | Analytics |
| 12 | Research |
| 13 | Portfolio — complete domain, then prove real Portfolio-evidence -> existing Risk integration |
| 14 | Orchestration |
| 15 | Interfaces |
| 16 | Final D-UI de-mock and complete-system integration |

Critical relative order:

```text
Broker -> Data -> Strategy -> Runtime Risk -> Trading -> Simulator -> Analytics -> Research -> Portfolio
```

### 8.1 Runtime Risk is not split across waterfall stages

The complete Runtime Risk domain is finished at Stage 8.

Portfolio-aware FRs are implemented at Stage 8 using their receiver-owned Risk contracts plus deterministic self-contained Portfolio projection/evidence fixtures and explicit absent-evidence behavior. They do not require a real Portfolio runtime provider.

Stage 13 does not “finish Risk.” It proves production cross-domain integration by creating real Portfolio evidence and submitting it through the already-ratified Risk boundary. Any incompatibility is an explicit versioned contract change, not a hidden second Risk implementation stage.

### 8.2 Trading before Simulator uses authority conformance fixtures

Trading is completed/tested against its versioned execution-authority port plus deterministic authority conformance doubles. Simulator then supplies the real `SIM`/`PAPER` authority implementation at Stage 10.

This preserves domain waterfall completion without introducing package or required capability cycles.

---

## 9. Canonical documentation reconciliation status

The architectural reconciliation requested on 2026-08-25 has been applied to:

- [x] `docs/dev/IMPLEMENTATION_ORDER.md` — replaced Agile increments/duplicated FR registry with UI-first domain waterfall and Risk -> Trading -> Simulator ordering.
- [x] `docs/PROJECT.md` — dependency graph/workflows/release semantics reconciled; hard `Portfolio -> Risk` and `Simulator -> Trading` implementation dependencies removed.
- [x] `app/services/risk/README.md` — common-route admission and Portfolio independence adopted.
- [x] `app/services/trading/README.md` — canonical four-route Trading lifecycle adopted.
- [x] `app/services/simulator/README.md` — authority/result ownership adopted; duplicate executable sizing/business lifecycle removed.
- [ ] `app/contracts/README.md` — semantic inventory wording still requires final documentation sweep.
- [ ] Physical `app/contracts/{common,risk,trading,simulator}/`, generated schemas/TypeScript, and contract tests — **not modified by this documentation-only reconciliation**. They must be reconciled as implementation artifacts before affected product features are implemented/accepted.
- [ ] Remaining domain/UI/Interfaces/Analytics/Research/Portfolio documentation — audit stale summary wording where it conflicts with this cross-domain decision.

The checked canonical registries above must be used for planning. Existing physical contract scaffolding never authorizes implementation of the superseded parallel-lifecycle model.

---

## 10. Mandatory acceptance evidence

The implementation must eventually prove:

1. equivalent intent/risk evidence produces same canonical Trading request shape independent of authority-specific fields;
2. `SIM`, `PAPER`, `DEMO`, `LIVE` execute same business/risk gate categories/order;
3. Simulator/Broker cannot increase or replace Risk-approved quantity;
4. switching route changes authority/time/safety mechanics, not Trading state machine;
5. accepted/rejected/unknown/partial/fill authority outcomes normalize into same Trading semantics;
6. no authority permits blind retry after unknown outcome;
7. authority order/deal/position evidence reconciles through same Trading policy;
8. identical pinned simulation manifests/seeds/providers reproduce identical authority evidence and canonical Trading result;
9. core Runtime Risk starts/governs account/strategy actions when Portfolio is physically absent;
10. real Portfolio evidence adds portfolio-aware review without becoming Risk dependency;
11. removing Simulator withdraws Simulator-backed routes only;
12. removing Broker withdraws Broker-backed routes only;
13. no reverse private implementation imports;
14. required feature-capability graph remains acyclic;
15. parity claims are bounded/falsifiable; empirical spread/slippage/latency equivalence is never claimed without evidence.

---

## 11. Non-goals

This decision does **not** require simulated fills to equal live fills. Real venues contain latency, queue position, liquidity, spread dynamics, slippage, rejects, outages, and undocumented behavior that historical replay may only model approximately.

Parity targets:

- same business lifecycle;
- same applicable risk/admission semantics;
- same canonical request/response families;
- same business state-transition rules;
- same safety/idempotency/reconciliation policy;
- explicit, measurable route-specific execution mechanics.

Simulation realism improves by calibrating Simulator authority behavior against real broker evidence, not by cloning Trading inside Simulator.

---

## 12. Final architecture statement

```text
Strategy
   |
   v
Runtime Risk
   |
   v
Trading  <--- single canonical business execution lifecycle
   |
   +-- SIM   ----> Simulator historical authority
   +-- PAPER ----> Simulator forward-paper authority
   +-- DEMO  ----> Broker demo authority
   +-- LIVE  ----> Broker live authority
   |
   v
Canonical execution evidence
   |
   +--> Simulator result commit / Analytics
   +--> Research
   +--> Portfolio
   +--> Interfaces / UI
```

Any future design that introduces a second route-specific business order lifecycle or executable Risk authority inside Simulator is an architecture regression unless this decision is explicitly superseded.