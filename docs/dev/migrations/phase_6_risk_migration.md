# Phase 6 Risk StandardResponse Migration

> **Plan ID:** `RISK-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/risk`
> **Migration program:** HaruQuantAI standard public-operation responses
> **Safety posture:** Fail closed; no live trading authorization

## 1. Purpose

This is the self-contained implementation plan for migrating qualifying Risk public
operations to Utils `StandardResponse[T]`. It must preserve Risk decisions, audit
integrity, token semantics, kill-switch authority, and every safe current result.

The coding agent must first read the repository authorities, the root and affected
Risk feature READMEs, current Utils response/error contracts, source, consumers, and
tests. It must produce a fresh dry run and wait for a standalone
`APPROVED: EXECUTE`. Approval used to create this plan does not authorize code
changes or any live action.

## 2. Contract and Safety Invariants

`StandardResponse[T]` contains exactly `status`, `message`, `data`, `error`, and
`metadata`.

- Successful Risk DTOs, decisions, reports, tokens, snapshots, hashes, and audit
  evidence remain directly in `data`.
- Response status is only `success` or `error`.
- Business states such as `approve`, `warn`, `needs_approval`, `reject`, and `block`
  remain inside the raw Risk result.
- A policy rejection that is a successfully evaluated Risk decision normally remains
  a success response containing that reject/block decision. It is not converted into
  a technical error merely because approval was denied.
- Invalid requests, unavailable required evidence, persistence failure, policy
  execution failure, or unexpected exception use the error branch according to the
  existing feature contract.
- Metadata must never weaken or override a Risk decision.
- No caller may bypass a kill switch, approval token, evidence gate, or governor.
- Timing uses the shared monotonic helper and three-decimal milliseconds.

## 3. Feature Order

The registry contains 15 features:

1. Contracts and errors.
2. Configuration.
3. Portfolio risk snapshots.
4. Position sizing.
5. Audit chain.
6. Limits.
7. Regimes.
8. Strategy admission.
9. Allocation review/activation.
10. Approval tokens.
11. Decision validity.
12. Governor.
13. Kill switch.
14. Scenarios.
15. Reporting.

## 4. Public Operation Inventory

The baseline contains 24 qualifying operations.

### 4.1 Public functions

- `load_risk_config`
- `compute_config_hash`
- `build_portfolio_risk_snapshot`
- `calculate_position_size`
- `evaluate_market_context`
- `evaluate_portfolio_limits`
- `validate_market_context_evidence`
- `assess_risk_regime`
- `review_strategy_admission`
- `review_allocation_proposal`
- `activate_allocation_budget`
- `revalidate_risk_decision`
- `apply_kill_switch_command`
- `check_risk_kill_switch`
- `run_risk_scenario_analysis`
- `generate_risk_report`

Each raw current return becomes `data` without adding a result/payload wrapper.

### 4.2 Approval service methods

- `ApprovalTokenService.issue`
- `ApprovalTokenService.validate_reserve_and_consume`
- `ApprovalTokenService.revoke_scope`

Preserve token identity, scope, expiry, single-use, reservation, consumption,
revocation, and double-spend behavior. A validation result that denies use remains
the documented raw result unless the current contract explicitly raises a domain
failure.

### 4.3 Audit-chain methods

- `RiskAuditChain.append`
- `RiskAuditChain.append_kill_switch_transition`
- `RiskAuditChain.verify`

Preserve initial ledger verification, write locks, checksums, sequence order,
transactionality, and tamper detection. Never report success before a required audit
write is durable.

### 4.4 Governor methods

- `RiskGovernor.review_trade_risk`
- `RiskGovernor.run_portfolio_risk_governor`

The governor result remains raw `data`; response metadata cannot substitute for
decision evidence.

### 4.5 Exclusions

DTO constructors, enum values, properties, database migrations, internal storage
helpers, and injected dependency callables are not independently migrated unless the
refreshed root registry classifies them as public operations.

## 5. Error Catalogue Migration

Create a Risk-owned immutable catalogue using Utils `ErrorDefinition`. Preserve all
33 current codes:

- `INVALID_INPUT`
- `VALIDATION_FAILED`
- `INVALID_PORTFOLIO_STATE`
- `INVALID_RISK_CONFIG`
- `MISSING_EVIDENCE`
- `STALE_EVIDENCE`
- `LIMIT_FAILED`
- `POLICY_BLOCKED`
- `PERMISSION_DENIED`
- `KILL_SWITCH_ACTIVE`
- `KILL_SWITCH_UNKNOWN`
- `APPROVAL_REQUIRED`
- `APPROVAL_TOKEN_INVALID`
- `APPROVAL_TOKEN_EXPIRED`
- `APPROVAL_TOKEN_REVOKED`
- `APPROVAL_TOKEN_CONSUMED`
- `CONFIG_VERSION_MISMATCH`
- `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`
- `PAYLOAD_TOO_LARGE`
- `MISSING_STOP_LOSS`
- `INSUFFICIENT_VOLATILITY_EVIDENCE`
- `INSUFFICIENT_K_EVIDENCE`
- `LIVE_STATE_STALE`
- `IN_FLIGHT_TOLERANCE_EXCEEDED`
- `IN_FLIGHT_RECONCILIATION_EXPIRED`
- `AUDIT_CHAIN_TAMPER_DETECTED`
- `CALCULATION_FAILED`
- `SNAPSHOT_BUILD_FAILED`
- `GOVERNOR_DECISION_FAILED`
- `REPORT_GENERATION_FAILED`
- `STORAGE_ERROR`
- `TOOL_EXECUTION_FAILED`
- `UNKNOWN_ERROR`

The catalogue owns safe description, severity, retryability, and operator action.
Utils owns only the common shape and validation.

Map `RiskDomainError` as follows:

- `risk_code.value` to `StandardError.code`.
- Safe redacted diagnostic evidence to `error.details`.
- A stable safe summary to `message`.
- Unexpected exceptions to `UNKNOWN_ERROR`, except where the current operation has a
  more precise approved internal failure code.

Preserve the existing assignment/key redaction and strengthen it only through shared
Utils redaction. No exception message may expose positions, orders, credentials,
tokens, account identifiers, or full request payloads.

## 6. Metadata Matrix

Common:

- `domain="risk"`.
- `places_trade=False`; Risk authorizes or blocks but does not execute broker orders.
- `requires_network=False` unless a concrete public operation directly invokes a
  verified external port.

| Operations | Risk level | Read only | DB/file mutation |
|---|---|---:|---|
| Config load/hash, snapshot, sizing, limits, regimes, scenarios, reporting | `medium` | Usually yes | Declare actual config/report IO |
| Admission/allocation review, revalidation | `high` | Yes | False unless audit is part of the operation |
| Token issue/consume/revoke | `critical` | No | `modifies_database=True` when persisted |
| Audit append/transition | `critical` | No | `modifies_database=True` |
| Audit verify | `critical` | Yes | False |
| Governor review | `critical` | Depends | Declare audit/state persistence |
| Kill-switch apply | `critical` | No | Declare authoritative state/audit mutation |
| Kill-switch check | `critical` | Yes | False |
| Allocation activation | `critical` | No | Declare activation/audit persistence |

Extensions may preserve audit record IDs, policy/config versions, evidence hashes,
reservation IDs, or persistence references that were formerly returned beside the
raw payload. They may not contain the raw decision again.

## 7. Upstream and Downstream Coordination

Prerequisites:

- Data migration for market/portfolio evidence.
- Strategy migration for admission and intent evidence.
- Indicators migration where Risk consumes calculated evidence.

Every upstream response must be checked before consuming `data`. Translate upstream
failures into approved Risk codes while preserving the safe upstream domain/code in
details. Missing, malformed, stale, or error responses fail closed.

Downstream consumers include Trading, Simulation, Portfolio, and live-session gates.
They must:

- Treat response success separately from Risk approval state.
- Read the actual decision from `response.data`.
- Block if the response is error, absent, stale, or structurally invalid.
- Never interpret `status="success"` as permission to trade.

This distinction requires dedicated integration tests.

## 8. Implementation Work Packages

### RISK-WP1 — Contract freeze

Reconcile the root export, 15 feature registries, raw return types, exceptions,
side effects, consumers, mocks, and usage evidence. Add failing five-field boundary
tests and decision-vs-response-state tests.

### RISK-WP2 — Error infrastructure

Add and validate the immutable Risk catalogue. Adapt `RiskDomainError` at public
boundaries. Preserve typed internal exceptions if useful, but do not let them escape
qualifying public operations.

### RISK-WP3 — Pure calculations

Migrate config, snapshot, sizing, limit, regime, scenario, and report operations
first. Do not change formulas, thresholds, evidence freshness, or decision rules.

### RISK-WP4 — Admission, allocation, and validity

Migrate review and revalidation operations. Preserve reason codes, evidence hashes,
policy versions, expiration semantics, and reject/block states.

### RISK-WP5 — Stateful authority

Migrate tokens, audit chain, governor, kill switch, and activation last. Maintain
transactions and locking. Construct a success response only after all required state
and audit changes complete.

### RISK-WP6 — Consumer hardening

Update Trading/Portfolio/Simulation consumers and tests so they fail closed on an
error response and separately evaluate the decision in `data`.

### RISK-WP7 — Active documentation

Update the root and feature READMEs with exact `FR-*`, API, contracts, requirements,
and usage paths/lines. Update architecture/project documents only for real
cross-domain changes and add a concise `[Unreleased]` changelog entry.

## 9. Tests and Usage

Tests must prove:

- All 24 public operations return the exact response shape.
- All raw results are direct `data`.
- All 33 error codes are catalogue-approved.
- Decision state remains distinct from response status.
- Error/absent/stale upstream responses fail closed.
- Kill switches cannot be bypassed.
- Tokens cannot be replayed or double-spent.
- Audit append is durable before success and tamper verification remains strict.
- Sensitive evidence is redacted.
- Side-effect metadata matches actual behavior.

Primary suites:

- `tests/risk/unit/test_public_api.py`
- `tests/risk/unit/test_errors.py`
- `tests/risk/unit/test_tokens.py`
- `tests/risk/unit/test_chain.py`
- `tests/risk/unit/test_governor.py`
- `tests/risk/unit/test_kill_switch.py`
- `tests/risk/integration/test_contract_compatibility.py`
- `tests/risk/integration/test_approval_tokens.py`
- `tests/risk/integration/test_risk_persistence.py`
- `tests/risk/integration/test_trade_review.py`
- `tests/risk/integration/test_usage_scripts.py`
- All 15 numbered usage programs under `tests/risk/usage/`

Suggested final gate:

```powershell
uv run ruff check app/services/risk tests/risk
uv run ruff format --check app/services/risk tests/risk
uv run mypy app/services/risk tests/risk
uv run pytest tests/risk
Get-ChildItem tests/risk/usage/[0-9][0-9]_*.py | ForEach-Object {
    uv run python $_.FullName
}
```

Do not run live broker operations. Persistence tests must use isolated temporary
databases and close every handle.

## 10. Risks, Scope, and Rollback

Risks:

- Mistaking successful evaluation for approved action.
- Returning success before token/audit/state persistence completes.
- Losing audit identity in response conversion.
- Weakening fail-closed behavior while translating upstream errors.
- Incorrectly setting `places_trade=True` for a policy-only operation.

Excluded:

- Risk-policy redesign.
- New thresholds, models, or decision states.
- Live trading.
- Kill-switch override mechanisms.
- AI-tool exposure.
- Unrelated downstream migrations.

Rollback only the affected Risk files, focused consumer changes, tests, examples, and
active documentation. Remove a new catalogue/export only after restoring all
references. Verify the legacy Risk suite and fail-closed integration paths.

## 11. Completion Checklist

- [ ] All 24 refreshed public operations return `StandardResponse[T]`.
- [ ] Raw Risk outputs are directly in `data`.
- [ ] All 33 codes use a validated Risk-owned catalogue.
- [ ] Decision state is never conflated with response status.
- [ ] Tokens, audits, governors, activation, and kill switches remain fail closed.
- [ ] Metadata accurately declares risk and side effects.
- [ ] Consumers, protocols, mocks, tests, and examples are coordinated.
- [ ] Exact `FR-*` evidence and line references are updated.
- [ ] All validation passes with no live actions.
