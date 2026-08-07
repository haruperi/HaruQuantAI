# Data-Store and Persistence Ownership Inventory

**Work package:** `TC-IMP-BASE-06`
**Baseline ID:** `HQA-TC-P0-20260807T075707Z-3b039544`
**Captured (UTC):** `2026-08-07T07:57:07Z`

**No migration was applied. No database was opened or written.** Every statement below was read from
migration source definitions under `app/**/migrations/`.

---

## 1. Engines, layers and tooling

| Concern | Implementation | Evidence |
|---|---|---|
| Engine | SQLite (`STRICT` tables, `SQLITE_BUSY_TIMEOUT_SECONDS`, `PRAGMA`-style rebuild patterns) | `AGENTS.md` section 5; `app/services/data/persistence/` |
| Query layer | Hand-written SQL in migration definitions; per-domain `persistence/` CRUD packages (`create.py`, `read.py`, `update.py`, `delete.py`) | `AGENTS.md` Domain Persistence Support |
| Shared infrastructure owner | `app/services/data/persistence/` — connection, transaction, write lock, migration ledger, backup, recovery. Explicitly exempted from the five-file CRUD layout. | `AGENTS.md` Domain Persistence Support |
| Migration tooling | Code-defined manifests, not Alembic. Applied through `run_data_migrations` / `run_domain_migrations` under ledger verification, an explicit write lock and checksum validation. | `AGENTS.md` section 5 |
| Immutability rule | Applied migration steps are immutable; a step checksum mismatch blocks database access | `AGENTS.md` section 5 |
| Target-schema model | `docs/schema/` (authoritative for the *target* schema, authorises no migration) with `verify_schema.py`, `compare_model_to_code.py`, `verify_persistence_sql.py` | `docs/schema/README.md` |
| Transactions | `execute_transaction` with write-lock leases and strict busy-timeout policy | `AGENTS.md` section 5 |
| Outbox | `portfolio_audit_outbox` is the only outbox-shaped table located | `app/services/portfolio/migrations/definitions.py` |
| Object storage | Large replay/partition data referenced from `data_partition_files`; files are not in the database | `app/services/data/migrations/core.py` |

### 1.1 Migration modules and declared tables

| Domain | Migration module(s) | `CREATE TABLE` statements | Logical tables | Indexes |
|---|---|---:|---:|---:|
| Data | `core.py`, `economic_calendar.py`, `economic_event_definitions.py`, `research_sources.py`, `runtime_stores.py` | 22 | 21 | 20 |
| Risk | `definitions.py` | 14 | 7 | 20 |
| Agentic | `experiment.py`, `lifecycle.py`, `memory.py`, `operations.py`, `workflow.py`, `manifest.py` | 13 | 13 | 10 |
| UI-API | `definitions.py` | 12 | 12 | 3 |
| Strategy | `definitions.py` | 11 | 11 | 7 |
| Trading | `definitions.py` | 9 | 8 + 1 guard | 17 |
| Portfolio | `definitions.py`, `runner.py` | 7 | 7 | 4 |
| Analytics | `definitions.py` | 6 | 6 | 9 |
| Indicators | `definitions.py` | 3 | 3 | 5 |
| Optimization | `definitions.py` | 2 | 2 | 1 |
| Simulator | `definitions.py` | 2 | 2 | 3 |
| Brokers | `definitions.py` | 1 | 1 | 2 |
| Research | `definitions.py` | 1 | 1 | 2 |
| Utils | none | 0 | 0 | 0 |
| **Total** | | **103** | **94 logical** | **103** |

Data's 22nd statement is a legacy-table rebuild of `data_economic_events`
(`ALTER TABLE ... RENAME TO data_economic_events_legacy` → `CREATE TABLE data_economic_events` → copy →
`DROP TABLE ... _legacy`), which is a correct rebuild pattern, not a duplicate table.
Risk's 14 statements are 7 live tables each paired with a `__new` rebuild table.

---

## 2. Ownership inventory

| Store/Object | Type | Current Model/Path | Migration | Current Owner | Required Owner | Key/Uniqueness | Mutability | Transaction Boundary | Retention | Consumers | Collision/Gap | Future Action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `broker_symbol_map` | table | `app/services/brokers/registry/` | `brokers/migrations/definitions.py` | Brokers | Brokers | PK `map_id`; UQ (`provider_code`,`provider_symbol`,`effective_from`), (`provider_code`,`symbol_id`,`effective_from`) | effective-dated append | domain CRUD | not declared | Trading, Data | No instrument/venue profile table exists | EXTEND (`TC-IMP-BRK-01`) |
| `data_symbols` | table | `app/services/data/` | `data/migrations/core.py` | Data | Brokers (per plan, instrument identity) | PK `symbol_id` | mutable | domain CRUD | not declared | all | Symbol identity split between `data_symbols` and `broker_symbol_map` | REFACTOR decision required |
| `data_providers` | table | `app/services/data/sources/` | `core.py` | Data | Data | PK `provider_id` | mutable | domain CRUD | not declared | Data | none | REUSE |
| `data_feeds` | table | `app/services/data/realtime_feeds/` | `core.py` | Data | Data | PK `feed_id` (24 cols) | mutable | domain CRUD | not declared | Data, UI-API | none | EXTEND (`TC-IMP-DATA-01`) |
| `data_datasets` | table | `app/services/data/local_datasets/` | `core.py` | Data | Data | PK `dataset_id`; UQ (`dataset_kind`,`symbol_id`,`timeframe`,`provider_id`,`producer_ref`) | mutable | domain CRUD | not declared | Research, Optimization | No content hash / point-in-time status column | EXTEND (`TC-IMP-DATA-07`) |
| `data_partition_files` | table | `app/services/data/artifact_catalog/` | `core.py` | Data | Data | PK `file_id`; UQ (`dataset_id`,`relative_path`) | append | domain CRUD | not declared | Research | none | EXTEND |
| `data_market_sessions` | table | `app/services/data/time_sessions/` | `core.py` | Data | Data | PK `session_id`; UQ (`symbol_id`,`session_name`,`day_of_week`,`effective_from`) | effective-dated | domain CRUD | not declared | Risk, Simulator | No halt / auction / reopen / roll state | EXTEND (`TC-IMP-DATA-05`) |
| `data_economic_events` | table | `app/services/data/economic_calendar/store.py` | `economic_calendar.py` (rebuild of `core.py`) | Data | Data | PK (`provider`,`provider_event_id`) | rebuilt once by migration | domain CRUD | not declared | Risk, Strategy, Simulator | No original-release vs revision publication timestamps | EXTEND (`TC-IMP-DATA-04`) |
| `data_economic_event_definitions` | table | `app/services/data/economic_calendar/` | `economic_event_definitions.py` | Data | Data | PK (`provider`,`provider_definition_id`); UQ (`provider`,`source_url`) | mutable | domain CRUD | not declared | Data | none | REUSE |
| `data_economic_calendar_coverage` | table | `app/services/data/economic_calendar/` | `economic_calendar.py` | Data | Data | PK (`provider`,`range_start`,`range_end`) | mutable | domain CRUD | not declared | Data | none | REUSE |
| `data_quality_events` | table | `app/services/data/quality/` | `core.py` | Data | Data | PK `event_id` | append | domain CRUD | not declared | Data, Risk | No stale/crossed/out-of-order/clock-drift taxonomy | EXTEND (`TC-IMP-DATA-06`) |
| `data_audit_events` | table | `app/services/data/audit/` | `core.py` | Data | Data | PK `event_id` | append-only | domain CRUD | not declared | audit | none | REUSE |
| `data_cache` | table | `app/services/data/_shared/` | `core.py` | Data | Data | PK `key` | mutable/TTL | domain CRUD | TTL implied, not declared | Data | Retention policy not declared | EXTEND |
| `data_fetch_log` | table | `app/services/data/sources/` | `core.py` | Data | Data | PK `fetch_id` | append | domain CRUD | not declared | Data | none | REUSE |
| `data_source_state` | table | `app/services/data/sources/` | `core.py` | Data | Data | PK `source_id` | mutable | domain CRUD | not declared | Data | none | REUSE |
| `data_source_attempts` | table | `app/services/data/sources/` | `core.py` | Data | Data | PK (`source_id`,`timestamp_ns`) | append | domain CRUD | not declared | Data | none | REUSE |
| `data_update_jobs` | table | `app/services/data/data_jobs/` | `core.py` | Data | Data | PK `job_id` | mutable | domain CRUD | not declared | Data | none | REUSE |
| `data_backfill_checkpoints` | table | `app/services/data/data_jobs/` | `core.py` | Data | Data | PK `idempotency_key` | mutable | domain CRUD | not declared | Data | A fourth idempotency-keyed store | note for `TC-IMP-UTIL-07` |
| `data_research_sources` | table | `app/services/data/research_sources/` | `research_sources.py` | Data | Data | PK `document_id`; UQ (`source_id`,`external_id`,`normalized_hash`) (31 cols) | append | domain CRUD | not declared | Research | none | REUSE (`TC-IMP-RES-01`) |
| `data_research_observations` | table | `app/services/data/research_sources/` | `research_sources.py` | Data | Data | PK `observation_id`; UQ (`source_id`,`series_id`,`observation_period`,`content_hash`) | append | domain CRUD | not declared | Research | none | REUSE |
| `data_verified_research_sources` | table | `app/services/data/research_sources/` | `research_sources.py` | Data | Data | PK (`source_id`,`parser_version`) | mutable | domain CRUD | not declared | Research | none | REUSE |
| `data_runtime_records` | table | `app/services/data/runtime_stores/` | `runtime_stores.py` | Data | Owning domain | PK (`namespace`,`collection_name`,`record_key`); UQ (`namespace`,`collection_name`,`partition_key`,`sequence_number`) | mutable | domain CRUD | not declared | **any domain** | **AMBIGUOUS OWNERSHIP** — a generic namespaced key-value store usable by any domain (`FEAT-DATA-17`). Durable cockpit state must not land here. | Governance rule required |
| `indicator_definitions` | table | `app/services/indicators/` | `indicators/migrations/definitions.py` | Indicators | Indicators | PK `definition_id`; UQ (`indicator_code`,`version`) | versioned | domain CRUD | not declared | Strategy | none | REUSE |
| `indicator_param_sets` | table | `app/services/indicators/` | same | Indicators | Indicators | PK `param_set_id`; UQ (`definition_id`,`params_hash`) | append | domain CRUD | not declared | Strategy | none | REUSE |
| `indicator_materializations` | table | `app/services/indicators/` | same | Indicators | Indicators | PK `materialization_id`; UQ (`definition_id`,`param_set_id`,`symbol_id`,`timeframe`) | mutable | domain CRUD | not declared | Strategy, UI-API | No completeness / data-health / freshness column | EXTEND (`TC-IMP-IND-09`) |
| `strategy_definitions` | table | `app/services/strategy/registry/` | `strategy/migrations/definitions.py` | Strategy | Strategy | PK `strategy_id` | mutable | domain CRUD | not declared | Risk, Trading | none | EXTEND |
| `strategy_versions` | table | same | same | Strategy | Strategy | PK (`strategy_id`,`strategy_version`) (8 cols) | immutable | domain CRUD | not declared | — | **SUPERSEDED?** coexists with `strategy_versions_v2` | REFACTOR — confirm authority |
| `strategy_versions_v2` | table | same | same | Strategy | Strategy | PK `version_id`; UQ (`strategy_id`,`strategy_version`), (`strategy_id`,`source_hash`); FK → `strategy_definitions` (14 cols) | immutable | domain CRUD | not declared | Strategy | duplicate family | REFACTOR |
| `strategy_configs` | table | same | same | Strategy | Strategy | PK (`strategy_id`,`strategy_version`,`config_hash`) | immutable | domain CRUD | not declared | — | duplicate family | REFACTOR |
| `strategy_configs_v2` | table | same | same | Strategy | Strategy | PK `config_id`; UQ (`version_id`,`config_hash`,`runtime_profile`); FK → `strategy_versions_v2` | immutable | domain CRUD | not declared | Strategy | duplicate family | REFACTOR |
| `strategy_checkpoints` | table | `app/services/strategy/checkpoints/` | same | Strategy | Strategy | PK `checkpoint_id` (5 cols) | mutable | domain CRUD | not declared | — | duplicate family | REFACTOR |
| `strategy_checkpoints_v2` | table | same | same | Strategy | Strategy | PK `checkpoint_id`; UQ (`config_id`,`sequence`); FK → `strategy_configs_v2` | append | domain CRUD | not declared | Strategy | duplicate family | REFACTOR |
| `strategy_mutations` | table | same | same | Strategy | Strategy | PK `command_id` (3 cols) | append | domain CRUD | not declared | — | duplicate family | REFACTOR |
| `strategy_mutations_v2` | table | same | same | Strategy | Strategy | PK `command_id` (10 cols) | append | domain CRUD | not declared | Strategy | duplicate family | REFACTOR |
| `strategy_state` | table | `app/services/strategy/persistence/` | same | Strategy | Strategy | PK `config_id`; FK → `strategy_configs_v2` | mutable | domain CRUD | not declared | Strategy | none | EXTEND |
| `strategy_signals` | table | `app/services/strategy/signals/` | same | Strategy | Strategy | PK `signal_id`; UQ (`config_id`,`sequence`,`signal_name`); FK → `strategy_configs_v2` | append | domain CRUD | not declared | Trading | none | EXTEND |
| `risk_policy_versions` | table | `app/services/risk/config/` | `risk/migrations/definitions.py` | Risk | Risk | PK `config_hash` | immutable | domain CRUD | not declared | Trading, Analytics | none | EXTEND (`TC-IMP-RISK-01`) |
| `risk_decision_snapshots` | table | `app/services/risk/contracts/` | same | Risk | Risk | PK `record_id` | append | domain CRUD | not declared | Trading, Analytics | none | EXTEND (`TC-IMP-RISK-16`) |
| `risk_audit_records` | table | `app/services/risk/audit/` | same | Risk | Risk | PK `record_id` | append-only, tamper-evident | domain CRUD | not declared | audit | none | REUSE |
| `risk_approval_tokens` | table | `app/services/risk/approvals/` | same | Risk | Risk | PK `token_id` | lifecycle-mutable | domain CRUD | not declared | Trading | none | EXTEND (`TC-IMP-RISK-14`) |
| `risk_kill_switch_states` | table | `app/services/risk/kill_switch/` | same | Risk | Risk | PK `state_id`; CAS adapter | CAS-mutable | domain CRUD + CAS | durable across restart | Trading, Agentic, UI-API | No close-only/reduction-only separation, no cooldown | EXTEND (`TC-IMP-RISK-14`) |
| `risk_eligibility_decisions` | table | `app/services/risk/admission/` | same | Risk | Risk | PK `decision_id` | append | domain CRUD | not declared | Strategy | none | EXTEND |
| `risk_allocation_decisions` | table | `app/services/risk/allocation/` | same | Risk | Risk | PK `decision_id`; UQ (`portfolio_id`,`reviewed_version`) | append | domain CRUD | not declared | Portfolio | none | REUSE |
| `risk_*__new` (7 tables) | rebuild tables | same | same | Risk | Risk | mirror the live tables | transient | migration only | n/a | none | **In-flight table rebuild.** Confirm completion before Phase 6 adds columns. | Verify |
| `trading_orders` | table | `app/services/trading/state/` | `trading/migrations/definitions.py` | Trading | Trading | PK `order_id` (27 cols) | mutable | `execute_transaction` | not declared | Portfolio, Analytics | No UNKNOWN state column evidenced | EXTEND (`TC-IMP-TRD-03`) |
| `trading_order_transitions` | table | same | same | Trading | Trading | PK `transition_seq`; FK → `trading_orders` | append-only | `execute_transaction` | not declared | Analytics | Allowed-edge validation not evidenced | EXTEND (`TC-IMP-TRD-04`) |
| `trading_fills` | table | same | same | Trading | Trading | PK `fill_id`; UQ (`order_id`,`sequence`), (`broker_fill_id`); FK → `trading_orders` | append-only | `execute_transaction` | not declared | Portfolio | **Good idempotency key** (`broker_fill_id` unique) | EXTEND (`TC-IMP-TRD-06`) |
| `trading_positions` | table | same | same | Trading | Trading | PK `position_id` (20 cols) | mutable | `execute_transaction` | not declared | Portfolio, Risk | **SUPERSEDED?** coexists with `trading_positions__new` (PK `ticket`, 26 cols) | REFACTOR — confirm authority |
| `trading_positions__new` | rebuild table | same | same | Trading | Trading | PK `ticket` (26 cols) | transient | migration | n/a | none | **In-flight rebuild with a different primary key.** Blocking clarification before Phase 7. | Verify |
| `trading_closed_position_migration_guard` | guard table | same | same | Trading | Trading | 1 column, no PK | guard | migration | n/a | none | Migration guard, not a domain record | NOT_APPLICABLE (documented) |
| `trading_events` | table | `app/services/trading/monitoring/` | same | Trading | Trading | PK `event_seq`; UQ (`scope_key`,`aggregate_version`) | append-only | `execute_transaction` | not declared | Portfolio (future), Analytics | **Good event-sequence invariant.** No economic event types for ledger posting | EXTEND (`TC-IMP-TRD-11`) |
| `trading_idempotency` | table | `app/services/trading/state/` | same | Trading | Utils (per plan) | PK `idempotency_key` | mutable/TTL | `execute_transaction` | `IDEMPOTENCY_RETENTION_SECONDS` config | Trading | **One of four idempotency stores** | REFACTOR (`TC-IMP-UTIL-07`) |
| `trading_projections` | table | same | same | Trading | Trading | PK `scope_key` | rebuildable | `execute_transaction` | not declared | UI-API | Projection, not truth | EXTEND |
| `sim_runs` | table | `app/services/simulator/run/` | `simulator/migrations/definitions.py` | Simulator | Simulator | PK `request_id` (6 cols) | mutable | domain CRUD | not declared | UI-API, Optimization | none | EXTEND (`TC-IMP-SIM-23`) |
| `sim_sessions` | table | `app/services/simulator/state/` | same | Simulator | Simulator | PK `session_id`; FK → `sim_runs` (4 cols) | mutable | domain CRUD | not declared | UI-API | **Only 4 columns.** Must carry clock, scenario, replay identity, checklist, alerts, emergency state, counters, branches and secured marker. | EXTEND (`TC-IMP-SIM-23`) |
| `analytics_metric_definitions` | table | `app/services/analytics/metrics/` | `analytics/migrations/definitions.py` | Analytics | Analytics | PK `metric_id`; UQ (`metric_code`,`version`) | versioned | domain CRUD | not declared | UI-API | none | REUSE |
| `analytics_metric_values` | table | same | same | Analytics | Analytics | PK `value_id`; UQ (`metric_id`,`scope_level`,`scope_key`,`period_kind`,`period_start_utc`,`period_end_utc`) | append | domain CRUD | not declared | UI-API | none | EXTEND |
| `analytics_trade_analysis` | table | same | same | Analytics | Analytics | PK `trade_id` (27 cols) | append | domain CRUD | not declared | UI-API | Best base for execution-quality analytics | EXTEND (`TC-IMP-ANL-05`) |
| `analytics_pnl_attribution` | table | same | same | Analytics | Analytics | PK `attribution_id`; UQ (`scope_level`,`scope_key`,`period_start_utc`,`period_end_utc`,`factor`) | append | domain CRUD | not declared | UI-API | none | EXTEND |
| `analytics_equity_curves` | table | same | same | Analytics | Analytics | PK `curve_id`; UQ (`scope_level`,`scope_key`,`period_start_utc`,`period_end_utc`) | append | domain CRUD | not declared | UI-API | Equity curves exist but no ledger produces them today | EXTEND |
| `analytics_reports` | table | `app/services/analytics/reports/` | same | Analytics | Analytics | PK `report_id` | append | domain CRUD | not declared | UI-API | Correct home for debrief | EXTEND (`TC-IMP-ANL-09`) |
| `optimization_results` | table | `app/services/optimization/state/` | `optimization/migrations/definitions.py` | Optimization | Optimization | PK `search_id` | append | domain CRUD | not declared | Strategy, Research | none | EXTEND |
| `optimization_checkpoints` | table | same | same | Optimization | Optimization | PK `search_id` | mutable | domain CRUD | not declared | Optimization | none | REUSE |
| `research_artifacts` | table | `app/services/research/artifacts/` | `research/migrations/definitions.py` | Research | Research | PK `relative_path` | append | domain CRUD | not declared | Strategy | **PK is a filesystem path** — brittle business key for expectancy governance | EXTEND (`TC-IMP-RES-03`) |
| `portfolio_definitions` | table | `app/services/portfolio/` | `portfolio/migrations/definitions.py` | Portfolio | Portfolio | PK (`portfolio_id`,`portfolio_version`) | versioned | domain CRUD | not declared | Risk | none | REUSE |
| `portfolio_allocation_versions` | table | `app/services/portfolio/allocation/` | same | Portfolio | Portfolio | PK `allocation_id`; UQ (`portfolio_id`,`allocation_version`) | versioned | domain CRUD | not declared | Risk | none | REUSE (`TC-IMP-PORT-13`) |
| `portfolio_construction_results` | table | `app/services/portfolio/construction/` | same | Portfolio | Portfolio | PK `result_id` | append | domain CRUD | not declared | Risk | none | REUSE |
| `portfolio_rebalance_plans` | table | `app/services/portfolio/rebalancing/` | same | Portfolio | Portfolio | PK (`plan_id`,`plan_version`) | versioned | domain CRUD | not declared | Trading | none | REUSE |
| `portfolio_active_scopes` | table | `app/services/portfolio/state/repository.py` | same | Portfolio | Portfolio | PK (`portfolio_id`,`scope_key`) | mutable | domain CRUD | not declared | Risk | none | EXTEND (`TC-IMP-PORT-08`) |
| `portfolio_idempotency` | table | `app/services/portfolio/persistence/` | same | Portfolio | Utils (per plan) | PK `idempotency_key` | mutable/TTL | domain CRUD | not declared | Portfolio | **One of four idempotency stores** | REFACTOR (`TC-IMP-UTIL-07`) |
| `portfolio_audit_outbox` | table | same | same | Portfolio | Portfolio / Utils | PK `event_id` | append-only | domain CRUD | not declared | audit | **Only outbox in the repository.** Plan places outbox infrastructure in Utils (`TC-IMP-UTIL-12`) | REFACTOR decision required |
| `api_accounts` | table | `app/services/api/identity/` | `api/migrations/definitions.py` | UI-API | UI-API | PK `user_id` | mutable | domain CRUD | not declared | UI-API | none | EXTEND (`TC-IMP-UIAPI-06`) |
| `api_sessions` | table | same | same | UI-API | UI-API | PK `session_digest`; FK → `api_accounts` | mutable/TTL | domain CRUD | not declared | UI-API | Distinct from `sim_sessions` — do not conflate | REUSE |
| `api_credentials` | table | same | same | UI-API | UI-API | PK `reference` | mutable | domain CRUD | not declared | UI-API | Stores references, not secret values | REUSE |
| `api_idempotency` | table | same | same | UI-API | Utils (per plan) | PK `scope_key` | mutable/TTL | domain CRUD | not declared | UI-API | **One of four idempotency stores** | REFACTOR (`TC-IMP-UTIL-07`) |
| `api_approvals` | table | same | same | UI-API | UI-API | PK `approval_id` | lifecycle | domain CRUD | not declared | UI-API | Second approval store alongside `risk_approval_tokens` | Review before Phase 14 |
| `api_roles` / `api_permissions` / `api_role_permissions` / `api_role_bindings` | tables | same | same | UI-API | UI-API | PKs `role_id` / `permission_id` / (`role_id`,`permission_id`) / `binding_id`; UQ (`account_id`,`role_id`,`scope_key`); FKs into `api_accounts`, `api_roles`, `api_permissions` | mutable | domain CRUD | not declared | UI-API | No player/instructor/reviewer roles | EXTEND (`TC-IMP-UIAPI-06`) |
| `api_auth_failures` | table | same | same | UI-API | UI-API | PK `username_hash` | mutable | domain CRUD | not declared | UI-API | Stores a hash, not a username | REUSE |
| `api_settings` / `api_user_settings` | tables | `app/services/api/` | same | UI-API | UI-API | PK (`scope`,`subject_id`) / `user_id` | mutable | domain CRUD | not declared | UI-API | Correct home for UI display preferences only | REUSE |
| `agentic_*` (13 tables) | tables | `app/agentic/` | `agentic/migrations/*.py` | Agentic | Agentic | hash- or id-keyed PKs (`spec_hash`, `packet_hash`, `trace_hash`, `claim_id`, `run_id`, …) | append-dominant | domain CRUD | not declared | Agentic, audit | `agentic_lifecycle_transitions` has **no primary key** | Note for Phase 13 |

---

## 3. Durable state required by the cockpit that has no owner today

Every item below was searched for by symbol, table name and migration text. Absence is evidence-backed.

| Required durable state | Required owner | Exists today? | Nearest existing thing | Consequence |
|---|---|---|---|---|
| Order intents | Trading | **Partial** | `trading_orders`, `trading_idempotency` | Intent is not separated from order state |
| Broker events | Brokers | **No** | `trading_events` (internal, not broker-sourced) | No source cursor or dedup checkpoint table |
| Fills | Trading | **Yes** | `trading_fills` with UQ (`order_id`,`sequence`) and UQ `broker_fill_id` | Good foundation |
| Positions | Trading | **Yes, but** | `trading_positions` + `trading_positions__new` | Two competing shapes with different primary keys |
| Protective orders | Trading | **No** | none | Entire protection lifecycle absent |
| Ledger entries | Portfolio | **No** | none anywhere in `app/` | **Critical.** The cockpit's financial authority has no store. |
| Account snapshots | Brokers / Portfolio | **Partial** | `AccountStateSnapshot` model in **Data**, no table | Model in the wrong domain, no persistence |
| Portfolio state | Portfolio | **Conflicting** | `PortfolioState` model in **Risk**; `portfolio_active_scopes` table in Portfolio | Two competing definitions |
| Risk lockouts | Risk | **Yes** | `risk_kill_switch_states` (CAS, durable) | Strong; needs permission granularity and cooldown |
| Simulation clocks | Simulator | **No** | `sim_sessions` (4 columns) | No clock persisted |
| Replay identity | Simulator | **No** | Strategy replay manifests (`FEAT-STR-05`), Simulator journal (`FEAT-SIM-06`) | Split across two domains, neither is an identity record |
| Scenario state | Simulator | **No** | `ScenarioDefinition` model in **Risk** (advisory) | Name occupied by a different concept |
| Checklist state | Simulator | **No** | none | Entire concept absent |
| Alerts | Simulator | **No** | `agentic_operations_incidents` (agent incidents, different concept) | Entire concept absent |
| Scores and qualifications | Analytics | **No** | `analytics_reports`, `analytics_metric_values` | Reporting only |
| Research approvals | Research | **Partial** | `research_artifacts` (PK is a filesystem path) | Weak business key for governance |
| Idempotency records | Utils | **Four competing** | `trading_idempotency`, `portfolio_idempotency`, `api_idempotency`, `data_backfill_checkpoints` | No cross-store exactly-once guarantee |

---

## 4. Ambiguous ownership and schema collisions

| # | Issue | Evidence | Recommended future action |
|---|---|---|---|
| P-1 | **No ledger anywhere.** The cockpit's balanced double-entry ledger, accounts, cash, valuation, margin and P&L have no table, model or migration in any domain. | Repository-wide scan of 103 `CREATE TABLE` statements and all symbol definitions under `app/` | `CREATE` under Portfolio (`TC-IMP-PORT-01`). Highest-risk item in the programme. |
| P-2 | **Four idempotency stores.** `trading_idempotency`, `portfolio_idempotency`, `api_idempotency`, `data_backfill_checkpoints` are independent, with different key columns and no shared contract. | migration definitions in four domains | `REFACTOR` to one Utils-owned primitive with migrated callers (`TC-IMP-UTIL-07`). Do not add a fifth. |
| P-3 | **`data_runtime_records` is a generic cross-domain store.** A namespaced key-value table (`FEAT-DATA-17`) that any domain may write to. | `app/services/data/migrations/runtime_stores.py` | Governance rule: no cockpit durable state may be placed here. Each cockpit record needs a named, owned table. |
| P-4 | **Strategy `_v2` duplication.** Four table families exist in both original and `_v2` form in one migration module. | `app/services/strategy/migrations/definitions.py` | Confirm the authoritative family and retire the other before Phase 5. |
| P-5 | **Trading position rebuild in flight.** `trading_positions` (PK `position_id`, 20 cols) coexists with `trading_positions__new` (PK `ticket`, 26 cols) plus a migration guard table. | `app/services/trading/migrations/definitions.py` | Blocking clarification before Phase 7 adds position states. |
| P-6 | **Risk `__new` rebuild tables.** All seven Risk tables have a `__new` twin. | `app/services/risk/migrations/definitions.py` | Confirm the rebuild completed before Phase 6 adds columns. |
| P-7 | **Symbol identity split.** `data_symbols` (Data) and `broker_symbol_map` (Brokers) both hold instrument identity. | two migrations | Decide the authoritative source before `TC-IMP-BRK-01` builds `InstrumentVenueProfile`. |
| P-8 | **Outbox ownership.** `portfolio_audit_outbox` is the only outbox; the plan places outbox infrastructure in Utils. | `AGENTS.md`; `portfolio/migrations/definitions.py` | Owner decision (`TC-IMP-UTIL-12`). |
| P-9 | **Two approval stores.** `risk_approval_tokens` and `api_approvals`. | two migrations | Clarify which authorizes a cockpit action before Phase 14. |
| P-10 | **`agentic_lifecycle_transitions` has no primary key.** | `app/agentic/migrations/lifecycle.py` | Note for Phase 13; not cockpit-blocking. |
| P-11 | **`research_artifacts` primary key is a filesystem path.** | `app/services/research/migrations/definitions.py` | Unsuitable as the business key for approved expectancy profiles; Phase 11 needs a stable profile identity. |
| P-12 | **Retention and archival rules are not declared** for any of the 94 logical tables, except an implied TTL on idempotency and cache tables. | all migrations | Every cockpit table must declare retention at creation (`TC-IMP-BASE-10` rule 8). |
| P-13 | **Transaction boundaries are not documented per table.** `execute_transaction` exists and is mandated by `AGENTS.md`, but no per-table boundary declaration was found. | `AGENTS.md` section 5 | Cockpit financial tables must declare their transaction boundary explicitly. |

---

## 5. Test-database behavior

`AGENTS.md` requires SQLite handles, sockets and subprocesses to be closed explicitly in test teardown to
eliminate `ResourceWarning` leaks, and requires database calls to be mocked or isolated when a unit test
would otherwise exceed 100 ms. Per-domain `tests/*/conftest.py` files exist (for example
`tests/trading/conftest.py`). No test was found that targets a shared or production database. This was
not exhaustively proven; see `trading-cockpit-test-baseline.md` for what was and was not executed.
