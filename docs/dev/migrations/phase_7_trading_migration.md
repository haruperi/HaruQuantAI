# Phase 7 Trading StandardResponse Migration

> **Plan ID:** `TRADE-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/trading`
> **Migration program:** HaruQuantAI standard public-operation responses
> **Safety posture:** Fail closed; live mutation requires separate deterministic authority

## 1. Purpose and Gate

This document plans the complete Trading public-response migration. It replaces
`StandardTradingEnvelope` at qualifying public boundaries while preserving every raw
result, business outcome state, warning, error, audit field, reconciliation state,
and side-effect guarantee.

The coding agent must read `AGENTS.md`, repository authorities, the Trading root and
feature READMEs, current Brokers/Data/Indicators/Strategy/Risk/Simulator contracts,
and all affected source/tests. It must inspect the worktree, issue a fresh dry run,
and wait for a standalone `APPROVED: EXECUTE`. This plan never authorizes live broker
calls, production mutations, commits, or pushes.

## 2. StandardResponse Rules

The Utils response has exactly:

```text
status
message
data
error
metadata
```

`status` is only `success` or `error`. The current Trading envelope supports:

- `success`
- `rejected`
- `blocked`
- `pending_approval`
- `packaged`
- `sent`
- `partial`
- `filled`
- `cancelled`
- `unknown_outcome`
- `error`

Migration policy:

- A successfully completed business outcome such as rejected, blocked,
  pending-approval, packaged, sent, partial, filled, or cancelled uses standard
  `status="success"` and preserves its legacy/business status under the stable
  `metadata.extensions["legacy_status"]` key.
- `unknown_outcome` uses `status="error"`, code `UNKNOWN_OUTCOME`, and preserves
  `legacy_status="unknown_outcome"`. It must continue to trigger reconciliation and
  must never be reported as a confirmed success or failure.
- Technical/domain failures use `status="error"`.
- Current envelope `data` becomes direct `StandardResponse.data`, not the old
  envelope object.
- `message` is preserved as the response message.
- Warnings and audit metadata move to redacted, bounded extensions.
- Primary error code/evidence moves to `StandardError`; additional legacy error rows
  are retained in bounded `error.details`.
- Raw receipts, plans, reports, snapshots, events, projections, and action results
  stay in `data`.

## 3. Domain Features

Migration order follows:

1. Contracts.
2. State.
3. Validation.
4. Routing.
5. Reconciliation.
6. Monitoring.
7. Live session.
8. Actions.
9. Reporting.

Preserve the package root as the authoritative public boundary.

## 4. Public Operation Inventory

The baseline contains 52 qualifying operations: 35 functions and 17 exported-class
methods.

### 4.1 Contracts and validation

- `get_public_contracts`
- `create_trading_action_draft`
- `redact_trading_payload`
- `map_trading_error`
- `validate_order_request`
- `build_execution_plan`
- `assess_execution_readiness`
- `get_route_snapshot`

`redact_trading_payload` returns its existing redacted `JsonValue` directly in
`data`. `map_trading_error` becomes `StandardResponse[Any]` and no longer constructs
`StandardTradingEnvelope`.

### 4.2 State

- `get_trading_migrations`
- `reserve_idempotency`
- `apply_execution_event`
- `TradingStateStore.reserve_idempotency`
- `TradingStateStore.complete_idempotency`
- `TradingStateStore.append_event`
- `TradingStateStore.load_projection`
- `TradingStateStore.save_projection`
- `TradingStateStore.load_unresolved_attempts`
- `TradingStateStore.load_report_evidence`

The protocol and every implementation/mock must migrate together. Successful
`None`-returning writes use `data=None`; Utils explicitly permits successful `None`.

### 4.3 Routing and reconciliation

- `validate_adapter_capability`
- `classify_authority_response`
- `dispatch_order_intent`
- `compare_authority_state`
- `resolve_unknown_outcome`

`dispatch_order_intent` must consume the already-migrated Brokers response and put
the raw `ExecutionReceipt` in its own response `data`.

### 4.4 Monitoring

- `BudgetGate.validate`
- `build_broker_state_unknown_event`
- `emit_runtime_event`

Operational events remain raw data. Event publication evidence that is not the event
itself belongs in extensions.

### 4.5 Live session

- `LiveSession.risk_decision_for`
- `LiveSession.action_policy_for`
- `LiveSession.kill_switches_for`
- `LiveSession.readiness_for`
- `LiveSession.adapter_capability_for`
- `LiveSession.write_pre_audit`
- `LiveSession.start`
- `LiveSession.status`
- `LiveSession.stop`
- `evaluate_live_gate`

`LiveSession.now()` is excluded as a trivial injected clock accessor. Properties
`config`, `started`, `admission_enabled`, `reconciliation_ready`, and `store` are
also accessors rather than bounded operations.

Live start/stop must remain safe on repeated calls and partial shutdown. Do not emit
success before required audit/state/health transitions finish.

### 4.6 Trading actions

- `submit_order`
- `modify_order`
- `cancel_order`
- `close_position`
- `modify_position`
- `cancel_all_orders`
- `close_all_positions`
- `reduce_exposure`
- `pause_strategy`
- `resume_strategy`
- `sync_positions`
- `trigger_kill_switch`
- `clear_kill_switch`
- `execute_portfolio_rebalance`
- `run_live_evaluation_cycle`

Action results remain directly in `data`. The migration must not alter authorization,
idempotency, route choice, broker calls, or emergency-control order.

### 4.7 Reporting

- `build_trading_report`

The existing complete report is raw `data`; report/audit references outside the
report may use extensions.

## 5. Legacy Envelope Retirement

`StandardTradingEnvelope` currently contains `status`, `message`, `data`, `errors`,
`warnings`, and `audit_metadata`.

Required staged retirement:

1. Build characterization tests for every legacy status and evidence field.
2. Introduce a focused internal adapter from legacy envelope evidence to
   `StandardResponse` only if it reduces staged risk.
3. Migrate producers feature by feature.
4. Migrate all consumers, protocols, mocks, and examples.
5. Search the repository for live annotations and constructors.
6. Remove the envelope from the package root and contracts only after no production
   boundary depends on it.
7. Keep domain business result DTOs; do not replace them with JSON dictionaries.

Do not preserve `errors=()` or `warnings=()` as new top-level keys. Empty evidence
does not need extension entries.

## 6. Trading Error Catalogue

Replace `_TRADING_ERROR_CODES` with one immutable Trading-owned catalogue using Utils
`ErrorDefinition`. Preserve all 34 codes:

- `ADAPTER_INCOMPATIBLE`
- `AUDIT_FAILED`
- `BUDGET_BLOCKED`
- `CONFIGURATION_INVALID`
- `CONTRACT_CATALOG_CONFLICT`
- `GATE_BLOCKED`
- `IDEMPOTENCY_CONFLICT`
- `INVALID_DECIMAL`
- `INVALID_DRAFT`
- `INVALID_ENVELOPE`
- `INVALID_REBALANCE_REQUEST`
- `INVALID_REQUEST`
- `INVALID_ROUTE`
- `INVALID_TIME`
- `KILL_SWITCH_ACTIVE`
- `KILL_SWITCH_STALE`
- `KILL_SWITCH_UNKNOWN`
- `MALFORMED_RECEIPT`
- `PAYLOAD_NOT_JSON_SAFE`
- `PERMISSION_DENIED`
- `PERSISTENCE_FAILED`
- `PROVIDER_ERROR`
- `RECONCILIATION_REQUIRED`
- `SCOPE_MISMATCH`
- `SERVICE_UNAVAILABLE`
- `SIZE_MISMATCH`
- `STALE_EVIDENCE`
- `TIMEOUT`
- `TRADING_CONCURRENCY_CONFLICT`
- `UNKNOWN_ERROR`
- `UNKNOWN_OUTCOME`
- `VALIDATION_FAILED`
- `VERSION_CONFLICT`
- `WORKFLOW_TIMEOUT`

Preserve `TradingError.trading_code`, safe details, and trace context when mapping:

- Code becomes `StandardError.code`.
- Safe details become `message` and/or structured `error.details`.
- Redacted trace context is merged into `error.details`.
- Request/correlation IDs become canonical metadata IDs.
- Route/provider evidence may appear in details/extensions only if safe.
- Retryability comes from the approved catalogue, not ad hoc exception branches.

Unknown outcome and timeouts must remain non-retryable unless policy is explicitly
changed in the authoritative registry; caller retries could duplicate trades.

## 7. Operation Metadata

Common values:

- `domain="trading"`.
- `modifies_database=True` for state/idempotency/event writes.
- `writes_file` reflects the concrete audit/report sink.
- `requires_network=True` only when the operation can call a broker/provider.

| Family | Risk | Read only | Places trade |
|---|---|---:|---:|
| Contract discovery/redaction/validation | `low` | Yes | No |
| Readiness/routing/reconciliation reads | `high` | Yes | No |
| State reads | `medium` | Yes | No |
| State/event/idempotency writes | `high` | No | No |
| Live start/status/stop | `critical` | Depends | No |
| Draft/package-only action | `high` | Yes | No |
| Submit/modify/close/rebalance/live cycle | `critical` | No | Yes when route can execute |
| Cancel orders | `critical` | No | No, but state-changing |
| Emergency controls/kill switch | `critical` | No | No |
| Reporting | `low` | Yes | No |

For route-dependent operations, metadata must conservatively declare the maximum
possible side effect for that public operation; do not claim read-only because a
particular test used simulation.

## 8. Cross-Domain Coordination

Upstream contracts:

- Brokers `StandardResponse[ExecutionReceipt or broker result]`.
- Data/Indicators evidence.
- Strategy decisions/intents.
- Risk decisions, approval tokens, kill switches, and governors.
- Simulator execution for simulation routes.
- Portfolio rebalance requests.

Rules:

- Check upstream response status before data.
- A Risk response success is not authorization; inspect the decision in data.
- Broker error/unknown outcome must not be converted to a confirmed rejection.
- Never recursively nest upstream responses in Trading data.
- Preserve upstream domain/code in safe error details when translating.

Downstream Analytics and reporting adapters must consume raw Trading result data and
may use metadata extensions for warnings/audit evidence.

## 9. Implementation Work Packages

### TRD-WP1 — Characterization

Freeze 52 operation signatures, legacy statuses, raw results, errors, warnings,
audit evidence, side effects, idempotency, and unknown-outcome behavior.

### TRD-WP2 — Contracts and catalogue

Add the validated catalogue and response mapping infrastructure. Add tests for every
legacy status conversion. Do not remove the legacy model yet.

### TRD-WP3 — State and validation

Migrate protocols and implementations atomically. Preserve database transactions,
locks, migrations, optimistic versions, append-only events, and idempotency.

### TRD-WP4 — Routing, reconciliation, and monitoring

Migrate broker response consumption, unknown-outcome resolution, runtime events, and
budget gates. Exercise malformed and contradictory provider receipts.

### TRD-WP5 — Live lifecycle

Migrate dependency lookup methods, audit writes, gates, and start/status/stop. Use
only demo/demo/sandbox integration targets if real integration is separately
authorized.

### TRD-WP6 — Actions

Migrate one action family at a time: orders, positions, controls, emergency,
rebalance, then live runtime. Verify authorization before side effect and audit
before/after rules.

### TRD-WP7 — Reporting and retirement

Migrate reports/Analytics adapters, remove all legacy envelope references, update
root exports, feature registries, exact `FR-*` evidence, architecture relationships,
and `[Unreleased]`.

## 10. Tests and Validation

Mandatory coverage:

- Exact response shape and raw data for all operations.
- Every legacy status mapping.
- All 34 catalogue codes.
- Provider timeout/unknown outcome reconciliation.
- No duplicate dispatch on retries.
- Kill-switch and approval fail-closed behavior.
- Side-effect metadata for every action route.
- Async methods and mocks return genuine awaitables.
- SQLite/resource cleanup and micro-timeout circuit tests.

Primary suites include all `tests/trading/unit/` and `tests/trading/integration/`,
especially:

- `test_live_dispatch.py`
- `test_unknown_outcome.py`
- `test_state_recovery.py`
- `test_kill_switch.py`
- `test_portfolio_rebalance.py`
- `test_sim_dispatch.py`
- `test_contracts/test_errors.py`
- `test_live/test_session.py`
- `test_usage_scripts.py`

Final gate:

```powershell
uv run ruff check app/services/trading tests/trading
uv run ruff format --check app/services/trading tests/trading
uv run mypy app/services/trading tests/trading
uv run pytest tests/trading
Get-ChildItem tests/trading/usage/[0-9][0-9]_*.py | ForEach-Object {
    uv run python $_.FullName
}
```

No production/live broker call is permitted.

## 11. Risks, Exclusions, and Rollback

Highest risks are duplicate orders, false success, lost reconciliation evidence,
authorization bypass, inaccurate `places_trade`, and incomplete async/protocol
migration.

Excluded:

- Trading-policy redesign.
- New actions/routes/providers.
- Live production verification.
- AI-tool registration.
- Unrelated broker, risk, or portfolio refactors.

Rollback the approved Trading files, focused consumer edits, tests, usage programs,
and active docs as a coherent unit. Restore the legacy envelope/export only if every
producer and consumer is restored. Rerun all safety-critical targeted tests.

## 12. Completion Checklist

- [ ] All 52 refreshed public operations return `StandardResponse[T]`.
- [ ] Raw results are directly in `data`.
- [ ] All legacy status/evidence is preserved without extra top-level keys.
- [ ] All 34 errors use a validated Trading catalogue.
- [ ] Unknown outcome remains unconfirmed and reconcilable.
- [ ] Authorization, idempotency, audit, and kill switches remain fail closed.
- [ ] Protocols, async mocks, consumers, examples, and docs agree.
- [ ] Full validation passes without live action.
