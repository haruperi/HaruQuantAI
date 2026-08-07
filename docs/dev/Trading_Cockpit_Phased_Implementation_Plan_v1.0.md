
# HaruQuantAI Trading Cockpit Simulator
## Phased Domain-Ordered Implementation Plan

**Document ID:** `HQA-TCS-IMP-001`
**Version:** `1.0`
**Date:** `2026-08-04`
**Status:** Implementation baseline
**Source specification:** `TCS-TRADING-COCKPIT-001`, Version `1.2`
**Target application:** Existing HaruQuantAI application
**Implementation model:** Expand the current domains in their established order; do not create a parallel Trading Cockpit application.

> **Purpose:** This document translates the complete Trading Cockpit specification into an ordered implementation program for the existing HaruQuantAI codebase. It is a delivery plan, not a replacement for the normative specification. Every capability in the specification remains in scope; the phases determine build order, integration order, and acceptance evidence.

> **Safety boundary:** The Trading Cockpit shall operate only through deterministic simulation, historical replay, paper trading, or explicitly approved broker sandboxes/testnets. The implementation plan does not authorize production live-money order routing.

---

# 1. Implementation Objective

Build the Trading Cockpit by extending these existing HaruQuantAI domains in this exact order:

1. `Utils`
2. `Brokers`
3. `Data`
4. `Indicators`
5. `Strategy`
6. `Risk`
7. `Trading`
8. `Simulator`
9. `Analytics`
10. `Optimization`
11. `Research`
12. `Portfolio`
13. `Agentic`
14. `UI-API`

A final cross-domain integration and release phase follows the fourteen domain phases. It does not create another product domain; it verifies that the completed domains satisfy the end-to-end specification.

The implementation shall preserve HaruQuantAI's existing domain ownership. Trading Cockpit behavior must be added to the domain that already owns the underlying responsibility. The project shall **not** introduce a new top-level `trading_cockpit/` service tree that duplicates `risk/`, `trading/`, `simulator/`, `portfolio/`, or any other current domain.

---

# 2. Delivery Principles

## 2.1 Extend Before Creating

Every work package begins with a current-state audit and receives one classification:

| Classification | Meaning | Required action |
| --- | --- | --- |
| `REUSE` | Existing behavior already satisfies the required contract and tests | Preserve it; add traceability and integration evidence only |
| `EXTEND` | Existing behavior is correct but incomplete | Add the missing fields, states, rules, tests, and exports without creating a competing implementation |
| `CREATE` | No suitable behavior exists | Add one cohesive feature within the owning domain |
| `REFACTOR` | Existing behavior conflicts with the specification or is duplicated | Migrate callers to one authoritative implementation; preserve compatibility only where necessary |
| `DEFERRED_INTEGRATION` | The consumer phase arrives before a later provider domain is expanded | Define a narrow consumer port and test fake; replace the fake when the provider phase is completed |
| `NOT_APPLICABLE` | The domain does not require a database, UI surface, or other checklist item | Record the reason explicitly rather than leaving the audit blank |

No work package may be marked complete merely because a similarly named class or function exists. Its behavior, state transitions, edge cases, persistence, and tests must satisfy the specification.

## 2.2 Workflow-First Implementation

Features shall be implemented to support complete workflows, not as isolated utilities. The primary workflows are:

```text
Session Power-Up
  -> Pre-Market Preparation
  -> Cockpit Armed
  -> Setup Scan
  -> Trade Plan
  -> Risk Validation
  -> Order Staging
  -> Order Execution
  -> Position Management
  -> Exit
  -> Reconciliation
  -> Journal and Debrief
  -> Session Secured
```

Emergency workflows interrupt the normal path:

```text
Flash Crash / Black Swan
API or Network Failure
Maximum Daily Drawdown Breach
Margin or Stress Survival Emergency
Recovery or State-Integrity Failure
```

## 2.3 Deterministic Core, Advisory Intelligence

All authoritative calculations and state changes must remain deterministic:

- Market and instrument eligibility.
- Position size and risk.
- Drawdown and account lockout.
- Order, fill, position, and ledger state.
- Replay time and no-lookahead enforcement.
- Scenario triggers.
- Alerts and checklist state.
- Scoring and qualification.

Agentic components may explain, coach, summarize, or recommend. They may not become the source of truth for risk, accounting, order state, score, or emergency interlocks.

## 2.4 Provider-Owned Models, Consumer-Owned Ports

The domain that owns a concept owns its canonical model. Earlier phases may define a narrow port for a later provider, but they may not implement the later domain's business logic.

Examples:

- `Risk` may define the fields it needs from a `PortfolioRiskView`, but `Portfolio` owns authoritative balance, equity, margin, exposure, and ledger calculations.
- `Risk` may consume an expectancy-eligibility port before `Research` is expanded, but `Research` owns approved evidence and profile governance.
- `Trading` may emit economic execution events before `Portfolio` is expanded, but `Portfolio` owns ledger posting and valuation.
- `Brokers` owns broker and venue capability profiles; `Data` owns point-in-time market observations and dataset integrity.

## 2.5 No Silent Fallbacks

If a required profile, state, timestamp, conversion rate, or broker result is unknown, the system shall enter a visible restricted or unknown state. It shall never manufacture a default that creates false certainty.

## 2.6 Quality Gates

Each phase shall preserve the current HaruQuantAI quality toolchain and project commands. Where the repository currently uses `uv run --frozen`, Ruff, strict mypy, pytest, and coverage, those remain the authoritative validation route.

A domain phase is not complete until:

- The domain README and feature registry are updated.
- Functional requirements and workflows are traceable to code and tests.
- Public exports are intentional and documented.
- Database changes, or an explicit `NOT_APPLICABLE` decision, are recorded.
- Unit and integration tests cover positive, negative, and boundary behavior.
- A runnable usage example demonstrates the domain behavior.
- Telemetry and failure states are observable.
- The domain's UI/API read contract is published, even if the web cockpit is not connected until Phase 14.

---

# 3. Domain Completion Audit

Use this audit for every domain phase.

| Audit Area | Completion requirement |
| --- | --- |
| `README` | Feature table, responsibilities, public exports, dependencies, workflows, safety boundaries, and status are current |
| `Database` | Required entities and migrations exist, or `NOT_APPLICABLE` is justified |
| `Unit Tests` | Deterministic unit, property/boundary, and error-path tests pass |
| `FR Usage` | Every implemented requirement has a real usage or acceptance test; no dead contract-only feature is marked complete |
| `Workflow` | The feature participates in at least one documented end-to-end or domain workflow |
| `UI Connection` | A stable API/read-model/event contract exists; actual cockpit integration is completed in Phase 14 |
| `Telemetry` | State transitions, failures, warnings, and important decisions emit structured events |
| `Persistence` | Durable state is restored correctly where the domain owns persistent consequences |
| `Security and Safety` | Simulation isolation, permissions, validation, and fail-closed behavior are tested |
| `Acceptance Evidence` | Test output, usage output, schema evidence, and traceability records are stored in the implementation handoff |

Recommended domain feature-registry row:

| Status | Work Package | Requirement / Specification Mapping | Responsibility | Files / Modules | Public Exports | Database | Tests | Usage / Workflow | UI/API Contract |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

---

# 4. Phase and Milestone Map

| Phase | Domain / Scope | Principal outcome | Main specification coverage |
| ---: | --- | --- | --- |
| `0` | Program baseline and traceability | Current-state inventory, contracts, gap matrix, and protected implementation baseline | Entire specification |
| `1` | Utils | Shared deterministic primitives without financial business logic | Sections 5-13 and 17 support contracts |
| `2` | Brokers | Broker/venue capabilities, health, read/write sandbox routes, normalized account/order state | Sections 5, 6, 10, 12 |
| `3` | Data | Point-in-time L1/L2, event/calendar data, dataset integrity, replay-ready records | Sections 1, 5, 7, 9, 12 |
| `4` | Indicators | Cockpit market gauges and no-lookahead analytical signals | Sections 1, 2, 4, 15 |
| `5` | Strategy | Versioned playbooks, setup evaluation, trade plans, and operating envelopes | Sections 2, 4, 16, 17 |
| `6` | Risk | Policy resolution, sizing, trade gates, drawdown, stress risk, emergency governance | Sections 2-4, 15, 16 |
| `7` | Trading | Authoritative order and execution lifecycle, protection, idempotency, reconciliation | Sections 2, 3, 6, 10, 12 |
| `8` | Simulator | Session/checklist engine, clock, replay, scenarios, fills, recovery, game modes | Sections 2, 3, 7, 9, 10, 12, 13 |
| `9` | Analytics | Journal, process-first scoring, debrief, qualification evidence, execution analytics | Sections 4, 11, 13, 14 |
| `10` | Optimization | Calibrated simulator/strategy parameters with no leakage or safety bypass | Sections 12, 15, 16 |
| `11` | Research | Evidence packages, stress research, scenario evidence, approved expectancy governance | Sections 7, 9, 15, 16 |
| `12` | Portfolio | Ledger, accounting, valuation, margin, exposure, drawdown, stress aggregation | Sections 1, 4, 6, 8, 15, 17 |
| `13` | Agentic | Read-safe cockpit coaching, scenario instruction, research assistance, and debrief support | Sections 4, 13, 14 plus deterministic boundaries |
| `14` | UI-API | Complete web cockpit, real-time controls, alerts, training, replay, and API surface | Sections 1-4, 13, 14, 17 |
| `15` | System integration and release | Full acceptance against all 40 specification criteria | Entire specification |

## 4.1 Integration Checkpoints

| Checkpoint | Completed phases | Demonstrable result |
| --- | --- | --- |
| `IC-1 — Market Foundation` | `0-3` | A versioned instrument can be selected; market, calendar, venue, and health data are replay-ready and auditable |
| `IC-2 — Decision Foundation` | `4-6` | A setup can become an immutable trade plan and receive a deterministic allow/block/resize decision |
| `IC-3 — Headless Trading Mission` | `7-8` | A complete simulated session can run without a web UI, including fills, emergencies, replay, and recovery |
| `IC-4 — Measured Training Loop` | `9-11` | The session produces journals, scores, evidence-backed expectancy decisions, and calibrated scenarios |
| `IC-5 — Financial Authority` | `12` | Every fill and cost rebuilds into balanced ledger, portfolio, margin, exposure, and stress state |
| `IC-6 — Intelligent Cockpit` | `13-14` | The user can operate the full web cockpit with deterministic controls and advisory agents |
| `IC-7 — Release Candidate` | `15` | Compound failures, golden runs, recovery, security, and all specification acceptance criteria pass |

---

# 5. Specification-to-Domain Ownership

| Specification capability | Primary owner | Supporting domains |
| --- | --- | --- |
| Simulation/assessment modes | Simulator | Risk, Analytics, UI-API |
| Global session and checklist state | Simulator | Trading, Risk, UI-API |
| Cockpit panel presentation | UI-API | All data-producing domains |
| Instrument and venue profile | Brokers | Data, Portfolio, Risk, Trading |
| Market data integrity and point-in-time visibility | Data | Utils, Simulator, Research |
| Market gauges and regime indicators | Indicators | Data, UI-API |
| Strategy playbook and trade plan | Strategy | Indicators, Research, Risk |
| Trading policy and effective-rule resolution | Risk | Brokers, Strategy, Portfolio, Research |
| Order and execution state | Trading | Brokers, Risk, Simulator, Portfolio |
| Position execution lifecycle | Trading | Portfolio, Risk, Brokers |
| Simulation clock and replay identity | Simulator | Utils, Data, Analytics |
| Scenario definition and event injection | Simulator | Data, Research, Risk, Brokers |
| Latency, queue, fill, and slippage simulation | Simulator | Brokers, Trading, Data |
| Immutable economic ledger | Portfolio | Trading, Brokers, Simulator |
| Valuation and multi-currency accounting | Portfolio | Data, Brokers, Utils |
| Stress loss and gap risk | Risk | Portfolio, Research, Data |
| Approved expectancy evidence | Research | Strategy, Risk, Analytics |
| Journal, scoring, and debrief | Analytics | Simulator, Trading, Risk, Agentic, UI-API |
| Player qualification and progression state | Analytics | Simulator, UI-API, Agentic |
| Alert source state | Owning business domain | Simulator for lifecycle; UI-API for presentation |
| Persistence and crash recovery | Each state-owning domain | Utils infrastructure; Simulator orchestration |
| Verification and traceability | Each domain | Phase 15 system QA |

---

# 6. Cross-Domain Contract Registry

| Contract | Authoritative domain | Main consumers | Introduced / finalized |
| --- | --- | --- | --- |
| `ProfileRef`, `VersionRef`, `EventEnvelope`, `ValidationResult` | Utils | All domains | Phase 1 |
| `InstrumentVenueProfile` | Brokers | Data, Risk, Trading, Simulator, Portfolio, UI-API | Phase 2 |
| `BrokerHealth`, `BrokerOrderSnapshot`, `BrokerPositionSnapshot` | Brokers | Risk, Trading, Simulator, UI-API | Phase 2 |
| `MarketEvent`, `MarketSnapshot`, `OrderBookSnapshot`, `EconomicEvent` | Data | Indicators, Strategy, Risk, Simulator, Research, UI-API | Phase 3 |
| `IndicatorSnapshot`, `MarketRegimeSnapshot`, `LiquiditySnapshot` | Indicators | Strategy, Risk, Simulator, UI-API | Phase 4 |
| `StrategyProfile`, `SetupEvaluation`, `TradePlan` | Strategy | Risk, Trading, Simulator, Analytics, UI-API | Phase 5 |
| `TradingPolicyProfile`, `RiskDecision`, `EmergencyDirective`, `AccountLockState` | Risk | Trading, Simulator, Analytics, Portfolio, UI-API | Phase 6 |
| `OrderIntent`, `OrderState`, `ExecutionEvent`, `ExecutionPositionState` | Trading | Brokers, Simulator, Portfolio, Analytics, UI-API | Phase 7 |
| `SimulationClock`, `ReplayIdentity`, `ScenarioDefinition`, `ChecklistState`, `AlertEvent` | Simulator | All gameplay consumers | Phase 8 |
| `Scorecard`, `Debrief`, `JournalEntry`, `PlayerQualification` | Analytics | Agentic, UI-API, Research | Phase 9 |
| `OptimizationStudy`, `CalibrationProfile` | Optimization | Simulator, Strategy, Risk, Research | Phase 10 |
| `ResearchEvidence`, `ApprovedExpectancyProfile`, `ScenarioEvidence` | Research | Strategy, Risk, Simulator, Analytics, Agentic | Phase 11 |
| `PortfolioState`, `LedgerEntry`, `ValuationPolicy`, `FXConversionRate` | Portfolio | Risk, Trading, Simulator, Analytics, UI-API | Phase 12 |
| `AgentRecommendation`, `AgentToolDecision`, `CoachingMessage` | Agentic | UI-API, Analytics | Phase 13 |
| API DTOs and cockpit read models | UI-API | Web client and external approved clients | Phase 14 |

---

# 7. Target End-to-End Runtime Flow

## 7.1 Pre-Market

```text
UI-API requests session start
  -> Simulator creates SimulationClock, ReplayIdentity, and Checklist session
  -> Brokers supplies instrument/venue capabilities and broker health
  -> Data supplies point-in-time market, calendar, and venue state
  -> Indicators calculates cockpit market gauges
  -> Portfolio supplies authoritative account state
  -> Risk resolves effective policy and pre-market restrictions
  -> Simulator satisfies or blocks checklist steps from actual domain state
  -> UI-API displays COCKPIT_ARMED only when all mandatory gates are valid
```

## 7.2 Trade Launch

```text
Strategy creates TradePlan
  -> Risk validates entry, stop, reward, size, liquidity, news, margin, correlation, drawdown, and stress
  -> Trading persists OrderIntent before submission
  -> Brokers or Simulator execution route accepts/rejects the request
  -> Trading processes acknowledgement, partial fill, fill, cancel, or UNKNOWN state
  -> Portfolio posts economic events and recalculates account state
  -> Risk reevaluates residual and aggregate risk
  -> Simulator updates checklist, alerts, and score events
  -> UI-API displays authoritative state
```

## 7.3 Emergency

```text
Any domain emits a critical condition
  -> Simulator applies emergency priority
  -> Risk disables new exposure and issues allowed reduction actions
  -> Trading keeps cancel/protection/reduction/closure actions available
  -> Brokers and Data expose current health and freshness
  -> Portfolio recalculates survival state
  -> UI-API presents a latched emergency checklist
  -> Analytics records response time and process quality
  -> Recovery requires authoritative reconciliation and explicit re-arming
```

## 7.4 Post-Market

```text
Trading and Portfolio reconcile orders, fills, positions, protection, and ledger
  -> Analytics completes journal, execution review, process score, and qualification evidence
  -> Simulator validates replay integrity and durable session closure
  -> UI-API archives debrief and resets temporary cockpit state
```

---

# 8. Phase 0 — Program Baseline, Gap Audit, and Traceability

## 8.1 Goal

Create a protected baseline and determine which Trading Cockpit requirements are already implemented, partially implemented, missing, or conflicting in each current domain. This phase prevents duplicate features and preserves existing owner changes.

## 8.2 Work Packages

| ID | Work package | Required result |
| --- | --- | --- |
| `TC-IMP-BASE-01` | Repository baseline | Record branch, commit SHA, worktree status, modified/untracked files, Python version, dependency-manager version, lockfile state, database migration head, and exact audit timestamp |
| `TC-IMP-BASE-02` | Domain inventory | Record each domain's README, feature folders, public exports, database entities, tests, usage examples, workflows, and UI/API consumers |
| `TC-IMP-BASE-03` | Specification decomposition | Assign every normative specification requirement and acceptance criterion to one primary owner domain and its consumers |
| `TC-IMP-BASE-04` | Gap matrix | Classify every planned work package as `REUSE`, `EXTEND`, `CREATE`, `REFACTOR`, or `DEFERRED_INTEGRATION` |
| `TC-IMP-BASE-05` | Contract inventory | Record current DTOs, protocols, enums, event schemas, and versioning rules; identify collisions with required contracts |
| `TC-IMP-BASE-06` | Data-store inventory | Record current tables/collections, migration tooling, ownership, unique keys, event stores, and retention rules |
| `TC-IMP-BASE-07` | Test baseline | Run and record lint, formatting, typing, unit/integration tests, coverage, and known failures before Trading Cockpit changes |
| `TC-IMP-BASE-08` | Safety baseline | Prove that production live-write routes are disabled or excluded from Trading Cockpit modes |
| `TC-IMP-BASE-09` | Documentation set | Establish `docs/trading-cockpit/` or the project's equivalent location for the specification, this plan, traceability, ADRs, schemas, and acceptance evidence |
| `TC-IMP-BASE-10` | Change-control rule | Define how existing public APIs are extended, deprecated, migrated, and tested without silently breaking current HaruQuantAI workflows |

## 8.3 Required Planning Artifacts

- `trading-cockpit-gap-matrix.md`
- `trading-cockpit-traceability-matrix.md`
- `trading-cockpit-contract-registry.md`
- `trading-cockpit-database-ownership.md`
- `trading-cockpit-test-baseline.md`
- One ADR confirming that the cockpit is implemented through the existing domains rather than a parallel service tree.

## 8.4 Exit Gate

Phase 0 is complete when every planned work package has an owner, dependency, current-state classification, and acceptance evidence target. No implementation phase may start from an assumed gap.

---

# 9. Phase 1 — Utils

## 9.1 Goal

Provide the shared deterministic primitives required by later domains while keeping all financial and trading business rules out of `Utils`.

## 9.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-UTIL-01` | Identity and version references | Strong IDs for sessions, replays, scenarios, profiles, orders, fills, ledger entries, events, players, and branches; explicit profile/version references |
| `TC-IMP-UTIL-02` | Decimal unit primitives | Safe representations and validation helpers for money, price, quantity, percentage, basis points, ticks, points, lots/contracts/shares, and currencies |
| `TC-IMP-UTIL-03` | Time primitives | UTC normalization, source/event/receive/process timestamps, venue-local conversion, monotonic sequence support, and explicit clock interfaces |
| `TC-IMP-UTIL-04` | State-machine primitives | Generic transition result, allowed-transition validation, terminal-state handling, regression events, and transition audit records |
| `TC-IMP-UTIL-05` | Validation result model | `PASS`, `WARN`, `BLOCK`, `FAIL`, `UNKNOWN`, structured reason codes, corrective actions, severity, and source evidence references |
| `TC-IMP-UTIL-06` | Event envelope and sequencing | Event ID, source ID, source sequence, correlation/causation IDs, deduplication key, integrity hash, and schema version |
| `TC-IMP-UTIL-07` | Idempotency primitives | Idempotency-key generation, ownership, TTL/persistence semantics, duplicate detection, and exactly-once economic-intent helpers |
| `TC-IMP-UTIL-08` | Profile loading and schema validation | Versioned profile references, strict schema validation, immutable loaded representation, compatibility checks, and no-silent-fallback behavior |
| `TC-IMP-UTIL-09` | Error and health taxonomy | Transient/permanent/integrity/policy/data-stale/unknown-state categories plus retryability and operator-action metadata |
| `TC-IMP-UTIL-10` | Structured audit and telemetry | Common event metadata, privacy-safe serialization, integrity hashing, and append-only audit interfaces |
| `TC-IMP-UTIL-11` | Deterministic random streams | Seeded stream names and reproducible pseudo-random draws for simulator scenarios and fills |
| `TC-IMP-UTIL-12` | Persistence transaction helpers | Transaction/outbox or equivalent durable-intent primitives used by state-owning domains without moving domain records into Utils |

## 9.3 Candidate Feature Modules — Only If Absent

```text
utils/
├── identity/
├── units/
├── time/
├── state_machine/
├── validation/
├── events/
├── idempotency/
├── profiles/
├── health/
├── telemetry/
├── deterministic_random/
└── persistence/
```

These are logical feature boundaries, not mandatory filenames. Reuse existing cohesive modules where they already satisfy the contract.

## 9.4 Public Contracts

- `ProfileRef`
- `VersionRef`
- `EventEnvelope`
- `ValidationResult`
- `ValidationIssue`
- `StateTransition`
- `HealthState`
- `IdempotencyKey`
- `ClockPort`
- `DeterministicRandomPort`

## 9.5 Persistence Impact

Utils may own schema metadata, idempotency infrastructure, or outbox infrastructure only if the current architecture already places those concerns there. Domain economic records remain in their owner domains.

## 9.6 Required Tests

- Decimal arithmetic and round-down behavior at tick/quantity boundaries.
- Invalid unit mixing is rejected.
- UTC and venue-local conversions survive daylight-saving transitions.
- Event sequences are monotonic and duplicates are detected by ID, not timestamp.
- Identical seeds and stream names reproduce identical draws.
- Profile version mismatch fails closed.
- State transitions reject impossible edges.
- Integrity hashes change when protected event content changes.
- Idempotency keys cannot map to two economic intents.

## 9.7 Exit Criteria

- Later domains can import stable primitives through public exports.
- No market, strategy, risk, order, or accounting rule has leaked into Utils.
- All primitives are deterministic, typed, documented, and covered by boundary tests.

---

# 10. Phase 2 — Brokers

## 10.1 Goal

Expand broker adapters into authoritative broker/venue capability and state boundaries for simulation, paper, and approved sandbox routes.

## 10.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-BRK-01` | Instrument and venue profile | Authoritative `InstrumentVenueProfile` covering symbol identity, asset class, venue, tick size, price precision, quantity step, contract multiplier, session calendar, order types, time-in-force, margin, shorting, settlement, halt, lifecycle, and eligibility rules |
| `TC-IMP-BRK-02` | Adapter capability matrix | Declare supported reads/writes, order types, bracket/OCO behavior, netting/hedging, partial fills, modifications, cancellation semantics, and sandbox availability for each adapter |
| `TC-IMP-BRK-03` | Broker health model | Authentication, session status, API heartbeat, WebSocket status, latency, error rate, maintenance state, and route readiness |
| `TC-IMP-BRK-04` | Normalized account snapshot | Balance/equity fields as reported by the broker, margin fields, currency, permissions, and source timestamp without replacing Portfolio accounting |
| `TC-IMP-BRK-05` | Normalized order/fill/position snapshots | Stable broker-facing models with authoritative IDs, source sequences, receive times, raw payload references, and uncertainty state |
| `TC-IMP-BRK-06` | Safe order command port | Submit, cancel, replace, attach protection, reduce, and close commands with idempotency and explicit acknowledgement semantics |
| `TC-IMP-BRK-07` | Unknown-state preservation | Timeouts and lost acknowledgements produce `UNKNOWN`, not assumed rejection or cancellation |
| `TC-IMP-BRK-08` | Read-based reconciliation port | Query authoritative open orders, fills, positions, balances, and venue status for Trading and Simulator recovery |
| `TC-IMP-BRK-09` | Primary/backup route discipline | Health-aware fallback for reads or recovery without duplicate order submission or silent cross-broker rerouting |
| `TC-IMP-BRK-10` | Simulation/sandbox isolation | Explicit environment guard proving that Trading Cockpit writes cannot reach production accounts |
| `TC-IMP-BRK-11` | Broker event normalization | Convert adapter callbacks/polls into ordered, deduplicated `EventEnvelope` records |
| `TC-IMP-BRK-12` | Broker contract test kit | One reusable adapter conformance suite applied to every enabled HaruQuantAI broker route |

## 10.3 Candidate Feature Modules — Only If Absent

```text
brokers/
├── instrument_profiles/
├── capabilities/
├── health/
├── snapshots/
├── commands/
├── events/
├── reconciliation/
└── conformance/
```

Do not implement simulated queue/fill logic here. `Simulator` owns the simulation model; `Brokers` exposes the simulation adapter through the same normalized contract.

## 10.4 Database and Persistence

Potential owned records:

- Versioned instrument/venue profiles.
- Broker route configuration references.
- Source event cursors and deduplication checkpoints.
- Raw broker payload references where required for audit.
- Environment and account permission metadata.

Order intents and internal order state remain owned by `Trading`; financial ledger entries remain owned by `Portfolio`.

## 10.5 Required Tests

- Contract tests for every configured adapter.
- Unsupported order types fail before submission.
- Tick and quantity constraints are enforced from the selected profile.
- Timeout after submission returns `UNKNOWN` and prohibits blind resubmission.
- Cancel-pending remains executable until cancellation confirmation.
- Repeated broker events are deduplicated exactly once.
- Primary/backup recovery cannot create duplicate orders.
- Production environment credentials or routes are rejected by Trading Cockpit configuration.
- Health transitions are observable and timestamped.

## 10.6 Exit Criteria

- One stable broker contract supports current adapters and the future Simulator adapter.
- Every tradable instrument has an explicit eligible/ineligible profile state.
- Trading can discover authoritative broker state after a disconnect without adapter-specific logic.

---

# 11. Phase 3 — Data

## 11.1 Goal

Provide replay-safe, point-in-time market and reference data that can drive cockpit gauges, strategies, risk, scenarios, and execution simulation without lookahead.

## 11.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-DATA-01` | Unified market event model | Normalize quotes, trades, bars, depth updates, venue state, halts, auctions, corporate actions, and economic events |
| `TC-IMP-DATA-02` | Level 1 snapshots | Bid, ask, last, spread, volume, source/event/receive times, and quote freshness |
| `TC-IMP-DATA-03` | Level 2 order-book state | Ordered depth levels, update sequence, reset/snapshot semantics, crossed-book detection, and executable depth calculations |
| `TC-IMP-DATA-04` | Point-in-time economic calendar | Original release, publication time, later revisions, impact classification, and replay visibility timestamps |
| `TC-IMP-DATA-05` | Session and venue calendar | Market hours, holidays, daylight-saving rules, halts, reopening states, and close/roll windows |
| `TC-IMP-DATA-06` | Data-integrity engine | Stale data, gaps, duplicate events, crossed markets, out-of-order sequences, clock drift, and primary/backup disagreement |
| `TC-IMP-DATA-07` | Dataset manifest and hashing | Dataset ID/version, source provenance, coverage, point-in-time status, content hash, and compatibility metadata |
| `TC-IMP-DATA-08` | Replay data package | Stream events in deterministic source order with explicit availability timestamps and no future visibility |
| `TC-IMP-DATA-09` | Bar construction | Closed-bar semantics, incomplete-bar state, multi-timeframe resampling, and no-lookahead alignment |
| `TC-IMP-DATA-10` | Multi-symbol alignment | Datetime-indexed alignment across symbols with declared missing-data behavior; no silent forward knowledge |
| `TC-IMP-DATA-11` | Market snapshot service | Produce bounded current snapshots for Strategy, Risk, Simulator, Analytics, and UI-API |
| `TC-IMP-DATA-12` | Data provenance and quality score | Source, license/use classification, trust, revisions, scope, coverage, and quality state |
| `TC-IMP-DATA-13` | Replay evidence export | Reconstruct the exact visible data set for any player decision or automated action |

## 11.3 Candidate Feature Modules — Only If Absent

```text
data/
├── market_events/
├── quotes/
├── order_book/
├── economic_calendar/
├── sessions/
├── integrity/
├── datasets/
├── replay_stream/
├── bars/
├── alignment/
└── snapshots/
```

## 11.4 Database and Storage

Potential owned records:

- Dataset manifests and hashes.
- Point-in-time economic releases and revisions.
- Session/venue calendars.
- Corporate actions and lifecycle events.
- Raw/normalized market-event references.
- Data-quality incidents and repair lineage.

Large replay data may remain in files/object storage while manifests and hashes are stored in the application database.

## 11.5 Required Tests

- No record is emitted before its availability timestamp.
- Economic revisions become visible only at revision publication time.
- Incomplete bars cannot be used as closed bars.
- Multi-timeframe alignment uses only closed higher-timeframe bars.
- Replaying the same manifest produces identical event ordering.
- Stale and out-of-order data trigger explicit integrity states.
- L2 reset and incremental update sequences rebuild the expected book.
- Dataset hash mismatch invalidates official replay use.
- Multi-symbol alignment preserves datetime indices and declared gaps.

## 11.6 Integration Checkpoint `IC-1`

Demonstrate one eligible instrument with:

- Versioned broker/venue profile.
- Point-in-time session and calendar state.
- L1 and, where available, L2 replay.
- Data-health status.
- Deterministic dataset hash and replay sequence.

---

# 12. Phase 4 — Indicators

## 12.1 Goal

Implement the deterministic analytical outputs behind the market-flight instruments. Indicators provide measured state; they do not approve trades or own risk policy.

## 12.2 Planned Work Packages

| ID | Cockpit output | Responsibility |
| --- | --- | --- |
| `TC-IMP-IND-01` | Market speed | Composite momentum, realized volatility, ATR/range expansion, volume acceleration, and order-flow velocity with `SLOW/NORMAL/FAST/EXTREME` bands |
| `TC-IMP-IND-02` | Market regime | Point-in-time classification such as trend, range, breakout, event, unstable, or low-liquidity with confidence and reason codes |
| `TC-IMP-IND-03` | Trend strength and higher-timeframe direction | Strategy-independent directional and strength measurements |
| `TC-IMP-IND-04` | Support/resistance and structural levels | Deterministic levels, pivots, volume profile zones, gaps, and invalidation references with timestamps |
| `TC-IMP-IND-05` | Liquidity pressure | Spread, executable depth, imbalance, volume, fill-probability inputs, and liquidity regime |
| `TC-IMP-IND-06` | Order-flow and depth features | Imbalance, pressure, queue/depth changes, sweep events, and liquidity gaps |
| `TC-IMP-IND-07` | Volatility envelope | Current versus historical volatility, strategy-operating-envelope inputs, and extreme-event thresholds |
| `TC-IMP-IND-08` | Chart-pattern evidence | Bounded, deterministic pattern observations used by Strategy; no direct trade approval |
| `TC-IMP-IND-09` | Indicator snapshot contract | Value, unit, state, timestamp, source data range, completeness, confidence, and data-health dependency |
| `TC-IMP-IND-10` | Closed-input enforcement | Reject incomplete bars, future data, stale snapshots, or incompatible timeframes |

## 12.3 Candidate Feature Modules — Only If Absent

```text
indicators/
├── market_speed/
├── regime/
├── trend/
├── structure/
├── liquidity/
├── order_flow/
├── volatility/
├── patterns/
└── snapshots/
```

Reuse existing indicator implementations where mathematically correct; add cockpit adapters rather than duplicating formulas.

## 12.4 Required Tests

- Golden-value tests for each calculation.
- Boundary tests at regime/state thresholds.
- No future or incomplete inputs.
- Identical data produces identical snapshots.
- Stale data propagates an unavailable/restricted state rather than a plausible value.
- Multi-timeframe indicators use the correct closed-bar alignment.
- Composite gauges expose component contributions for debrief transparency.

## 12.5 Exit Criteria

- Strategy and UI can consume stable indicator snapshots without reading indicator internals.
- Every displayed gauge value has a timestamp, unit, data-health state, and reproducible calculation.

---

# 13. Phase 5 — Strategy

## 13.1 Goal

Represent approved trading playbooks and convert a valid market setup into a complete, versioned `TradePlan` before Risk or Trading can act.

## 13.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-STRAT-01` | Strategy profile | Versioned identity, permitted instruments/sessions/regimes, indicator dependencies, entry/exit rules, invalidation rules, and automation permissions |
| `TC-IMP-STRAT-02` | Strategy playbook | Human-readable and machine-evaluable setup definition used by pre-market planning and debrief |
| `TC-IMP-STRAT-03` | Setup evaluation | Return `MATCH`, `NO_MATCH`, `STALE`, `REGIME_MISMATCH`, or `INSUFFICIENT_EVIDENCE` with source snapshots |
| `TC-IMP-STRAT-04` | Trade-plan builder | Create the canonical `TradePlan`: direction, entry rule/price, invalidation, stop, target/exit, requested size basis, planned rationale, and profile references |
| `TC-IMP-STRAT-05` | Trade-plan lifecycle | `DRAFT -> READY_FOR_RISK -> APPROVED/REJECTED -> RELEASED -> MANAGED -> CLOSED/ABORTED`; released plans are immutable except through versioned amendments |
| `TC-IMP-STRAT-06` | Operating envelope | Define permitted volatility, spread, liquidity, regime, session, holding, and event conditions |
| `TC-IMP-STRAT-07` | Exit and management plan | Initial protection, target, partial exits, trailing rules, time stop, invalidation, and ownership handoff to approved automation |
| `TC-IMP-STRAT-08` | Expectancy reference | Link to an `ApprovedExpectancyProfile` without storing research evidence or deciding eligibility locally |
| `TC-IMP-STRAT-09` | Automation mode policy | `OFF`, `ADVISORY`, `SUPERVISED`, `AUTOMATED`; all actions remain subordinate to Risk and Trading interlocks |
| `TC-IMP-STRAT-10` | Manual-plan support | Allow a player-authored plan to use the same contract and validation path as automated strategies |
| `TC-IMP-STRAT-11` | Strategy lifecycle governance | Draft, test, approve, suspend, retire, and version strategies without changing historical replay meaning |

## 13.3 Candidate Feature Modules — Only If Absent

```text
strategy/
├── profiles/
├── playbooks/
├── setup_evaluation/
├── trade_plan/
├── operating_envelope/
├── management_plan/
├── automation/
└── lifecycle/
```

## 13.4 Boundary Rules

Strategy shall not:

- Calculate authoritative account risk or position size.
- Loosen account, venue, challenge, or emergency limits.
- Submit broker orders directly.
- Read future replay data.
- Treat a forecast or LLM opinion as a valid setup without deterministic strategy rules.

## 13.5 Required Tests

- Every trade plan contains entry, invalidation, stop, and exit logic before risk review.
- Released plans cannot be silently mutated.
- Setup evaluation regresses when data, regime, or signal validity is lost.
- Strategy operating-envelope mismatch prevents normal approval.
- Manual and automated plans follow the same contract.
- Suspended/retired versions cannot launch new plans but remain replayable historically.
- Expectancy references are version-exact and do not imply eligibility by themselves.

## 13.6 Exit Criteria

- A strategy or player can produce one complete `TradePlan` from point-in-time data.
- Risk receives all required fields without inferring missing trading intent.

---

# 14. Phase 6 — Risk

## 14.1 Goal

Make Risk the deterministic safety authority for policy resolution, trade readiness, sizing, drawdown, stress survival, emergency lockout, and expectancy eligibility.

## 14.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-RISK-01` | Trading policy profile | Versioned account, drawdown, trade, market, emergency, and assessment rules |
| `TC-IMP-RISK-02` | Effective-rule resolver | Combine scenario, account, venue/instrument, strategy, and simulator defaults using the strictest applicable rule |
| `TC-IMP-RISK-03` | Trade readiness gate | Reevaluate session, news, account lock, entry, stop, exit, strategy, broker health, data health, margin, risk, correlation, and stress at submit time |
| `TC-IMP-RISK-04` | Planned risk and net reward | Include stop distance, contract value, quantity, fees, spread, and estimated slippage |
| `TC-IMP-RISK-05` | Position sizing | Minimum of risk, margin, symbol, portfolio, liquidity, strategy, and stress-allowed size; quantity rounds down to venue step |
| `TC-IMP-RISK-06` | Stop-loss validator | Correct side, tick validity, technical invalidation, noise/venue distance, projected loss, and widening permissions |
| `TC-IMP-RISK-07` | Risk-to-reward / expectancy gate | Apply configured minimum RR unless a current, approved, exactly matched expectancy profile is eligible |
| `TC-IMP-RISK-08` | Drawdown engine | Static/trailing, realized/unrealized variants, daily and total reference, and `NORMAL/CAUTION/RESTRICTED/CRITICAL/LOCKED` states |
| `TC-IMP-RISK-09` | Exposure and correlation gates | Symbol, strategy, currency, directional, gross, and correlated-cluster limits using a Portfolio view |
| `TC-IMP-RISK-10` | Margin and leverage gates | Pre-trade projected margin, reserve, leverage, maintenance, and liquidation proximity |
| `TC-IMP-RISK-11` | Market restrictions | Session, news blackout, quote freshness, spread, liquidity, weekend, overnight, and venue-state rules |
| `TC-IMP-RISK-12` | Stress-loss and gap-risk model | Nominal, liquidity-adjusted, gap, event, margin-liquidation, and portfolio stress layers |
| `TC-IMP-RISK-13` | Emergency risk governor | Flash crash, data/connectivity failure, margin emergency, drawdown breach, unknown state, and recovery lock priorities |
| `TC-IMP-RISK-14` | Account lock and cooldown | Durable lockout, close-only/reduction-only permissions, cooldown, explicit re-arming, and review requirements |
| `TC-IMP-RISK-15` | Continuous monitoring | Recalculate risk after market events, fills, cancellations, position changes, valuation changes, and policy events |
| `TC-IMP-RISK-16` | Explainable risk decision | Structured allow/block/resize/restrict result, failed rules, inputs, effective limits, source versions, and corrective actions |
| `TC-IMP-RISK-17` | No-trade success state | Distinguish safe stand-down from failed gameplay when mandatory gates reject a setup |

## 14.3 Candidate Feature Modules — Only If Absent

```text
risk/
├── policy_profiles/
├── rule_resolution/
├── trade_readiness/
├── planned_risk/
├── position_sizing/
├── stop_validation/
├── reward_expectancy/
├── drawdown/
├── exposure_limits/
├── margin_limits/
├── market_restrictions/
├── stress_loss/
├── emergency_governor/
├── account_lock/
└── decisions/
```

## 14.4 Deferred Provider Integrations

Because `Portfolio` and `Research` are expanded later in the requested domain order:

- Risk consumes a narrow `PortfolioRiskView` port. Use the current Portfolio implementation where sufficient; otherwise use a deterministic test fake until Phase 12.
- Risk consumes an `ExpectancyEligibilityEvidencePort`. Until Phase 11, a missing provider must return `NOT_ELIGIBLE`, causing fallback to the normal RR gate.
- No temporary calculation in Risk may become a second account ledger, valuation engine, or research evidence store.

## 14.5 Database and Persistence

Potential owned records:

- Policy profiles and versions.
- Risk decisions and input snapshots.
- Account lockouts and cooldowns.
- Emergency directives.
- Approved overrides with actor, reason, and mode.

## 14.6 Required Tests

- Positive, negative, and exact-boundary tests for every limit.
- Property tests proving requested size never exceeds any active cap.
- Quantity rounds down, never up, when limiting risk.
- Submit-time reevaluation catches changed spread, price, margin, news, or drawdown.
- Unknown Portfolio or Research inputs fail closed.
- Drawdown state transitions and regressions are correct.
- Lockout survives restart and cannot be bypassed by mode change.
- Risk-reducing actions remain allowed while exposure-increasing actions are blocked.
- Stress risk blocks/resizes when projected loss breaches limits.
- Expired, suspended, mismatched, or missing expectancy profiles fall back to normal RR.
- Profitability never overrides a critical risk violation.

## 14.7 Integration Checkpoint `IC-2`

Demonstrate a complete pre-trade decision:

```text
Point-in-time market snapshot
  + indicator snapshot
  + strategy trade plan
  + instrument/venue profile
  + policy profile
  + portfolio risk view
  -> ALLOW / BLOCK / RESIZE / RESTRICT
```

The output must be fully explainable and replayable.

---

# 15. Phase 7 — Trading

## 15.1 Goal

Implement the authoritative internal order and execution lifecycle that converts an approved trade plan into controlled broker interaction while preserving unknown states and financial consequences.

## 15.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-TRD-01` | Order intent | Immutable economic intent linked to trade plan, risk decision, policy/profile versions, quantity, order type, time-in-force, protection, and idempotency key |
| `TC-IMP-TRD-02` | Write-before-send | Persist intent and idempotency state durably before any broker/simulator submission |
| `TC-IMP-TRD-03` | Order state machine | `CREATED -> STAGED -> SENT -> ACKNOWLEDGED -> PARTIALLY_FILLED -> FILLED` plus reject, cancel, expire, replace, unknown, and reconciled branches |
| `TC-IMP-TRD-04` | Order transition enforcement | Validate allowed edges, store source sequence, and record every transition once |
| `TC-IMP-TRD-05` | Cancel/replace lifecycle | Preserve executable cancel-pending state, model non-atomic replacement where applicable, and prevent duplicate exposure |
| `TC-IMP-TRD-06` | Partial fills and residuals | Update average price, filled/residual quantity, residual risk, and protection after every fill |
| `TC-IMP-TRD-07` | Execution position state | `FLAT`, `OPENING`, `OPEN`, `REDUCING`, `CLOSING`, `OVERNIGHT_APPROVED`, `EMERGENCY_CONTROLLED`, `LIQUIDATION_PENDING`, `UNKNOWN` |
| `TC-IMP-TRD-08` | Protective-order lifecycle | Attach/verify stop and target, coverage ratio, bracket/OCO behavior, residual resize, orphan prevention, and reverse-exposure prevention |
| `TC-IMP-TRD-09` | Master trading enable | New-exposure kill switch separated from cancel, protection, reduction, and closure permissions |
| `TC-IMP-TRD-10` | Reconciliation orchestrator | Compare internal intents/orders/fills/positions with broker snapshots and preserve `UNKNOWN` until resolved |
| `TC-IMP-TRD-11` | Economic execution events | Emit fill, fee estimate, correction, financing trigger, corporate-action trigger, and liquidation events for Portfolio posting |
| `TC-IMP-TRD-12` | Trade ownership | Record player, supervised automation, or automated owner; detect orphaned positions |
| `TC-IMP-TRD-13` | Session order controls | Cancel all entries, flatten, reduce-only, close-only, and explicit re-arm commands |
| `TC-IMP-TRD-14` | Execution audit | Store request, broker acknowledgement, fill, cancellation, error, and reconciliation evidence with causation links |

## 15.3 Candidate Feature Modules — Only If Absent

```text
trading/
├── order_intent/
├── order_state/
├── position_state/
├── protection/
├── cancel_replace/
├── reconciliation/
├── trade_ownership/
├── session_controls/
└── execution_events/
```

## 15.4 Database and Persistence

Trading owns durable records for:

- Order intents and idempotency keys.
- Internal order states and transitions.
- Fill records as received from the execution source.
- Execution-position state and ownership.
- Protective-order associations.
- Reconciliation incidents and outcomes.

Portfolio later consumes these economic events and owns the balanced ledger and accounting state.

## 15.5 Required Tests

- Every allowed and prohibited order-state transition.
- Duplicate submission with the same idempotency key produces one economic intent.
- Timeout after send becomes `UNKNOWN`; blind retry is blocked.
- Fill during cancel-pending is applied before final cancel state.
- Partial fill followed by disconnect preserves residual exposure.
- Stop rejection after entry creates critical unprotected exposure and approved recovery action.
- Protection always matches residual quantity unless an explicit exception is active.
- OCO cancellation cannot remove both exits while exposure remains.
- Unknown position prohibits new exposure.
- Application restart restores order intent and state without resubmission.
- Emergency lock preserves reduction/closure capabilities.

## 15.6 Exit Criteria

- Trading can execute against a fake or sandbox broker contract without simulator-specific branches.
- Every order outcome is explicit, persistent, idempotent, and reconcilable.

---

# 16. Phase 8 — Simulator

## 16.1 Goal

Create the authoritative Trading Cockpit game runtime: deterministic clock, market replay, scenarios, checklist state, assessment modes, simulated execution, emergency interruption, persistence, and recovery.

This is the first phase that produces a complete headless Trading Cockpit mission.

## 16.2 Subphase 8A — Session and Clock

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-SIM-01` | Simulation clock | Authoritative simulation time, source market time, venue time, replay speed, pause state, event sequence, branch, and integrity state |
| `TC-IMP-SIM-02` | Time-domain propagation | Preserve market-event, broker-receive, client-receive, display, player-action, venue-accept, fill, report, and processing times |
| `TC-IMP-SIM-03` | Global session state | `SESSION_SECURED` through pre-market, setup, launch, management, exit, review, and securing states |
| `TC-IMP-SIM-04` | Replay identity | Scenario/data/profile hashes, versions, seeds, rules version, and branch lineage |
| `TC-IMP-SIM-05` | Replay integrity | `VALID`, `TAINTED`, `INVALID`; scored sessions prohibit rewind and authoritative rollback |

## 16.3 Subphase 8B — Checklist and Assessment Modes

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-SIM-06` | Checklist definition | Load all pre-market, launch, management, exit, post-market, and emergency checklist steps from versioned data |
| `TC-IMP-SIM-07` | Checklist runtime | `LOCKED -> AVAILABLE -> ACTIVE -> SATISFIED` plus failed, blocked, bypassed, and regressed states |
| `TC-IMP-SIM-08` | Actual-state binding | A step is satisfied only by real domain state; UI checkboxes never mutate financial state |
| `TC-IMP-SIM-09` | Mode behavior | Guided, Standard, Expert, and Challenge assistance/override behavior without weakening non-bypassable interlocks |
| `TC-IMP-SIM-10` | No-trade mission completion | Safe stand-down can pass a mission when required gates reject launch |

## 16.4 Subphase 8C — Scenario Engine

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-SIM-11` | Scenario definition | Versioned mission, profiles, initial state, briefing, hidden conditions, injected events, triggers, pass/fail, scoring, and golden replay |
| `TC-IMP-SIM-12` | Trigger engine | Time, price, volatility, liquidity, player action, checklist state, account state, compound, and probabilistic seeded triggers |
| `TC-IMP-SIM-13` | Emergency scenarios | Flash crash, API/network failure, daily drawdown breach, margin survival, and recovery/integrity failure |
| `TC-IMP-SIM-14` | Abnormal operations | Bad tick, feed disagreement, halt/reopen, gap, margin change, repeated rejection, cancel/fill race, clock drift, corporate action, and process failure |
| `TC-IMP-SIM-15` | Event priority | Apply defined emergency priority and suspend incompatible normal transitions |

## 16.5 Subphase 8D — Execution Simulation

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-SIM-16` | Latency profile | Market-data, client, network, broker, venue, report, and processing delays using deterministic distributions |
| `TC-IMP-SIM-17` | Queue model | Price level, quantity ahead, queue position, traded volume, cancellations ahead, and fill probability |
| `TC-IMP-SIM-18` | Fill engine | Market, limit, stop, stop-limit, partial, IOC/FOK/day/GTC behavior according to instrument profile |
| `TC-IMP-SIM-19` | Slippage and market impact | Spread, depth, order size, volatility, latency, gaps, and emergency conditions |
| `TC-IMP-SIM-20` | Cancel/replace race simulation | Orders remain executable until authoritative cancel acknowledgement; replacement semantics follow venue profile |
| `TC-IMP-SIM-21` | Data/execution-view separation | Player view and venue execution state differ according to modeled latency without future leakage |
| `TC-IMP-SIM-22` | Simulator broker adapter | Expose simulated execution through the Phase 2 broker contract |

## 16.6 Subphase 8E — Persistence and Recovery

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-SIM-23` | Durable session state | Persist clock, scenario, replay, checklist, alerts, emergency state, counters, branches, and secure marker |
| `TC-IMP-SIM-24` | Recovery state machine | `STARTING -> RECOVERY_LOCKED -> RESTORING -> RECONCILING -> VERIFIED -> EXPLICIT_REARM -> RUNNING` |
| `TC-IMP-SIM-25` | Crash recovery | Restore authoritative orders, fills, positions, protection, Portfolio state references, lockouts, cooldowns, alerts, and score events |
| `TC-IMP-SIM-26` | Save/branch integrity | Practice branches are isolated; scored restart resumes authoritative consequences and prevents save-scumming |
| `TC-IMP-SIM-27` | Corruption handling | Hash mismatch, missing sequence, or inconsistent snapshot enters `INTEGRITY_FAILURE` and blocks new exposure |

## 16.7 Subphase 8F — Alerts and Human-Factor Backend

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-SIM-28` | Alert lifecycle | `INACTIVE`, `ACTIVE_UNACKNOWLEDGED`, `ACTIVE_ACKNOWLEDGED`, `RESOLVED`, `CLEARED` with latching rules |
| `TC-IMP-SIM-29` | Root-cause grouping | Group derivative symptoms under one actionable incident while preserving underlying evidence |
| `TC-IMP-SIM-30` | Perception timestamp | Record when an actionable condition became visible/audible so response-time scoring is fair |
| `TC-IMP-SIM-31` | Emergency control availability | Keep technically possible risk-reducing controls available during lock states |

## 16.8 Candidate Feature Modules — Only If Absent

```text
simulator/
├── session/
├── clock/
├── replay/
├── checklist/
├── modes/
├── scenarios/
├── triggers/
├── emergencies/
├── latency/
├── queue/
├── fills/
├── slippage/
├── recovery/
└── alerts/
```

## 16.9 Database and Persistence

Potential owned records:

- Simulation sessions and durable state.
- Replay identities and branch lineage.
- Scenario definitions and versions.
- Checklist definitions and transitions.
- Injected events and trigger outcomes.
- Alerts and acknowledgement/resolution lifecycle.
- Recovery checkpoints and secured markers.
- Deterministic random-stream state where required.

## 16.10 Required Tests

- Same replay identity and player events produce identical outputs.
- No future data is visible to UI, Strategy, Risk, alerts, automation, or logs.
- Scored rewind/rollback invalidates official score.
- All checklist transitions and continuous regressions behave correctly.
- Mode changes alter assistance but not hard safety/integrity locks.
- Every scenario has deterministic triggers and a golden run.
- Limit orders never receive impossible fills; stops do not guarantee trigger price.
- Queue, partial-fill, latency, and cancel races are reproducible.
- Compound emergencies honor priority.
- Crash recovery cannot erase losses, fills, warnings, cooldowns, or score events.
- Corrupted state enters recovery lock.
- Risk-reducing controls remain available when allowed.

## 16.11 Integration Checkpoint `IC-3`

Run a headless mission from `SESSION_SECURED` back to `SESSION_SECURED` with:

- Pre-market checklist.
- One valid trade and one blocked trade.
- Partial fill and protective-order handling.
- One injected emergency.
- Reconciliation and restart recovery.
- Deterministic replay output.

---

# 17. Phase 9 — Analytics

## 17.1 Goal

Turn authoritative events into process-first scoring, journal evidence, debriefs, execution analytics, behavioral insights, and player qualification without mutating trading state.

## 17.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-ANL-01` | Trading event analytics stream | Consume immutable market, checklist, risk, order, fill, portfolio, alert, and player-action events |
| `TC-IMP-ANL-02` | Process-first scoring | Preparation, risk, execution, plan adherence, portfolio management, emergency response, discipline, and post-market review |
| `TC-IMP-ANL-03` | Critical-failure override | A critical safety, integrity, or replay failure caps or invalidates scores regardless of P&L |
| `TC-IMP-ANL-04` | Trade journal | Store plan, context, screenshots/references, entries/exits, management actions, notes, and result |
| `TC-IMP-ANL-05` | Execution quality | Expected versus actual price, spread, slippage, latency, queue outcome, partial fills, and missed/canceled opportunity |
| `TC-IMP-ANL-06` | Plan-adherence analytics | Compare every action with the released TradePlan and management rules |
| `TC-IMP-ANL-07` | Behavioral analytics | Overtrading, order churn, revenge patterns, impulsive size increases, stop widening, and unapproved averaging |
| `TC-IMP-ANL-08` | Emergency response analytics | Detection/perception/action/recovery time, correct sequence, unnecessary exposure, and survival outcome |
| `TC-IMP-ANL-09` | Debrief generator | Answer-first session report with decisions, causes, warnings, counterfactual process lessons, and replay links |
| `TC-IMP-ANL-10` | Player qualification | Curriculum prerequisites, ratings, checkrides, remediation, recurrent validity, and disqualifying breaches |
| `TC-IMP-ANL-11` | Comparative scoring | Leaderboard eligibility and process/safety/risk-adjusted ranking; profit remains secondary |
| `TC-IMP-ANL-12` | Score reproducibility | Rebuild score from stored events and scoring-profile version |
| `TC-IMP-ANL-13` | No-trade scoring | Award competence for correct stand-down and controlled loss behavior |

## 17.3 Candidate Feature Modules — Only If Absent

```text
analytics/
├── event_consumers/
├── scoring/
├── journal/
├── execution_quality/
├── plan_adherence/
├── behavior/
├── emergency_response/
├── debrief/
├── qualification/
└── comparative_scoring/
```

## 17.4 Database and Persistence

Potential owned records:

- Journal entries and evidence references.
- Score events and finalized scorecards.
- Debriefs.
- Player qualifications, attempts, remediation, and expiry.
- Analytics aggregates derived from immutable source events.

Source financial events shall not be rewritten by Analytics.

## 17.5 Required Tests

- Score rebuild from the same events is identical.
- Profit cannot compensate for a critical violation.
- Controlled loss and correct stand-down can score highly.
- Response time starts at the perception timestamp, not hidden event time.
- Journal and debrief link to exact source events and replay position.
- Behavioral rules do not infer violations without supporting events.
- Qualification prerequisites and expiry are deterministic.
- Leaderboard eligibility rejects tainted/invalid replays.

## 17.6 Integration Checkpoint `IC-4A`

The headless mission from Phase 8 must produce a reproducible journal, scorecard, debrief, and qualification update.

---

# 18. Phase 10 — Optimization

## 18.1 Goal

Use HaruQuantAI's Optimization domain to calibrate and evaluate simulator, strategy, and risk parameters without introducing lookahead, unsafe policy relaxation, or score-gaming.

## 18.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-OPT-01` | Optimization study contract | Versioned objective, search space, constraints, dataset/replay identity, seed, sampler, budget, and output artifact |
| `TC-IMP-OPT-02` | Fill-model calibration | Estimate latency, slippage, partial-fill, queue, and market-impact parameters from approved historical/sandbox evidence |
| `TC-IMP-OPT-03` | Scenario difficulty calibration | Tune event intensity, information load, time pressure, liquidity loss, and compound failures to target competence levels |
| `TC-IMP-OPT-04` | Strategy parameter studies | Optimize only within approved strategy and instrument envelopes, with walk-forward/out-of-sample validation |
| `TC-IMP-OPT-05` | Risk sensitivity analysis | Measure outcome sensitivity to risk per trade, drawdown warnings, stress limits, and exposure caps without automatically weakening hard limits |
| `TC-IMP-OPT-06` | Stress-profile calibration | Calibrate shock magnitudes and dependencies while preserving transparent assumptions |
| `TC-IMP-OPT-07` | Multi-objective evaluation | Safety, process adherence, stability, execution realism, and risk-adjusted performance; raw profit is never the sole objective |
| `TC-IMP-OPT-08` | Anti-leakage controls | Strict training/validation/test splits, point-in-time data, scenario holdouts, and no future revisions |
| `TC-IMP-OPT-09` | Robustness and overfit checks | Parameter stability, perturbation tests, regime splits, multiple seeds, and uncertainty intervals |
| `TC-IMP-OPT-10` | Promotion contract | Optimization outputs become versioned candidate profiles; they require Research/Strategy/Risk approval before use |

## 18.3 Candidate Feature Modules — Only If Absent

```text
optimization/
├── studies/
├── fill_calibration/
├── scenario_calibration/
├── strategy_search/
├── risk_sensitivity/
├── stress_calibration/
├── objectives/
├── leakage_controls/
└── promotion/
```

## 18.4 Required Tests

- Fixed study identity and seed reproduce results.
- Holdout datasets are inaccessible during training.
- Unsafe parameter combinations are rejected by constraints.
- Optimization cannot change non-bypassable account or integrity locks.
- Promoted artifacts include data hash, code version, assumptions, and validation evidence.
- Multiple seeds/regimes reveal unstable solutions.
- Score optimization cannot reward critical violations.

## 18.5 Exit Criteria

- The simulator and strategy can consume approved calibration profiles by exact version.
- No optimizer output becomes authoritative without the later approval workflow.

---

# 19. Phase 11 — Research

## 19.1 Goal

Provide the evidence and governance layer for approved expectancy profiles, stress assumptions, market baselines, scenario realism, and strategy operating envelopes.

## 19.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-RES-01` | Research evidence contract | Source, publication/availability time, provenance, license/use, trust, scope, revision, dataset hash, and bounded findings |
| `TC-IMP-RES-02` | Strategy evidence package | Hypothesis, instruments, regimes, sessions, methodology, sample, costs, results, limitations, and versioned strategy linkage |
| `TC-IMP-RES-03` | Approved expectancy profile | Sample dates/size, out-of-sample status, expected win rate, average win/loss in R, expected value, drawdown, operating envelope, approval, review, and expiry |
| `TC-IMP-RES-04` | Expectancy governance | `DRAFT`, `UNDER_REVIEW`, `APPROVED`, `SUSPENDED`, `EXPIRED`, `REVOKED`; exact strategy/instrument/regime/session matching |
| `TC-IMP-RES-05` | Performance drift evidence | Monitor live-simulation/paper outcomes against approved envelope and propose suspension when drift thresholds are reached |
| `TC-IMP-RES-06` | Stress-scenario evidence | Historical or reasoned basis for price, spread, liquidity, correlation, FX, margin, halt, gap, and connectivity shocks |
| `TC-IMP-RES-07` | Scenario evidence package | Learning objective, event realism, information fairness, trigger justification, expected recovery, and golden-run notes |
| `TC-IMP-RES-08` | Market/instrument research | Evidence supporting session, liquidity, cost, margin, lifecycle, and event assumptions without replacing Brokers profiles |
| `TC-IMP-RES-09` | Point-in-time evidence projection | Consume eligible Data-owned records and expose only evidence available at the simulation timestamp |
| `TC-IMP-RES-10` | Research-to-profile promotion | Produce versioned candidate profiles for Strategy, Risk, Simulator, or Optimization with review evidence |
| `TC-IMP-RES-11` | Evidence audit trail | Record reviewer, decision, reason, superseded version, and affected scenarios/strategies |

## 19.3 Candidate Feature Modules — Only If Absent

```text
research/
├── evidence/
├── strategy_evidence/
├── expectancy_profiles/
├── governance/
├── drift/
├── stress_evidence/
├── scenario_evidence/
├── market_baselines/
└── promotion/
```

## 19.4 Boundary Rules

- Data owns eligible point-in-time records; Research selects and measures bounded evidence.
- Research does not submit orders, approve individual trades, or calculate account state.
- LLM-generated prose cannot become quantitative evidence without source-backed deterministic measurements.
- Missing, expired, or mismatched evidence results in `NOT_ELIGIBLE`, not an inferred approval.

## 19.5 Required Tests

- Exact version/profile matching.
- Expiry, suspension, and revocation immediately disable eligibility.
- Historical replay sees only evidence available at the simulated time.
- Every quantitative claim traces to a source record or deterministic calculation.
- Profile promotion requires complete review fields.
- Drift thresholds produce a suspension recommendation/event without silently changing history.
- Scenario evidence and golden-run identity remain reproducible.

## 19.6 Integration Checkpoint `IC-4B`

Demonstrate that Risk accepts a lower RR exception only through a current, exactly matched, evidence-backed profile; all mismatches fall back to the default gate.

---

# 20. Phase 12 — Portfolio

## 20.1 Goal

Make Portfolio the authoritative financial-state domain for ledger, accounting, valuation, multi-currency conversion, margin, exposure, drawdown, capital allocation, reconciliation, and portfolio stress.

This phase replaces any provisional Portfolio fakes used by Risk, Trading, Simulator, and Analytics.

## 20.2 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-PORT-01` | Immutable balanced ledger | Debit/credit postings for deposits, withdrawals, fills, commissions, fees, spread, financing, funding, borrow, dividends, FX translation, mark-to-market, settlement, corporate action, liquidation, and correction |
| `TC-IMP-PORT-02` | Ledger event ingestion | Consume Trading/Broker/Simulator economic events exactly once using event and source-sequence invariants |
| `TC-IMP-PORT-03` | Account balance and cash | Settled/unsettled cash where applicable, accrued income/costs, and reproducible balance |
| `TC-IMP-PORT-04` | Valuation policy | Bid/ask/mid/mark/last/settlement rules by instrument and position side, plus stale/unknown valuation states |
| `TC-IMP-PORT-05` | Realized/unrealized P&L | Lot matching or venue-defined netting/hedging rules, fees/costs, and exact event linkage |
| `TC-IMP-PORT-06` | Multi-currency accounting | Timestamped FX conversion, freshness limits, translation postings, and unknown state on missing/stale rates |
| `TC-IMP-PORT-07` | Margin and buying power | Used, available, reserved order margin, maintenance, reserve, leverage, and liquidation proximity using selected profile |
| `TC-IMP-PORT-08` | Position and exposure state | Instrument, strategy sleeve, currency, direction, gross/net, beta/delta where applicable, and ownership references |
| `TC-IMP-PORT-09` | Correlation and concentration | Cluster exposure, correlated risk, concentration drift, and portfolio attitude inputs |
| `TC-IMP-PORT-10` | Drawdown and references | Daily/total reference equity, high-water marks, realized/unrealized inclusion, and policy-compatible state views |
| `TC-IMP-PORT-11` | VaR/CVaR and risk-health views | Versioned portfolio risk metrics for cockpit display; clearly labeled model assumptions |
| `TC-IMP-PORT-12` | Portfolio stress aggregation | Apply Risk/Research shock profiles to positions, liquidity, conversion, margin, and correlation; expose projected stress loss |
| `TC-IMP-PORT-13` | Capital allocation / fuel selector | Strategy sleeves, account allocations, reserved risk budgets, and prohibited allocation routes |
| `TC-IMP-PORT-14` | Broker/internal reconciliation | Compare broker-reported and rebuilt state; enter unknown/recovery state on differences beyond tolerance |
| `TC-IMP-PORT-15` | Snapshots and event rebuild | Rebuild current state from ledger/events; snapshots are accelerators, not alternative truth |
| `TC-IMP-PORT-16` | Corporate action and settlement handling | Apply profile-driven lifecycle events without corrupting historical positions or P&L |
| `TC-IMP-PORT-17` | PortfolioState contract | Publish the complete specification-defined read model to Risk, Simulator, Analytics, and UI-API |

## 20.3 Candidate Feature Modules — Only If Absent

```text
portfolio/
├── ledger/
├── accounting/
├── valuation/
├── pnl/
├── currencies/
├── margin/
├── positions/
├── exposure/
├── correlation/
├── drawdown/
├── var_cvar/
├── stress/
├── allocations/
├── reconciliation/
├── snapshots/
└── corporate_actions/
```

## 20.4 Database and Persistence

Portfolio persistence is authoritative and requires careful migration design. Likely owned entities include:

- Ledger entries and reversal relationships.
- Accounts and currencies.
- Position lots or net position records.
- Valuation snapshots and policies.
- FX conversion records/references.
- Margin and exposure snapshots.
- Drawdown reference state.
- Allocation/sleeve records.
- Reconciliation incidents.

Financial records must be append-only or corrected through explicit reversal/correction events. Direct historical mutation is prohibited.

## 20.5 Required Tests

- Every ledger event balances.
- Rebuild from events equals stored state within declared tolerance.
- Duplicate economic event is posted once.
- Fill/cancel race produces correct position and cash.
- Fees, funding, financing, borrow, dividends, and corporate actions reconcile.
- Long and short valuation use the declared policy.
- Missing/stale FX rate creates unknown/restricted state.
- Margin and buying power reproduce the selected instrument/account model.
- Correlation and stress aggregation update atomically after simultaneous fills.
- Snapshot restore plus remaining events equals full replay.
- Broker/internal mismatch locks new exposure.
- Decimal/tick/quantity/currency rounding follows Utils and profile rules.

## 20.6 Integration Checkpoint `IC-5`

Replace provisional Portfolio ports in Risk, Trading, Simulator, and Analytics. Re-run all earlier tests and demonstrate:

```text
Execution events
  -> balanced ledger
  -> account/position/valuation/margin/exposure state
  -> risk reevaluation
  -> cockpit-ready PortfolioState
```

---

# 21. Phase 13 — Agentic

## 21.1 Goal

Add intelligent coaching, explanation, research assistance, and debrief interaction while preserving deterministic authority and strict tool permissions.

## 21.2 Proposed Agent Roles

| Agent | Permitted responsibility | Prohibited responsibility |
| --- | --- | --- |
| Trading Cockpit CEO / Instructor | Explain session state, coordinate training, summarize specialist outputs, guide checklist understanding | Directly submit orders, change risk policy, fabricate state, or override lockouts |
| Pre-Market Coach | Help review calendar, regime, playbook, and checklist gaps using current system data | Mark a checklist step satisfied without actual state |
| Risk Officer Explainer | Explain failed risk rules, limits, sizing, stress, and corrective options | Recalculate or alter authoritative Risk decisions |
| Scenario Instructor | Deliver briefing, prompts, and post-event coaching according to scenario visibility | Reveal hidden/future scenario information |
| Research Analyst | Summarize approved evidence and profile limitations | Treat unsupported web/LLM claims as approved evidence |
| Debrief Analyst | Explain journal, score, decisions, warnings, and replay evidence | Change official score or source events |
| Portfolio Officer | Explain equity, margin, exposure, correlation, and ledger state | Post or edit ledger entries |

## 21.3 Planned Work Packages

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-AGT-01` | Agent constitution and permissions | Explicit read/write scopes, environment restrictions, domain-tool allowlists, and prohibited actions |
| `TC-IMP-AGT-02` | Read-only cockpit tools | Retrieve current session, checklist, market, strategy, risk, trading, portfolio, scenario, score, and evidence state |
| `TC-IMP-AGT-03` | Controlled action proposal | Agents may propose a deterministic API action; the user and normal policy/trading gates authorize it |
| `TC-IMP-AGT-04` | Guided-mode coaching | Explain next step, reason for block, corrective action, and relevant panel without completing the step |
| `TC-IMP-AGT-05` | Emergency coaching | Present the authoritative emergency checklist and current state without inventing broker or market certainty |
| `TC-IMP-AGT-06` | Debrief conversation | Query exact events, compare plan versus action, explain score, and support journal reflection |
| `TC-IMP-AGT-07` | Research-grounded explanation | Cite approved internal evidence/profile versions and clearly distinguish assumptions |
| `TC-IMP-AGT-08` | Scenario narration | Deliver only information whose scenario availability time has arrived |
| `TC-IMP-AGT-09` | Tool and response audit | Persist tool request, permission decision, source records, proposed action, user decision, and result |
| `TC-IMP-AGT-10` | Failure behavior | On tool/data failure, say state is unavailable; never infer an order, position, risk, or account result |
| `TC-IMP-AGT-11` | Prompt-injection resistance | Treat market/news/journal content as untrusted data and prevent it from changing permissions or hidden rules |

## 21.4 Candidate Feature Modules — Only If Absent

```text
agentic/
├── permissions/
├── cockpit_ceo/
├── pre_market_coach/
├── risk_explainer/
├── scenario_instructor/
├── research_analyst/
├── debrief_analyst/
├── portfolio_explainer/
├── tools/
└── audit/
```

## 21.5 Required Tests

- Agents cannot call production live-trading tools.
- Agents cannot bypass Risk, Trading, account lock, replay integrity, or checklist state.
- Hidden/future scenario data is never exposed.
- Tool failures produce explicit uncertainty.
- Prompt injection in news, market data, strategy notes, or journal content cannot change permissions.
- Proposed actions still fail when deterministic gates reject them.
- Official score and financial state are read-only to agents.
- Responses cite the correct internal profile/evidence/event where required.
- Every tool call and proposed action is auditable.

## 21.6 Exit Criteria

- Agentic assistance improves understanding but is never required for deterministic operation.
- Disabling all agents leaves the complete simulator functional and safe.

---

# 22. Phase 14 — UI-API

## 22.1 Goal

Deliver the complete web-based Trading Cockpit and stable API layer over the authoritative domain contracts. The UI visualizes and controls real state; it never owns trading truth.

## 22.2 Subphase 14A — API Foundation

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-UIAPI-01` | Session API | Create/resume/end simulation sessions; expose mode, scenario, replay identity, clock, and integrity state |
| `TC-IMP-UIAPI-02` | Cockpit read model | Aggregate panel-ready state without duplicating domain calculations |
| `TC-IMP-UIAPI-03` | Command API | Pre-market interactions, plan creation, risk review, order actions, emergency controls, checklist acknowledgement, journaling, and explicit re-arm |
| `TC-IMP-UIAPI-04` | Real-time event stream | WebSocket/SSE or current project equivalent for market, order, portfolio, risk, checklist, alert, and score events |
| `TC-IMP-UIAPI-05` | Optimistic-concurrency control | Commands include expected state/version; stale UI actions fail safely |
| `TC-IMP-UIAPI-06` | Authentication and authorization | Player, instructor, reviewer, admin, and agent permissions; simulation environment enforcement |
| `TC-IMP-UIAPI-07` | API idempotency and error model | Stable reason codes, corrective actions, retryability, correlation IDs, and no ambiguous success |

## 22.3 Subphase 14B — Cockpit Shell and Panels

Implement the required panel architecture:

```text
TradingCockpit
├── Market Flight Instruments
├── Portfolio Flight Instruments
├── Trade Control Panels
├── Navigation and Planning Panels
└── Warning and Emergency Panels
```

| ID | Panel group | Required components |
| --- | --- | --- |
| `TC-IMP-UIAPI-08` | Market instruments | Market speed, regime, trend, spread/liquidity, order-book depth, support/resistance, news/event radar, data integrity |
| `TC-IMP-UIAPI-09` | Portfolio instruments | Equity/balance altimeter, P&L velocity, margin fuel, leverage, drawdown heat, risk health, exposure attitude, correlation turn, VaR/CVaR, stress state |
| `TC-IMP-UIAPI-10` | Trade controls | Order ticket, exposure throttle, risk mixture, stop/target, execution flaps, partial trim, cancel, flatten, master enable, automation mode |
| `TC-IMP-UIAPI-11` | Navigation/planning | Charts, market radar, session planner, economic calendar, playbook, trade plan, course deviation, journal |
| `TC-IMP-UIAPI-12` | Warning/emergency | Annunciator, connectivity power, redundancy, margin stall, emergency checklist, lockout, recovery, and explicit re-arm |

## 22.4 Subphase 14C — Workflow Interfaces

| ID | Workflow | Required UI behavior |
| --- | --- | --- |
| `TC-IMP-UIAPI-13` | Pre-market | Sequential checklist tied to actual state, calendar review, policy baseline, levels, regime, watchlist, exposure, objective, and cockpit arm |
| `TC-IMP-UIAPI-14` | Trade planning | Setup evidence, entry/invalidation/stop/exit, costs, RR/expectancy, size request, and trade-plan confirmation |
| `TC-IMP-UIAPI-15` | Risk decision | Display allow/block/resize/restrict result, effective rule sources, failed checks, and safe corrective actions |
| `TC-IMP-UIAPI-16` | Order execution | Confirmation, acknowledgement, partial fills, slippage, unknown states, protection, and cancel/replace status |
| `TC-IMP-UIAPI-17` | Position management | Risk trim, partial exit, market/regime/news/liquidity monitoring, plan deviation, ownership, and exit triggers |
| `TC-IMP-UIAPI-18` | Post-market | Reconciliation state, journal, screenshots/evidence, execution review, score, lessons, dashboard reset, and secure session |

## 22.5 Subphase 14D — Emergency and Recovery UX

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-UIAPI-19` | Flash-crash checklist | Stop new orders, assess liquidity/risk/margin/correlation, verify protection, reduce/flatten per policy, preserve event log |
| `TC-IMP-UIAPI-20` | API/network failure checklist | Show stale/unknown state, disable new orders, offer backup/status channels, reconcile, and require explicit re-arm |
| `TC-IMP-UIAPI-21` | Drawdown-breach checklist | Critical warning, cancel entries, reduce/flatten, lockout, cooldown, incident review, and end session |
| `TC-IMP-UIAPI-22` | Recovery screen | Present restore/reconcile/invariant status; never imply recovery before authoritative verification |
| `TC-IMP-UIAPI-23` | Emergency control ergonomics | Guard against accidental flatten while keeping it rapidly reachable; preserve cancel/reduce/close controls during locks |

## 22.6 Subphase 14E — Human Factors and Accessibility

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-UIAPI-24` | Alert priority and lifecycle | Severity, source, root cause, affected entity, acknowledgement, unresolved condition, and clearance |
| `TC-IMP-UIAPI-25` | Alarm-flood control | Group related symptoms and prioritize the highest actionable root cause |
| `TC-IMP-UIAPI-26` | Multimodal warnings | Never rely only on color or sound; use text, icon/shape, placement, and accessible labels |
| `TC-IMP-UIAPI-27` | Data freshness visibility | Show source timestamp, quote age, stale state, and unknown valuation/order status clearly |
| `TC-IMP-UIAPI-28` | Responsive cockpit layout | Preserve critical controls and warnings across supported viewport sizes without hiding emergency functions |
| `TC-IMP-UIAPI-29` | Interaction safety | Confirmation only where it does not obstruct emergency risk reduction; prevent stale or double submissions |

## 22.7 Subphase 14F — Training, Replay, and Progression

| ID | Capability | Responsibility |
| --- | --- | --- |
| `TC-IMP-UIAPI-30` | Trading Flight School | Cockpit familiarization, pre-market, risk/sizing, execution, management, portfolio, emergencies, degraded-data, and final checkride modules |
| `TC-IMP-UIAPI-31` | Guided/Standard/Expert/Challenge UX | Assistance and feedback change by mode while authoritative rules remain unchanged |
| `TC-IMP-UIAPI-32` | Scenario browser | Briefing, objectives, difficulty, prerequisites, allowed aids, profile versions, and score eligibility |
| `TC-IMP-UIAPI-33` | Replay workstation | Timeline, events, orders, fills, market/portfolio snapshots, alerts, decisions, branches, and integrity status |
| `TC-IMP-UIAPI-34` | Debrief and journal | Process score, violations, strengths, lessons, remediation, evidence, and Agentic discussion |
| `TC-IMP-UIAPI-35` | Qualification and progression | Ratings, prerequisites, checkrides, remediation, recurrent status, and leaderboard eligibility |

## 22.8 Candidate Feature Modules — Only If Absent

Respect the current HaruQuantAI physical UI/API layout. Logical feature areas are:

```text
UI-API
├── session_api
├── cockpit_read_models
├── command_api
├── realtime_events
├── cockpit_shell
├── market_panels
├── portfolio_panels
├── trade_controls
├── planning_panels
├── alerts_and_emergencies
├── checklists
├── training
├── scenarios
├── replay
├── debrief
└── qualifications
```

## 22.9 Required Tests

- API schema/contract tests for every domain read model and command.
- UI never marks checklist completion by local checkbox state alone.
- Stale expected-version commands are rejected.
- Double click/retry cannot duplicate an order intent.
- All panel values match authoritative backend state.
- Unknown/stale states are visible and not rendered as zero or normal.
- Alert acknowledgement does not clear an unresolved hazard.
- Emergency controls remain accessible and keyboard/screen-reader operable.
- Mode behavior matches specification.
- End-to-end browser tests cover normal, no-trade, flash crash, outage, drawdown, restart recovery, and post-market workflows.
- Replay cannot mutate official session state.
- Agentic output is visually distinguished from authoritative system state.

## 22.10 Integration Checkpoint `IC-6`

A player can complete the full Trading Cockpit workflow from the web application, including a safe no-trade session, a normal trade, an emergency, recovery, debrief, and qualification update.

---

# 23. Phase 15 — Cross-Domain Integration, Verification, and Release

## 23.1 Goal

Prove that the assembled HaruQuantAI domains satisfy the complete Trading Cockpit specification as one deterministic, recoverable, auditable system.

## 23.2 Work Packages

| ID | Work package | Required result |
| --- | --- | --- |
| `TC-IMP-SYS-01` | Contract closure | Remove provisional fakes, reconcile schemas, freeze public contracts for the release candidate, and verify owner-domain authority |
| `TC-IMP-SYS-02` | Full traceability | Map every normative requirement and all 40 acceptance criteria to code, tests, usage, UI, and evidence |
| `TC-IMP-SYS-03` | Compound-failure suite | Execute all required concurrency, disconnect, fill, margin, drawdown, halt, crash, and integrity combinations |
| `TC-IMP-SYS-04` | Golden scenario pack | Publish deterministic normal, no-trade, news spike, flash crash, API outage, drawdown breach, recovery, and compound-failure missions |
| `TC-IMP-SYS-05` | Financial reconciliation | Rebuild every release mission from events and prove orders, fills, positions, protection, ledger, equity, margin, drawdown, and score |
| `TC-IMP-SYS-06` | Replay integrity | Verify hashes, seeds, sequence, no-lookahead, branch isolation, restart, and identical-output guarantees |
| `TC-IMP-SYS-07` | Performance and capacity | Validate event throughput, UI update cadence, scenario determinism under load, persistence latency, and recovery time without dropping critical events |
| `TC-IMP-SYS-08` | Security and permissions | Environment isolation, API authorization, agent tool permissions, prompt-injection resistance, secret handling, and audit integrity |
| `TC-IMP-SYS-09` | Human-factors acceptance | Alarm priority, root-cause grouping, accessibility, emergency-control reachability, and fair response-time measurement |
| `TC-IMP-SYS-10` | Migration and compatibility | Verify existing HaruQuantAI workflows still pass or have documented, tested migrations |
| `TC-IMP-SYS-11` | Operations package | Configuration examples, profile authoring guides, scenario authoring guide, recovery runbook, data integrity runbook, and incident/debrief workflow |
| `TC-IMP-SYS-12` | Release evidence | Store exact commit, lockfile, migration head, configuration/profile versions, dataset hashes, scenario seeds, tests, and known limitations |

## 23.3 Required Compound-Failure Scenarios

At minimum:

1. Partial fill followed immediately by network loss.
2. Drawdown breach while an exit order is unacknowledged.
3. Flash crash while broker connectivity is degraded.
4. Cancel request followed by final fill.
5. Protective-stop rejection after a partial entry fill.
6. Margin breach and exchange halt at the same time.
7. Application restart with an unknown order.
8. Corporate action or contract lifecycle event with an overnight position.
9. Stale FX conversion in a multi-currency account.
10. Automation remains active when the player activates the master kill switch.
11. Simultaneous fills in a correlated cluster cause a portfolio-risk breach.
12. Dataset hash mismatch during a scored mission.
13. Alert acknowledgement while the underlying hazard remains active.
14. Recovery snapshot is valid but a later source sequence is missing.
15. Agent proposes an action that deterministic Risk rejects.

## 23.4 Release Candidate Scenarios

| Scenario | Purpose |
| --- | --- |
| `RC-01 Normal Mission` | Full pre-market, valid plan, controlled fill, managed exit, reconciliation, and debrief |
| `RC-02 Safe Stand-Down` | Mandatory gates reject all setups; player succeeds by not trading |
| `RC-03 News and Liquidity` | Event blackout, spread expansion, partial fill, and strategy-envelope regression |
| `RC-04 Flash Crash` | Volatility, liquidity collapse, correlation convergence, margin pressure, and emergency reduction |
| `RC-05 API Outage` | Unknown order state, stale data, backup status, reconciliation, and explicit re-arm |
| `RC-06 Drawdown Breach` | Lockout, pending-order cancellation, reduction/flatten, cooldown, and session termination |
| `RC-07 Crash Recovery` | Application restart preserves fills, loss, alerts, lockouts, score, and scenario clock |
| `RC-08 Compound Failure` | At least three simultaneous failures with correct priority and no state corruption |

## 23.5 Final Release Gate

The Trading Cockpit release candidate is acceptable only when:

- All specification acceptance criteria `1-40` are evidenced.
- All fourteen domain audits are complete.
- All public contracts are versioned and documented.
- No production live-money route is reachable.
- All golden runs are deterministic.
- Financial state rebuilds from immutable events.
- Unknown and stale states fail closed.
- Required compound-failure tests pass.
- Full web workflows and accessibility tests pass.
- Agentic behavior remains advisory and permission-bounded.
- The session can be securely closed and later replayed without mutating official history.

---

# 24. Cross-Phase Test Strategy

## 24.1 Test Levels

| Level | Focus |
| --- | --- |
| Unit | Calculation, validation, state transition, serialization, and error behavior within one feature |
| Property / Boundary | Invariants over ranges, exact thresholds, rounding, sequencing, and sizing limits |
| Contract | Provider-consumer schemas and every broker/data/API adapter |
| Integration | Two or more domains using real contracts and persistence |
| Workflow | Complete pre-market, trade, emergency, post-market, and recovery paths |
| Determinism | Same identity/seed/events produce identical outputs |
| Persistence | Restart, snapshot restore, event replay, idempotency, and lock survival |
| Concurrency | Fill/cancel/reconnect/simultaneous-event races |
| Financial Integrity | Ledger balance, position quantity, protection, equity, margin, drawdown, and event sequence |
| Security | Environment isolation, authorization, secrets, agent tools, and prompt injection |
| UI End-to-End | Cockpit controls, real-time state, alerts, accessibility, and mode behavior |
| Golden Run | Versioned official scenarios with exact expected ordered outcomes |

## 24.2 Mandatory Test Classes Per Requirement

For each applicable normative requirement, record evidence for:

- Positive case.
- Negative case.
- Exact lower/upper boundary.
- Regression after a previously valid condition becomes invalid.
- Recovery after failure.
- Concurrency/race behavior.
- Persistence/restart behavior.
- Determinism.
- Integrity invariant.

## 24.3 Coverage Rule

Maintain or exceed the project's required coverage threshold. Coverage alone does not satisfy acceptance: state-transition, concurrency, no-lookahead, and financial-invariant evidence must be explicitly demonstrated.

---

# 25. Database and Migration Strategy

## 25.1 Ownership Rules

- One domain owns each authoritative record.
- Other domains store references, projections, or cached read models, not competing truth.
- Immutable events are corrected by reversal/correction events rather than historical mutation.
- Every migration declares owner domain, backward-compatibility impact, data backfill, rollback/forward-fix strategy, and acceptance query.
- Schema versions are attached to replay and release evidence where they affect determinism.

## 25.2 Likely Persistence Sequence

| Phase | Persistence focus |
| --- | --- |
| Utils | Event/outbox/idempotency infrastructure if not already present |
| Brokers | Instrument profiles, capabilities, source cursors, environment permissions |
| Data | Dataset manifests, point-in-time records, calendars, data-quality incidents |
| Strategy | Strategy/playbook/profile versions and trade plans |
| Risk | Policy profiles, risk decisions, lockouts, emergency directives |
| Trading | Order intents, order transitions, fills, protection, reconciliation incidents |
| Simulator | Sessions, replay identities, scenarios, checklist transitions, alerts, branches, recovery state |
| Analytics | Journals, scores, debriefs, qualifications |
| Optimization | Study definitions, trials/results, calibration profiles |
| Research | Evidence packages, approvals, expectancy/stress/scenario profiles |
| Portfolio | Ledger, accounts, valuation, FX, positions, margin, exposure, snapshots, reconciliation |
| Agentic | Tool/action audit and bounded conversation/session references |
| UI-API | User display preferences and UI workflow state only where necessary; never duplicate financial truth |

---

# 26. Documentation and Handoff Requirements

Each domain phase shall update or create:

1. Domain README feature/FR/workflow/export/status tables.
2. Requirements mapping for Trading Cockpit work packages.
3. Blueprint or design note for state machines and persistence where applicable.
4. Public contract documentation with examples.
5. Database migration notes and acceptance queries.
6. Unit/integration/workflow test instructions.
7. Runnable usage example using simulation or sandbox only.
8. Known limitations and deferred integrations.
9. Handoff prompt for the next implementation/review agent, where the project workflow uses one.
10. Acceptance evidence record with exact commands and results.

---

# 27. Master Implementation Tracker

Use one row per work package.

| Phase | Domain | Work Package | Current Classification | Owner | Dependencies | Code Status | DB Status | Tests | Usage | UI/API Contract | Traceability | Acceptance Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Recommended status values:

```text
NOT_AUDITED
REUSE_CONFIRMED
EXTENSION_PLANNED
IMPLEMENTING
BLOCKED_BY_CONTRACT
READY_FOR_REVIEW
CORRECTION_REQUIRED
DOMAIN_COMPLETE
SYSTEM_INTEGRATED
ACCEPTED
```

---

# 28. Final Definition of Done

The phased implementation is complete only when HaruQuantAI can demonstrate all of the following through the existing domains:

1. Select an explicit, eligible, versioned instrument and venue profile.
2. Load point-in-time market, calendar, and reference data without lookahead.
3. Calculate reproducible cockpit indicators with freshness and health state.
4. Produce a complete versioned trade plan.
5. Resolve strict policy, size, stop, RR/expectancy, margin, exposure, drawdown, and stress gates.
6. Persist an idempotent order intent before submission.
7. Process acknowledgements, partial fills, cancels, replaces, unknown states, and protective orders through formal state machines.
8. Simulate latency, queue, liquidity, slippage, gaps, and emergency events deterministically.
9. Rebuild immutable financial state through the Portfolio ledger and valuation rules.
10. Preserve authoritative consequences through disconnects, crashes, and restarts.
11. Run every normal and emergency checklist from actual domain state.
12. Produce process-first score, journal, debrief, replay, and qualification evidence.
13. Govern expectancy and scenario assumptions through source-backed Research profiles.
14. Offer advisory Agentic coaching without weakening deterministic controls.
15. Present the complete cockpit through the web UI/API with accessible, prioritized alerts and safe emergency controls.
16. Pass all 40 specification acceptance criteria, compound-failure tests, and golden replay runs.

---

**End of Implementation Plan**
