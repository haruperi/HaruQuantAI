# Phase 11 Portfolio StandardResponse Migration

> **Plan ID:** `PORT-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/portfolio`
> **Migration program:** HaruQuantAI standard public-operation responses
> **Safety posture:** Fail closed at Risk and Trading authority boundaries

## 1. Purpose and Gate

Replace `PortfolioOutcome[T]` at the Portfolio public boundary with Utils
`StandardResponse[T]`, preserving raw portfolio results, trace identity, audit event
references, error evidence, lifecycle state, uncertain execution truth, and
reconciliation behavior.

Before implementation, read all repository authorities, the Portfolio README and
feature specifications, Utils responses/errors, and current Strategy/Data/
Simulation/Risk/Trading/Analytics contracts. Refresh the worktree inventory, issue a
dry run, and wait for a new standalone `APPROVED: EXECUTE`.

No live Trading action is authorized by this plan.

## 2. Standard Contract and Portfolio Semantics

The exact top-level fields are `status`, `message`, `data`, `error`, and `metadata`.

- `PortfolioOutcome.value` becomes direct `data`.
- `request_id` and `correlation_id` become canonical metadata identifiers.
- `audit_event_id` moves to `metadata.extensions` when present.
- `PortfolioOutcome.error.code` becomes `StandardError.code`.
- Its symbolic detail becomes structured `error.details`.
- `PortfolioOutcome.ok` becomes standard status and is not duplicated.
- Lifecycle/business state remains inside `PortfolioConstructionResult`,
  `ActivePortfolioAllocation`, or `PortfolioRebalancePlan`.
- Successful `None` remains allowed if any operation currently returns it.
- Do not nest `PortfolioOutcome` in `data`.

An executed-but-unmeasured rebalance is a successfully completed Portfolio business
outcome with that state in the raw plan; it is not erased by an Analytics failure.
An uncertain Trading outcome remains fail-closed and must not be blindly retried.

## 3. Features and Boundary

The registry contains:

1. Contracts.
2. Construction.
3. Rebalancing.
4. Lifecycle API.
5. Evidence.
6. State.
7. Allocation.
8. Orchestration.

The root exports `PortfolioService` as the public operational facade. Feature helper
functions remain implementation seams unless the refreshed root registry explicitly
promotes them.

## 4. Public Operation Inventory

The baseline contains nine operations.

### 4.1 Portfolio service

- `PortfolioService.construct`
- `PortfolioService.status`
- `PortfolioService.activate`
- `PortfolioService.assess_drift`
- `PortfolioService.submit_rebalance`
- `PortfolioService.recompute_measurement`
- `PortfolioService.rollback`
- `PortfolioService.history`

Required raw data:

| Method | Raw successful result |
|---|---|
| `construct` | `PortfolioConstructionResult` |
| `status` | `ActivePortfolioAllocation` |
| `activate` | `ActivePortfolioAllocation` |
| `assess_drift` | `PortfolioRebalancePlan` |
| `submit_rebalance` | `PortfolioRebalancePlan` |
| `recompute_measurement` | `PortfolioRebalancePlan` |
| `rollback` | `ActivePortfolioAllocation` |
| `history` | `tuple[ActivePortfolioAllocation, ...]` |

Refresh exact optional/absence behavior before implementation. If status/not-found
currently returns a typed error outcome, preserve that error rather than introducing
successful `None`.

### 4.2 Error conversion

- `PortfolioError.to_payload`

Because `PortfolioError` is root-exported and `to_payload` is a public bounded
conversion method, migrate it to `StandardResponse[PortfolioErrorPayload]`; the
existing immutable payload is direct `data`.

Internal Portfolio error handling should not call this public method merely to build
another response. Use the error fields/catalogue directly at the service boundary.

### 4.3 Exclusions

- Service constructor and private `_trace`, `_fallback_trace`, `_success`, `_failure`,
  and `_active` helpers.
- DTO constructors/properties.
- Feature-level construction/evidence helpers not exported at the package root.
- Repository, allocation, rebalancing, and orchestration internals.

Those helpers remain raw internally so the facade wraps once.

## 5. Legacy Envelope Retirement

`PortfolioOutcome[T]` contains:

- `ok`
- `request_id`
- `correlation_id`
- exactly one of `value` or `error`
- optional `audit_event_id`

Retirement sequence:

1. Characterize all success/error branches and audit references.
2. Migrate `PortfolioService._success` and `_failure` internals to Utils factories or
   remove them in favor of one focused response builder.
3. Migrate all eight facade methods.
4. Update tests, usage, type annotations, direct consumers, and mocks.
5. Remove `PortfolioOutcome` from contracts and the root only after repository-wide
   search proves no remaining public dependency.
6. Preserve Portfolio business DTOs unchanged.

No compatibility adapter may leak beyond the Portfolio package.

## 6. Error Catalogue Migration

Replace `PORTFOLIO_ERROR_CODES` with an immutable Portfolio-owned catalogue using
Utils `ErrorDefinition`, preserving all 24 codes:

- `PORT_APPROVAL_REQUIRED`
- `PORT_AUDIT_PENDING`
- `PORT_CONFIG_INVALID`
- `PORT_CONSTRUCTION_FAILED`
- `PORT_DEPENDENCY_FAILED`
- `PORT_ELIGIBILITY_INVALID`
- `PORT_EVIDENCE_INVALID`
- `PORT_FX_EVIDENCE_INVALID`
- `PORT_IDEMPOTENCY_CONFLICT`
- `PORT_INTERNAL_ERROR`
- `PORT_INVALID_INPUT`
- `PORT_KILL_SWITCH_ACTIVE`
- `PORT_MEASUREMENT_FAILED`
- `PORT_METHOD_UNSUPPORTED`
- `PORT_NOT_FOUND`
- `PORT_PERSISTENCE_FAILED`
- `PORT_REBALANCE_BLOCKED`
- `PORT_REFERENCE_CHANGED`
- `PORT_RISK_AUTHORIZATION_INVALID`
- `PORT_SIMULATION_INVALID`
- `PORT_UNCERTAIN_OUTCOME`
- `PORT_UNSAFE_OBJECT`
- `PORT_VERSION_CONFLICT`
- `PORT_WEIGHT_INVALID`

Mapping:

- Catalogue description to response message.
- Code to standard error code.
- Symbolic detail and safe dependency evidence to error details.
- Unexpected exceptions to `PORT_INTERNAL_ERROR`.
- Ambiguous Trading results to `PORT_UNCERTAIN_OUTCOME`.
- Missing/stale Risk authorization to the precise approved Portfolio code.

Do not expose allocation payloads, account identifiers, approval tokens, credentials,
or broker responses in errors/logs.

## 7. Metadata Matrix

Common:

- `domain="portfolio"`.
- `requires_network` reflects concrete cross-domain ports.
- Side-effect declarations describe the maximum behavior reachable from the public
  operation.

| Method | Risk | Read only | DB mutation | Places trade |
|---|---|---:|---:|---:|
| `construct` | `medium` | Depends | If candidate persisted | No |
| `status` | `low` | Yes | No | No |
| `activate` | `critical` | No | Yes | No |
| `assess_drift` | `high` | Yes | No | No |
| `submit_rebalance` | `critical` | No | Yes | Yes |
| `recompute_measurement` | `high` | No | Yes | No |
| `rollback` | `critical` | No | Yes | No |
| `history` | `low` | Yes | No | No |
| `PortfolioError.to_payload` | `none` | Yes | No | No |

`submit_rebalance` can invoke Trading and therefore conservatively declares
`places_trade=True`. `recompute_measurement` must never invoke Trading again.

Extensions may preserve audit event ID, workflow/causation IDs not already in the raw
DTO, repository revision, dependency response codes, or measurement state evidence.

## 8. Cross-Domain Coordination

Prerequisites:

- Strategy immutable version references.
- Data/Analytics market, FX, performance, and measurement evidence.
- Simulation portfolio validation.
- Risk review, activation, validity, approval, and kill-switch responses.
- Trading rebalance execution.

Rules:

- Check every upstream response before data.
- A successful Risk response is not necessarily approval; inspect its raw decision.
- Never retry `PORT_UNCERTAIN_OUTCOME` by calling Trading again.
- Preserve immutable Trading execution truth if Analytics measurement fails.
- `recompute_measurement` consumes stored facts only.
- Do not embed an upstream `StandardResponse` in Portfolio data.

## 9. Implementation Work Packages

### PORT-WP1 — Characterization

Freeze all nine signatures, raw values, errors, trace/audit fields, lifecycle states,
cross-domain calls, repository writes, and idempotency.

### PORT-WP2 — Catalogue and facade responses

Add the catalogue, migrate public error conversion, and adapt `_success`/`_failure`.
Add exact response-shape and trace tests.

### PORT-WP3 — Read and construction operations

Migrate construct, status, history, and drift assessment. Preserve hashes, weights,
versions, ordering, and evidence validation.

### PORT-WP4 — Governed lifecycle

Migrate activation and rollback. Maintain Risk authorization, expected revision,
audit ordering, transactions, and immutable history.

### PORT-WP5 — Rebalance

Migrate submit/recompute. Coordinate Trading and Analytics response consumption,
uncertain outcomes, executed-unmeasured state, and no-repeat execution.

### PORT-WP6 — Envelope removal and docs

Remove all `PortfolioOutcome` references, update root exports, all eight feature
registries, exact `FR-*` and usage paths/lines, architecture relationships, and
`[Unreleased]`.

## 10. Tests and Usage

Required:

- All nine public operations return exact standard responses.
- Raw DTO/tuple/error-payload placement.
- All 24 catalogue codes.
- Request/correlation/audit preservation.
- Risk fail-closed behavior.
- Trading uncertain-outcome non-retry.
- Analytics failure preserves execution truth.
- Rollback creates new immutable history.
- Accurate metadata and resource cleanup.

Primary suites:

- `tests/portfolio/unit/test_api_and_quality.py`
- `tests/portfolio/unit/test_portfolio_api_service_coverage.py`
- `tests/portfolio/unit/test_contracts.py`
- `tests/portfolio/unit/test_config_and_errors.py`
- `tests/portfolio/integration/test_construction_workflow.py`
- `test_activation_workflow.py`
- `test_rebalance_workflow.py`
- `test_owner_contract_compatibility.py`
- `test_usage_scripts.py`
- All eight numbered usage programs

Final gate:

```powershell
uv run ruff check app/services/portfolio tests/portfolio
uv run ruff format --check app/services/portfolio tests/portfolio
uv run mypy app/services/portfolio tests/portfolio
uv run pytest tests/portfolio
Get-ChildItem tests/portfolio/usage/[0-9][0-9]_*.py | ForEach-Object {
    uv run python $_.FullName
}
```

No live Trading call is permitted.

## 11. Risks, Exclusions, and Rollback

Risks:

- Nested `PortfolioOutcome` inside standard data.
- Loss of audit/trace fields.
- Treating Risk response success as authorization.
- Retrying uncertain execution.
- `recompute_measurement` accidentally invoking Trading.

Excluded:

- Portfolio construction/rebalance policy changes.
- New allocation methods.
- Live execution.
- AI-tool registration.
- Broad upstream-domain refactoring.

Rollback facade, catalogue, focused consumers, tests, examples, and active docs as a
coherent unit. Restore `PortfolioOutcome` only with all producer/consumer
annotations. Rerun construction, activation, rebalance, and uncertain-outcome gates.

## 12. Completion Checklist

- [ ] All nine refreshed operations return `StandardResponse[T]`.
- [ ] `PortfolioOutcome[T]` no longer crosses the public boundary.
- [ ] Raw results are directly in `data`.
- [ ] All 24 errors use a validated Portfolio catalogue.
- [ ] Audit, Risk authority, Trading truth, and immutable history are preserved.
- [ ] Side-effect metadata is accurate.
- [ ] Consumers, tests, examples, and exact `FR-*` evidence agree.
- [ ] Full validation passes without live action.
