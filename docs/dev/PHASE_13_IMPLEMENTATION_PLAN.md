# Phase 13 Implementation Plan - v2.0 - Completion and parity

> **Status:** Not started
> **Requirement count:** 69
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 13
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 13. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v2.0`.
- **Theme:** Completion and parity.
- **Entry condition:** Phase 12 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Run every system workflow and prove no Missing, duplicated, or unassigned scope.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v2.0 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires all remaining parity gaps; checklist claims require evidence.

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
| Utils | 0 | Close remaining package checklist. |
| Brokers | 10 | Close remaining provider capabilities and release evidence. |
| Data | 17 | Close remaining capabilities and negative boundaries. |
| Indicators | 0 | Close exports/usage checklist. |
| Strategy | 0 | Close package checklist. |
| Risk | 0 | Close package checklist. |
| Trading | 23 | Close capability catalogue and package checklist. |
| Simulation | 3 | Close exclusions and usage checklist. |
| Analytics | 2 | Close output/usage checklist. |
| Optimization | 0 | Close public API/usage checklist. |
| Research | 0 | Close artifacts/usage checklist. |
| Portfolio | 0 | Close portfolio checklist. |
| UI/API | 13 | Close remaining routes, negative boundaries, and UI checklist. |

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

#### Step `P13-S0001` [ ] `FR-BRK-135` - brokers/__init__.py

- **Execution domain:** `Brokers`.
- **Execution position:** `1` of `69`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1342); matrix row `273`.
- **Source assigned file:** `brokers/__init__.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-135`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0002` [ ] `CAP-BRK-002` - Session lifecycle

- **Execution domain:** `Brokers`.
- **Execution position:** `2` of `69`.
- **Cannot start before:** Step `P13-S0001` (`FR-BRK-135`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 517); matrix row `264`.
- **Source final destination:** `contracts/protocols.py`; FR-BRK-047–057; provider transports
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0003` [ ] `CAP-BRK-004` - Capabilities/unsupported outcomes

- **Execution domain:** `Brokers`.
- **Execution position:** `3` of `69`.
- **Cannot start before:** Step `P13-S0002` (`CAP-BRK-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 519); matrix row `265`.
- **Source final destination:** `contracts` and `registry/catalogue.py`; FR-BRK-005, 010–011, 073–074, 103
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0004` [ ] `CAP-BRK-006` - Quotes/ticks/bars/order books

- **Execution domain:** `Brokers`.
- **Execution position:** `4` of `69`.
- **Cannot start before:** Step `P13-S0003` (`CAP-BRK-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 521); matrix row `266`.
- **Source final destination:** FR-BRK-022–025, 063–067 and provider adapters
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0005` [ ] `CAP-BRK-008` - Account/platform/permissions

- **Execution domain:** `Brokers`.
- **Execution position:** `5` of `69`.
- **Cannot start before:** Step `P13-S0004` (`CAP-BRK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 523); matrix row `267`.
- **Source final destination:** FR-BRK-012, 014–018, 073–082
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0006` [ ] `CAP-BRK-009` - Positions/orders/deals/activity

- **Execution domain:** `Brokers`.
- **Execution position:** `6` of `69`.
- **Cannot start before:** Step `P13-S0005` (`CAP-BRK-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 524); matrix row `268`.
- **Source final destination:** FR-BRK-027–032, 083–090
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0007` [ ] `CAP-BRK-010` - Single-target mutations

- **Execution domain:** `Brokers`.
- **Execution position:** `7` of `69`.
- **Cannot start before:** Step `P13-S0006` (`CAP-BRK-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 525); matrix row `269`.
- **Source final destination:** FR-BRK-033–038, 091–097
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0008` [ ] `CAP-BRK-011` - Provider-native calculations

- **Execution domain:** `Brokers`.
- **Execution position:** `8` of `69`.
- **Cannot start before:** Step `P13-S0007` (`CAP-BRK-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 526); matrix row `270`.
- **Source final destination:** FR-BRK-039–041, 098–100
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0009` [ ] `CAP-BRK-017` - Session/account isolation

- **Execution domain:** `Brokers`.
- **Execution position:** `9` of `69`.
- **Cannot start before:** Step `P13-S0008` (`CAP-BRK-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 532); matrix row `271`.
- **Source final destination:** FR-BRK-006, 047–052, 101; NFR-BRK-005
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0010` [ ] `CAP-BRK-018` - Redacted observability

- **Execution domain:** `Brokers`.
- **Execution position:** `10` of `69`.
- **Cannot start before:** Step `P13-S0009` (`CAP-BRK-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 533); matrix row `272`.
- **Source final destination:** `BrokerResult` metadata; NFR-BRK-007–010
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Data

Implement `Data` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P13-S0011` [ ] `FR-DATA-009` - Negative requirement: Data exposes no restricted broker-execution channel.

- **Execution domain:** `Data`.
- **Execution position:** `11` of `69`.
- **Cannot start before:** Step `P13-S0010` (`CAP-BRK-018`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `S`; source status `Removed`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `broker.py` — Broker Boundary Contracts`` (line 667); matrix row `384`.
- **Source responsibility:** *(The restricted broker-execution channel is outside the architecture. Trading dispatches mutations directly through Brokers' `BrokerAdapter`; Data holds and issues no mutation capability.)*
- **Source class / function / method:** —
- **Source side effects:** None
- **Source raises:** —
- **Source usage / test:** —
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0012` [ ] `FR-DATA-029` - Negative requirement: Data issues no mutation capability; Trading obtains it from Brokers.

- **Execution domain:** `Data`.
- **Execution position:** `12` of `69`.
- **Cannot start before:** Step `P13-S0011` (`FR-DATA-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `S`; source status `Removed`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public source API`` (line 870); matrix row `385`.
- **Source responsibility:** *(Channel issuance is outside Data; Trading obtains mutation capability directly from Brokers' `BrokerAdapter`.)*
- **Source class / function / method:** —
- **Source side effects:** None
- **Source raises:** —
- **Source usage / test:** —
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-029`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0013` [ ] `FR-DATA-040` - Negative requirement: Data contains no historical labeling implementation.

- **Execution domain:** `Data`.
- **Execution position:** `13` of `69`.
- **Cannot start before:** Step `P13-S0012` (`FR-DATA-029`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public processing API`` (line 1002); matrix row `386`.
- **Source responsibility:** Research owns historical labeling; no Data implementation.
- **Source class / function / method:** —
- **Source side effects:** —
- **Source raises:** —
- **Source usage / test:** —
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-040`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0014` [ ] `WF-DATA-006` - Negative requirement: historical labeling remains outside Data and owned by Research.

- **Execution domain:** `Data`.
- **Execution position:** `14` of `69`.
- **Cannot start before:** Step `P13-S0013` (`FR-DATA-040`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 366); matrix row `387`.
- **Source scope:** —
- **Source workflow:** Historical labeling
- **Source requirement sequence:** —
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0015` [ ] `CAP-DATA-001` - Typed public and internal API boundary

- **Execution domain:** `Data`.
- **Execution position:** `15` of `69`.
- **Cannot start before:** Step `P13-S0014` (`WF-DATA-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 311); matrix row `371`.
- **Source capability:** `CAP-DATA-001` Typed public and internal API boundary
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0016` [ ] `CAP-DATA-002` - Historical OHLCV/tick/spread retrieval

- **Execution domain:** `Data`.
- **Execution position:** `16` of `69`.
- **Cannot start before:** Step `P13-S0015` (`CAP-DATA-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 312); matrix row `372`.
- **Source capability:** `CAP-DATA-002` Historical OHLCV/tick/spread retrieval
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0017` [ ] `CAP-DATA-005` - Quality/gaps/availability/revision

- **Execution domain:** `Data`.
- **Execution position:** `17` of `69`.
- **Cannot start before:** Step `P13-S0016` (`CAP-DATA-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 315); matrix row `373`.
- **Source capability:** `CAP-DATA-005` Quality/gaps/availability/revision
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0018` [ ] `CAP-DATA-006` - Versioned cache and safe clear

- **Execution domain:** `Data`.
- **Execution position:** `18` of `69`.
- **Cannot start before:** Step `P13-S0017` (`CAP-DATA-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 316); matrix row `374`.
- **Source capability:** `CAP-DATA-006` Versioned cache and safe clear
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0019` [ ] `CAP-DATA-009` - Jobs and resumable backfills

- **Execution domain:** `Data`.
- **Execution position:** `19` of `69`.
- **Cannot start before:** Step `P13-S0018` (`CAP-DATA-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 319); matrix row `375`.
- **Source capability:** `CAP-DATA-009` Jobs and resumable backfills
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0020` [ ] `CAP-DATA-011` - Timeframes/resampling/alignment/aggregation

- **Execution domain:** `Data`.
- **Execution position:** `20` of `69`.
- **Cannot start before:** Step `P13-S0019` (`CAP-DATA-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 321); matrix row `376`.
- **Source capability:** `CAP-DATA-011` Timeframes/resampling/alignment/aggregation
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0021` [ ] `CAP-DATA-012` - Deterministic synthetic generation

- **Execution domain:** `Data`.
- **Execution position:** `21` of `69`.
- **Cannot start before:** Step `P13-S0020` (`CAP-DATA-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 322); matrix row `377`.
- **Source capability:** `CAP-DATA-012` Deterministic synthetic generation
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0022` [ ] `CAP-DATA-013` - Historical labeling

- **Execution domain:** `Data`.
- **Execution position:** `22` of `69`.
- **Cannot start before:** Step `P13-S0021` (`CAP-DATA-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 323); matrix row `378`.
- **Source capability:** `CAP-DATA-013` Historical labeling
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0023` [ ] `CAP-DATA-014` - Market hours/sessions/volume

- **Execution domain:** `Data`.
- **Execution position:** `23` of `69`.
- **Cannot start before:** Step `P13-S0022` (`CAP-DATA-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 324); matrix row `379`.
- **Source capability:** `CAP-DATA-014` Market hours/sessions/volume
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0024` [ ] `CAP-DATA-017` - Errors/request correlation/audit/side effects

- **Execution domain:** `Data`.
- **Execution position:** `24` of `69`.
- **Cannot start before:** Step `P13-S0023` (`CAP-DATA-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 327); matrix row `380`.
- **Source capability:** `CAP-DATA-017` Errors/request correlation/audit/side effects
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0025` [ ] `CAP-DATA-018` - Workflow-aware precision/serialization

- **Execution domain:** `Data`.
- **Execution position:** `25` of `69`.
- **Cannot start before:** Step `P13-S0024` (`CAP-DATA-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 328); matrix row `381`.
- **Source capability:** `CAP-DATA-018` Workflow-aware precision/serialization
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0026` [ ] `CAP-DATA-020` - Legacy implementation/facade cleanup

- **Execution domain:** `Data`.
- **Execution position:** `26` of `69`.
- **Cannot start before:** Step `P13-S0025` (`CAP-DATA-018`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 330); matrix row `382`.
- **Source capability:** `CAP-DATA-020` Legacy implementation/facade cleanup
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-020`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0027` [ ] `CAP-DATA-021` - Tests and validation evidence

- **Execution domain:** `Data`.
- **Execution position:** `27` of `69`.
- **Cannot start before:** Step `P13-S0026` (`CAP-DATA-020`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 331); matrix row `383`.
- **Source capability:** `CAP-DATA-021` Tests and validation evidence
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-021`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Trading

Implement `Trading` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P13-S0028` [ ] `CAP-TRD-001` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `28` of `69`.
- **Cannot start before:** Step `P13-S0027` (`CAP-DATA-021`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 883); matrix row `670`.
- **Source decision:** Modify
- **Source final destination:** `contracts/registry.py` — exact typed Python public API
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0029` [ ] `CAP-TRD-002` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `29` of `69`.
- **Cannot start before:** Step `P13-S0028` (`CAP-TRD-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 884); matrix row `671`.
- **Source decision:** Modify
- **Source final destination:** `contracts/models.py` — one request/receipt/result family
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0030` [ ] `CAP-TRD-003` - Merge

- **Execution domain:** `Trading`.
- **Execution position:** `30` of `69`.
- **Cannot start before:** Step `P13-S0029` (`CAP-TRD-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 885); matrix row `672`.
- **Source decision:** Merge
- **Source final destination:** `contracts/errors.py` — one taxonomy, mapper, and redaction boundary
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0031` [ ] `CAP-TRD-004` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `31` of `69`.
- **Cannot start before:** Step `P13-S0030` (`CAP-TRD-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 886); matrix row `673`.
- **Source decision:** Modify
- **Source final destination:** `validation/orders.py`, `validation/readiness.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0032` [ ] `CAP-TRD-005` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `32` of `69`.
- **Cannot start before:** Step `P13-S0031` (`CAP-TRD-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 887); matrix row `674`.
- **Source decision:** Modify
- **Source final destination:** `actions/orders.py`, `actions/positions.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0033` [ ] `CAP-TRD-006` - Add

- **Execution domain:** `Trading`.
- **Execution position:** `33` of `69`.
- **Cannot start before:** Step `P13-S0032` (`CAP-TRD-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 888); matrix row `675`.
- **Source decision:** Add
- **Source final destination:** `routing/dispatcher.py` — external Simulation authority
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0034` [ ] `CAP-TRD-007` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `34` of `69`.
- **Cannot start before:** Step `P13-S0033` (`CAP-TRD-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 889); matrix row `676`.
- **Source decision:** Modify
- **Source final destination:** `validation/snapshots.py`, `validation/readiness.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0035` [ ] `CAP-TRD-008` - Merge

- **Execution domain:** `Trading`.
- **Execution position:** `35` of `69`.
- **Cannot start before:** Step `P13-S0034` (`CAP-TRD-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 890); matrix row `677`.
- **Source decision:** Merge
- **Source final destination:** `live/config.py`, `live/session.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0036` [ ] `CAP-TRD-009` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `36` of `69`.
- **Cannot start before:** Step `P13-S0035` (`CAP-TRD-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 891); matrix row `678`.
- **Source decision:** Modify
- **Source final destination:** `live/gates.py` — mandatory fail-fast sequence
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0037` [ ] `CAP-TRD-010` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `37` of `69`.
- **Cannot start before:** Step `P13-S0036` (`CAP-TRD-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 892); matrix row `679`.
- **Source decision:** Modify
- **Source final destination:** `live/gates.py` — external verdict validation only
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0038` [ ] `CAP-TRD-011` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `38` of `69`.
- **Cannot start before:** Step `P13-S0037` (`CAP-TRD-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 893); matrix row `680`.
- **Source decision:** Modify
- **Source final destination:** `state/idempotency.py`, injected coordination contract
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0039` [ ] `CAP-TRD-012` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `39` of `69`.
- **Cannot start before:** Step `P13-S0038` (`CAP-TRD-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 894); matrix row `681`.
- **Source decision:** Modify
- **Source final destination:** `routing/capabilities.py`, `routing/dispatcher.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0040` [ ] `CAP-TRD-013` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `40` of `69`.
- **Cannot start before:** Step `P13-S0039` (`CAP-TRD-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 895); matrix row `682`.
- **Source decision:** Modify
- **Source final destination:** `state/events.py`, `state/projections.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0041` [ ] `CAP-TRD-014` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `41` of `69`.
- **Cannot start before:** Step `P13-S0040` (`CAP-TRD-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 896); matrix row `683`.
- **Source decision:** Modify
- **Source final destination:** `reconciliation/`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0042` [ ] `CAP-TRD-015` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `42` of `69`.
- **Cannot start before:** Step `P13-S0041` (`CAP-TRD-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 897); matrix row `684`.
- **Source decision:** Modify
- **Source final destination:** `actions/controls.py`, `actions/emergency.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0043` [ ] `CAP-TRD-016` - Merge

- **Execution domain:** `Trading`.
- **Execution position:** `43` of `69`.
- **Cannot start before:** Step `P13-S0042` (`CAP-TRD-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 898); matrix row `685`.
- **Source decision:** Merge
- **Source final destination:** `state/events.py`, `state/stores.py`, `state/migrations.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0044` [ ] `CAP-TRD-017` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `44` of `69`.
- **Cannot start before:** Step `P13-S0043` (`CAP-TRD-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 899); matrix row `686`.
- **Source decision:** Modify
- **Source final destination:** `monitoring/events.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0045` [ ] `CAP-TRD-018` - Add

- **Execution domain:** `Trading`.
- **Execution position:** `45` of `69`.
- **Cannot start before:** Step `P13-S0044` (`CAP-TRD-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 900); matrix row `687`.
- **Source decision:** Add
- **Source final destination:** Enforce registered Risk-owned portfolio budget decisions during authorized Portfolio rebalance execution
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0046` [ ] `CAP-TRD-019` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `46` of `69`.
- **Cannot start before:** Step `P13-S0045` (`CAP-TRD-018`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 901); matrix row `688`.
- **Source decision:** Modify
- **Source final destination:** `reporting/evidence.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0047` [ ] `CAP-TRD-022` - Remove

- **Execution domain:** `Trading`.
- **Execution position:** `47` of `69`.
- **Cannot start before:** Step `P13-S0046` (`CAP-TRD-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 902); matrix row `689`.
- **Source decision:** Remove
- **Source final destination:** No raw signal translator; upstream supplies the canonical request
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0048` [ ] `CAP-TRD-023` - Merge

- **Execution domain:** `Trading`.
- **Execution position:** `48` of `69`.
- **Cannot start before:** Step `P13-S0047` (`CAP-TRD-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 903); matrix row `690`.
- **Source decision:** Merge
- **Source final destination:** `routing/responses.py`; external rate verdicts, no local policy engine
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-023`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0049` [ ] `CAP-TRD-024` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `49` of `69`.
- **Cannot start before:** Step `P13-S0048` (`CAP-TRD-023`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 904); matrix row `691`.
- **Source decision:** Modify
- **Source final destination:** `validation/readiness.py`, `live/gates.py`; consume promotion evidence only
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-024`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0050` [ ] `CAP-TRD-025` - Modify

- **Execution domain:** `Trading`.
- **Execution position:** `50` of `69`.
- **Cannot start before:** Step `P13-S0049` (`CAP-TRD-024`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration > Reconciliation decision coverage`` (line 905); matrix row `692`.
- **Source decision:** Modify
- **Source final destination:** `contracts/registry.py`; non-mutating governed drafts
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-TRD-025`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P13-S0051` [ ] `CAP-SIM-002` - Validation, orchestration, and lifecycle

- **Execution domain:** `Simulation`.
- **Execution position:** `51` of `69`.
- **Cannot start before:** Step `P13-S0050` (`CAP-TRD-025`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 449); matrix row `761`.
- **Source final destination:** `validation/`, `journal/`, `run/`: `FR-SIM-001`, `FR-SIM-003`, `FR-SIM-017`, `FR-SIM-030`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0052` [ ] `CAP-SIM-003` - Signal timing, tick construction, no-lookahead

- **Execution domain:** `Simulation`.
- **Execution position:** `52` of `69`.
- **Cannot start before:** Step `P13-S0051` (`CAP-SIM-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 450); matrix row `762`.
- **Source final destination:** `timeline/`: `FR-SIM-004`–`FR-SIM-006`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0053` [ ] `CAP-SIM-011` - Determinism, precision, reliability, security

- **Execution domain:** `Simulation`.
- **Execution position:** `53` of `69`.
- **Cannot start before:** Step `P13-S0052` (`CAP-SIM-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 458); matrix row `763`.
- **Source final destination:** `NFR-SIM-001`–`NFR-SIM-012` and the approved Phase 1 error surface
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 5 - Analytics

Implement `Analytics` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P13-S0054` [ ] `FR-ANLT-024` - Negative requirement: Analytics defines no local redaction primitive and uses Utils.

- **Execution domain:** `Analytics`.
- **Execution position:** `54` of `69`.
- **Cannot start before:** Step `P13-S0053` (`CAP-SIM-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.1` functional behavior in authoritative source order.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `S`; source status `Removed`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.1 `contracts/` — Schemas, Catalogs, and Evidence Safety > `evidence.py` — Evidence Construction and Output Safety`` (line 536); matrix row `836`.
- **Source responsibility:** Local redaction is prohibited; Analytics imports and applies Utils `redact_mapping_value`.
- **Source class / function / method:** None in Analytics
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Verification:** boundary test confirms Analytics defines no redaction primitive.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-024`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0055` [ ] `FR-ANLT-026` - Negative requirement: Analytics defines no local canonical serializer and uses Utils.

- **Execution domain:** `Analytics`.
- **Execution position:** `55` of `69`.
- **Cannot start before:** Step `P13-S0054` (`FR-ANLT-024`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` module `4.1` functional behavior in authoritative source order.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `S`; source status `Removed`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 4. Module and Requirement Specifications > 4.1 `contracts/` — Schemas, Catalogs, and Evidence Safety > `evidence.py` — Evidence Construction and Output Safety`` (line 538); matrix row `837`.
- **Source responsibility:** Local canonical serialization is prohibited; Analytics imports Utils `canonical_json`.
- **Source class / function / method:** None in Analytics
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Verification:** boundary test confirms Analytics defines no canonical JSON primitive.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-ANLT-026`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 6 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P13-S0056` [ ] `FR-API-027` - Negative requirement: interactive Simulation session/frame/mutation routes remain absent.

- **Execution domain:** `UI/API`.
- **Execution position:** `56` of `69`.
- **Cannot start before:** Step `P13-S0055` (`FR-ANLT-026`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 4. Module and Requirement Specifications > 4.6 `routes/` — Thin HTTP and streaming boundaries > Route-family functional requirements`` (line 603); matrix row `1238`.
- **Source responsibility:** Interactive Simulation sessions, frames, replay, positions/orders, mutations, and what-if routes are outside the initial synchronous build.
- **Source class / function / method:** None
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** Route-absence test `tests/api/unit/test_route_catalog.py::test_interactive_simulation_routes_absent()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-API-027`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0057` [ ] `WF-API-007` - Negative requirement: interactive Simulation session lifecycle remains excluded.

- **Execution domain:** `UI/API`.
- **Execution position:** `57` of `69`.
- **Cannot start before:** Step `P13-S0056` (`FR-API-027`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 360); matrix row `1239`.
- **Source scope:** Cross-domain
- **Source workflow:** Interactive Simulation session lifecycle
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0058` [ ] `WF-API-008` - Negative requirement: interactive Simulation mutation and what-if workflow remains excluded.

- **Execution domain:** `UI/API`.
- **Execution position:** `58` of `69`.
- **Cannot start before:** Step `P13-S0057` (`WF-API-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Verify exclusion / absence.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 361); matrix row `1240`.
- **Source scope:** Cross-domain
- **Source workflow:** Governed interactive Simulation mutation/what-if
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0059` [ ] `CAP-UI-004` - authorization/governed writes/idempotency

- **Execution domain:** `UI/API`.
- **Execution position:** `59` of `69`.
- **Cannot start before:** Step `P13-S0058` (`WF-API-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 296); matrix row `1228`.
- **Source final destination:** `identity/`; `FR-API-014`, `FR-API-015`; UI/API-owned storage policy
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0060` [ ] `CAP-UI-005` - request security/context/observability

- **Execution domain:** `UI/API`.
- **Execution position:** `60` of `69`.
- **Cannot start before:** Step `P13-S0059` (`CAP-UI-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 297); matrix row `1229`.
- **Source final destination:** `middleware/`; `FR-API-016`, `FR-API-017`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0061` [ ] `CAP-UI-006` - health/readiness

- **Execution domain:** `UI/API`.
- **Execution position:** `61` of `69`.
- **Cannot start before:** Step `P13-S0060` (`CAP-UI-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 298); matrix row `1230`.
- **Source final destination:** `health/`; `FR-API-018`, `FR-API-019`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0062` [ ] `CAP-UI-011` - synchronous backtest result

- **Execution domain:** `UI/API`.
- **Execution position:** `62` of `69`.
- **Cannot start before:** Step `P13-S0061` (`CAP-UI-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 303); matrix row `1231`.
- **Source final destination:** `routes/backtests.py`; `FR-API-026`; no query/log/session lifecycle
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0063` [ ] `CAP-UI-012` - interactive simulator

- **Execution domain:** `UI/API`.
- **Execution position:** `63` of `69`.
- **Cannot start before:** Step `P13-S0062` (`CAP-UI-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 304); matrix row `1232`.
- **Source final destination:** Excluded from the initial synchronous lifecycle; no initial route or component
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0064` [ ] `CAP-UI-016` - initial Edge Lab

- **Execution domain:** `UI/API`.
- **Execution position:** `64` of `69`.
- **Cannot start before:** Step `P13-S0063` (`CAP-UI-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 308); matrix row `1233`.
- **Source final destination:** `routes/research.py`; `FR-API-031`; advanced surface excluded
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0065` [ ] `CAP-UI-019` - documentation

- **Execution domain:** `UI/API`.
- **Execution position:** `65` of `69`.
- **Cannot start before:** Step `P13-S0064` (`CAP-UI-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 310); matrix row `1234`.
- **Source final destination:** Excluded from the initial build; no route, state, client, or component
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0066` [ ] `CAP-UI-021` - typed frontend clients

- **Execution domain:** `UI/API`.
- **Execution position:** `66` of `69`.
- **Cannot start before:** Step `P13-S0065` (`CAP-UI-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 312); matrix row `1235`.
- **Source final destination:** `ui/clients/`; `FR-API-038`–`FR-API-041`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-021`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0067` [ ] `CAP-UI-022` - frontend auth/shell

- **Execution domain:** `UI/API`.
- **Execution position:** `67` of `69`.
- **Cannot start before:** Step `P13-S0066` (`CAP-UI-021`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 313); matrix row `1236`.
- **Source final destination:** `ui/context/`, `ui/app/`; `FR-API-042`, `FR-API-046`, `FR-API-053`, `FR-API-054`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P13-S0068` [ ] `CAP-UI-023` - workflow pages/components

- **Execution domain:** `UI/API`.
- **Execution position:** `68` of `69`.
- **Cannot start before:** Step `P13-S0067` (`CAP-UI-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 314); matrix row `1237`.
- **Source final destination:** `ui/components/`, `ui/app/`; `FR-API-047`–`FR-API-055`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-023`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 7 - System phase completion

Perform the final assurance, parity, or release-completion work after all implementation and verification steps above.

#### Step `P13-S0069` [ ] `P-SYS-005` - Full-system usage, integration verification, and parity definition of done

- **Execution domain:** `System`.
- **Execution position:** `69` of `69`.
- **Cannot start before:** Step `P13-S0068` (`CAP-UI-023`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** Final phase assurance after implementation and verification.
- **Delivery type:** Resolve specification before implementation.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `docs/PROJECT.md` - ``§7 System-Wide Requirements`` (`P-SYS-005`); matrix row `30`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SYS-005`.
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

- **Expected assigned IDs:** 69.
- **Plan requirement entries:** 69.
- **Matrix phase:** `13`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (1):** `P-SYS-005`
- **Utils (0):** None.
- **Brokers (10):** `CAP-BRK-002`, `CAP-BRK-004`, `CAP-BRK-006`, `CAP-BRK-008`, `CAP-BRK-009`, `CAP-BRK-010`, `CAP-BRK-011`, `CAP-BRK-017`, `CAP-BRK-018`, `FR-BRK-135`
- **Data (17):** `CAP-DATA-001`, `CAP-DATA-002`, `CAP-DATA-005`, `CAP-DATA-006`, `CAP-DATA-009`, `CAP-DATA-011`, `CAP-DATA-012`, `CAP-DATA-013`, `CAP-DATA-014`, `CAP-DATA-017`, `CAP-DATA-018`, `CAP-DATA-020`, `CAP-DATA-021`, `FR-DATA-009`, `FR-DATA-029`, `FR-DATA-040`, `WF-DATA-006`
- **Indicators (0):** None.
- **Strategy (0):** None.
- **Risk (0):** None.
- **Trading (23):** `CAP-TRD-001`, `CAP-TRD-002`, `CAP-TRD-003`, `CAP-TRD-004`, `CAP-TRD-005`, `CAP-TRD-006`, `CAP-TRD-007`, `CAP-TRD-008`, `CAP-TRD-009`, `CAP-TRD-010`, `CAP-TRD-011`, `CAP-TRD-012`, `CAP-TRD-013`, `CAP-TRD-014`, `CAP-TRD-015`, `CAP-TRD-016`, `CAP-TRD-017`, `CAP-TRD-018`, `CAP-TRD-019`, `CAP-TRD-022`, `CAP-TRD-023`, `CAP-TRD-024`, `CAP-TRD-025`
- **Simulation (3):** `CAP-SIM-002`, `CAP-SIM-003`, `CAP-SIM-011`
- **Analytics (2):** `FR-ANLT-024`, `FR-ANLT-026`
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (13):** `CAP-UI-004`, `CAP-UI-005`, `CAP-UI-006`, `CAP-UI-011`, `CAP-UI-012`, `CAP-UI-016`, `CAP-UI-019`, `CAP-UI-021`, `CAP-UI-022`, `CAP-UI-023`, `FR-API-027`, `WF-API-007`, `WF-API-008`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
