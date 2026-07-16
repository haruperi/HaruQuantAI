# Phase 6 Implementation Plan - v1.6 - High-fidelity simulation

> **Status:** Not started
> **Requirement count:** 22
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 6
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 6. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.6`.
- **Theme:** High-fidelity simulation.
- **Entry condition:** Phase 5 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Replay a costed FX backtest and reproduce result and artifact hashes.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.6 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires bar-only realism; model risk stays explicit.

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
| Utils | 0 | Serialization/time hash regression. |
| Brokers | 0 | Prove simulation network isolation. |
| Data | 3 | Add FX evidence and simulation modeling boundary. |
| Indicators | 0 | Enforce decision-time availability. |
| Strategy | 4 | Add replay checkpoints. |
| Risk | 0 | Evaluate every sim intent. |
| Trading | 0 | Keep identical sim formulation. |
| Simulation | 15 | Complete tick timeline, pricing, Decimal ledger, costs, margin, journal, replay, artifacts, and official/research modes. |
| Analytics | 0 | Consume richer SimulationResult. |
| Optimization | 0 | Use official Simulation adapter. |
| Research | 0 | Expose labeled fast research. |
| Portfolio | 0 | Add portfolio-backtest projections. |
| UI/API | 0 | Display realism and replay evidence. |

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

### Stage 1 - Data

Implement `Data` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P06-S0001` [ ] `WF-DATA-012` - Simulation Data-Modelling Boundary

- **Execution domain:** `Data`.
- **Execution position:** `1` of `22`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 372); matrix row `346`.
- **Source scope:** Cross-domain
- **Source workflow:** Simulation data-modelling boundary
- **Source requirement sequence:** `FR-DATA-030 → 005`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0002` [ ] `WF-DATA-015` - FX Conversion Evidence

- **Execution domain:** `Data`.
- **Execution position:** `2` of `22`.
- **Cannot start before:** Step `P06-S0001` (`WF-DATA-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 375); matrix row `347`.
- **Source scope:** Cross-domain
- **Source workflow:** FX conversion evidence
- **Source requirement sequence:** `FR-DATA-078 → FR-DATA-079`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0003` [ ] `CAP-DATA-019` - Simulation tick-model boundary

- **Execution domain:** `Data`.
- **Execution position:** `3` of `22`.
- **Cannot start before:** Step `P06-S0002` (`WF-DATA-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 329); matrix row `345`.
- **Source capability:** `CAP-DATA-019` Simulation tick-model boundary
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Strategy

Implement `Strategy` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P06-S0004` [ ] `P-STR-005` - replay feature/component (provisional)

- **Execution domain:** `Strategy`.
- **Execution position:** `4` of `22`.
- **Cannot start before:** Step `P06-S0003` (`CAP-DATA-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 7. Tests and Definition of Done > Package completion checklist`` (line 890); matrix row `479`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-STR-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0005` [ ] `FR-STR-027` - bind strategy/interface/config/data/indicator/simulation/seed/timing identity for deterministic replay.

- **Execution domain:** `Strategy`.
- **Execution position:** `5` of `22`.
- **Cannot start before:** Step `P06-S0004` (`P-STR-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 663); matrix row `477`.
- **Source responsibility:** The system shall bind strategy/interface/config/data/indicator/simulation/seed/timing identity for deterministic replay.
- **Source class / function / method:** `StrategyReplayManifest`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/strategy/usage/test_usage_replay.py::test_usage_models_strategy_replay_manifest()`**Unit:** `tests/strategy/unit/test_replay_models.py::test_manifest_requires_complete_lineage()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-STR-027`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0006` [ ] `FR-STR-028` - contain only serializable, redacted, bounded strategy-local state with identity, schema, checksum, and authorization reference.

- **Execution domain:** `Strategy`.
- **Execution position:** `6` of `22`.
- **Cannot start before:** Step `P06-S0005` (`FR-STR-027`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Functional requirements`` (line 664); matrix row `478`.
- **Source responsibility:** The system shall contain only serializable, redacted, bounded strategy-local state with identity, schema, checksum, and authorization reference.
- **Source class / function / method:** `StrategyCheckpoint`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/strategy/usage/test_usage_replay.py::test_usage_models_strategy_checkpoint()`**Unit:** `tests/strategy/unit/test_replay_models.py::test_checkpoint_rejects_official_state()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-STR-028`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0007` [ ] `WF-STR-005` - Create Replay Manifest and Checkpoint

- **Execution domain:** `Strategy`.
- **Execution position:** `7` of `22`.
- **Cannot start before:** Step `P06-S0006` (`FR-STR-028`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 3. Workflows > Status values`` (line 300); matrix row `480`.
- **Source scope:** Cross-domain
- **Source workflow:** Create replay manifest and checkpoint
- **Source requirement sequence:** `FR-STR-029 → FR-STR-030 → FR-STR-031`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-STR-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P06-S0008` [ ] `P-SIM-002` - timeline feature/component (provisional)

- **Execution domain:** `Simulation`.
- **Execution position:** `8` of `22`.
- **Cannot start before:** Step `P06-S0007` (`WF-STR-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` module `4.2` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Files`` (line 661); matrix row `738`.
- **Source file:** `engine.py`
- **Source responsibility:** Own the canonical tick lifecycle and authoritative simulated execution state.
- **Source key exports:** `EventDrivenExecutionEngine` (`execute_tick`)
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SIM-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0009` [ ] `P-SIM-003` - accounting feature/component (provisional)

- **Execution domain:** `Simulation`.
- **Execution position:** `9` of `22`.
- **Cannot start before:** Step `P06-S0008` (`P-SIM-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration > Approved Phase 1 Error Surface`` (line 853); matrix row `739`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SIM-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0010` [ ] `P-SIM-004` - journal feature/component (provisional)

- **Execution domain:** `Simulation`.
- **Execution position:** `10` of `22`.
- **Cannot start before:** Step `P06-S0009` (`P-SIM-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` module `4.4` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 7. Tests and Definition of Done > Package completion checklist`` (line 912); matrix row `740`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SIM-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0011` [ ] `FR-SIM-004` - expose an immutable UTC tick containing symbol, timestamp, bid, ask, source identity, sequence, and availability metadata with finite positi...

- **Execution domain:** `Simulation`.
- **Execution position:** `11` of `22`.
- **Cannot start before:** Step `P06-S0010` (`P-SIM-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `contracts.py` — Canonical Tick Contract`` (line 529); matrix row `729`.
- **Source responsibility:** The system shall expose an immutable UTC tick containing symbol, timestamp, bid, ask, source identity, sequence, and availability metadata with finite positive prices and `ask >= bid`.
- **Source class / function / method:** `Tick(symbol: str, timestamp: datetime, bid: Decimal, ask: Decimal, source_id: str, sequence: int, available_at: datetime)`
- **Source side effects:** None
- **Source raises:** `ValueError`: invalid timestamp, price, spread, sequence, or metadata
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_timeline.py::test_usage_tick_contract()`<br>**Unit:** `tests/simulator/unit/test_timeline_contracts.py::test_tick_rejects_negative_spread()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0012` [ ] `FR-SIM-007` - verify that the final approved volume is finite, positive, and within symbol min/max/step constraints without increasing, decreasing, or oth...

- **Execution domain:** `Simulation`.
- **Execution position:** `12` of `22`.
- **Cannot start before:** Step `P06-S0011` (`FR-SIM-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `calculations.py` — Stateless Accounting Calculations`` (line 574); matrix row `730`.
- **Source responsibility:** The system shall verify that the final approved volume is finite, positive, and within symbol min/max/step constraints without increasing, decreasing, or otherwise re-sizing it.
- **Source class / function / method:** `normalize_volume(volume: Decimal, specification: Mapping[str, Decimal]) -> Decimal`
- **Source side effects:** None
- **Source raises:** `SimulationError`: `SIM_INVALID_VOLUME`, `SIM_VOLUME_BELOW_MIN`, `SIM_VOLUME_ABOVE_MAX`, or `SIM_VOLUME_STEP_MISMATCH`
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_accounting.py::test_usage_normalize_volume()`<br>**Unit:** `tests/simulator/unit/test_accounting.py::test_normalize_volume_preserves_approved_size()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0013` [ ] `FR-SIM-008` - calculate configured Phase 1 commission and swap deterministically and return an itemized fixed-precision cost mapping.

- **Execution domain:** `Simulation`.
- **Execution position:** `13` of `22`.
- **Cannot start before:** Step `P06-S0012` (`FR-SIM-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `calculations.py` — Stateless Accounting Calculations`` (line 575); matrix row `731`.
- **Source responsibility:** The system shall calculate configured Phase 1 commission and swap deterministically and return an itemized fixed-precision cost mapping.
- **Source class / function / method:** `calculate_execution_costs(fill: Mapping[str, object], model: Mapping[str, object]) -> Mapping[str, Decimal]`
- **Source side effects:** None
- **Source raises:** `SimulationError`: `SIM_COMMISSION_CALCULATION_FAILED`, `SIM_SWAP_CALCULATION_FAILED`, or unsupported model code
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_accounting.py::test_usage_calculate_execution_costs()`<br>**Unit:** `tests/simulator/unit/test_accounting.py::test_calculate_execution_costs_is_exact()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0014` [ ] `FR-SIM-009` - calculate required FX margin from approved symbol evidence, price, volume, and leverage, rejecting insufficient free margin before a fill.

- **Execution domain:** `Simulation`.
- **Execution position:** `14` of `22`.
- **Cannot start before:** Step `P06-S0013` (`FR-SIM-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `calculations.py` — Stateless Accounting Calculations`` (line 576); matrix row `732`.
- **Source responsibility:** The system shall calculate required FX margin from approved symbol evidence, price, volume, and leverage, rejecting insufficient free margin before a fill.
- **Source class / function / method:** `calculate_margin(volume: Decimal, price: Decimal, contract_size: Decimal, leverage: Decimal) -> Decimal`
- **Source side effects:** None
- **Source raises:** `SimulationError`: `SIM_INVALID_CONFIG` or `SIM_INSUFFICIENT_MARGIN`
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_accounting.py::test_usage_calculate_margin()`<br>**Unit:** `tests/simulator/unit/test_accounting.py::test_calculate_margin_rejects_zero_leverage()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0015` [ ] `FR-SIM-011` - atomically apply a simulated fill, realized PnL, commission, swap, and margin effect while preserving balance/equity/free-margin invariants ...

- **Execution domain:** `Simulation`.
- **Execution position:** `15` of `22`.
- **Cannot start before:** Step `P06-S0014` (`FR-SIM-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `ledger.py` — Authoritative Account Ledger`` (line 583); matrix row `733`.
- **Source responsibility:** The system shall atomically apply a simulated fill, realized PnL, commission, swap, and margin effect while preserving balance/equity/free-margin invariants and emitting journal evidence.
- **Source class / function / method:** `AccountLedger.apply_fill(fill: Mapping[str, object]) -> None`
- **Source side effects:** Local state mutation; event publication
- **Source raises:** `SimulationError`: `SIM_ACCOUNT_INVARIANT_BROKEN` or `SIM_INSUFFICIENT_MARGIN`
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_accounting.py::test_usage_ledger_apply_fill()`<br>**Unit:** `tests/simulator/unit/test_ledger.py::test_apply_fill_preserves_account_invariants()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0016` [ ] `FR-SIM-012` - return an immutable read-only fixed-precision account snapshot without exposing mutable engine state.

- **Execution domain:** `Simulation`.
- **Execution position:** `16` of `22`.
- **Cannot start before:** Step `P06-S0015` (`FR-SIM-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `ledger.py` — Authoritative Account Ledger`` (line 584); matrix row `734`.
- **Source responsibility:** The system shall return an immutable read-only fixed-precision account snapshot without exposing mutable engine state.
- **Source class / function / method:** `AccountLedger.snapshot() -> Mapping[str, Decimal]`
- **Source side effects:** Read-only
- **Source raises:** `SimulationError`: `SIM_ACCOUNT_INVARIANT_BROKEN` when current state is inconsistent
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_accounting.py::test_usage_ledger_snapshot()`<br>**Unit:** `tests/simulator/unit/test_ledger.py::test_snapshot_is_immutable()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0017` [ ] `FR-SIM-013` - expose an immutable versioned journal event containing run, sequence, UTC time, event type, redacted payload, previous hash, event hash, cor...

- **Execution domain:** `Simulation`.
- **Execution position:** `17` of `22`.
- **Cannot start before:** Step `P06-S0016` (`FR-SIM-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `contracts.py` — Journal Event Contract`` (line 623); matrix row `735`.
- **Source responsibility:** The system shall expose an immutable versioned journal event containing run, sequence, UTC time, event type, redacted payload, previous hash, event hash, correlation, and causation identities.
- **Source class / function / method:** `JournalEvent(run_id: str, sequence: int, occurred_at: datetime, event_type: str, payload: Mapping[str, object], previous_hash: str, event_hash: str, correlation_id: str, causation_id: str | None, schema_version: str = "v1")`
- **Source side effects:** None
- **Source raises:** `ValueError`: missing identity, invalid sequence/hash, non-UTC time, unsafe payload, or unsupported version
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_journal.py::test_usage_journal_event()`<br>**Unit:** `tests/simulator/unit/test_journal_contracts.py::test_journal_event_rejects_secret_payload()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0018` [ ] `FR-SIM-015` - finalize a completed journal atomically and return its checksum without publishing incomplete temporary artifacts.

- **Execution domain:** `Simulation`.
- **Execution position:** `18` of `22`.
- **Cannot start before:** Step `P06-S0017` (`FR-SIM-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `writer.py` — Streaming Journal Persistence`` (line 630); matrix row `736`.
- **Source responsibility:** The system shall finalize a completed journal atomically and return its checksum without publishing incomplete temporary artifacts.
- **Source class / function / method:** `JournalWriter.finalize() -> str`
- **Source side effects:** Persistence write
- **Source raises:** `SimulationError`: `SIM_PERSISTENCE_FAILED` on flush, checksum, or atomic-finalization failure
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_journal.py::test_usage_journal_finalize()`<br>**Unit:** `tests/simulator/unit/test_journal_writer.py::test_finalize_is_atomic()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0019` [ ] `FR-SIM-017` - return the existing completed run for the same request ID and hash, and reject the same request ID with a different hash.

- **Execution domain:** `Simulation`.
- **Execution position:** `19` of `22`.
- **Cannot start before:** Step `P06-S0018` (`FR-SIM-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `replay.py` — Replay and Idempotency`` (line 637); matrix row `737`.
- **Source responsibility:** The system shall return the existing completed run for the same request ID and hash, and reject the same request ID with a different hash.
- **Source class / function / method:** `resolve_idempotent_run(request_id: str, request_hash: str, lookup: Callable[[str], Mapping[str, str] | None]) -> str | None`
- **Source side effects:** Read-only
- **Source raises:** `SimulationError`: `SIM_RUN_ID_CONFLICT` when an existing request hash differs
- **Source usage / test:** **Usage:** `tests/simulator/usage/test_usage_journal.py::test_usage_resolve_idempotent_run()`<br>**Unit:** `tests/simulator/unit/test_replay.py::test_request_id_conflict_fails_closed()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-SIM-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0020` [ ] `WF-SIM-004` - Severe Data-Quality Block

- **Execution domain:** `Simulation`.
- **Execution position:** `20` of `22`.
- **Cannot start before:** Step `P06-S0019` (`FR-SIM-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 3. Workflows > Workflow scope values`` (line 253); matrix row `741`.
- **Source scope:** Cross-domain
- **Source workflow:** Severe data-quality blocked run
- **Source requirement sequence:** `FR-SIM-002 → FR-SIM-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-SIM-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0021` [ ] `WF-SIM-005` - Deterministic Replay

- **Execution domain:** `Simulation`.
- **Execution position:** `21` of `22`.
- **Cannot start before:** Step `P06-S0020` (`WF-SIM-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 3. Workflows > Workflow scope values`` (line 254); matrix row `742`.
- **Source scope:** Internal
- **Source workflow:** Deterministic replay
- **Source requirement sequence:** `FR-SIM-016`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-SIM-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P06-S0022` [ ] `CAP-SIM-007` - Journal, replay, persistence, idempotency

- **Execution domain:** `Simulation`.
- **Execution position:** `22` of `22`.
- **Cannot start before:** Step `P06-S0021` (`WF-SIM-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 454); matrix row `728`.
- **Source final destination:** `journal/`: `FR-SIM-013`–`FR-SIM-017`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-007`.
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

- **Expected assigned IDs:** 22.
- **Plan requirement entries:** 22.
- **Matrix phase:** `6`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (0):** None.
- **Utils (0):** None.
- **Brokers (0):** None.
- **Data (3):** `CAP-DATA-019`, `WF-DATA-012`, `WF-DATA-015`
- **Indicators (0):** None.
- **Strategy (4):** `FR-STR-027`, `FR-STR-028`, `P-STR-005`, `WF-STR-005`
- **Risk (0):** None.
- **Trading (0):** None.
- **Simulation (15):** `CAP-SIM-007`, `FR-SIM-004`, `FR-SIM-007`, `FR-SIM-008`, `FR-SIM-009`, `FR-SIM-011`, `FR-SIM-012`, `FR-SIM-013`, `FR-SIM-015`, `FR-SIM-017`, `P-SIM-002`, `P-SIM-003`, `P-SIM-004`, `WF-SIM-004`, `WF-SIM-005`
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (0):** None.

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
