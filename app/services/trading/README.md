# Trading

> **Package:** `app/services/trading/`
> **Status:** `Missing`
> **Last updated:** `2026-08-25`
> **Domain ID:** `D-TRD`
> **Specification version:** `1.2-execution-parity`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Update this document before modifying or adding code.
> Cross-domain execution ownership follows [`docs/EXECUTION_PARITY.md`](../../../docs/EXECUTION_PARITY.md): Trading owns one canonical business execution lifecycle, while Simulator supplies `SIM`/`PAPER` authority mechanics and Broker Connectivity supplies `DEMO`/`LIVE` authority transport.

---

## Code-Aligned Implementation Convention

This README is the sole current target registry for this domain's feature IDs and statuses, functional requirements, domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence, and deletion behavior. `PROJECT.md` owns system scope, cross-domain behavior, system NFRs, and release gates; `ARCHITECTURE.md` owns universal package and runtime constraints; `EXECUTION_PARITY.md` owns the unified Trading/authority relationship. Feature-local READMEs, manifests, contract definitions, migrations, and tests provide current implementation evidence without silently changing this target registry.

Implementation uses the repository's existing feature substrate: each feature lives directly at `app/services/<domain>/<feature>/`, is discovered through the `haruquantai.features` Python entry-point group, and declares one immutable `FeatureSpec` in `manifest.py`. There are no domain or feature YAML manifests.

Every implemented feature also contains a mandatory runtime-validated `README.md`, pure `__init__.py`, strict `config.py`, lifecycle `feature.py`, and focused implementation modules. Dependencies and effects flow through `FeatureContext`/`FeatureScope`; cross-feature implementation imports are forbidden. Persistent state is declared by `FeatureSpec.state`; any migrations and storage adapters remain with the owning feature. Capability keys use `<domain>.<name>@<major>`. FR IDs remain product, acceptance, and test-trace identities rather than one runtime registration per FR. A requirement `Depends` cell expresses product sequencing, traceability, or acceptance evidence only; runtime dependencies are declared separately with exact keys in `FeatureSpec.requires` or `FeatureSpec.optional`.

Feature-level automated tests live at `tests/services/trading/<feature>/`. Usage examples never live under `tests/`; they belong to each feature's designated primary domain-logic module. Broader automated verification retains its documented architecture, composition, API, integration, or system test location. The code-backed procedure is the [Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md).

## 1. Purpose and Boundary

### Purpose

Trading converts an exact Strategy intent or authorized manual plan into one governed execution lifecycle shared by `SIM`, `PAPER`, `DEMO`, and `LIVE`. It owns session/context mode, authority selection, readiness, canonical operation/order/deal/position state, dispatch state, authority correlation, reconciliation, protective-order ownership, immutable execution evidence, and account projections. Every executable mutation passes Runtime Risk. Route selection changes authority mechanics and explicit safety gates; it does not select a different business trading state machine.

`SIM` and `PAPER` use versioned Simulator execution-authority capabilities. `DEMO` and `LIVE` use versioned Broker Connectivity authority capabilities. No Simulator engine object, broker SDK object, or provider credential crosses the Trading boundary.

### Owns

- Explicit `SIM`, `PAPER`, `DEMO`, and `LIVE` execution context/mode semantics; no live default or implicit promotion.
- Canonical application order, deal/fill acceptance, position projection, operation, and lifecycle state machines for every route.
- Trade plans, manual-order identity, readiness, common business/risk gate sequencing, and preflight orchestration.
- Selection of Simulator versus Broker execution authority and the exact route/profile.
- Idempotent dispatch, unknown-outcome handling, retry guard, and authority correlation.
- Reconciliation of orders, deals, positions, account state, and in-flight operations from route-specific authority evidence.
- Protective-order lifecycle, ownership, modification, and recovery across every route.
- Immutable execution journal, causal Trading events, provenance, and transaction-ledger semantics.
- Account/valuation projections used by operational and simulation contexts where the selected profile requires them.
- A stable execution-authority port that can be implemented by Simulator or Broker Connectivity without Trading importing either implementation.

### Does not own

- Strategy authoring, validation, or signal generation; Strategy owns them.
- Risk decisions, sizing authority, budgets, approval tokens, capacity, or kill switch; Runtime Risk owns them.
- Simulator scheduler time, historical replay, intrabar path, matching, fill-price mechanics, simulated spread/slippage/commission/swap models, or deterministic simulation result orchestration; Simulator owns those authority mechanics.
- Provider connections, permissions, credentials, SDK transport, or provider-truth decoding; Broker Connectivity owns them.
- Instrument identity, sessions/calendars, trading rules, costs, or currency topology; Catalogue owns them.
- Market/account/FX/news evidence normalization; Data and Broker Connectivity own source evidence.
- Derived result/operational-journal analysis and qualification projections; Analytics owns them, while Trading retains canonical execution evidence.
- Research portfolio construction; Portfolio owns it.
- Custody, deposits, withdrawals, tax accounting, or copy trading.

### Unified execution invariant

```text
Strategy intent / authorized manual action
                -> Runtime Risk
                -> Trading
                -> selected execution authority
                   |-- SIM/PAPER -> Simulator
                   `-- DEMO/LIVE -> Broker Connectivity
                -> canonical Trading receipt/order/deal/position evidence
```

A route may add explicit authority-specific safety gates (for example deterministic scheduler readiness or live-credential authorization), but `SIM` may not bypass a business/risk gate merely because it is simulated.

### Dependency and removability invariant

Trading is implemented before Simulator and therefore must not require the concrete Simulator package to activate.

- Trading defines/consumes the versioned execution-authority contract and proves `SIM`/`PAPER` behavior with deterministic conformance authorities.
- Simulator later registers the real `SIM`/`PAPER` provider.
- Removing Simulator withdraws Simulator-backed routes only; Broker-backed routes remain healthy if their own dependencies are present.
- Removing Broker Connectivity withdraws `DEMO`/`LIVE` only; Simulator-backed routes remain healthy.
- No cross-domain implementation import is permitted in either direction.

### Shared Contracts

Trading semantically owns its public session/context, plan, operation, canonical order/deal/position, protection, journal, ledger, reconciliation, and action contracts, but their sole physical definitions live in `app/contracts/trading/` and wire schemas in `app/contracts/trading/wire/`. `app/services/trading/` contains implementations only and shall not define or re-export substitute public contract types. Consumed contract types are imported from their corresponding `app/contracts/<owner>/` namespace. Feature IDs and FR IDs are documentation, lifecycle, acceptance, and traceability identities; runtime consumption uses exact versioned capability keys declared by contracts and `FeatureSpec`. The exact public records and capability bundles are listed in the [Shared Contracts README](../../contracts/README.md#414-appcontractstrading).

The previously ratified planning records are reconciled in place before feature implementation: `SIM` is added to the route/mode authority vocabulary and the Simulator capability reference represents both `SIM` and `PAPER`. No released product consumer exists yet, so this is a pre-implementation v1 contract correction rather than a runtime compatibility migration.

#### Ratified v1 public records (28)

Table anchors: `trading_sessions(session_id UNIQUE)`, `trading_session_events(session_id,sequence UNIQUE)`, `trading_operations(operation_id UNIQUE,idempotency_scope,idempotency_key UNIQUE)`, `trading_operation_events(operation_id,sequence UNIQUE)`, `trading_orders(session_id,authority_order_id UNIQUE)`, `trading_deals(session_id,authority_deal_id UNIQUE)`, `trading_position_projections(session_id,position_identity UNIQUE)`, `trading_protection_sets(owner_identity,version UNIQUE)`, `trading_journal_records(session_id,sequence UNIQUE,record_hash UNIQUE)`, `operational_accounts(session_id,account_ref UNIQUE)`, `operational_ledger_entries(account_id,sequence UNIQUE,record_hash UNIQUE)`, `operational_valuations(account_id,as_of,valuation_version UNIQUE)`, `trading_reconciliation_runs(session_id,run_sequence UNIQUE)`, `trading_reconciliation_findings(run_id,finding_key UNIQUE)`.

| # | Record | Exact wire fields | FRs / rules |
|---|---|---|---|
| R1 | `TradingMode` | `mode: Literal[SIM,PAPER,DEMO,LIVE]`; `schema_version: Literal[1] = 1`. Explicit per execution session/context; no live default or implicit promotion; missing/mismatched mode blocks start and dispatch. | FR-TRD-DEFINE_TRADING_MODES. |
| R2 | `TradingSessionRef` | `session_id: Uuid7`; `mode: Literal[SIM,PAPER,DEMO,LIVE]`; `schema_version: Literal[1] = 1`. A deterministic SIM run may bind a run-scoped Trading session/context; forward PAPER/DEMO/LIVE sessions retain durable operational identity. | FR-TRD-BIND_TRADING_SESSION. |
| R3 | `TradingSession` | `session_id: Uuid7`; `mode: TradingMode`; `account_authority_ref: nonempty str`; `route_profile_version: int >= 1`; `capability_snapshot_id: Uuid7`; `risk_profile_id: Uuid7`; `opening_state: JsonObject | None = None` (SIM/PAPER opening authority state/data binding where applicable); `created_at: UtcTimestamp`; `started_at: UtcTimestamp | None = None`; `stopped_at: UtcTimestamp | None = None`; `archived_at: UtcTimestamp | None = None`; `generation: int >= 1`; `schema_version: Literal[1] = 1`. Uniqueness `(session_ref,generation)`; deterministic SIM timestamps/time semantics are supplied by the injected simulation time authority. | FR-TRD-BIND_TRADING_SESSION, DEFINE_SESSION_STATES. |
| R4 | `TradingSessionState` | `session_id: Uuid7`; `state: Literal[CREATED,STARTING,ACTIVE,DEGRADED,STOPPING,STOPPED,ARCHIVED]`; `generation: int >= 1`; `changed_at: UtcTimestamp`; `causal_event_id: Uuid7 | None = None`; `schema_version: Literal[1] = 1`. Illegal transitions have no side effect; recovery fences old generations and reconciles before `ACTIVE`; unresolved drift stays `DEGRADED`. | FR-TRD-DEFINE_SESSION_STATES, RECOVER_TRADING_SESSION. |
| R5 | `TradingOperationRef` | `operation_id: Uuid7`; `session_id: Uuid7`; `idempotency_scope: nonempty str`; `idempotency_key: nonempty str`; `schema_version: Literal[1] = 1`. Dispatch at most once per logical identity. | FR-TRD-DEFINE_LOGICAL_OPERATION, DISPATCH_ONCE. |
| R6 | `TradingOperation` | `operation_id: Uuid7`; `session_id: Uuid7`; `idempotency_scope: nonempty str`; `idempotency_key: nonempty str`; `action: Literal[CREATE,SUBMIT,CANCEL,MODIFY,CLOSE,FLATTEN,HOLD,PROTECTION]`; `plan_hash: ContentHash`; `risk_decision_id: Uuid7 | None`; `risk_reservation_id: Uuid7 | None`; `authority_route: nonempty str`; `state: TradingOperationState`; `provider_correlation_id: Uuid7 | None`; `simulator_correlation_id: Uuid7 | None`; `event_ids: tuple[Uuid7, ...] = ()`; `schema_version: Literal[1] = 1`. No operation changes identity mid-flight; the correlation field used depends only on the selected authority family. | FR-TRD-DEFINE_LOGICAL_OPERATION. |
| R7 | `TradingOperationState` | `operation_id: Uuid7`; `state: Literal[PLANNED,ADMITTED,DISPATCHING,ACCEPTED,REJECTED,UNKNOWN,RECONCILING,PARTIALLY_FILLED,FILLED,CANCELLED,CLOSED,FAILED]`; `changed_at: UtcTimestamp`; `schema_version: Literal[1] = 1`. Unknown authority outcomes enter `UNKNOWN`→`RECONCILING`; only reconciled authority evidence establishes fills/final state. | FR-TRD-DEFINE_OPERATION_STATES, CLASSIFY_DISPATCH_RECEIPTS. |
| R8 | `TradeIntentRef` | `intent_id: Uuid7`; `origin: Literal[STRATEGY_INTENT,MANUAL_ORDER]`; `strategy_version_id: Uuid7 | None`; `intent_hash: ContentHash`; `schema_version: Literal[1] = 1`. Manual actions carry authenticated principal, reason, source interface, request/correlation IDs, explicit discretionary identity; they cannot masquerade as Strategy signals. | FR-TRD-BIND_TRADE_PLAN, IDENTIFY_MANUAL_ACTIONS. |
| R9 | `TradePlan` | `plan_id: Uuid7`; `intent: TradeIntentRef`; `instrument: InstrumentRef`; `side: Literal[BUY,SELL]`; `order_type: Literal[MARKET,STOP,LIMIT,STOP_LIMIT]`; `quantity_method: JsonObject`; `entry: JsonObject`; `protection: ProtectionSet | None`; `time_in_force: Literal[GTC,DAY,IOC,FOK]`; `route: nonempty str`; `session_id: Uuid7`; `evidence_version_ids: tuple[Uuid7, ...] = ()`; `content_hash: ContentHash`; `schema_version: Literal[1] = 1`. Route is explicit and must match the bound `SIM|PAPER|DEMO|LIVE` context; ambiguity rejects. | FR-TRD-BIND_TRADE_PLAN, NORMALIZE_TRADE_PLAN. |
| R10 | `TradingReadiness` | `session: TradingSessionRef`; `is_session_active: bool`; `selected_authority: ExecutionAuthorityRef | None`; `authority_capability_ready: bool`; `instrument_mapping_valid: bool`; `market_session_state: Literal[OPEN,CLOSED,UNKNOWN]`; `evidence_fresh: bool`; `route_profile_compatible: bool`; `account_permission_granted: bool`; `risk_admissible: bool`; `assessed_at: UtcTimestamp`; `blocking_reasons: tuple[nonempty str, ...] = ()`; `schema_version: Literal[1] = 1`. Route-specific safety fields may be not-applicable only when the profile explicitly says so; business/risk readiness semantics remain paired. | FR-TRD-VALIDATE_TRADING_READINESS. |
| R11 | `ExecutionAuthorityRef` | `authority_id: Uuid7`; `kind: Literal[SIM,PAPER,DEMO,LIVE]`; `simulator_capability: CapabilityIdentifier | None` (`SIM`/`PAPER` use a registered Simulator execution-authority capability with pinned semantic profile); `broker_session_id: Uuid7 | None` (`DEMO`/`LIVE` exact Broker session environment); `generation: int >= 1`; `schema_version: Literal[1] = 1`. Exactly one authority family is valid for the selected kind; cross-authority/cross-environment requests reject. | FR-TRD-SELECT_EXECUTION_AUTHORITY, OBTAIN_RISK_AUTHORITY, RECHECK_DISPATCH_AUTHORITY. |
| R12 | `DispatchEvidence` | `evidence_id: Uuid7`; `operation_id: Uuid7`; `request_hash: ContentHash`; `staged_at: UtcTimestamp`; `authority_generation: int >= 1`; `recheck_passed: Literal[True]`; `schema_version: Literal[1] = 1`. Pre-dispatch record + immutable request hash commit before any authority side effect; staging failure causes no dispatch. | FR-TRD-STAGE_DISPATCH_EVIDENCE, RECHECK_DISPATCH_AUTHORITY. |
| R13 | `DispatchReceipt` | `receipt_id: Uuid7`; `operation_id: Uuid7`; `outcome: Literal[ACCEPTED,REJECTED,UNKNOWN]`; `authority_request_id: nonempty str | None`; `authority_receipt_id: nonempty str | None`; `provider_evidence: JsonObject`; `received_at: UtcTimestamp`; `schema_version: Literal[1] = 1`. Concurrent/repeated requests never create a duplicate logical order; blind retry disabled on `UNKNOWN` until reconciliation proves no authority operation or a new separately authorized action exists. Same semantic shape across Simulator/Broker authorities. | FR-TRD-DISPATCH_ONCE, CLASSIFY_DISPATCH_RECEIPTS, BLOCK_BLIND_RETRY. |
| R14 | `TradingOrder` | `order_id: Uuid7`; `session_id: Uuid7`; `operation_id: Uuid7`; `authority_order_id: nonempty str`; `instrument: InstrumentRef`; `side: Literal[BUY,SELL]`; `order_type: Literal[MARKET,STOP,LIMIT,STOP_LIMIT]`; `requested_quantity: DecimalValue > 0`; `filled_quantity: DecimalValue >= 0 = "0"`; `state: Literal[CREATED,ACCEPTED,REJECTED,PENDING,PARTIALLY_FILLED,FILLED,CANCELLED,EXPIRED]`; `schema_version: Literal[1] = 1`. Canonical application order for all routes; Simulator authority orders are evidence inputs, not competing application orders. Uniqueness `(session_id,authority_order_id)`. | FR-TRD-CLASSIFY_DISPATCH_RECEIPTS, TRUST_EXECUTION_DEALS. |
| R15 | `TradingDeal` | `deal_id: Uuid7`; `session_id: Uuid7`; `order_id: Uuid7`; `authority_deal_id: nonempty str`; `timestamp: UtcTimestamp`; `side: Literal[BUY,SELL]`; `quantity: DecimalValue > 0`; `price: DecimalValue`; `fee: Money | None`; `financing: Money | None`; `realized_pl: Money | None`; `schema_version: Literal[1] = 1`. Authority fills/deals become canonical accepted execution evidence only through Trading; uniqueness `(session_id,authority_deal_id)`. | FR-TRD-TRUST_EXECUTION_DEALS. |
| R16 | `TradingPositionProjection` | `position_id: Uuid7`; `session_id: Uuid7`; `position_identity: nonempty str`; `instrument: InstrumentRef`; `direction: Literal[LONG,SHORT]`; `quantity: DecimalValue`; `avg_price: DecimalValue | None`; `realized_pl: Money`; `unrealized_pl: Money | None`; `as_of: UtcTimestamp`; `authority_source: Literal[DEAL_DERIVED,SNAPSHOT]`; `schema_version: Literal[1] = 1`. Canonical application projection across all routes; Simulator/Broker snapshots are current-state evidence, never a replacement for transaction history. | FR-TRD-TRUST_EXECUTION_DEALS, RECONCILE_TRADING_STATE. |
| R17 | `ReconciliationRequest` | `request_id: Uuid7`; `session_id: Uuid7`; `time_window: SeriesInterval`; `event_cursor: str | None`; `scope: Literal[ORDERS,DEALS,POSITIONS,ACCOUNT,EVENTS,ALL] = "ALL"`; `schema_version: Literal[1] = 1`. Compares local operations/projections with bounded selected-authority state; missing pages/event gaps block clean completion. | FR-TRD-RECONCILE_TRADING_STATE. |
| R18 | `ReconciliationFinding` | `finding_id: Uuid7`; `run_id: Uuid7`; `finding_key: nonempty str`; `kind: Literal[MISSING_ORDER,MISSING_DEAL,MISSING_POSITION,QUANTITY_MISMATCH,PRICE_MISMATCH,STATE_MISMATCH,EVENT_GAP,PAGE_MISSING,DUPLICATE,CORPORATE_ACTION_UNMATCHED,PROTECTION_MISSING,PROTECTION_ORPHANED,PROTECTION_STALE,PROTECTION_DUPLICATED]`; `severity: Literal[INFO,WARNING,CRITICAL]`; `evidence_refs: tuple[Uuid7, ...] = ()`; `resolution_policy: Literal[AUTO,MANUAL]`; `transition_history: tuple[JsonObject, ...] = ()`; `schema_version: Literal[1] = 1`. Destructive repair requires explicit authorization where applicable; append-only history. | FR-TRD-RECORD_RECONCILIATION_FINDINGS, RECOVER_PROTECTIVE_ORDERS. |
| R19 | `ProtectionSet` | `owner_identity: nonempty str` (exact entry/order/position identity); `version: int >= 1`; `owner_kind: Literal[STRATEGY,MANUAL,ATM]`; `protections: tuple[ProtectionSpec, ...] = ()` where `ProtectionSpec(kind: Literal[STOP,TARGET,TRAILING,BREAKEVEN,PARTIAL_EXIT], quantity_scope: DecimalValue > 0, parameters: JsonObject)`; `plan_version: int >= 1`; `content_hash: ContentHash`; `schema_version: Literal[1] = 1`. Protections bind exact owner across all routes; protected quantity never exceeds residual canonical quantity. | FR-TRD-OWN_PROTECTIVE_ORDERS, ALLOCATE_PROTECTED_QUANTITY. |
| R20 | `ProtectionChange` | `change_id: Uuid7`; `protection_set: ProtectionSet`; `change: Literal[INSTALL,MODIFY,CANCEL]`; `risk_validation_id: Uuid7`; `authority_rules_applied: JsonObject`; `is_risk_worsening: bool`; `explicit_exception_id: Uuid7 | None = None`; `changed_at: UtcTimestamp`; `schema_version: Literal[1] = 1`. Risk-worsening changes block unless an explicit exception authorizes them. | FR-TRD-VALIDATE_PROTECTION_CHANGES. |
| R21 | `TradingJournalRecord` | `record_id: Uuid7`; `session_id: Uuid7`; `sequence: int >= 1` (monotonic session sequence); `record_hash: ContentHash`; `event_kind: Literal[PLAN,VALIDATION,RISK_CHECK,RESERVATION,DISPATCH,RECEIPT,ORDER_CHANGE,DEAL,POSITION_CHANGE,RECONCILIATION,PROTECTION,RETRY,CLOSURE]`; `contract_versions: JsonObject`; `request_hash: ContentHash | None`; `response_hash: ContentHash | None`; `evidence_refs: tuple[Uuid7, ...] = ()`; `authority_generation: int >= 1`; `operator_or_strategy_identity: nonempty str`; `occurred_at: UtcTimestamp`; `failure_detail_redacted: str = ""`; `schema_version: Literal[1] = 1`. First-divergence reconstruction possible for SIM as well as operational routes; secrets never appear. | FR-TRD-JOURNAL_TRADING_EVENTS, PIN_EXECUTION_PROVENANCE. |
| R22 | `ExecutionProvenance` | `provenance_id: Uuid7`; `journal_record_id: Uuid7`; `profile_versions: JsonObject`; `evidence_refs: tuple[Uuid7, ...] = ()`; `export_bounds: JsonObject`; `schema_version: Literal[1] = 1`. Bounded canonical verifiable export reproducing record hashes; no credentials or unrestricted authority payloads. | FR-TRD-PIN_EXECUTION_PROVENANCE, EXPORT_EXECUTION_EVIDENCE. |
| R23 | `OperationalAccount` | `account_id: Uuid7`; `session_id: Uuid7`; `account_ref: nonempty str`; `currency: CurrencyCode`; `cash: Money`; `balances: dict[CurrencyCode, DecimalValue] = {}`; `open_positions: tuple[Uuid7, ...] = ()`; `pending_obligations: JsonObject = {}`; `realized_pl: Money`; `unrealized_pl: Money | None`; `fees: Money`; `financing: Money`; `equity: Money | None`; `margin: Money | None`; `free_margin: Money | None`; `buying_power: Money | None`; `risk_health_at: UtcTimestamp | None`; `as_of: UtcTimestamp`; `schema_version: Literal[1] = 1`. Projected from reconciled canonical deals/events only; SIM/PAPER may bind deterministic simulated authority state. | FR-TRD-PROJECT_OPERATIONAL_ACCOUNTS. |
| R24 | `OperationalLedgerEntry` | `entry_id: Uuid7`; `account_id: Uuid7`; `sequence: int >= 1`; `record_hash: ContentHash`; `entry_kind: Literal[CASH,ASSET_POSITION,FEE,FINANCING_SWAP,REALIZED_PL,ADJUSTMENT]`; `debit: DecimalValue >= 0`; `credit: DecimalValue >= 0`; `currency: CurrencyCode`; `source_deal_id: Uuid7 | None`; `source_event_id: Uuid7 | None`; `effective_at: UtcTimestamp`; `recorded_at: UtcTimestamp`; `posted_at: UtcTimestamp`; `reversal_of: Uuid7 | None`; `schema_version: Literal[1] = 1`. Signed balanced entries; every journalized transaction balances; direct edit/delete of history prohibited. | FR-TRD-BALANCE_TRANSACTION_LEDGER, POST_ACCOUNT_ADJUSTMENTS. |
| R25 | `OperationalValuation` | `valuation_id: Uuid7`; `account_id: Uuid7`; `as_of: UtcTimestamp`; `valuation_version: int >= 1`; `mark_source: nonempty str`; `mark_time: UtcTimestamp`; `fx_graph_version: nonempty str`; `contract_sizes: JsonObject`; `currencies: tuple[CurrencyCode, ...] = ()`; `rounding: Literal[DOWN,UP,HALF_UP,HALF_EVEN,TOWARD_ZERO]`; `missing_price_policy: nonempty str`; `values: JsonObject`; `stale_mandatory_marks: tuple[nonempty str, ...] = ()`; `schema_version: Literal[1] = 1`. No value/P/L/margin/buying power is derived from a stale/missing mandatory mark. | FR-TRD-VALUE_OPERATIONAL_ACCOUNTS. |
| R26 | `PublicTradingAction` | `action_id: Uuid7`; `action: Literal[CREATE,SUBMIT,CANCEL,MODIFY,CLOSE,FLATTEN,HOLD,PROTECTION]`; `contract_version: Literal[1] = 1`; `session: TradingSessionRef`; `payload: JsonObject` (mode-neutral plan/protection/selection payload); `pinned_selection_token_id: Uuid7 | None = None`; `impact_preview_id: Uuid7 | None = None`; `conflict_policy: Literal[REJECT,KEEP_EXISTING,CREATE_NEW_VERSION] | None = None`; `approval_token_id: Uuid7 | None = None`; `idempotency_key: nonempty str`; `per_target_outcomes: tuple[Uuid7, ...] = ()`; `schema_version: Literal[1] = 1`. One versioned route-neutral contract delegated to the exact session/context owner; no caller selects a private adapter; scope cannot broaden between preview and commit. | FR-TRD-ROUTE_PUBLIC_ACTIONS, GOVERN_BULK_ACTIONS. |
| R27 | `TradingStateQuery` | `query_id: Uuid7`; `session_id: Uuid7 | None`; `projection: Literal[SESSIONS,OPERATIONS,ORDERS,DEALS,POSITIONS,PROTECTIONS,ACCOUNTS,LEDGER,RECONCILIATION]`; `cursor: str | None`; `page_size: int 1..500 = 100`; `filters: tuple[FilterSpec, ...] = ()`; `schema_version: Literal[1] = 1`. Bounded projections carry authority/freshness state; stale or unresolved projections are visibly marked. | FR-TRD-QUERY_TRADING_STATE. |
| R28 | `TradingEvent` | `DomainEvent` envelope with `event_type: "trading.event"`; payload `session_id: Uuid7`, `sequence: int >= 1`, `kind: Literal[PLAN,VALIDATION,RISK_CHECK,RESERVATION,DISPATCH,RECEIPT,ORDER_CHANGE,DEAL,POSITION_CHANGE,RECONCILIATION,PROTECTION,RETRY,CLOSURE]`, `operation_id: Uuid7 | None = None`, `values: JsonObject`, `schema_version: Literal[1] = 1`. Ordered with replay/resync; stable links among plan/decision/reservation/operation/order/deal/position/protection/ledger/reconciliation records. | FR-TRD-JOURNAL_TRADING_EVENTS, STREAM_TRADING_EVENTS (Interfaces). |

#### Ratified v1 capabilities and operation envelopes

All new (universal rule; shared `TradingFailure` with `code: Literal[TRADING_VALIDATION_FAILED,TRADING_MODE_MISMATCH,TRADING_SESSION_NOT_ACTIVE,TRADING_STATE_CONFLICT,TRADING_AUTHORITY_MISMATCH,TRADING_RISK_AUTHORITY_INVALID,TRADING_IDEMPOTENCY_CONFLICT,TRADING_PROTECTION_INVALID,TRADING_QUERY_INVALID,CAPABILITY_UNAVAILABLE]`; no subscriptions — the event stream is consumed through `interfaces.operate-trading@1`):

1. `trading.manage-trading-sessions@1` / `ManageTradingSessionsCapability` / `manage_trading_sessions` — ops `CREATE, START, STOP, ARCHIVE, RECOVER`. Success: `session: TradingSession | None`; `state: TradingSessionState | None`. FRs: DEFINE_TRADING_MODES, BIND_TRADING_SESSION, DEFINE_SESSION_STATES, RECOVER_TRADING_SESSION.
2. `trading.validate-trade-plans@1` / `ValidateTradePlansCapability` / `validate_trade_plans` — ops `BIND_INTENT, BIND_PLAN, VALIDATE_READINESS, NORMALIZE`. Success: `intent: TradeIntentRef | None`; `plan: TradePlan | None`; `readiness: TradingReadiness | None`. FRs: BIND_TRADE_PLAN, IDENTIFY_MANUAL_ACTIONS, VALIDATE_TRADING_READINESS, NORMALIZE_TRADE_PLAN.
3. `trading.account-operations@1` / `AccountOperationsCapability` / `account_operations` — ops `PROJECT_ACCOUNT, VALUE, POST_ADJUSTMENT`. Success: `account: OperationalAccount | None`; `valuation: OperationalValuation | None`; `ledger_entry: OperationalLedgerEntry | None`. FRs: PROJECT_OPERATIONAL_ACCOUNTS, VALUE_OPERATIONAL_ACCOUNTS, POST_ACCOUNT_ADJUSTMENTS.
4. `trading.dispatch-orders@1` / `DispatchOrdersCapability` / `dispatch_orders` — ops `OBTAIN_AUTHORITY, RECHECK, STAGE_EVIDENCE, DISPATCH, CLASSIFY_RECEIPT`. Success: `authority: ExecutionAuthorityRef | None`; `evidence: DispatchEvidence | None`; `receipt: DispatchReceipt | None`; `operation: TradingOperation | None`. The authority is an exact versioned port; concrete Simulator/Broker implementations are resolved by Composition, not imported. FRs: OBTAIN_RISK_AUTHORITY, RECHECK_DISPATCH_AUTHORITY, SELECT_EXECUTION_AUTHORITY, STAGE_DISPATCH_EVIDENCE, DISPATCH_ONCE, CLASSIFY_DISPATCH_RECEIPTS.
5. `trading.reconcile-trading@1` / `ReconcileTradingCapability` / `reconcile_trading` — ops `REQUEST_RUN, EXECUTE, RESOLVE_FINDING`. Success: `request: ReconciliationRequest | None`; `findings: tuple[ReconciliationFinding, ...] = ()`. FRs: RECONCILE_TRADING_STATE, TRUST_EXECUTION_DEALS, BLOCK_BLIND_RETRY, RECORD_RECONCILIATION_FINDINGS.
6. `trading.manage-protections@1` / `ManageProtectionsCapability` / `manage_protections` — ops `INSTALL, MODIFY, CANCEL, RECOVER`. Success: `protection_set: ProtectionSet | None`; `change: ProtectionChange | None`. FRs: OWN_PROTECTIVE_ORDERS…RECOVER_PROTECTIVE_ORDERS.
7. `trading.journal-execution@1` / `JournalExecutionCapability` / `journal_execution` — ops `APPEND, EXPORT, BALANCE_LEDGER`. Success: `record: TradingJournalRecord | None`; `provenance: ExecutionProvenance | None`; `ledger_entry: OperationalLedgerEntry | None`. FRs: JOURNAL_TRADING_EVENTS, PIN_EXECUTION_PROVENANCE, BALANCE_TRANSACTION_LEDGER, EXPORT_EXECUTION_EVIDENCE.
8. `trading.execute-public-actions@1` / `ExecutePublicActionsCapability` / `execute_public_actions` — ops `ROUTE_ACTION, GOVERN_BULK, QUERY_STATE`. Success: `action: PublicTradingAction | None`; `query: TradingStateQuery | None` plus bounded `ResultPage`-style rows as `JsonObject` tuples referencing owner records. FRs: ROUTE_PUBLIC_ACTIONS, GOVERN_BULK_ACTIONS, QUERY_TRADING_STATE, ENFORCE_ACTION_PARITY.

Cross-owner references: `InstrumentRef` (Catalogue); Simulator execution-authority capability (`SIM`/`PAPER`); Broker sessions/correlations (`DEMO`/`LIVE`); `RiskDecision`/`RiskApprovalToken`/`RiskCapacityReservation`/`KillSwitchState` (Risk); `PrincipalRef` (Workspace); bulk tokens (Interfaces/Analytics). No subscriptions (streaming owned by Interfaces).

### Mandatory mutation chain

```text
Strategy intent or authorized manual plan
  -> Trading validation and readiness
  -> Runtime Risk decision + approval/capacity when required by route/profile
  -> immediate kill-switch and authority-generation recheck
  -> selected Simulator or Broker authority dispatch
  -> canonical receipt classification
  -> authority reconciliation
  -> canonical Trading order/deal/position projections
  -> immutable Trading journal and ledger/result evidence
```

The business/risk chain is common to `SIM`, `PAPER`, `DEMO`, and `LIVE`. Explicit route-specific safety gates are recorded separately and cannot silently replace or skip the common chain.

### Persisted State Ownership

| Status | Owned state | Rule |
|---|---|---|
| Missing | `trading_sessions`, `trading_session_events` | Explicit mode/context/authority/profile lifecycle; SIM may be run-scoped, PAPER/DEMO/LIVE durable operational. |
| Missing | `trading_operations`, `trading_operation_events` | One logical idempotent mutation state machine across all routes. |
| Missing | `trading_orders`, `trading_deals`, `trading_position_projections` | Canonical application projections reconciled from selected-authority evidence; raw Simulator/Broker authority evidence remains authority-owner state. |
| Missing | `trading_protection_sets`, `trading_protection_events` | Exact entry/position ownership and recovery state across routes. |
| Missing | `trading_journal_records` | Append-only typed intent/validation/dispatch/reconciliation evidence. |
| Missing | `operational_accounts`, `operational_ledger_entries`, `operational_valuations` | Balanced immutable accounting and point-in-time projections where the selected execution profile requires account projection. |
| Missing | `trading_reconciliation_runs`, `trading_reconciliation_findings` | Bounded authority evidence and resolution history. |

Current authority-side position truth is never accepted from Trading tables without reconciliation against the selected authority. Simulator authority state remains Simulator-owned; Broker provider truth remains Broker-owned.

## 2. Final Package Structure and Feature Independence

| Status | Feature | Module | Actor outcome | Deletion contract |
|---|---|---|---|---|
| Missing | `FEAT-TRD-MANAGE_TRADING_SESSIONS` Contracts, Sessions, and State | `session_state/` | Create and inspect explicit SIM/PAPER/DEMO/LIVE contexts and canonical operation states using definitions from `app/contracts/trading/` | Canonical execution lifecycle is unavailable; unrelated research/data/strategy capabilities continue. |
| Missing | `FEAT-TRD-VALIDATE_TRADE_PLANS` Plans, Validation, and Readiness | `plans_readiness/` | Turn an exact intent/manual request into a validated immutable route-aware plan | New operations cannot be admitted. |
| Missing | `FEAT-TRD-DISPATCH_ORDERS` Authority and Dispatch | `authority_dispatch/` | Send one admitted logical operation to the exact selected Simulator/Broker authority | New mutations are unavailable; monitoring/reconciliation continue where possible. |
| Missing | `FEAT-TRD-RECONCILE_TRADING` Reconciliation and Recovery | `reconciliation_recovery/` | Resolve authority truth, unknown outcomes, reconnects/gaps, and drift for every route | State becomes read-only/degraded until restored. |
| Missing | `FEAT-TRD-MANAGE_PROTECTIONS` Protective Orders and Ownership | `protection_ownership/` | Maintain stop/target/trailing ownership safely across fills and changes | New protected trades block unless the selected profile explicitly permits unprotected exposure. |
| Missing | `FEAT-TRD-JOURNAL_EXECUTION` Execution Evidence and Journal | `execution_evidence/` | Reconstruct every business decision and authority side effect causally | Mutations block if mandatory evidence cannot be staged. |
| Missing | `FEAT-TRD-ACCOUNT_OPERATIONS` Accounts and Ledger | `accounts_ledger/` | Reconcile balances/P&L/margin/accounting where required from canonical execution and authority evidence | Account valuation/capital health is unavailable; core execution may continue only if its profile does not require this capability. |
| Missing | `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS` Route-Aware Public Actions | `public_actions/` | Submit/cancel/modify/close through one safe route-neutral boundary | Interfaces cannot mutate Trading; internal monitoring continues. |

```text
trading/
├── README.md
├── __init__.py
├── session_state/
├── plans_readiness/
├── authority_dispatch/
├── reconciliation_recovery/
├── protection_ownership/
├── execution_evidence/
├── accounts_ledger/
└── public_actions/
```

| Feature | Responsibility file | Requirement implementation traces |
|---|---|---|
| `FEAT-TRD-MANAGE_TRADING_SESSIONS` | `session_state/session_state.py` | `fr_trd_define_trading_modes` through `fr_trd_define_operation_states` |
| `FEAT-TRD-VALIDATE_TRADE_PLANS` | `plans_readiness/plans_readiness.py` | `fr_trd_bind_trade_plan` through `fr_trd_recheck_dispatch_authority` |
| `FEAT-TRD-DISPATCH_ORDERS` | `authority_dispatch/authority_dispatch.py` | `fr_trd_select_execution_authority` through `fr_trd_classify_dispatch_receipts` |
| `FEAT-TRD-RECONCILE_TRADING` | `reconciliation_recovery/reconciliation_recovery.py` | `fr_trd_reconcile_trading_state` through `fr_trd_record_reconciliation_findings` |
| `FEAT-TRD-MANAGE_PROTECTIONS` | `protection_ownership/protection_ownership.py` | `fr_trd_own_protective_orders` through `fr_trd_recover_protective_orders` |
| `FEAT-TRD-JOURNAL_EXECUTION` | `execution_evidence/execution_evidence.py` | `fr_trd_journal_trading_events` through `fr_trd_export_execution_evidence` |
| `FEAT-TRD-ACCOUNT_OPERATIONS` | `accounts_ledger/accounts_ledger.py` | `fr_trd_project_operational_accounts` through `fr_trd_post_account_adjustments` |
| `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS` | `public_actions/public_actions.py` | `fr_trd_route_public_actions` through `fr_trd_enforce_action_parity` |

Each functional-requirement row owns a focused implementation and acceptance-test trace. `fr_*` names may be used as trace labels, but runtime discovery, dependency resolution, and removal occur through the owning feature's `FeatureSpec` and entry point. Private helpers are not public requirements.

## 3. Workflows

| Status | Workflow ID | Trigger | Inputs | Outcome |
|---|---|---|---|---|
| Missing | `WF-TRD-001` Session/context lifecycle | Simulator run or operator creates/starts/stops/archives context | Explicit SIM/PAPER/DEMO/LIVE mode, authority reference, route/profile, capability snapshot, opening state/data binding where applicable | Bound state transition or classified failure |
| Missing | `WF-TRD-002` New order/action | Strategy intent or manual action | Exact plan, current evidence, context/session, Runtime Risk decision/authority | Accepted/rejected/unknown logical operation and causal events through the selected authority |
| Missing | `WF-TRD-003` Cancel/modify/close | Authorized strategy/operator/simulation action | Existing operation/order/position identity, new plan, current Risk authority | Idempotent authority mutation and reconciled canonical state |
| Missing | `WF-TRD-004` Reconciliation | Scheduler/scheduled check, reconnect, event gap, unknown outcome, or operator request | Context generation, selected-authority snapshots/pages/events, local canonical operation state | Reconciled projections and explicit findings |
| Missing | `WF-TRD-005` Protection lifecycle | Entry fill or plan change | Entry/position identity, protection plan, selected authority capabilities, Risk decision | Owned protections installed/updated/recovered or exposure block/escalation |
| Missing | `WF-TRD-006` Account/result projection | Authority deal/position/account evidence changes | Exact Simulator/Broker evidence, Catalogue/FX versions | Balanced ledger/result/account projection appropriate to the route profile |
| Missing | `WF-TRD-007` Emergency block and drain | Kill-switch event or critical unknown state | Effective Risk block, contexts, in-flight operations, route-specific recovery policy | New mutations stopped and bounded cancel/flatten/hold actions executed only if explicitly authorized/applicable |

## 4. Composable Feature Specifications

### 4.1 `FEAT-TRD-MANAGE_TRADING_SESSIONS` Contracts, Sessions, and State

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-DEFINE_TRADING_MODES` | P0 | Trading execution mode/context shall be exactly `SIM`, `PAPER`, `DEMO`, or `LIVE`, explicitly selected, with no live default or implicit promotion. `SIM` is deterministic historical/replay execution; `PAPER` is forward paper execution; `DEMO`/`LIVE` are Broker-backed. | Missing/mismatched mode blocks start and dispatch. | Unified execution parity |
| Missing | `FR-TRD-BIND_TRADING_SESSION` | P0 | A Trading session/context shall bind stable ID, mode, exact execution authority reference, route/profile versions, capability snapshot, risk profile, opening state where applicable, created/started/stopped/archived times, and lifecycle generation. SIM contexts may be run-scoped but remain fully identified for deterministic replay. | Immutable bindings cannot change while active; changes create a new generation/context. | Session/context registry |
| Missing | `FR-TRD-DEFINE_SESSION_STATES` | P0 | Session/context states shall be `CREATED`, `STARTING`, `ACTIVE`, `DEGRADED`, `STOPPING`, `STOPPED`, or `ARCHIVED` with explicit legal transitions and causal events. | Illegal transitions have no side effect. | Lifecycle |
| Missing | `FR-TRD-DEFINE_LOGICAL_OPERATION` | P0 | A logical operation shall have stable operation ID, idempotency key, action, session/context, plan hash, Risk references, authority route, state, authority correlation, and ordered events. | No operation can change context, action, plan, or approved quantity identity after dispatch. | Canonical contracts |
| Missing | `FR-TRD-DEFINE_OPERATION_STATES` | P0 | Operation states shall distinguish `PLANNED`, `ADMITTED`, `DISPATCHING`, `ACCEPTED`, `REJECTED`, `UNKNOWN`, `RECONCILING`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `CLOSED`, and `FAILED` identically across routes. | Unknown authority outcome never becomes rejected/accepted/filled without authority evidence. | Deterministic projections |

#### Feature usage examples

The primary domain-logic module `app/services/trading/session_state/session_state.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above and route-parity scenarios covering all four modes.

### 4.2 `FEAT-TRD-VALIDATE_TRADE_PLANS` Plans, Validation, and Readiness

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-BIND_TRADE_PLAN` | P0 | A trade plan shall bind exact Strategy/version/intent or authenticated manual-order identity, instrument, side, order type, quantity method, entry, protection, time-in-force, explicit route, context/session, and evidence versions. | Ambiguous or mutable inputs are rejected before Risk review. | Plans/readiness |
| Missing | `FR-TRD-IDENTIFY_MANUAL_ACTIONS` | P0 | Manual actions shall carry authenticated principal, reason, source interface, request/correlation IDs, and explicit discretionary identity; they cannot masquerade as a Strategy signal. | Missing authorization or identity blocks. | Strategy discretionary identity |
| Missing | `FR-TRD-VALIDATE_TRADING_READINESS` | P0 | Readiness shall validate active context, selected authority capability, instrument mapping/rules, route-applicable market/session state, evidence freshness, route/profile compatibility, applicable account permission, and absence of unresolved reconciliation. Simulator and Broker differences are declared safety checks, not separate business readiness semantics. | Any mandatory unknown state blocks new mutation. | Unified validation/readiness |
| Missing | `FR-TRD-OBTAIN_RISK_AUTHORITY` | P0 | Trading shall obtain a current Runtime Risk decision for the exact plan/route and validate approval/capacity references where required by that profile. | Expired or mismatched authority causes no dispatch; Simulator cannot substitute its own sizing/admission. | Risk/Trading boundary |
| Missing | `FR-TRD-RECHECK_DISPATCH_AUTHORITY` | P0 | Immediately before dispatch Trading shall recheck context/authority generation, applicable kill switch, Risk validity, reservation, in-flight tolerance, and plan hash using the injected route time authority. | A change after admission returns to evaluation or blocks. | Common pre-dispatch gate |

#### Feature usage examples

The primary domain-logic module `app/services/trading/plans_readiness/plans_readiness.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.3 `FEAT-TRD-DISPATCH_ORDERS` Authority and Dispatch

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-SELECT_EXECUTION_AUTHORITY` | P0 | `SIM`/`PAPER` shall use only a registered Simulator execution-authority capability with a pinned semantic profile; `DEMO`/`LIVE` shall use only the exact Broker session environment. The authority port is versioned and implementation-neutral. | Cross-authority/cross-environment dispatch is structurally impossible; removing one authority family withdraws only its routes. | Unified authority selection |
| Missing | `FR-TRD-NORMALIZE_TRADE_PLAN` | P0 | Trading shall normalize a plan through Catalogue rules and selected authority capabilities before constructing the exact authority request. | Unsupported order/position/protection semantics reject or require explicit Strategy lowering; no silent route substitution. | Dispatch/target semantics |
| Missing | `FR-TRD-STAGE_DISPATCH_EVIDENCE` | P0 | The pre-dispatch operation record and immutable request hash shall commit before any Simulator/Broker authority side effect. | Staging failure causes no dispatch. | Immutable execution evidence |
| Missing | `FR-TRD-DISPATCH_ONCE` | P0 | Dispatch shall occur at most once per logical operation/idempotency identity and preserve exact selected-authority request/receipt correlation. | Concurrent/repeated requests cannot create a duplicate logical order on any route. | Route-aware actions |
| Missing | `FR-TRD-CLASSIFY_DISPATCH_RECEIPTS` | P0 | Simulator/Broker accepted, rejected, and unknown receipts shall normalize through one documented Trading state machine and causal event shape without inferring fills/final state. | Only reconciled authority evidence may establish canonical orders, deals, positions, or closure. | Parity dispatch/state |

#### Feature usage examples

The primary domain-logic module `app/services/trading/authority_dispatch/authority_dispatch.py` owns the executable `__main__` usage harness, with one named scenario per requirement and paired authority-conformance scenarios.

### 4.4 `FEAT-TRD-RECONCILE_TRADING` Reconciliation and Recovery

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-RECONCILE_TRADING_STATE` | P0 | Reconciliation shall compare canonical operations/projections with bounded selected-authority orders, deals/fills, positions, account state, and event cursors using authority IDs and time windows. | Missing evidence/gaps/inconsistent identities produce unresolved findings, not fabricated state. | Common reconciliation |
| Missing | `FR-TRD-TRUST_EXECUTION_DEALS` | P0 | Authority deals/fills are the input authority for executed quantity and realized state; authority position snapshots are current-state evidence, not a replacement for transaction history. Simulator fills become canonical only after Trading accepts/reconciles them. | Deal/position disagreements remain explicit until resolved. | Execution authority |
| Missing | `FR-TRD-BLOCK_BLIND_RETRY` | P0 | Unknown dispatch outcomes shall enter reconciliation with blind retry disabled on every route; retry requires proof of no authority operation or a new separately authorized logical action. | Duplicate-order fault fixtures create no second order for Simulator or Broker authorities. | Retry guard |
| Missing | `FR-TRD-RECOVER_TRADING_SESSION` | P0 | Recovery shall fence old generations, refresh selected-authority state, replay retained events where possible, and reconcile before returning context to `ACTIVE`. SIM uses deterministic scheduler/checkpoint evidence; forward routes use their authority reconnect semantics. | Unresolved drift leaves the context `DEGRADED` and blocks mutations. | Recovery |
| Missing | `FR-TRD-RECORD_RECONCILIATION_FINDINGS` | P0 | Reconciliation findings shall be typed, severity-ranked, linked to authority evidence, assigned deterministic auto/manual resolution policy, and append complete transition history. | Destructive operational repair requires explicit authorization; deterministic SIM repair/replay follows its pinned profile and never invents authority truth. | Execution evidence |

#### Feature usage examples

The primary domain-logic module `app/services/trading/reconciliation_recovery/reconciliation_recovery.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.5 `FEAT-TRD-MANAGE_PROTECTIONS` Protective Orders and Ownership

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-OWN_PROTECTIVE_ORDERS` | P0 | Every stop, target, trailing, break-even, partial-exit, or ATM action shall bind an exact canonical entry/order/position identity, quantity scope, plan version, and owner across every route. | Protections cannot attach to another strategy/manual trade/entry/residual quantity. | Protective lifecycle/ownership |
| Missing | `FR-TRD-VALIDATE_PROTECTION_CHANGES` | P0 | Protection installation/modification/cancellation shall pass current Risk validation and selected authority capability/distance/rounding rules. | Unsupported or risk-worsening changes block unless an explicit applicable exception authorizes them. | Protection/Risk validation |
| Missing | `FR-TRD-ALLOCATE_PROTECTED_QUANTITY` | P0 | Partial fills/exits shall allocate protected quantity, costs, realized P/L, and residual protection deterministically by the selected semantic profile, independent of authority family. | Protected quantity never exceeds canonical residual quantity and no residual is silently unprotected. | Parity semantics |
| Missing | `FR-TRD-RECOVER_PROTECTIVE_ORDERS` | P0 | Missing, rejected, orphaned, duplicated, or stale protection shall emit a critical finding and execute only the configured route-applicable authorized hold/cancel/flatten/retry policy. | No unapproved emergency mutation is invented. | Protection recovery |

#### Feature usage examples

The primary domain-logic module `app/services/trading/protection_ownership/protection_ownership.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.6 `FEAT-TRD-JOURNAL_EXECUTION` Execution Evidence and Journal

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-JOURNAL_TRADING_EVENTS` | P0 | Trading shall append typed events for plan, validation, Risk checks, reservation, dispatch, receipt, canonical order/deal/position change, reconciliation, protection, retry, and closure with monotonic context/session sequence. | First-divergence and causal reconstruction require no free-text log parsing. | Immutable execution evidence |
| Missing | `FR-TRD-PIN_EXECUTION_PROVENANCE` | P0 | Journal records shall pin domain/authority contract and profile versions, request/response hashes, evidence refs, authority generation, operator/strategy identity, route-appropriate time, and redacted failure details. | Secret canaries and hash verification pass; deterministic SIM reruns produce identical canonical evidence. | Audit/parity evidence |
| Missing | `FR-TRD-BALANCE_TRANSACTION_LEDGER` | P0 | A signed transaction ledger shall record balanced cash, asset/position, fee, financing/swap, realized P/L, and adjustment entries sourced from canonical reconciled deals/events where the route profile uses account projection. | Every journalized transaction balances in declared currencies/units; mutations are append-only reversals. | Transaction ledger |
| Missing | `FR-TRD-EXPORT_EXECUTION_EVIDENCE` | P1 | Execution evidence export shall be bounded, canonical, verifiable, route-labelled, and preserve linkage without exposing credentials or unrestricted authority payloads. | Export/import verification reproduces record hashes and detects gaps. | Evidence export |

#### Feature usage examples

The primary domain-logic module `app/services/trading/execution_evidence/execution_evidence.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.7 `FEAT-TRD-ACCOUNT_OPERATIONS` Accounts and Ledger

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-PROJECT_OPERATIONAL_ACCOUNTS` | P0 | Where required by the route profile, account projections shall include cash, balances, open positions, pending obligations, realized/unrealized P/L, fees, financing, equity, margin, free margin, buying power, and risk-health timestamps from canonical reconciled execution and selected-authority evidence. | Projection totals reconcile to the ledger and explicit authority differences. | Account semantics |
| Missing | `FR-TRD-VALUE_OPERATIONAL_ACCOUNTS` | P0 | Valuation shall pin mark source/time, FX graph/version, contract sizes, currencies, rounding, and missing-price policy; deterministic SIM uses pinned simulation marks/time. | No value, P/L, margin, or buying power is fabricated. | Valuation/P&L |
| Missing | `FR-TRD-RECONCILE_OPERATIONAL_LEDGER` | P0 | Selected-authority reconciliation shall compare balances, orders, deals/fills, positions, fees, financing, and applicable adjustment evidence against canonical ledger/projections. | Differences produce typed findings and cannot be silently posted. | Authority reconciliation |
| Missing | `FR-TRD-POST_ACCOUNT_ADJUSTMENTS` | P1 | Authorized adjustments/corporate actions shall append evidence-linked balanced entries with effective/record/posting times and reversal lineage where the authority/profile supports them. | Direct edit/delete of ledger history is prohibited. | Accounting |

#### Feature usage examples

The primary domain-logic module `app/services/trading/accounts_ledger/accounts_ledger.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.8 `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS` Route-Aware Public Actions

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-ROUTE_PUBLIC_ACTIONS` | P0 | Public create/submit/cancel/modify/close/flatten/hold actions shall use one versioned route-neutral contract and delegate to the exact bound execution context; no caller chooses a private Simulator/Broker adapter. | Unsupported action or unavailable authority capability returns a stable structured failure. | Route-aware public actions |
| Missing | `FR-TRD-GOVERN_BULK_ACTIONS` | P0 | Bulk/emergency actions shall require pinned selection, impact preview, explicit conflict policy, applicable authenticated approval, idempotency identity, and per-target outcome. | Scope cannot broaden between preview and commit; partial outcomes remain explicit. | Emergency/interface rule |
| Missing | `FR-TRD-QUERY_TRADING_STATE` | P0 | Query operations shall expose bounded context/session, operation, canonical order/deal/position, protection, account/ledger, and reconciliation projections with route/authority/freshness state. | Authority-local Simulator/Broker evidence is not mislabeled as canonical Trading state; stale/unresolved projections are explicit. | Read model |
| Missing | `FR-TRD-ENFORCE_ACTION_PARITY` | P0 | Simulator orchestration, direct package use, HTTP, UI, CLI, MCP, and automation shall reach the same Trading business behavior, Risk checks, idempotency, events, and audit for equivalent actions. | No transport or execution route offers a privileged business-mutation path. | Unified parity |

#### Feature usage examples

The primary domain-logic module `app/services/trading/public_actions/public_actions.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

## 5. Package-Wide Requirements, Configuration, and Architecture Invariants

| Status | Setting | Default | Rule |
|---|---|---|---|
| Missing | `trading_default_mode` | None | Execution context must be explicit; never defaults to `LIVE` or any other route. |
| Missing | `operation_admission_ttl` | 30 seconds | Cannot exceed Risk decision/reservation validity; SIM may use injected deterministic scheduler time. |
| Missing | `reconciliation_interval` | Profile-defined | SIM may reconcile at deterministic event/checkpoint boundaries; forward routes use bounded time intervals; unknown outcomes trigger immediate reconciliation. |
| Missing | `reconciliation_page_limit` | 1,000 | Continue with explicit cursors; never truncate silently. |
| Missing | `max_unresolved_critical_findings` | 0 | Any critical unresolved finding degrades and blocks new mutation in the affected scope. |
| Missing | `protection_recovery_deadline` | Profile-defined | Time source is injected; expiry executes only an explicitly authorized/applicable recovery policy. |

### Non-Functional Requirements

- There is no implicit mode, execution authority, account, size, protection, retry, or emergency action.
- Exact decimals and units are required for price, quantity, money, P/L, cost, and ledger values.
- An authority timeout after dispatch is an unknown outcome until reconciled, including Simulator authority when such uncertainty is deliberately modeled.
- Every mutation is idempotent, causally traceable, and preceded by staged evidence.
- UI/API/CLI/MCP/Simulator cannot bypass Strategy validation, Runtime Risk, authority capability release, or Trading state machines.
- The common Trading lifecycle accepts an injected time/deadline authority; deterministic SIM must not be forced through wall-clock semantics.
- AI or plugin output is proposal evidence only and never direct execution authority.
- Trading contains no Simulator matching engine and no Broker SDK/provider implementation.

## 6. Open Decisions

None currently. Add only unresolved architectural choices that would otherwise require implementation guesswork.

## 7. Tests and Definition of Done

- Every `FR-TRD-*` has focused automated verification and a named scenario in its feature's executable primary-module usage harness.
- Contract tests prove `SIM`/`PAPER`/`DEMO`/`LIVE` route neutrality for common business state and explicit differences for authority/time/safety fields.
- Trading unit/integration tests use deterministic authority conformance doubles so the domain can complete before the concrete Simulator provider exists.
- Simulator integration later proves its real authority provider executes through the same public Trading path and cannot construct canonical orders/deals/positions independently.
- Broker integration proves demo/live authority requests normalize through the same Trading receipt/operation/reconciliation semantics.
- Concurrency tests prove at-most-once logical dispatch, token/reservation single use, and no duplicate retry after unknown outcome.
- Reconciliation fixtures cover partial fills, out-of-order events, gaps, reconnect/checkpoint recovery, manual/provider-side change where applicable, stale generation, orphan protection, fees, swap, and adjustments.
- Ledger fixtures balance exactly and reconcile to canonical deals, account projections, and independent calculations.
- Gate-sequence tests prove equivalent `SIM`, `PAPER`, `DEMO`, and `LIVE` actions traverse the same business/risk gate categories and order, with only declared route-specific safety deltas.
- Deterministic SIM parity tests prove identical pinned manifests/seed streams/time authority produce identical canonical Trading evidence.
- Kill-switch, stale-risk, capability removal, authority loss, persistence failure, deletion, reinstall, and leak tests pass.
- Physical removal of Simulator withdraws only `SIM`/`PAPER`; physical removal of Broker Connectivity withdraws only `DEMO`/`LIVE`.

## 8. Change Process

Any mode, state transition, authority, time/deadline semantics, retry, reconciliation, protection, ledger, or emergency-policy change requires versioned contracts and failure fixtures. Trading may consume public contracts but never duplicate Strategy, Risk, Broker, Catalogue, Data, or Simulator implementation logic.
