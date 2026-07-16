# HaruQuantAI Agile Delivery Roadmap

> **Status:** Replanned thirteen-phase target
> **Releases:** Phases 1-12 = v1.1-v1.12; Phase 13 = v2.0
> **Baseline:** `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, all 13 domain READMEs, and owner clarifications dated 2026-07-16
> **Traceability:** [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md)

## 1. Summary

The roadmap uses 13 vertical-slice phases for 13 authoritative domains. Utils,
Brokers, and Data already exist as completed implementation baselines and are reused,
not rebuilt. Indicators is completed as one full domain before Strategy, which is
also completed as one full domain; their later phase allocations become regression
and compatibility gates for already-landed behavior.

Phase 1 remains a dual production-grade walking skeleton: it runs the complete
deterministic backtest path and performs actual actions on the configured MT5 demo
account. Real MT5 bars and account evidence enter Data, one MA-crossover strategy
emits an intent, Risk sizes and authorizes it, Trading places the actual demo order,
reads and reconciles provider truth, closes the test-owned position, persists factual
execution evidence, and Analytics displays actual outcomes.

Nothing in Phase 1 is disposable. All code must use the final package topology, stable v1 seams, typed contracts, deterministic validation, structured logs, production persistence boundaries, targeted tests, and the project quality gates. Phase 11 hardens the already-operational MT5 path; it does not introduce live broker execution for the first time. Phase 12 closes cross-cutting assurance, and Phase 13 reaches v2.0 parity.

The matrix assigns all **1230** IDs exactly once. No fake adapter participates in the Phase 1 demo or integration proof. The existing ledger-mandated FakeBrokerAdapter remains isolated to Phase 12 contract-test assurance.

## 2. Binding planning principles

1. Every phase delivers a user- or backtest-visible increment and remains runnable, releasable, and demonstrable.
2. Phase 1 touches all 13 domains and proves both Simulation and actual MT5 demo execution.
3. Stable seams exist from Phase 1. Later phases deepen behavior behind them rather than rewrite callers.
4. No throwaway code: narrow Phase 1 implementations are production-grade, typed, logged, documented, persisted where required, and tested.
5. Dependency order inside every phase is Utils -> Brokers -> Data -> Indicators -> Strategy -> Risk -> Trading -> Simulation -> Analytics -> Optimization/Research/Portfolio -> UI/API.
6. Actual broker proof uses `BrokerEnvironment.DEMO` from `MT5_ENVIRONMENT=demo`; the demo aborts before mutation for any other environment.
7. MT5 credentials and provider permission are the real authority path. No fake or synthetic broker result may substitute for the Phase 1 proof.
8. Risk approval, action policy, token reservation, kill-switch state, Trading idempotency, and reconciliation remain authoritative even on demo.
9. Provider outcomes are factual. The plan never predicts or invents fill price, latency, identifiers, or performance.
10. Earlier demos stay green in later phases.
11. Each inventory ID lands once; removed/excluded behavior remains a negative test, not resurrected scope.
12. A requirement already satisfied by a retained full-domain baseline is not
    reimplemented in its allocated phase; that phase verifies compatibility and
    regression evidence against the same authoritative ID.

The existing “Requirement IDs landing in this phase” lists retain the traceability
matrix's first system-slice acceptance allocation. For retained Utils/Brokers/Data
and the pre-Phase-1 full Indicator/Strategy builds, “landing” means the first phase
that must demonstrate that requirement in the integrated system; it does not delay
or split initial domain implementation and never authorizes duplicate code.

## 3. Owner-confirmed decisions

- HaruQuantAI has 13 domains, and the agile roadmap has 13 phases.
- Phase 1 performs actual MT5 demo-account actions, never real-capital actions.
- `.env` currently confirms `MT5_ENVIRONMENT=demo`.
- Phase 1 uses the production MT5 adapter and the production Risk/Trading path, not a fake adapter.
- Production-grade narrow scope and all binding planning principles apply from the first line of implementation.
- Utils, Brokers, and Data are retained completed implementation baselines.
- Indicators is built in full before the full Strategy build; neither is split into
  duplicate later implementations.

## 4. Pass 1 - domain summaries

**Utils.** Business-neutral contracts, logging, errors, IDs, UTC, serialization, redaction, and settings.

**Brokers.** Sole direct provider boundary; MT5 demo is the real Phase 1 mutation authority.

**Data.** Trusted market/account/context/FX evidence plus shared persistence infrastructure.

**Indicators.** Pure availability-aware deterministic formula evaluation.

**Strategy.** Immutable reviewed strategies and canonical TradeIntent proposals.

**Risk.** Independent sizing, approval, token, policy, audit, and kill-switch authority.

**Trading.** Single post-Risk owner of sim/demo/paper/live dispatch, state, reconciliation, and emergency controls.

**Simulation.** Historical orchestrator and simulated execution/account authority.

**Analytics.** Read-only factual metrics, reports, comparisons, scorecards, and dashboards.

**Optimization.** Bounded advisory search using Simulation and Analytics.

**Research.** Leakage-gated advisory studies, profiles, reports, and artifacts.

**Portfolio.** Deterministic allocation construction, activation coordination, drift, and rebalancing.

**UI/API.** Authenticated FastAPI/Next.js composition and presentation boundary.

## 5. Phase table

| Phase | Version | Theme | Capability gained | Exit demo |
|---:|---|---|---|---|
| 1 | 1.1 | Dual walking skeleton: backtest and actual MT5 demo execution | Run the whole product through both deterministic simulation and a real broker-mutating MT5 demo-account path. | Run one MA backtest, then place, reconcile, and close one Risk-approved MT5 demo position and display factual results. |
| 2 | 1.2 | Trusted evidence and observability | Prove provenance, quality, storage, cache, redaction, trace, identity, and audit behavior. | Repeat the Phase 1 workflows through persisted evidence and demonstrate stale/malformed rejection. |
| 3 | 1.3 | Strategy expressiveness | Use the complete official indicator family with immutable vectorized and event strategies. | Register two strategy versions and reproduce their point-in-time decisions. |
| 4 | 1.4 | Independent risk depth | Deepen the Phase 1 safety slice into full portfolio, regime, scenario, and governance analysis. | Show policy caps, regime changes, scenario evidence, and deterministic decision precedence. |
| 5 | 1.5 | Execution robustness | Deepen demo execution with durable state, route authority, idempotency, and unknown-outcome recovery. | Repeat an idempotent demo action and resolve an induced reconciliation discrepancy. |
| 6 | 1.6 | High-fidelity simulation | Add tick-time replay, exact accounting, costs, FX evidence, journals, artifacts, and recovery. | Replay a costed FX backtest and reproduce result and artifact hashes. |
| 7 | 1.7 | Decision-grade analytics | Add benchmark, risk, distribution, cost, statistical, scorecard, comparison, and dashboard evidence. | Render and verify a known-fixture tearsheet and report comparison. |
| 8 | 1.8 | Robust parameter selection | Add walk-forward, overfit, Monte Carlo, stress, checkpoint, and advisory handoff evidence. | Resume a seeded search and inspect robustness evidence before adoption. |
| 9 | 1.9 | Governed multi-strategy portfolios | Construct, simulate, risk-authorize, activate, monitor, and rebalance portfolios. | Activate a capped allocation and produce an authorized reduce-only rebalance. |
| 10 | 1.10 | Reproducible research workflow | Run the leakage-gated Edge Lab through statistical, seasonal, structure, modeling, and artifact evidence. | Persist a ResearchReport and hand a reviewed candidate to Strategy. |
| 11 | 1.11 | MT5 operational hardening and provider depth | Harden the already-running MT5 demo path with feeds, monitoring, recovery, emergency handling, and wider provider depth. | Recover the MT5 demo session, reconcile, emergency-stop, and shut down safely. |
| 12 | 1.12 | Production assurance | Close cross-cutting NFRs, contract-test utilities, security, performance, accessibility, and release evidence. | Run quality, security, contract, recovery, and performance gates without using a fake for the MT5 demo proof. |
| 13 | 2.0 | Completion and parity | Close remaining capabilities, negative-boundary tests, exports, usage evidence, and all ledger checklists. | Run every system workflow and prove no Missing, duplicated, or unassigned scope. |

## 6. Per-phase detail

### Phase 1 - v1.1 - Dual walking skeleton: backtest and actual MT5 demo execution

**Goal:** Run the whole product through both deterministic simulation and a real broker-mutating MT5 demo-account path.

**New system capability:** Run one MA backtest, then place, reconcile, and close one Risk-approved MT5 demo position and display factual results.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Reuse the completed baseline; run Phase 1 contract/settings/logging regression. |
| Brokers | Reuse the completed baseline and its production MT5 adapter for the proof. No fake adapter. |
| Data | Reuse the completed baseline for MT5 bars/account/context evidence and durable dataset/audit support. |
| Indicators | Reuse the complete Indicator domain; the Phase 1 proof exercises availability-aware SMA/EMA through its stable v1 surface. |
| Strategy | Reuse the complete Strategy domain; the Phase 1 proof selects one immutable MA-crossover strategy. |
| Risk | Configured sizing, proposal review, ActionPolicyVerdict, approval token, audit chain, and kill-switch block/clear needed by actual demo mutation. |
| Trading | One production path for sim and MT5 demo: session start, gate, idempotent place/close, factual receipt/record, persistence, basic reconciliation, safe shutdown. |
| Simulation | Simple official backtest loop with deterministic fills, results, and artifacts. |
| Analytics | Core reports from both SimulationResult and factual MT5 demo TradeRecord; never invent fills or performance. |
| Optimization | Bounded deterministic MA grid sweep through official Simulation. |
| Research | Minimal prepared-data/core-metric ResearchReport entry point. |
| Portfolio | Deterministic single-portfolio construction through stable contracts. |
| UI/API | Canonical FastAPI/Next.js app with authenticated controls for backtest and actual MT5 demo place/reconcile/close, plus kill switch and factual status. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `P-SYS-001-002`, `SYS-NFR-001-006`, `SYS-WF-001-002`, `SYS-WF-005`
- **Utils:** `FR-UTL-001-015`, `FR-UTL-021-022`, `FR-UTL-026-035`, `FR-UTL-039-041`, `P-UTL-001-005`, `P-UTL-008`, `WF-UTL-001`
- **Brokers:** `CAP-BRK-001`, `CAP-BRK-003`, `CAP-BRK-012`, `FR-BRK-001-105`, `FR-BRK-110-114`, `FR-BRK-116-118`, `FR-BRK-133`, `P-BRK-001`, `P-BRK-003-004`, `WF-BRK-001-003`, `WF-BRK-008-009`
- **Data:** `CAP-DATA-003-004`, `FR-DATA-001-008`, `FR-DATA-010-013`, `FR-DATA-016`, `FR-DATA-023`, `FR-DATA-026`, `FR-DATA-028`, `FR-DATA-030-036`, `FR-DATA-039`, `FR-DATA-041`, `FR-DATA-046`, `FR-DATA-075-076`, `FR-DATA-078-079`, `P-DATA-001`, `P-DATA-004`, `P-DATA-008`, `WF-DATA-001`, `WF-DATA-013-014`
- **Indicators:** `FR-INDI-001-017`, `P-INDI-001-002`, `WF-INDI-001-002`
- **Strategy:** `FR-STR-001-021`, `FR-STR-023-026`, `FR-STR-029-033`, `P-STR-001`, `P-STR-004`, `P-STR-006`, `WF-STR-001-002`, `WF-STR-004`
- **Risk:** `FR-RISK-001-021`, `FR-RISK-023`, `FR-RISK-025-027`, `FR-RISK-029-031`, `FR-RISK-033-034`, `FR-RISK-036-046`, `FR-RISK-058-060`, `P-RISK-001-002`, `P-RISK-004-005`, `P-RISK-007-009`, `WF-RISK-002`, `WF-RISK-004`, `WF-RISK-008-009`, `WF-RISK-012`
- **Trading:** `FR-TRD-001-010`, `FR-TRD-012-028`, `FR-TRD-030-039`, `FR-TRD-042-046`, `FR-TRD-048-058`, `FR-TRD-061-062`, `P-TRD-001-005`, `P-TRD-007-009`, `WF-TRD-001-004`, `WF-TRD-006`, `WF-TRD-008`, `WF-TRD-011-012`
- **Simulation:** `CAP-SIM-001`, `CAP-SIM-004`, `FR-SIM-001-003`, `FR-SIM-005-006`, `FR-SIM-010`, `FR-SIM-014`, `FR-SIM-016`, `FR-SIM-018-031`, `P-SIM-001`, `P-SIM-005-007`, `WF-SIM-001-002`
- **Analytics:** `FR-ANLT-001-014`, `FR-ANLT-016-018`, `FR-ANLT-020-023`, `FR-ANLT-025`, `FR-ANLT-027-028`, `FR-ANLT-033-034`, `FR-ANLT-036`, `FR-ANLT-038-046`, `P-ANLT-001-002`, `P-ANLT-004`, `P-ANLT-006`, `WF-ANLT-001`, `WF-ANLT-005-006`
- **Optimization:** `FR-OPT-001-007`, `FR-OPT-010-013`, `FR-OPT-015-028`, `FR-OPT-032-033`, `FR-OPT-038-040`, `FR-OPT-042-049`, `FR-OPT-053`, `P-OPT-001`, `P-OPT-003-004`, `P-OPT-007`, `P-OPT-009`, `WF-OPT-001-002`
- **Research:** `FR-RES-001-031`, `FR-RES-042-050`, `FR-RES-069`, `FR-RES-075`, `FR-RES-077`, `FR-RES-081`, `FR-RES-089-096`, `P-RES-001-002`, `P-RES-005`, `P-RES-011`, `WF-RES-001-002`
- **Portfolio:** `FR-PORT-001-006`, `FR-PORT-009-015`, `FR-PORT-018-020`, `FR-PORT-024-025`, `FR-PORT-029-030`, `FR-PORT-034-037`, `P-PORT-001`, `P-PORT-003`, `P-PORT-008`, `WF-PORT-002`
- **UI/API:** `CAP-UI-001-003`, `CAP-UI-007`, `CAP-UI-013-014`, `CAP-UI-024`, `FR-API-001-008`, `FR-API-013-015`, `FR-API-017-026`, `FR-API-028-032`, `FR-API-034-051`, `FR-API-053-058`, `P-API-001-004`, `P-API-006-011`, `WF-API-001-002`, `WF-API-004`, `WF-API-006`, `WF-API-012-013`, `WF-API-015`

#### Public interfaces

Define all registered v1 names, owners, schema IDs, capability-scoped ports, compatibility rules, and package-root operations. Narrow unsupported behavior fails deterministically; it never returns a synthetic success.

#### Exit criteria

- **Functional:** Run one MA backtest, then place, reconcile, and close one Risk-approved MT5 demo position and display factual results.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.1 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires integration-late and broker-integration-late risk. Phase 1 is very large (675 IDs) because actual MT5 demo mutation pulls safety, persistence, and reconciliation forward.

### Phase 2 - v1.2 - Trusted evidence and observability

**Goal:** Prove provenance, quality, storage, cache, redaction, trace, identity, and audit behavior.

**New system capability:** Repeat the Phase 1 workflows through persisted evidence and demonstrate stale/malformed rejection.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Regression only; the completed baseline already contains the assigned behavior. |
| Brokers | Regression only; the completed baseline already contains the assigned behavior. |
| Data | Regression only; the completed baseline already contains the assigned behavior. |
| Indicators | Regression of completed quality/provenance evidence propagation. |
| Strategy | Regression of completed diagnostics and point-in-time checks. |
| Risk | Consume stronger evidence through Phase 1 gates. |
| Trading | Persist richer dependency failures. |
| Simulation | Block severe data-quality errors. |
| Analytics | Harden adapters, JSON safety, warnings, lineage, and hashes. |
| Optimization | Validate provenance before search. |
| Research | Harden dataset preparation/core profiles. |
| Portfolio | Consume validated evidence. |
| UI/API | Deepen sessions, middleware, readiness, settings, and audit views. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `P-SYS-003`
- **Utils:** `FR-UTL-016-020`, `FR-UTL-023-024`, `NFR-UTL-001-007`, `P-UTL-006-007`, `WF-UTL-002-003`
- **Brokers:** `CAP-BRK-005`, `CAP-BRK-016`, `FR-BRK-108`, `FR-BRK-130-132`, `P-BRK-008`
- **Data:** `CAP-DATA-007`, `CAP-DATA-015-016`, `FR-DATA-014-015`, `FR-DATA-017-022`, `FR-DATA-024-025`, `FR-DATA-027`, `FR-DATA-037-038`, `FR-DATA-077`, `FR-DATA-080-084`, `P-DATA-002-003`, `P-DATA-005`, `WF-DATA-002-005`, `WF-DATA-009-011`
- **Strategy:** `P-STR-002`, `WF-STR-006`
- **Simulation:** `CAP-SIM-009`
- **UI/API:** `CAP-UI-008-009`, `FR-API-009-012`, `FR-API-016`, `WF-API-016`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Repeat the Phase 1 workflows through persisted evidence and demonstrate stale/malformed rejection.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.2 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires weak evidence; adds bounded storage/source-policy complexity.

### Phase 3 - v1.3 - Strategy expressiveness

**Goal:** Use the complete official indicator family with immutable vectorized and event strategies.

**New system capability:** Register two strategy versions and reproduce their point-in-time decisions.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Regression only. |
| Brokers | Contract compatibility regression. |
| Data | Regression of completed point-in-time multi-timeframe data. |
| Indicators | Regression of the already complete official indicator family. |
| Strategy | Regression/deepening behind the already complete Strategy v1 seams. |
| Risk | Review richer intents through stable ports. |
| Trading | Orchestrate richer decisions without translating signals. |
| Simulation | Exercise registered strategies and reject raw code. |
| Analytics | Accept richer metadata. |
| Optimization | Complete parameter contracts/constraints. |
| Research | Add feature-frame inputs. |
| Portfolio | Validate immutable Strategy references. |
| UI/API | Expose strategy catalogue/version/run views. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **Indicators:** `FR-INDI-018-022`, `P-INDI-003-004`, `WF-INDI-003-005`
- **Strategy:** `FR-STR-022`, `P-STR-003`, `P-STR-007`, `WF-STR-003`, `WF-STR-008-009`
- **Simulation:** `CAP-SIM-010`, `WF-SIM-006`
- **UI/API:** `CAP-UI-010`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Register two strategy versions and reproduce their point-in-time decisions.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.3 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires strategy narrowness; adds state/no-lookahead complexity.

### Phase 4 - v1.4 - Independent risk depth

**Goal:** Deepen the Phase 1 safety slice into full portfolio, regime, scenario, and governance analysis.

**New system capability:** Show policy caps, regime changes, scenario evidence, and deterministic decision precedence.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Governance primitive regression. |
| Brokers | Exercise completed account/execution read depth through the new Risk consumers. |
| Data | Exercise completed `MarketContextEvidence` through the new Risk consumers. |
| Indicators | Availability regression. |
| Strategy | Exercise completed intent evidence. |
| Risk | Complete portfolio snapshot, limits, regimes, scenarios, allocation/admission governance, and focused reporting. |
| Trading | Consume deeper Risk evidence without self-approval. |
| Simulation | Exercise full sim policy. |
| Analytics | Present non-binding Risk evidence. |
| Optimization | Remain advisory. |
| Research | Consume ScenarioResult only. |
| Portfolio | Prepare portfolio governance adapters. |
| UI/API | Expose full Risk decision support. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **Risk:** `FR-RISK-022`, `FR-RISK-024`, `FR-RISK-028`, `FR-RISK-032`, `FR-RISK-035`, `P-RISK-003`, `P-RISK-006`, `P-RISK-010-011`, `WF-RISK-001`, `WF-RISK-003`, `WF-RISK-005`, `WF-RISK-010-011`, `WF-RISK-014`
- **Trading:** `FR-TRD-059-060`, `WF-TRD-007`
- **Simulation:** `CAP-SIM-006`
- **UI/API:** `WF-API-003`, `WF-API-011`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Show policy caps, regime changes, scenario evidence, and deterministic decision precedence.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.4 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires shallow governance; adds portfolio/regime/scenario complexity.

### Phase 5 - v1.5 - Execution robustness

**Goal:** Deepen demo execution with durable state, route authority, idempotency, and unknown-outcome recovery.

**New system capability:** Repeat an idempotent demo action and resolve an induced reconciliation discrepancy.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Trace/redaction regression. |
| Brokers | Exercise retained cTrader/Binance execution profiles and transport mapping through Trading; run compatibility regression. |
| Data | Refresh authority facts. |
| Indicators | No change. |
| Strategy | Supply paper/demo decisions. |
| Risk | Revalidate evidence/tokens. |
| Trading | Complete state projections, routing, retry guard, discrepancy handling, and richer reconciliation. |
| Simulation | Sim compatibility. |
| Analytics | Adapt richer factual records. |
| Optimization | No change. |
| Research | No change. |
| Portfolio | Consume factual execution outcomes. |
| UI/API | Expose idempotency/reconciliation incidents. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **Brokers:** `CAP-BRK-013-014`, `FR-BRK-106`, `FR-BRK-115`, `FR-BRK-119-125`, `P-BRK-002`, `P-BRK-005-006`, `WF-BRK-004-005`, `WF-BRK-007`
- **Data:** `CAP-DATA-008`
- **Trading:** `FR-TRD-029`, `FR-TRD-040-041`, `WF-TRD-005`
- **Simulation:** `CAP-SIM-005`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Repeat an idempotent demo action and resolve an induced reconciliation discrepancy.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.5 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires minimal reconciliation; unknown outcomes remain fail-closed.

### Phase 6 - v1.6 - High-fidelity simulation

**Goal:** Add tick-time replay, exact accounting, costs, FX evidence, journals, artifacts, and recovery.

**New system capability:** Replay a costed FX backtest and reproduce result and artifact hashes.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Serialization/time hash regression. |
| Brokers | Prove simulation network isolation. |
| Data | Exercise completed FX evidence and the simulation-modeling boundary. |
| Indicators | Regression of completed decision-time availability. |
| Strategy | Exercise completed replay checkpoints. |
| Risk | Evaluate every sim intent. |
| Trading | Keep identical sim formulation. |
| Simulation | Complete tick timeline, pricing, Decimal ledger, costs, margin, journal, replay, artifacts, and official/research modes. |
| Analytics | Consume richer SimulationResult. |
| Optimization | Use official Simulation adapter. |
| Research | Expose labeled fast research. |
| Portfolio | Add portfolio-backtest projections. |
| UI/API | Display realism and replay evidence. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **Data:** `CAP-DATA-019`, `WF-DATA-012`, `WF-DATA-015`
- **Strategy:** `FR-STR-027-028`, `P-STR-005`, `WF-STR-005`
- **Simulation:** `CAP-SIM-007`, `FR-SIM-004`, `FR-SIM-007-009`, `FR-SIM-011-013`, `FR-SIM-015`, `FR-SIM-017`, `P-SIM-002-004`, `WF-SIM-004-005`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Replay a costed FX backtest and reproduce result and artifact hashes.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.6 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires bar-only realism; model risk stays explicit.

### Phase 7 - v1.7 - Decision-grade analytics

**Goal:** Add benchmark, risk, distribution, cost, statistical, scorecard, comparison, and dashboard evidence.

**New system capability:** Render and verify a known-fixture tearsheet and report comparison.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | No change. |
| Brokers | No change. |
| Data | Serve benchmark/FX evidence. |
| Indicators | No change. |
| Strategy | No change. |
| Risk | No change. |
| Trading | Supply factual fills/costs. |
| Simulation | Supply complete simulation evidence. |
| Analytics | Complete metrics, benchmarks, statistics, scorecards, comparisons, allocation evidence, and dashboards. |
| Optimization | Consume Analytics metrics. |
| Research | Consume public metric evidence. |
| Portfolio | Consume allocation evidence. |
| UI/API | Expose report/comparison/dashboard views. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **Simulation:** `CAP-SIM-008`
- **Analytics:** `FR-ANLT-029-032`, `FR-ANLT-035`, `FR-ANLT-037`, `P-ANLT-003`, `P-ANLT-005`, `WF-ANLT-002-004`, `WF-ANLT-007-008`, `WF-ANLT-010`
- **UI/API:** `CAP-UI-018`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Render and verify a known-fixture tearsheet and report comparison.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.7 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires shallow metrics; interpretation is cataloged and caveated.

### Phase 8 - v1.8 - Robust parameter selection

**Goal:** Add walk-forward, overfit, Monte Carlo, stress, checkpoint, and advisory handoff evidence.

**New system capability:** Resume a seeded search and inspect robustness evidence before adoption.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | No change. |
| Brokers | No change. |
| Data | Serve bounded leakage-safe data. |
| Indicators | No change. |
| Strategy | Validate candidate/version compatibility. |
| Risk | No approval implication. |
| Trading | Simulation route only. |
| Simulation | Provide deterministic candidate backtests. |
| Analytics | Provide objectives/caveats. |
| Optimization | Complete ranking, random search, splits, walk-forward, overfit, Monte Carlo, stress, evidence, state, and API. |
| Research | No change. |
| Portfolio | No change. |
| UI/API | Expose synchronous optimization and explicit adoption. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `SYS-WF-003`
- **Simulation:** `CAP-SIM-012-013`, `WF-SIM-003`
- **Optimization:** `FR-OPT-008-009`, `FR-OPT-014`, `FR-OPT-029-031`, `FR-OPT-034-037`, `FR-OPT-041`, `FR-OPT-050-052`, `FR-OPT-054-055`, `P-OPT-002`, `P-OPT-005-006`, `P-OPT-008`, `WF-OPT-003-006`
- **UI/API:** `CAP-UI-015`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Resume a seeded search and inspect robustness evidence before adoption.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.8 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires naive selection; compute/overfit risk is capped.

### Phase 9 - v1.9 - Governed multi-strategy portfolios

**Goal:** Construct, simulate, risk-authorize, activate, monitor, and rebalance portfolios.

**New system capability:** Activate a capped allocation and produce an authorized reduce-only rebalance.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | No change. |
| Brokers | No change. |
| Data | Supply market/account/FX truth. |
| Indicators | No change. |
| Strategy | Publish eligible immutable references. |
| Risk | Complete eligibility, allocation review/caps, authoritative budgets, and activation/rebalance authorization. |
| Trading | Execute only authorized rebalance requests. |
| Simulation | Run portfolio backtests. |
| Analytics | Produce allocation/performance evidence. |
| Optimization | No change. |
| Research | No change. |
| Portfolio | Complete construction methods, state, activation, drift, rollback, and rebalancing. |
| UI/API | Expose portfolio lifecycle workflows. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `SYS-WF-006-008`
- **Risk:** `WF-RISK-006-007`
- **Trading:** `WF-TRD-013`
- **Simulation:** `WF-SIM-009`
- **Analytics:** `WF-ANLT-009`, `WF-ANLT-013`
- **Portfolio:** `FR-PORT-007-008`, `FR-PORT-016-017`, `FR-PORT-021-023`, `FR-PORT-026-028`, `FR-PORT-031-033`, `P-PORT-002`, `P-PORT-004-007`, `WF-PORT-001`, `WF-PORT-003-007`
- **UI/API:** `WF-API-010`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Activate a capped allocation and produce an authorized reduce-only rebalance.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.9 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires single-strategy allocation limits; receiver-owned projections avoid cycles.

### Phase 10 - v1.10 - Reproducible research workflow

**Goal:** Run the leakage-gated Edge Lab through statistical, seasonal, structure, modeling, and artifact evidence.

**New system capability:** Persist a ResearchReport and hand a reviewed candidate to Strategy.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | No change. |
| Brokers | No change. |
| Data | Supply research-ready data. |
| Indicators | No change. |
| Strategy | Accept only reviewed candidates. |
| Risk | Research remains advisory. |
| Trading | No change. |
| Simulation | Expose labeled fast research. |
| Analytics | Supply public metric evidence. |
| Optimization | No change. |
| Research | Complete features, leakage, statistics, studies, seasonality, market structure, PCA/K-Means, profiles, scorecards, rendering, and artifacts. |
| Portfolio | No change. |
| UI/API | Expose Edge Lab, artifacts, comparisons, and reviewed handoff. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `SYS-WF-004`
- **Simulation:** `WF-SIM-007`
- **Research:** `FR-RES-032-041`, `FR-RES-051-068`, `FR-RES-070-074`, `FR-RES-076`, `FR-RES-078-080`, `FR-RES-082-088`, `FR-RES-097`, `P-RES-003-004`, `P-RES-006-010`, `P-RES-012`, `WF-RES-003-011`
- **UI/API:** `WF-API-009`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Persist a ResearchReport and hand a reviewed candidate to Strategy.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.10 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires ad hoc research; leakage/multiple testing remain gated.

### Phase 11 - v1.11 - MT5 operational hardening and provider depth

**Goal:** Harden the already-running MT5 demo path with feeds, monitoring, recovery, emergency handling, and wider provider depth.

**New system capability:** Recover the MT5 demo session, reconcile, emergency-stop, and shut down safely.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Re-run completed logging lifecycle/rotation/shutdown assurance. |
| Brokers | Exercise retained MT5 reconnect/stream/backpressure and provider-depth behavior. |
| Data | Re-run completed jobs/backfills, feeds, readiness/promotion, and recovery assurance. |
| Indicators | Live availability regression. |
| Strategy | Supply live decisions/checkpoint recovery. |
| Risk | Revalidate approvals and recovery eligibility. |
| Trading | Complete monitoring, budgets, session recovery, emergency controls, startup reconciliation, and shutdown around the existing demo path. |
| Simulation | Prove network isolation. |
| Analytics | Consume stale/unreconciled flags. |
| Optimization | No change. |
| Research | No change. |
| Portfolio | Monitor active allocation/outcomes. |
| UI/API | Complete streams, readiness, operator incidents, and recovery UI. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `P-SYS-004`
- **Brokers:** `CAP-BRK-007`, `CAP-BRK-015`, `FR-BRK-107`, `FR-BRK-126-129`, `P-BRK-007`, `WF-BRK-006`
- **Data:** `CAP-DATA-010`, `FR-DATA-042-045`, `FR-DATA-047-048`, `P-DATA-006-007`, `WF-DATA-007-008`
- **Strategy:** `WF-STR-007`
- **Trading:** `FR-TRD-047`, `P-TRD-006`, `WF-TRD-009-010`
- **UI/API:** `CAP-UI-020`, `P-API-005`, `WF-API-005`, `WF-API-017`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Recover the MT5 demo session, reconcile, emergency-stop, and shut down safely.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.11 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires operational weakness in the already-live demo path.

### Phase 12 - v1.12 - Production assurance

**Goal:** Close cross-cutting NFRs, contract-test utilities, security, performance, accessibility, and release evidence.

**New system capability:** Run quality, security, contract, recovery, and performance gates without using a fake for the MT5 demo proof.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Re-run NFR, export, usage, and shutdown assurance against the retained baseline. |
| Brokers | Re-run NFRs and FakeBrokerAdapter contract assurance; never use the fake as Phase 1/demo authority. |
| Data | Re-run NFR, migration, precision, and recovery assurance against the retained baseline. |
| Indicators | Re-run formula fixtures and performance gates against the complete domain. |
| Strategy | Re-run NFR, migration, export, and replay assurance against the complete domain. |
| Risk | Security, concurrency, persistence, and tamper tests. |
| Trading | Safety, reconciliation, timeout, and performance assurance. |
| Simulation | Determinism/resource/error assurance. |
| Analytics | Finite-output, catalog, fixture, and hash assurance. |
| Optimization | Bounded-resource/state/checkpoint assurance. |
| Research | Leakage/resource/artifact assurance. |
| Portfolio | Determinism/persistence assurance. |
| UI/API | Security, route drift, accessibility, responsiveness, and client-contract assurance. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `P-SYS-006`
- **Brokers:** `CAP-BRK-019`, `FR-BRK-109`, `FR-BRK-134`, `NFR-BRK-001-015`, `P-BRK-009`
- **Data:** `NFR-DATA-001-012`
- **Indicators:** `NFR-INDI-001-014`
- **Strategy:** `NFR-STR-001-012`
- **Risk:** `NFR-RISK-001-012`
- **Trading:** `NFR-TRD-001-008`
- **Simulation:** `NFR-SIM-001-012`
- **Analytics:** `NFR-ANLT-001-013`
- **Optimization:** `NFR-OPT-001-012`
- **Research:** `NFR-RES-001-015`
- **Portfolio:** `NFR-PORT-001-010`
- **UI/API:** `NFR-API-001-018`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Run quality, security, contract, recovery, and performance gates without using a fake for the MT5 demo proof.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.12 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires cross-cutting quality gaps; fake utility is isolated to test assurance.

### Phase 13 - v2.0 - Completion and parity

**Goal:** Close remaining capabilities, negative-boundary tests, exports, usage evidence, and all ledger checklists.

**New system capability:** Run every system workflow and prove no Missing, duplicated, or unassigned scope.

#### Per-domain work

| Domain | Work |
|---|---|
| Utils | Close residual repository-quality evidence without rebuilding the package. |
| Brokers | Close residual provider/release evidence without rebuilding its contracts or adapters. |
| Data | Close residual repository-quality and negative-boundary evidence without rebuilding the package. |
| Indicators | Close residual exports/usage evidence against the already complete v1 package. |
| Strategy | Close residual checklist evidence against the already complete v1 package. |
| Risk | Close package checklist. |
| Trading | Close capability catalogue and package checklist. |
| Simulation | Close exclusions and usage checklist. |
| Analytics | Close output/usage checklist. |
| Optimization | Close public API/usage checklist. |
| Research | Close artifacts/usage checklist. |
| Portfolio | Close portfolio checklist. |
| UI/API | Close remaining routes, negative boundaries, and UI checklist. |

#### Requirement IDs landing in this phase

Exact rows are authoritative in the traceability matrix; ranges compact the same IDs.

- **System:** `P-SYS-005`
- **Brokers:** `CAP-BRK-002`, `CAP-BRK-004`, `CAP-BRK-006`, `CAP-BRK-008-011`, `CAP-BRK-017-018`, `FR-BRK-135`
- **Data:** `CAP-DATA-001-002`, `CAP-DATA-005-006`, `CAP-DATA-009`, `CAP-DATA-011-014`, `CAP-DATA-017-018`, `CAP-DATA-020-021`, `FR-DATA-009`, `FR-DATA-029`, `FR-DATA-040`, `WF-DATA-006`
- **Trading:** `CAP-TRD-001-019`, `CAP-TRD-022-025`
- **Simulation:** `CAP-SIM-002-003`, `CAP-SIM-011`
- **Analytics:** `FR-ANLT-024`, `FR-ANLT-026`
- **UI/API:** `CAP-UI-004-006`, `CAP-UI-011-012`, `CAP-UI-016`, `CAP-UI-019`, `CAP-UI-021-023`, `FR-API-027`, `WF-API-007-008`

#### Public interfaces

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

#### Exit criteria

- **Functional:** Run every system workflow and prove no Missing, duplicated, or unassigned scope.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v2.0 only after documented automated checks and the phase exit demo pass.

#### Risks introduced or retired

Retires all remaining parity gaps; checklist claims require evidence.

## 7. Phase 1 deep dive

### 7.1 Final-topology file minimum

| Domain | Phase 1 minimum |
|---|---|
| Utils | Reuse the complete v1 package; Phase 1 exercises contracts, settings, security, logging, and exports |
| Brokers | Reuse the complete v1 package and production MT5 adapter; no fake in the proof |
| Data | Reuse the complete v1 package for MT5-backed access, account/context evidence, storage/audit, and public operations |
| Indicators | Complete v1 package: Core, trend, volatility, momentum, tests, and public exports |
| Strategy | Complete v1 package per its README; Phase 1 selects the immutable MA-crossover implementation |
| Risk | contracts, config, sizing, minimum policy, audit chain, approvals, decisions, kill switch, public API |
| Trading | contracts, state, validation, routing, reconciliation, live session, actions, evidence, migrations |
| Simulation | validation, minimum accounting/execution/reporting, official orchestrator |
| Analytics | contracts, factual adapters, core metrics, report builder, dashboard payload |
| Optimization | parameters, Simulation adapter, grid/sweep, minimum evidence |
| Research | contracts, data preparation, core metric profile, minimum ResearchReport |
| Portfolio | contracts, deterministic construction, public API |
| UI/API | FastAPI contracts/identity/middleware/health/routes/composition/main and minimal Next.js clients/context/components/pages |

Every file is part of the approved final structure. Temporary broker facades, fake live routes, duplicate contracts, bypass policies, and prototype persistence are prohibited.

### 7.2 Deterministic simulation path

1. Fetch and normalize real MT5 historical bars.
2. Calculate short/long moving averages with availability metadata.
3. Evaluate the immutable MA-crossover strategy.
4. Submit each TradeIntent to Risk.
5. Trading formulates sim OrderIntent values from approved decisions.
6. Simulation produces deterministic fills/results/artifacts.
7. Analytics reports core metrics; Optimization sweeps parameters; Research and Portfolio return their narrow outputs.
8. UI/API displays evidence and trace lineage.

### 7.3 Actual MT5 demo execution path

1. The proof preflight reads the non-secret environment selection and requires exactly `MT5_ENVIRONMENT=demo`.
2. UI/API resolves configured credentials in memory and constructs `BrokerConnectionConfig v1` with `BrokerEnvironment.DEMO`.
3. MT5 connect verifies the configured terminal, login, server, account identity, and trade permission. Any mismatch aborts before mutation.
4. Data obtains current bars, account snapshot, and minimum market context through Brokers read traits.
5. Indicators and Strategy produce one canonical proposal. Neutral output performs no action.
6. Risk applies the configured policy, final size, attestation, action verdict, approval-token reservation, and kill-switch state. Missing evidence blocks.
7. Trading reserves idempotency, starts the real MT5 demo session, packages the approved size, and calls the production MT5 adapter once.
8. Brokers returns factual provider acknowledgement. Trading persists the receipt, reads authority state, and reconciles without blind retry.
9. Trading closes only the position created by this proof through the same gates, reads authority state again, and proves that proof-owned exposure is reconciled.
10. Analytics consumes factual TradeRecord evidence. UI/API displays actual provider IDs, prices, times, costs when supplied, reconciliation status, and warnings without manufacturing missing values.
11. The kill-switch check proves a subsequent risk-increasing mutation is blocked, then the session shuts down safely.

The proof is valid only when the configured market is open and the MT5 demo account permits trading. A market-closed or permission-denied result is an honest fail-closed outcome, not a successful release demo.

### 7.4 Phase 1 proof commands

```powershell
Select-String -LiteralPath .env -Pattern '^MT5_ENVIRONMENT=demo$'
$env:RUNTIME_PROFILE = 'simulation'
$env:EXECUTION_ROUTE = 'sim'
$env:ALLOW_LIVE_MUTATIONS = 'false'
uv run pytest tests/system/integration/test_backtest.py --cov=app --cov-fail-under=80
$env:RUNTIME_PROFILE = 'paper'
$env:EXECUTION_ROUTE = 'paper'
$env:ALLOW_LIVE_MUTATIONS = 'true'
uv run pytest tests/system/integration/test_signal_to_mt5_demo.py --cov=app --cov-fail-under=80
uv run python tests/system/usage/phase1_mt5_demo.py
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run uvicorn app.services.api.main:app --host 127.0.0.1 --port 8000
npm --prefix ui run dev
```

The MT5 usage command performs the actual demo-account place/reconcile/close proof and must refuse non-demo configuration. The explicit per-process `paper` profile/route selects the architecture's real demo-account path; `ALLOW_LIVE_MUTATIONS=true` opens the Trading-owned gate only for that command sequence, while `BrokerEnvironment.DEMO` remains mandatory. The proof does not use `FakeBrokerAdapter`, monkeypatched provider success, invented fills, or an in-memory substitute. Test-owned position identity is captured from factual MT5 results and used for the close/reconciliation step.

## 8. Interface contracts from Phase 1 onward

| Domain | Stable Phase 1 surface | Stability |
|---|---|---|
| Utils | AuthContext/AuditEvent, errors, IDs, UTC, canonical JSON, redaction, AppSettings, logging | Stable v1 |
| Brokers | BrokerAdapter traits, config, result/error/DTO/event family, registry, production adapters | Complete v1 baseline; later phases exercise consumers and evidence |
| Data | MarketDataset, AccountStateSnapshot, MarketContextEvidence, FXConversionEvidence, audit query/page, typed operations | Complete v1 baseline; later phases exercise consumers and evidence |
| Indicators | IndicatorSeries, calculation/spec/result, registry, complete official formula family | Complete v1 baseline before Phase 1 |
| Strategy | Registration/update/result, TradeIntent, evaluation, replay, diagnostics, approved strategy family | Complete v1 baseline before Phase 1 |
| Risk | RiskDecision, action verdict, approval, token, kill switch, eligibility, allocation, scenario, governor/sizing | Stable authority |
| Trading | OrderIntent, receipt, record, operational event, action/readiness/reconciliation/session APIs | Reliability deepens |
| Simulation | Backtest/portfolio requests/results and run/replay ports | Realism deepens |
| Analytics | PerformanceReport, DashboardPayload, PortfolioAllocationEvidence, comparison | Sections deepen |
| Optimization | OptimizationResult and search/validation/robustness/evidence ports | Algorithms deepen |
| Research | ResearchReport and classified stage/report API | Stages deepen |
| Portfolio | Construction/result, active allocation, rebalance plan, lifecycle APIs | Lifecycle deepens |
| UI/API | ApiResponse/Error/Metadata, StreamEvent, RouteContract, governed/page context, ASGI app, typed clients | Routes activate |

## 9. Deviations from the original seed

- Thirteen phases replace twelve because the owner confirmed thirteen domains and authorized matching phase count.
- Phase 1 includes actual MT5 demo broker mutation, basic persistence/reconciliation, approval tokens, kill switch, and authenticated operator controls.
- Utils exceeds logging-only because production seams require shared context, errors, IDs, UTC, serialization, redaction, and settings.
- Data exceeds bars-only because actual mutation requires account and market-context truth plus factual audit evidence.
- Risk exceeds sizing-only because real demo mutation cannot use a safety bypass.
- Trading exceeds basic formulation because actual mutation requires idempotency, receipt persistence, reconciliation, and safe close.
- Analytics reports both simulation and factual demo execution evidence.
- The fake adapter is explicitly excluded from Phase 1 proof and moved to Phase 12 test assurance.
- Phase 11 hardens an existing actual broker path rather than introducing it.

## 10. Open questions and assumptions

1. **MT5 terminology:** The roadmap calls this "actual MT5 demo execution." Under the current profile/route compatibility table it runs as `paper`/`paper` with `BrokerEnvironment.DEMO`, exercises the shared production paper/live execution code, and performs real broker mutations without targeting real capital.
2. **Market availability:** The release demo requires an open market and a trade-permitted configured symbol/account. The system must not fabricate success when unavailable.
3. **Configured risk values:** The roadmap invents no volume or threshold. Phase 1 uses the authoritative configured Risk policy and factual broker constraints.
4. **Test-only fake scope:** The FakeBrokerAdapter remains only because it is explicit current ledger scope and is useful for deterministic contract failure tests. It cannot satisfy or replace the MT5 demo proof.
5. **Phase 1 size:** Phase 1 contains **675** IDs. Many are trace/container/contract IDs, but actual broker execution makes this a materially large phase.
6. **Phase 13 exceptions:** None known. Any impossible requirement must reopen this section and the matrix rather than disappear.

## 11. Pass 4 verification

- [X] Exactly 13 phases: v1.1-v1.12 and v2.0.
- [X] All 13 domains appear in every phase breakdown.
- [X] Phase 1 includes deterministic Simulation and actual MT5 demo place/reconcile/close.
- [X] No fake adapter participates in the Phase 1 proof.
- [X] Every inventory ID is assigned exactly once: **1230**.
- [X] Unassigned: **0**; duplicates: **0**.
- [X] Dependencies resolve to same/earlier phases.
- [X] No architecture, infrastructure dependency, numerical risk limit, or fabricated broker behavior was introduced.
