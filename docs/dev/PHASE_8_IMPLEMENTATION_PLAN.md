# Phase 8 Implementation Plan - v1.8 - Robust parameter selection

> **Status:** Not started
> **Requirement count:** 29
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 8
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 8. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.8`.
- **Theme:** Robust parameter selection.
- **Entry condition:** Phase 7 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Resume a seeded search and inspect robustness evidence before adoption.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.8 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires naive selection; compute/overfit risk is capped.

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
| Data | 0 | Serve bounded leakage-safe data. |
| Indicators | 0 | No change. |
| Strategy | 0 | Validate candidate/version compatibility. |
| Risk | 0 | No approval implication. |
| Trading | 0 | Simulation route only. |
| Simulation | 3 | Provide deterministic candidate backtests. |
| Analytics | 0 | Provide objectives/caveats. |
| Optimization | 24 | Complete ranking, random search, splits, walk-forward, overfit, Monte Carlo, stress, evidence, state, and API. |
| Research | 0 | No change. |
| Portfolio | 0 | No change. |
| UI/API | 1 | Expose synchronous optimization and explicit adoption. |

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

#### Step `P08-S0001` [ ] `WF-SIM-003` - Optimization Candidate Execution

- **Execution domain:** `Simulation`.
- **Execution position:** `1` of `29`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 3. Workflows > Workflow scope values`` (line 252); matrix row `746`.
- **Source scope:** Cross-domain
- **Source workflow:** Optimization candidate execution
- **Source requirement sequence:** `FR-SIM-030 → FR-SIM-024 → FR-SIM-026`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-SIM-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0002` [ ] `CAP-SIM-012` - Explicit fast-research mode

- **Execution domain:** `Simulation`.
- **Execution position:** `2` of `29`.
- **Cannot start before:** Step `P08-S0001` (`WF-SIM-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 459); matrix row `744`.
- **Source final destination:** `run/`: `FR-SIM-031`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0003` [ ] `CAP-SIM-013` - Optimization/robustness execution boundary

- **Execution domain:** `Simulation`.
- **Execution position:** `3` of `29`.
- **Cannot start before:** Step `P08-S0002` (`CAP-SIM-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 460); matrix row `745`.
- **Source final destination:** `run/`, `reporting/`: `FR-SIM-024`, `FR-SIM-026`, `FR-SIM-030`; search/ranking remain outside Simulation
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Optimization

Implement `Optimization` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P08-S0004` [ ] `P-OPT-002` - scoring feature/component (provisional)

- **Execution domain:** `Optimization`.
- **Execution position:** `4` of `29`.
- **Cannot start before:** Step `P08-S0003` (`CAP-SIM-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.2` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-OPT-002`); matrix row `900`
- **Source file:** `walk_forward.py`
- **Source responsibility:** Execute the single walk-forward workflow
- **Source key exports:** `run_walk_forward_validation`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-OPT-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0005` [ ] `FR-OPT-008` - enumerate the approved calculation names total_return, profit_factor, sharpe, sortino, and calmar; production enablement remains controlled ...

- **Execution domain:** `Optimization`.
- **Execution position:** `5` of `29`.
- **Cannot start before:** Step `P08-S0004` (`P-OPT-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.2 `scoring/` — Objectives, Ranking, and Overfit Evidence > `contracts.py` — Score Contracts`` (line 509); matrix row `884`.
- **Source responsibility:** The system shall enumerate the approved calculation names `total_return`, `profit_factor`, `sharpe`, `sortino`, and `calmar`; production enablement remains controlled by the whitelist.
- **Source class / function / method:** `ObjectiveName: type[StrEnum]`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_scoring.py::test_usage_contracts_objective_name()`<br>**Unit:** `tests/optimization/unit/test_scoring_contracts.py::test_objective_name_values_are_canonical()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0006` [ ] `FR-OPT-009` - represent a candidate score with availability, raw value, objective, trade count, metric evidence, and caveats without substituting another ...

- **Execution domain:** `Optimization`.
- **Execution position:** `6` of `29`.
- **Cannot start before:** Step `P08-S0005` (`FR-OPT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.2 `scoring/` — Objectives, Ranking, and Overfit Evidence > `contracts.py` — Score Contracts`` (line 510); matrix row `885`.
- **Source responsibility:** The system shall represent a candidate score with availability, raw value, objective, trade count, metric evidence, and caveats without substituting another metric.
- **Source class / function / method:** `CandidateScore(candidate_hash: str, objective: ObjectiveName, value: float | None, available: bool, trade_count: int | None, metrics: Mapping[str, float | None], caveats: tuple[str, ...]) -> CandidateScore`
- **Source side effects:** None
- **Source raises:** `pydantic.ValidationError`: score is non-finite or fields are inconsistent
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_scoring.py::test_usage_contracts_candidate_score()`<br>**Unit:** `tests/optimization/unit/test_scoring_contracts.py::test_candidate_score_rejects_non_finite_value()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0007` [ ] `FR-OPT-014` - return a deterministic non-dominated candidate set for explicitly supplied objectives without choosing an unapproved knee point.

- **Execution domain:** `Optimization`.
- **Execution position:** `7` of `29`.
- **Cannot start before:** Step `P08-S0006` (`FR-OPT-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.2 `scoring/` — Objectives, Ranking, and Overfit Evidence > `ranking.py` — Deterministic Selection`` (line 525); matrix row `886`.
- **Source responsibility:** The system shall return a deterministic non-dominated candidate set for explicitly supplied objectives without choosing an unapproved knee point.
- **Source class / function / method:** `select_pareto_candidates(candidates: Sequence[Mapping[str, float]], objectives: Sequence[str]) -> tuple[int, ...]`
- **Source side effects:** None
- **Source raises:** `ValueError`: objectives are empty, missing, or non-finite
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_scoring.py::test_usage_ranking_select_pareto_candidates()`<br>**Unit:** `tests/optimization/unit/test_ranking.py::test_select_pareto_candidates_is_deterministic()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0008` [ ] `P-OPT-005` - validation feature/component (provisional)

- **Execution domain:** `Optimization`.
- **Execution position:** `8` of `29`.
- **Cannot start before:** Step `P08-S0007` (`FR-OPT-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-OPT-005`); matrix row `901`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-OPT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0009` [ ] `FR-OPT-029` - support rolling, anchored, and expanding modes; anchored and expanding have equivalent growing-train semantics.

- **Execution domain:** `Optimization`.
- **Execution position:** `9` of `29`.
- **Cannot start before:** Step `P08-S0008` (`P-OPT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.5 `validation/` — Time-Series Splits and Walk-Forward > `contracts.py` — Validation Contracts`` (line 681); matrix row `887`.
- **Source responsibility:** The system shall support `rolling`, `anchored`, and `expanding` modes; anchored and expanding have equivalent growing-train semantics.
- **Source class / function / method:** `SplitMode: type[StrEnum]`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_validation.py::test_usage_contracts_split_mode()`<br>**Unit:** `tests/optimization/unit/test_validation_contracts.py::test_split_mode_excludes_custom_and_cpcv()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-029`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0010` [ ] `FR-OPT-030` - represent one UTC train/test fold with explicit purge, embargo, and leakage-prevention evidence.

- **Execution domain:** `Optimization`.
- **Execution position:** `10` of `29`.
- **Cannot start before:** Step `P08-S0009` (`FR-OPT-029`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.5 `validation/` — Time-Series Splits and Walk-Forward > `contracts.py` — Validation Contracts`` (line 682); matrix row `888`.
- **Source responsibility:** The system shall represent one UTC train/test fold with explicit purge, embargo, and leakage-prevention evidence.
- **Source class / function / method:** `TimeSeriesSplit(fold_id: str, train_start: datetime, train_end: datetime, test_start: datetime, test_end: datetime, purge_bars: int, embargo_bars: int, leakage_prevented: bool) -> TimeSeriesSplit`
- **Source side effects:** None
- **Source raises:** `pydantic.ValidationError`: boundaries are naive, overlap, reversed, or inconsistent
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_validation.py::test_usage_contracts_time_series_split()`<br>**Unit:** `tests/optimization/unit/test_validation_contracts.py::test_time_series_split_rejects_overlap()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-030`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0011` [ ] `FR-OPT-031` - model one WFA request with a bounded search, mode, windows, purge/embargo, optional average trade duration, and minimum fold count.

- **Execution domain:** `Optimization`.
- **Execution position:** `11` of `29`.
- **Cannot start before:** Step `P08-S0010` (`FR-OPT-030`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.5 `validation/` — Time-Series Splits and Walk-Forward > `contracts.py` — Validation Contracts`` (line 683); matrix row `889`.
- **Source responsibility:** The system shall model one WFA request with a bounded search, mode, windows, purge/embargo, optional average trade duration, and minimum fold count.
- **Source class / function / method:** `WalkForwardRequest(search: SearchRequest, mode: SplitMode, start: datetime, end: datetime, train_bars: int, test_bars: int, step_bars: int, purge_bars: int = 0, embargo_bars: int = 0, average_trade_duration_bars: int | None = None, minimum_fold_count: int = 1) -> WalkForwardRequest`
- **Source side effects:** None
- **Source raises:** `pydantic.ValidationError`: range/window/leakage values are invalid
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_validation.py::test_usage_contracts_walk_forward_request()`<br>**Unit:** `tests/optimization/unit/test_validation_contracts.py::test_walk_forward_request_validates_windows()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-031`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0012` [ ] `FR-OPT-034` - optimize each train fold, evaluate the selected candidate OOS through Simulation, and aggregate evidence without replacing failures with zero.

- **Execution domain:** `Optimization`.
- **Execution position:** `12` of `29`.
- **Cannot start before:** Step `P08-S0011` (`FR-OPT-031`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.5` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.5 `validation/` — Time-Series Splits and Walk-Forward > `splits.py` and `walk_forward.py` — Validation Behavior`` (line 691); matrix row `890`.
- **Source responsibility:** The system shall optimize each train fold, evaluate the selected candidate OOS through Simulation, and aggregate evidence without replacing failures with zero.
- **Source class / function / method:** `run_walk_forward_validation(request: WalkForwardRequest, adapter: BacktestExecutionAdapter, *, enabled_objectives: frozenset[ObjectiveName]) -> WalkForwardResult`
- **Source side effects:** External API call
- **Source raises:** `ValueError`: split/policy evidence is invalid; `OptimizationExecutionError`: candidate execution fails
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_validation.py::test_usage_walk_forward_run_walk_forward_validation()`<br>**Unit:** `tests/optimization/unit/test_walk_forward.py::test_walk_forward_records_fold_failure()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-034`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0013` [ ] `P-OPT-006` - robustness feature/component (provisional)

- **Execution domain:** `Optimization`.
- **Execution position:** `13` of `29`.
- **Cannot start before:** Step `P08-S0012` (`FR-OPT-034`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-OPT-006`); matrix row `902`
- **Source public operation:** `calculate_robustness_score`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-OPT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0014` [ ] `FR-OPT-035` - support shuffle_trades, resample_returns, and block_bootstrap Monte Carlo methods in the initial implementation.

- **Execution domain:** `Optimization`.
- **Execution position:** `14` of `29`.
- **Cannot start before:** Step `P08-S0013` (`P-OPT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.6 `robustness/` — Monte Carlo and Stress Analysis > `contracts.py` — Robustness Contracts`` (line 736); matrix row `891`.
- **Source responsibility:** The system shall support `shuffle_trades`, `resample_returns`, and `block_bootstrap` Monte Carlo methods in the initial implementation.
- **Source class / function / method:** `MonteCarloMethod: type[StrEnum]`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_robustness.py::test_usage_contracts_monte_carlo_method()`<br>**Unit:** `tests/optimization/unit/test_robustness_contracts.py::test_monte_carlo_method_values()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-035`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0015` [ ] `FR-OPT-036` - model bounded Monte Carlo inputs with supplied outcomes, balance, method, simulations, seed, block size, and optional thresholds.

- **Execution domain:** `Optimization`.
- **Execution position:** `15` of `29`.
- **Cannot start before:** Step `P08-S0014` (`FR-OPT-035`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.6 `robustness/` — Monte Carlo and Stress Analysis > `contracts.py` — Robustness Contracts`` (line 737); matrix row `892`.
- **Source responsibility:** The system shall model bounded Monte Carlo inputs with supplied outcomes, balance, method, simulations, seed, block size, and optional thresholds.
- **Source class / function / method:** `MonteCarloRequest(outcomes: tuple[Decimal, ...], initial_balance: Decimal, method: MonteCarloMethod, simulations: int, seed: int, block_size: int | None = None, ruin_threshold: Decimal | None = None, confidence_level: float | None = None) -> MonteCarloRequest`
- **Source side effects:** None
- **Source raises:** `pydantic.ValidationError`: inputs are empty, non-finite, non-positive, or incompatible
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_robustness.py::test_usage_contracts_monte_carlo_request()`<br>**Unit:** `tests/optimization/unit/test_robustness_contracts.py::test_monte_carlo_request_rejects_empty_outcomes()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-036`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0016` [ ] `FR-OPT-037` - represent reproducible path summaries, equity/drawdown percentiles, ruin probability, streak/return evidence, seed provenance, and caveats.

- **Execution domain:** `Optimization`.
- **Execution position:** `16` of `29`.
- **Cannot start before:** Step `P08-S0015` (`FR-OPT-036`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.6 `robustness/` — Monte Carlo and Stress Analysis > `contracts.py` — Robustness Contracts`` (line 738); matrix row `893`.
- **Source responsibility:** The system shall represent reproducible path summaries, equity/drawdown percentiles, ruin probability, streak/return evidence, seed provenance, and caveats.
- **Source class / function / method:** `MonteCarloResult(method: MonteCarloMethod, simulations: int, seed: int, sub_seed_policy: str, final_equity: tuple[Decimal, ...], max_drawdowns: tuple[Decimal, ...], percentiles: Mapping[str, Decimal | None], ruin_probability: float | None, warnings: tuple[str, ...]) -> MonteCarloResult`
- **Source side effects:** None
- **Source raises:** `pydantic.ValidationError`: distributions, counts, or probabilities are inconsistent
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_robustness.py::test_usage_contracts_monte_carlo_result()`<br>**Unit:** `tests/optimization/unit/test_robustness_contracts.py::test_monte_carlo_result_validates_path_count()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-037`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0017` [ ] `FR-OPT-041` - calculate deterministic empirical confidence intervals for validated finite metric samples at a caller-supplied confidence level.

- **Execution domain:** `Optimization`.
- **Execution position:** `17` of `29`.
- **Cannot start before:** Step `P08-S0016` (`FR-OPT-037`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.6 `robustness/` — Monte Carlo and Stress Analysis > `monte_carlo.py`, `stress.py`, and `assessment.py` — Robustness Behavior`` (line 747); matrix row `894`.
- **Source responsibility:** The system shall calculate deterministic empirical confidence intervals for validated finite metric samples at a caller-supplied confidence level.
- **Source class / function / method:** `calculate_confidence_intervals(values: Sequence[Decimal], *, confidence_level: float) -> tuple[Decimal, Decimal]`
- **Source side effects:** None
- **Source raises:** `ValueError`: sample is empty/non-finite or confidence level is outside `(0, 1)`
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_robustness.py::test_usage_monte_carlo_calculate_confidence_intervals()`<br>**Unit:** `tests/optimization/unit/test_monte_carlo.py::test_calculate_confidence_intervals_known_fixture()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-041`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0018` [ ] `P-OPT-008` - state feature/component (provisional)

- **Execution domain:** `Optimization`.
- **Execution position:** `18` of `29`.
- **Cannot start before:** Step `P08-S0017` (`FR-OPT-041`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.8` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-OPT-008`); matrix row `903`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-OPT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0019` [ ] `FR-OPT-050` - define an injected store port limited to Optimization-owned checkpoint/result reads and atomic writes.

- **Execution domain:** `Optimization`.
- **Execution position:** `19` of `29`.
- **Cannot start before:** Step `P08-S0018` (`P-OPT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.8` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.8 `state/` — Optimization-Owned Durable State > Functional requirements`` (line 844); matrix row `895`.
- **Source responsibility:** The system shall define an injected store port limited to Optimization-owned checkpoint/result reads and atomic writes.
- **Source class / function / method:** `OptimizationStateStore`
- **Source side effects:** Read-only; persistence write
- **Source raises:** `OptimizationError`: unavailable store, version conflict, or failed write
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_state.py::test_usage_state_store()`<br>**Unit:** `tests/optimization/unit/test_state_contracts.py::test_store_port_exposes_only_owned_state()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-050`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0020` [ ] `FR-OPT-051` - define immutable checkpoint evidence with schema version, search ID, reproducibility hash, completed-candidate position, deterministic RNG s...

- **Execution domain:** `Optimization`.
- **Execution position:** `20` of `29`.
- **Cannot start before:** Step `P08-S0019` (`FR-OPT-050`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.8` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.8 `state/` — Optimization-Owned Durable State > Functional requirements`` (line 845); matrix row `896`.
- **Source responsibility:** The system shall define immutable checkpoint evidence with schema version, search ID, reproducibility hash, completed-candidate position, deterministic RNG state where applicable, evidence references, and UTC timestamp.
- **Source class / function / method:** `OptimizationCheckpoint`
- **Source side effects:** None
- **Source raises:** `pydantic.ValidationError`: malformed, incomplete, or incompatible checkpoint
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_state.py::test_usage_checkpoint_contract()`<br>**Unit:** `tests/optimization/unit/test_state_contracts.py::test_checkpoint_requires_reproducibility_identity()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-051`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0021` [ ] `FR-OPT-052` - atomically save each completed-candidate checkpoint and recover only an exact schema/search/reproducibility match.

- **Execution domain:** `Optimization`.
- **Execution position:** `21` of `29`.
- **Cannot start before:** Step `P08-S0020` (`FR-OPT-051`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.8` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.8 `state/` — Optimization-Owned Durable State > Functional requirements`` (line 846); matrix row `897`.
- **Source responsibility:** The system shall atomically save each completed-candidate checkpoint and recover only an exact schema/search/reproducibility match.
- **Source class / function / method:** `save_search_checkpoint`, `load_search_checkpoint`
- **Source side effects:** Read-only; persistence write
- **Source raises:** `OptimizationError`: stale version, identity mismatch, or store failure
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_state.py::test_usage_checkpoint_round_trip()`<br>**Unit:** `tests/optimization/unit/test_state_stores.py::test_checkpoint_recovery_requires_exact_hash()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-052`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0022` [ ] `FR-OPT-054` - build artifact locations only beneath the approved result/checkpoint roots from validated search and reproducibility identifiers.

- **Execution domain:** `Optimization`.
- **Execution position:** `22` of `29`.
- **Cannot start before:** Step `P08-S0021` (`FR-OPT-052`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.8` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.8 `state/` — Optimization-Owned Durable State > Functional requirements`` (line 848); matrix row `898`.
- **Source responsibility:** The system shall build artifact locations only beneath the approved result/checkpoint roots from validated search and reproducibility identifiers.
- **Source class / function / method:** `build_optimization_artifact_path(...) -> Path`
- **Source side effects:** None
- **Source raises:** `OptimizationError`: invalid identifier or traversal attempt
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_state.py::test_usage_artifact_path()`<br>**Unit:** `tests/optimization/unit/test_state_artifacts.py::test_artifact_path_cannot_escape_root()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-054`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0023` [ ] `FR-OPT-055` - expose ordered additive Optimization migration definitions for optimization_results and optimization_checkpoints without opening a database.

- **Execution domain:** `Optimization`.
- **Execution position:** `23` of `29`.
- **Cannot start before:** Step `P08-S0022` (`FR-OPT-054`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` module `4.8` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T2 Advanced; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 4. Module and Requirement Specifications > 4.8 `state/` — Optimization-Owned Durable State > Functional requirements`` (line 849); matrix row `899`.
- **Source responsibility:** The system shall expose ordered additive Optimization migration definitions for `optimization_results` and `optimization_checkpoints` without opening a database.
- **Source class / function / method:** `get_optimization_migrations() -> tuple[MigrationDefinition, ...]`
- **Source side effects:** None
- **Source raises:** `OptimizationError`: invalid or non-additive definition
- **Source usage / test:** **Usage:** `tests/optimization/usage/test_usage_state.py::test_usage_migrations()`<br>**Unit:** `tests/optimization/unit/test_state_migrations.py::test_migrations_are_owned_additive_and_ordered()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-OPT-055`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0024` [ ] `WF-OPT-003` - Score, Rank, and Assess Overfit Evidence

- **Execution domain:** `Optimization`.
- **Execution position:** `24` of `29`.
- **Cannot start before:** Step `P08-S0023` (`FR-OPT-055`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 3. Workflows > Workflow scope values`` (line 252); matrix row `904`.
- **Source scope:** Internal
- **Source workflow:** Score, rank, and assess overfit evidence
- **Source requirement sequence:** `FR-OPT-010 → FR-OPT-011 → FR-OPT-012 → FR-OPT-013 → FR-OPT-015`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-OPT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0025` [ ] `WF-OPT-004` - Run Walk-Forward Validation

- **Execution domain:** `Optimization`.
- **Execution position:** `25` of `29`.
- **Cannot start before:** Step `P08-S0024` (`WF-OPT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 3. Workflows > Workflow scope values`` (line 253); matrix row `905`.
- **Source scope:** Cross-domain
- **Source workflow:** Run walk-forward validation
- **Source requirement sequence:** `FR-OPT-032 → FR-OPT-027 → FR-OPT-020 → FR-OPT-033`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-OPT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0026` [ ] `WF-OPT-005` - Run Monte Carlo and Robustness Analysis

- **Execution domain:** `Optimization`.
- **Execution position:** `26` of `29`.
- **Cannot start before:** Step `P08-S0025` (`WF-OPT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 3. Workflows > Workflow scope values`` (line 254); matrix row `906`.
- **Source scope:** Internal
- **Source workflow:** Run Monte Carlo and robustness analysis
- **Source requirement sequence:** `FR-OPT-038 → FR-OPT-039 → FR-OPT-040 → FR-OPT-042 → FR-OPT-043`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-OPT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P08-S0027` [ ] `WF-OPT-006` - Build Versioned Evidence and Handoffs

- **Execution domain:** `Optimization`.
- **Execution position:** `27` of `29`.
- **Cannot start before:** Step `P08-S0026` (`WF-OPT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 3. Workflows > Workflow scope values`` (line 255); matrix row `907`.
- **Source scope:** Cross-domain
- **Source workflow:** Build and persist versioned evidence and handoffs
- **Source requirement sequence:** `FR-OPT-047 → FR-OPT-048 → FR-OPT-053 → FR-OPT-049`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-OPT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P08-S0028` [ ] `CAP-UI-015` - optimization/scenarios

- **Execution domain:** `UI/API`.
- **Execution position:** `28` of `29`.
- **Cannot start before:** Step `P08-S0027` (`WF-OPT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T2 Advanced; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 307); matrix row `1203`.
- **Source final destination:** `routes/optimization.py`; `FR-API-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - System integration workflows

Execute cross-domain workflows only after every contributing domain stage above is complete and evidenced.

#### Step `P08-S0029` [ ] `SYS-WF-003` - Parameter optimization and approved adoption

- **Execution domain:** `System`.
- **Execution position:** `29` of `29`.
- **Cannot start before:** Step `P08-S0028` (`CAP-UI-015`).
- **Authoritative dependency evidence:** `SYS-WF-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** Cross-domain integration after all contributing domain stages.
- **Delivery type:** Workflow integration.
- **Classification:** T2 Advanced; size `M`; source status `Missing`.
- **Dependencies:** `SYS-WF-001`.
- **Authoritative source:** `docs/PROJECT.md` - ``HaruQuantAI > 4. Cross-Domain Workflows > Status and scope`` (line 382); matrix row `23`.
- **Source workflow:** Parameter optimization and approved adoption
- **Source final outcome:** Advisory optimization result and, only after explicit user approval, a new immutable Strategy configuration
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `SYS-WF-003`.
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

- **Expected assigned IDs:** 29.
- **Plan requirement entries:** 29.
- **Matrix phase:** `8`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (1):** `SYS-WF-003`
- **Utils (0):** None.
- **Brokers (0):** None.
- **Data (0):** None.
- **Indicators (0):** None.
- **Strategy (0):** None.
- **Risk (0):** None.
- **Trading (0):** None.
- **Simulation (3):** `CAP-SIM-012`, `CAP-SIM-013`, `WF-SIM-003`
- **Analytics (0):** None.
- **Optimization (24):** `FR-OPT-008`, `FR-OPT-009`, `FR-OPT-014`, `FR-OPT-029`, `FR-OPT-030`, `FR-OPT-031`, `FR-OPT-034`, `FR-OPT-035`, `FR-OPT-036`, `FR-OPT-037`, `FR-OPT-041`, `FR-OPT-050`, `FR-OPT-051`, `FR-OPT-052`, `FR-OPT-054`, `FR-OPT-055`, `P-OPT-002`, `P-OPT-005`, `P-OPT-006`, `P-OPT-008`, `WF-OPT-003`, `WF-OPT-004`, `WF-OPT-005`, `WF-OPT-006`
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (1):** `CAP-UI-015`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
