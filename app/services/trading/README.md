# Trading

> **Package:** `app/services/trading/`
> **Status:** `Missing`
> **Last updated:** `2026-08-23`
> **Domain ID:** `D-TRD`
> **Specification version:** `1.1-code-aligned`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Update this document before modifying or adding code.

---

## Code-Aligned Implementation Convention

This README is the sole current target registry for this domain's feature IDs and statuses, functional requirements, domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence, and deletion behavior. `PROJECT.md` owns system scope, cross-domain behavior, system NFRs, and release gates; `ARCHITECTURE.md` owns universal package and runtime constraints. Feature-local READMEs, manifests, contract definitions, migrations, and tests provide current implementation evidence without silently changing this target registry.

Implementation uses the repository's existing feature substrate: each feature lives directly at `app/services/<domain>/<feature>/`, is discovered through the `haruquantai.features` Python entry-point group, and declares one immutable `FeatureSpec` in `manifest.py`. There are no domain or feature YAML manifests.

Every implemented feature also contains a mandatory runtime-validated `README.md`, pure `__init__.py`, strict `config.py`, lifecycle `feature.py`, and focused implementation modules. Dependencies and effects flow through `FeatureContext`/`FeatureScope`; cross-feature implementation imports are forbidden. Persistent state is declared by `FeatureSpec.state`; any migrations and storage adapters remain with the owning feature. Capability keys use `<domain>.<name>@<major>`. FR IDs remain product, acceptance, and test-trace identities rather than one runtime registration per FR. A requirement `Depends` cell expresses product sequencing, traceability, or acceptance evidence only; runtime dependencies are declared separately with exact keys in `FeatureSpec.requires` or `FeatureSpec.optional`.

Feature-level automated tests live at `tests/services/trading/<feature>/`. Usage examples never live under `tests/`; they belong to each feature's designated primary domain-logic module. Broader automated verification retains its documented architecture, composition, API, integration, or system test location. The code-backed procedure is the [Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md).

## 1. Purpose and Boundary

### Purpose

Trading converts an exact Strategy intent or authorized manual plan into a governed paper/demo/live execution lifecycle. It owns session mode, authority selection, readiness, dispatch state, provider correlation, reconciliation, protective-order ownership, immutable execution evidence, and operational account projections. Every mutation passes Runtime Risk and uses either the paper-execution capability or Broker Connectivity; no broker SDK or simulation engine object crosses the boundary.

### Owns

- Durable trading sessions and explicit `PAPER`, `DEMO`, or `LIVE` mode.
- Canonical operational order/position/deal contracts and state machines.
- Trade plans, manual-order identity, readiness, and preflight orchestration.
- Selection of paper versus broker execution authority and exact route.
- Idempotent dispatch, unknown-outcome handling, retry guard, and provider correlation.
- Reconciliation of orders, deals, positions, account state, and in-flight operations from authority evidence.
- Protective-order lifecycle, ownership, modification, and recovery.
- Immutable execution journal, operational events, and signed transaction ledger.
- Operational account ledger, valuation, realized/unrealized P/L, margin/buying-power projection, corporate-action evidence, and broker reconciliation.

### Does not own

- Strategy authoring, validation, or signal generation; Strategy owns them.
- Risk decisions, sizing authority, budgets, approval tokens, capacity, or kill switch; Risk owns them.
- Provider connections, permissions, SDK transport, or provider-truth decoding; Broker Connectivity owns them.
- Simulated fill semantics or research results; Simulator owns them. Paper sessions consume a versioned paper-execution capability.
- Instrument identity, sessions, trading rules, costs, or currency topology; Catalogue owns them.
- Market/account/FX/news evidence normalization; Data and Broker Connectivity own the evidence.
- Derived operational-journal analysis and qualification projections; Analytics owns them, while Trading retains the canonical execution journal and ledger.
- Research portfolio construction; Portfolio owns it.
- Custody, deposits, withdrawals, tax accounting, or copy trading.

### Shared Contracts

Trading semantically owns its public session, plan, operation, order, deal, protection, journal, ledger, reconciliation, and action contracts, but their sole physical definitions live in `app/contracts/trading/` and wire schemas in `app/contracts/trading/wire/`. `app/services/trading/` contains implementations only and shall not define or re-export substitute public contract types. Consumed contract types are imported from their corresponding `app/contracts/<owner>/` namespace. Feature IDs and FR IDs are documentation, lifecycle, acceptance, and traceability identities; runtime consumption uses exact versioned capability keys declared by contracts and `FeatureSpec`. The exact public records and capability bundles are listed in the [Shared Contracts README](../../contracts/README.md#414-appcontractstrading).

### Mandatory mutation chain

```text
Strategy intent or authorized manual plan
  → Trading validation and readiness
  → Runtime Risk decision + approval/capacity when required
  → immediate kill-switch and session-generation recheck
  → selected paper or broker authority dispatch
  → receipt classification
  → authority reconciliation
  → immutable Trading journal and operational ledger
```

### Persisted State Ownership

| Status | Owned state | Rule |
|---|---|---|
| Missing | `trading_sessions`, `trading_session_events` | Durable explicit mode/account/route/profile lifecycle. |
| Missing | `trading_operations`, `trading_operation_events` | One logical idempotent mutation state machine. |
| Missing | `trading_orders`, `trading_deals`, `trading_position_projections` | Canonical operational projections reconciled from authority evidence; raw provider evidence remains Broker Connectivity-owned. |
| Missing | `trading_protection_sets`, `trading_protection_events` | Exact entry/position ownership and recovery state. |
| Missing | `trading_journal_records` | Append-only typed intent/validation/dispatch/reconciliation evidence. |
| Missing | `operational_accounts`, `operational_ledger_entries`, `operational_valuations` | Balanced immutable accounting and point-in-time projections. |
| Missing | `trading_reconciliation_runs`, `trading_reconciliation_findings` | Bounded evidence and resolution history. |

Current mutable provider position truth is never accepted from these tables without reconciliation against the selected authority.

## 2. Final Package Structure and Feature Independence

| Status | Feature | Module | Actor outcome | Deletion contract |
|---|---|---|---|---|
| Missing | `FEAT-TRD-MANAGE_TRADING_SESSIONS` Contracts, Sessions, and State | `session_state/` | Create and inspect durable paper/demo/live sessions and canonical operation states using definitions from `app/contracts/trading/` | Operational trading is unavailable; research continues. |
| Missing | `FEAT-TRD-VALIDATE_TRADE_PLANS` Plans, Validation, and Readiness | `plans_readiness/` | Turn an exact intent/manual request into a validated immutable plan | New operations cannot be admitted. |
| Missing | `FEAT-TRD-DISPATCH_ORDERS` Authority and Dispatch | `authority_dispatch/` | Send one admitted logical operation to the exact selected authority | New mutations are unavailable; monitoring/reconciliation continue. |
| Missing | `FEAT-TRD-RECONCILE_TRADING` Reconciliation and Recovery | `reconciliation_recovery/` | Resolve provider/paper truth, unknown outcomes, reconnects, and drift | State becomes read-only/degraded until restored. |
| Missing | `FEAT-TRD-MANAGE_PROTECTIONS` Protective Orders and Ownership | `protection_ownership/` | Maintain stop/target/trailing ownership safely across fills and changes | New protected trades block unless policy permits unprotected exposure. |
| Missing | `FEAT-TRD-JOURNAL_EXECUTION` Execution Evidence and Journal | `execution_evidence/` | Reconstruct every operational decision and side effect causally | Mutations block if mandatory evidence cannot be staged. |
| Missing | `FEAT-TRD-ACCOUNT_OPERATIONS` Operational Accounts and Ledger | `accounts_ledger/` | Reconcile balances, P/L, margin, and accounting from broker/paper evidence | Operational valuation and capital/risk health are unavailable. |
| Missing | `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS` Route-Aware Public Actions | `public_actions/` | Submit/cancel/modify/close through one safe mode-neutral boundary | Interfaces cannot mutate Trading; internal monitoring continues. |

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
| Missing | `WF-TRD-001` Session lifecycle | Operator creates/starts/stops/archives session | Explicit mode, account, route/profile, capability snapshot, optional paper opening state/data binding | Durable state transition or classified failure |
| Missing | `WF-TRD-002` New order/action | Strategy intent or manual action | Exact plan, current evidence, session, Risk decision/authority | Accepted/rejected/unknown logical operation and causal events |
| Missing | `WF-TRD-003` Cancel/modify/close | Authorized operator/strategy action | Existing operation/order/position identity, new plan, current Risk authority | Idempotent authority mutation and reconciled state |
| Missing | `WF-TRD-004` Reconciliation | Scheduled, reconnect, event gap, unknown outcome, or operator request | Session generation, authority snapshots/pages/events, local operation state | Reconciled projections and explicit findings |
| Missing | `WF-TRD-005` Protection lifecycle | Entry fill or plan change | Entry/position identity, protection plan, provider/paper capabilities, Risk decision | Owned protections installed/updated/recovered or exposure block/escalation |
| Missing | `WF-TRD-006` Account valuation | Authority/account/deal/position evidence changes | Exact provider/paper evidence, Catalogue/FX versions | Balanced ledger entries and point-in-time account/risk-health projection |
| Missing | `WF-TRD-007` Emergency block and drain | Kill-switch event or critical unknown state | Effective Risk block, sessions, in-flight operations, recovery policy | New mutations stopped and bounded cancel/flatten/hold actions executed only if explicitly authorized |

## 4. Composable Feature Specifications

### 4.1 `FEAT-TRD-MANAGE_TRADING_SESSIONS` Contracts, Sessions, and State

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-DEFINE_TRADING_MODES` | P0 | Trading mode shall be exactly `PAPER`, `DEMO`, or `LIVE`, explicitly selected per durable session, with no live default or implicit promotion. | Missing/mismatched mode blocks start and dispatch. | Session/mode policy |
| Missing | `FR-TRD-BIND_TRADING_SESSION` | P0 | A session shall bind stable session ID, mode, account/authority reference, route/profile versions, capability snapshot, risk profile, opening state where applicable, created/started/stopped/archived times, and lifecycle version. | Immutable bindings cannot change while active; changes create a new session/version. | Durable session registry |
| Missing | `FR-TRD-DEFINE_SESSION_STATES` | P0 | Session states shall be `CREATED`, `STARTING`, `ACTIVE`, `DEGRADED`, `STOPPING`, `STOPPED`, or `ARCHIVED` with explicit legal transitions and causal events. | Illegal transitions have no side effect. | Session lifecycle |
| Missing | `FR-TRD-DEFINE_LOGICAL_OPERATION` | P0 | A logical operation shall have stable operation ID, idempotency key, action, session, plan hash, Risk references, authority route, state, provider/paper correlations, and ordered events. | No operation can change session, action, or plan identity after dispatch. | Canonical contracts |
| Missing | `FR-TRD-DEFINE_OPERATION_STATES` | P0 | Operation states shall distinguish `PLANNED`, `ADMITTED`, `DISPATCHING`, `ACCEPTED`, `REJECTED`, `UNKNOWN`, `RECONCILING`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `CLOSED`, and `FAILED`. | Unknown transport outcome never becomes rejected or accepted without authority evidence. | Deterministic projections |

#### Feature usage examples

The primary domain-logic module `app/services/trading/session_state/session_state.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.2 `FEAT-TRD-VALIDATE_TRADE_PLANS` Plans, Validation, and Readiness

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-BIND_TRADE_PLAN` | P0 | A trade plan shall bind exact Strategy/version/intent or authenticated manual-order identity, instrument, side, order type, quantity method, entry, protection, time-in-force, route, session, and evidence versions. | Ambiguous or mutable inputs are rejected before Risk review. | Plans/readiness and Strategy manual identity |
| Missing | `FR-TRD-IDENTIFY_MANUAL_ACTIONS` | P0 | Manual actions shall carry authenticated principal, reason, source interface, request/correlation IDs, and explicit discretionary identity; they cannot masquerade as a Strategy signal. | Missing authorization or identity blocks. | Strategy discretionary identity |
| Missing | `FR-TRD-VALIDATE_TRADING_READINESS` | P0 | Readiness shall validate active session, selected authority, provider/paper capability, instrument mapping/rules, market/session state, evidence freshness, route/profile compatibility, account permission, and absence of unresolved reconciliation. | Any mandatory unknown state blocks new mutation. | Validation/readiness |
| Missing | `FR-TRD-OBTAIN_RISK_AUTHORITY` | P0 | Trading shall obtain a current Runtime Risk decision for the exact plan and validate approval/capacity references where required. | Expired or mismatched authority causes no dispatch. | Risk/trading boundary |
| Missing | `FR-TRD-RECHECK_DISPATCH_AUTHORITY` | P0 | Immediately before dispatch Trading shall recheck session/authority generation, effective kill switch, Risk validity, reservation, in-flight tolerance, and plan hash. | A change after admission returns to evaluation or blocks. | Manual preflight/reuse rules |

#### Feature usage examples

The primary domain-logic module `app/services/trading/plans_readiness/plans_readiness.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.3 `FEAT-TRD-DISPATCH_ORDERS` Authority and Dispatch

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-SELECT_EXECUTION_AUTHORITY` | P0 | `PAPER` shall use only a registered paper-execution capability with a pinned Simulator semantic profile; `DEMO` and `LIVE` shall use only the exact Broker session environment. | Cross-authority or cross-environment dispatch is structurally impossible and tested. | Authority selection/isolation and Simulator |
| Missing | `FR-TRD-NORMALIZE_TRADE_PLAN` | P0 | Trading shall normalize a plan through Catalogue rules and selected authority capabilities before constructing the exact authority request. | Unsupported order/position/protection semantics reject or require explicit Strategy lowering; no silent substitution. | Dispatch and target semantics |
| Missing | `FR-TRD-STAGE_DISPATCH_EVIDENCE` | P0 | The pre-dispatch operation record and immutable request hash shall commit before any external or paper side effect. | Staging failure causes no dispatch. | Immutable execution evidence |
| Missing | `FR-TRD-DISPATCH_ONCE` | P0 | Dispatch shall occur at most once per logical operation/idempotency identity and preserve exact authority request/receipt correlation. | Concurrent or repeated requests cannot create a duplicate logical order. | Route-aware actions |
| Missing | `FR-TRD-CLASSIFY_DISPATCH_RECEIPTS` | P0 | Accepted, rejected, and unknown receipts shall transition through the documented state machine and publish causal events without inferring fills or final state. | Only reconciled authority evidence may establish orders, deals, positions, or closure. | Dispatch/state |

#### Feature usage examples

The primary domain-logic module `app/services/trading/authority_dispatch/authority_dispatch.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.4 `FEAT-TRD-RECONCILE_TRADING` Reconciliation and Recovery

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-RECONCILE_TRADING_STATE` | P0 | Reconciliation shall compare local operations/projections with bounded authority orders, deals, positions, account state, and event cursors using provider/paper IDs and time windows. | Missing pages, event gaps, or inconsistent identities produce unresolved findings, not fabricated state. | Reconciliation |
| Missing | `FR-TRD-TRUST_EXECUTION_DEALS` | P0 | Deals/fills are the authority for executed quantity and realized state; position snapshots are current-state evidence, not a replacement for transaction history. | Position/deal disagreements remain explicit until resolved. | Position authority |
| Missing | `FR-TRD-BLOCK_BLIND_RETRY` | P0 | Unknown dispatch outcomes shall enter reconciliation with blind retry disabled; a retry requires proof of no authority operation or a new separately authorized logical action. | Duplicate-order fault fixtures create no second order. | Retry guard |
| Missing | `FR-TRD-RECOVER_TRADING_SESSION` | P0 | Reconnect or event-gap recovery shall fence old generations, refresh authority state, replay retained events where possible, and reconcile before returning the session to `ACTIVE`. | Unresolved drift leaves the session `DEGRADED` and blocks mutations. | Recovery |
| Missing | `FR-TRD-RECORD_RECONCILIATION_FINDINGS` | P0 | Reconciliation findings shall be typed, severity-ranked, linked to evidence, assigned deterministic auto/manual resolution policy, and append their complete transition history. | Destructive repair requires explicit authorization and pre-repair evidence. | Operational evidence |

#### Feature usage examples

The primary domain-logic module `app/services/trading/reconciliation_recovery/reconciliation_recovery.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.5 `FEAT-TRD-MANAGE_PROTECTIONS` Protective Orders and Ownership

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-OWN_PROTECTIVE_ORDERS` | P0 | Every stop, target, trailing, break-even, partial-exit, or ATM action shall bind an exact entry/order/position identity, quantity scope, plan version, and owner. | Protections cannot attach to another strategy, manual trade, entry, or residual quantity. | Protective lifecycle/ownership |
| Missing | `FR-TRD-VALIDATE_PROTECTION_CHANGES` | P0 | Protection installation/modification/cancellation shall pass current Risk validation and selected authority capability/distance/rounding rules. | Unsupported or risk-worsening changes block unless an explicit emergency policy authorizes them. | Protection and risk stop validation |
| Missing | `FR-TRD-ALLOCATE_PROTECTED_QUANTITY` | P0 | Partial fills/exits shall allocate protected quantity, costs, realized P/L, and residual protection deterministically by the selected semantic profile. | Protected quantity never exceeds live residual quantity and no residual is silently unprotected. | Parity semantics |
| Missing | `FR-TRD-RECOVER_PROTECTIVE_ORDERS` | P0 | Missing, rejected, orphaned, duplicated, or stale protection shall emit a critical finding and execute only the configured authorized hold/cancel/flatten/retry policy. | No unapproved emergency mutation is invented. | Protection recovery |

#### Feature usage examples

The primary domain-logic module `app/services/trading/protection_ownership/protection_ownership.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.6 `FEAT-TRD-JOURNAL_EXECUTION` Execution Evidence and Journal

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-JOURNAL_TRADING_EVENTS` | P0 | Trading shall append typed events for plan, validation, Risk checks, reservation, dispatch, receipt, order/deal/position change, reconciliation, protection, retry, and closure with monotonic session sequence. | First-divergence and causal reconstruction require no free-text log parsing. | Immutable execution evidence |
| Missing | `FR-TRD-PIN_EXECUTION_PROVENANCE` | P0 | Journal records shall pin domain contract/profile versions, request/response hashes, evidence refs, authority generation, operator/strategy identity, UTC and monotonic times, and redacted failure details. | Secret canaries and hash verification pass. | Audit/evidence |
| Missing | `FR-TRD-BALANCE_TRANSACTION_LEDGER` | P0 | A signed transaction ledger shall record balanced cash, asset/position, fee, financing/swap, realized P/L, and adjustment entries sourced from reconciled deals/events. | Every journalized transaction balances in declared currencies/units; mutations are append-only reversals. | Transaction ledger and portfolio ledger |
| Missing | `FR-TRD-EXPORT_EXECUTION_EVIDENCE` | P1 | Execution evidence export shall be bounded, canonical, verifiable, and preserve linkage without exposing credentials or unrestricted provider payloads. | Export/import verification reproduces record hashes and detects gaps. | Evidence export |

#### Feature usage examples

The primary domain-logic module `app/services/trading/execution_evidence/execution_evidence.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.7 `FEAT-TRD-ACCOUNT_OPERATIONS` Operational Accounts and Ledger

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-PROJECT_OPERATIONAL_ACCOUNTS` | P0 | Operational accounts shall project cash, balances, open positions, pending obligations, realized/unrealized P/L, fees, financing, equity, margin, free margin, buying power, and risk-health timestamps from reconciled authority evidence and ledger entries. | Projection totals reconcile to the ledger and explicit provider differences. | Portfolio feature evidence |
| Missing | `FR-TRD-VALUE_OPERATIONAL_ACCOUNTS` | P0 | Valuation shall pin mark source/time, FX graph/version, contract sizes, currencies, rounding, and missing-price policy; stale or missing mandatory marks remain explicit. | No value, P/L, margin, or buying power is fabricated. | Valuation/P&L |
| Missing | `FR-TRD-RECONCILE_OPERATIONAL_LEDGER` | P0 | Broker/paper reconciliation shall compare balances, orders, deals, positions, fees, financing, and corporate-action/adjustment evidence against operational ledger/projections. | Differences produce typed findings and cannot be silently posted. | Broker reconciliation/corporate actions |
| Missing | `FR-TRD-POST_ACCOUNT_ADJUSTMENTS` | P1 | Authorized adjustments and corporate actions shall append evidence-linked balanced entries with effective/record/posting times and reversal lineage. | Direct edit/delete of ledger history is prohibited. | Portfolio accounting |

#### Feature usage examples

The primary domain-logic module `app/services/trading/accounts_ledger/accounts_ledger.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.8 `FEAT-TRD-EXECUTE_PUBLIC_ACTIONS` Route-Aware Public Actions

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-TRD-ROUTE_PUBLIC_ACTIONS` | P0 | Public create/submit/cancel/modify/close/flatten/hold actions shall use one versioned mode-neutral contract and delegate to the exact session owner; no caller chooses a private adapter. | Unsupported action or unavailable capability returns a stable structured failure. | Route-aware public actions |
| Missing | `FR-TRD-GOVERN_BULK_ACTIONS` | P0 | Bulk or emergency actions shall require pinned selection, impact preview, explicit conflict policy, authenticated approval, idempotency identity, and per-target outcome. | Scope cannot broaden between preview and commit; partial outcomes remain explicit. | Emergency/operator and interface bulk rule |
| Missing | `FR-TRD-QUERY_TRADING_STATE` | P0 | Query operations shall expose bounded session, operation, order, deal, position, protection, account, ledger, and reconciliation projections with authority/freshness state. | Stale or unresolved projections are visibly classified and never presented as live authority. | Operational read model |
| Missing | `FR-TRD-ENFORCE_ACTION_PARITY` | P0 | Direct package use, HTTP, UI, CLI, MCP, and automation shall reach identical application behavior, authorization, Risk checks, idempotency, events, and audit. | No transport offers a privileged mutation path. | API parity and Interfaces |

#### Feature usage examples

The primary domain-logic module `app/services/trading/public_actions/public_actions.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

## 5. Package-Wide Requirements, Configuration, and Architecture Invariants

| Status | Setting | Default | Rule |
|---|---|---|---|
| Missing | `trading_default_mode` | None | Session mode must be explicit; never defaults to `LIVE`. |
| Missing | `operation_admission_ttl` | 30 seconds | Cannot exceed Risk decision/reservation validity. |
| Missing | `reconciliation_interval` | 5 seconds active / 60 seconds idle | Profiles may narrow; unknown outcomes trigger immediate reconciliation. |
| Missing | `reconciliation_page_limit` | 1,000 | Continue with explicit cursors; never truncate silently. |
| Missing | `max_unresolved_critical_findings` | 0 | Any critical unresolved finding degrades and blocks new mutation. |
| Missing | `protection_recovery_deadline` | 5 seconds | Expiry executes only an explicitly authorized emergency policy. |

### Non-Functional Requirements

- There is no implicit live mode, route, broker account, size, protection, retry, or emergency action.
- Exact decimals and units are required for price, quantity, money, P/L, cost, and ledger values.
- A network timeout after dispatch is an unknown outcome until reconciled.
- Every mutation is idempotent, causally traceable, and preceded by staged evidence.
- UI/API/CLI/MCP cannot bypass Strategy validation, Runtime Risk, Broker capability release, or Trading state machines.
- AI or plugin output is proposal evidence only and never direct execution authority.

## 6. Open Decisions

None currently. Add only unresolved architectural choices that would otherwise require implementation guesswork.

## 7. Tests and Definition of Done

- Every `FR-TRD-*` has focused automated verification and a named scenario in its feature's executable primary-module usage harness.
- Contract tests prove mode/route neutrality and transport parity.
- Integration fixtures cover paper, demo, and live-certified routes; live fixtures may use only explicitly approved sandbox/testnet accounts until owner release.
- Concurrency tests prove at-most-once logical dispatch, token/reservation single use, and no duplicate retry after unknown outcome.
- Reconciliation fixtures cover partial fills, out-of-order events, gaps, reconnect, manual provider-side change, stale generation, orphan protection, fees, swap, and corporate adjustments.
- Ledger fixtures balance exactly and reconcile to deals, account projections, and independent calculations.
- Kill-switch, stale-risk, capability removal, adapter loss, persistence failure, deletion, reinstall, and leak tests pass.

## 8. Change Process

Any mode, state transition, authority, retry, reconciliation, protection, ledger, or emergency-policy change requires versioned contracts and failure fixtures. Trading may consume but never duplicate Strategy, Risk, Broker, Catalogue, Data, or Simulator business logic.
