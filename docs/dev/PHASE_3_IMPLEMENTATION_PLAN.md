# Phase 3 Implementation Plan - v1.3 - Strategy expressiveness

> **Status:** Not started
> **Requirement count:** 19
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 3
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 3. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.3`.
- **Theme:** Strategy expressiveness.
- **Entry condition:** Phase 2 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Register two strategy versions and reproduce their point-in-time decisions.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.3 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires strategy narrowness; adds state/no-lookahead complexity.

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
| Utils | 0 | Regression only. |
| Brokers | 0 | Contract compatibility regression. |
| Data | 0 | Serve point-in-time multi-timeframe data. |
| Indicators | 10 | Complete official trend, volatility, and momentum indicators. |
| Strategy | 6 | Complete immutable registry/config, arbitrary-code rejection, vectorized/event modes, and replay manifests. |
| Risk | 0 | Review richer intents through stable ports. |
| Trading | 0 | Orchestrate richer decisions without translating signals. |
| Simulation | 2 | Exercise registered strategies and reject raw code. |
| Analytics | 0 | Accept richer metadata. |
| Optimization | 0 | Complete parameter contracts/constraints. |
| Research | 0 | Add feature-frame inputs. |
| Portfolio | 0 | Validate immutable Strategy references. |
| UI/API | 1 | Expose strategy catalogue/version/run views. |

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

### Stage 1 - Indicators

Implement `Indicators` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P03-S0001` [ ] `P-INDI-003` - volatility feature/component (provisional)

- **Execution domain:** `Indicators`.
- **Execution position:** `1` of `19`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 7. Tests and Definition of Done > Test and usage locations`` (line 704); matrix row `414`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-INDI-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0002` [ ] `P-INDI-004` - momentum feature/component (provisional)

- **Execution domain:** `Indicators`.
- **Execution position:** `2` of `19`.
- **Cannot start before:** Step `P03-S0001` (`P-INDI-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` module `4.4` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 7. Tests and Definition of Done > Test and usage locations`` (line 705); matrix row `415`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-INDI-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0003` [ ] `FR-INDI-018` - calculate non-negative ATR per symbol from validated OHLC using the approved true-range/smoothing/seed contract, preserve gap and warmup sem...

- **Execution domain:** `Indicators`.
- **Execution position:** `3` of `19`.
- **Cannot start before:** Step `P03-S0002` (`P-INDI-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `ranges.py` — ATR and ADR`` (line 577); matrix row `409`.
- **Source responsibility:** The system shall calculate non-negative ATR per symbol from validated OHLC using the approved true-range/smoothing/seed contract, preserve gap and warmup semantics, and return causal metadata without input mutation.
- **Source class / function / method:** `atr(data: pd.DataFrame, *, period: int, config: IndicatorConfig | None = None) -> IndicatorResult`
- **Source side effects:** None
- **Source raises:** `IndicatorError`: validation, formula-version, limit, timeout, or atomic calculation failure
- **Source usage / test:** **Usage:** `tests/indicators/usage/test_usage_volatility.py::test_usage_ranges_atr()`<br>**Unit:** `tests/indicators/unit/test_ranges.py::test_atr_matches_approved_gap_fixture()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-INDI-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0004` [ ] `FR-INDI-019` - calculate ADR per symbol using the owner-approved range and session/day convention, preserve warmup rows, and return deterministic availabil...

- **Execution domain:** `Indicators`.
- **Execution position:** `4` of `19`.
- **Cannot start before:** Step `P03-S0003` (`FR-INDI-018`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `ranges.py` — ATR and ADR`` (line 578); matrix row `410`.
- **Source responsibility:** The system shall calculate ADR per symbol using the owner-approved range and session/day convention, preserve warmup rows, and return deterministic availability and manifest metadata.
- **Source class / function / method:** `adr(data: pd.DataFrame, *, period: int, config: IndicatorConfig | None = None) -> IndicatorResult`
- **Source side effects:** None
- **Source raises:** `IndicatorError`: validation, formula-version, limit, timeout, or atomic calculation failure
- **Source usage / test:** **Usage:** `tests/indicators/usage/test_usage_volatility.py::test_usage_ranges_adr()`<br>**Unit:** `tests/indicators/unit/test_ranges.py::test_adr_matches_approved_golden_fixture()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-INDI-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0005` [ ] `FR-INDI-020` - calculate rolling volatility per symbol from the approved simple/log-return, ddof, window, and annualization convention, handling constant/a...

- **Execution domain:** `Indicators`.
- **Execution position:** `5` of `19`.
- **Cannot start before:** Step `P03-S0004` (`FR-INDI-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `rolling.py` — Rolling Volatility`` (line 586); matrix row `411`.
- **Source responsibility:** The system shall calculate rolling volatility per symbol from the approved simple/log-return, ddof, window, and annualization convention, handling constant/all-null windows deterministically and returning causal metadata.
- **Source class / function / method:** `rolling_volatility(data: pd.DataFrame, *, period: int, source: str = "close", config: IndicatorConfig | None = None) -> IndicatorResult`
- **Source side effects:** None
- **Source raises:** `IndicatorError`: validation, formula-version, limit, timeout, or atomic calculation failure
- **Source usage / test:** **Usage:** `tests/indicators/usage/test_usage_volatility.py::test_usage_rolling_rolling_volatility()`<br>**Unit:** `tests/indicators/unit/test_rolling.py::test_rolling_volatility_matches_approved_return_fixture()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-INDI-020`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0006` [ ] `FR-INDI-021` - calculate RSI per symbol using the approved gain/loss smoothing and seed contract, keep values within approved bounds, handle flat/zero-gain...

- **Execution domain:** `Indicators`.
- **Execution position:** `6` of `19`.
- **Cannot start before:** Step `P03-S0005` (`FR-INDI-020`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `oscillators.py` — RSI and Williams %R`` (line 638); matrix row `412`.
- **Source responsibility:** The system shall calculate RSI per symbol using the approved gain/loss smoothing and seed contract, keep values within approved bounds, handle flat/zero-gain/zero-loss windows deterministically, and expose causal metadata.
- **Source class / function / method:** `rsi(data: pd.DataFrame, *, period: int, source: str = "close", config: IndicatorConfig | None = None) -> IndicatorResult`
- **Source side effects:** None
- **Source raises:** `IndicatorError`: validation, formula-version, limit, timeout, or atomic calculation failure
- **Source usage / test:** **Usage:** `tests/indicators/usage/test_usage_momentum.py::test_usage_oscillators_rsi()`<br>**Unit:** `tests/indicators/unit/test_oscillators.py::test_rsi_matches_approved_flat_and_golden_fixtures()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-INDI-021`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0007` [ ] `FR-INDI-022` - calculate Williams %R per symbol over the approved inclusive high/low window, enforce approved bounds and zero-range behavior, preserve warm...

- **Execution domain:** `Indicators`.
- **Execution position:** `7` of `19`.
- **Cannot start before:** Step `P03-S0006` (`FR-INDI-021`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `oscillators.py` — RSI and Williams %R`` (line 639); matrix row `413`.
- **Source responsibility:** The system shall calculate Williams %R per symbol over the approved inclusive high/low window, enforce approved bounds and zero-range behavior, preserve warmup rows, and expose causal metadata.
- **Source class / function / method:** `williams_r(data: pd.DataFrame, *, period: int, config: IndicatorConfig | None = None) -> IndicatorResult`
- **Source side effects:** None
- **Source raises:** `IndicatorError`: validation, formula-version, limit, timeout, or atomic calculation failure
- **Source usage / test:** **Usage:** `tests/indicators/usage/test_usage_momentum.py::test_usage_oscillators_williams_r()`<br>**Unit:** `tests/indicators/unit/test_oscillators.py::test_williams_r_matches_approved_zero_range_fixture()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-INDI-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0008` [ ] `WF-INDI-003` - Warmup Coordination

- **Execution domain:** `Indicators`.
- **Execution position:** `8` of `19`.
- **Cannot start before:** Step `P03-S0007` (`FR-INDI-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 3. Workflows > Workflow register`` (line 217); matrix row `416`.
- **Source scope:** Cross-domain
- **Source workflow:** Warmup coordination
- **Source requirement sequence:** `FR-INDI-005 → FR-INDI-014 → FR-INDI-015..022`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-INDI-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0009` [ ] `WF-INDI-004` - Availability-Aware Multi-Timeframe Calculation

- **Execution domain:** `Indicators`.
- **Execution position:** `9` of `19`.
- **Cannot start before:** Step `P03-S0008` (`WF-INDI-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 3. Workflows > Workflow register`` (line 218); matrix row `417`.
- **Source scope:** Cross-domain
- **Source workflow:** Availability-aware multi-timeframe calculation
- **Source requirement sequence:** `FR-INDI-014 → FR-INDI-015..022 → FR-INDI-007`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-INDI-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0010` [ ] `WF-INDI-005` - Static Registry Discovery and Validation

- **Execution domain:** `Indicators`.
- **Execution position:** `10` of `19`.
- **Cannot start before:** Step `P03-S0009` (`WF-INDI-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 3. Workflows > Workflow register`` (line 219); matrix row `418`.
- **Source scope:** Internal
- **Source workflow:** Static registry discovery and validation
- **Source requirement sequence:** `FR-INDI-011..014`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-INDI-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Strategy

Implement `Strategy` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P03-S0011` [ ] `P-STR-003` - registry feature/component (provisional)

- **Execution domain:** `Strategy`.
- **Execution position:** `11` of `19`.
- **Cannot start before:** Step `P03-S0010` (`WF-INDI-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 7. Tests and Definition of Done > Package completion checklist`` (line 890); matrix row `472`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-STR-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0012` [ ] `P-STR-007` - event feature/component (provisional)

- **Execution domain:** `Strategy`.
- **Execution position:** `12` of `19`.
- **Cannot start before:** Step `P03-S0011` (`P-STR-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` module `4.7` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 7. Tests and Definition of Done > Required test levels`` (line 867); matrix row `473`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-STR-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0013` [ ] `FR-STR-022` - return immutable registry entries in deterministic strategy-id/version order without exposing persistence objects.

- **Execution domain:** `Strategy`.
- **Execution position:** `13` of `19`.
- **Cannot start before:** Step `P03-S0012` (`P-STR-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 597); matrix row `471`.
- **Source source context:** | Missing | `FR-STR-022` | The system shall return immutable registry entries in deterministic strategy-id/version order without exposing persistence objects.                                             | `list_strategy_versions(strategy_id: str                                                                                               | None = None) -> StrategyOutcome[tuple[ValidatedStrategyRef, ...]]` | Read-only                                                                                          | None; returns`STRATEGY_NOT_FOUND` only for an explicit missing id                                                                                                                                                       |
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-STR-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0014` [ ] `WF-STR-003` - Run Stateful Event Strategy Hook

- **Execution domain:** `Strategy`.
- **Execution position:** `14` of `19`.
- **Cannot start before:** Step `P03-S0013` (`FR-STR-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 3. Workflows > Status values`` (line 298); matrix row `474`.
- **Source scope:** Cross-domain
- **Source workflow:** Run stateful event hook
- **Source requirement sequence:** `FR-STR-023 → FR-STR-024 → FR-STR-033`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-STR-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0015` [ ] `WF-STR-008` - Register Immutable Strategy Version

- **Execution domain:** `Strategy`.
- **Execution position:** `15` of `19`.
- **Cannot start before:** Step `P03-S0014` (`WF-STR-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 3. Workflows > Status values`` (line 303); matrix row `475`.
- **Source scope:** Cross-domain
- **Source workflow:** Register immutable strategy version
- **Source requirement sequence:** `FR-STR-020 → FR-STR-021`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-STR-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0016` [ ] `WF-STR-009` - Reject Arbitrary Strategy Code

- **Execution domain:** `Strategy`.
- **Execution position:** `16` of `19`.
- **Cannot start before:** Step `P03-S0015` (`WF-STR-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 3. Workflows > Status values`` (line 304); matrix row `476`.
- **Source scope:** Cross-domain
- **Source workflow:** Reject arbitrary strategy code
- **Source requirement sequence:** `FR-STR-018 → FR-STR-020/021/023/024`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-STR-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P03-S0017` [ ] `WF-SIM-006` - Registered-Strategy Security Rejection

- **Execution domain:** `Simulation`.
- **Execution position:** `17` of `19`.
- **Cannot start before:** Step `P03-S0016` (`WF-STR-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 3. Workflows > Workflow scope values`` (line 255); matrix row `725`.
- **Source scope:** Cross-domain
- **Source workflow:** Registered-strategy security rejection
- **Source requirement sequence:** `FR-SIM-001 → FR-SIM-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-SIM-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P03-S0018` [ ] `CAP-SIM-010` - Strategy and Indicator boundary

- **Execution domain:** `Simulation`.
- **Execution position:** `18` of `19`.
- **Cannot start before:** Step `P03-S0017` (`WF-SIM-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 457); matrix row `724`.
- **Source final destination:** `validation/`, `timeline/`, `run/`: `FR-SIM-001`, `FR-SIM-006`, `FR-SIM-029`, `FR-SIM-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P03-S0019` [ ] `CAP-UI-010` - strategy catalogue/version commands

- **Execution domain:** `UI/API`.
- **Execution position:** `19` of `19`.
- **Cannot start before:** Step `P03-S0018` (`CAP-SIM-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 302); matrix row `1199`.
- **Source final destination:** `routes/strategies.py`; `FR-API-025`; raw import/export/SQX excluded
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-010`.
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

- **Expected assigned IDs:** 19.
- **Plan requirement entries:** 19.
- **Matrix phase:** `3`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (0):** None.
- **Utils (0):** None.
- **Brokers (0):** None.
- **Data (0):** None.
- **Indicators (10):** `FR-INDI-018`, `FR-INDI-019`, `FR-INDI-020`, `FR-INDI-021`, `FR-INDI-022`, `P-INDI-003`, `P-INDI-004`, `WF-INDI-003`, `WF-INDI-004`, `WF-INDI-005`
- **Strategy (6):** `FR-STR-022`, `P-STR-003`, `P-STR-007`, `WF-STR-003`, `WF-STR-008`, `WF-STR-009`
- **Risk (0):** None.
- **Trading (0):** None.
- **Simulation (2):** `CAP-SIM-010`, `WF-SIM-006`
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (1):** `CAP-UI-010`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
