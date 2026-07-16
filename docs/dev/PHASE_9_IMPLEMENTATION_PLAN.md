# Phase 9 Implementation Plan - v1.9 - Governed multi-strategy portfolios

> **Status:** Not started
> **Requirement count:** 34
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 9
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 9. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.9`.
- **Theme:** Governed multi-strategy portfolios.
- **Entry condition:** Phase 8 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Activate a capped allocation and produce an authorized reduce-only rebalance.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.9 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires single-strategy allocation limits; receiver-owned projections avoid cycles.

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
| System | 3 | Cross-domain architecture and workflow control. |
| Utils | 0 | No change. |
| Brokers | 0 | No change. |
| Data | 0 | Supply market/account/FX truth. |
| Indicators | 0 | No change. |
| Strategy | 0 | Publish eligible immutable references. |
| Risk | 2 | Complete eligibility, allocation review/caps, authoritative budgets, and activation/rebalance authorization. |
| Trading | 1 | Execute only authorized rebalance requests. |
| Simulation | 1 | Run portfolio backtests. |
| Analytics | 2 | Produce allocation/performance evidence. |
| Optimization | 0 | No change. |
| Research | 0 | No change. |
| Portfolio | 24 | Complete construction methods, state, activation, drift, rollback, and rebalancing. |
| UI/API | 1 | Expose portfolio lifecycle workflows. |

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

#### Step `P09-S0001` [ ] `WF-RISK-006` - Review strategy admission

- **Execution domain:** `Risk`.
- **Execution position:** `1` of `34`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 270); matrix row `565`.
- **Source scope:** Cross-domain
- **Source workflow:** Review strategy operational eligibility
- **Source requirement sequence:** `FR-RISK-010 → FR-RISK-029`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0002` [ ] `WF-RISK-007` - Review allocation proposal

- **Execution domain:** `Risk`.
- **Execution position:** `2` of `34`.
- **Cannot start before:** Step `P09-S0001` (`WF-RISK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 3. Workflows > Workflow scope values`` (line 271); matrix row `566`.
- **Source scope:** Cross-domain
- **Source workflow:** Review/activate allocation risk
- **Source requirement sequence:** `FR-RISK-009 → FR-RISK-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-RISK-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Trading

Implement `Trading` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P09-S0003` [ ] `WF-TRD-013` - Execute an Authorized Portfolio Rebalance

- **Execution domain:** `Trading`.
- **Execution position:** `3` of `34`.
- **Cannot start before:** Step `P09-S0002` (`WF-RISK-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 3. Workflows > Workflow scope values`` (line 270); matrix row `657`.
- **Source scope:** Cross-domain
- **Source workflow:** Execute authorized portfolio rebalance
- **Source requirement sequence:** `FR-TRD-024 → FR-TRD-036 → FR-TRD-039`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-TRD-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P09-S0004` [ ] `WF-SIM-009` - Portfolio Backtest

- **Execution domain:** `Simulation`.
- **Execution position:** `4` of `34`.
- **Cannot start before:** Step `P09-S0003` (`WF-TRD-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 3. Workflows > Workflow scope values`` (line 257); matrix row `747`.
- **Source scope:** Cross-domain
- **Source workflow:** Portfolio backtest
- **Source requirement sequence:** `FR-SIM-029 → FR-SIM-010 → FR-SIM-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-SIM-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - Analytics

Implement `Analytics` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P09-S0005` [ ] `WF-ANLT-009` - Build Portfolio Performance Report

- **Execution domain:** `Analytics`.
- **Execution position:** `5` of `34`.
- **Cannot start before:** Step `P09-S0004` (`WF-SIM-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 263); matrix row `821`.
- **Source scope:** Internal
- **Source workflow:** Build portfolio performance report
- **Source requirement sequence:** `FR-ANLT-012 → FR-ANLT-041`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0006` [ ] `WF-ANLT-013` - Build Portfolio Allocation Evidence

- **Execution domain:** `Analytics`.
- **Execution position:** `6` of `34`.
- **Cannot start before:** Step `P09-S0005` (`WF-ANLT-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 3. Workflows > Workflow registry`` (line 265); matrix row `822`.
- **Source scope:** Cross-domain
- **Source workflow:** Build portfolio allocation evidence
- **Source requirement sequence:** `FR-ANLT-012 → FR-ANLT-041`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-ANLT-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 5 - Portfolio

Implement `Portfolio` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P09-S0007` [ ] `P-PORT-002` - evidence feature/component (provisional)

- **Execution domain:** `Portfolio`.
- **Execution position:** `7` of `34`.
- **Cannot start before:** Step `P09-S0006` (`WF-ANLT-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.2` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-PORT-002`); matrix row `1096`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-PORT-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0008` [ ] `FR-PORT-007` - Fail closed on missing, stale, incompatible, cyclic, or unverifiable FX evidence.

- **Execution domain:** `Portfolio`.
- **Execution position:** `8` of `34`.
- **Cannot start before:** Step `P09-S0007` (`P-PORT-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.2 `evidence/` — Evidence and Eligibility Validation`` (line 301); matrix row `1083`.
- **Source requirement:** Fail closed on missing, stale, incompatible, cyclic, or unverifiable FX evidence.
- **Source verification:** FX tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0009` [ ] `FR-PORT-008` - Never synthesize rates, metrics, registrations, or approvals.

- **Execution domain:** `Portfolio`.
- **Execution position:** `9` of `34`.
- **Cannot start before:** Step `P09-S0008` (`FR-PORT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.2 `evidence/` — Evidence and Eligibility Validation`` (line 302); matrix row `1084`.
- **Source requirement:** Never synthesize rates, metrics, registrations, or approvals.
- **Source verification:** Negative tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0010` [ ] `P-PORT-004` - state feature/component (provisional)

- **Execution domain:** `Portfolio`.
- **Execution position:** `10` of `34`.
- **Cannot start before:** Step `P09-S0009` (`FR-PORT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.4` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-PORT-004`); matrix row `1097`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-PORT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0011` [ ] `FR-PORT-031` - Preserve every superseded and rolled-back version.

- **Execution domain:** `Portfolio`.
- **Execution position:** `11` of `34`.
- **Cannot start before:** Step `P09-S0010` (`P-PORT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.4` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.4 `state/` — Portfolio Persistence`` (line 348); matrix row `1093`.
- **Source requirement:** Preserve every superseded and rolled-back version.
- **Source verification:** History tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-031`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0012` [ ] `FR-PORT-032` - Use atomic activation and deterministic idempotency keys.

- **Execution domain:** `Portfolio`.
- **Execution position:** `12` of `34`.
- **Cannot start before:** Step `P09-S0011` (`FR-PORT-031`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.4` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.4 `state/` — Portfolio Persistence`` (line 349); matrix row `1094`.
- **Source requirement:** Use atomic activation and deterministic idempotency keys.
- **Source verification:** Transaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-032`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0013` [ ] `FR-PORT-033` - Store references, hashes, and decisions needed to reproduce lineage.

- **Execution domain:** `Portfolio`.
- **Execution position:** `13` of `34`.
- **Cannot start before:** Step `P09-S0012` (`FR-PORT-032`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.4` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.4 `state/` — Portfolio Persistence`` (line 350); matrix row `1095`.
- **Source requirement:** Store references, hashes, and decisions needed to reproduce lineage.
- **Source verification:** Persistence tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-033`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0014` [ ] `P-PORT-005` - allocation feature/component (provisional)

- **Execution domain:** `Portfolio`.
- **Execution position:** `14` of `34`.
- **Cannot start before:** Step `P09-S0013` (`FR-PORT-033`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-PORT-005`); matrix row `1098`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-PORT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0015` [ ] `FR-PORT-016` - Require explicit human approval for paper/live; allow automatic simulation activation only within simulation policy.

- **Execution domain:** `Portfolio`.
- **Execution position:** `15` of `34`.
- **Cannot start before:** Step `P09-S0014` (`P-PORT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.5 `allocation/` — Version and Activation Governance`` (line 371); matrix row `1085`.
- **Source requirement:** Require explicit human approval for paper/live; allow automatic simulation activation only within simulation policy.
- **Source verification:** Profile tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0016` [ ] `FR-PORT-017` - Block activation while any applicable kill switch is active.

- **Execution domain:** `Portfolio`.
- **Execution position:** `16` of `34`.
- **Cannot start before:** Step `P09-S0015` (`FR-PORT-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.5 `allocation/` — Version and Activation Governance`` (line 372); matrix row `1086`.
- **Source requirement:** Block activation while any applicable kill switch is active.
- **Source verification:** Kill-switch tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0017` [ ] `P-PORT-006` - rebalancing feature/component (provisional)

- **Execution domain:** `Portfolio`.
- **Execution position:** `17` of `34`.
- **Cannot start before:** Step `P09-S0016` (`FR-PORT-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-PORT-006`); matrix row `1099`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-PORT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0018` [ ] `FR-PORT-021` - Route every plan through Risk review before Trading submission.

- **Execution domain:** `Portfolio`.
- **Execution position:** `18` of `34`.
- **Cannot start before:** Step `P09-S0017` (`P-PORT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.6 `rebalancing/` — Drift and Rebalance Planning`` (line 395); matrix row `1087`.
- **Source requirement:** Route every plan through Risk review before Trading submission.
- **Source verification:** Workflow tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-021`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0019` [ ] `FR-PORT-022` - Make existing over-budget correction reduce-only unless a separately authorized risk increase exists.

- **Execution domain:** `Portfolio`.
- **Execution position:** `19` of `34`.
- **Cannot start before:** Step `P09-S0018` (`FR-PORT-021`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.6 `rebalancing/` — Drift and Rebalance Planning`` (line 396); matrix row `1088`.
- **Source requirement:** Make existing over-budget correction reduce-only unless a separately authorized risk increase exists.
- **Source verification:** Safety tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0020` [ ] `FR-PORT-023` - Never open solely to match target weights.

- **Execution domain:** `Portfolio`.
- **Execution position:** `20` of `34`.
- **Cannot start before:** Step `P09-S0019` (`FR-PORT-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.6 `rebalancing/` — Drift and Rebalance Planning`` (line 397); matrix row `1089`.
- **Source requirement:** Never open solely to match target weights.
- **Source verification:** Negative tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-023`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0021` [ ] `P-PORT-007` - orchestration feature/component (provisional)

- **Execution domain:** `Portfolio`.
- **Execution position:** `21` of `34`.
- **Cannot start before:** Step `P09-S0020` (`FR-PORT-023`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.7` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-PORT-007`); matrix row `1100`
- **Source file:** `api.py`
- **Source responsibility:** Expose the typed Portfolio application boundary.
- **Source key exports:** `PortfolioService`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-PORT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0022` [ ] `FR-PORT-026` - Revalidate every mutable/expiring gate immediately before side effects.

- **Execution domain:** `Portfolio`.
- **Execution position:** `22` of `34`.
- **Cannot start before:** Step `P09-S0021` (`P-PORT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.7` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.7 `orchestration/` — Cross-Domain Workflow Coordination`` (line 414); matrix row `1090`.
- **Source requirement:** Revalidate every mutable/expiring gate immediately before side effects.
- **Source verification:** Race tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-026`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0023` [ ] `FR-PORT-027` - Propagate request/correlation/causation IDs end to end.

- **Execution domain:** `Portfolio`.
- **Execution position:** `23` of `34`.
- **Cannot start before:** Step `P09-S0022` (`FR-PORT-026`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.7` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.7 `orchestration/` — Cross-Domain Workflow Coordination`` (line 415); matrix row `1091`.
- **Source requirement:** Propagate request/correlation/causation IDs end to end.
- **Source verification:** Trace tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-027`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0024` [ ] `FR-PORT-028` - Emit redacted audit events for requests, decisions, activation, rollback, and submission.

- **Execution domain:** `Portfolio`.
- **Execution position:** `24` of `34`.
- **Cannot start before:** Step `P09-S0023` (`FR-PORT-027`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` module `4.7` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 4. Module and Requirement Specifications > 4.7 `orchestration/` — Cross-Domain Workflow Coordination`` (line 416); matrix row `1092`.
- **Source requirement:** Emit redacted audit events for requests, decisions, activation, rollback, and submission.
- **Source verification:** Audit tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-PORT-028`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0025` [ ] `WF-PORT-001` - Cross-domain

- **Execution domain:** `Portfolio`.
- **Execution position:** `25` of `34`.
- **Cannot start before:** Step `P09-S0024` (`FR-PORT-028`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 3. Workflows`` (line 168); matrix row `1101`.
- **Source scope:** Cross-domain
- **Source workflow:** Validate construction evidence
- **Source requirement sequence:** `FR-PORT-006 → FR-PORT-009`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-PORT-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0026` [ ] `WF-PORT-003` - Cross-domain

- **Execution domain:** `Portfolio`.
- **Execution position:** `26` of `34`.
- **Cannot start before:** Step `P09-S0025` (`WF-PORT-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 3. Workflows`` (line 170); matrix row `1102`.
- **Source scope:** Cross-domain
- **Source workflow:** Coordinate simulation and Risk review
- **Source requirement sequence:** `FR-PORT-025 → FR-PORT-029`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-PORT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0027` [ ] `WF-PORT-004` - Activate Allocation Version

- **Execution domain:** `Portfolio`.
- **Execution position:** `27` of `34`.
- **Cannot start before:** Step `P09-S0026` (`WF-PORT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 3. Workflows`` (line 171); matrix row `1103`.
- **Source scope:** Cross-domain
- **Source workflow:** Activate allocation version
- **Source requirement sequence:** `FR-PORT-015 → FR-PORT-019`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-PORT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0028` [ ] `WF-PORT-005` - Detect Drift and Plan Rebalance

- **Execution domain:** `Portfolio`.
- **Execution position:** `28` of `34`.
- **Cannot start before:** Step `P09-S0027` (`WF-PORT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 3. Workflows`` (line 172); matrix row `1104`.
- **Source scope:** Cross-domain
- **Source workflow:** Detect drift and plan rebalance
- **Source requirement sequence:** `FR-PORT-020 → FR-PORT-024`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-PORT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0029` [ ] `WF-PORT-006` - Cross-domain

- **Execution domain:** `Portfolio`.
- **Execution position:** `29` of `34`.
- **Cannot start before:** Step `P09-S0028` (`WF-PORT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 3. Workflows`` (line 173); matrix row `1105`.
- **Source scope:** Cross-domain
- **Source workflow:** Submit and measure authorized rebalance
- **Source requirement sequence:** `FR-PORT-025 → FR-PORT-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-PORT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0030` [ ] `WF-PORT-007` - Internal

- **Execution domain:** `Portfolio`.
- **Execution position:** `30` of `34`.
- **Cannot start before:** Step `P09-S0029` (`WF-PORT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 3. Workflows`` (line 174); matrix row `1106`.
- **Source scope:** Internal
- **Source workflow:** Roll back allocation
- **Source requirement sequence:** `FR-PORT-018 → FR-PORT-019`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-PORT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 6 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P09-S0031` [ ] `WF-API-010` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `31` of `34`.
- **Cannot start before:** Step `P09-S0030` (`WF-PORT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 363); matrix row `1204`.
- **Source scope:** Cross-domain
- **Source workflow:** Risk decision support
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 7 - System integration workflows

Execute cross-domain workflows only after every contributing domain stage above is complete and evidenced.

#### Step `P09-S0032` [ ] `SYS-WF-006` - Strategy operational eligibility

- **Execution domain:** `System`.
- **Execution position:** `32` of `34`.
- **Cannot start before:** Step `P09-S0031` (`WF-API-010`).
- **Authoritative dependency evidence:** `SYS-WF-005` completed in Phase 1 before this phase opened.
- **Ordering basis:** Cross-domain integration after all contributing domain stages.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `SYS-WF-005`.
- **Authoritative source:** `docs/PROJECT.md` - ``HaruQuantAI > 4. Cross-Domain Workflows > Status and scope`` (line 385); matrix row `24`.
- **Source workflow:** Strategy operational eligibility
- **Source final outcome:** Versioned route/profile eligibility decision
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `SYS-WF-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0033` [ ] `SYS-WF-007` - Portfolio construction and activation

- **Execution domain:** `System`.
- **Execution position:** `33` of `34`.
- **Cannot start before:** Step `P09-S0032` (`SYS-WF-006`).
- **Authoritative dependency evidence:** `SYS-WF-001` completed in Phase 1 before this phase opened; `SYS-WF-006` at Step `P09-S0032`.
- **Ordering basis:** Cross-domain integration after all contributing domain stages.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `SYS-WF-001`, `SYS-WF-006`.
- **Authoritative source:** `docs/PROJECT.md` - ``HaruQuantAI > 4. Cross-Domain Workflows > Status and scope`` (line 386); matrix row `25`.
- **Source workflow:** Portfolio construction and activation
- **Source final outcome:** Risk-approved active portfolio allocation
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `SYS-WF-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P09-S0034` [ ] `SYS-WF-008` - Governed portfolio rebalance

- **Execution domain:** `System`.
- **Execution position:** `34` of `34`.
- **Cannot start before:** Step `P09-S0033` (`SYS-WF-007`).
- **Authoritative dependency evidence:** `SYS-WF-005` completed in Phase 1 before this phase opened; `SYS-WF-007` at Step `P09-S0033`.
- **Ordering basis:** Cross-domain integration after all contributing domain stages.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `SYS-WF-005`, `SYS-WF-007`.
- **Authoritative source:** `docs/PROJECT.md` - ``HaruQuantAI > 4. Cross-Domain Workflows > Status and scope`` (line 387); matrix row `26`.
- **Source workflow:** Governed portfolio rebalance
- **Source final outcome:** Approved reduce-only rebalance reconciled and measured
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `SYS-WF-008`.
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

- **Expected assigned IDs:** 34.
- **Plan requirement entries:** 34.
- **Matrix phase:** `9`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (3):** `SYS-WF-006`, `SYS-WF-007`, `SYS-WF-008`
- **Utils (0):** None.
- **Brokers (0):** None.
- **Data (0):** None.
- **Indicators (0):** None.
- **Strategy (0):** None.
- **Risk (2):** `WF-RISK-006`, `WF-RISK-007`
- **Trading (1):** `WF-TRD-013`
- **Simulation (1):** `WF-SIM-009`
- **Analytics (2):** `WF-ANLT-009`, `WF-ANLT-013`
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (24):** `FR-PORT-007`, `FR-PORT-008`, `FR-PORT-016`, `FR-PORT-017`, `FR-PORT-021`, `FR-PORT-022`, `FR-PORT-023`, `FR-PORT-026`, `FR-PORT-027`, `FR-PORT-028`, `FR-PORT-031`, `FR-PORT-032`, `FR-PORT-033`, `P-PORT-002`, `P-PORT-004`, `P-PORT-005`, `P-PORT-006`, `P-PORT-007`, `WF-PORT-001`, `WF-PORT-003`, `WF-PORT-004`, `WF-PORT-005`, `WF-PORT-006`, `WF-PORT-007`
- **UI/API (1):** `WF-API-010`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
