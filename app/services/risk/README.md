# Runtime Risk

> **Package:** `app/services/risk/`
> **Status:** `Missing`
> **Last updated:** `2026-08-23`
> **Domain ID:** `D-RISK`
> **Specification version:** `1.1-code-aligned`

> This README is the domain package's **single source of truth** for domain boundaries, composable feature capabilities, architecture invariants, implementation sequence, progress, usage examples, and tests.
> Update this document before modifying or adding code.

---

## Code-Aligned Implementation Convention

This README is the sole current target registry for this domain's feature IDs and statuses, functional requirements, domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence, and deletion behavior. `PROJECT.md` owns system scope, cross-domain behavior, system NFRs, and release gates; `ARCHITECTURE.md` owns universal package and runtime constraints. Feature-local READMEs, manifests, contract definitions, migrations, and tests provide current implementation evidence without silently changing this target registry.

Implementation uses the repository's existing feature substrate: each feature lives directly at `app/services/<domain>/<feature>/`, is discovered through the `haruquantai.features` Python entry-point group, and declares one immutable `FeatureSpec` in `manifest.py`. There are no domain or feature YAML manifests.

Every implemented feature also contains a mandatory runtime-validated `README.md`, pure `__init__.py`, strict `config.py`, lifecycle `feature.py`, and focused implementation modules. Dependencies and effects flow through `FeatureContext`/`FeatureScope`; cross-feature implementation imports are forbidden. Persistent state is declared by `FeatureSpec.state`; any migrations and storage adapters remain with the owning feature. Capability keys use `<domain>.<name>@<major>`. FR IDs remain product, acceptance, and test-trace identities rather than one runtime registration per FR. A requirement `Depends` cell expresses product sequencing, traceability, or acceptance evidence only; runtime dependencies are declared separately with exact keys in `FeatureSpec.requires` or `FeatureSpec.optional`.

Feature-level automated tests live at `tests/services/risk/<feature>/`. Usage examples never live under `tests/`; they belong to each feature's designated primary domain-logic module. Broader automated verification retains its documented architecture, composition, API, integration, or system test location. The code-backed procedure is the [Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md).

## 1. Purpose and Boundary

### Purpose

Runtime Risk is the non-bypassable, deterministic admission authority for paper/demo/live actions. It evaluates current evidence, profiles, limits, operational eligibility, allocation budgets, approval policy, reservations, and kill-switch state. It returns bounded decisions and authorization evidence; it never places an order.

### Owns

- Versioned runtime risk profiles, firm mandates, limits, freshness rules, and precedence.
- Immutable portfolio/account risk snapshots used for current-state decisions.
- Position-sizing recommendations that never imply approval.
- Proposed-trade admission and the canonical risk governor.
- Strategy operational eligibility and allocation/budget activation decisions.
- Approval attestation validation, signed approval-token lifecycle, and durable capacity reservation.
- Hierarchical kill-switch authority, state, recovery, and fail-closed unknown state.
- Decision reuse revalidation, scenario/what-if analysis, decision summaries, and tamper-evident risk audit.
- A successful `NO_TRADE` outcome distinct from system failure.

### Does not own

- Strategy definitions or trade-intent generation; Strategy owns them.
- Market, account, FX, news, session, or provider evidence; Data, Catalogue, and Broker Connectivity own source evidence.
- Research portfolio risk metrics and Markowitz construction; Portfolio owns them.
- Backtest sizing/fill semantics; Simulator owns them.
- Order routing, dispatch, execution retry, reconciliation, or protective-order management; Trading owns them.
- Authentication principals or stored secrets; Workspace owns their behavior and `app/contracts/workspace/` owns their public definitions.

### Shared Contracts

Runtime Risk semantically owns its public decision, profile, evidence, approval, capacity, kill-switch, and audit contracts, but their sole physical definitions live in `app/contracts/risk/` and wire schemas in `app/contracts/risk/wire/`. `app/services/risk/` contains implementations only and shall not define or re-export substitute public contract types. Consumed contract types are imported from their corresponding `app/contracts/<owner>/` namespace. Feature IDs and FR IDs are documentation, lifecycle, acceptance, and traceability identities; runtime consumption uses exact versioned capability keys declared by contracts and `FeatureSpec`. The exact public records and capability bundles are listed in the [Shared Contracts README](../../contracts/README.md#413-appcontractsrisk).

### Core invariant

```text
No paper/demo/live mutation
  unless kill-switch state is known and clear for the exact scope,
  evidence and configuration are current,
  a Risk decision allows the exact action and size,
  required human approval is valid,
  and capacity is atomically reserved.
```

### Persisted State Ownership

| Status | Owned state | Rule |
|---|---|---|
| Missing | `risk_profiles`, `risk_profile_versions`, `firm_mandate_versions` | Immutable/effective-dated; canonical hash pins every decision. |
| Missing | `risk_decisions`, `risk_limit_results`, `risk_evidence_refs` | Append-only decision history; no copied foreign evidence payload unless required by audit policy. |
| Missing | `risk_approval_tokens`, `risk_token_events` | Signed, scoped, expiring, revocable, single-use where required. |
| Missing | `risk_capacity_reservations`, `risk_capacity_events` | Atomic reserve/commit/release/expire lifecycle with fencing. |
| Missing | `risk_kill_switch_state`, `risk_kill_switch_events` | Hierarchical, versioned, tamper-evident; unknown blocks action. |
| Missing | `risk_audit_records` | Append-only hash chain with redacted canonical payload. |

## 2. Final Package Structure and Feature Independence

| Status | Feature | Module | Actor outcome | Deletion contract |
|---|---|---|---|---|
| Missing | `FEAT-RISK-DEFINE_RISK_CONTRACTS` Contracts, Profiles, and Evidence | `profiles_evidence/` | Configure and validate exact risk vocabulary, profiles, mandates, and evidence using definitions from `app/contracts/risk/` | Runtime action admission is unavailable. |
| Missing | `FEAT-RISK-CALCULATE_RISK` Snapshot and Sizing | `snapshot_sizing/` | Understand current risk and calculate bounded size without granting approval | Current-state review and sizing are unavailable. |
| Missing | `FEAT-RISK-GOVERN_ADMISSION` Admission and Governor | `admission_governor/` | Receive one deterministic allow/warn/approval/reject/block decision | Trading cannot dispatch new risk-bearing actions. |
| Missing | `FEAT-RISK-MANAGE_APPROVALS` Approvals and Capacity | `approvals_capacity/` | Bind human approval and reserve risk budget exactly once | Approval-required or capacity-consuming actions block. |
| Missing | `FEAT-RISK-CONTROL_KILL_SWITCH` Kill Switch | `kill_switch/` | Block or recover scopes through authorized, audited transitions | All runtime actions block because state cannot be proven clear. |
| Missing | `FEAT-RISK-GOVERN_ALLOCATIONS` Eligibility and Allocation | `eligibility_allocation/` | Govern strategy versions and portfolio/allocation budgets for operations | Operational promotion and portfolio activation are unavailable. |
| Missing | `FEAT-RISK-AUDIT_RISK_DECISIONS` Revalidation, Scenarios, and Audit | `revalidation_audit/` | Revalidate reuse, run advisory scenarios, report decisions, and prove audit integrity | Decision reuse blocks; unrelated domains continue. |

```text
risk/
├── README.md
├── __init__.py
├── profiles_evidence/
├── snapshot_sizing/
├── admission_governor/
├── approvals_capacity/
├── kill_switch/
├── eligibility_allocation/
└── revalidation_audit/
```

| Feature | Responsibility file | Requirement implementation traces |
|---|---|---|
| `FEAT-RISK-DEFINE_RISK_CONTRACTS` | `profiles_evidence/profiles_evidence.py` | `fr_risk_define_decision_states` through `fr_risk_validate_source_evidence` |
| `FEAT-RISK-CALCULATE_RISK` | `snapshot_sizing/snapshot_sizing.py` | `fr_risk_calculate_risk_snapshot` through `fr_risk_validate_stop_loss` |
| `FEAT-RISK-GOVERN_ADMISSION` | `admission_governor/admission_governor.py` | `fr_risk_bind_proposed_action` through `fr_risk_prevent_execution_effects` |
| `FEAT-RISK-MANAGE_APPROVALS` | `approvals_capacity/approvals_capacity.py` | `fr_risk_bind_human_approval` through `fr_risk_bind_capacity_reservation` |
| `FEAT-RISK-CONTROL_KILL_SWITCH` | `kill_switch/kill_switch.py` | `fr_risk_define_kill_scopes` through `fr_risk_audit_kill_transitions` |
| `FEAT-RISK-GOVERN_ALLOCATIONS` | `eligibility_allocation/eligibility_allocation.py` | `fr_risk_assess_strategy_eligibility` through `fr_risk_validate_portfolio_budget` |
| `FEAT-RISK-AUDIT_RISK_DECISIONS` | `revalidation_audit/revalidation_audit.py` | `fr_risk_revalidate_risk_authority` through `fr_risk_chain_audit_records` |

Each functional-requirement row owns a focused implementation and acceptance-test trace. `fr_*` names may be used as trace labels, but runtime discovery, dependency resolution, and removal occur through the owning feature's `FeatureSpec` and entry point. Private helpers are not public requirements.

## 3. Workflows

| Status | Workflow ID | Trigger | Inputs | Outcome |
|---|---|---|---|---|
| Missing | `WF-RISK-001` Review proposed action | Trading submits preflight | Exact Strategy intent or manual plan, current account/portfolio/market evidence, route/profile, risk profile | Decision package plus optional bounded authorization reference |
| Missing | `WF-RISK-002` Calculate position size | Strategy/Trading requests recommendation | Method, stop evidence, account/equity, instrument rules, FX, limits | Requested and normalized size, constraints, gaps; never approval |
| Missing | `WF-RISK-003` Kill-switch transition/check | Authorized command or pre-dispatch check | Scope, current state/version, reason, approval if clearing | New state or block/recovery decision |
| Missing | `WF-RISK-004` Activate strategy/allocation | Promotion or rebalance request | Exact versions, evidence, policy, route, allocation plan | Eligibility/allocation decision and optional budget activation |
| Missing | `WF-RISK-005` Validate approval and reserve capacity | Admission requires approval/capacity | Decision, token/attestation, exact action hash, current state | Atomic validation plus reservation, or no authority |
| Missing | `WF-RISK-006` Revalidate before reuse | Trading reuses a decision or retries after delay | Prior decision/token/reservation and fresh current evidence | Reusable authorization, refresh required, or block |
| Missing | `WF-RISK-007` Scenario and report | Operator requests advisory analysis | Immutable snapshot, versioned scenario, explicit seed if stochastic | Advisory result and separated evidence/assumptions/warnings |

## 4. Composable Feature Specifications

### 4.1 `FEAT-RISK-DEFINE_RISK_CONTRACTS` Contracts, Profiles, and Evidence

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-DEFINE_DECISION_STATES` | P0 | Decision states shall distinguish `APPROVE`, `WARN`, `NEEDS_APPROVAL`, `NEEDS_MORE_EVIDENCE`, `REJECT`, `BLOCK`, and `ERROR`; limit states shall distinguish pass/warn/missing/fail/blocked. | Unknown states are rejected and no state implies execution. | Requirement evidence |
| Missing | `FR-RISK-VERSION_RISK_PROFILES` | P0 | Risk profiles shall be immutable, effective-dated, strictly validated, and define thresholds, units, modes, freshness, rounding, concurrency, approval, audit, and failure precedence without implicit defaults. | Invalid or incomplete profiles cannot activate. | Profile/config requirements |
| Missing | `FR-RISK-PIN_RISK_PROVENANCE` | P0 | Every decision shall pin profile/mandate versions, canonical configuration hash, evidence references/hashes, `as_of`, request/workflow/correlation IDs, and schema version. | Missing or conflicting provenance produces `NEEDS_MORE_EVIDENCE` or `BLOCK`, never approval. | Config hash/audit |
| Missing | `FR-RISK-VALIDATE_SOURCE_EVIDENCE` | P0 | Consumed account, FX, market, news, session, strategy, broker, and portfolio evidence shall be validated for owner schema, identity, UTC time, freshness, coverage, provenance, explicit missingness, and exact units without redefining it. | Stale, incompatible, absent, or contradictory required evidence fails closed. | Requirement evidence |

#### Feature usage examples

The primary domain-logic module `app/services/risk/profiles_evidence/profiles_evidence.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.2 `FEAT-RISK-CALCULATE_RISK` Snapshot and Sizing

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-CALCULATE_RISK_SNAPSHOT` | P0 | A portfolio risk snapshot shall compute base-currency equity, daily/total loss, drawdown, gross/net and dimensional exposure, margin/leverage, historical tail risk, volatility/correlation contribution, limit results, assumptions, coverage, and regime from one pinned evidence set. | Independent fixtures reconcile exact decimals; missing inputs remain explicit. | Requirement evidence |
| Missing | `FR-RISK-INCLUDE_PENDING_EXPOSURE` | P0 | Snapshot construction shall include remaining pending-order quantity and current open-position exposure, with deterministic duplicate and in-flight treatment. | Open, pending, and reserved exposure cannot be silently omitted or double-counted. | Portfolio-state semantics |
| Missing | `FR-RISK-CALCULATE_POSITION_SIZE` | P0 | Sizing shall support versioned methods declared by the profile and return requested size, normalized size, instrument/portfolio constraints, evidence gaps, fallback disclosure, and calculation trace. | A sizing result cannot claim approval or exceed an applicable hard limit. | Requirement evidence |
| Missing | `FR-RISK-VALIDATE_STOP_LOSS` | P0 | Stop-dependent sizing shall validate side, tick alignment, invalidation distance, noise/venue minimums, projected loss, and widening permissions. | Missing/invalid stop or required volatility evidence rejects sizing/admission. | Feature evidence |

#### Feature usage examples

The primary domain-logic module `app/services/risk/snapshot_sizing/snapshot_sizing.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.3 `FEAT-RISK-GOVERN_ADMISSION` Admission and Governor

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-BIND_PROPOSED_ACTION` | P0 | A proposed-action contract shall embed the complete immutable Strategy intent or Trading manual plan unchanged and add exact account/portfolio scope, valuation, stop, route/profile, evidence, and requested risk profile. | Incompatible version, conflicting fact, invalid scope/size, or missing mandatory evidence is rejected. | Requirement evidence |
| Missing | `FR-RISK-EVALUATE_RISK_GOVERNOR` | P0 | The governor shall evaluate kill switch, evidence validity, profile validity, eligibility, session/news/regime constraints, stop validity, size, portfolio/market limits, allocation budget, approval policy, and capacity in a fixed documented precedence. | Earlier blocking reasons cannot be masked by later approvals. | Canonical governor |
| Missing | `FR-RISK-RETURN_RISK_DECISION` | P0 | The decision package shall contain verdict, exact allowed action and maximum size where applicable, ordered checks, primary/composite reasons, expiry, provenance, concurrency disclosure, and optional authorization references. | Current-state compliance with no intent cannot invent a trade or size. | Requirement evidence |
| Missing | `FR-RISK-RETURN_NO_TRADE` | P0 | Mandatory-gate rejection with a valid system/evidence state shall return a successful `NO_TRADE` business outcome distinct from transport, calculation, or storage failure. | Interfaces and analytics can distinguish safe stand-down from failed evaluation. | Feature evidence |
| Missing | `FR-RISK-PREVENT_EXECUTION_EFFECTS` | P0 | The governor shall not mutate Trading or Broker state and shall not treat a recommendation, report, scenario, or human attestation as execution authority. | Capability-boundary tests prove no execution side effect. | Domain boundary |

#### Feature usage examples

The primary domain-logic module `app/services/risk/admission_governor/admission_governor.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.4 `FEAT-RISK-MANAGE_APPROVALS` Approvals and Capacity

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-BIND_HUMAN_APPROVAL` | P0 | Human approval evidence shall bind authenticated principal, exact action/scope/policy, decision/config hashes, issue/expiry times, and trace IDs; it carries no secret and grants no authority by itself. | Unbound, expired, mismatched, or unauthorized approval is invalid. | Requirement evidence |
| Missing | `FR-RISK-SIGN_APPROVAL_TOKENS` | P0 | A risk approval token shall be signed, scoped, expiring, nonce-bearing, revocable, and bound to decision/config/action hashes and approver identity. | Invalid, expired, revoked, consumed, or mismatched tokens grant no verdict. | Requirement evidence |
| Missing | `FR-RISK-CONSUME_APPROVAL_ATOMICALLY` | P0 | Validation and required token consumption shall be atomic and return authority only after successful single-use reservation/consumption. | Concurrent double spend produces one success at most. | Durable token lifecycle |
| Missing | `FR-RISK-RESERVE_RISK_CAPACITY` | P0 | Risk capacity shall be atomically reserved before dispatch against account, strategy, portfolio, symbol, and global budgets, then committed, released, or expired through fenced transitions. | Concurrent admissions cannot exceed any hard budget. | Durable capacity reservation |
| Missing | `FR-RISK-BIND_CAPACITY_RESERVATION` | P0 | A reservation shall bind decision, action/plan hash, amount/units, scope, predecessor state, issue/expiry, and idempotency identity. | Trading cannot substitute another action or amount. | Capacity/approval binding |

#### Feature usage examples

The primary domain-logic module `app/services/risk/approvals_capacity/approvals_capacity.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.5 `FEAT-RISK-CONTROL_KILL_SWITCH` Kill Switch

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-DEFINE_KILL_SCOPES` | P0 | Kill-switch scopes shall include global, environment, broker account, portfolio, strategy, and symbol; an active broader scope dominates narrower clear states. | Effective-state fixtures prove deterministic hierarchy. | Kill-switch authority |
| Missing | `FR-RISK-CHECK_KILL_SWITCH` | P0 | Every preflight and immediately pre-dispatch check shall read a known current kill-switch version for the exact action scope. | Active, unknown, stale, unavailable, or version-mismatched state blocks. | Fail-closed kill switch |
| Missing | `FR-RISK-AUTHORIZE_KILL_TRANSITIONS` | P0 | Activate/block transitions require authorized principal and reason; clear/recover additionally requires separate matching current approval and verified remediation evidence. | Unauthorized or incomplete clearance leaves the block active. | Kill-switch command/state |
| Missing | `FR-RISK-AUDIT_KILL_TRANSITIONS` | P0 | Kill-switch transitions shall be atomic, append-only audited, idempotent, and publish a critical causal event to Trading and Interfaces. | Failed persistence cannot report a successful transition. | Tamper-evident authority |

#### Feature usage examples

The primary domain-logic module `app/services/risk/kill_switch/kill_switch.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.6 `FEAT-RISK-GOVERN_ALLOCATIONS` Eligibility and Allocation

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-ASSESS_STRATEGY_ELIGIBILITY` | P0 | Strategy operational eligibility shall bind an exact strategy/version, runtime profile, route, policy, evidence, approval context, conditions, validity interval, and decision lineage without altering Strategy registration. | A different strategy version/profile/route requires a new decision. | Strategy eligibility |
| Missing | `FR-RISK-REVIEW_PORTFOLIO_ALLOCATION` | P0 | Allocation review shall consume a self-contained projection of exact portfolio/allocation versions, ordered weights/actions, eligibility, account/market/FX evidence, and runtime scope without importing Portfolio internals. | Incomplete or stale projections are rejected. | Allocation review |
| Missing | `FR-RISK-AUTHORIZE_ALLOCATION_BUDGET` | P0 | An allocation decision shall return capped weights, authoritative risk-budget projection, conditions, evidence/policy lineage, and expiry; activation shall bind predecessor and effective time. | Trading receives budget authority only for the activated exact version. | Allocation decision/activation |
| Missing | `FR-RISK-VALIDATE_PORTFOLIO_BUDGET` | P0 | Execution-time portfolio budget verdicts shall bind the current allocation decision, portfolio/allocation version, plan ID/hash, budget unit, reasons, and UTC validity; Trading validates and never recalculates budget consumption. | Binding mismatch blocks dispatch. | Requirement evidence |

#### Feature usage examples

The primary domain-logic module `app/services/risk/eligibility_allocation/eligibility_allocation.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

### 4.7 `FEAT-RISK-AUDIT_RISK_DECISIONS` Revalidation, Scenarios, and Audit

| Status | Requirement ID | Pri | Responsibility | Failure / acceptance | Source / confidence |
|---|---|---|---|---|---|
| Missing | `FR-RISK-REVALIDATE_RISK_AUTHORITY` | P0 | Before reuse, retry, modification, or delayed dispatch, Risk shall revalidate decision/token/reservation against current time, evidence, configuration, kill switch, provider session generation, and in-flight exposure. | Any material change requires refresh or blocks; prior approval is not grandfathered. | Decision reuse revalidation |
| Missing | `FR-RISK-RUN_RISK_SCENARIOS` | P1 | Advisory scenarios shall apply bounded deterministic shocks, use an explicit seed for stochastic paths, and compare baseline/projected risk without producing approval. | Scenario results state assumptions, limitations, and advisory status. | Scenario analysis |
| Missing | `FR-RISK-REPORT_RISK_DECISIONS` | P1 | Risk reports shall separate evidence, assumptions, warnings, checks, decision, and recommendations in canonical JSON or Markdown. | Reports cannot strengthen or alter the underlying decision. | Decision summaries |
| Missing | `FR-RISK-CHAIN_AUDIT_RECORDS` | P0 | Every material profile, evidence-validation, decision, token, reservation, kill-switch, eligibility, allocation, reuse, and scenario event shall append a redacted canonical hash-chained audit record. | Chain verification detects insertion, deletion, reordering, or mutation; tamper detection activates a block policy. | Risk audit |

#### Feature usage examples

The primary domain-logic module `app/services/risk/revalidation_audit/revalidation_audit.py` owns the executable `__main__` usage harness, with one named scenario per requirement listed above.

## 5. Package-Wide Requirements, Configuration, and Architecture Invariants

| Status | Setting | Default | Rule |
|---|---|---|---|
| Missing | `risk_profile_id` | None | Required for runtime risk-bearing actions. |
| Missing | `risk_decision_ttl` | 30 seconds | Profiles may narrow; reuse after expiry requires reevaluation. |
| Missing | `approval_token_ttl` | 5 minutes | Cannot outlive the underlying decision or attestation. |
| Missing | `capacity_reservation_ttl` | 30 seconds | Expiry releases capacity unless already committed. |
| Missing | `evidence_freshness` | No implicit defaults | Each evidence kind declares a required policy. |
| Missing | `historical_var_method` | Historical only | Additional methods require new versioned requirements and fixtures. |

### Non-Functional Requirements

- All money, price, quantity, percentage, and limit arithmetic uses exact decimal/unit contracts and documented rounding.
- Deterministic inputs produce byte-identical canonical decisions and audit payload hashes.
- The kill switch and hard limits are non-bypassable through UI, API, CLI, MCP, automation, retry, or direct adapter use.
- Missing/unknown/stale security-critical state fails closed.
- Risk has no broker credential and no execution route.

## 6. Open Decisions

None currently. Add only unresolved architectural choices that would otherwise require implementation guesswork.

## 7. Tests and Definition of Done

- Every `FR-RISK-*` has focused automated verification and a named scenario in its feature's executable primary-module usage harness.
- Hand-worked snapshot, sizing, limit precedence, hierarchy, token, reservation, concurrency, revalidation, and audit-chain fixtures pass.
- Property tests cover non-negative sizes, hard-limit monotonicity, exact decision binding, and broader kill-switch dominance.
- Fault tests cover persistence loss, stale evidence, conflicting evidence, unknown provider state, concurrent token use, reservation expiry, and audit tamper.
- System tests prove that Trading cannot dispatch without a current decision, reservation where required, and immediately pre-dispatch clear kill-switch state.

## 8. Change Process

Any threshold, calculation, rounding, precedence, freshness, approval, token, reservation, hierarchy, or evidence-binding change requires a new profile/contract version and independent fixtures. Risk must never absorb Trading dispatch or Broker transport responsibilities.
