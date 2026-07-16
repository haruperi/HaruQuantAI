# Risk

> **Package:** `app/services/risk`
> **Status:** `Missing`
> **Last updated:** `2026-07-13`

> This README is the package's **single source of truth** for requirements, final structure, implementation sequence, progress, usage examples, and tests.
> Update this file before changing the code.

---

## 1. Purpose and Boundary

### Purpose

Risk is HaruQuantAI's independent, deterministic master gate for risk-increasing actions. It converts immutable point-in-time evidence and policy into reproducible portfolio measurements, sizing recommendations, risk decisions, approval-token results, kill-switch state, scenarios, audit records, and focused explanations. Missing, stale, invalid, or unverifiable safety evidence fails closed; Risk never executes a trade.

### Owns

- Interception and deterministic review of every `TradeIntent` before execution.
- Final approved or capped position size, safety limits, exposure, concentration, drawdown, margin, leverage, historical VaR/CVaR, and correlation-impact evaluation.
- Risk policy/profile validation, stable configuration hashes, fixed decision precedence, and canonical reason/error codes.
- Canonical `RiskDecision` production through the concrete `RiskDecisionPackage` v1 schema.
- Kill-switch policy, `global > portfolio > strategy > symbol` hierarchy, canonical active state,
  block-state evaluation, clearance, and recovery eligibility.
- Approval-attestation validation, action-policy verdicts, approval-token issuance,
  validation, revocation, scope binding, expiry, and atomic durable single-use reservation.
- Strategy operational-eligibility decisions for exact registered versions/scopes, without owning technical registration.
- Allocation approval/capping/rejection, authoritative portfolio risk-budget projections, and budget activation, without constructing or executing allocations.
- Deterministic regime assessment, advisory scenario/what-if analysis, risk summaries, and risk-owned audit-chain records.

### Does not own

- Market, broker, account, position, pending-order, calendar, session, liquidity, or execution-state acquisition.
- Strategy signal generation or registry mutation; Portfolio-owned construction, allocation versioning, drift detection, or rebalance planning; portfolio execution, broker submission, fills, reconciliation, or emergency execution mutation.
- MT5 connections, provider SDK objects, broker credentials, database connection/locking infrastructure, broad performance reporting, cost reporting, incident management, or enterprise audit services.
- Full replay/timeline/cockpit infrastructure, ranked recommendation engines, parametric VaR, exit-liquidity stress, or graduated step-down controls in the initial build.
- Live approval from unverified text or any override of deterministic policy or kill-switch state.

### Shared contracts

Contract names, versions, and owners follow `docs/PROJECT.md`. The package path is `app/services/risk`, matching the top-level registry.

**Owned by this domain** — defined authoritatively here:
| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Missing | `RiskDecision`, represented by `RiskDecisionPackage` | `v1` | Trading, UI/API, Simulation | Return an independent verdict, approved size, reasons, evidence/config provenance, expiry, and optional approval token. |
| Missing | `ActionPolicyVerdict` | `v1` | Trading, UI/API | Return a Risk-owned allowed/denied action classification bound to approval, policy version, scope, and expiry. |
| Missing | `KillSwitchCommand` | `v1` | UI/API | Request authorized activation or clearance of Risk's canonical kill-switch state. |
| Missing | `KillSwitchState` | `v1` | Trading, UI/API | Publish canonical active/inactive state, scope, reason, version, and update time. |
| Missing | `ApprovalAttestation` | `v1` | UI/API | Authenticated human approval evidence containing action/scope, policy reference/version, issue/expiry times, principal, and trace IDs. |
| Missing | `StrategyOperationalEligibilityRequest` | `v1` | UI/API, Portfolio submit; Risk receives | Request deterministic operational review of an exact registered strategy version and scope. |
| Missing | `StrategyOperationalEligibilityDecision` | `v1` | Portfolio, Trading, UI/API | Publish scoped approval, conditions, suspension, expiry, or rejection without altering Strategy registration. |
| Missing | `AllocationReviewRequest` | `v1` | Portfolio submits; Risk receives | Request independent review of a Portfolio construction result or rebalance plan. |
| Missing | `AllocationRiskDecision` | `v1` | Portfolio, Trading, UI/API | Publish approval/caps/conditions/rejection and the authoritative risk-budget projection. |
| Missing | `AllocationBudgetActivationRequest` | `v1` | Portfolio submits; Risk receives | Activate the Risk-owned budget projection for one approved immutable allocation version. |
| Missing | `ScenarioResult` | `v1` | UI/API, Research | Publish a bounded deterministic advisory comparison that cannot grant execution approval. |

Each registered Risk contract carries `contract_version="v1"` and a separate
stable `risk.<contract_name>.v1` `schema_id`, including the eligibility,
allocation-review, and budget-activation family above. Compatibility is evaluated
only from `contract_version`.

**Consumed from other domains** — referenced only:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `TradeIntent` | `v1` | Strategy | Source proposal converted without loss into `ProposedTrade` for review. |
| `AccountStateSnapshot` | `v1` | Data | Read-only account, position, margin, and snapshot-time evidence. |
| `MarketContextEvidence` | `v1` | Data | Normalized session, calendar, spread, liquidity, volatility, correlation, crisis, freshness, provenance, and missingness evidence. |
| `FXConversionEvidence` | `v1` | Data | Fresh Data-owned conversion path/rate evidence; Risk never synthesizes rates. |
| Strategy registry reference | `v1` | Strategy | Verify exact immutable technical registration before operational eligibility review. |
| `PortfolioAllocationEvidence` | `v1` | Analytics | Consume non-binding performance/dependence/concentration evidence without delegating policy. |
| `AuthContext` | `v1` | Utils | Authenticated principal, roles/scopes, workflow, request, and correlation context. |
| `AuditEvent` | `v1` | Utils | Redacted common envelope through which Risk submits audit payloads to Data's durable audit storage. |

No raw DataFrame, provider object, socket, database session, or broker client may cross the Risk boundary.

### Persisted state

Data owns database connections, locking, and migration execution. Risk owns the following schemas and is their only semantic writer; concrete persistence occurs through injected narrow interfaces.

| Status | State / Store | Read access (via contract) | Migration definitions |
|---|---|---|---|
| Missing | Risk policy versions and configuration hashes | Risk; UI/API through approved policy views | `app/services/risk/audit/migrations.py` |
| Missing | Canonical kill-switch state | Trading and UI/API through `KillSwitchState` v1 | `app/services/risk/audit/migrations.py` |
| Missing | Approval-token issuance, revocation, nonce, and atomic reservation/consumption state | Risk validation only; validation result returned to caller | `app/services/risk/audit/migrations.py` |
| Missing | Decision audit chain, including `previous_hash` and `record_hash` | Trading/UI/API through `RiskDecision` and audit views through `AuditEvent` | `app/services/risk/audit/migrations.py` |
| Missing | Operational-eligibility decisions and suspension/expiry history | Portfolio, Trading, UI/API through `StrategyOperationalEligibilityDecision` | `app/services/risk/audit/migrations.py` |
| Missing | Allocation decisions and active authoritative risk-budget projections | Portfolio, Trading, UI/API through `AllocationRiskDecision` and approved Risk views | `app/services/risk/audit/migrations.py` |
| Missing | Optional decision/snapshot records enabled by an approved profile | Callers through Risk-owned result contracts only | `app/services/risk/audit/migrations.py` |

### Four-level structure

| Code level | Represents |
|---|---|
| **Package** | Risk domain |
| **Module folder** | One Risk feature/capability |
| **File** | One use case or focused responsibility |
| **Class / function / method** | Observable functional requirement |

```text
Risk package
└── Capability module
    └── Focused file
        └── Public class / function / method / constant
```

### Package capability map

```mermaid
flowchart TD
    RISK[[Risk Package]]
    RISK --> CONTRACTS[[contracts]]
    RISK --> CONFIG[[config]]
    RISK --> PORTFOLIO[[portfolio]]
    RISK --> SIZING[[sizing]]
    RISK --> POLICY[[policy]]
    RISK --> REGIMES[[regimes]]
    RISK --> AUDIT[[audit]]
    RISK --> APPROVALS[[approvals]]
    RISK --> DECISIONS[[decisions]]
    RISK --> SCENARIOS[[scenarios]]
    RISK --> REPORTING[[reporting]]

    CONTRACTS --> CFILES[Enums, errors, evidence, requests, results]
    CONFIG --> CFGFILES[Profiles and config hashes]
    PORTFOLIO --> PFILES[Evidence normalization and snapshot]
    SIZING --> SFILES[Position sizing]
    POLICY --> POFILES[Limits, market context, admission, allocation]
    REGIMES --> RFILES[Regime assessment]
    AUDIT --> AFILES[Hash chain, persistence interface, migrations]
    APPROVALS --> APFILES[Token lifecycle and state interface]
    DECISIONS --> DFILES[Governor, validity, kill switch]
    SCENARIOS --> SCFILES[Scenario and what-if analysis]
    REPORTING --> RPFILES[Markdown and JSON summaries]
```

---

## 2. Final Package Structure

Modules and files are ordered from lowest dependency to highest dependency. Private helpers may be added inside the listed focused files; they are not public requirements.

```text
risk/
├── __init__.py                         # Strict domain-level exports
├── README.md
├── contracts/                          # Versioned public contracts and errors
│   ├── __init__.py
│   ├── enums.py
│   ├── errors.py
│   ├── evidence.py
│   ├── requests.py
│   └── results.py
├── config/                             # Validated profiles and stable hashes
│   ├── __init__.py
│   └── profiles.py
├── portfolio/                          # Evidence normalization and risk snapshot
│   ├── __init__.py
│   └── snapshot.py
├── sizing/                             # Position sizing recommendations
│   ├── __init__.py
│   └── calculator.py
├── policy/                             # Limits and non-trade risk gates
│   ├── __init__.py
│   ├── limits.py
│   ├── admission.py
│   └── allocation.py
├── regimes/                            # Regime assessment and tightening
│   ├── __init__.py
│   └── assessment.py
├── audit/                              # Risk audit chain and persistence boundary
│   ├── __init__.py
│   ├── chain.py
│   ├── storage.py
│   └── migrations.py
├── approvals/                          # Approval-token lifecycle
│   ├── __init__.py
│   ├── state.py
│   └── tokens.py
├── decisions/                          # Canonical governor and block-state decisions
│   ├── __init__.py
│   ├── governor.py
│   ├── validity.py
│   └── kill_switch.py
├── scenarios/                          # Advisory scenario and what-if analysis
│   ├── __init__.py
│   └── analysis.py
└── reporting/                          # Focused Risk summaries
│   ├── __init__.py
│   └── reports.py
```

### Module dependency diagram

Arrows point from a required module to its consumer.

```mermaid
flowchart LR
    C[[contracts]] --> CFG[[config]]
    C --> P[[portfolio]]
    CFG --> P
    C --> S[[sizing]]
    CFG --> S
    P --> S
    C --> POL[[policy]]
    CFG --> POL
    P --> POL
    C --> R[[regimes]]
    CFG --> R
    P --> R
    C --> A[[audit]]
    CFG --> A
    C --> AP[[approvals]]
    CFG --> AP
    A --> AP
    C --> D[[decisions]]
    CFG --> D
    P --> D
    S --> D
    POL --> D
    R --> D
    A --> D
    AP --> D
    C --> SC[[scenarios]]
    CFG --> SC
    P --> SC
    C --> REP[[reporting]]
    D --> REP
    SC --> REP
    A --> REP
```

### Structure rules

- Package and feature `__init__.py` files contain explicit imports and `__all__` only.
- Root `__all__` exposes only versioned public contracts and typed domain operations; it exposes no calculator, persistence backend, signer, repository, or provider object.
- Functions are preferred for stateless behavior. `RiskGovernor`, `ApprovalTokenService`, and `RiskAuditChain` are classes because they own injected dependencies and coordinated state.
- `core/`, `api/`, `models/`, `simulation/`, `safety/`, generic `storage/`, generic `validators/`, and `workflows/` compatibility layers are not part of the target.
- No module imports Trading, MT5, a broker adapter, Data internals, or another domain's persistence implementation.
- Usage examples live only under `tests/risk/usage/`.

---

## 3. Workflows

### Status values

| Status | Meaning |
|---|---|
| **Missing** | Not implemented, incompatible with the target, or not verified. |
| **Partial** | Useful V1 behavior exists but contracts, relocation, validation, persistence, or tests remain. |
| **Completed** | Target behavior, location, callers, tests, and boundaries are all verified. |

### Workflow scope values

| Scope | Meaning |
|---|---|
| **Internal** | Complete inside Risk. |
| **Cross-domain** | Risk receives or returns a documented cross-domain contract. |

| Status | Workflow ID | Scope | Workflow | Trigger / Input boundary | Final outcome / Output boundary | Requirement sequence |
|---|---|---|---|---|---|---|
| Missing | `WF-RISK-001` | Internal with Data input | Build portfolio risk snapshot | Data/account and bounded market evidence | Risk-internal immutable `PortfolioRiskSnapshot` | `FR-RISK-004 → FR-RISK-005 → FR-RISK-025` |
| Missing | `WF-RISK-002` | Cross-domain | Calculate position size | Sizing request plus portfolio/symbol evidence | `PositionSizingResult`; never approval | `FR-RISK-007 → FR-RISK-008 → FR-RISK-026` |
| Missing | `WF-RISK-003` | Cross-domain | Assess risk regime | Bounded external market/context evidence | `RegimeAssessment` and limit modifiers | `FR-RISK-011 → FR-RISK-031` |
| Missing | `WF-RISK-004` | Cross-domain | Review proposed trade risk | `TradeIntent`, fresh evidence, config, governance state | `RiskDecision` v1 / `RiskDecisionPackage` | `FR-RISK-006 → FR-RISK-027 → FR-RISK-031 → FR-RISK-040` |
| Missing | `WF-RISK-005` | Cross-domain | Run current portfolio governor | Current snapshot, config, kill-switch evidence | Current-state `RiskDecisionPackage`; caller remediates | `FR-RISK-005 → FR-RISK-044 → FR-RISK-041` |
| Missing | `WF-RISK-006` | Cross-domain | Review strategy operational eligibility | Exact registered strategy/version, evidence, policy, route/profile, approval context | `StrategyOperationalEligibilityDecision v1` | `FR-RISK-010 → FR-RISK-029` |
| Missing | `WF-RISK-007` | Cross-domain | Review/activate allocation risk | Portfolio construction/rebalance reference plus fresh evidence and approval context | `AllocationRiskDecision v1` and budget activation result | `FR-RISK-009 → FR-RISK-030` |
| Missing | `WF-RISK-008` | Cross-domain | Validate approval token | Token, expected scope/action/config, injected time | Durable validation/consumption result | `FR-RISK-015 → FR-RISK-020 → FR-RISK-037` |
| Missing | `WF-RISK-009` | Cross-domain | Apply/check kill-switch state | Authorized command or current state and scope | Canonical state or block/recovery decision | `FR-RISK-016 → FR-RISK-043 → FR-RISK-017 → FR-RISK-044` |
| Missing | `WF-RISK-010` | Cross-domain | Run scenario or what-if analysis | Immutable snapshot and scenario definitions | Advisory `ScenarioResult` | `FR-RISK-012 → FR-RISK-013 → FR-RISK-045` |
| Missing | `WF-RISK-011` | Internal/Cross-domain | Generate risk decision summary | Snapshot, decision, or scenario result | Markdown/JSON `RiskReport` | `FR-RISK-019 → FR-RISK-046` |
| Missing | `WF-RISK-012` | Cross-domain | Persist risk audit and token state | Material decision/token event | Durable hash-chain/token state or fail-closed result | `FR-RISK-018 → FR-RISK-033 → FR-RISK-037` |
| Missing | `WF-RISK-014` | Cross-domain | Revalidate decision/evidence before reuse | Prior decision/token plus current evidence/config/time | Reuse validity result; refresh or block | `FR-RISK-042 → FR-RISK-037` |

### Workflow details

#### `WF-RISK-001` — Build portfolio risk snapshot

**System workflow:** Internal contribution to `SYS-WF-001` and `SYS-WF-002`.
**Input boundary:** `AccountStateSnapshot` v1 plus explicit position, pending-order, symbol, return-history, FX-conversion, and provenance evidence supplied by owning domains.
**Output boundary:** immutable `PortfolioRiskSnapshot` retained inside Risk for sizing,
limits, regime assessment, decision synthesis, scenarios, and reporting. Cross-domain
callers receive registered `RiskDecision` contracts or UI/API-owned views, never the
snapshot directly.

1. Validate contract versions, timestamps, numeric finiteness, and profile/config hash.
2. Normalize evidence without inventing missing values or mutating inputs.
3. Include pending exposure and calculate base-currency exposure, drawdown, margin/leverage, historical VaR/CVaR, correlation, and contributions where evidence is sufficient.
4. Return calculations, assumptions, coverage, missing-evidence markers, and provenance.

**Failure behaviour:** invalid input raises `RiskDomainError(INVALID_PORTFOLIO_STATE)`; missing material conversion/metadata remains explicit and blocks live-sensitive consumers; calculation failure never creates a synthetic safe value.
**Integration test:** `tests/risk/integration/test_build_portfolio_snapshot.py::test_build_portfolio_snapshot_from_external_evidence()`

#### `WF-RISK-002` — Calculate position size

**System workflow:** Internal contribution to `SYS-WF-001` and `SYS-WF-002`.
**Input boundary:** `PositionSizingRequest` (a Risk-internal type, not a registered cross-domain contract) plus portfolio, symbol, stop, broker-constraint, volatility/correlation, and performance evidence.
**Output boundary:** `PositionSizingResult` only (Risk-internal; cross-domain consumers receive sizing outcomes only inside `RiskDecision v1`).

The calculator supports fixed-lot, fixed-risk, milestone, fractional-Kelly, volatility, and fixed-fractional methods; it clamps or rejects against supplied constraints and never returns the V1 `0.1`-lot failure fallback. Missing stop distance, zero equity, insufficient volatility/Kelly evidence, or unapproved full Kelly produces a deterministic failure or an explicitly configured fixed-risk fallback.

**Integration test:** `tests/risk/integration/test_position_sizing.py::test_position_sizing_requires_governor_after_result()`

#### `WF-RISK-003` — Assess risk regime

**System workflow:** `SYS-WF-001`, `SYS-WF-002`
**Input boundary:** external volatility, liquidity, correlation, drawdown, crisis, news, and session evidence.
**Output boundary:** `RegimeAssessment` with transition evidence and configured tightening modifiers.

Unknown or required-missing regime evidence fails closed for live-sensitive workflows. Data supplies `MarketContextEvidence v1`; Risk profiles interpret it using a default stressed lookback of 252 trading days and named UTC crisis windows, without fetching or extrapolating evidence.

**Integration test:** `tests/risk/integration/test_regime_assessment.py::test_high_risk_regime_tightens_limits()`

#### `WF-RISK-004` — Review proposed trade risk

**System workflow:** `SYS-WF-001`, `SYS-WF-002`
**Input boundary:** Strategy `TradeIntent`, Data `AccountStateSnapshot`, external market/governance evidence, `AuthContext`, and validated config.
**Output boundary:** `RiskDecision` v1, concretely serialized as `RiskDecisionPackage`.

```mermaid
flowchart LR
    I[TradeIntent + evidence] --> V["Validate request, state, config"]
    V --> K["Kill-switch and freshness"]
    K --> R["Regime and ordered limits"]
    R --> C["Concurrent-capacity gate"]
    C --> A["Approval-token eligibility"]
    A --> D["RiskDecisionPackage"]
    D --> H["Audit-chain write"]
    H --> O[Trading or Simulation boundary]
```

The fixed precedence is validation/config → kill switch → missing/stale evidence → hard limits → policy restrictions → approval requirement → final verdict. Every material result includes `primary_failure_limit` and ordered `composite_breach_flags`. No forced/manual override is accepted.

**Failure behaviour:** any unknown safety state, unavailable mandatory audit/token state, or unresolved live double-spend protection blocks approval.
**Integration test:** `tests/risk/integration/test_trade_review.py::test_trade_review_uses_fixed_precedence_and_fails_closed()`

#### `WF-RISK-005` — Run current portfolio governor

**System workflow:** `SYS-WF-001`, `SYS-WF-002`, `SYS-WF-005`
**Input boundary:** current snapshot, config, regime, kill-switch, and governance evidence.
**Output boundary:** current-state compliance `RiskDecisionPackage`; Trading/UI/API owns remediation.

Risk detects breaches and recommends block/reduction/review without cancelling orders, closing positions, or changing execution controls.

**Integration test:** `tests/risk/integration/test_portfolio_governor.py::test_portfolio_governor_has_no_execution_side_effect()`

#### `WF-RISK-006` — Review strategy admission

**System workflow:** `SYS-WF-006`
**Input boundary:** `StrategyOperationalEligibilityRequest v1`, exact Strategy
registration reference, required Data evidence, policy, route/profile, and approval
context.
**Output boundary:** `StrategyOperationalEligibilityDecision v1`.

Risk approves, conditions, expires, suspends, or rejects operational use without
altering Strategy's registry. Registration alone never authorizes allocation or
execution; missing or stale evidence fails closed.

#### `WF-RISK-007` — Review allocation proposal

**System workflows:** `SYS-WF-007`, `SYS-WF-008`
**Input boundary:** `AllocationReviewRequest v1` carries a self-contained
Risk-owned projection of the immutable candidate or rebalance plan plus current
eligibility, account, market, FX, Analytics, policy, and approval evidence. The
projection contains only scalar values, ordered components, identifiers, versions,
references, and hashes; it never embeds or imports a Portfolio-owned contract.
**Output boundary:** `AllocationRiskDecision v1` and, after a valid
`AllocationBudgetActivationRequest v1`, the active authoritative risk-budget
projection.

Risk may approve, cap, condition, expire, or reject. It never constructs Portfolio
weights, activates Portfolio state, or executes a rebalance. Capital weights remain
Portfolio metadata; the Risk budget projection is the binding control.

#### `WF-RISK-008` — Validate approval token

**System workflow:** `SYS-WF-002`
**Input boundary:** token plus expected decision, action, account, strategy, symbol,
config, Risk-owned and UI/API-produced `ApprovalAttestation`, audit requirement, and injected time.
**Output boundary:** `ApprovalValidationResult`; caller proceeds only when valid and durably consumed.

Schema, HMAC-or-stronger signature, scope, decision/config binding, expiry,
revocation, nonce, single use, authorized attestation, and mandatory audit write are
checked atomically. Risk reserves token + workflow + action scope + expiry before a
live-success path; concurrent or conflicting reservation fails closed.

**Integration test:** `tests/risk/integration/test_approval_tokens.py::test_live_token_is_consumed_once_durably()`

#### `WF-RISK-009` — Apply or check kill-switch state

**System workflow:** `SYS-WF-005`
**Input boundary:** UI/API `KillSwitchCommand` with explicit scope level
(`global`, `portfolio`, `strategy`, or `symbol`) and applicable identifiers, plus a
separate `AuthContext`. Clearance also requires a matching current
`ApprovalAttestation`; activation does not.
**Output boundary:** canonical `KillSwitchState` and deterministic block/recovery decision consumed by Trading/UI/API.

Active or unknown state blocks live risk increase. `global` state overrides
`portfolio`, which overrides `strategy`, which overrides `symbol`; an inactive child cannot override an active
parent. Risk persists canonical state and revokes affected approvals; only Trading
mutates execution controls. Clearance requires a valid Risk-owned, UI/API-produced
`ApprovalAttestation`, and Trading resumes only after all applicable scopes are
inactive and reconciliation succeeds.

**Integration test:** `tests/risk/integration/test_kill_switch.py::test_kill_switch_command_blocks_trading_without_execution_mutation()`

#### `WF-RISK-010` — Run scenario or what-if analysis

**System workflow:** Cross-domain advisory result; no execution workflow is registered.
**Input boundary:** immutable snapshot plus bounded `ScenarioDefinition` values.
**Output boundary:** registered `ScenarioResult v1` advisory baseline/projected comparison.

No live state changes. Scenario output cannot claim approval and must pass through the canonical governor before any action.

**Integration test:** `tests/risk/integration/test_scenario_analysis.py::test_scenario_analysis_is_deterministic_and_advisory()`

#### `WF-RISK-011` — Generate risk decision summary

**System workflow:** `SYS-WF-001`, `SYS-WF-002`, `SYS-WF-005`
**Input boundary:** completed snapshot, decision, or scenario result.
**Output boundary:** focused Markdown/JSON `RiskReport`.

Evidence, calculations, assumptions, warnings, decisions, and recommendations are separated. Rejections/blocks identify the primary failure first. Live approval is claimed only when a valid decision and token are present.

**Integration test:** `tests/risk/integration/test_risk_reporting.py::test_report_separates_evidence_and_decision()`

#### `WF-RISK-012` — Persist risk audit and token state

**System workflow:** `SYS-WF-002`, `SYS-WF-005`
**Input boundary:** material decision, kill-switch, audit, or token event.
**Output boundary:** Risk-owned record persisted through Data-owned infrastructure or a fail-closed live result.

Canonical JSON and SHA-256-or-stronger hashing bind each record to `previous_hash`; genesis defaults to 64 zeroes unless deployment config specifies another constant. Partial writes, tamper, or mandatory-store unavailability block live-sensitive success.

**Integration test:** `tests/risk/integration/test_risk_persistence.py::test_audit_and_token_state_fail_closed_atomically()`

#### `WF-RISK-014` — Revalidate decision/evidence before reuse

**System workflow:** `SYS-WF-001`, `SYS-WF-002`
**Input boundary:** prior decision/token plus current proposal, evidence, config, and injected time.
**Output boundary:** reusable/refresh-required/blocked validation result.

Material scope change, expiry, clock skew, stale evidence, config mismatch, in-flight reconciliation expiry, revoked token, or consumed token invalidates reuse.

**Integration test:** `tests/risk/integration/test_decision_revalidation.py::test_material_change_requires_new_decision()`

---

## 4. Module and Requirement Specifications

Requirements are ordered by implementation dependency. Each public symbol appears in exactly one `FR-RISK-*` row.
Manifest identifiers are configuration fields or private implementation constants unless a file's `Key exports` explicitly lists them; they do not create additional public symbols.
Shortened test references are relative to the module's documented `tests/risk/usage/test_usage_*.py` file or to `tests/risk/unit/`; together with the module's `Usage file` line they identify one exact pytest node.

### 4.1 `contracts/` — Versioned Contracts and Deterministic Errors

**Purpose:** Define strict Pydantic V2 contracts, exact Decimal serialization, canonical enums, and one coded domain exception without business I/O.

**Module flow:** `untrusted mapping → strict contract/version/finite-value validation → immutable typed value or coded error`

#### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `enums.py` | Canonical stable enum values | `DecisionState`, `LimitStatus`, `RiskErrorCode` | **Standard library:** enum<br>**Required third-party:** None<br>**Local:** None |
| Missing | `errors.py` | Coded domain exception | `RiskDomainError` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `enums.py → RiskErrorCode` |
| Missing | `evidence.py` | Immutable normalized portfolio evidence and compatibility validation for Data-owned market-context evidence | `PortfolioState`, `PortfolioRiskSnapshot`, `validate_market_context_evidence` | **Standard library:** datetime, decimal<br>**Required third-party:** pydantic 2.13.4<br>**Local:** `enums.py → LimitStatus`; Data public API → `MarketContextEvidence` |
| Missing | `requests.py` | Versioned Risk-owned request contracts | `ProposedTrade`, `PositionSizingRequest`, `ProposedAllocation`, `StrategyAdmissionRequest`, `ScenarioDefinition`, `KillSwitchCommand` | **Standard library:** datetime, decimal<br>**Required third-party:** pydantic 2.13.4<br>**Local:** `enums.py → DecisionState` |
| Missing | `results.py` | Versioned Risk-owned result/state contracts | `RiskLimitResult`, `PositionSizingResult`, `RegimeAssessment`, `ScenarioResult`, `RiskDecisionPackage`, `ActionPolicyVerdict`, `RiskApprovalToken`, `KillSwitchState`, `RiskAuditRecord`, `RiskReport`, `ApprovalValidationResult` | **Standard library:** datetime, decimal<br>**Required third-party:** pydantic 2.13.4<br>**Local:** `enums.py`, `evidence.py`, `requests.py` |
| Missing | `__init__.py` | Expose the approved contract API | All symbols above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** files above |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `SCHEMA_VERSION` | `str` | `v1` | Yes | Every public model | Reject unsupported breaking contract versions. |
| Missing | `DECIMAL_ROUNDING` | rounding mode | `ROUND_HALF_EVEN` | Yes | Monetary/sizing validators | Different mode requires an approved profile. |
| Missing | `ALLOW_INF_NAN` | `bool` | `False` | Yes | Every public model | Non-finite values are rejected. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-001` | Define `approve`, `warn`, `needs_approval`, `needs_more_evidence`, `reject`, `block`, and `error` exactly. | `DecisionState` | None | None | **Usage:** `tests/risk/usage/test_usage_contracts.py::test_usage_enums_decision_state()`<br>**Unit:** `tests/risk/unit/test_enums.py::test_decision_state_values_are_stable()` |
| Missing | `FR-RISK-002` | Define `pass`, `warn`, `needs_more_evidence`, `fail`, and `blocked` exactly. | `LimitStatus` | None | None | **Usage:** `test_usage_contracts.py::test_usage_enums_limit_status()`<br>**Unit:** `test_enums.py::test_limit_status_values_are_stable()` |
| Missing | `FR-RISK-003` | Define every accepted deterministic Risk error code; historical VaR/CVaR is the sole supported VaR method. | `RiskErrorCode` | None | None | **Usage:** `test_usage_contracts.py::test_usage_errors_codes()`<br>**Unit:** `test_errors.py::test_error_code_catalog()` |
| Missing | `FR-RISK-004` | Carry immutable account/position/pending-order/symbol/market evidence with UTC `as_of`, provenance, missingness, and schema version. | `PortfolioState` | None | `ValidationError`: invalid version, naive time, non-finite Decimal, or malformed evidence | **Usage:** `test_usage_contracts.py::test_usage_evidence_portfolio_state()`<br>**Unit:** `test_evidence.py::test_portfolio_state_preserves_missingness()` |
| Missing | `FR-RISK-005` | Carry reproducible base-currency metrics, limit results, assumptions, coverage, regime, request/workflow IDs, evidence refs, and config hash. | `PortfolioRiskSnapshot` | None | `ValidationError`: invalid or non-finite result | **Usage:** `test_usage_contracts.py::test_usage_evidence_portfolio_snapshot()`<br>**Unit:** `test_evidence.py::test_snapshot_serializes_decimal_exactly()` |
| Missing | `FR-RISK-058` | Validate the consumed Data-owned `MarketContextEvidence v1` version, UTC freshness, provenance, bounded values, and explicit missingness without redefining or fetching it. | `validate_market_context_evidence(evidence: MarketContextEvidence, *, now: datetime) -> None` | None | `RiskDomainError(MISSING_EVIDENCE, STALE_EVIDENCE, VALIDATION_FAILED)`: incompatible, stale, or malformed evidence | **Usage:** `test_usage_contracts.py::test_usage_evidence_market_context()`<br>**Unit:** `test_evidence.py::test_market_context_uses_data_owned_contract()` |
| Missing | `FR-RISK-059` | Return `ActionPolicyVerdict v1` bound to action, scope, policy version, approval attestation, decision, reservation, expiry, reasons, and trace IDs. | `ActionPolicyVerdict` | None | `ValidationError`: inconsistent, unbound, or non-UTC verdict | **Usage:** `test_usage_contracts.py::test_usage_results_action_policy()`<br>**Unit:** `test_results.py::test_action_policy_verdict_requires_reservation()` |
| Missing | `FR-RISK-060` | Carry one ordered limit result with status, observed/threshold values, reason code, evidence refs, and precedence without granting approval. | `RiskLimitResult` | None | `ValidationError`: inconsistent status/reason or non-finite value | **Usage:** `test_usage_contracts.py::test_usage_results_limit()`<br>**Unit:** `test_results.py::test_limit_result_invariants()` |
| Missing | `FR-RISK-006` | Represent one non-executable risk-increasing proposal with intent reference, scope, direction, requested size, price/stop evidence, validity, and provenance. | `ProposedTrade` | None | `ValidationError`: invalid size/scope or required stop evidence absent | **Usage:** `test_usage_contracts.py::test_usage_requests_proposed_trade()`<br>**Unit:** `test_requests.py::test_proposed_trade_requires_fixed_risk_stop()` |
| Missing | `FR-RISK-007` | Represent one of six sizing methods and its complete evidence/config references. | `PositionSizingRequest` | None | `ValidationError`: unknown method or incomplete method evidence | **Usage:** `test_usage_contracts.py::test_usage_requests_sizing()`<br>**Unit:** `test_requests.py::test_sizing_request_is_method_strict()` |
| Missing | `FR-RISK-008` | Return exact requested/normalized size, constraints applied, evidence gaps, fallback disclosure, and no approval claim. | `PositionSizingResult` | None | `ValidationError`: non-finite result | **Usage:** `test_usage_contracts.py::test_usage_results_sizing()`<br>**Unit:** `test_results.py::test_sizing_result_cannot_claim_approval()` |
| Missing | `FR-RISK-009` | Validate and review `AllocationReviewRequest v1` without constructing or applying a Portfolio allocation. | `review_allocation_proposal` | None | Structured rejection on missing/stale/incompatible evidence | **Verification:** `SYS-WF-007`/`SYS-WF-008` compatibility tests. |
| Missing | `FR-RISK-010` | Validate `StrategyOperationalEligibilityRequest v1` for an exact registered strategy/version and scope. | `review_strategy_admission` | None | Structured rejection on registration/evidence/policy failure | **Verification:** `SYS-WF-006` compatibility test. |
| Missing | `FR-RISK-011` | Return classified volatility/liquidity/correlation/drawdown/crisis/news/session states, transition evidence, modifiers, and missingness. | `RegimeAssessment` | None | `ValidationError`: invalid regime value | **Usage:** `test_usage_contracts.py::test_usage_results_regime()`<br>**Unit:** `test_results.py::test_regime_assessment_carries_transition()` |
| Missing | `FR-RISK-012` | Define a bounded immutable advisory scenario with deterministic shocks and optional explicit seed. | `ScenarioDefinition` | None | `ValidationError`: unsupported/non-finite shock or unseeded randomness | **Usage:** `test_usage_contracts.py::test_usage_requests_scenario()`<br>**Unit:** `test_requests.py::test_scenario_requires_seed_if_randomized()` |
| Missing | `FR-RISK-013` | Return baseline/projected risk comparison and state that the output is advisory and not approved. | `ScenarioResult` | None | `ValidationError`: invalid projection | **Usage:** `test_usage_contracts.py::test_usage_results_scenario()`<br>**Unit:** `test_results.py::test_scenario_result_is_advisory()` |
| Missing | `FR-RISK-014` | Implement `RiskDecision` v1 with verdict, approved size, ordered checks, primary/composite reasons, provenance, expiry, concurrency disclosure, and optional token. | `RiskDecisionPackage` | None | `ValidationError`: inconsistent verdict/token or missing provenance | **Usage:** `test_usage_contracts.py::test_usage_results_decision()`<br>**Unit:** `test_results.py::test_decision_package_invariants()` |
| Missing | `FR-RISK-015` | Carry signed token scope, decision/config hashes, approver, expiry, nonce, schema version, and no secret key. | `RiskApprovalToken` | None | `ValidationError`: incomplete or non-UTC token | **Usage:** `test_usage_contracts.py::test_usage_results_token()`<br>**Unit:** `test_results.py::test_token_contract_has_required_bindings()` |
| Missing | `FR-RISK-016` | Implement `KillSwitchCommand v1` with action, explicit scope level, applicable portfolio/strategy/symbol identifiers, reason, UTC timestamp, request/workflow/correlation IDs, and schema identity. Principal authorization remains in the separate `AuthContext`; clearance requires a separate matching current `ApprovalAttestation`. | `KillSwitchCommand` | None | `ValidationError`: invalid action, scope, identifiers, time, or trace identity | **Usage:** `test_usage_contracts.py::test_usage_requests_kill_switch()`<br>**Unit:** `test_requests.py::test_kill_switch_command_requires_scope_and_reason()` |
| Missing | `FR-RISK-017` | Implement `KillSwitchState` v1 with scope, active/unknown state, reason, version, and UTC update time. | `KillSwitchState` | None | `ValidationError`: invalid transition data | **Usage:** `test_usage_contracts.py::test_usage_results_kill_switch()`<br>**Unit:** `test_results.py::test_kill_switch_unknown_is_representable()` |
| Missing | `FR-RISK-018` | Carry canonical redacted audit payload, evidence/config/decision provenance, sequence, previous hash, and record hash. | `RiskAuditRecord` | None | `ValidationError`: secret-like field, invalid hash, or incomplete provenance | **Usage:** `test_usage_contracts.py::test_usage_results_audit()`<br>**Unit:** `test_results.py::test_audit_record_redacts_secrets()` |
| Missing | `FR-RISK-019` | Carry Markdown or exact JSON summary with separated evidence, assumptions, warnings, decision, and recommendations. | `RiskReport` | None | `ValidationError`: invalid format or false approval state | **Usage:** `test_usage_contracts.py::test_usage_results_report()`<br>**Unit:** `test_results.py::test_report_contract_separates_sections()` |
| Missing | `FR-RISK-020` | Return token validity, consumption state, reason code, and audit reference without exposing secrets. | `ApprovalValidationResult` | None | `ValidationError`: inconsistent valid/reason state | **Usage:** `test_usage_contracts.py::test_usage_results_token_validation()`<br>**Unit:** `test_results.py::test_validation_result_invariants()` |
| Missing | `FR-RISK-021` | Raise one redacted domain exception carrying a `RiskErrorCode` and safe details for boundary mapping. | `RiskDomainError(code: RiskErrorCode, details: str)` | None | None | **Usage:** `test_usage_contracts.py::test_usage_errors_domain_error()`<br>**Unit:** `test_errors.py::test_domain_error_redacts_details()` |

**Rules and implementation notes:**

- Pydantic models use strict mode, `extra="forbid"`, `allow_inf_nan=False`, UTC-aware timestamps, immutable public results, and exact Decimal-to-string JSON serialization.
- Keep useful V1 contract semantics but merge duplicate `domain/models` types; no compatibility namespace is canonical.
- `RiskErrorCode` includes `INVALID_INPUT`, `INVALID_PORTFOLIO_STATE`, `INVALID_RISK_CONFIG`, `MISSING_EVIDENCE`, `STALE_EVIDENCE`, `LIMIT_FAILED`, `POLICY_BLOCKED`, `PERMISSION_DENIED`, `KILL_SWITCH_ACTIVE`, `KILL_SWITCH_UNKNOWN`, `APPROVAL_REQUIRED`, token invalid/expired/revoked/consumed codes, config mismatch codes, `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`, `PAYLOAD_TOO_LARGE`, sizing/evidence codes, `LIVE_STATE_STALE`, `IN_FLIGHT_TOLERANCE_EXCEEDED`, `IN_FLIGHT_RECONCILIATION_EXPIRED`, `AUDIT_CHAIN_TAMPER_DETECTED`, `CALCULATION_FAILED`, `SNAPSHOT_BUILD_FAILED`, `GOVERNOR_DECISION_FAILED`, `REPORT_GENERATION_FAILED`, `STORAGE_ERROR`, `TOOL_EXECUTION_FAILED`, and `UNKNOWN_ERROR`.

**Usage file:** `tests/risk/usage/test_usage_contracts.py`

### 4.2 `config/` — Risk Profiles and Stable Configuration

**Purpose:** Load, validate, select, and hash profile-driven Risk configuration without inventing trading thresholds.

**Module flow:** `configs/risk/*.yaml → strict RiskConfig → canonical JSON → config hash`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `profiles.py` | Profile contract, load/validation, and hashing | `RiskConfig`, `load_risk_config`, `compute_config_hash` | **Standard library:** hashlib, json, pathlib<br>**Required third-party:** pydantic 2.13.4; PyYAML 6.0.3 (lockfile; direct declaration Pending)<br>**Local:** `contracts` |
| Missing | `__init__.py` | Expose config API | symbols above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `profiles.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `RISK_PROFILE` | `str` | `research` | Yes | `load_risk_config()` | Selects an approved profile; missing live profile fails closed. |
| Missing | `CONFIG_ROOT` | `Path` | `configs/risk` | Yes | `load_risk_config()` | Path is bounded and may not escape the approved root. |
| Missing | `PENDING_ORDER_EXPOSURE_POLICY` | enum | None | Live: Yes | snapshot/governor | Missing policy with pending orders blocks review. |
| Missing | `EVIDENCE_MAX_AGE_SECONDS` | mapping | None | Live: Yes | snapshot/governor/token validity | No default is invented; stale evidence fails closed. |
| Missing | `CLOCK_SKEW_TOLERANCE_SECONDS` | `Decimal` | None | Live: Yes | validity/token checks | Exceeding tolerance invalidates evidence/token. |
| Missing | `AUDIT_PERSISTENCE_REQUIRED` | `bool` | `True` for live | Yes | governor/audit/token | Mandatory-store failure blocks live success. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-022` | Define strict profile fields, thresholds, modes, freshness, rounding, concurrency, audit, and dependency timeouts with stable schema version. | `RiskConfig` | None | `ValidationError`: missing/invalid values | **Usage:** `tests/risk/usage/test_usage_config.py::test_usage_profiles_config()`<br>**Unit:** `tests/risk/unit/test_profiles.py::test_live_profile_requires_all_safety_values()` |
| Missing | `FR-RISK-023` | Load only the selected YAML profile from the bounded root and fail closed on missing/invalid live configuration. | `load_risk_config(profile: str, config_root: Path) -> RiskConfig` | Read-only | `RiskDomainError(INVALID_RISK_CONFIG)`: file/schema/path failure | **Usage:** `test_usage_config.py::test_usage_profiles_load()`<br>**Unit:** `test_profiles.py::test_missing_live_profile_fails_closed()` |
| Missing | `FR-RISK-024` | Hash canonical exact serialization so any material config change changes the SHA-256 hash. | `compute_config_hash(config: RiskConfig) -> str` | None | `RiskDomainError(INVALID_RISK_CONFIG)`: canonicalization failure | **Usage:** `test_usage_config.py::test_usage_profiles_hash()`<br>**Unit:** `test_profiles.py::test_config_hash_is_stable_and_sensitive()` |

**Rules and implementation notes:**

- Preserve V1 threshold/hash logic only after consolidation; remove hidden defaults and direct environment/provider reads.
- Numeric risk limits are owner policy. This README records only reconciliation-approved baselines; live values remain profile-required where semantics or owner approval is absent.

**Usage file:** `tests/risk/usage/test_usage_config.py`

### 4.3 `portfolio/` — Evidence Normalization and Portfolio Risk Snapshot

**Purpose:** Produce one immutable, reproducible snapshot from supplied evidence using private deterministic calculators.

**Module flow:** `PortfolioState + RiskConfig → validate/normalize → exposure/drawdown/margin/historical tail risk/correlation → PortfolioRiskSnapshot`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `snapshot.py` | Normalize evidence and calculate the canonical snapshot | `build_portfolio_risk_snapshot` | **Standard library:** datetime, decimal, math, statistics<br>**Required third-party:** None<br>**Local:** `contracts`, `config` |
| Missing | `__init__.py` | Expose snapshot API | `build_portfolio_risk_snapshot` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `snapshot.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `VAR_METHOD` | enum | `historical` | Yes | `build_portfolio_risk_snapshot()` | Parametric methods are excluded initially. |
| Missing | `VAR_CONFIDENCE` | `Decimal` | `0.95` | Yes | snapshot | Outside (0,1) is invalid. |
| Missing | `VAR_MIN_OBSERVATIONS` | `int` | None | Live: Yes | snapshot | Insufficient data returns missing evidence; missing live config is invalid. |
| Missing | `VAR_LOOKBACK` | `int` | None | Yes | snapshot | Must be documented in assumptions/coverage. |
| Missing | `MAX_CORRELATION` | `Decimal` | `0.50` FX baseline | Yes | snapshot/policy | Breach becomes an ordered limit result. |
| Missing | `PSD_POLICY` | enum | None | Yes | snapshot | Deterministically sanitize or reject a non-PSD matrix. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-025` | Build an immutable snapshot containing pending-order-aware gross/net exposure by dimension, account-currency conversions, drawdown/loss state, margin/leverage, volatility, historical VaR/CVaR, pair/portfolio correlation, incremental contribution, assumptions, coverage, and explicit gaps. | `build_portfolio_risk_snapshot(state: PortfolioState, config: RiskConfig, *, now: datetime) -> PortfolioRiskSnapshot` | None | `RiskDomainError(INVALID_PORTFOLIO_STATE, MISSING_EVIDENCE, SNAPSHOT_BUILD_FAILED)`: corresponding condition | **Usage:** `tests/risk/usage/test_usage_portfolio.py::test_usage_snapshot_build()`<br>**Unit:** `tests/risk/unit/test_snapshot.py::test_snapshot_includes_pending_and_conversion_evidence()` |

**Rules and implementation notes:**

- Reuse V1 state normalization, exposure, drawdown, margin, historical VaR/CVaR, covariance, contribution math, and decision-relevant metric/score aggregation after Decimal/evidence refactoring; merge scores into snapshot/decision summaries without a public registry or recommendation engine.
- Never fetch broker/market data, infer contract size/pip value/conversion rates, return infinity, or mutate source evidence.
- Monthly-target fields are excluded from the public Risk contract; stressed crisis calculations fail closed rather than using ordinary lookbacks.

**Usage file:** `tests/risk/usage/test_usage_portfolio.py`

### 4.4 `sizing/` — Position Sizing Recommendations

**Purpose:** Calculate deterministic, evidence-driven position sizing without granting trade approval.

**Module flow:** `PositionSizingRequest + snapshot + constraints → method calculation → normalization/caps → PositionSizingResult`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `calculator.py` | Execute the six approved sizing methods | `calculate_position_size` | **Standard library:** decimal<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio` |
| Missing | `__init__.py` | Expose sizing API | `calculate_position_size` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `calculator.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `MIN_KELLY_TRADES` | `int` | `30` | Kelly: Yes | `calculate_position_size()` | Fewer observations emit `INSUFFICIENT_K_EVIDENCE`. |
| Missing | `FRACTIONAL_KELLY_MULTIPLIER` | `Decimal` | None | Kelly: Yes | calculator | Every approved profile must provide an explicit value; no system default exists. |
| Missing | `ALLOW_FULL_KELLY` | `bool` | `False` | Yes | calculator | Full Kelly requires a documented waiver. |
| Missing | `KELLY_INSUFFICIENT_EVIDENCE_MODE` | enum | None | Kelly: Yes | calculator | Either reject or explicit fixed-risk fallback. |
| Missing | `CORRELATION_SIZE_PENALTY` | enum/config | None | If enabled | calculator | Missing correlation evidence cannot silently apply no penalty. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-026` | Calculate fixed-lot, fixed-risk, milestone, fractional-Kelly, volatility, or fixed-fractional size; enforce stop/equity/evidence rules; disclose fallback/correlation adjustment; normalize against explicit broker and risk constraints; return no non-zero failure fallback and no approval. | `calculate_position_size(request: PositionSizingRequest, snapshot: PortfolioRiskSnapshot, config: RiskConfig) -> PositionSizingResult` | None | `RiskDomainError(MISSING_STOP_LOSS, INSUFFICIENT_VOLATILITY_EVIDENCE, INSUFFICIENT_K_EVIDENCE, CALCULATION_FAILED)`: corresponding condition | **Usage:** `tests/risk/usage/test_usage_sizing.py::test_usage_calculator_position_size()`<br>**Unit:** `tests/risk/unit/test_calculator.py::test_all_six_methods_and_no_point_one_fallback()` |

**Implementation notes:** Refactor V1 `PositionSizer` formulas; remove provider reads, float arithmetic, inferred stop distance, full-Kelly default, and catch-all `0.1` result.

**Usage file:** `tests/risk/usage/test_usage_sizing.py`

### 4.5 `policy/` — Limits, Market Context, Admission, and Allocation Gates

**Purpose:** Evaluate deterministic configured constraints and return ordered results without execution or lifecycle authority.

**Module flow:** `typed evidence + config → focused checks → ordered limit/decision package`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `limits.py` | Portfolio and external market-context limit evaluation | `evaluate_portfolio_limits`, `evaluate_market_context` | **Standard library:** datetime, decimal<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio` |
| Missing | `admission.py` | Strategy admission/demotion risk gate | `review_strategy_admission` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio` |
| Missing | `allocation.py` | Allocation constraint review | `review_allocation_proposal` | **Standard library:** decimal<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio` |
| Missing | `__init__.py` | Expose policy API | symbols above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** files above |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `MAX_DAILY_LOSS` | `Decimal` | `0.05` baseline | Yes | portfolio limits | Equity base must be explicit; breach fails. |
| Missing | `MAX_TOTAL_LOSS` | `Decimal` | `0.10` baseline | Yes | portfolio limits | Breach fails/blocks by profile. |
| Missing | `MONTHLY_TARGET` | `Decimal` | `0.10` baseline | Optional | portfolio limits | Non-production until reset/accounting semantics resolve. |
| Missing | `MAX_MARGIN_UTILIZATION` | `Decimal` | None | Live: Yes | portfolio limits | Missing metadata/config blocks live review. |
| Missing | `MAX_EFFECTIVE_LEVERAGE` | `Decimal` | None | Live: Yes | portfolio limits | Breach fails. |
| Missing | `MAX_SPREAD` | mapping | None | Profile-defined | market context | Breach fails/warns per policy. |
| Missing | `NEWS_BLACKOUT_BEFORE_MINUTES` / `AFTER` | `int` | `10` / `10` baseline | If enabled | market context | Applies only to supplied calendar evidence. |
| Missing | `MISSING_CALENDAR_MODE` | enum | None | Live if rule enabled | market context | `ignore`, `warn`, `needs_more_evidence`, or `block`. |
| Missing | `SESSION_TIMEZONE` | IANA timezone | None | If enabled | market context | Conversion failure blocks live review. |
| Missing | Allocation/strategy/symbol/cluster caps | `Decimal` mappings | None | Allocation review: Yes | allocation | No numeric cap is invented. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-027` | Evaluate daily/total loss, drawdown state, consistency, exposure/concentration, margin/leverage, historical tail risk, correlation, and freshness in deterministic precedence, returning primary and composite failures. | `evaluate_portfolio_limits(snapshot: PortfolioRiskSnapshot, config: RiskConfig) -> tuple[RiskLimitResult, ...]` | None | `RiskDomainError(INVALID_RISK_CONFIG, MISSING_EVIDENCE, LIMIT_FAILED)` | **Usage:** `tests/risk/usage/test_usage_policy.py::test_usage_limits_portfolio()`<br>**Unit:** `tests/risk/unit/test_limits.py::test_limit_order_and_composite_failures()` |
| Missing | `FR-RISK-028` | Evaluate supplied spread, slippage, liquidity, session, and calendar evidence without external fetches or naive/aware datetime comparison. | `evaluate_market_context(evidence: MarketContextEvidence, config: RiskConfig, *, now: datetime) -> tuple[RiskLimitResult, ...]` | None | `RiskDomainError(MISSING_EVIDENCE, POLICY_BLOCKED)` | **Usage:** `test_usage_policy.py::test_usage_limits_market_context()`<br>**Unit:** `test_limits.py::test_timezone_failure_blocks_live()` |
| Missing | `FR-RISK-029` | Produce and persist `StrategyOperationalEligibilityDecision v1` with exact scope, conditions, evidence/policy lineage, issue/expiry, and suspension semantics; never mutate Strategy state. | `review_strategy_admission` | Risk decision/audit stores | Structured fail-closed error | **Verification:** eligibility contract and persistence tests. |
| Missing | `FR-RISK-030` | Produce `AllocationRiskDecision v1`, enforce caps, and atomically activate the authoritative risk-budget projection only for the exact approved Portfolio version. | `review_allocation_proposal`, budget activation API | Risk budget/audit stores | Version/expiry/kill-switch conflict blocks activation | **Verification:** allocation and concurrency tests. |

**Implementation notes:** Merge V1 limit/policy calculations; do not preserve root check wrappers, `AllocationService`, lifecycle mutation, forced decisions, or policy-manager layers.

**Usage file:** `tests/risk/usage/test_usage_policy.py`

### 4.6 `regimes/` — Regime Assessment and Limit Tightening

**Purpose:** Classify supplied market/risk context and derive deterministic stricter limit modifiers.

**Module flow:** `PortfolioRiskSnapshot + MarketContextEvidence + RiskConfig → classify/transition → RegimeAssessment`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `assessment.py` | Regime classification, transitions, and modifiers | `assess_risk_regime` | **Standard library:** datetime, decimal<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio` |
| Missing | `__init__.py` | Expose regime API | `assess_risk_regime` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `assessment.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `REGIME_ASSESSMENT_ENABLED` | `bool` | Profile-defined | Yes | `assess_risk_regime()` | Disabled state is explicit. |
| Missing | Regime thresholds/modifiers | mapping | None | If enabled | assessment | High-risk modifiers may only tighten limits. |
| Missing | Stressed evidence/lookback policy | contract/config | No shared default | Crisis live: Yes | Every crisis-live profile must supply and validate an explicit stressed evidence/lookback policy; omission blocks assessment. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-031` | Classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes; record deterministic transitions/evidence; return only equal-or-stricter modifiers; fail closed on required missing/unknown live evidence. | `assess_risk_regime(snapshot: PortfolioRiskSnapshot, evidence: MarketContextEvidence, config: RiskConfig, *, now: datetime) -> RegimeAssessment` | None | `RiskDomainError(MISSING_EVIDENCE, STALE_EVIDENCE, CALCULATION_FAILED)` | **Usage:** `tests/risk/usage/test_usage_regimes.py::test_usage_assessment_regime()`<br>**Unit:** `tests/risk/unit/test_assessment.py::test_high_risk_modifiers_only_tighten()` |

**Implementation notes:** Reuse V1 detectors/transition logic; do not silently use ordinary lookbacks where stressed evidence is required.

**Usage file:** `tests/risk/usage/test_usage_regimes.py`

### 4.7 `audit/` — Tamper-Evident Risk Audit Boundary

**Purpose:** Canonically serialize, hash-chain, verify, and persist Risk-owned records through Data-owned infrastructure.

**Module flow:** `material Risk event → redaction/canonical JSON → previous-hash chain → durable append/verification`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `storage.py` | Private injected persistence Protocol; no public export | None | **Standard library:** typing<br>**Required third-party:** None<br>**Local:** `contracts` |
| Missing | `chain.py` | Stateful audit-chain coordination | `RiskAuditChain`, `RiskAuditChain.append`, `RiskAuditChain.verify` | **Standard library:** collections.abc, datetime, hashlib<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, private storage port |
| Missing | `migrations.py` | Risk-owned table/index migration definitions | None | **Standard library:** None<br>**Required third-party:** None<br>**Local:** None |
| Missing | `__init__.py` | Expose audit coordinator only | `RiskAuditChain` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `chain.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `AUDIT_HASH_ALGORITHM` | `str` | `sha256` | Yes | `RiskAuditChain` | Must be SHA-256 or stronger. |
| Missing | `AUDIT_GENESIS_HASH` | `str` | 64 zeroes | Yes | chain | Deterministic deployment constant. |
| Missing | `AUDIT_TIMEOUT_SECONDS` | `Decimal` | None | Live: Yes | append/verify | Timeout blocks mandatory live persistence. |
| Missing | `AUDIT_RETRY_POLICY` | config | None | Yes | append | Only idempotent writes retry; exhaustion is surfaced. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-032` | Own injected canonical serializer, clock, storage port, and deterministic chain configuration without owning database infrastructure. | `RiskAuditChain(config: RiskConfig, store: _RiskAuditStore, clock: Callable[[], datetime])` | Local state mutation | `RiskDomainError(INVALID_RISK_CONFIG)` | **Usage:** `tests/risk/usage/test_usage_audit.py::test_usage_chain_create()`<br>**Unit:** `tests/risk/unit/test_chain.py::test_chain_requires_deterministic_genesis()` |
| Missing | `FR-RISK-033` | Redact, canonicalize, hash, and durably append a material record with previous-hash continuity. | `RiskAuditChain.append(record: RiskAuditRecord) -> RiskAuditRecord` | Persistence write | `RiskDomainError(STORAGE_ERROR)`: partial/unavailable/permission failure | **Usage:** `test_usage_audit.py::test_usage_chain_append()`<br>**Unit:** `test_chain.py::test_append_hashes_and_fails_closed()` |
| Missing | `FR-RISK-034` | Verify genesis, sequence, previous hash, and record hash; identify tamper deterministically. | `RiskAuditChain.verify(records: Sequence[RiskAuditRecord]) -> bool` | Read-only | `RiskDomainError(AUDIT_CHAIN_TAMPER_DETECTED, STORAGE_ERROR)` | **Usage:** `test_usage_audit.py::test_usage_chain_verify()`<br>**Unit:** `test_chain.py::test_verify_detects_tamper()` |

**Implementation notes:** Refactor focused V1 audit/signature behavior; remove generic repository hierarchy and broad audit/report ownership.

**Usage file:** `tests/risk/usage/test_usage_audit.py`

### 4.8 `approvals/` — Durable Approval-Token Lifecycle

**Purpose:** Issue, validate, consume, revoke, and invalidate signed scoped tokens through durable state.

**Module flow:** `eligible decision + authenticated approver → signed/scoped token → durable state/audit → atomic validation/consumption or revocation`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `state.py` | Private durable token-state Protocol; no public export | None | **Standard library:** typing<br>**Required third-party:** None<br>**Local:** `contracts` |
| Missing | `tokens.py` | Coordinated signing and durable lifecycle | `ApprovalTokenService` and its public methods | **Standard library:** collections.abc, datetime, hashlib, hmac, secrets<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `audit`, private state port |
| Missing | `__init__.py` | Expose token coordinator | `ApprovalTokenService` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `tokens.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `APPROVAL_TOKEN_TTL_SECONDS` | `Decimal` | None | Yes | issue/validate | Expired tokens fail deterministically. |
| Missing | `APPROVAL_SIGNING_KEY_REF` | secret reference | None | Yes | issue/validate | Secret value is never logged or serialized. |
| Missing | `APPROVAL_SIGNING_ALGORITHM` | `str` | HMAC-SHA-256 minimum | Yes | service | Weaker algorithms are invalid. |
| Missing | `TOKEN_STATE_TIMEOUT_SECONDS` | `Decimal` | None | Live: Yes | validate/revoke | Unavailable backend fails closed. |
| Missing | Config compatibility policy | exact hash-pair/scope/expiry rules | deny | Yes | validate | Unapproved config mismatch fails closed. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-035` | Own injected signer/secret resolver, clock, durable state port, authorization verifier, and audit chain. | `ApprovalTokenService(config: RiskConfig, state: _TokenStateStore, audit: RiskAuditChain, clock: Callable[[], datetime])` | Local state mutation | `RiskDomainError(INVALID_RISK_CONFIG, STORAGE_ERROR)` | **Usage:** `tests/risk/usage/test_usage_approvals.py::test_usage_tokens_create_service()`<br>**Unit:** `tests/risk/unit/test_tokens.py::test_service_never_exposes_key()` |
| Missing | `FR-RISK-036` | Validate Risk-owned, UI/API-produced `ApprovalAttestation v1`, then issue a tamper-evident token only for an eligible decision, binding request/workflow/action/account/strategy/symbol/config/decision/approver/expiry/nonce and writing audit/state durably. | `ApprovalTokenService.issue(decision: RiskDecisionPackage, attestation: ApprovalAttestation, *, now: datetime) -> RiskApprovalToken` | Persistence write | `RiskDomainError(APPROVAL_REQUIRED, PERMISSION_DENIED, STORAGE_ERROR)` | **Usage:** `test_usage_approvals.py::test_usage_tokens_issue()`<br>**Unit:** `test_tokens.py::test_issue_requires_valid_ui_approval_attestation()` |
| Missing | `FR-RISK-037` | Atomically verify schema/signature/scope/hashes/attestation/time/revocation/nonce, reserve token + workflow + action scope + expiry, persist single-use consumption before live success, and audit the result. | `ApprovalTokenService.validate_reserve_and_consume(token: RiskApprovalToken, attestation: ApprovalAttestation, expected: Mapping[str, str], *, now: datetime) -> ApprovalValidationResult` | Persistence write | `RiskDomainError(APPROVAL_TOKEN_INVALID, APPROVAL_TOKEN_EXPIRED, APPROVAL_TOKEN_REVOKED, APPROVAL_TOKEN_CONSUMED, PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED, CONFIG_VERSION_MISMATCH, STORAGE_ERROR)` | **Usage:** `test_usage_approvals.py::test_usage_tokens_validate()`<br>**Unit:** `test_tokens.py::test_concurrent_reservation_succeeds_once()` |
| Missing | `FR-RISK-038` | Revoke every outstanding token intersecting an activated global/portfolio/strategy/symbol scope and write a material audit event. | `ApprovalTokenService.revoke_scope(scope: Mapping[str, str], reason: str, *, now: datetime) -> int` | Persistence write | `RiskDomainError(STORAGE_ERROR, PERMISSION_DENIED)` | **Usage:** `test_usage_approvals.py::test_usage_tokens_revoke_scope()`<br>**Unit:** `test_tokens.py::test_kill_switch_revokes_affected_scope()` |

**Implementation notes:** Reuse V1 signing/material-change/expiry logic; replace
hard-coded identity and process-global replay sets. UI/API owns approval attestation;
Risk owns validation, token issuance, reservation, consumption, and action-policy
verdicts under the registered market-context, approval-attestation, reservation, and execution-governance contracts.

**Usage file:** `tests/risk/usage/test_usage_approvals.py`

### 4.9 `decisions/` — Canonical Governor, Validity, and Kill Switch

**Purpose:** Produce one fixed-order decision path and canonical Risk-owned kill-switch state.

**Module flow:** `proposal/current state + config/evidence → validity/kill switch/regime/limits/capacity/approval → audited RiskDecisionPackage`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `governor.py` | Pre-trade and current-state decision orchestration | `RiskGovernor`, `RiskGovernor.review_trade_risk`, `RiskGovernor.run_portfolio_risk_governor` | **Standard library:** collections.abc, datetime<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio`, `sizing`, `policy`, `regimes`, `audit`, `approvals`; `app.utils → AuthContext` |
| Missing | `validity.py` | Decision/evidence/config reuse checks | `revalidate_risk_decision` | **Standard library:** datetime<br>**Required third-party:** None<br>**Local:** `contracts`, `config` |
| Missing | `kill_switch.py` | Apply authorized commands and evaluate block/recovery state | `apply_kill_switch_command`, `check_risk_kill_switch` | **Standard library:** collections.abc, datetime<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `audit`, `approvals`; `app.utils → AuthContext` |
| Missing | `__init__.py` | Expose decisions API | symbols above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** files above |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `DECISION_TTL_SECONDS` | `Decimal` | None | Yes | governor/validity | Expired decisions require refresh. |
| Missing | `IN_FLIGHT_TOLERANCE` | config | None | Live if used | governor | Exceeding buffer blocks; use is disclosed. |
| Missing | `IN_FLIGHT_GRACE_SECONDS` | `Decimal` | None | Live if used | validity | Expiry forces state refresh. |
| Missing | `DOUBLE_SPEND_OWNER` | enum | None | Live: Yes | governor | No owner causes `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`. |
| Missing | Kill-switch trigger/recovery policy | config | None | Yes | kill-switch | Unknown state blocks; recovery follows external authority policy. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-039` | Own immutable config plus injected token, audit, clock, and optional configured concurrency protection dependencies. | `RiskGovernor(config: RiskConfig, approvals: ApprovalTokenService, audit: RiskAuditChain, clock: Callable[[], datetime], capacity_guard: _CapacityGuard | None = None)` | Local state mutation | `RiskDomainError(INVALID_RISK_CONFIG)` | **Usage:** `tests/risk/usage/test_usage_decisions.py::test_usage_governor_create()`<br>**Unit:** `tests/risk/unit/test_governor.py::test_governor_requires_live_dependencies()` |
| Missing | `FR-RISK-040` | Validate and review one proposed trade in fixed precedence, include regime/projected risks/final capped size/concurrency disclosure, attach token only when eligible, and audit the decision. | `RiskGovernor.review_trade_risk(proposal: ProposedTrade, snapshot: PortfolioRiskSnapshot, market: MarketContextEvidence, regime: RegimeAssessment, auth: AuthContext, *, now: datetime) -> RiskDecisionPackage` | Persistence write | `RiskDomainError(GOVERNOR_DECISION_FAILED, STORAGE_ERROR)` | **Usage:** `test_usage_decisions.py::test_usage_governor_trade_review()`<br>**Unit:** `test_governor.py::test_trade_review_truth_table_and_precedence()` |
| Missing | `FR-RISK-041` | Evaluate current portfolio compliance and return a remediation recommendation without changing execution state. | `RiskGovernor.run_portfolio_risk_governor(snapshot: PortfolioRiskSnapshot, market: MarketContextEvidence, regime: RegimeAssessment, auth: AuthContext, *, now: datetime) -> RiskDecisionPackage` | Persistence write | `RiskDomainError(GOVERNOR_DECISION_FAILED, STORAGE_ERROR)` | **Usage:** `test_usage_decisions.py::test_usage_governor_portfolio()`<br>**Unit:** `test_governor.py::test_portfolio_governor_no_execution_mutation()` |
| Missing | `FR-RISK-042` | Compare proposal/evidence/config/time with a prior decision and invalidate material changes, expiry, skew, stale state, config mismatch, or reconciliation expiry. | `revalidate_risk_decision(decision: RiskDecisionPackage, proposal: ProposedTrade, snapshot: PortfolioRiskSnapshot, config: RiskConfig, *, now: datetime) -> ApprovalValidationResult` | None | `RiskDomainError(STALE_EVIDENCE, CONFIG_VERSION_MISMATCH, IN_FLIGHT_RECONCILIATION_EXPIRED)` | **Usage:** `test_usage_decisions.py::test_usage_validity_revalidate()`<br>**Unit:** `tests/risk/unit/test_validity.py::test_material_change_invalidates()` |
| Missing | `FR-RISK-043` | Apply authorized activation/clearance under `global > portfolio > strategy > symbol` precedence, revoke affected approvals on activation, and never mutate execution controls. Activation requires an authorized `AuthContext`; clearance additionally requires a matching current `ApprovalAttestation v1`. | `apply_kill_switch_command(command: KillSwitchCommand, current: KillSwitchState, auth: AuthContext, approvals: ApprovalTokenService, audit: RiskAuditChain, *, attestation: ApprovalAttestation | None = None, now: datetime) -> KillSwitchState` | Persistence write | `RiskDomainError(PERMISSION_DENIED, POLICY_BLOCKED, STORAGE_ERROR)` | **Usage:** `test_usage_decisions.py::test_usage_kill_switch_apply()`<br>**Unit:** `tests/risk/unit/test_kill_switch.py::test_child_clear_cannot_override_active_parent()` |
| Missing | `FR-RISK-044` | Return deterministic block/recovery eligibility; active or unknown applicable state blocks live risk increase, and recovery requires all applicable scopes inactive plus Trading reconciliation. | `check_risk_kill_switch(states: Sequence[KillSwitchState], scope: Mapping[str, str], *, reconciled: bool, now: datetime) -> RiskDecisionPackage` | None | `RiskDomainError(KILL_SWITCH_ACTIVE, KILL_SWITCH_UNKNOWN, POLICY_BLOCKED)` | **Usage:** `test_usage_decisions.py::test_usage_kill_switch_check()`<br>**Unit:** `test_kill_switch.py::test_recovery_requires_clear_hierarchy_and_reconciliation()` |

**Implementation notes:** Merge V1 `GovernanceEngine` and `RiskGovernor`, preserve execution-used validity and entry-block logic, and remove forced/manual decisions, broker reads, synthetic approvals, and execution-control mutation.

**Usage file:** `tests/risk/usage/test_usage_decisions.py`

### 4.10 `scenarios/` — Advisory Scenario and What-If Analysis

**Purpose:** Project bounded immutable scenarios without live mutation or approval authority.

**Module flow:** `immutable snapshot + bounded scenario definitions → projected snapshot metrics → advisory comparisons`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `analysis.py` | Baseline/projected scenario comparison | `run_risk_scenario_analysis` | **Standard library:** datetime<br>**Required third-party:** None<br>**Local:** `contracts`, `config`, `portfolio` |
| Missing | `__init__.py` | Expose scenario API | `run_risk_scenario_analysis` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `analysis.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `MAX_SCENARIOS_PER_RUN` | `int` | `100` supported baseline | Yes | scenario analysis | Excess is rejected before calculation. |
| Missing | `MAX_POSITIONS_PER_SCENARIO_RUN` | `int` | `500` supported baseline | Yes | scenario analysis | Excess is rejected or bounded. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-045` | Deterministically apply bounded scenarios to immutable snapshot evidence, return baseline/projected risk differences, preserve explicit seed, and mark every result advisory. | `run_risk_scenario_analysis(snapshot: PortfolioRiskSnapshot, scenarios: Sequence[ScenarioDefinition], config: RiskConfig, *, now: datetime) -> tuple[ScenarioResult, ...]` | None | `RiskDomainError(PAYLOAD_TOO_LARGE, CALCULATION_FAILED)` | **Usage:** `tests/risk/usage/test_usage_scenarios.py::test_usage_analysis_scenarios()`<br>**Unit:** `tests/risk/unit/test_analysis.py::test_analysis_is_immutable_and_deterministic()` |

**Implementation notes:** Refactor V1 `WhatIfEngine` and scenario registry behavior; exclude replay clock/timeline/cockpit/recommendation infrastructure.

**Usage file:** `tests/risk/usage/test_usage_scenarios.py`

### 4.11 `reporting/` — Focused Risk Decision Summaries

**Purpose:** Render Risk-owned Markdown/JSON explanations, not broad portfolio performance reports.

**Module flow:** `snapshot/decision/scenario result → deterministic sectioned renderer → RiskReport`

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Missing | `reports.py` | Focused deterministic summary rendering | `generate_risk_report` | **Standard library:** collections.abc, json, typing<br>**Required third-party:** None<br>**Local:** `contracts`, `audit`, `decisions`, `scenarios` |
| Missing | `__init__.py` | Expose reporting API | `generate_risk_report` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** `reports.py` |

#### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `RISK_REPORT_FORMAT` | enum | `markdown` | Yes | `generate_risk_report()` | Supported: Markdown or exact JSON. |
| Missing | `REPORT_TIMEOUT_SECONDS` | `Decimal` | None | Yes | report generation | Failure is surfaced and never hides the decision. |

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Missing | `FR-RISK-046` | Render evidence, calculations, assumptions, warnings, decision, and recommendations separately; show primary failure first; never claim live approval without valid decision/token evidence. | `generate_risk_report(source: PortfolioRiskSnapshot | RiskDecisionPackage | Sequence[ScenarioResult], format: Literal["markdown", "json"]) -> RiskReport` | None | `RiskDomainError(REPORT_GENERATION_FAILED)` | **Usage:** `tests/risk/usage/test_usage_reporting.py::test_usage_reports_generate()`<br>**Unit:** `tests/risk/unit/test_reports.py::test_report_has_no_false_approval_claim()` |

**Implementation notes:** Reuse focused V1 Markdown/JSON renderers; remove filesystem saving and broad performance/reporting infrastructure from Risk.

**Usage file:** `tests/risk/usage/test_usage_reporting.py`

### 4.12 Public Risk API

Risk exposes only the typed domain operations defined by the owning capability
modules. Public operations accept Risk-owned contracts, return Risk-owned results,
and surface `RiskDomainError` failures. No wrapper-only API, metadata catalog, or
parallel payload-mapping layer exists. UI/API alone adapts Risk results to external
transport responses.
---

## 5. Package-Wide Requirements and Shared Configuration

### Shared configuration

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Missing | `RUNTIME_PROFILE` | enum | `research` | Yes | config, governor, public API | Consumed from Utils; live requires complete safety configuration. |
| Missing | `EXECUTION_ROUTE` | enum | `none` | Yes | governor | Consumed from Trading; incompatible profile/route fails closed. |
| Missing | `DATABASE_URL` / `DATA_DIR` | `str` / path | System configuration | Yes | audit, approval, and Risk state persistence | Data owns connection, locking, and migration execution infrastructure; Risk owns its schemas and records. |
| Missing | UTC-first time policy | policy | ISO 8601 `Z` | Yes | all time-sensitive symbols | Naive time is invalid. |
| Missing | Decimal precision | context | ≥28 digits | Yes | all financial calculations | Exact Decimal, documented quantization, half-even default. |
| Missing | Correlation/trace IDs | policy | prefixed UUID4 | Yes | all material workflows | Propagated into decisions, logs, audits, and public results. |
| Missing | Secret redaction | policy | denylist-first, case-insensitive | Yes | all outputs | Applied before logs, errors, metrics, reports, and audit persistence. |

### Non-functional requirements

| Status | Requirement ID | Type | Responsibility | Verification |
|---|---|---|---|---|
| Missing | `NFR-RISK-001` | API boundary | Cross-domain callers use only documented versioned contracts; root `__all__` is explicit and contains only approved contracts and public operations. | Import/API tests |
| Missing | `NFR-RISK-002` | Determinism | Identical inputs, config hash, explicit time, seed, and dependency versions produce identical exact results and decision packages. | Reproduction tests |
| Missing | `NFR-RISK-003` | Precision | All broker-critical money/size/exposure/tail-risk fields use strict finite Decimal and exact JSON serialization. | Contract/property tests |
| Missing | `NFR-RISK-004` | Reliability | Invalid input, missing/stale mandatory evidence, unknown approval/kill-switch state, calculation failure, or mandatory persistence failure never yields approval. | Failure-path tests |
| Missing | `NFR-RISK-005` | Concurrency | Stateless calculations are thread-safe; shared token/audit/capacity state is synchronized and tested; concurrent requests cannot collectively overspend stale capacity. | Concurrent integration tests |
| Missing | `NFR-RISK-006` | Security | HMAC-or-stronger signing, least privilege, scope binding, payload guards, and redaction prevent prompt/token/payload bypass and secret exposure. | Security tests |
| Missing | `NFR-RISK-007` | Observability | Every material decision logs request/workflow/correlation IDs, verdict, reason codes, latency, evidence/config refs, and emits a serializable redacted audit record. | Log/audit inspection |
| Missing | `NFR-RISK-008` | Performance | Support 500 positions, 100 strategies, 5,000 return points, and 100 scenarios; normal pre-trade work is no worse than O(n²). Exact p95 gates remain proposed until baselined. | Representative benchmarks |
| Missing | `NFR-RISK-009` | Maintainability | Python ≥3.14, Google-style module/public docstrings, explicit type hints, focused files, no generic layer without demonstrated need, and project logging/result conventions. | Ruff/mypy/structure review |
| Missing | `NFR-RISK-010` | Testing | Every public symbol has one usage example and unit coverage; every collaborative workflow has an integration test; package coverage is at least 80%. | Test/traceability audit |
| Missing | `NFR-RISK-011` | Persistence | Risk owns schemas/semantics while Data owns connection/locking/migration execution; retries are idempotent and exhaustion is surfaced. | Persistence contract tests |
| Missing | `NFR-RISK-012` | Safety | Risk operations never place or close trades, mutate broker state, or override execution controls; only deterministic approved commands can authorize live actions or clear the kill switch. | Permission/side-effect tests |

The V2 timing observations—100 ms pre-trade, 250 ms snapshot, 50 ms prepared governor, 25 ms sizing, 50 ms correlation sizing, 5 s scenario, 1 s report, and 2 s/10,000-record chain verification—are diagnostic benchmark references, not acceptance gates. Benchmarks must record hardware, Python/dependency versions, data shape, cache state, and variance.

---

## 6. Open Decisions

No open decisions.

---

## 7. Tests and Definition of Done

### Test and usage locations

```text
tests/risk/
├── unit/
├── integration/
└── usage/
```

### Commands

```bash
uv run ruff check app/services/risk tests/risk
uv run ruff format --check app/services/risk tests/risk
uv run mypy app/services/risk

uv run pytest tests/risk/unit
uv run pytest tests/risk/integration
uv run pytest tests/risk/usage

uv run pytest tests/risk --cov=app/services/risk --cov-fail-under=80
```

During iterative implementation, run only the specific changed test files. Run the complete Risk package command at the verification milestone.

### Required test levels

- **Unit:** success, validation, exact errors, side effects, boundaries, retained V1 math, concurrency primitives, and all `FR-RISK-*` rows.
- **Integration:** all fourteen `WF-RISK-*` workflows, persistence failure, producer/consumer compatibility, and no broker/execution side effects.
- **Usage:** one independently runnable `test_usage_*` function per public symbol, importing only the documented feature API.
- **Security:** payload limits, secret redaction, prompt/argument bypass, token tamper/replay/scope, and kill-switch non-bypass.
- **Performance:** representative baselines before any proposed p95 value becomes a hard gate.

### Package completion checklist

- [ ] The actual package tree matches Section 2 in dependency order.
- [ ] Every module is one coherent capability and every file one focused responsibility.
- [ ] Every workflow and every `FR-RISK-*` / `NFR-RISK-*` row is `Completed` with mapped tests.
- [ ] Every public export appears in exactly one requirement row and root `__all__` is exact.
- [ ] Owned/consumed contracts match PROJECT names, versions, and ownership.
- [ ] Risk-owned persisted state uses Data-owned infrastructure through narrow interfaces.
- [ ] Every setting/limit has an owner, enforcement symbol, and exceeded behavior.
- [ ] No broker/provider/database-session object crosses the boundary.
- [ ] No removed or rejected capability appears in the architecture or implementation.
- [X] No unresolved decision affects a completed requirement.
- [ ] Google style, types, docstrings, logging, exact Decimal policy, and ≥80% coverage pass.
- [ ] Targeted tests and final Risk quality commands pass.

### README specification validation

- [X] Domain boundary and system contracts were reconciled against PROJECT.
- [X] All approved reconciliation capabilities have a destination.
- [X] All fourteen approved workflows are represented.
- [X] Removed or rejected behavior is absent from the architecture.
- [X] Every intended public symbol has one typed functional-requirement row.
- [X] Every functional requirement maps to usage and unit-test locations.
- [X] Every collaborative workflow maps to an integration-test location.
- [X] Diagrams, tree, module order, and dependency direction agree.
- [X] No unresolved specification conflict remains; affected behavior stays Missing until implementation evidence exists.

---

## 8. Change Process

For every future change:

```text
1. Update this README first.
2. Update the workflow and cross-domain contract when behavior changes.
3. Resolve or record decisions that would otherwise require guessing.
4. Add or change exactly one functional requirement per public symbol.
5. Update key exports, dependencies, configuration, side effects, and errors.
6. Reorder modules/files if dependency order changes.
7. Implement the smallest approved change.
8. Add or update the usage example and targeted tests.
9. Run targeted verification, then the Risk package quality gate.
10. Mark Completed only after implementation, callers, tests, and boundaries are verified.
```

This keeps Risk's requirements, implementation sequence, contracts, safety boundary, examples, tests, and evidence-based status aligned.


---

## Appendix P — Provisional Component Requirements (roadmap-promoted)

These IDs were minted by the agile delivery roadmap (`docs/dev/AGILE_ROADMAP.md`) and are promoted here to authoritative status. Each `P-RISK-NNN` authorizes establishment of the named package seam under `app/services/risk/` — its public port, package `__init__`, and error/DTO surface — as a stable component that hosts the same-named module and its `FR-RISK-*` behavior defined in §4 (Module and Requirement Specifications). Acceptance = the named package exists with its public seam fixed, typed, logged, tested, and passing the domain quality gates. "First phase" is the delivery phase in the roadmap; the seam is defined no later than that phase and deepened behind it.

| Requirement ID | Component / package | First phase | Hosts |
|---|---|---|---|
| `P-RISK-001` | `app/services/risk/contracts/` | 1 | `contracts` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-002` | `app/services/risk/config/` | 1 | `config` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-004` | `app/services/risk/sizing/` | 1 | `sizing` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-005` | `app/services/risk/policy/` | 1 | `policy` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-007` | `app/services/risk/audit/` | 1 | `audit` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-008` | `app/services/risk/approvals/` | 1 | `approvals` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-009` | `app/services/risk/decisions/` | 1 | `decisions` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-003` | `app/services/risk/portfolio/` | 4 | `portfolio` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-006` | `app/services/risk/regimes/` | 4 | `regimes` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-010` | `app/services/risk/scenarios/` | 4 | `scenarios` module + its `FR-RISK-*` behavior (§4) |
| `P-RISK-011` | `app/services/risk/reporting/` | 4 | `reporting` module + its `FR-RISK-*` behavior (§4) |
