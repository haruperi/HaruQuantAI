# Phase 7 Implementation Plan - v1.7 - Decision-grade analytics

> **Status:** Not started
> **Requirement count:** 16
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 7
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 7. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.7`.
- **Theme:** Decision-grade analytics.
- **Entry condition:** Phase 6 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Render and verify a known-fixture tearsheet and report comparison.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.7 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires shallow metrics; interpretation is cataloged and caveated.

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
| Utils | 0 | No change. |
| Brokers | 0 | No change. |
| Data | 0 | Serve benchmark/FX evidence. |
| Indicators | 0 | No change. |
| Strategy | 0 | No change. |
| Risk | 0 | No change. |
| Trading | 0 | Supply factual fills/costs. |
| Simulation | 1 | Supply complete simulation evidence. |
| Analytics | 14 | Complete metrics, benchmarks, statistics, scorecards, comparisons, allocation evidence, and dashboards. |
| Optimization | 0 | Consume Analytics metrics. |
| Research | 0 | Consume public metric evidence. |
| Portfolio | 0 | Consume allocation evidence. |
| UI/API | 1 | Expose report/comparison/dashboard views. |

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

### Stage 1 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P07-S0001` [ ] `CAP-SIM-008` - Results, artifacts, Analytics boundary

- **Execution domain:** `Simulation`.
- **Execution position:** `1` of `16`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 455); matrix row `743`.
- **Source final destination:** `reporting/`: `FR-SIM-024`–`FR-SIM-028`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Analytics

Implement `Analytics` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P07-S0002` [ ] `P-ANLT-003` - metrics feature/component (provisional)

- **Execution domain:** `Analytics`.
- **Execution position:** `2` of `16`.
- **Cannot start before:** Step `P07-S0001` (`CAP-SIM-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration > Shared configuration consumed by Analytics`` (line 882); matrix row `813`.
- **Source setting / limit:** UTC-first time policy
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-ANLT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0003` [ ] `FR-ANLT-029` - calculate monetary PnL in Decimal and deterministic sorted equity/return evidence with explicit frequency, scale, UTC, and undefined behavior.

- **Execution domain:** `Analytics`.
- **Execution position:** `3` of `16`.
- **Cannot start before:** Step `P07-S0002` (`P-ANLT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.3 `metrics/` — Internal Pure Analytical Evidence > Functional requirements`` (line 663); matrix row `807`.
- **Source responsibility:** The system shall calculate monetary PnL in `Decimal` and deterministic sorted equity/return evidence with explicit frequency, scale, UTC, and undefined behavior.
- **Source class / function / method:** `calculate_return_evidence(result: TradingResult) -> SectionEvidence`
- **Source side effects:** None
- **Source raises:** `AnalyticsValidationError`: curve, frequency, currency, or finite-value policy is invalid
- **Source usage / test:** **Usage:** `tests/analytics/usage/test_usage_metrics.py::test_usage_returns_calculate_return_evidence()`<br>**Unit:** `tests/analytics/unit/test_returns.py::test_return_evidence_sorts_utc_and_records_frequency()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-029`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0004` [ ] `FR-ANLT-030` - calculate core drawdown depth, duration, recovery, ulcer, and pain evidence from approved curves while returning undefined ratios as None wi...

- **Execution domain:** `Analytics`.
- **Execution position:** `4` of `16`.
- **Cannot start before:** Step `P07-S0003` (`FR-ANLT-029`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.3 `metrics/` — Internal Pure Analytical Evidence > Functional requirements`` (line 664); matrix row `808`.
- **Source responsibility:** The system shall calculate core drawdown depth, duration, recovery, ulcer, and pain evidence from approved curves while returning undefined ratios as `None` with warnings.
- **Source class / function / method:** `calculate_drawdown_evidence(result: TradingResult) -> SectionEvidence`
- **Source side effects:** None
- **Source raises:** `AnalyticsValidationError`: curve or drawdown policy is invalid
- **Source usage / test:** **Usage:** `tests/analytics/usage/test_usage_metrics.py::test_usage_drawdowns_calculate_drawdown_evidence()`<br>**Unit:** `tests/analytics/unit/test_drawdowns.py::test_drawdown_evidence_matches_golden_fixture()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-030`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0005` [ ] `FR-ANLT-031` - calculate only approved volatility, VaR, CVaR, and expected-shortfall evidence with cataloged sign, confidence, sample, and units.

- **Execution domain:** `Analytics`.
- **Execution position:** `5` of `16`.
- **Cannot start before:** Step `P07-S0004` (`FR-ANLT-030`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.3 `metrics/` — Internal Pure Analytical Evidence > Functional requirements`` (line 665); matrix row `809`.
- **Source responsibility:** The system shall calculate only approved volatility, VaR, CVaR, and expected-shortfall evidence with cataloged sign, confidence, sample, and units.
- **Source class / function / method:** `calculate_risk_evidence(returns: Sequence[float]) -> SectionEvidence`
- **Source side effects:** None
- **Source raises:** `AnalyticsValidationError`: returns or risk policy is invalid
- **Source usage / test:** **Usage:** `tests/analytics/usage/test_usage_metrics.py::test_usage_risk_calculate_risk_evidence()`<br>**Unit:** `tests/analytics/unit/test_risk.py::test_risk_evidence_uses_cataloged_tail_convention()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-031`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0006` [ ] `FR-ANLT-032` - calculate only approved core ratios and return zero-denominator/insufficient-sample results as None with warnings.

- **Execution domain:** `Analytics`.
- **Execution position:** `6` of `16`.
- **Cannot start before:** Step `P07-S0005` (`FR-ANLT-031`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.3 `metrics/` — Internal Pure Analytical Evidence > Functional requirements`` (line 666); matrix row `810`.
- **Source responsibility:** The system shall calculate only approved core ratios and return zero-denominator/insufficient-sample results as `None` with warnings.
- **Source class / function / method:** `calculate_ratio_evidence(result: TradingResult, returns: Sequence[float]) -> SectionEvidence`
- **Source side effects:** None
- **Source raises:** `AnalyticsValidationError`: formula or annualization policy is absent/invalid
- **Source usage / test:** **Usage:** `tests/analytics/usage/test_usage_metrics.py::test_usage_ratios_calculate_ratio_evidence()`<br>**Unit:** `tests/analytics/unit/test_ratios.py::test_ratio_evidence_never_returns_infinity()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-032`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0007` [ ] `FR-ANLT-035` - use one cataloged implementation for approved moments, percentiles, tails, histogram, and outlier evidence, with constant/short samples hand...

- **Execution domain:** `Analytics`.
- **Execution position:** `7` of `16`.
- **Cannot start before:** Step `P07-S0006` (`FR-ANLT-032`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.3 `metrics/` — Internal Pure Analytical Evidence > Functional requirements`` (line 669); matrix row `811`.
- **Source responsibility:** The system shall use one cataloged implementation for approved moments, percentiles, tails, histogram, and outlier evidence, with constant/short samples handled explicitly.
- **Source class / function / method:** `calculate_distribution_evidence(values: Sequence[float]) -> SectionEvidence`
- **Source side effects:** None
- **Source raises:** `AnalyticsValidationError`: values or selected definition is invalid
- **Source usage / test:** **Usage:** `tests/analytics/usage/test_usage_metrics.py::test_usage_distributions_calculate_evidence()`<br>**Unit:** `tests/analytics/unit/test_distributions.py::test_distribution_constant_sample_is_explicit()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-035`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0008` [ ] `FR-ANLT-037` - calculate supplied cost drag, duration, MAE/MFE, and selected efficiency evidence with documented sign conventions and no source mutation.

- **Execution domain:** `Analytics`.
- **Execution position:** `8` of `16`.
- **Cannot start before:** Step `P07-S0007` (`FR-ANLT-035`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.3 `metrics/` — Internal Pure Analytical Evidence > Functional requirements`` (line 671); matrix row `812`.
- **Source responsibility:** The system shall calculate supplied cost drag, duration, MAE/MFE, and selected efficiency evidence with documented sign conventions and no source mutation.
- **Source class / function / method:** `calculate_cost_efficiency_evidence(result: TradingResult) -> SectionEvidence`
- **Source side effects:** None
- **Source raises:** `AnalyticsValidationError`: cost sign, timestamps, or required fields are invalid
- **Source usage / test:** **Usage:** `tests/analytics/usage/test_usage_metrics.py::test_usage_cost_efficiency_calculate_evidence()`<br>**Unit:** `tests/analytics/unit/test_cost_efficiency.py::test_cost_evidence_preserves_rebates_and_signs()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-037`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0009` [ ] `P-ANLT-005` - scorecards feature/component (provisional)

- **Execution domain:** `Analytics`.
- **Execution position:** `9` of `16`.
- **Cannot start before:** Step `P07-S0008` (`FR-ANLT-037`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > Feature usage examples`` (line 807); matrix row `814`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-ANLT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0010` [ ] `WF-ANLT-002` - Calculate Grouped Analytics Evidence

- **Execution domain:** `Analytics`.
- **Execution position:** `10` of `16`.
- **Cannot start before:** Step `P07-S0009` (`P-ANLT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 256); matrix row `815`.
- **Source scope:** Internal
- **Source workflow:** Calculate grouped analytics evidence
- **Source requirement sequence:** `FR-ANLT-028 → FR-ANLT-038`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0011` [ ] `WF-ANLT-003` - Benchmark-Relative Analysis

- **Execution domain:** `Analytics`.
- **Execution position:** `11` of `16`.
- **Cannot start before:** Step `P07-S0010` (`WF-ANLT-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 257); matrix row `816`.
- **Source scope:** Internal
- **Source workflow:** Benchmark-relative analysis
- **Source requirement sequence:** `FR-ANLT-033 → FR-ANLT-034`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0012` [ ] `WF-ANLT-004` - Evaluate Strategy Quality

- **Execution domain:** `Analytics`.
- **Execution position:** `12` of `16`.
- **Cannot start before:** Step `P07-S0011` (`WF-ANLT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 258); matrix row `817`.
- **Source scope:** Internal
- **Source workflow:** Evaluate strategy quality
- **Source requirement sequence:** `FR-ANLT-044`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0013` [ ] `WF-ANLT-007` - Run Statistical Validation

- **Execution domain:** `Analytics`.
- **Execution position:** `13` of `16`.
- **Cannot start before:** Step `P07-S0012` (`WF-ANLT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 261); matrix row `818`.
- **Source scope:** Internal
- **Source workflow:** Run statistical validation
- **Source requirement sequence:** `FR-ANLT-036`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0014` [ ] `WF-ANLT-008` - Serialize and Hash Report

- **Execution domain:** `Analytics`.
- **Execution position:** `14` of `16`.
- **Cannot start before:** Step `P07-S0013` (`WF-ANLT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 262); matrix row `819`.
- **Source scope:** Internal
- **Source workflow:** Serialize and hash report
- **Source requirement sequence:** `FR-ANLT-025 → FR-ANLT-039 → FR-ANLT-040`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P07-S0015` [ ] `WF-ANLT-010` - Compare Performance Reports

- **Execution domain:** `Analytics`.
- **Execution position:** `15` of `16`.
- **Cannot start before:** Step `P07-S0014` (`WF-ANLT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 264); matrix row `820`.
- **Source scope:** Internal
- **Source workflow:** Compare performance reports
- **Source requirement sequence:** `FR-ANLT-042`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P07-S0016` [ ] `CAP-UI-018` - dashboard reads

- **Execution domain:** `UI/API`.
- **Execution position:** `16` of `16`.
- **Cannot start before:** Step `P07-S0015` (`WF-ANLT-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 309); matrix row `1202`.
- **Source final destination:** `routes/dashboards.py`; `FR-API-032`; currency strength excluded
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-018`.
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

- **Expected assigned IDs:** 16.
- **Plan requirement entries:** 16.
- **Matrix phase:** `7`.
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
- **Risk (0):** None.
- **Trading (0):** None.
- **Simulation (1):** `CAP-SIM-008`
- **Analytics (14):** `FR-ANLT-029`, `FR-ANLT-030`, `FR-ANLT-031`, `FR-ANLT-032`, `FR-ANLT-035`, `FR-ANLT-037`, `P-ANLT-003`, `P-ANLT-005`, `WF-ANLT-002`, `WF-ANLT-003`, `WF-ANLT-004`, `WF-ANLT-007`, `WF-ANLT-008`, `WF-ANLT-010`
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (1):** `CAP-UI-018`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
