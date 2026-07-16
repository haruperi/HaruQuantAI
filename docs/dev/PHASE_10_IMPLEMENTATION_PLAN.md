# Phase 10 Implementation Plan - v1.10 - Reproducible research workflow

> **Status:** Not started
> **Requirement count:** 65
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 10
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 10. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.10`.
- **Theme:** Reproducible research workflow.
- **Entry condition:** Phase 9 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Persist a ResearchReport and hand a reviewed candidate to Strategy.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.10 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires ad hoc research; leakage/multiple testing remain gated.

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
| System | 1 | Cross-domain architecture and workflow control. |
| Utils | 0 | No change. |
| Brokers | 0 | No change. |
| Data | 0 | Supply research-ready data. |
| Indicators | 0 | No change. |
| Strategy | 0 | Accept only reviewed candidates. |
| Risk | 0 | Research remains advisory. |
| Trading | 0 | No change. |
| Simulation | 1 | Expose labeled fast research. |
| Analytics | 0 | Supply public metric evidence. |
| Optimization | 0 | No change. |
| Research | 62 | Complete features, leakage, statistics, studies, seasonality, market structure, PCA/K-Means, profiles, scorecards, rendering, and artifacts. |
| Portfolio | 0 | No change. |
| UI/API | 1 | Expose Edge Lab, artifacts, comparisons, and reviewed handoff. |

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

#### Step `P10-S0001` [ ] `WF-SIM-007` - Non-Canonical Fast Research

- **Execution domain:** `Simulation`.
- **Execution position:** `1` of `65`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 3. Workflows > Workflow scope values`` (line 256); matrix row `748`.
- **Source scope:** Internal
- **Source workflow:** Non-canonical fast research
- **Source requirement sequence:** `FR-SIM-003 → FR-SIM-031`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-SIM-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Research

Implement `Research` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P10-S0002` [ ] `P-RES-003` - features feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `2` of `65`.
- **Cannot start before:** Step `P10-S0001` (`WF-SIM-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-003`); matrix row `1023`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0003` [ ] `P-RES-004` - leakage feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `3` of `65`.
- **Cannot start before:** Step `P10-S0002` (`P-RES-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.4` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-004`); matrix row `1024`
- **Source type:** Leakage
- **Source responsibility:** Forward-looking fields shall be declared, detectable, excluded from feature inputs, and gated before publication.
- **Source verification:** Generated-case leakage tests
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0004` [ ] `P-RES-006` - statistics feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `4` of `65`.
- **Cannot start before:** Step `P10-S0003` (`P-RES-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-006`); matrix row `1025`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0005` [ ] `P-RES-007` - studies feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `5` of `65`.
- **Cannot start before:** Step `P10-S0004` (`P-RES-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.7` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-007`); matrix row `1026`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0006` [ ] `P-RES-008` - seasonality feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `6` of `65`.
- **Cannot start before:** Step `P10-S0005` (`P-RES-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.8` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-008`); matrix row `1027`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0007` [ ] `P-RES-009` - market_structure feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `7` of `65`.
- **Cannot start before:** Step `P10-S0006` (`P-RES-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.9` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-009`); matrix row `1028`
- **Source responsibility:** Build deterministic score rows, final score, uncertainty, readiness/reasons, versions, warnings, and advisory status from approved evidence.
- **Source class / function / method:** `build_research_scorecard(*, metric_profile: CoreMetricProfile, seasonality: Mapping[str, JSONValue] | None, edges: Sequence[EdgeResult], market_structure: MarketStructureProfile | None, modeling: UnsupervisedResearchResult | None, performance: PerformanceReport | None = None) -> ResearchScorecard`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy/dependency: absent prerequisite or incompatible versions
- **Source usage / test:** **Usage:** `test_usage_profiles.py::test_usage_scorecard_build()`<br>**Unit:** `test_scorecard.py::test_scorecard_is_deterministic_and_advisory()`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0008` [ ] `P-RES-010` - modeling feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `8` of `65`.
- **Cannot start before:** Step `P10-S0007` (`P-RES-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.10` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-010`); matrix row `1029`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0009` [ ] `P-RES-012` - artifacts feature/component (provisional)

- **Execution domain:** `Research`.
- **Execution position:** `9` of `65`.
- **Cannot start before:** Step `P10-S0008` (`P-RES-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` module `4.12` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-RES-012`); matrix row `1030`
- **Source type:** Security
- **Source responsibility:** Secrets, credentials, broker/account identifiers, private fields, and forbidden forward fields shall not appear in artifacts, warnings, logs, errors, or audit metadata.
- **Source verification:** Nested masking/security tests
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-RES-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0010` [ ] `FR-RES-032` - Compute arithmetic returns without mutating input and preserve index alignment.

- **Execution domain:** `Research`.
- **Execution position:** `10` of `65`.
- **Cannot start before:** Step `P10-S0009` (`P-RES-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 689); matrix row `978`.
- **Source responsibility:** Compute arithmetic returns without mutating input and preserve index alignment.
- **Source class / function / method:** `simple_returns(close: Series) -> Series`
- **Source side effects:** Read-only
- **Source raises:** invalid/insufficient input
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_calculations_simple_returns`<br>**Unit:** `test_calculations.py::test_simple_returns_constant_series`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-032`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0011` [ ] `FR-RES-033` - Estimate Hurst exponent with explicit minimum sample and finite-value validation.

- **Execution domain:** `Research`.
- **Execution position:** `11` of `65`.
- **Cannot start before:** Step `P10-S0010` (`FR-RES-032`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 690); matrix row `979`.
- **Source responsibility:** Estimate Hurst exponent with explicit minimum sample and finite-value validation.
- **Source class / function / method:** `hurst_exponent(values: Series, *, minimum_samples: int) -> float`
- **Source side effects:** Read-only
- **Source raises:** insufficient/non-finite/constant sample
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_calculations_hurst_exponent`<br>**Unit:** `test_calculations.py::test_hurst_rejects_insufficient_sample`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-033`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0012` [ ] `FR-RES-034` - Compute rolling Hurst values with documented warm-up NaNs and stable alignment.

- **Execution domain:** `Research`.
- **Execution position:** `12` of `65`.
- **Cannot start before:** Step `P10-S0011` (`FR-RES-033`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 691); matrix row `980`.
- **Source responsibility:** Compute rolling Hurst values with documented warm-up NaNs and stable alignment.
- **Source class / function / method:** `rolling_hurst(values: Series, *, window: int, minimum_samples: int) -> Series`
- **Source side effects:** Read-only
- **Source raises:** invalid window/sample
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_calculations_rolling_hurst`<br>**Unit:** `test_calculations.py::test_rolling_hurst_has_declared_warmup`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-034`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0013` [ ] `FR-RES-035` - Compute one canonical horizon-aligned forward return in log or simple mode and mark it research-only.

- **Execution domain:** `Research`.
- **Execution position:** `13` of `65`.
- **Cannot start before:** Step `P10-S0012` (`FR-RES-034`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 692); matrix row `981`.
- **Source responsibility:** Compute one canonical horizon-aligned forward return in log or simple mode and mark it research-only.
- **Source class / function / method:** `forward_returns(close: Series, *, horizon: int, mode: Literal["log", "simple"], output_label: str) -> Series`
- **Source side effects:** Read-only
- **Source raises:** invalid horizon/mode/label
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_calculations_forward_returns`<br>**Unit:** `test_calculations.py::test_forward_returns_never_used_as_feature`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-035`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0014` [ ] `FR-RES-036` - Compute forward maximum favorable excursion for declared side/horizon with trailing unavailability explicit.

- **Execution domain:** `Research`.
- **Execution position:** `14` of `65`.
- **Cannot start before:** Step `P10-S0013` (`FR-RES-035`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 693); matrix row `982`.
- **Source responsibility:** Compute forward maximum favorable excursion for declared side/horizon with trailing unavailability explicit.
- **Source class / function / method:** `forward_max_favorable_excursion(data: DataFrame, *, horizon: int, side: Literal["buy", "sell"]) -> Series`
- **Source side effects:** Read-only
- **Source raises:** invalid side/horizon/OHLC
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_calculations_forward_mfe`<br>**Unit:** `test_calculations.py::test_forward_mfe_buy_sell_direction`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-036`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0015` [ ] `FR-RES-037` - Compute forward maximum adverse excursion for declared side/horizon with trailing unavailability explicit.

- **Execution domain:** `Research`.
- **Execution position:** `15` of `65`.
- **Cannot start before:** Step `P10-S0014` (`FR-RES-036`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 694); matrix row `983`.
- **Source responsibility:** Compute forward maximum adverse excursion for declared side/horizon with trailing unavailability explicit.
- **Source class / function / method:** `forward_max_adverse_excursion(data: DataFrame, *, horizon: int, side: Literal["buy", "sell"]) -> Series`
- **Source side effects:** Read-only
- **Source raises:** invalid side/horizon/OHLC
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_calculations_forward_mae`<br>**Unit:** `test_calculations.py::test_forward_mae_buy_sell_direction`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-037`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0016` [ ] `FR-RES-038` - Build a new feature frame with declared lineage, warm-up/NaN behavior, shared indicator inputs, research-only forward columns, and no input mutation.

- **Execution domain:** `Research`.
- **Execution position:** `16` of `65`.
- **Cannot start before:** Step `P10-S0015` (`FR-RES-037`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 695); matrix row `984`.
- **Source responsibility:** Build a new feature frame with declared lineage, warm-up/NaN behavior, shared indicator inputs, research-only forward columns, and no input mutation.
- **Source class / function / method:** `build_research_feature_frame(prepared: PreparedDataset, *, config: FeatureConfig, limits: ResearchResourceLimits) -> tuple[DataFrame, Mapping[str, JSONValue]]`
- **Source side effects:** Read-only
- **Source raises:** invalid feature/shared dependency/resource
- **Source usage / test:** **Usage:** `test_usage_features.py::test_usage_frame_build_research_feature_frame`<br>**Unit:** `test_frame.py::test_feature_frame_records_lineage_and_forward_columns`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-038`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0017` [ ] `FR-RES-039` - Inspect feature metadata, names, targets, horizons, and declarations and return evidence/severity/recommendation without claiming proof of no leakage.

- **Execution domain:** `Research`.
- **Execution position:** `17` of `65`.
- **Cannot start before:** Step `P10-S0016` (`FR-RES-038`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 736); matrix row `985`.
- **Source responsibility:** Inspect feature metadata, names, targets, horizons, and declarations and return evidence/severity/recommendation without claiming proof of no leakage.
- **Source class / function / method:** `validate_no_lookahead_features(data: DataFrame, *, feature_metadata: Mapping[str, JSONValue], target_column: str | None, allowed_forward_columns: tuple[str,...] = ) -> LeakageReport`
- **Source side effects:** Read-only
- **Source raises:** malformed metadata/missing field
- **Source usage / test:** **Usage:** `test_usage_leakage.py::test_usage_validation_validate_no_lookahead`<br>**Unit:** `test_validation.py::test_leakage_report_detects_forward_target`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-039`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0018` [ ] `FR-RES-040` - Split chronologically into non-overlapping train/validation/test frames with deterministic boundaries and split hash.

- **Execution domain:** `Research`.
- **Execution position:** `18` of `65`.
- **Cannot start before:** Step `P10-S0017` (`FR-RES-039`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 737); matrix row `986`.
- **Source responsibility:** Split chronologically into non-overlapping train/validation/test frames with deterministic boundaries and split hash.
- **Source class / function / method:** `enforce_time_split(data: DataFrame, *, train_fraction: float, validation_fraction: float, gap_rows: int = 0) -> TimeSplitResult`
- **Source side effects:** Read-only
- **Source raises:** invalid fractions/gap/insufficient rows
- **Source usage / test:** **Usage:** `test_usage_leakage.py::test_usage_splitting_enforce_time_split`<br>**Unit:** `test_splitting.py::test_time_split_is_chronological_and_gapped`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-040`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0019` [ ] `FR-RES-041` - Recursively mask sensitive, broker/account, and forbidden forward fields before sharing or serialization without mutating input.

- **Execution domain:** `Research`.
- **Execution position:** `19` of `65`.
- **Cannot start before:** Step `P10-S0018` (`FR-RES-040`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 738); matrix row `987`.
- **Source responsibility:** Recursively mask sensitive, broker/account, and forbidden forward fields before sharing or serialization without mutating input.
- **Source class / function / method:** `mask_research_artifact(artifact: JSONValue, *, extra_sensitive_keys: frozenset[str] = frozenset) -> JSONValue`
- **Source side effects:** Read-only
- **Source raises:** unsupported/non-serializable structure
- **Source usage / test:** **Usage:** `test_usage_leakage.py::test_usage_masking_mask_research_artifact`<br>**Unit:** `test_masking.py::test_masking_covers_nested_sensitive_fields`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-041`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0020` [ ] `FR-RES-051` - Compute a block-bootstrap confidence interval from the seeded distribution.

- **Execution domain:** `Research`.
- **Execution position:** `20` of `65`.
- **Cannot start before:** Step `P10-S0019` (`FR-RES-041`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 819); matrix row `988`.
- **Source responsibility:** Compute a block-bootstrap confidence interval from the seeded distribution.
- **Source class / function / method:** `block_bootstrap_ci(values: NDArray, *, statistic: Callable[[NDArray], float], confidence: float, config: StatisticalConfig) -> tuple[float, float]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid confidence/sample/statistic
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_resampling_ci()`<br>**Unit:** `test_resampling.py::test_ci_rejects_non_finite_statistic()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-051`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0021` [ ] `FR-RES-052` - Compute an empirical permutation p-value with declared alternative and seed.

- **Execution domain:** `Research`.
- **Execution position:** `21` of `65`.
- **Cannot start before:** Step `P10-S0020` (`FR-RES-051`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 820); matrix row `989`.
- **Source responsibility:** Compute an empirical permutation p-value with declared alternative and seed.
- **Source class / function / method:** `permutation_test(observed: float, samples: NDArray, *, alternative: str, config: StatisticalConfig) -> float`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid observed/empty sample/alternative
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_resampling_permutation()`<br>**Unit:** `test_resampling.py::test_permutation_rejects_empty_sample()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-052`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0022` [ ] `FR-RES-053` - Generate a side- and horizon-matched random-entry null in log-return space.

- **Execution domain:** `Research`.
- **Execution position:** `22` of `65`.
- **Cannot start before:** Step `P10-S0021` (`FR-RES-052`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 821); matrix row `990`.
- **Source responsibility:** Generate a side- and horizon-matched random-entry null in log-return space.
- **Source class / function / method:** `random_entry_null(data: DataFrame, *, side: Literal["buy", "sell", "mixed"], hold_bars: int, config: StatisticalConfig) -> NDArray`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid side/horizon/OHLC/sample
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_random_entry()`<br>**Unit:** `test_null_models.py::test_random_entry_null_matches_side()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-053`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0023` [ ] `FR-RES-054` - Generate a seeded null distribution in R-multiple space from declared trade assumptions.

- **Execution domain:** `Research`.
- **Execution position:** `23` of `65`.
- **Cannot start before:** Step `P10-S0022` (`FR-RES-053`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 822); matrix row `991`.
- **Source responsibility:** Generate a seeded null distribution in R-multiple space from declared trade assumptions.
- **Source class / function / method:** `r_space_null(samples: NDArray, *, config: StatisticalConfig) -> NDArray`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: empty/non-finite/invalid config
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_r_space()`<br>**Unit:** `test_null_models.py::test_r_space_null_rejects_non_finite()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-054`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0024` [ ] `FR-RES-055` - Generate a seeded null by shuffling entries only within the same configured session.

- **Execution domain:** `Research`.
- **Execution position:** `24` of `65`.
- **Cannot start before:** Step `P10-S0023` (`FR-RES-054`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 823); matrix row `992`.
- **Source responsibility:** Generate a seeded null by shuffling entries only within the same configured session.
- **Source class / function / method:** `session_randomized_null(data: DataFrame, *, session_column: str, config: StatisticalConfig) -> NDArray`
- **Source side effects:** Read-only
- **Source raises:** invalid session/sample/config
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_session_randomized`<br>**Unit:** `test_null_models.py::test_session_null_preserves_session_groups`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-055`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0025` [ ] `FR-RES-056` - Generate a seeded null by shuffling return blocks while preserving declared block length.

- **Execution domain:** `Research`.
- **Execution position:** `25` of `65`.
- **Cannot start before:** Step `P10-S0024` (`FR-RES-055`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 824); matrix row `993`.
- **Source responsibility:** Generate a seeded null by shuffling return blocks while preserving declared block length.
- **Source class / function / method:** `shuffle_returns_null(returns: Series, *, config: StatisticalConfig) -> NDArray`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid block/sample/non-finite values
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_shuffle_returns()`<br>**Unit:** `test_null_models.py::test_shuffle_null_rejects_large_block()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-056`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0026` [ ] `FR-RES-057` - Compute the observed percentile within a finite non-empty null distribution.

- **Execution domain:** `Research`.
- **Execution position:** `26` of `65`.
- **Cannot start before:** Step `P10-S0025` (`FR-RES-056`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 825); matrix row `994`.
- **Source responsibility:** Compute the observed percentile within a finite non-empty null distribution.
- **Source class / function / method:** `compute_null_percentile(observed: float, distribution: NDArray) -> float`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: non-finite observed/empty/non-finite distribution
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_percentile()`<br>**Unit:** `test_null_models.py::test_percentile_outside_sample_range()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-057`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0027` [ ] `FR-RES-058` - Return finite count, location, dispersion, and declared quantiles for a null distribution.

- **Execution domain:** `Research`.
- **Execution position:** `27` of `65`.
- **Cannot start before:** Step `P10-S0026` (`FR-RES-057`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 826); matrix row `995`.
- **Source responsibility:** Return finite count, location, dispersion, and declared quantiles for a null distribution.
- **Source class / function / method:** `null_distribution_stats(distribution: NDArray) -> Mapping[str, float]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: empty/non-finite distribution
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_stats()`<br>**Unit:** `test_null_models.py::test_null_stats_reject_empty()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-058`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0028` [ ] `FR-RES-059` - Determine threshold exceedance under an explicit upper/lower/two-sided rule.

- **Execution domain:** `Research`.
- **Execution position:** `28` of `65`.
- **Cannot start before:** Step `P10-S0027` (`FR-RES-058`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 827); matrix row `996`.
- **Source responsibility:** Determine threshold exceedance under an explicit upper/lower/two-sided rule.
- **Source class / function / method:** `exceeds_null_threshold(observed: float, distribution: NDArray, *, quantile: float, alternative: str) -> bool`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid quantile/alternative/distribution
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_null_models_threshold()`<br>**Unit:** `test_null_models.py::test_threshold_direction_is_explicit()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-059`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0029` [ ] `FR-RES-060` - Apply Benjamini-Hochberg FDR correction to finite p-values in original order.

- **Execution domain:** `Research`.
- **Execution position:** `29` of `65`.
- **Cannot start before:** Step `P10-S0028` (`FR-RES-059`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 828); matrix row `997`.
- **Source responsibility:** Apply Benjamini-Hochberg FDR correction to finite p-values in original order.
- **Source class / function / method:** `benjamini_hochberg(p_values: Sequence[float], *, q: float) -> NDArray`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: empty/invalid p-values/q
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_corrections_bh()`<br>**Unit:** `test_corrections.py::test_bh_preserves_original_order()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-060`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0030` [ ] `FR-RES-061` - Apply Holm-Bonferroni family-wise correction to finite p-values in original order.

- **Execution domain:** `Research`.
- **Execution position:** `30` of `65`.
- **Cannot start before:** Step `P10-S0029` (`FR-RES-060`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 829); matrix row `998`.
- **Source responsibility:** Apply Holm-Bonferroni family-wise correction to finite p-values in original order.
- **Source class / function / method:** `holm_bonferroni(p_values: Sequence[float], *, alpha: float) -> NDArray`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: empty/invalid p-values/alpha
- **Source usage / test:** **Usage:** `test_usage_statistics.py::test_usage_corrections_holm()`<br>**Unit:** `test_corrections.py::test_holm_rejects_invalid_p_value()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-061`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0031` [ ] `FR-RES-062` - Build seeded random-entry, R-space, and shuffled-return baselines with recorded data/split/config identity.

- **Execution domain:** `Research`.
- **Execution position:** `31` of `65`.
- **Cannot start before:** Step `P10-S0030` (`FR-RES-061`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 863); matrix row `999`.
- **Source responsibility:** Build seeded random-entry, R-space, and shuffled-return baselines with recorded data/split/config identity.
- **Source class / function / method:** `run_eds_null_baseline(data: DataFrame, *, split: TimeSplitResult, statistics: StatisticalConfig, study: StudyConfig) -> EdgeResult`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid/insufficient data/config
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_null_baseline_run()`<br>**Unit:** `test_null_baseline.py::test_baseline_records_seed_and_split()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-062`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0032` [ ] `FR-RES-063` - Compare observed evidence to the correctly matched null and return percentile, threshold, p-value, and warnings.

- **Execution domain:** `Research`.
- **Execution position:** `32` of `65`.
- **Cannot start before:** Step `P10-S0031` (`FR-RES-062`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 864); matrix row `1000`.
- **Source responsibility:** Compare observed evidence to the correctly matched null and return percentile, threshold, p-value, and warnings.
- **Source class / function / method:** `compare_to_null(observed: EdgeResult, baseline: EdgeResult) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: incompatible/malformed results
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_null_baseline_compare()`<br>**Unit:** `test_null_baseline.py::test_compare_rejects_mismatched_side()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-063`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0033` [ ] `FR-RES-064` - Extract versioned acceptance criteria from baseline evidence without hard-coded direction drift.

- **Execution domain:** `Research`.
- **Execution position:** `33` of `65`.
- **Cannot start before:** Step `P10-S0032` (`FR-RES-063`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 865); matrix row `1001`.
- **Source responsibility:** Extract versioned acceptance criteria from baseline evidence without hard-coded direction drift.
- **Source class / function / method:** `get_acceptance_criteria(baseline: EdgeResult) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: absent/incompatible baseline
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_null_baseline_criteria()`<br>**Unit:** `test_null_baseline.py::test_criteria_follow_confirmation_policy()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-064`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0034` [ ] `FR-RES-065` - Evaluate compression/z-score fade mean reversion on declared split data and return advisory uncertainty evidence.

- **Execution domain:** `Research`.
- **Execution position:** `34` of `65`.
- **Cannot start before:** Step `P10-S0033` (`FR-RES-064`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 866); matrix row `1002`.
- **Source responsibility:** Evaluate compression/z-score fade mean reversion on declared split data and return advisory uncertainty evidence.
- **Source class / function / method:** `run_eds_mean_reversion(data: DataFrame, *, split: TimeSplitResult, study: StudyConfig, statistics: StatisticalConfig, limits: ResearchResourceLimits) -> EdgeResult`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid/insufficient/resource/statistical failure
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_edge_studies_mean_reversion()`<br>**Unit:** `test_edge_studies.py::test_mean_reversion_uses_matched_null()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-065`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0035` [ ] `FR-RES-066` - Evaluate high-volatility breakout follow-through on declared split data and return advisory uncertainty evidence.

- **Execution domain:** `Research`.
- **Execution position:** `35` of `65`.
- **Cannot start before:** Step `P10-S0034` (`FR-RES-065`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 867); matrix row `1003`.
- **Source responsibility:** Evaluate high-volatility breakout follow-through on declared split data and return advisory uncertainty evidence.
- **Source class / function / method:** `run_eds_trend_persistence(data: DataFrame, *, split: TimeSplitResult, study: StudyConfig, statistics: StatisticalConfig, limits: ResearchResourceLimits) -> EdgeResult`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid/insufficient/resource/statistical failure
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_edge_studies_trend()`<br>**Unit:** `test_edge_studies.py::test_trend_study_records_rule_config()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-066`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0036` [ ] `FR-RES-067` - Evaluate breakout/fade hypotheses on a frame already tagged by seasonality.tag_sessions and apply multiple-testing correction without redefining session wind...

- **Execution domain:** `Research`.
- **Execution position:** `36` of `65`.
- **Cannot start before:** Step `P10-S0035` (`FR-RES-066`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 868); matrix row `1004`.
- **Source responsibility:** Evaluate breakout/fade hypotheses on a frame already tagged by `seasonality.tag_sessions` and apply multiple-testing correction without redefining session windows.
- **Source class / function / method:** `run_eds_session(tagged_data: DataFrame, *, split: TimeSplitResult, study: StudyConfig, statistics: StatisticalConfig, limits: ResearchResourceLimits) -> EdgeResult`
- **Source side effects:** Read-only
- **Source raises:** missing/invalid canonical session tags, validation, or resource failure
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_edge_studies_session`<br>**Unit:** `test_edge_studies.py::test_session_study_applies_fdr`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-067`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0037` [ ] `FR-RES-068` - Classify mean-reversion and trend evidence using one versioned confirmation policy and preserve uncertainty/advisory status.

- **Execution domain:** `Research`.
- **Execution position:** `37` of `65`.
- **Cannot start before:** Step `P10-S0036` (`FR-RES-067`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 869); matrix row `1005`.
- **Source responsibility:** Classify mean-reversion and trend evidence using one versioned confirmation policy and preserve uncertainty/advisory status.
- **Source class / function / method:** `classify_symbol(mean_reversion: EdgeResult, trend_persistence: EdgeResult, *, policy_version: str) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: incompatible result/policy
- **Source usage / test:** **Usage:** `test_usage_studies.py::test_usage_classification_classify_symbol()`<br>**Unit:** `test_classification.py::test_classification_matches_report_policy()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-068`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0038` [ ] `FR-RES-070` - Return the deterministic primary session label for an hour while preserving overlap evidence.

- **Execution domain:** `Research`.
- **Execution position:** `38` of `65`.
- **Cannot start before:** Step `P10-S0037` (`FR-RES-068`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 908); matrix row `1006`.
- **Source responsibility:** Return the deterministic primary session label for an hour while preserving overlap evidence.
- **Source class / function / method:** `session_label_for_hour(hour: int, *, config: SessionConfig) -> str`
- **Source side effects:** Read-only
- **Source raises:** unmatched/invalid hour
- **Source usage / test:** **Usage:** `test_usage_seasonality.py::test_usage_sessions_label`<br>**Unit:** `test_sessions.py::test_session_label_uses_precedence`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-070`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0039` [ ] `FR-RES-071` - Return a machine-readable payload of timezone, windows, order, overlaps, and schema version.

- **Execution domain:** `Research`.
- **Execution position:** `39` of `65`.
- **Cannot start before:** Step `P10-S0038` (`FR-RES-070`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 909); matrix row `1007`.
- **Source responsibility:** Return a machine-readable payload of timezone, windows, order, overlaps, and schema version.
- **Source class / function / method:** `session_hours_payload(*, config: SessionConfig) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** invalid policy
- **Source usage / test:** **Usage:** `test_usage_seasonality.py::test_usage_sessions_payload`<br>**Unit:** `test_sessions.py::test_session_payload_is_versioned`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-071`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0040` [ ] `FR-RES-072` - Add session labels to a copied timezone-aware frame and record DST/unmatched warnings without changing row order.

- **Execution domain:** `Research`.
- **Execution position:** `40` of `65`.
- **Cannot start before:** Step `P10-S0039` (`FR-RES-071`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 910); matrix row `1008`.
- **Source responsibility:** Add session labels to a copied timezone-aware frame and record DST/unmatched warnings without changing row order.
- **Source class / function / method:** `tag_sessions(data: DataFrame, *, config: SessionConfig) -> tuple[DataFrame, tuple[ResearchWarning,...]]`
- **Source side effects:** Read-only
- **Source raises:** invalid index/timezone/policy
- **Source usage / test:** **Usage:** `test_usage_seasonality.py::test_usage_sessions_tag`<br>**Unit:** `test_sessions.py::test_tag_sessions_handles_cross_midnight`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-072`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0041` [ ] `FR-RES-073` - Define immutable optional calendar, session, symbol, and hour filters without embedding session definitions.

- **Execution domain:** `Research`.
- **Execution position:** `41` of `65`.
- **Cannot start before:** Step `P10-S0040` (`FR-RES-072`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 911); matrix row `1009`.
- **Source responsibility:** Define immutable optional calendar, session, symbol, and hour filters without embedding session definitions.
- **Source class / function / method:** `SeasonalityFilters(years: tuple[int, ...] = (), months: tuple[int, ...] = (), weekdays: tuple[int, ...] = (), hours: tuple[int, ...] = (), sessions: tuple[str, ...] = ())`
- **Source side effects:** None
- **Source raises:** Pending taxonomy: invalid range/filter
- **Source usage / test:** **Usage:** `test_usage_seasonality.py::test_usage_analysis_filters()`<br>**Unit:** `test_analysis.py::test_filters_reject_invalid_month()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-073`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0042` [ ] `FR-RES-074` - Compute calendar/session/hour summaries, sparse-bucket warnings, opportunity windows, and extremes from supplied data and filters.

- **Execution domain:** `Research`.
- **Execution position:** `42` of `65`.
- **Cannot start before:** Step `P10-S0041` (`FR-RES-073`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 912); matrix row `1010`.
- **Source responsibility:** Compute calendar/session/hour summaries, sparse-bucket warnings, opportunity windows, and extremes from supplied data and filters.
- **Source class / function / method:** `run_seasonality(prepared: PreparedDataset, *, sessions: SessionConfig, filters: SeasonalityFilters, limits: ResearchResourceLimits) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** invalid session/data/resource
- **Source usage / test:** **Usage:** `test_usage_seasonality.py::test_usage_analysis_run_seasonality`<br>**Unit:** `test_analysis.py::test_seasonality_warns_sparse_bucket`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-074`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0043` [ ] `FR-RES-076` - Run bounded temporal stability and parameter robustness only when enabled and record windows, variants, duration, and warnings.

- **Execution domain:** `Research`.
- **Execution position:** `43` of `65`.
- **Cannot start before:** Step `P10-S0042` (`FR-RES-074`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 950); matrix row `1011`.
- **Source responsibility:** Run bounded temporal stability and parameter robustness only when enabled and record windows, variants, duration, and warnings.
- **Source class / function / method:** `evaluate_market_structure_quality(prepared: PreparedDataset, *, config: MarketStructureConfig, limits: ResearchResourceLimits) -> MarketStructureQualityReport`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy/resource: disabled/invalid/budget exceeded
- **Source usage / test:** **Usage:** `test_usage_market_structure.py::test_usage_quality_evaluate()`<br>**Unit:** `test_quality.py::test_quality_is_opt_in_and_bounded()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-076`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0044` [ ] `FR-RES-078` - Aggregate prediction evidence by confidence, verdict, symbol, and timeframe with sample counts and warnings.

- **Execution domain:** `Research`.
- **Execution position:** `44` of `65`.
- **Cannot start before:** Step `P10-S0043` (`FR-RES-076`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 952); matrix row `1012`.
- **Source responsibility:** Aggregate prediction evidence by confidence, verdict, symbol, and timeframe with sample counts and warnings.
- **Source class / function / method:** `build_validation_summary(rows: Sequence[Mapping[str, JSONValue]]) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: malformed/insufficient rows
- **Source usage / test:** **Usage:** `test_usage_market_structure.py::test_usage_validation_summary()`<br>**Unit:** `test_validation.py::test_summary_preserves_sample_counts()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-078`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0045` [ ] `FR-RES-079` - Build and rank a bounded candidate grid against approved validation truth using the same canonical score, recording parameters, criteria, window, stability, ...

- **Execution domain:** `Research`.
- **Execution position:** `45` of `65`.
- **Cannot start before:** Step `P10-S0044` (`FR-RES-078`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 953); matrix row `1013`.
- **Source responsibility:** Build and rank a bounded candidate grid against approved validation truth using the same canonical score, recording parameters, criteria, window, stability, and warnings.
- **Source class / function / method:** `calibrate_market_structure(run_rows: Sequence[Mapping[str, JSONValue]], validation_rows: Sequence[Mapping[str, JSONValue]], *, config: MarketStructureConfig, limits: ResearchResourceLimits) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** invalid truth/candidate/resource
- **Source usage / test:** **Usage:** `test_usage_market_structure.py::test_usage_calibration_calibrate`<br>**Unit:** `test_calibration.py::test_calibration_uses_profile_score`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-079`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0046` [ ] `FR-RES-080` - Rank advisory strategy archetypes from profile evidence without mutating or approving Strategy, Risk, or Trading state.

- **Execution domain:** `Research`.
- **Execution position:** `46` of `65`.
- **Cannot start before:** Step `P10-S0045` (`FR-RES-079`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 954); matrix row `1014`.
- **Source responsibility:** Rank advisory strategy archetypes from profile evidence without mutating or approving Strategy, Risk, or Trading state.
- **Source class / function / method:** `build_strategy_fit(profile: MarketStructureProfile) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: malformed/insufficient profile
- **Source usage / test:** **Usage:** `test_usage_market_structure.py::test_usage_fit_build_strategy_fit()`<br>**Unit:** `test_fit.py::test_strategy_fit_is_advisory_only()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-080`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0047` [ ] `FR-RES-082` - Cluster finite feature rows with deterministic K-Means under the effective seed and return labels/centers/diagnostics.

- **Execution domain:** `Research`.
- **Execution position:** `47` of `65`.
- **Cannot start before:** Step `P10-S0046` (`FR-RES-080`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 997); matrix row `1015`.
- **Source responsibility:** Cluster finite feature rows with deterministic K-Means under the effective seed and return labels/centers/diagnostics.
- **Source class / function / method:** `cluster_feature_space(features: DataFrame, *, config: UnsupervisedResearchConfig) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid cluster/sample/seed/data
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_clustering_cluster()`<br>**Unit:** `test_clustering.py::test_clusters_reproduce_with_seed()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-082`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0048` [ ] `FR-RES-083` - Attach aligned labels to a copied feature frame without mutating input or changing row order.

- **Execution domain:** `Research`.
- **Execution position:** `48` of `65`.
- **Cannot start before:** Step `P10-S0047` (`FR-RES-082`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 998); matrix row `1016`.
- **Source responsibility:** Attach aligned labels to a copied feature frame without mutating input or changing row order.
- **Source class / function / method:** `attach_cluster_labels(features: DataFrame, labels: Series, *, column: str = "cluster") -> DataFrame`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: misaligned labels/duplicate column
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_clustering_attach_labels()`<br>**Unit:** `test_clustering.py::test_attach_labels_does_not_mutate()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-083`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0049` [ ] `FR-RES-084` - Return descriptive finite-value, missingness, duplicate, return, and correlation evidence for investment data.

- **Execution domain:** `Research`.
- **Execution position:** `49` of `65`.
- **Cannot start before:** Step `P10-S0048` (`FR-RES-083`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 999); matrix row `1017`.
- **Source responsibility:** Return descriptive finite-value, missingness, duplicate, return, and correlation evidence for investment data.
- **Source class / function / method:** `summarize_investment_data(data: DataFrame) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: empty/invalid data
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_insights_summarize()`<br>**Unit:** `test_insights.py::test_summary_handles_constant_columns()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-084`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0050` [ ] `FR-RES-085` - Extract the largest absolute PCA loadings as interpretable factors with component/feature/sign/magnitude evidence.

- **Execution domain:** `Research`.
- **Execution position:** `50` of `65`.
- **Cannot start before:** Step `P10-S0049` (`FR-RES-084`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 1000); matrix row `1018`.
- **Source responsibility:** Extract the largest absolute PCA loadings as interpretable factors with component/feature/sign/magnitude evidence.
- **Source class / function / method:** `identify_pca_risk_factors(pca: Mapping[str, JSONValue], *, top_count: int) -> tuple[Mapping[str, JSONValue], ...]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: malformed PCA/non-positive count
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_insights_identify_factors()`<br>**Unit:** `test_insights.py::test_factors_rank_absolute_loadings()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-085`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0051` [ ] `FR-RES-086` - Compare clusters using canonical forward returns, sample counts, uncertainty, and semantic advisory names without adapting signals.

- **Execution domain:** `Research`.
- **Execution position:** `51` of `65`.
- **Cannot start before:** Step `P10-S0050` (`FR-RES-085`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 1001); matrix row `1019`.
- **Source responsibility:** Compare clusters using canonical forward returns, sample counts, uncertainty, and semantic advisory names without adapting signals.
- **Source class / function / method:** `analyze_cluster_outperformance(data: DataFrame, labels: Series, *, horizon: int) -> tuple[Mapping[str, JSONValue], ...]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: invalid/misaligned/insufficient data
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_insights_cluster_outperformance()`<br>**Unit:** `test_insights.py::test_cluster_outperformance_records_sample_size()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-086`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0052` [ ] `FR-RES-087` - Combine descriptive, PCA, cluster, factor, and forward evidence with warnings and diagnostics; omit all signal-adaptation behavior.

- **Execution domain:** `Research`.
- **Execution position:** `52` of `65`.
- **Cannot start before:** Step `P10-S0051` (`FR-RES-086`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 1002); matrix row `1020`.
- **Source responsibility:** Combine descriptive, PCA, cluster, factor, and forward evidence with warnings and diagnostics; omit all signal-adaptation behavior.
- **Source class / function / method:** `build_unsupervised_insight_report(features: DataFrame, *, config: UnsupervisedResearchConfig) -> Mapping[str, JSONValue]`
- **Source side effects:** Read-only
- **Source raises:** Pending taxonomy: nested model/validation failure
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_insights_build_report()`<br>**Unit:** `test_insights.py::test_insight_report_has_no_signal_control()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-087`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0053` [ ] `FR-RES-088` - Execute the stateless bounded modeling workflow and return complete reproducibility metadata and advisory status.

- **Execution domain:** `Research`.
- **Execution position:** `53` of `65`.
- **Cannot start before:** Step `P10-S0052` (`FR-RES-087`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 1003); matrix row `1021`.
- **Source responsibility:** Execute the stateless bounded modeling workflow and return complete reproducibility metadata and advisory status.
- **Source class / function / method:** `run_unsupervised_research(features: DataFrame, *, config: UnsupervisedResearchConfig, limits: ResearchResourceLimits) -> UnsupervisedResearchResult`
- **Source side effects:** Read-only
- **Source raises:** invalid/insufficient/resource/model failure
- **Source usage / test:** **Usage:** `test_usage_modeling.py::test_usage_workflow_run_unsupervised`<br>**Unit:** `test_workflow.py::test_workflow_is_stateless_seeded_and_advisory`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-088`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0054` [ ] `FR-RES-097` - Mask and render an approved artifact, enforce allowed root/overwrite/encoding/size/atomic policy, write via temporary replacement, emit a redacted audit even...

- **Execution domain:** `Research`.
- **Execution position:** `54` of `65`.
- **Cannot start before:** Step `P10-S0053` (`FR-RES-088`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 1091); matrix row `1022`.
- **Source responsibility:** Mask and render an approved artifact, enforce allowed root/overwrite/encoding/size/atomic policy, write via temporary replacement, emit a redacted audit event, and return `ArtifactReference`.
- **Source class / function / method:** `write_research_artifact(artifact: ResearchReport | ResearchProfileSnapshot, destination: Path, *, config: ArtifactWriteConfig, auth: AuthContext, limits: ResearchResourceLimits) -> ArtifactReference`
- **Source side effects:** Persistence write; event publication
- **Source raises:** invalid path, traversal, conflict, permission, serialization, size, atomicity, audit failure
- **Source usage / test:** **Usage:** `test_usage_artifacts.py::test_usage_persistence_write_research_artifact`<br>**Unit:** `test_persistence.py::test_write_artifact_masks_and_replaces_atomically`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-RES-097`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0055` [ ] `WF-RES-003` - Build Leakage-Safe Feature Frame and Time Splits

- **Execution domain:** `Research`.
- **Execution position:** `55` of `65`.
- **Cannot start before:** Step `P10-S0054` (`FR-RES-097`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 356); matrix row `1031`.
- **Source scope:** Internal
- **Source workflow:** Build Leakage-Safe Feature Frame and Time Splits
- **Source requirement sequence:** `FR-RES-031 → 041`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0056` [ ] `WF-RES-004` - Analyze Session and Seasonality Opportunity

- **Execution domain:** `Research`.
- **Execution position:** `56` of `65`.
- **Cannot start before:** Step `P10-S0055` (`WF-RES-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 357); matrix row `1032`.
- **Source scope:** Internal
- **Source workflow:** Analyze Session and Seasonality Opportunity
- **Source requirement sequence:** `FR-RES-069 → 074`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0057` [ ] `WF-RES-005` - Run Edge Study Against Null Evidence

- **Execution domain:** `Research`.
- **Execution position:** `57` of `65`.
- **Cannot start before:** Step `P10-S0056` (`WF-RES-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 358); matrix row `1033`.
- **Source scope:** Internal
- **Source workflow:** Run Edge Study Against Null Evidence
- **Source requirement sequence:** `FR-RES-050 → 068`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0058` [ ] `WF-RES-006` - Build Market-Structure Profile

- **Execution domain:** `Research`.
- **Execution position:** `58` of `65`.
- **Cannot start before:** Step `P10-S0057` (`WF-RES-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 359); matrix row `1034`.
- **Source scope:** Internal
- **Source workflow:** Build Market-Structure Profile
- **Source requirement sequence:** `FR-RES-075 → 076, 080`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0059` [ ] `WF-RES-007` - Forward Validate and Calibrate Market Structure

- **Execution domain:** `Research`.
- **Execution position:** `59` of `65`.
- **Cannot start before:** Step `P10-S0058` (`WF-RES-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 360); matrix row `1035`.
- **Source scope:** Internal
- **Source workflow:** Forward Validate and Calibrate Market Structure
- **Source requirement sequence:** `FR-RES-077 → 079`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0060` [ ] `WF-RES-008` - Run Unsupervised Market-Structure Research

- **Execution domain:** `Research`.
- **Execution position:** `60` of `65`.
- **Cannot start before:** Step `P10-S0059` (`WF-RES-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 361); matrix row `1036`.
- **Source scope:** Internal
- **Source workflow:** Run Unsupervised Market-Structure Research
- **Source requirement sequence:** `FR-RES-081 → 088`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0061` [ ] `WF-RES-009` - Build Research Scorecard and Profile Snapshot

- **Execution domain:** `Research`.
- **Execution position:** `61` of `65`.
- **Cannot start before:** Step `P10-S0060` (`WF-RES-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 362); matrix row `1037`.
- **Source scope:** Internal
- **Source workflow:** Build Research Scorecard and Profile Snapshot
- **Source requirement sequence:** `FR-RES-089 → 092`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0062` [ ] `WF-RES-010` - Render and Persist Research Artifact

- **Execution domain:** `Research`.
- **Execution position:** `62` of `65`.
- **Cannot start before:** Step `P10-S0061` (`WF-RES-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 363); matrix row `1038`.
- **Source scope:** Internal
- **Source workflow:** Render and Persist Research Artifact
- **Source requirement sequence:** `FR-RES-093 → 095, 097`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P10-S0063` [ ] `WF-RES-011` - Run Complete Edge Lab Profile

- **Execution domain:** `Research`.
- **Execution position:** `63` of `65`.
- **Cannot start before:** Step `P10-S0062` (`WF-RES-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 3. Workflows > Workflow scope values`` (line 364); matrix row `1039`.
- **Source scope:** Cross-domain
- **Source workflow:** Run Complete Edge Lab Profile
- **Source requirement sequence:** `FR-RES-096` plus selected stage requirements
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RES-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P10-S0064` [ ] `WF-API-009` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `64` of `65`.
- **Cannot start before:** Step `P10-S0063` (`WF-RES-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 362); matrix row `1205`.
- **Source scope:** Cross-domain
- **Source workflow:** Synchronous Optimization and scenario run
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - System integration workflows

Execute cross-domain workflows only after every contributing domain stage above is complete and evidenced.

#### Step `P10-S0065` [ ] `SYS-WF-004` - Research to strategy candidate

- **Execution domain:** `System`.
- **Execution position:** `65` of `65`.
- **Cannot start before:** Step `P10-S0064` (`WF-API-009`).
- **Authoritative dependency evidence:** `SYS-WF-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** Cross-domain integration after all contributing domain stages.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `SYS-WF-001`.
- **Authoritative source:** `docs/PROJECT.md` - ``HaruQuantAI > 4. Cross-Domain Workflows > Status and scope`` (line 383); matrix row `27`.
- **Source workflow:** Research to strategy candidate
- **Source final outcome:** Reviewed strategy registration request entering Strategy validation
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `SYS-WF-004`.
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

- **Expected assigned IDs:** 65.
- **Plan requirement entries:** 65.
- **Matrix phase:** `10`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (1):** `SYS-WF-004`
- **Utils (0):** None.
- **Brokers (0):** None.
- **Data (0):** None.
- **Indicators (0):** None.
- **Strategy (0):** None.
- **Risk (0):** None.
- **Trading (0):** None.
- **Simulation (1):** `WF-SIM-007`
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (62):** `FR-RES-032`, `FR-RES-033`, `FR-RES-034`, `FR-RES-035`, `FR-RES-036`, `FR-RES-037`, `FR-RES-038`, `FR-RES-039`, `FR-RES-040`, `FR-RES-041`, `FR-RES-051`, `FR-RES-052`, `FR-RES-053`, `FR-RES-054`, `FR-RES-055`, `FR-RES-056`, `FR-RES-057`, `FR-RES-058`, `FR-RES-059`, `FR-RES-060`, `FR-RES-061`, `FR-RES-062`, `FR-RES-063`, `FR-RES-064`, `FR-RES-065`, `FR-RES-066`, `FR-RES-067`, `FR-RES-068`, `FR-RES-070`, `FR-RES-071`, `FR-RES-072`, `FR-RES-073`, `FR-RES-074`, `FR-RES-076`, `FR-RES-078`, `FR-RES-079`, `FR-RES-080`, `FR-RES-082`, `FR-RES-083`, `FR-RES-084`, `FR-RES-085`, `FR-RES-086`, `FR-RES-087`, `FR-RES-088`, `FR-RES-097`, `P-RES-003`, `P-RES-004`, `P-RES-006`, `P-RES-007`, `P-RES-008`, `P-RES-009`, `P-RES-010`, `P-RES-012`, `WF-RES-003`, `WF-RES-004`, `WF-RES-005`, `WF-RES-006`, `WF-RES-007`, `WF-RES-008`, `WF-RES-009`, `WF-RES-010`, `WF-RES-011`
- **Portfolio (0):** None.
- **UI/API (1):** `WF-API-009`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
