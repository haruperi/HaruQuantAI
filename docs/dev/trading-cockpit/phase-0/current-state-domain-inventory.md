# Current-State Domain Inventory

**Work package:** `TC-IMP-BASE-02`
**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Captured (UTC):** `2026-08-07T07:57:07Z`

Fourteen domains, inspected in the exact implementation order defined by the phased plan. Every claim
below is anchored to a path, symbol, table or test file located during the audit. A directory name or a
class name alone was never treated as evidence.

---

## 0. Physical layout and the UI-API question

The fourteen logical domains do **not** map one-to-one onto fourteen folders.

| Logical domain | Physical location(s) |
|---|---|
| Utils | `app/utils/` |
| Brokers | `app/services/brokers/` |
| Data | `app/services/data/` |
| Indicators | `app/services/indicators/` |
| Strategy | `app/services/strategy/` |
| Risk | `app/services/risk/` |
| Trading | `app/services/trading/` |
| Simulator | `app/services/simulator/` |
| Analytics | `app/services/analytics/` |
| Optimization | `app/services/optimization/` |
| Research | `app/services/research/` |
| Portfolio | `app/services/portfolio/` |
| Agentic | `app/agentic/` — **top-level, not under `app/services/`** |
| UI-API | **two locations**: `app/services/api/` (FastAPI backend) and `app/ui/` (Next.js frontend) |

Two structural facts matter for the cockpit:

1. **Agentic is deliberately top-level.** `AGENTS.md` section 1 records this as an approved exception:
   `app/agentic/` is the orchestration domain, follows the same one-feature-per-module rules, and must
   still cross `app/services/[DOMAIN]` public boundaries like any other consumer.
2. **UI-API is a Python backend plus a TypeScript frontend.** `app/services/api/` holds 81 Python files
   and 19 route modules; `app/ui/src/` holds 102 `.ts`/`.tsx` files. `app/services/api/README.md`
   registers `FEAT-API-09` (typed frontend transport), `FEAT-API-10` (frontend session and page context),
   `FEAT-API-11` (workflow presentation components) and `FEAT-API-12` (protected workflow pages), so the
   backend README is the feature registry for both halves. Phase 14 must respect this split rather than
   assuming a single folder.

Also present: `app/runtime.py` (application composition), `app/configs/` (`env.json`,
`gcp-oauth.keys.json`), `scripts/` (including `ci_check.py`), `docs/schema/` (target schema model with
`verify_schema.py`, `compare_model_to_code.py`, `verify_persistence_sql.py`).

### 0.1 Architectural rules that constrain every later phase

Verified empirically, not just read from `AGENTS.md`:

- **Package-Root Export Gate.** `app/services/[DOMAIN]/__init__.py` is the sole public import boundary.
- **No Deep Cross-Domain Imports.** Consumers must import from `app.services.[DOMAIN]` only.
- **Function-Only Public API Surface.** Across all fourteen domains, `__all__` contains **1064 names and
  zero class-like names**. Every domain exports only functions. Every contract the Trading Cockpit plan
  requires is a type. This is the single largest architectural collision in the programme and is recorded
  as a blocking owner decision in `phase-0-findings-and-decisions.md`.
- **One feature = one module folder = one usage program.** 165 features are registered across the
  fourteen domain READMEs; `tests/*/usage/` holds 411 standalone usage programs.

---

## Domain audit summary matrix

| Domain | README | Database | Unit Tests | FR Usage | Workflow | UI/API Connection | Telemetry | Persistence | Safety | Overall Evidence Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Utils | VERIFIED | NOT_APPLICABLE | VERIFIED | VERIFIED | VERIFIED | NOT_APPLICABLE | VERIFIED | NOT_APPLICABLE | VERIFIED | VERIFIED |
| Brokers | VERIFIED | PARTIAL | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | PARTIAL | VERIFIED | VERIFIED |
| Data | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED |
| Indicators | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED | PARTIAL | VERIFIED | NOT_APPLICABLE | VERIFIED |
| Strategy | VERIFIED | CONFLICTING | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED | PARTIAL | PARTIAL |
| Risk | VERIFIED | CONFLICTING | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL |
| Trading | VERIFIED | CONFLICTING | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL |
| Simulator | VERIFIED | PARTIAL | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| Analytics | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED | PARTIAL | VERIFIED | NOT_APPLICABLE | VERIFIED |
| Optimization | VERIFIED | PARTIAL | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED | PARTIAL | VERIFIED |
| Research | VERIFIED | PARTIAL | VERIFIED | VERIFIED | VERIFIED | VERIFIED | PARTIAL | PARTIAL | PARTIAL | VERIFIED |
| Portfolio | VERIFIED | PARTIAL | PARTIAL | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED | PARTIAL | PARTIAL |
| Agentic | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| UI-API | VERIFIED | VERIFIED | VERIFIED | PARTIAL | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED |

`Overall Evidence Status` describes the **health of the current domain against its own stated purpose**,
not its readiness for the Trading Cockpit. Cockpit readiness is in `trading-cockpit-gap-matrix.md`, where
no work package is `FULL` outside Phase 0. `PARTIAL` at domain level flags an internal inconsistency
found during the audit (duplicate tables, misplaced contracts, weakened types, low usage coverage).

---

## Quantitative inventory

| Domain | Path | Module folders | Python files | Lines | Registered features | Public exports | `test_*.py` | Usage programs | README lines | Tables |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Utils | `app/utils` | 9 | 30 | 4,239 | 9 | 43 | 28 | 20 | 943 | 0 |
| Brokers | `app/services/brokers` | 18 | 71 | 15,321 | 16 | 86 | 67 | 31 | 2,028 | 1 |
| Data | `app/services/data` | 20 | 158 | 37,638 | 18 | 266 | 119 | 43 | 2,716 | 21 |
| Indicators | `app/services/indicators` | 7 | 36 | 6,906 | 6 | 31 | 39 | 19 | 1,498 | 3 |
| Strategy | `app/services/strategy` | 13 | 74 | 11,066 | 11 | 61 | 70 | 27 | 1,487 | 11 |
| Risk | `app/services/risk` | 17 | 56 | 15,096 | 15 | 78 | 48 | 35 | 2,374 | 14 |
| Trading | `app/services/trading` | 11 | 60 | 14,111 | 9 | 72 | 57 | 30 | 1,816 | 9 |
| Simulator | `app/services/simulator` | 11 | 49 | 9,541 | 9 | 55 | 44 | 24 | 1,519 | 2 |
| Analytics | `app/services/analytics` | 7 | 35 | 8,266 | 5 | 48 | 50 | 24 | 1,492 | 6 |
| Optimization | `app/services/optimization` | 12 | 52 | 6,909 | 9 | 55 | 50 | 23 | 1,215 | 2 |
| Research | `app/services/research` | 15 | 59 | 8,863 | 13 | 78 | 48 | 30 | 1,548 | 1 |
| Portfolio | `app/services/portfolio` | 10 | 34 | 8,724 | 8 | 26 | 21 | 21 | 932 | 7 |
| Agentic | `app/agentic` | 13 | 115 | 34,716 | 22 | 96 | 50 | 37 | 1,668 | 13 |
| UI-API | `app/services/api` (+ `app/ui`) | 11 | 81 | 16,956 | 13 | 69 | 54 | 10 | 1,493 | 12 |
| **Total** | | **174** | **910** | **198,352** | **165** | **1,064** | **745** | **374** | **22,729** | **102** |

Test totals include `tests/system/` (12 files, 10 end-to-end integration workflows) and `tests/unit/`
(1 file), giving 758 `test_*.py` files repository-wide.

---

## 1. Utils — `app/utils/`

**Stated responsibility (README):** shared authentication and audit contracts, error normalization,
identity, time, serialization, redaction, settings, logging, standard responses.

**Actual implementation responsibility:** matches the stated one. No market, strategy, risk, order or
accounting rule was found in `app/utils`, which satisfies the Phase 1 exit criterion in advance.

**Module folders:** `contracts/`, `errors/`, `identity/`, `logging/`, `responses/`, `security/`,
`serialization/`, `settings/`, `time/`.

**Registered features:** `FEAT-UTIL-00` shared authentication and audit contracts · `FEAT-UTIL-01` error
mapping and exception normalization · `FEAT-UTIL-02` prefixed and deterministic identity generation ·
`FEAT-UTIL-03` aware UTC time and timestamp utilities · `FEAT-UTIL-04` canonical JSON serialization and
safe conversion · `FEAT-UTIL-05` sensitive data redaction · `FEAT-UTIL-06` precedence-ordered settings
loading · `FEAT-UTIL-07` non-blocking logging configuration · `FEAT-UTIL-08` standard operation responses.

**Public exports:** 43 functions in `app/utils/__init__.py` (`__all__` begins at line 57), including
`age_seconds`, `build_response_metadata`, `canonical_digest`, `canonical_json`, `configure_logging`,
`create_audit_event`, `get_logger`, `load_broker_provider_settings`.

**Key symbols located:**

- `app/utils/time/clocks.py:11` — `class Clock(Protocol)`. This is the only clock abstraction in the
  repository and is the correct home for the required `ClockPort`.
- `app/utils/settings/loader.py:19,67,239` — `ENVIRONMENT` handling and `_ENVIRONMENT_FIELDS`.
- `app/utils/settings/models.py:45` — `ENVIRONMENT` round-trip.

**Persistence:** none. `NOT_APPLICABLE` — Utils declares no `migrations/` package and owns no table. Note
that the plan (`TC-IMP-UTIL-12`) contemplates Utils owning transaction/outbox infrastructure, but
`AGENTS.md` explicitly assigns that to `app/services/data/persistence/` with a documented exemption. This
is an unresolved ownership question, not a gap.

**Tests and usage:** 28 `test_*.py`, 20 usage programs under `tests/utils/usage/` including
`tests/utils/usage/workflows/wf_utl_sec_shared_settings_bootstrap.py` and
`wf_utl_ter_audit_event_construction.py`.

**Consumers:** every domain. `from app.utils import logger` is the mandated logging entry point.

**Cockpit-relevant gaps:** no `ProfileRef`, `VersionRef`, `EventEnvelope`, `ValidationResult`,
`ValidationIssue`, `StateTransition`, `HealthState`, `IdempotencyKey` or `DeterministicRandomPort`. Money,
price, quantity, tick and lot primitives live in Simulator (`FEAT-SIM-04`), not Utils.

**Documentation-vs-code:** consistent. No mismatch found.

**Conclusion:** the healthiest domain relative to its purpose, and the correct home for eight of the ten
required Utils contracts. Phase 1 is predominantly `EXTEND`, with one `REFACTOR` (idempotency) and two
`CREATE`s (state-machine primitives, deterministic random).

---

## 2. Brokers — `app/services/brokers/`

**Module folders:** `adapter_runtime/`, `binance_session/`, `contracts/`, `ctrader_market_data/`,
`ctrader_mutations/`, `ctrader_session/`, `dukascopy_bars/`, `dukascopy_ticks/`, `execution_history/`,
`migrations/`, `mt5_account/`, `mt5_mutations/`, `persistence/`, `price_streams/`,
`provider_calculations/`, `registry/`, `testing/`, `yahoo_history/`.

**Registered features:** `FEAT-BRK-00` canonical provider-neutral contracts · `FEAT-BRK-01` adapter
registry and capability discovery · `FEAT-BRK-02` · `FEAT-BRK-03` cTrader account lifecycle ·
`FEAT-BRK-04` Binance lifecycle · `FEAT-BRK-05` Dukascopy tick reads · `FEAT-BRK-06` Yahoo history ·
`FEAT-BRK-07` … `FEAT-BRK-13` · `FEAT-BRK-14` deterministic fake adapter · `FEAT-BRK-15` adapter runtime.
16 features registered.

**Public contract surface (internal types, exported as functions):**

| Symbol | Location |
|---|---|
| `BrokerEnvironment` (LIVE, DEMO, TESTNET, SANDBOX) | `app/services/brokers/contracts/enums.py:18` |
| `BrokerConnectionState` | `app/services/brokers/contracts/enums.py:27` |
| `BrokerOrderBook` | `app/services/brokers/contracts/models.py:941` |
| `BrokerPosition` | `app/services/brokers/contracts/models.py:1016` |
| `BrokerOrderFilter` | `app/services/brokers/contracts/models.py:1061` |
| `BrokerPositionFilter` | `app/services/brokers/contracts/models.py:1087` |
| `BrokerOrder` | `app/services/brokers/contracts/models.py:1102` |
| `BrokerOrderRequest` | `app/services/brokers/contracts/models.py:1260` |
| `BrokerOrderCheck` | `app/services/brokers/contracts/models.py:1403` |
| `BrokerOrderResult` | `app/services/brokers/contracts/models.py:1430` |

**Adapter protocol:** `app/services/brokers/contracts/protocols.py` declares `place_order` (578),
`modify_order` (591), `cancel_order` (604), `modify_position` (618), `close_position` (631),
`replace_order` (644). Contract version `v1`, schema id `brokers.adapter.v1` (asserted in
`app/services/trading/routing/dispatcher.py`).

**Concrete write paths:** `app/services/brokers/ctrader_mutations/operations.py` (62, 86, 106, 122, 152),
`app/services/brokers/mt5_mutations/operations.py` (80, 93, 112, 127, 161), and the domain-level
functions `place_broker_order` (1343), `modify_broker_order` (1359), `cancel_broker_order` (1375),
`modify_broker_position` (1393), `close_broker_position` (1409), `replace_broker_order` (1537) in
`app/services/brokers/operations.py`.

**Safety guard:** `app/services/brokers/registry/provider_connections.py:90` —
`_require_non_production(provider, environment)` raises unless the environment is in
`_NON_PRODUCTION_ENVIRONMENTS`. Module docstring: *"Only non-production environments (demo, testnet,
sandbox) are permitted through"*. Also `registry/catalogue.py:179` notes the demo default and that
downstream Trading/Risk controls are defence in depth. Full analysis in
`trading-cockpit-safety-baseline.md`.

**Persistence:** 1 table, `broker_symbol_map` (2 indexes). This is the weakest persistence footprint of
any adapter domain and is why `TC-IMP-BRK-01` (versioned instrument/venue profiles) is a substantial
`EXTEND`.

**Tests and usage:** 67 `test_*.py`, 31 usage programs, plus `tests/brokers/unit/test_documentation_parity.py`
(README-to-code parity) and `tests/brokers/unit/test_usage_real_connection_contract.py` (real-connection
contract, non-production only).

**Consumers:** Trading (dispatcher), Data (price streams), Simulator.

**Cockpit-relevant gaps:** no `InstrumentVenueProfile`, no normalized `BrokerHealth`, no source
sequence / receive time / raw-payload reference / `UNKNOWN` state on order and position snapshots, no
primary/backup route discipline, no single reusable conformance suite.

**Conclusion:** mature adapter layer with a single stable protocol and a deterministic fake. The gap is
almost entirely *profile and health modelling*, not connectivity.

---

## 3. Data — `app/services/data/`

Largest domain: 158 Python files, 37,638 lines, 266 public exports, 21 tables, 119 test files.

**Module folders:** `_shared/`, `artifact_catalog/`, `audit/`, `contracts/`, `data_jobs/`,
`economic_calendar/`, `evidence/`, `local_datasets/`, `market_data/`, `migrations/`, `persistence/`,
`quality/`, `realtime_feeds/`, `research_sources/`, `runtime_stores/`, `sources/`, `synthetic_data/`,
`tick_derivation/`, `time_sessions/`, `transformation/`.

**Registered features:** `FEAT-DATA-01` … `FEAT-DATA-18`, covering historical retrieval, market data,
local datasets, synthetic data, tick derivation, persistence, quality, transformation, time/sessions,
source governance, economic calendar, real-time feeds, scheduling, cross-domain evidence, audit evidence,
point-in-time research sources, runtime persistence adapters, artifact catalog.

**Key symbols located:**

| Symbol | Location |
|---|---|
| `EconomicEvent` | `app/services/data/economic_calendar/events.py:29` |
| `EconomicEventStore` | `app/services/data/economic_calendar/store.py:208` |
| `MarketStreamEvent` | `app/services/data/realtime_feeds/contracts.py:369` |
| `FXConversionRequest` | `app/services/data/evidence/fx_contracts.py:57` |
| `FXRateLeg` | `app/services/data/evidence/fx_contracts.py:125` |
| `FXConversionEvidence` | `app/services/data/evidence/fx_contracts.py:194` |
| `FXRateProvider` | `app/services/data/evidence/fx_conversion.py:39` |
| `AccountStateSnapshot` | `app/services/data/evidence/account_contracts.py:199` |

**Persistence (21 tables):** `data_audit_events`, `data_backfill_checkpoints`, `data_cache`,
`data_datasets`, `data_economic_calendar_coverage`, `data_economic_event_definitions`,
`data_economic_events`, `data_feeds`, `data_fetch_log`, `data_market_sessions`, `data_partition_files`,
`data_providers`, `data_quality_events`, `data_research_observations`, `data_research_sources`,
`data_runtime_records`, `data_source_attempts`, `data_source_state`, `data_symbols`, `data_update_jobs`,
`data_verified_research_sources`.

**Shared infrastructure ownership:** `app/services/data/persistence/` is exempted from the standard
five-file CRUD layout by `AGENTS.md` because it owns shared database connection, transaction, locking,
migration-ledger, backup and recovery infrastructure for the whole application. Every other domain's
persistence delegates execution through `app.services.data`.

**Cockpit-relevant gaps:** no unified `MarketEvent`, no `MarketSnapshot`, no Data-owned
`OrderBookSnapshot` (the only order-book model is in Brokers), no dataset manifest with content hash and
point-in-time status, no deterministic replay stream with availability timestamps, no closed-bar
semantics.

**Ownership anomalies found:**

- `AccountStateSnapshot` is defined in Data but the plan assigns normalized account snapshots to Brokers.
- FX rate and conversion evidence is defined in Data, but the plan assigns `FXConversionRate` to
  Portfolio, and Simulator re-validates it in `accounting/calculations.py:133`
  (`ValidatedFXConversionEvidence`). Three domains, no authoritative owner.

**Conclusion:** the most mature domain. Point-in-time source governance (`FEAT-DATA-16`) and the economic
calendar are direct reuse assets. The gaps are cockpit *replay* semantics, not data plumbing.

---

## 4. Indicators — `app/services/indicators/`

**Module folders:** `candles/`, `core/`, `migrations/`, `momentum/`, `trend/`, `volatility/`, `volume/`.

**Concrete implementations located:** `momentum/rsi.py`, `momentum/williams_r.py`, `trend/sma.py`,
`trend/ema.py`, `trend/wma.py`, `trend/hull_ma.py`, `trend/bollinger_bands.py`, `trend/directional.py`,
`trend/zigzag.py`, plus `volatility/` and `volume/` packages.

**Registered features:** `FEAT-INDI-01` … `FEAT-INDI-06` (6).

**Public exports:** 31 functions.

**Persistence (3 tables):** `indicator_definitions`, `indicator_param_sets`,
`indicator_materializations` (5 indexes).

**Tests and usage:** 39 `test_*.py`, 19 usage programs.

**Cockpit-relevant gaps:** the mathematics exists; the cockpit layer does not. There is no
`IndicatorSnapshot` contract, no `MarketRegimeSnapshot`, no `LiquiditySnapshot`, no
`SLOW/NORMAL/FAST/EXTREME` banding, no order-flow or structure-level model, and no closed-input
enforcement rejecting incomplete bars or stale snapshots.

**Conclusion:** the plan's guidance is exactly right for this domain — *reuse the formulas, add cockpit
adapters, do not duplicate the mathematics*. Phase 4 is eight `EXTEND` rows over the existing library and
two `CREATE` rows for the snapshot contract and the closed-input guard.

---

## 5. Strategy — `app/services/strategy/`

**Module folders:** `checkpoints/`, `contracts/`, `diagnostics/`, `evaluators/`, `event/`, `intents/`,
`migrations/`, `persistence/`, `proposal_intake/`, `registry/`, `replay/`, `signals/`, `vectorized/`.

**Registered features:** `FEAT-STR-01` versioned strategy contracts · `-02` deterministic safe
diagnostics · `-03` immutable registry and configuration · `-04` canonical TradeIntent proposals · `-05`
deterministic replay manifests · `-06` bounded persisted local state · `-07` atomic vectorized evaluation
· `-08` stateful event evaluation · `-09` concrete signal execution boundary · `-10` strategy signal
library · `-11` external research proposal evaluation.

**Persistence (11 tables) — with a duplication finding:** `strategy_definitions`, `strategy_versions`,
`strategy_versions_v2`, `strategy_configs`, `strategy_configs_v2`, `strategy_checkpoints`,
`strategy_checkpoints_v2`, `strategy_mutations`, `strategy_mutations_v2`, `strategy_signals`,
`strategy_state`.

> **Finding.** Four `_v2` tables coexist with their originals in a single migration definitions module.
> The authoritative family is not determinable from the migration source alone. Phase 5 must resolve this
> before adding trade-plan persistence. Recorded in `trading-cockpit-database-ownership.md`.

**Cockpit-relevant gaps:** `TradeIntent` exists (`FEAT-STR-04`) but the required `TradePlan` adds
invalidation, exit/management plan, requested size basis and profile references. No `StrategyProfile`
with permitted instruments/sessions/regimes, no `SetupEvaluation` result enum, no operating envelope, no
`DRAFT → READY_FOR_RISK → APPROVED → RELEASED → MANAGED → CLOSED` lifecycle, no automation-mode policy,
no manual-plan path.

**Reuse asset:** `tests/system/integration/test_research_to_strategy.py` proves an end-to-end
research-to-strategy promotion path already works.

**Conclusion:** `TradeIntent` is the correct base for `TradePlan`; the naming divergence must be settled
explicitly rather than by creating a second competing model.

---

## 6. Risk — `app/services/risk/`

**Module folders:** `admission/`, `allocation/`, `approvals/`, `audit/`, `config/`, `contracts/`,
`governor/`, `kill_switch/`, `limits/`, `migrations/`, `persistence/`, `portfolio/`, `regimes/`,
`reporting/`, `scenarios/`, `sizing/`, `validity/`.

**Registered features (15):** `FEAT-RISK-01` versioned contracts and deterministic errors · `-02` risk
profiles and stable configuration · `-03` portfolio risk snapshot · `-04` position sizing recommendations
· `-05` tamper-evident risk audit (durable stable-scope kill-switch CAS/read adapter) · `-06` portfolio
and market-context limits · `-07` regime assessment and limit tightening (equal-or-stricter modifiers cap
the final requested size) · `-08` strategy operational eligibility · `-09` allocation review and budget
activation · `-10` durable approval-token lifecycle · `-11` decision reuse revalidation · `-12` risk
governor · `-13` kill-switch authority and block state · `-14` advisory scenario analysis · `-15` risk
decision summaries.

**Key symbols located:**

| Symbol | Location | Note |
|---|---|---|
| `RiskDecisionPackage` | `app/services/risk/contracts/results.py:298` | candidate for the required `RiskDecision` |
| `DecisionReuseValidationResult` | `app/services/risk/contracts/results.py:491` | one of two divergent validation-result shapes |
| `PortfolioState` | `app/services/risk/contracts/evidence.py:240` | **defined in Risk; the plan assigns it to Portfolio** |
| `ScenarioDefinition` | `app/services/risk/contracts/requests.py:486` | **advisory Risk request; the plan assigns the name to Simulator** |

**Public exports (78) include:** `check_risk_kill_switch`, `apply_kill_switch_command`,
`get_kill_switch_state`, `create_kill_switch_command`, `create_kill_switch_state`,
`append_risk_kill_switch_transition`.

**Persistence (14 declared, 7 logical):** `risk_policy_versions`, `risk_decision_snapshots`,
`risk_audit_records`, `risk_approval_tokens`, `risk_kill_switch_states`, `risk_eligibility_decisions`,
`risk_allocation_decisions` — each accompanied by a `__new` table (the SQLite table-rebuild pattern), for
14 `CREATE TABLE` statements and 20 indexes.

**Tests:** 48 `test_*.py` including `test_kill_switch.py`, `test_governor.py`, `test_evidence.py`,
`test_profiles.py`, `test_default_policies.py`, `test_public_api.py`, `test_function_facades.py`,
`test_migrations.py`; 35 usage programs; plus `tests/system/integration/test_kill_switch.py`.

**Reuse assets:** the durable kill switch with a compare-and-swap adapter and the approval-token
lifecycle are the strongest safety assets in the repository outside Agentic. The regime limit-tightening
rule (`equal-or-stricter modifiers cap the final requested size`) is already the semantic the cockpit's
effective-rule resolver needs.

**Cockpit-relevant gaps and conflicts:** no `TradingPolicyProfile` drawdown/emergency/assessment rule
groups, no stop-loss validator, no RR/expectancy gate, no drawdown state machine, no margin model, no
emergency directive, no cooldown or close-only/reduction-only permission separation, no no-trade success
state. Two canonical names (`PortfolioState`, `ScenarioDefinition`) are occupied by Risk contracts that
belong to other domains.

**Conclusion:** structurally the right authority domain with real durable safety machinery, but it is
currently holding two contracts that Phase 8 and Phase 12 need to reclaim.

---

## 7. Trading — `app/services/trading/`

**Module folders:** `actions/`, `contracts/`, `live/`, `migrations/`, `monitoring/`, `persistence/`,
`reconciliation/`, `reporting/`, `routing/`, `state/`, `validation/`.

**Registered features (9):** `FEAT-TRD-01` canonical contracts and registries · `-02` state and
deterministic projections · `-03` validation, readiness and plans · `-04` authority selection and
dispatch · `-05` reconciliation and retry guard · `-06` operational and budget evidence · `-07` live and
paper session lifecycle · `-08` route-aware public actions · `-09` immutable execution evidence.

**Key symbols located:**

| Symbol | Location |
|---|---|
| `TradingRoute` (SIM, PAPER, LIVE) | `app/services/trading/contracts/models.py:383` |
| `TradingRequest` | `app/services/trading/contracts/models.py:391` |
| `OrderIntent` | `app/services/trading/contracts/models.py:653` |
| environment literal `"demo" \| "paper" \| "sim" \| "live"` | `app/services/trading/contracts/models.py:1115` |
| `_LiveRuntimeConfig` (`allow_live_mutations` default `False`) | `app/services/trading/live/config.py:103` |
| `_evaluate_live_gate_value` (fail-fast gate sequence) | `app/services/trading/live/gates.py:71` |
| route/environment scope checks | `app/services/trading/routing/dispatcher.py:294-302` |
| sim-route isolation | `app/services/trading/routing/dispatcher.py:503` |
| `ChildRiskDecisionSource`, `ExecutionRiskDecisionSource`, `AccountStateSource` | `app/services/trading/actions/dependencies.py:109,110,62` |

**Gate sequence (verified in `live/gates.py`):** schema compatibility → session started and request
validity → `session.admission_enabled` → action policy → risk decision → kill switches → readiness →
adapter capability. Any authority read error raises `GATE_BLOCKED`.

**Persistence (9 tables):** `trading_orders`, `trading_order_transitions`, `trading_fills`,
`trading_positions`, `trading_positions__new`, `trading_events`, `trading_idempotency`,
`trading_projections`, `trading_closed_position_migration_guard` (17 indexes).

> **Finding.** `trading_positions__new` and `trading_closed_position_migration_guard` indicate an
> in-flight schema rebuild. Phase 7 must confirm the authoritative table before adding position states.

**Tests:** 57 `test_*.py`, 30 usage programs, including `tests/trading/unit/live/test_gates.py`,
`tests/trading/unit/actions/test_orders.py`, `test_positions.py`, `test_rebalance.py`,
`tests/trading/unit/state/test_projections.py`, `tests/trading/unit/validation/test_snapshots.py`.

**Cockpit-relevant gaps:** no protective-order lifecycle at all (no coverage ratio, bracket/OCO or orphan
prevention), no nine-state execution position machine, no first-class `UNKNOWN` state preserved to
reconciliation, no trade ownership, no separation of the new-exposure kill switch from cancel /
protection / reduction / closure permissions.

**Cross-domain finding:** `OrderIntent` is correctly owned here, but
`app/services/simulator/execution/engine.py:32` and `app/services/simulator/run/orchestrator.py:41` each
declare `OrderIntent = Any`, erasing the authoritative type at the Simulator boundary. This is a
duplicate-authority defect that Phase 7 or Phase 8 must remove.

**Conclusion:** the order lifecycle skeleton, idempotency reservation, gate sequence and route isolation
are real and tested. Protection and unknown-state handling are the two largest holes.

---

## 8. Simulator — `app/services/simulator/`

**Module folders:** `accounting/`, `errors/`, `execution/`, `journal/`, `migrations/`, `persistence/`,
`reporting/`, `run/`, `state/`, `timeline/`, `validation/`.

**Registered features (9):** `FEAT-SIM-01` boundary and quality validation · `-02` simulation-owned state
· `-03` canonical tick timeline · `-04` fixed-precision account math · `-05` matching and simulated state
· `-06` immutable journal and replay · `-07` official and research orchestration · `-08` domain error
taxonomy · `-09` results and canonical artifacts.

**Key symbols located:**

| Symbol | Location |
|---|---|
| `EventDrivenExecutionEngine` | `app/services/simulator/execution/engine.py:85` |
| `OrderIntent = Any` (type erasure) | `app/services/simulator/execution/engine.py:32` |
| `OrderIntent = Any` (type erasure) | `app/services/simulator/run/orchestrator.py:41` |
| `ValidatedFXConversionEvidence` | `app/services/simulator/accounting/calculations.py:133` |

**Persistence (2 tables):** `sim_sessions`, `sim_runs` (3 indexes).

**API surface already wired:** `app/services/api/routes/simulation_sessions.py` (POST create with a
mandatory idempotency header, GET `/{session_id}/frames` as a Server-Sent Events stream, resume-sequence
and replayed-response handling) and `app/services/api/routes/simulation_live.py` (create, read, step,
branch, close). Plus `app/services/api/routes/simulation.py`.

**Tests:** 44 `test_*.py`, 24 usage programs.

**Reuse assessment:** this is the **single strongest cockpit reuse asset in the repository**. A durable
simulation session with an orchestrator, a stepping and branching HTTP API, an SSE frame stream, an
immutable journal, a canonical tick timeline and fixed-precision account math already exists.

**Cockpit-relevant gaps:** everything the cockpit adds. No checklist, no assessment mode, no scenario, no
trigger engine, no emergency, no latency/queue/slippage model, no replay identity, no replay integrity
state, no recovery state machine, no alert lifecycle, no global session state machine from
`SESSION_SECURED` back to `SESSION_SECURED`. Of the 31 Phase 8 work packages, 23 are `CREATE`.

**Boundary findings:** Simulator currently holds two responsibilities the plan assigns elsewhere —
fixed-precision account math (`FEAT-SIM-04`, plan assigns unit primitives to Utils) and FX conversion
validation (plan assigns FX to Portfolio). Its `journal/` also occupies the word *journal* with a
replay-record meaning, which the Analytics player trade journal must not collide with.

---

## 9. Analytics — `app/services/analytics/`

**Module folders:** `adapters/`, `contracts/`, `dashboards/`, `metrics/`, `migrations/`, `persistence/`,
`reports/`.

**Registered features (5):** `FEAT-ANLT-01` schemas, catalogs and evidence safety · `-02` approved
upstream result mapping · `-03` internal pure analytical evidence · `-04` canonical reporting · `-05`
bounded report projection.

**Persistence (6 tables):** `analytics_equity_curves`, `analytics_metric_definitions`,
`analytics_metric_values`, `analytics_pnl_attribution`, `analytics_reports`, `analytics_trade_analysis`
(9 indexes).

**Tests:** 50 `test_*.py`, 24 usage programs.

**Cockpit-relevant gaps:** Analytics today is a **reporting and metric-evidence domain**, not a scoring
domain. There is no process-first scoring model, no critical-failure override, no trade journal, no
execution-quality analytics, no plan-adherence comparison, no behavioral analytics, no emergency-response
timing, no debrief generator, no player qualification, no leaderboard, no score reproducibility and no
no-trade scoring. Eleven of thirteen Phase 9 work packages are `CREATE`.

**Naming caution:** `ResearchScorecard` (`app/services/research/contracts/results.py:446`) measures
research edges, not player process. The Analytics `Scorecard` must not reuse it.

**Reuse assets:** `analytics_trade_analysis` and `analytics_pnl_attribution` are the right tables to
extend for execution-quality analytics; `reports/` and `dashboards/` are the right home for the debrief
generator.

---

## 10. Optimization — `app/services/optimization/`

**Module folders:** `contracts/`, `evidence/`, `execution/`, `migrations/`, `parameters/`,
`persistence/`, `public_api/`, `robustness/`, `scoring/`, `search/`, `state/`, `validation/`.

**Registered features (9):** `FEAT-OPT-01` parameter space and provenance · `-02` objectives, ranking and
overfit evidence · `-03` bounded candidate search · `-04` simulation execution boundary · `-05` Monte
Carlo and stress analysis · `-06` optimization-owned durable state · `-07` versioned results and handoffs
· `-08` time-series validation · `-09` typed optimization boundary.

**Persistence (2 tables):** `optimization_results`, `optimization_checkpoints`.

**Tests:** 50 `test_*.py`, 23 usage programs, plus `tests/system/integration/test_optimization.py`.

**Assessment:** the best-aligned domain in the whole programme. Seven of ten Phase 10 work packages are
`EXTEND` over genuinely matching behavior — versioned studies with provenance, bounded search,
walk-forward validation, multi-objective ranking with overfit evidence, robustness and multi-seed checks,
anti-leakage controls and versioned promotion handoffs all already exist.

**Blocked packages:** fill-model calibration (`TC-IMP-OPT-02`), scenario difficulty calibration
(`TC-IMP-OPT-03`) and stress-profile calibration (`TC-IMP-OPT-06`) are `DEFERRED_INTEGRATION` — there is
nothing to calibrate until Phase 8 builds the fill and scenario models.

---

## 11. Research — `app/services/research/`

**Module folders:** `artifacts/`, `contracts/`, `data/`, `features/`, `intelligence/`, `leakage/`,
`market_structure/`, `metrics/`, `migrations/`, `modeling/`, `persistence/`, `profiles/`, `seasonality/`,
`statistics/`, `studies/`.

**Registered features (13):** `FEAT-RES-01` versioned contracts and configuration · `-02` deterministic
dataset preparation · `-03` research-specific features · `-04` leakage evidence, splits and masking ·
`-05` core metric profile · `-06` seeded statistical validation · `-07` edge discovery and confirmation ·
`-08` sessions and seasonality · `-09` market structure analysis · `-10` deterministic unsupervised
insights · `-11` scorecards, snapshots and edge lab profiles · `-12` safe research artifact persistence ·
`-13` fundamental and sentiment source evidence.

**Persistence:** 1 table, `research_artifacts`. Point-in-time source evidence lives in Data
(`data_research_sources`, `data_verified_research_sources`, `data_research_observations`), which matches
the plan's boundary rule that Data owns eligible point-in-time records and Research selects bounded
evidence from them.

**Tests:** 48 `test_*.py`, 30 usage programs, plus `tests/system/integration/test_research_to_strategy.py`.

**Cockpit-relevant gaps:** no `ApprovedExpectancyProfile`, no expectancy governance state machine
(`DRAFT/UNDER_REVIEW/APPROVED/SUSPENDED/EXPIRED/REVOKED`), no exact strategy/instrument/regime/session
matching rule, no drift monitor, no stress-shock evidence, no scenario evidence.

**Consequence for Phase 6:** because expectancy does not exist anywhere, Risk must consume an
`ExpectancyEligibilityEvidencePort` that returns `NOT_ELIGIBLE` and falls back to the normal RR gate until
Phase 11. This is recorded as `DEFERRED_INTEGRATION` on `TC-IMP-RISK-07` and `TC-IMP-STRAT-08`.

---

## 12. Portfolio — `app/services/portfolio/`

**Module folders:** `allocation/`, `api/`, `construction/`, `contracts/`, `evidence/`, `migrations/`,
`orchestration/`, `persistence/`, `rebalancing/`, `state/`.

**Registered features (8):** `FEAT-PORT-01` portfolio boundary contracts · `-02` evidence and eligibility
validation · `-03` deterministic construction · `-04` portfolio persistence · `-05` version and
activation governance · `-06` drift and rebalance planning · `-07` cross-domain workflow coordination ·
`-08` public portfolio API.

**Public exports (26)** include `measure_cross_account_correlation`, `recompute_portfolio_measurement`,
`dump_portfolio_value`, `submit_portfolio_rebalance`, `rollback_portfolio`, `validate_construction_evidence`.

**Key symbol:** `PortfolioStateStore` — `app/services/portfolio/state/repository.py:25`.

**Persistence (7 tables):** `portfolio_definitions`, `portfolio_allocation_versions`,
`portfolio_construction_results`, `portfolio_rebalance_plans`, `portfolio_active_scopes`,
`portfolio_idempotency`, `portfolio_audit_outbox`.

**Tests:** 21 `test_*.py` (the lowest of any domain) and 21 usage programs, plus
`tests/system/integration/test_portfolio_activation.py` and `test_portfolio_rebalance.py`.

> ### Critical finding
>
> **The existing Portfolio domain is an allocation and rebalancing engine, not an accounting system.**
> A repository-wide symbol scan found no ledger, account, cash, posting, debit/credit, balance, equity,
> margin, buying-power, realized-P&L or unrealized-P&L model anywhere in `app/`. Every one of the seven
> Portfolio tables is an allocation concern.
>
> The Trading Cockpit's entire financial authority — specification sections 6.7, 6.8 and 8 — must be
> created. Thirteen of the seventeen Phase 12 work packages are `CREATE`, and two more are `REFACTOR`
> because the pieces that do exist are in the wrong domains:
>
> - `PortfolioState` is defined in **Risk** (`app/services/risk/contracts/evidence.py:240`).
> - FX conversion is owned by **Data** and re-validated in **Simulator**.
>
> Phase 12 is the highest-risk phase in the programme and should be scheduled with that in mind, even
> though the requested domain order places it twelfth.

**Genuine reuse assets:** capital allocation with versioning and activation governance
(`TC-IMP-PORT-13`), proven by system integration tests, and `measure_cross_account_correlation` for
`TC-IMP-PORT-09`.

---

## 13. Agentic — `app/agentic/`

**Module folders:** `agents/` (with `engineering/`, `experimentation/`, `market_analysis/`,
`market_intelligence/`, `operations/`, `portfolio_risk_advisory/`, `strategy_desk/`), `context_memory/`,
`contracts/`, `deliberation/`, `governance/`, `lifecycle/`, `migrations/`, `operations/`,
`orchestration/`, `permissions/`, `persistence/`, `public_api/`, `runtime/`.

**Registered features (22):** `FEAT-AGT-01` … `FEAT-AGT-22`, covering canonical contracts and provenance,
firm governance, Google ADK runtime, durable task and workflow orchestration, tool registry and
permissions, evidence context and governed memory, deliberation, seven research/analysis agent families,
governed code generation and sandbox, evaluation, artefact promotion, portfolio and risk advisory, trade
proposal handoff, observability and incidents, and the public agentic API.

**Permission model — the strongest safety asset in the repository:**

| Symbol | Location | Effect |
|---|---|---|
| `FORBIDDEN_TOOL_TOKENS` | `app/agentic/permissions/models.py:46` | blocks `place_order`, `cancel_order`, `close_position`, `modify_position`, `modify_order`, `clear_kill_switch`, `activate_kill_switch`, `override_mandate`, `approve_own`, `deploy`, `rotate_key`, `credential` |
| `FORBIDDEN_RECEIVER_DOMAINS` | `app/agentic/permissions/models.py:64` | blocks `brokers` / `broker` as a tool receiver |
| `SideEffectClass` | `app/agentic/permissions/models.py:66` | only `read_only`, `deterministic_compute`, `staging_write`, `proposal_submission` are representable |
| `DenyReason` | `app/agentic/permissions/models.py:70` | 17 explicit deny reasons including `environment_mismatch`, `self_approval`, `approval_replayed` |

Module docstring: *"`controlled_mutation` and `critical` classes are unrepresentable, so no broker
mutation, kill-switch clearance, or production deployment can be [performed]"* (`FR-AGENTIC-015`).
This is deny-by-construction, not deny-by-check.

**Persistence (13 tables):** `agentic_evidence_claims`, `agentic_experiment_holdout_use`,
`agentic_experiment_runs`, `agentic_experiment_specs`, `agentic_experiment_verdicts`,
`agentic_lifecycle_transitions`, `agentic_memory_records`, `agentic_operations_incidents`,
`agentic_operations_replays`, `agentic_operations_traces`, `agentic_promotion_packets`,
`agentic_workflow_checkpoints`, `agentic_workflow_runs`.

**Tests:** 50 `test_*.py`, 37 usage programs, including `tests/agentic/unit/test_permissions.py`,
`tests/agentic/unit/test_governance.py` and `tests/agentic/integration/test_tool_permissions.py`.

**Cockpit-relevant gaps:** no cockpit coaching agents (pre-market coach, risk explainer, scenario
instructor, debrief analyst, portfolio explainer), and no cockpit read tools — because none of the state
they would read exists yet. Four Phase 13 packages are `DEFERRED_INTEGRATION` behind Phase 8 and Phase 9.

**Reuse verdict:** `TC-IMP-AGT-09` (tool and response audit) is the **only `REUSE` classification among
all 229 forward work packages**. Tool request, permission decision, source records, proposed action, user
decision and result are already persisted and tested end to end.

---

## 14. UI-API — `app/services/api/` and `app/ui/`

**Backend module folders:** `alerts/`, `composition/`, `contracts/`, `health/`, `identity/`,
`middleware/`, `migrations/`, `observability/`, `persistence/`, `routes/`, `streams/`.

**Routers (19):** `agentic.py`, `auth.py`, `dashboards.py`, `data.py`, `data_stream.py`, `health.py`,
`indicators.py`, `observability.py`, `operator.py`, `optimization.py`, `portfolio.py`, `research.py`,
`risk.py`, `settings.py`, `simulation.py`, `simulation_live.py`, `simulation_sessions.py`,
`strategies.py`, `trading.py`.

**Frontend:** `app/ui/src/` with `app/` (pages, `protected-layout.tsx`, `workflow-page.tsx`,
`pages.contract.test.ts`), `clients/`, `components/{layout,widgets,workflow}/`, `context/`, `mock/`,
`store/`, `test/`, `types/`, `utils/` — 102 `.ts`/`.tsx` files. `app/ui/docs/education/` exists.

**Registered features (13):** `FEAT-API-01` boundary contracts · `-02` authentication and authorization ·
`-03` request security and context · `-04` liveness and readiness · `-05` operational telemetry and
exposition · `-06` ordered event delivery · `-07` thin HTTP boundaries · `-08` canonical application
lifecycle · `-09` typed frontend transport · `-10` frontend session and page context · `-11` workflow
presentation components · `-12` protected workflow pages · `-13` critical operational alert delivery.

**Trading command surface (`routes/trading.py`):** `GET /session` (95), `POST /orders` (120),
`DELETE /orders/{order_id}` (159), `POST /positions/{position_id}/close` (199).

**Simulation session surface (`routes/simulation_sessions.py`):** `POST ""` (132) with
`_require_idempotency` (85) enforcing an idempotency header, `GET /{session_id}/frames` (188) returning a
`StreamingResponse` of SSE frames (72), plus `_resume_sequence` (46) and `_replayed_session` (114).
`routes/simulation_live.py` adds create (111), read (140), step (158), branch (181), close (213).

**Event delivery (`streams/events.py`):** `build_stream_event` (59) with `_assert_secret_free` (41) and
`StreamValidationError` (18).

**Persistence (12 tables):** `api_accounts`, `api_approvals`, `api_auth_failures`, `api_credentials`,
`api_idempotency`, `api_permissions`, `api_role_bindings`, `api_role_permissions`, `api_roles`,
`api_sessions`, `api_settings`, `api_user_settings`.

**Tests:** 54 `test_*.py`, but only **10 usage programs** — the weakest usage coverage of any domain, and
the reason `FR Usage` is `PARTIAL` in the summary matrix.

**Cockpit-relevant gaps:** no cockpit read model, no panel architecture (market instruments, portfolio
instruments, trade controls, navigation/planning, warning/emergency), no cockpit workflow interfaces, no
emergency or recovery UX, no human-factors or accessibility model, no training, scenario browser, replay
workstation, debrief or qualification UI. Twenty-eight of thirty-five Phase 14 packages are `CREATE` and
six are `DEFERRED_INTEGRATION`.

**Reuse assets:** the simulation session API with stepping, branching and SSE; mandatory API idempotency
with a durable table; complete RBAC with protected pages; ordered, secret-safe event delivery; and a
typed Python-to-TypeScript transport.

---

## Cross-domain dependency and consumer map

```text
Utils ────────────────────────────────────────────────► every domain (logger, identity, time, canonical json, redaction, settings)

Data/persistence ─────────────────────────────────────► every persistent domain (connection, transaction, write lock, migration ledger, backup, recovery)

Brokers ──► Trading (dispatcher: adapter capability, connection environment)
        └─► Data (price streams)

Data ─────► Indicators, Strategy, Risk, Research, Simulator, UI-API
        └─► Trading (FX evidence, account snapshot, data authority id)

Indicators ► Strategy, UI-API

Strategy ─► Risk (eligibility), Trading (intents), Optimization, Simulator
        └─◄ Research (research-to-strategy promotion), Agentic (proposal intake)

Risk ─────► Trading (risk decision, kill switches, action policy)
        └─► Portfolio (allocation review, budget activation)
        └─◄ Portfolio (portfolio risk snapshot — currently defined inside Risk)

Trading ──► Brokers (paper/live routes), Simulator (sim route)
        └─► UI-API (routes/trading.py)

Simulator ► UI-API (routes/simulation*.py), Optimization (execution boundary), Analytics

Portfolio ► Risk, UI-API, Trading (rebalance actions)

Research ─► Strategy, Optimization, Agentic

Analytics ► UI-API (dashboards, reports)

Agentic ──► every domain through public function boundaries only; broker mutation is
            structurally unrepresentable (permissions/models.py:46,64,66)

UI-API ───► every domain (19 routers) ; app/ui consumes app/services/api through a typed transport
```

---

## Documentation-versus-code findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| D-1 | The plan's cross-domain contract registry assumes exported types; the repository forbids exporting classes from domain roots | `AGENTS.md` Function-Only Public API Surface; 1064 exports / 0 class-like across 14 domains | **Blocking** |
| D-2 | `AGENTS.md` places transaction/outbox infrastructure in `app/services/data/persistence/` with a documented exemption; the plan places it in Utils (`TC-IMP-UTIL-12`) | `AGENTS.md` Domain Persistence Support; `app/services/data/persistence/` | High |
| D-3 | `AGENTS.md` Decision Hygiene prohibits standalone ADR documents; the audit prompt requires `ADR-0001-...` | `AGENTS.md` section 4; audit prompt `TC-IMP-BASE-09` | Resolved by owner — see `phase-0-findings-and-decisions.md` |
| D-4 | Risk README registers `FEAT-RISK-12` while noting an *"excluded legacy step-down subsystem"* | `app/services/risk/README.md` | Medium — confirm the exclusion is still accurate before Phase 6 |
| D-5 | Research README references `FEAT-DATA-16` as a Research feature row | `app/services/research/README.md` | Low — cross-domain reference, not a duplicate registry |
| D-6 | Agentic README references `FEAT-STR-11` | `app/agentic/README.md` | Low — same pattern |
| D-7 | `docs/schema/` declares itself authoritative for the *target* schema and ships `verify_schema.py`, `compare_model_to_code.py`, `verify_persistence_sql.py`; these were not executed in Phase 0 | `docs/schema/README.md` | Medium — run them at the start of Phase 1 |
| D-8 | `docs/dev/schema/` is an empty directory | filesystem | Low |
| D-9 | `app/configs/gcp-oauth.keys.json` is tracked in git | filesystem | **Review required** — contents were not read or reproduced |

---

## Per-domain current-state conclusions

| Domain | Conclusion for the Trading Cockpit |
|---|---|
| Utils | Correct home for 8 of 10 required primitives; mostly `EXTEND`. One `REFACTOR` (three competing idempotency stores). |
| Brokers | Stable adapter protocol and deterministic fake exist. Gap is profile and health modelling, not connectivity. |
| Data | Most mature domain. Economic calendar and point-in-time source governance are direct reuse. Gap is replay semantics. |
| Indicators | Reuse the mathematics; add cockpit snapshot adapters. Do not duplicate formulas. |
| Strategy | `TradeIntent` is the right base for `TradePlan`. Resolve the `_v2` table duplication first. |
| Risk | Real durable safety machinery (kill switch, approvals, audit). Holds two contracts that Simulator and Portfolio must reclaim. |
| Trading | Order lifecycle, idempotency and route isolation are real. Protection and `UNKNOWN` handling are the holes. Remove the `OrderIntent = Any` aliases. |
| Simulator | Strongest reuse asset (durable session + stepping API + SSE + journal + timeline). Also the largest build: 23 of 31 packages are `CREATE`. |
| Analytics | Reporting domain, not a scoring domain. 11 of 13 packages are `CREATE`. |
| Optimization | Best-aligned domain. 7 of 10 are `EXTEND`; 3 are blocked behind Phase 8. |
| Research | Point-in-time evidence and promotion path exist. Expectancy governance is entirely absent and blocks Risk. |
| Portfolio | **Highest-risk phase.** No accounting system exists anywhere. 13 of 17 are `CREATE`, 2 are `REFACTOR`. |
| Agentic | Strongest safety model in the repository; reuse the permission constitution verbatim. Coaching is blocked behind Phases 8-9. |
| UI-API | Real API foundation (RBAC, idempotency, SSE, typed transport, simulation sessions). The entire cockpit surface is new: 28 `CREATE`. |
