# Phase 11 Implementation Plan - v1.11 - MT5 operational hardening and provider depth

> **Status:** Not started
> **Requirement count:** 30
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 11
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 11. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.11`.
- **Theme:** MT5 operational hardening and provider depth.
- **Entry condition:** Phase 10 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Recover the MT5 demo session, reconcile, emergency-stop, and shut down safely.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.11 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires operational weakness in the already-live demo path.

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
| Utils | 0 | Finalize logging lifecycle/rotation/shutdown. |
| Brokers | 9 | Harden MT5 reconnect/stream/backpressure and add remaining provider depth. |
| Data | 11 | Complete jobs/backfills, feeds, readiness/promotion, and recovery. |
| Indicators | 0 | Live availability regression. |
| Strategy | 1 | Supply live decisions/checkpoint recovery. |
| Risk | 0 | Revalidate approvals and recovery eligibility. |
| Trading | 4 | Complete monitoring, budgets, session recovery, emergency controls, startup reconciliation, and shutdown around the existing demo path. |
| Simulation | 0 | Prove network isolation. |
| Analytics | 0 | Consume stale/unreconciled flags. |
| Optimization | 0 | No change. |
| Research | 0 | No change. |
| Portfolio | 0 | Monitor active allocation/outcomes. |
| UI/API | 4 | Complete streams, readiness, operator incidents, and recovery UI. |

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

### Stage 1 - Brokers

Implement `Brokers` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P11-S0001` [ ] `P-BRK-007` - dukascopy feature/component (provisional)

- **Execution domain:** `Brokers`.
- **Execution position:** `1` of `30`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-BRK-007`); matrix row `243`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-BRK-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0002` [ ] `FR-BRK-126` - dukascopy/instruments.py

- **Execution domain:** `Brokers`.
- **Execution position:** `2` of `30`.
- **Cannot start before:** Step `P11-S0001` (`P-BRK-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1333); matrix row `239`.
- **Source assigned file:** `dukascopy/instruments.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-126`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0003` [ ] `FR-BRK-127` - dukascopy/transport.py

- **Execution domain:** `Brokers`.
- **Execution position:** `3` of `30`.
- **Cannot start before:** Step `P11-S0002` (`FR-BRK-126`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1334); matrix row `240`.
- **Source assigned file:** `dukascopy/transport.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-127`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0004` [ ] `FR-BRK-128` - dukascopy/mapping.py

- **Execution domain:** `Brokers`.
- **Execution position:** `4` of `30`.
- **Cannot start before:** Step `P11-S0003` (`FR-BRK-127`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1335); matrix row `241`.
- **Source assigned file:** `dukascopy/mapping.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-128`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0005` [ ] `FR-BRK-129` - dukascopy/__init__.py

- **Execution domain:** `Brokers`.
- **Execution position:** `5` of `30`.
- **Cannot start before:** Step `P11-S0004` (`FR-BRK-128`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1336); matrix row `242`.
- **Source assigned file:** `dukascopy/__init__.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-129`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0006` [ ] `FR-BRK-107` - expose only genuine bounded Dukascopy ticks for research/development use, advertise exact provider-native symbols only, report production/li...

- **Execution domain:** `Brokers`.
- **Execution position:** `6` of `30`.
- **Cannot start before:** Step `P11-S0005` (`FR-BRK-129`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `adapter.py` — Canonical Dukascopy Adapter`` (line 1198); matrix row `238`.
- **Source responsibility:** The system shall expose only genuine bounded Dukascopy ticks for research/development use, advertise exact provider-native symbols only, report production/live availability as unavailable, and return deterministic unsupported for bars, account, calculation, subscription, and mutation operations.
- **Source class / function / method:** `class DukascopyBrokerAdapter(BrokerAdapter)`
- **Source side effects:** External API call; local session mutation
- **Source raises:** `asyncio.CancelledError`: caller cancels; operational failures are canonical results.
- **Source usage / test:** **Usage:** `tests/brokers/usage/06_dukascopy.py` (standalone script, run via `python`)<br>**Unit:** `tests/brokers/unit/test_dukascopy_adapter.py::test_adapter_get_symbols_filters_by_query()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-107`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0007` [ ] `WF-BRK-006` - Stream Provider and Connection Events

- **Execution domain:** `Brokers`.
- **Execution position:** `7` of `30`.
- **Cannot start before:** Step `P11-S0006` (`FR-BRK-107`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 3. Workflows > Workflow scope values`` (line 311); matrix row `244`.
- **Source scope:** Cross-domain
- **Source workflow:** Stream provider and connection events
- **Source requirement sequence:** `FR-BRK-026 → FR-BRK-112 → FR-BRK-114 → FR-BRK-057 → FR-BRK-068 → FR-BRK-072`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-BRK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0008` [ ] `CAP-BRK-007` - Streaming

- **Execution domain:** `Brokers`.
- **Execution position:** `8` of `30`.
- **Cannot start before:** Step `P11-S0007` (`WF-BRK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 522); matrix row `236`.
- **Source final destination:** FR-BRK-026, 057, 068–072 and provider transports
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0009` [ ] `CAP-BRK-015` - Dukascopy read-only adapter

- **Execution domain:** `Brokers`.
- **Execution position:** `9` of `30`.
- **Cannot start before:** Step `P11-S0008` (`CAP-BRK-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 530); matrix row `237`.
- **Source final destination:** `dukascopy/`; FR-BRK-107
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Data

Implement `Data` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P11-S0010` [ ] `P-DATA-006` - jobs feature/component (provisional)

- **Execution domain:** `Data`.
- **Execution position:** `10` of `30`.
- **Cannot start before:** Step `P11-S0009` (`CAP-BRK-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-DATA-006`); matrix row `355`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-DATA-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0011` [ ] `P-DATA-007` - feeds feature/component (provisional)

- **Execution domain:** `Data`.
- **Execution position:** `11` of `30`.
- **Cannot start before:** Step `P11-S0010` (`P-DATA-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` module `4.7` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-DATA-007`); matrix row `356`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-DATA-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0012` [ ] `FR-DATA-042` - Execute retrieval, normalization, quality, persistence, and checkpoint for one bounded chunk as one recoverable unit, deduplicating a committed key.

- **Execution domain:** `Data`.
- **Execution position:** `12` of `30`.
- **Cannot start before:** Step `P11-S0011` (`P-DATA-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public job runtime API`` (line 1053); matrix row `349`.
- **Source responsibility:** Execute retrieval, normalization, quality, persistence, and checkpoint for one bounded chunk as one recoverable unit, deduplicating a committed key.
- **Source class / function / method:** `execute_backfill_chunk(request: BackfillChunkRequest) -> BackfillChunkResult`
- **Source side effects:** External API call; persistence write
- **Source raises:** `DataError[CONCURRENT_WRITE_LOCKED|DATA_QUALITY_FAILED|DB_WRITE_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/06_update_jobs.py::example_fr_data_042_execute_chunk()`<br>**Unit:** `tests/data/unit/test_backfill.py::test_chunk_commit_and_checkpoint_are_atomic()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-042`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0013` [ ] `FR-DATA-043` - Validate interrupted job leases/checkpoints at startup and resume only after the last committed chunk without publishing partial work.

- **Execution domain:** `Data`.
- **Execution position:** `13` of `30`.
- **Cannot start before:** Step `P11-S0012` (`FR-DATA-042`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public job runtime API`` (line 1054); matrix row `350`.
- **Source responsibility:** Validate interrupted job leases/checkpoints at startup and resume only after the last committed chunk without publishing partial work.
- **Source class / function / method:** `recover_update_jobs(request_id: str | None = None) -> RecoveryReport`
- **Source side effects:** Persistence write
- **Source raises:** `DataError[CHECKPOINT_CORRUPTED|STATE_RECOVERY_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/06_update_jobs.py::example_fr_data_043_recovery()`<br>**Unit:** `tests/data/unit/test_backfill.py::test_recovery_resumes_after_committed_chunk()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-043`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0014` [ ] `FR-DATA-044` - Start or stop a persisted job only after state-transition, lease, source-policy, and schedule validation; recurring execution uses the single-node in-process...

- **Execution domain:** `Data`.
- **Execution position:** `14` of `30`.
- **Cannot start before:** Step `P11-S0013` (`FR-DATA-043`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public job runtime API`` (line 1055); matrix row `351`.
- **Source responsibility:** Start or stop a persisted job only after state-transition, lease, source-policy, and schedule validation; recurring execution uses the single-node in-process asyncio loop, while `run_data_update_job_once` remains independently invokable by an OS scheduler.
- **Source class / function / method:** `schedule_update_job(request: ScheduleJobRequest) -> JobStatus`
- **Source side effects:** Local state mutation; persistence write
- **Source raises:** `DataError[JOB_NOT_FOUND|SCHEDULER_ERROR|POLICY_BLOCKED]`
- **Source usage / test:** **Usage:** `tests/data/usage/06_update_jobs.py::example_fr_data_044_start_stop_worker()`<br>**Unit:** `tests/data/unit/test_scheduler.py::test_scheduler_cannot_report_false_success()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-044`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0015` [ ] `FR-DATA-045` - Return persisted job definition/state, enabled flag, run/checkpoint/error/next-run evidence, lease and recovery state, and request ID without mutation.

- **Execution domain:** `Data`.
- **Execution position:** `15` of `30`.
- **Cannot start before:** Step `P11-S0014` (`FR-DATA-044`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public job runtime API`` (line 1056); matrix row `352`.
- **Source responsibility:** Return persisted job definition/state, enabled flag, run/checkpoint/error/next-run evidence, lease and recovery state, and request ID without mutation.
- **Source class / function / method:** `read_update_job_status(request: JobStatusRequest) -> JobStatus`
- **Source side effects:** Read-only
- **Source raises:** `DataError[JOB_NOT_FOUND|DATABASE_ERROR]`
- **Source usage / test:** **Usage:** `tests/data/usage/06_update_jobs.py::example_fr_data_045_status_query()`<br>**Unit:** `tests/data/unit/test_scheduler.py::test_job_status_reflects_committed_work()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-045`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0016` [ ] `FR-DATA-047` - Normalize each event, update heartbeat/counters, enforce bounded overflow, record gap windows/drops, and reconnect with bounded backoff without hidden histor...

- **Execution domain:** `Data`.
- **Execution position:** `16` of `30`.
- **Cannot start before:** Step `P11-S0015` (`FR-DATA-045`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public feed runtime API`` (line 1105); matrix row `353`.
- **Source responsibility:** Normalize each event, update heartbeat/counters, enforce bounded overflow, record gap windows/drops, and reconnect with bounded backoff without hidden historical repair.
- **Source class / function / method:** `ingest_feed_event(feed_id: str, event: RawFeedEvent) -> FeedEventResult`
- **Source side effects:** Local state mutation; persistence write
- **Source raises:** `DataError[BUFFER_OVERFLOW|DATA_DROPPED|FEED_HEARTBEAT_TIMEOUT]`
- **Source usage / test:** **Usage:** `tests/data/usage/07_realtime_feeds.py::example_fr_data_047_ingest_event()`<br>**Unit:** `tests/data/unit/test_feed_runtime.py::test_overflow_records_gap_without_backfill()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-047`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0017` [ ] `FR-DATA-048` - Return bounded feed ID/state, heartbeat/event times, depth/capacity, dropped/gap/reconnect counts, breaker state, drift, and last safe error from real runtim...

- **Execution domain:** `Data`.
- **Execution position:** `17` of `30`.
- **Cannot start before:** Step `P11-S0016` (`FR-DATA-047`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public feed runtime API`` (line 1106); matrix row `354`.
- **Source responsibility:** Return bounded feed ID/state, heartbeat/event times, depth/capacity, dropped/gap/reconnect counts, breaker state, drift, and last safe error from real runtime state.
- **Source class / function / method:** `read_feed_status(request: FeedStatusRequest) -> FeedStatus`
- **Source side effects:** Read-only
- **Source raises:** `DataError[DATA_NOT_FOUND|DATABASE_ERROR]`
- **Source usage / test:** **Usage:** `tests/data/usage/07_realtime_feeds.py::example_fr_data_048_read_status()`<br>**Unit:** `tests/data/unit/test_feed_status.py::test_status_is_backed_by_real_runtime_state()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-048`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0018` [ ] `WF-DATA-007` - Update Job and Historical Backfill

- **Execution domain:** `Data`.
- **Execution position:** `18` of `30`.
- **Cannot start before:** Step `P11-S0017` (`FR-DATA-048`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 367); matrix row `357`.
- **Source scope:** Internal
- **Source workflow:** Update job and historical backfill
- **Source requirement sequence:** `FR-DATA-041 → 042 → 043/044/045`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0019` [ ] `WF-DATA-008` - Internal Real-Time Feed and Status

- **Execution domain:** `Data`.
- **Execution position:** `19` of `30`.
- **Cannot start before:** Step `P11-S0018` (`WF-DATA-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 368); matrix row `358`.
- **Source scope:** Cross-domain
- **Source workflow:** Internal real-time feed and status
- **Source requirement sequence:** `FR-DATA-046 → 047 → 048`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0020` [ ] `CAP-DATA-010` - Internal real-time feed lifecycle

- **Execution domain:** `Data`.
- **Execution position:** `20` of `30`.
- **Cannot start before:** Step `P11-S0019` (`WF-DATA-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 320); matrix row `348`.
- **Source capability:** `CAP-DATA-010` Internal real-time feed lifecycle
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Strategy

Implement `Strategy` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P11-S0021` [ ] `WF-STR-007` - Supply Paper/Live Decisions

- **Execution domain:** `Strategy`.
- **Execution position:** `21` of `30`.
- **Cannot start before:** Step `P11-S0020` (`CAP-DATA-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 3. Workflows > Status values`` (line 302); matrix row `481`.
- **Source scope:** Cross-domain
- **Source workflow:** Supply paper/live decisions
- **Source requirement sequence:** `FR-STR-023 → FR-STR-024 → FR-STR-032/033`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-STR-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - Trading

Implement `Trading` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P11-S0022` [ ] `P-TRD-006` - monitoring feature/component (provisional)

- **Execution domain:** `Trading`.
- **Execution position:** `22` of `30`.
- **Cannot start before:** Step `P11-S0021` (`WF-STR-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-TRD-006`); matrix row `659`
- **Source capability:** `CAP-TRD-017`
- **Source final destination:** `monitoring/events.py`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-TRD-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0023` [ ] `FR-TRD-047` - Enforce the current Risk-owned AllocationRiskDecision v1 and authoritative portfolio risk-budget projection for the exact allocation/plan; never calculate or...

- **Execution domain:** `Trading`.
- **Execution position:** `23` of `30`.
- **Cannot start before:** Step `P11-S0022` (`P-TRD-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Monitoring requirements`` (line 728); matrix row `658`.
- **Source responsibility:** Enforce the current Risk-owned `AllocationRiskDecision v1` and authoritative portfolio risk-budget projection for the exact allocation/plan; never calculate or modify the budget.
- **Source class / function / method:** `BudgetGate.validate`
- **Source side effects:** None
- **Source raises:** Missing, stale, expired, mismatched, or exceeded budget blocks dispatch
- **Source usage / test:** **Usage:** portfolio rebalance integration test; **Unit:** budget-gate contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-TRD-047`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0024` [ ] `WF-TRD-009` - Perform safe live shutdown

- **Execution domain:** `Trading`.
- **Execution position:** `24` of `30`.
- **Cannot start before:** Step `P11-S0023` (`FR-TRD-047`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 3. Workflows > Workflow scope values`` (line 266); matrix row `660`.
- **Source scope:** Cross-domain
- **Source workflow:** Perform safe live shutdown
- **Source requirement sequence:** `FR-TRD-035`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-TRD-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0025` [ ] `WF-TRD-010` - Emit monitoring, cost, and incident evidence

- **Execution domain:** `Trading`.
- **Execution position:** `25` of `30`.
- **Cannot start before:** Step `P11-S0024` (`WF-TRD-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 3. Workflows > Workflow scope values`` (line 267); matrix row `661`.
- **Source scope:** Cross-domain
- **Source workflow:** Emit monitoring, cost, and incident evidence
- **Source requirement sequence:** `FR-TRD-046 → FR-TRD-048`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-TRD-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 5 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P11-S0026` [ ] `P-API-005` - streams feature/component (provisional)

- **Execution domain:** `UI/API`.
- **Execution position:** `26` of `30`.
- **Cannot start before:** Step `P11-S0025` (`WF-TRD-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-API-005`); matrix row `1207`
- **Source type:** Contracts
- **Source responsibility:** Non-stream responses use `ApiResponse`; streams use `StreamEvent`; API/UI drift fails CI.
- **Source verification:** OpenAPI/DTO snapshot tests
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-API-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0027` [ ] `WF-API-005` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `27` of `30`.
- **Cannot start before:** Step `P11-S0026` (`P-API-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 358); matrix row `1208`.
- **Source scope:** Cross-domain
- **Source workflow:** Strategy catalogue, registered version commands, and approved optimization adoption
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0028` [ ] `WF-API-017` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `28` of `30`.
- **Cannot start before:** Step `P11-S0027` (`WF-API-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 369); matrix row `1209`.
- **Source scope:** Cross-domain
- **Source workflow:** Portfolio construction, eligibility, activation, history, and rebalance
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P11-S0029` [ ] `CAP-UI-020` - shared streaming

- **Execution domain:** `UI/API`.
- **Execution position:** `29` of `30`.
- **Cannot start before:** Step `P11-S0028` (`WF-API-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 311); matrix row `1206`.
- **Source final destination:** `streams/`; `FR-API-004`, `FR-API-020`, `FR-API-021`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-020`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 6 - System deployment composition

Compose the already implemented domains into the specified deployable runtime and startup topology.

#### Step `P11-S0030` [ ] `P-SYS-004` - Portable modular-monolith deployment topology and startup

- **Execution domain:** `System`.
- **Execution position:** `30` of `30`.
- **Cannot start before:** Step `P11-S0029` (`CAP-UI-020`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** Deployment composition after all phase domain implementations.
- **Delivery type:** Resolve specification before implementation.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `docs/PROJECT.md` - ``§7 System-Wide Requirements`` (`P-SYS-004`); matrix row `28`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SYS-004`.
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

- **Expected assigned IDs:** 30.
- **Plan requirement entries:** 30.
- **Matrix phase:** `11`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (1):** `P-SYS-004`
- **Utils (0):** None.
- **Brokers (9):** `CAP-BRK-007`, `CAP-BRK-015`, `FR-BRK-107`, `FR-BRK-126`, `FR-BRK-127`, `FR-BRK-128`, `FR-BRK-129`, `P-BRK-007`, `WF-BRK-006`
- **Data (11):** `CAP-DATA-010`, `FR-DATA-042`, `FR-DATA-043`, `FR-DATA-044`, `FR-DATA-045`, `FR-DATA-047`, `FR-DATA-048`, `P-DATA-006`, `P-DATA-007`, `WF-DATA-007`, `WF-DATA-008`
- **Indicators (0):** None.
- **Strategy (1):** `WF-STR-007`
- **Risk (0):** None.
- **Trading (4):** `FR-TRD-047`, `P-TRD-006`, `WF-TRD-009`, `WF-TRD-010`
- **Simulation (0):** None.
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (4):** `CAP-UI-020`, `P-API-005`, `WF-API-005`, `WF-API-017`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
