# Phase 4 Implementation Plan - v1.4 - Independent risk depth

> **Status:** Not started
> **Requirement count:** 21
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 4
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 4. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.4`.
- **Theme:** Independent risk depth.
- **Entry condition:** Phase 3 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Show policy caps, regime changes, scenario evidence, and deterministic decision precedence.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.4 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires shallow governance; adds portfolio/regime/scenario complexity.

## 3. Inherited implementation constraints (non-authoritative summary)

This section repeats constraints from the authoritative repository documents for developer convenience. It does not create or modify requirements. If any wording differs from an authoritative source, the source wins and this ledger must be corrected.

1. Deliver production-grade code for the narrow phase scope; no disposable implementation, temporary public API, silent fallback, or fake success path is allowed.
2. Keep the architecture acyclic and use only documented domain exports. Python remains the sole deterministic policy-enforcement authority.
3. Every broker-mutating proof uses an actual MT5 platform connected to an account whose environment is deterministically `demo`. Real-capital execution is prohibited.
4. A fake broker adapter may be used only where a later contract-test requirement explicitly mandates it; it cannot satisfy an actual MT5 integration or usage proof.
5. Risk approval, authorization evidence, route compatibility, kill switch state, idempotency, and audit persistence fail closed whenever required evidence is absent or stale.
6. Never record invented fills, performance, provider responses, or benchmark claims. Tests use declared fixtures; actual-provider proofs preserve factual returned evidence.
7. Use explicit types and Google-style docstrings for all signatures; use the project logger, never `print`; redact secrets before logs, errors, metrics, traces, audit payloads, or returned diagnostics.
8. Run targeted tests during implementation. Do not use the full test suite as the iterative inner loop.
9. During the phase, update only this plan's checkboxes and evidence. Reconcile affected domain READMEs and active system documentation during the phase-close stage.
10. A checked item without implementation and test `path:line` evidence is invalid and must be returned to unchecked state.

## 4. How to read the execution order

Section 8 is the sole implementation sequence for this phase. Execute it from the first numbered step to the last. Domain tables and ID manifests elsewhere in this document are coverage indexes only and must never be interpreted as delivery order.

Each step records its immediate ledger predecessor and its authoritative requirement dependencies. The default is strict top-to-bottom execution. Parallel work is allowed only when the lead reviewer records that the affected steps share no implementation, contract, migration, runtime, or verification predecessor; parallel completion must still be merged and evidenced in ledger order.

The ordering model is:

1. Phase-level system prerequisites.
2. Domain modules in architecture dependency order.
3. Within a module: component/package establishment before functional behavior.
4. Domain workflows after their contributing module behavior.
5. Capability acceptance after functional and workflow delivery.
6. Domain NFR verification after the behavior it verifies.
7. Cross-domain system workflows after all contributing domains.
8. System-wide quality verification and phase completion last.

## 5. Requirement distribution (coverage index only)

This table proves domain coverage. It is not an implementation sequence; Section 8 is the only execution order.

| Lane | Assigned IDs | Phase obligation |
|---|---:|---|
| System | 0 | Cross-domain architecture and workflow control. |
| Utils | 0 | Governance primitive regression. |
| Brokers | 0 | Add account/execution read depth. |
| Data | 0 | Deepen MarketContextEvidence. |
| Indicators | 0 | Availability regression. |
| Strategy | 0 | Complete intent evidence. |
| Risk | 15 | Complete portfolio snapshot, limits, regimes, scenarios, allocation/admission governance, and focused reporting. |
| Trading | 3 | Consume deeper Risk evidence without self-approval. |
| Simulation | 1 | Exercise full sim policy. |
| Analytics | 0 | Present non-binding Risk evidence. |
| Optimization | 0 | Remain advisory. |
| Research | 0 | Consume ScenarioResult only. |
| Portfolio | 0 | Prepare portfolio governance adapters. |
| UI/API | 2 | Expose full Risk decision support. |

## 6. Developer execution protocol

For each requirement, the assigned developer must:

1. Open the cited source document and locate the requirement ID or cited component section.
2. Confirm dependency evidence and identify the owning package, public export, side effects, failure behavior, usage example, and tests.
3. Submit a scoped dry run naming files, tests, runtime actions, safety conditions, and rollback.
4. Implement the smallest complete production-grade behavior that satisfies the requirement without weakening the final seam.
5. Run source-named unit/usage tests plus targeted integration, security, determinism, and negative-path tests appropriate to the change.
6. Run Ruff and MyPy over the affected code; maintain at least 80% coverage for changed behavior.
7. Replace the requirement's pending evidence line with concrete code and test `path:line` references and the passing commands.
8. Obtain review, then change `[ ]` to `[X]`. Never check an item based only on intent, scaffolding, or an unverified provider mock.

### 6.1 Standard verification commands

```powershell
uv run pytest <targeted-test-file>
uv run ruff check <changed-code-and-test-paths>
uv run ruff format --check <changed-code-and-test-paths>
uv run mypy app
git diff --check
```

Use the exact source-named usage and integration commands in addition to these gates. Any command that mutates a broker requires the separately approved, deterministic MT5-demo execution procedure.

## 7. Cross-domain integration gates

- [ ] All consumed contracts are imported only from documented public exports. Evidence: Pending.
- [ ] Every cross-domain request propagates authentication, correlation, causation, and audit context as specified. Evidence: Pending.
- [ ] Missing, stale, malformed, unauthorized, unsupported, or uncertain evidence fails closed at the owning boundary. Evidence: Pending.
- [ ] Deterministic paths reproduce canonical outputs and hashes from identical inputs. Evidence: Pending.
- [ ] Persistence ownership, transactions, migrations, locks, and restart behavior match domain boundaries. Evidence: Pending.
- [ ] Logs, errors, traces, metrics, audit records, and returned diagnostics contain no secrets. Evidence: Pending.
- [ ] Actual-provider tests distinguish factual provider evidence from fixtures and simulated results. Evidence: Pending.
- [ ] The roadmap exit workflow succeeds end to end and its negative/recovery cases are evidenced. Evidence: Pending.

## 8. Sequential implementation ledger

This section is the mandatory implementation order. Start at Step 1 and proceed downward. A requirement appearing in a later domain, workflow, capability, or verification stage is not ready merely because it is independently understandable.

Every step is gated by the immediately preceding ledger step. The additional dependency evidence identifies authoritative prerequisites that must also be complete. Checkboxes and evidence are updated here during implementation; domain README reconciliation remains a phase-close activity.

### Stage 1 - Risk

Implement `Risk` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P04-S0001` [ ] `FR-RISK-022` - Define strict profile fields, thresholds, modes, freshness, rounding, concurrency, audit, and dependency timeouts with stable schema version.

- **Execution domain:** `Risk`.
- **Execution position:** `1` of `21`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 4. Module and Requirement Specifications > 4.2 `config/` — Risk Profiles and Stable Configuration > Configuration and Limits Manifest`` (line 545); matrix row `550`.
- **Source responsibility:** Define strict profile fields, thresholds, modes, freshness, rounding, concurrency, audit, and dependency timeouts with stable schema version.
- **Source class / function / method:** `RiskConfig`
- **Source side effects:** None
- **Source raises:** `ValidationError`: missing/invalid values
- **Source usage / test:** **Usage:** `tests/risk/usage/test_usage_config.py::test_usage_profiles_config()`<br>**Unit:** `tests/risk/unit/test_profiles.py::test_live_profile_requires_all_safety_values()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RISK-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0002` [ ] `FR-RISK-024` - Hash canonical exact serialization so any material config change changes the SHA-256 hash.

- **Execution domain:** `Risk`.
- **Execution position:** `2` of `21`.
- **Cannot start before:** Step `P04-S0001` (`FR-RISK-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 4. Module and Requirement Specifications > 4.2 `config/` — Risk Profiles and Stable Configuration > Configuration and Limits Manifest`` (line 547); matrix row `551`.
- **Source responsibility:** Hash canonical exact serialization so any material config change changes the SHA-256 hash.
- **Source class / function / method:** `compute_config_hash(config: RiskConfig) -> str`
- **Source side effects:** None
- **Source raises:** `RiskDomainError(INVALID_RISK_CONFIG)`: canonicalization failure
- **Source usage / test:** **Usage:** `test_usage_config.py::test_usage_profiles_hash()`<br>**Unit:** `test_profiles.py::test_config_hash_is_stable_and_sensitive()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RISK-024`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0003` [ ] `P-RISK-003` - portfolio feature/component (provisional)

- **Execution domain:** `Risk`.
- **Execution position:** `3` of `21`.
- **Cannot start before:** Step `P04-S0002` (`FR-RISK-024`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RISK-003`); matrix row `555`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RISK-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0004` [ ] `FR-RISK-028` - Evaluate supplied spread, slippage, liquidity, session, and calendar evidence without external fetches or naive/aware datetime comparison.

- **Execution domain:** `Risk`.
- **Execution position:** `4` of `21`.
- **Cannot start before:** Step `P04-S0003` (`P-RISK-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 4. Module and Requirement Specifications > 4.5 `policy/` — Limits, Market Context, Admission, and Allocation Gates > Configuration and Limits Manifest`` (line 650); matrix row `552`.
- **Source responsibility:** Evaluate supplied spread, slippage, liquidity, session, and calendar evidence without external fetches or naive/aware datetime comparison.
- **Source class / function / method:** `evaluate_market_context(evidence: MarketContextEvidence, config: RiskConfig, *, now: datetime) -> tuple[RiskLimitResult, ...]`
- **Source side effects:** None
- **Source raises:** `RiskDomainError(MISSING_EVIDENCE, POLICY_BLOCKED)`
- **Source usage / test:** **Usage:** `test_usage_policy.py::test_usage_limits_market_context()`<br>**Unit:** `test_limits.py::test_timezone_failure_blocks_live()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RISK-028`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0005` [ ] `P-RISK-006` - regimes feature/component (provisional)

- **Execution domain:** `Risk`.
- **Execution position:** `5` of `21`.
- **Cannot start before:** Step `P04-S0004` (`FR-RISK-028`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RISK-006`); matrix row `556`
- **Source file:** `governor.py`
- **Source responsibility:** Pre-trade and current-state decision orchestration
- **Source key exports:** `RiskGovernor`, `RiskGovernor.review_trade_risk`, `RiskGovernor.run_portfolio_risk_governor`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RISK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0006` [ ] `FR-RISK-032` - Own injected canonical serializer, clock, storage port, and deterministic chain configuration without owning database infrastructure.

- **Execution domain:** `Risk`.
- **Execution position:** `6` of `21`.
- **Cannot start before:** Step `P04-S0005` (`P-RISK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.7` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 4. Module and Requirement Specifications > 4.7 `audit/` — Tamper-Evident Risk Audit Boundary > Configuration and Limits Manifest`` (line 709); matrix row `553`.
- **Source responsibility:** Own injected canonical serializer, clock, storage port, and deterministic chain configuration without owning database infrastructure.
- **Source class / function / method:** `RiskAuditChain(config: RiskConfig, store: _RiskAuditStore, clock: Callable[[], datetime])`
- **Source side effects:** Local state mutation
- **Source raises:** `RiskDomainError(INVALID_RISK_CONFIG)`
- **Source usage / test:** **Usage:** `tests/risk/usage/test_usage_audit.py::test_usage_chain_create()`<br>**Unit:** `tests/risk/unit/test_chain.py::test_chain_requires_deterministic_genesis()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RISK-032`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0007` [ ] `FR-RISK-035` - Own injected signer/secret resolver, clock, durable state port, authorization verifier, and audit chain.

- **Execution domain:** `Risk`.
- **Execution position:** `7` of `21`.
- **Cannot start before:** Step `P04-S0006` (`FR-RISK-032`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.8` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 4. Module and Requirement Specifications > 4.8 `approvals/` — Durable Approval-Token Lifecycle > Configuration and Limits Manifest`` (line 741); matrix row `554`.
- **Source responsibility:** Own injected signer/secret resolver, clock, durable state port, authorization verifier, and audit chain.
- **Source class / function / method:** `ApprovalTokenService(config: RiskConfig, state: _TokenStateStore, audit: RiskAuditChain, clock: Callable[[], datetime])`
- **Source side effects:** Local state mutation
- **Source raises:** `RiskDomainError(INVALID_RISK_CONFIG, STORAGE_ERROR)`
- **Source usage / test:** **Usage:** `tests/risk/usage/test_usage_approvals.py::test_usage_tokens_create_service()`<br>**Unit:** `tests/risk/unit/test_tokens.py::test_service_never_exposes_key()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RISK-035`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0008` [ ] `P-RISK-010` - scenarios feature/component (provisional)

- **Execution domain:** `Risk`.
- **Execution position:** `8` of `21`.
- **Cannot start before:** Step `P04-S0007` (`FR-RISK-035`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.10` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RISK-010`); matrix row `557`
- **Source type:** Performance
- **Source responsibility:** Support 500 positions, 100 strategies, 5,000 return points, and 100 scenarios; normal pre-trade work is no worse than O(n²). Exact p95 gates remain proposed until baselined.
- **Source verification:** Representative benchmarks
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RISK-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0009` [ ] `P-RISK-011` - reporting feature/component (provisional)

- **Execution domain:** `Risk`.
- **Execution position:** `9` of `21`.
- **Cannot start before:** Step `P04-S0008` (`P-RISK-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` module `4.11` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RISK-011`); matrix row `558`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RISK-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0010` [ ] `WF-RISK-001` - Build portfolio risk snapshot

- **Execution domain:** `Risk`.
- **Execution position:** `10` of `21`.
- **Cannot start before:** Step `P04-S0009` (`P-RISK-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 265); matrix row `559`.
- **Source scope:** Internal with Data input
- **Source workflow:** Build portfolio risk snapshot
- **Source requirement sequence:** `FR-RISK-004 → FR-RISK-005 → FR-RISK-025`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0011` [ ] `WF-RISK-003` - Assess risk regime

- **Execution domain:** `Risk`.
- **Execution position:** `11` of `21`.
- **Cannot start before:** Step `P04-S0010` (`WF-RISK-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 267); matrix row `560`.
- **Source scope:** Cross-domain
- **Source workflow:** Assess risk regime
- **Source requirement sequence:** `FR-RISK-011 → FR-RISK-031`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0012` [ ] `WF-RISK-005` - Run current portfolio governor

- **Execution domain:** `Risk`.
- **Execution position:** `12` of `21`.
- **Cannot start before:** Step `P04-S0011` (`WF-RISK-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 269); matrix row `561`.
- **Source scope:** Cross-domain
- **Source workflow:** Run current portfolio governor
- **Source requirement sequence:** `FR-RISK-005 → FR-RISK-044 → FR-RISK-041`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0013` [ ] `WF-RISK-010` - Run scenario or what-if analysis

- **Execution domain:** `Risk`.
- **Execution position:** `13` of `21`.
- **Cannot start before:** Step `P04-S0012` (`WF-RISK-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 274); matrix row `562`.
- **Source scope:** Cross-domain
- **Source workflow:** Run scenario or what-if analysis
- **Source requirement sequence:** `FR-RISK-012 → FR-RISK-013 → FR-RISK-045`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0014` [ ] `WF-RISK-011` - Generate risk decision summary

- **Execution domain:** `Risk`.
- **Execution position:** `14` of `21`.
- **Cannot start before:** Step `P04-S0013` (`WF-RISK-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 275); matrix row `563`.
- **Source scope:** Internal/Cross-domain
- **Source workflow:** Generate risk decision summary
- **Source requirement sequence:** `FR-RISK-019 → FR-RISK-046`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0015` [ ] `WF-RISK-014` - Revalidate decision/evidence before reuse

- **Execution domain:** `Risk`.
- **Execution position:** `15` of `21`.
- **Cannot start before:** Step `P04-S0014` (`WF-RISK-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 277); matrix row `564`.
- **Source scope:** Cross-domain
- **Source workflow:** Revalidate decision/evidence before reuse
- **Source requirement sequence:** `FR-RISK-042 → FR-RISK-037`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Trading

Implement `Trading` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P04-S0016` [ ] `FR-TRD-059` - expose one immutable snapshot containing explicit fact values, source, authority, UTC timestamps, freshness, availability, and capability ev...

- **Execution domain:** `Trading`.
- **Execution position:** `16` of `21`.
- **Cannot start before:** Step `P04-S0015` (`WF-RISK-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Validation requirements`` (line 620); matrix row `650`.
- **Source responsibility:** The system shall expose one immutable snapshot containing explicit fact values, source, authority, UTC timestamps, freshness, availability, and capability evidence.
- **Source class / function / method:** `RouteSnapshot`
- **Source side effects:** None
- **Source raises:** `TradingError`: invalid snapshot
- **Source usage / test:** **Usage:** `tests/trading/usage/test_usage_validation.py::test_usage_snapshots_route_snapshot()`<br>**Unit:** `tests/trading/unit/validation/test_snapshots.py::test_route_snapshot_requires_provenance()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-TRD-059`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0017` [ ] `FR-TRD-060` - expose a bounded passed/failed readiness result with failed check codes and evidence references.

- **Execution domain:** `Trading`.
- **Execution position:** `17` of `21`.
- **Cannot start before:** Step `P04-S0016` (`FR-TRD-059`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Validation requirements`` (line 621); matrix row `651`.
- **Source responsibility:** The system shall expose a bounded passed/failed readiness result with failed check codes and evidence references.
- **Source class / function / method:** `ReadinessAssessment`
- **Source side effects:** None
- **Source raises:** `TradingError`: invalid assessment
- **Source usage / test:** **Usage:** `tests/trading/usage/test_usage_validation.py::test_usage_readiness_assessment()`<br>**Unit:** `tests/trading/unit/validation/test_readiness.py::test_readiness_assessment_is_bounded()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-TRD-060`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0018` [ ] `WF-TRD-007` - Activate/enforce kill switch and emergency controls

- **Execution domain:** `Trading`.
- **Execution position:** `18` of `21`.
- **Cannot start before:** Step `P04-S0017` (`FR-TRD-060`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 3. Workflows > Workflow scope values`` (line 264); matrix row `652`.
- **Source scope:** Cross-domain
- **Source workflow:** Enforce kill switch and emergency controls
- **Source requirement sequence:** `FR-TRD-021 → FR-TRD-023`, `FR-TRD-050`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-TRD-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P04-S0019` [ ] `CAP-SIM-006` - Sizing application, accounting, costs, margin, FX

- **Execution domain:** `Simulation`.
- **Execution position:** `19` of `21`.
- **Cannot start before:** Step `P04-S0018` (`WF-TRD-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 453); matrix row `726`.
- **Source final destination:** `accounting/`: `FR-SIM-007`–`FR-SIM-012`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P04-S0020` [ ] `WF-API-003` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `20` of `21`.
- **Cannot start before:** Step `P04-S0019` (`CAP-SIM-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 356); matrix row `1200`.
- **Source scope:** Cross-domain
- **Source workflow:** Authentication, settings, and credential composition
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P04-S0021` [ ] `WF-API-011` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `21` of `21`.
- **Cannot start before:** Step `P04-S0020` (`WF-API-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 364); matrix row `1201`.
- **Source scope:** Cross-domain
- **Source workflow:** Core Edge Lab research
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

## 9. Phase exit demonstration

Execute the roadmap exit criteria exactly as written in Section 2.2. Before the demonstration:

- [ ] All Section 8 requirement items are checked with valid evidence. Evidence: Pending.
- [ ] All Section 7 integration gates pass. Evidence: Pending.
- [ ] Required provider credentials and environment selectors are loaded without logging secret values. Evidence: Pending.
- [ ] Any broker-mutating route proves `MT5_ENVIRONMENT=demo` and all required authorization/risk/kill-switch gates immediately before dispatch. Evidence: Pending.
- [ ] Demonstration inputs, configuration identity, artifact hashes, provider-returned facts, and timestamps are captured. Evidence: Pending.
- [ ] Failure and recovery evidence is captured without fabricating a successful result. Evidence: Pending.

## 10. Phase-close documentation reconciliation

Only after the exit demonstration passes:

1. Update each affected domain README status from `Missing`/`Partial` to the factual implemented state.
2. Cross-reference implemented files, public exports, usage examples, tests, migrations, and operational commands.
3. Remove resolved owner-decision rows and write the resolution as an ordinary authoritative requirement or boundary.
4. Update `docs/ARCHITECTURE.md` for implemented architecture, API, model, dependency, persistence, or runtime changes.
5. Update `docs/CHANGELOG.md` with completed scope, validation evidence, and resolved decisions.
6. Re-run the phase coverage audit and confirm no requirement was moved, duplicated, or silently omitted.
7. Record final README and active-document `path:line` evidence below.

- [ ] Affected domain READMEs reflect factual end-of-phase implementation state. Evidence: Pending.
- [ ] Architecture and changelog updates are complete and consistent. Evidence: Pending.
- [ ] Requirement coverage remains exact after documentation reconciliation. Evidence: Pending.

## 11. Traceability and completion summary

- **Expected assigned IDs:** 21.
- **Plan requirement entries:** 21.
- **Matrix phase:** `4`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (0):** None.
- **Utils (0):** None.
- **Brokers (0):** None.
- **Data (0):** None.
- **Indicators (0):** None.
- **Strategy (0):** None.
- **Risk (15):** `FR-RISK-022`, `FR-RISK-024`, `FR-RISK-028`, `FR-RISK-032`, `FR-RISK-035`, `P-RISK-003`, `P-RISK-006`, `P-RISK-010`, `P-RISK-011`, `WF-RISK-001`, `WF-RISK-003`, `WF-RISK-005`, `WF-RISK-010`, `WF-RISK-011`, `WF-RISK-014`
- **Trading (3):** `FR-TRD-059`, `FR-TRD-060`, `WF-TRD-007`
- **Simulation (1):** `CAP-SIM-006`
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (2):** `WF-API-003`, `WF-API-011`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
