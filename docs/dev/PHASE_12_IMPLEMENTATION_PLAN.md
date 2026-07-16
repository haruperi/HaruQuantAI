# Phase 12 Implementation Plan - v1.12 - Production assurance

> **Status:** Not started
> **Requirement count:** 158
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 12
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 12. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.12`.
- **Theme:** Production assurance.
- **Entry condition:** Phase 11 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Run quality, security, contract, recovery, and performance gates without using a fake for the MT5 demo proof.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.12 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires cross-cutting quality gaps; fake utility is isolated to test assurance.

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
| Utils | 0 | NFR, export, usage, and shutdown assurance. |
| Brokers | 19 | NFRs plus the ledger-mandated FakeBrokerAdapter as test-only contract utility; never a Phase 1/demo authority. |
| Data | 12 | NFR, migration, precision, and recovery assurance. |
| Indicators | 14 | Formula fixtures and performance gates. |
| Strategy | 12 | NFR, migration, export, and replay assurance. |
| Risk | 12 | Security, concurrency, persistence, and tamper tests. |
| Trading | 8 | Safety, reconciliation, timeout, and performance assurance. |
| Simulation | 12 | Determinism/resource/error assurance. |
| Analytics | 13 | Finite-output, catalog, fixture, and hash assurance. |
| Optimization | 12 | Bounded-resource/state/checkpoint assurance. |
| Research | 15 | Leakage/resource/artifact assurance. |
| Portfolio | 10 | Determinism/persistence assurance. |
| UI/API | 18 | Security, route drift, accessibility, responsiveness, and client-contract assurance. |

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

#### Step `P12-S0001` [ ] `P-BRK-009` - testing feature/component (provisional)

- **Execution domain:** `Brokers`.
- **Execution position:** `1` of `158`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.9` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T3 Complete; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Standalone real-behavior usage scripts (run individually, not via pytest):`` (line 1456); matrix row `263`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-BRK-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0002` [ ] `FR-BRK-134` - testing/__init__.py

- **Execution domain:** `Brokers`.
- **Execution position:** `2` of `158`.
- **Cannot start before:** Step `P12-S0001` (`P-BRK-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1341); matrix row `247`.
- **Source assigned file:** `testing/__init__.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-134`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0003` [ ] `FR-BRK-109` - provide a complete deterministic BrokerAdapter test double whose operations return canonical DTOs, support bounded streams, preserve isolati...

- **Execution domain:** `Brokers`.
- **Execution position:** `3` of `158`.
- **Cannot start before:** Step `P12-S0002` (`FR-BRK-134`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `fake.py` — Complete Fake Adapter`` (line 1301); matrix row `246`.
- **Source responsibility:** The system shall provide a complete deterministic `BrokerAdapter` test double whose operations return canonical DTOs, support bounded streams, preserve isolation, and allow a selected operation to return a chosen canonical failure without network access.
- **Source class / function / method:** `class FakeBrokerAdapter(BrokerAdapter)`
- **Source side effects:** Local state mutation
- **Source raises:** `asyncio.CancelledError`: explicitly injected or caller cancellation.
- **Source usage / test:** **Usage:** `tests/brokers/usage/09_testing.py` (standalone script, run via `python`)<br>**Unit:** `tests/brokers/unit/test_fake_adapter.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-109`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0004` [ ] `CAP-BRK-019` - Contract/boundary/fake tests

- **Execution domain:** `Brokers`.
- **Execution position:** `4` of `158`.
- **Cannot start before:** Step `P12-S0003` (`FR-BRK-109`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T3 Complete; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 534); matrix row `245`.
- **Source final destination:** `testing/`; FR-BRK-109; NFR-BRK-012
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0005` [ ] `NFR-BRK-001` - Architecture

- **Execution domain:** `Brokers`.
- **Execution position:** `5` of `158`.
- **Cannot start before:** Step `P12-S0004` (`CAP-BRK-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1379); matrix row `248`.
- **Source type:** Architecture
- **Source responsibility:** Brokers shall contain only direct provider protocol integration and structural mapping, with no business logic or higher-domain imports.
- **Source verification:** Import/ownership boundary tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0006` [ ] `NFR-BRK-002` - Provider truth

- **Execution domain:** `Brokers`.
- **Execution position:** `6` of `158`.
- **Cannot start before:** Step `P12-S0005` (`NFR-BRK-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1380); matrix row `249`.
- **Source type:** Provider truth
- **Source responsibility:** No operation shall fabricate, assume, synthesize, or silently substitute price, spread, tick, fill, identifier, balance, permission, success, or connection state.
- **Source verification:** Shared contract and provider mapping tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0007` [ ] `NFR-BRK-003` - API boundary

- **Execution domain:** `Brokers`.
- **Execution position:** `7` of `158`.
- **Cannot start before:** Step `P12-S0006` (`NFR-BRK-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1381); matrix row `250`.
- **Source type:** API boundary
- **Source responsibility:** Consumers shall use only package exports or documented capability protocols; provider modules are private except provider integration tests, and final code shall contain no `load_mt5`, `mt5_data_*`, `load_dukascopy`, old provider export, raw SDK delegation, or compatibility shim surface.
- **Source verification:** Import and public-symbol audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0008` [ ] `NFR-BRK-004` - Reliability

- **Execution domain:** `Brokers`.
- **Execution position:** `8` of `158`.
- **Cannot start before:** Step `P12-S0007` (`NFR-BRK-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1382); matrix row `251`.
- **Source type:** Reliability
- **Source responsibility:** Unverifiable provider, permission, environment, response, or mutation state shall fail closed with a canonical result.
- **Source verification:** Failure-path tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0009` [ ] `NFR-BRK-005` - Concurrency

- **Execution domain:** `Brokers`.
- **Execution position:** `9` of `158`.
- **Cannot start before:** Step `P12-S0008` (`NFR-BRK-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1383); matrix row `252`.
- **Source type:** Concurrency
- **Source responsibility:** Independent adapters shall not share mutable account/session/subscription state; single-threaded SDK access shall be internally serialized.
- **Source verification:** Concurrent isolation tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0010` [ ] `NFR-BRK-006` - Async safety

- **Execution domain:** `Brokers`.
- **Execution position:** `10` of `158`.
- **Cannot start before:** Step `P12-S0009` (`NFR-BRK-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1384); matrix row `253`.
- **Source type:** Async safety
- **Source responsibility:** Blocking SDK calls and callback work shall not block the caller event loop; cancellation shall propagate without corrupting state.
- **Source verification:** Event-loop/cancellation tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0011` [ ] `NFR-BRK-007` - Security

- **Execution domain:** `Brokers`.
- **Execution position:** `11` of `158`.
- **Cannot start before:** Step `P12-S0010` (`NFR-BRK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1385); matrix row `254`.
- **Source type:** Security
- **Source responsibility:** Secrets and full private account identifiers shall never appear in logs, errors, results, events, or metadata.
- **Source verification:** Redaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0012` [ ] `NFR-BRK-008` - Observability

- **Execution domain:** `Brokers`.
- **Execution position:** `12` of `158`.
- **Cannot start before:** Step `P12-S0011` (`NFR-BRK-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1386); matrix row `255`.
- **Source type:** Observability
- **Source responsibility:** Lifecycle, auth, calls, errors, subscriptions, acknowledgements, and unknown outcomes shall emit redacted structured logs with provider, operation, request ID, environment, result, provider code, and measured latency.
- **Source verification:** Log-capture tests — `tests/brokers/unit/test_observability.py`. Implemented centrally at the adapter result/transition/unsupported sinks (`contracts/protocols.py`), the runtime circuit/subscription, the registry factory, and every provider transport. Verified on Python 3.14 — 3/3 observability tests plus the full 391-test domain suite pass at 92.25% coverage.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0013` [ ] `NFR-BRK-009` - Determinism

- **Execution domain:** `Brokers`.
- **Execution position:** `13` of `158`.
- **Cannot start before:** Step `P12-S0012` (`NFR-BRK-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1387); matrix row `256`.
- **Source type:** Determinism
- **Source responsibility:** Unsupported operations shall fail immediately and identically without any provider SDK call or consumer provider branch.
- **Source verification:** Shared unsupported contract suite
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0014` [ ] `NFR-BRK-010` - Performance

- **Execution domain:** `Brokers`.
- **Execution position:** `14` of `158`.
- **Cannot start before:** Step `P12-S0013` (`NFR-BRK-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1388); matrix row `257`.
- **Source type:** Performance
- **Source responsibility:** Local mapping/copying shall be bounded and provider-network latency shall be measured separately from local adapter overhead; no unsupported numeric latency gate is imposed.
- **Source verification:** Representative benchmarks
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0015` [ ] `NFR-BRK-011` - Independence

- **Execution domain:** `Brokers`.
- **Execution position:** `15` of `158`.
- **Cannot start before:** Step `P12-S0014` (`NFR-BRK-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1389); matrix row `258`.
- **Source type:** Independence
- **Source responsibility:** Brokers shall compile/test independently of Data, Trading, Risk, Strategy, Indicators, Simulation, Analytics, Optimization, Research, and UI/API.
- **Source verification:** Dependency audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0016` [ ] `NFR-BRK-012` - Testing

- **Execution domain:** `Brokers`.
- **Execution position:** `16` of `158`.
- **Cannot start before:** Step `P12-S0015` (`NFR-BRK-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1390); matrix row `259`.
- **Source type:** Testing
- **Source responsibility:** Every FR shall have one runnable usage example and unit coverage; each provider shall pass the shared contract suite and the package shall maintain at least 80% coverage.
- **Source verification:** Test/coverage audit — 391 `pytest` tests pass plus 8 standalone real-behavior usage scripts; 92.25% branch coverage over `app/services/brokers`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0017` [ ] `NFR-BRK-013` - Dependencies

- **Execution domain:** `Brokers`.
- **Execution position:** `17` of `158`.
- **Cannot start before:** Step `P12-S0016` (`NFR-BRK-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1391); matrix row `260`.
- **Source type:** Dependencies
- **Source responsibility:** Provider library versions shall match `pyproject.toml`; directly imported transitive packages must be pinned before implementation.
- **Source verification:** Dependency manifest audit — confirmed against `pyproject.toml`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0018` [ ] `NFR-BRK-014` - Persistence

- **Execution domain:** `Brokers`.
- **Execution position:** `18` of `158`.
- **Cannot start before:** Step `P12-S0017` (`NFR-BRK-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1392); matrix row `261`.
- **Source type:** Persistence
- **Source responsibility:** Brokers shall own no database access, credential persistence, reusable market/account cache, business snapshot, order store, or migration.
- **Source verification:** Static and runtime side-effect tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0019` [ ] `NFR-BRK-015` - Provider scope

- **Execution domain:** `Brokers`.
- **Execution position:** `19` of `158`.
- **Cannot start before:** Step `P12-S0018` (`NFR-BRK-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 5. Package-Wide Requirements and Shared Configuration > Non-Functional Requirements`` (line 1393); matrix row `262`.
- **Source type:** Provider scope
- **Source responsibility:** Dukascopy and Yahoo shall be declared research-only and unavailable to production/live workflows; their provider results shall carry explicit provenance for Data.
- **Source verification:** Capability and consumer-boundary tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-BRK-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Data

Implement `Data` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0020` [ ] `NFR-DATA-001` - Architecture

- **Execution domain:** `Data`.
- **Execution position:** `20` of `158`.
- **Cannot start before:** Step `P12-S0019` (`NFR-BRK-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1159); matrix row `359`.
- **Source type:** Architecture
- **Source responsibility:** Other domains shall consume only documented Data contracts or focused public APIs; no provider, storage, cache, registry, or private-file imports cross the boundary.
- **Source verification:** Dependency/import audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0021` [ ] `NFR-DATA-002` - Determinism

- **Execution domain:** `Data`.
- **Execution position:** `21` of `158`.
- **Cannot start before:** Step `P12-S0020` (`NFR-DATA-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1160); matrix row `360`.
- **Source type:** Determinism
- **Source responsibility:** Given identical inputs, versions, source revision, and seed, normalization, quality, transforms, synthetic generation, cache identity, and historical processing shall be reproducible.
- **Source verification:** Replay/golden tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0022` [ ] `NFR-DATA-003` - Time safety

- **Execution domain:** `Data`.
- **Execution position:** `22` of `158`.
- **Cannot start before:** Step `P12-S0021` (`NFR-DATA-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1161); matrix row `361`.
- **Source type:** Time safety
- **Source responsibility:** All official/cross-domain timestamps shall be UTC and every aligned value shall expose `available_at`; lookahead or ambiguous timezone evidence fails atomically.
- **Source verification:** Boundary and no-lookahead tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0023` [ ] `NFR-DATA-004` - Reliability

- **Execution domain:** `Data`.
- **Execution position:** `23` of `158`.
- **Cannot start before:** Step `P12-S0022` (`NFR-DATA-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1162); matrix row `362`.
- **Source type:** Reliability
- **Source responsibility:** Missing safety/context/source/license/precision/account evidence shall fail closed; no partial dataset, chunk, migration, or audit write is published as successful.
- **Source verification:** Fault-injection tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0024` [ ] `NFR-DATA-005` - Security

- **Execution domain:** `Data`.
- **Execution position:** `24` of `158`.
- **Cannot start before:** Step `P12-S0023` (`NFR-DATA-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1163); matrix row `363`.
- **Source type:** Security
- **Source responsibility:** Sensitive values handled by Data shall be redacted before logs, errors, events, metrics, manifests, or responses; credential references are resolved by UI/API composition, never by Data.
- **Source verification:** Secret/redaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0025` [ ] `NFR-DATA-006` - Broker safety

- **Execution domain:** `Data`.
- **Execution position:** `25` of `158`.
- **Cannot start before:** Step `P12-S0024` (`NFR-DATA-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1164); matrix row `364`.
- **Source type:** Broker safety
- **Source responsibility:** All Data broker/provider access shall be read-only through Brokers' `BrokerAdapter` read traits; Data shall never invoke a mutation operation or place a trade.
- **Source verification:** Capability/dependency audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0026` [ ] `NFR-DATA-007` - Persistence

- **Execution domain:** `Data`.
- **Execution position:** `26` of `158`.
- **Cannot start before:** Step `P12-S0025` (`NFR-DATA-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1165); matrix row `365`.
- **Source type:** Persistence
- **Source responsibility:** SQLite operations shall be transactional, bounded, idempotent where required, use one lock/migration framework, and never expose connections to another domain.
- **Source verification:** Concurrency/recovery tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0027` [ ] `NFR-DATA-008` - Observability

- **Execution domain:** `Data`.
- **Execution position:** `27` of `158`.
- **Cannot start before:** Step `P12-S0026` (`NFR-DATA-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1166); matrix row `366`.
- **Source type:** Observability
- **Source responsibility:** Every governed operation shall propagate request/correlation IDs and emit bounded redacted source/cache/storage/job/feed evidence; failures are never swallowed.
- **Source verification:** Event/trace inspection
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0028` [ ] `NFR-DATA-009` - Performance

- **Execution domain:** `Data`.
- **Execution position:** `28` of `158`.
- **Cannot start before:** Step `P12-S0027` (`NFR-DATA-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1167); matrix row `367`.
- **Source type:** Performance
- **Source responsibility:** Official responses obey hard inline/allocation limits and reject excess work before expensive operations; no unmeasured latency, throughput, or memory claim is a binding gate.
- **Source verification:** Direct limit and pre-side-effect tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0029` [ ] `NFR-DATA-010` - Compatibility

- **Execution domain:** `Data`.
- **Execution position:** `29` of `158`.
- **Cannot start before:** Step `P12-S0028` (`NFR-DATA-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1168); matrix row `368`.
- **Source type:** Compatibility
- **Source responsibility:** Schema changes shall be additive within v1 or use a new major identifier; incompatible persisted data is explicitly migrated offline or invalidated/re-ingested.
- **Source verification:** Contract/migration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0030` [ ] `NFR-DATA-011` - Maintainability

- **Execution domain:** `Data`.
- **Execution position:** `30` of `158`.
- **Cannot start before:** Step `P12-S0029` (`NFR-DATA-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1169); matrix row `369`.
- **Source type:** Maintainability
- **Source responsibility:** Every file shall retain one focused responsibility, imports shall be absolute, and package/submodule `__all__` values shall list only approved public symbols.
- **Source verification:** Structure/import review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0031` [ ] `NFR-DATA-012` - Testing

- **Execution domain:** `Data`.
- **Execution position:** `31` of `158`.
- **Cannot start before:** Step `P12-S0030` (`NFR-DATA-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 5. Package-Wide Requirements and Shared Configuration`` (line 1170); matrix row `370`.
- **Source type:** Testing
- **Source responsibility:** Every `FR-DATA-*` shall have one runnable usage example and at least one unit test; every collaborative workflow shall have an integration test; coverage shall be at least 80%.
- **Source verification:** Traceability and coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-DATA-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Indicators

Implement `Indicators` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0032` [ ] `NFR-INDI-001` - Architecture

- **Execution domain:** `Indicators`.
- **Execution position:** `32` of `158`.
- **Cannot start before:** Step `P12-S0031` (`NFR-DATA-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 653); matrix row `419`.
- **Source type:** Architecture
- **Source responsibility:** The package shall remain a pure, persistence-free calculation domain with no broker, network, filesystem, cache, audit-sink, telemetry-export, or mutable registry I/O.
- **Source verification:** Side-effect/dependency audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0033` [ ] `NFR-INDI-002` - Determinism

- **Execution domain:** `Indicators`.
- **Execution position:** `33` of `158`.
- **Cannot start before:** Step `P12-S0032` (`NFR-INDI-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 654); matrix row `420`.
- **Source type:** Determinism
- **Source responsibility:** Equivalent canonical inputs, parameters, versions, and policy shall produce byte-equivalent canonical values/checksums/manifests independent of call order.
- **Source verification:** Replay and checksum tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0034` [ ] `NFR-INDI-003` - API boundary

- **Execution domain:** `Indicators`.
- **Execution position:** `34` of `158`.
- **Cannot start before:** Step `P12-S0033` (`NFR-INDI-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 655); matrix row `421`.
- **Source type:** API boundary
- **Source responsibility:** Consumers shall use only documented root/feature exports; leaf modules, private helpers, DataFrames internal to other domains, and provider SDK objects are not cross-domain contracts.
- **Source verification:** Import contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0035` [ ] `NFR-INDI-004` - Maintainability

- **Execution domain:** `Indicators`.
- **Execution position:** `35` of `158`.
- **Cannot start before:** Step `P12-S0034` (`NFR-INDI-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 656); matrix row `422`.
- **Source type:** Maintainability
- **Source responsibility:** Python shall follow Google style, explicit signature typing, Google docstrings, absolute imports, logging rules, and one focused responsibility per file.
- **Source verification:** Ruff, mypy, structure review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0036` [ ] `NFR-INDI-005` - Vectorization

- **Execution domain:** `Indicators`.
- **Execution position:** `36` of `158`.
- **Cannot start before:** Step `P12-S0035` (`NFR-INDI-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 657); matrix row `423`.
- **Source type:** Vectorization
- **Source responsibility:** Official batch formulas shall use vectorized pandas/NumPy operations except a documented mathematically stateful dependency that cannot be vectorized safely.
- **Source verification:** Implementation review and benchmark
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0037` [ ] `NFR-INDI-006` - Numeric policy

- **Execution domain:** `Indicators`.
- **Execution position:** `37` of `158`.
- **Cannot start before:** Step `P12-S0036` (`NFR-INDI-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 658); matrix row `424`.
- **Source type:** Numeric policy
- **Source responsibility:** Indicator values shall use float64 and approved absolute/relative tolerances; NaN, infinity, overflow, underflow, negative zero, null, and degenerate windows shall follow each approved formula table.
- **Source verification:** Golden/property/edge tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0038` [ ] `NFR-INDI-007` - No-lookahead

- **Execution domain:** `Indicators`.
- **Execution position:** `38` of `158`.
- **Cannot start before:** Step `P12-S0037` (`NFR-INDI-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 659); matrix row `425`.
- **Source type:** No-lookahead
- **Source responsibility:** Every row shall expose earliest-safe UTC `available_at` and source-window bounds; current/future data cannot be represented as already available.
- **Source verification:** Causality tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0039` [ ] `NFR-INDI-008` - Data boundary

- **Execution domain:** `Indicators`.
- **Execution position:** `39` of `158`.
- **Cannot start before:** Step `P12-S0038` (`NFR-INDI-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 660); matrix row `426`.
- **Source type:** Data boundary
- **Source responsibility:** The package shall consume and propagate Data-owned provenance/quality/alignment evidence without implementing provider normalization, calendar, symbol-mapping, or quote-quality policy.
- **Source verification:** Producer-consumer contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0040` [ ] `NFR-INDI-009` - Reliability

- **Execution domain:** `Indicators`.
- **Execution position:** `40` of `158`.
- **Cannot start before:** Step `P12-S0039` (`NFR-INDI-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 661); matrix row `427`.
- **Source type:** Reliability
- **Source responsibility:** Validation and resource/timeout failures shall be atomic, deterministic, and fail closed; no partial official result is published.
- **Source verification:** Failure-injection tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0041` [ ] `NFR-INDI-010` - Concurrency

- **Execution domain:** `Indicators`.
- **Execution position:** `41` of `158`.
- **Cannot start before:** Step `P12-S0040` (`NFR-INDI-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 662); matrix row `428`.
- **Source type:** Concurrency
- **Source responsibility:** Public calculations and registry reads shall be thread-safe through immutability and absence of shared mutable state.
- **Source verification:** Concurrency tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0042` [ ] `NFR-INDI-011` - Testing

- **Execution domain:** `Indicators`.
- **Execution position:** `42` of `158`.
- **Cannot start before:** Step `P12-S0041` (`NFR-INDI-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 663); matrix row `429`.
- **Source type:** Testing
- **Source responsibility:** Every `FR-INDI-*` shall have usage and unit coverage; formulas require approved golden fixtures, invariants/property tests, retained-V1 characterization where applicable, and the approved independent cross-validation policy.
- **Source verification:** Traceability and coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0043` [ ] `NFR-INDI-012` - Coverage

- **Execution domain:** `Indicators`.
- **Execution position:** `43` of `158`.
- **Cannot start before:** Step `P12-S0042` (`NFR-INDI-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 664); matrix row `430`.
- **Source type:** Coverage
- **Source responsibility:** The package shall maintain at least 80% statement and branch coverage, with all documented error paths exercised.
- **Source verification:** `pytest --cov`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0044` [ ] `NFR-INDI-013` - Dependencies

- **Execution domain:** `Indicators`.
- **Execution position:** `44` of `158`.
- **Cannot start before:** Step `P12-S0043` (`NFR-INDI-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 665); matrix row `431`.
- **Source type:** Dependencies
- **Source responsibility:** Runtime dependencies shall be direct project dependencies and locked; current lock evidence is Python 3.14.3, pandas 3.0.3, and NumPy 2.4.6, but pandas/NumPy are not yet direct `pyproject.toml` dependencies.
- **Source verification:** Dependency/lock audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0045` [ ] `NFR-INDI-014` - Security

- **Execution domain:** `Indicators`.
- **Execution position:** `45` of `158`.
- **Cannot start before:** Step `P12-S0044` (`NFR-INDI-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Indicators` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/indicators/README.md` - ``Indicators > 5. Package-Wide Requirements and Shared Configuration`` (line 666); matrix row `432`.
- **Source type:** Security
- **Source responsibility:** Errors, manifests, and quality/provenance metadata shall exclude secrets and raw full input payloads; safe details are redacted before crossing the boundary.
- **Source verification:** Security/redaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-INDI-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - Strategy

Implement `Strategy` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0046` [ ] `NFR-STR-001` - Architecture

- **Execution domain:** `Strategy`.
- **Execution position:** `46` of `158`.
- **Cannot start before:** Step `P12-S0045` (`NFR-INDI-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 763); matrix row `482`.
- **Source type:** Architecture
- **Source responsibility:** Other domains shall use only documented package/feature exports; Strategy shall import no other domain internals.
- **Source verification:** Import-boundary tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0047` [ ] `NFR-STR-002` - Determinism

- **Execution domain:** `Strategy`.
- **Execution position:** `47` of `158`.
- **Cannot start before:** Step `P12-S0046` (`NFR-STR-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 764); matrix row `483`.
- **Source type:** Determinism
- **Source responsibility:** Identical strategy version, config, data, indicators, context, seed, and interface version shall produce identical decisions and intents.
- **Source verification:** Golden and property replay tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0048` [ ] `NFR-STR-003` - Safety

- **Execution domain:** `Strategy`.
- **Execution position:** `48` of `158`.
- **Cannot start before:** Step `P12-S0047` (`NFR-STR-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 765); matrix row `484`.
- **Source type:** Safety
- **Source responsibility:** Strategy shall emit proposals only and shall never approve risk, create official orders/fills, mutate broker/account state, or bypass runtime gates.
- **Source verification:** Boundary tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0049` [ ] `NFR-STR-004` - Security

- **Execution domain:** `Strategy`.
- **Execution position:** `49` of `158`.
- **Cannot start before:** Step `P12-S0048` (`NFR-STR-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 766); matrix row `485`.
- **Source type:** Security
- **Source responsibility:** Strategy imports and evaluation shall perform no network, broker, filesystem, subprocess, environment, secret, wall-clock, or unseeded-random decision access.
- **Source verification:** Import/security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0050` [ ] `NFR-STR-005` - Reliability

- **Execution domain:** `Strategy`.
- **Execution position:** `50` of `158`.
- **Cannot start before:** Step `P12-S0049` (`NFR-STR-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 767); matrix row `486`.
- **Source type:** Reliability
- **Source responsibility:** Validation, lookahead, clock-drift, hash, checkpoint, and safety failures shall fail closed before any intent or state commit.
- **Source verification:** Failure-path tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0051` [ ] `NFR-STR-006` - Error handling

- **Execution domain:** `Strategy`.
- **Execution position:** `51` of `158`.
- **Cannot start before:** Step `P12-S0050` (`NFR-STR-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 768); matrix row `487`.
- **Source type:** Error handling
- **Source responsibility:** Every expected failure shall return one accepted stable code and redacted structured details; raw exceptions shall not cross the public boundary.
- **Source verification:** Error catalogue tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0052` [ ] `NFR-STR-007` - Precision

- **Execution domain:** `Strategy`.
- **Execution position:** `52` of `158`.
- **Cannot start before:** Step `P12-S0051` (`NFR-STR-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 769); matrix row `488`.
- **Source type:** Precision
- **Source responsibility:** Price and quantity values shall use finite`Decimal`; tolerance rules shall be explicit; downstream domains own final execution quantization.
- **Source verification:** Contract/property tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0053` [ ] `NFR-STR-008` - Time

- **Execution domain:** `Strategy`.
- **Execution position:** `53` of `158`.
- **Cannot start before:** Step `P12-S0052` (`NFR-STR-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 770); matrix row `489`.
- **Source type:** Time
- **Source responsibility:** All timestamps shall be aware UTC and point-in-time safe; previous-close is the default bar policy.
- **Source verification:** DST/session/lookahead tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0054` [ ] `NFR-STR-009` - Compatibility

- **Execution domain:** `Strategy`.
- **Execution position:** `54` of `158`.
- **Cannot start before:** Step `P12-S0053` (`NFR-STR-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 771); matrix row `490`.
- **Source type:** Compatibility
- **Source responsibility:** Public contracts shall remain backward compatible within a major version; breaking changes require version bumps, migration guidance, and compatibility tests.
- **Source verification:** Contract compatibility tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0055` [ ] `NFR-STR-010` - Maintainability

- **Execution domain:** `Strategy`.
- **Execution position:** `55` of `158`.
- **Cannot start before:** Step `P12-S0054` (`NFR-STR-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 772); matrix row `491`.
- **Source type:** Maintainability
- **Source responsibility:** Public Python signatures shall be typed; modules/classes/functions shall have Google-style docstrings; private helpers shall begin with`_`.
- **Source verification:** Ruff/mypy/API review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0056` [ ] `NFR-STR-011` - Testing

- **Execution domain:** `Strategy`.
- **Execution position:** `56` of `158`.
- **Cannot start before:** Step `P12-S0055` (`NFR-STR-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 773); matrix row `492`.
- **Source type:** Testing
- **Source responsibility:** Every public requirement shall have a unit test and usage example; collaborative workflows shall have integration tests; package coverage shall be at least 80%.
- **Source verification:** Traceability and coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0057` [ ] `NFR-STR-012` - Performance

- **Execution domain:** `Strategy`.
- **Execution position:** `57` of `158`.
- **Cannot start before:** Step `P12-S0056` (`NFR-STR-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 774); matrix row `493`.
- **Source type:** Performance
- **Source responsibility:** Reference hardware, OS, Python/dependency versions, dataset, strategy type, method, and workload shall be recorded before numerical budgets become CI gates.
- **Source verification:** Approved benchmark report
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-STR-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 5 - Risk

Implement `Risk` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0058` [ ] `NFR-RISK-001` - API boundary

- **Execution domain:** `Risk`.
- **Execution position:** `58` of `158`.
- **Cannot start before:** Step `P12-S0057` (`NFR-STR-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 868); matrix row `567`.
- **Source type:** API boundary
- **Source responsibility:** Cross-domain callers use only documented versioned contracts; root `__all__` is explicit and contains only approved contracts and public operations.
- **Source verification:** Import/API tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0059` [ ] `NFR-RISK-002` - Determinism

- **Execution domain:** `Risk`.
- **Execution position:** `59` of `158`.
- **Cannot start before:** Step `P12-S0058` (`NFR-RISK-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 869); matrix row `568`.
- **Source type:** Determinism
- **Source responsibility:** Identical inputs, config hash, explicit time, seed, and dependency versions produce identical exact results and decision packages.
- **Source verification:** Reproduction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0060` [ ] `NFR-RISK-003` - Precision

- **Execution domain:** `Risk`.
- **Execution position:** `60` of `158`.
- **Cannot start before:** Step `P12-S0059` (`NFR-RISK-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 870); matrix row `569`.
- **Source type:** Precision
- **Source responsibility:** All broker-critical money/size/exposure/tail-risk fields use strict finite Decimal and exact JSON serialization.
- **Source verification:** Contract/property tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0061` [ ] `NFR-RISK-004` - Reliability

- **Execution domain:** `Risk`.
- **Execution position:** `61` of `158`.
- **Cannot start before:** Step `P12-S0060` (`NFR-RISK-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 871); matrix row `570`.
- **Source type:** Reliability
- **Source responsibility:** Invalid input, missing/stale mandatory evidence, unknown approval/kill-switch state, calculation failure, or mandatory persistence failure never yields approval.
- **Source verification:** Failure-path tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0062` [ ] `NFR-RISK-005` - Concurrency

- **Execution domain:** `Risk`.
- **Execution position:** `62` of `158`.
- **Cannot start before:** Step `P12-S0061` (`NFR-RISK-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 872); matrix row `571`.
- **Source type:** Concurrency
- **Source responsibility:** Stateless calculations are thread-safe; shared token/audit/capacity state is synchronized and tested; concurrent requests cannot collectively overspend stale capacity.
- **Source verification:** Concurrent integration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0063` [ ] `NFR-RISK-006` - Security

- **Execution domain:** `Risk`.
- **Execution position:** `63` of `158`.
- **Cannot start before:** Step `P12-S0062` (`NFR-RISK-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 873); matrix row `572`.
- **Source type:** Security
- **Source responsibility:** HMAC-or-stronger signing, least privilege, scope binding, payload guards, and redaction prevent prompt/token/payload bypass and secret exposure.
- **Source verification:** Security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0064` [ ] `NFR-RISK-007` - Observability

- **Execution domain:** `Risk`.
- **Execution position:** `64` of `158`.
- **Cannot start before:** Step `P12-S0063` (`NFR-RISK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 874); matrix row `573`.
- **Source type:** Observability
- **Source responsibility:** Every material decision logs request/workflow/correlation IDs, verdict, reason codes, latency, evidence/config refs, and emits a serializable redacted audit record.
- **Source verification:** Log/audit inspection
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0065` [ ] `NFR-RISK-008` - Performance

- **Execution domain:** `Risk`.
- **Execution position:** `65` of `158`.
- **Cannot start before:** Step `P12-S0064` (`NFR-RISK-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 875); matrix row `574`.
- **Source type:** Performance
- **Source responsibility:** Support 500 positions, 100 strategies, 5,000 return points, and 100 scenarios; normal pre-trade work is no worse than O(n²). Exact p95 gates remain proposed until baselined.
- **Source verification:** Representative benchmarks
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0066` [ ] `NFR-RISK-009` - Maintainability

- **Execution domain:** `Risk`.
- **Execution position:** `66` of `158`.
- **Cannot start before:** Step `P12-S0065` (`NFR-RISK-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 876); matrix row `575`.
- **Source type:** Maintainability
- **Source responsibility:** Python ≥3.14, Google-style module/public docstrings, explicit type hints, focused files, no generic layer without demonstrated need, and project logging/result conventions.
- **Source verification:** Ruff/mypy/structure review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0067` [ ] `NFR-RISK-010` - Testing

- **Execution domain:** `Risk`.
- **Execution position:** `67` of `158`.
- **Cannot start before:** Step `P12-S0066` (`NFR-RISK-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 877); matrix row `576`.
- **Source type:** Testing
- **Source responsibility:** Every public symbol has one usage example and unit coverage; every collaborative workflow has an integration test; package coverage is at least 80%.
- **Source verification:** Test/traceability audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0068` [ ] `NFR-RISK-011` - Persistence

- **Execution domain:** `Risk`.
- **Execution position:** `68` of `158`.
- **Cannot start before:** Step `P12-S0067` (`NFR-RISK-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 878); matrix row `577`.
- **Source type:** Persistence
- **Source responsibility:** Risk owns schemas/semantics while Data owns connection/locking/migration execution; retries are idempotent and exhaustion is surfaced.
- **Source verification:** Persistence contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0069` [ ] `NFR-RISK-012` - Safety

- **Execution domain:** `Risk`.
- **Execution position:** `69` of `158`.
- **Cannot start before:** Step `P12-S0068` (`NFR-RISK-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Risk` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/risk/README.md` - ``Risk > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 879); matrix row `578`.
- **Source type:** Safety
- **Source responsibility:** Risk operations never place or close trades, mutate broker state, or override execution controls; only deterministic approved commands can authorize live actions or clear the kill switch.
- **Source verification:** Permission/side-effect tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RISK-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 6 - Trading

Implement `Trading` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0070` [ ] `NFR-TRD-001` - Safety

- **Execution domain:** `Trading`.
- **Execution position:** `70` of `158`.
- **Cannot start before:** Step `P12-S0069` (`NFR-RISK-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 859); matrix row `662`.
- **Source type:** Safety
- **Source responsibility:** Missing/unverifiable policy, context, authority, or state shall block mutation.
- **Source verification:** Failure-path integration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0071` [ ] `NFR-TRD-002` - Determinism

- **Execution domain:** `Trading`.
- **Execution position:** `71` of `158`.
- **Cannot start before:** Step `P12-S0070` (`NFR-TRD-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 860); matrix row `663`.
- **Source type:** Determinism
- **Source responsibility:** Canonical JSON, Decimal material, IDs, projections, and comparisons shall be deterministic.
- **Source verification:** Replay/hash tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0072` [ ] `NFR-TRD-003` - Security

- **Execution domain:** `Trading`.
- **Execution position:** `72` of `158`.
- **Cannot start before:** Step `P12-S0071` (`NFR-TRD-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 861); matrix row `664`.
- **Source type:** Security
- **Source responsibility:** No secret/provider object shall cross or leak from the boundary; production broker transport must satisfy an approved security profile.
- **Source verification:** Redaction/adapter security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0073` [ ] `NFR-TRD-004` - Reliability

- **Execution domain:** `Trading`.
- **Execution position:** `73` of `158`.
- **Cannot start before:** Step `P12-S0072` (`NFR-TRD-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 862); matrix row `665`.
- **Source type:** Reliability
- **Source responsibility:** Unknown outcomes shall freeze the conflict scope until reconciliation; blind retries are forbidden.
- **Source verification:** Timeout/reconciliation tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0074` [ ] `NFR-TRD-005` - API boundary

- **Execution domain:** `Trading`.
- **Execution position:** `74` of `158`.
- **Cannot start before:** Step `P12-S0073` (`NFR-TRD-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 863); matrix row `666`.
- **Source type:** API boundary
- **Source responsibility:** Consumers shall use documented public exports; package import shall have no runtime side effect.
- **Source verification:** Import/catalog tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0075` [ ] `NFR-TRD-006` - Observability

- **Execution domain:** `Trading`.
- **Execution position:** `75` of `158`.
- **Cannot start before:** Step `P12-S0074` (`NFR-TRD-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 864); matrix row `667`.
- **Source type:** Observability
- **Source responsibility:** Every governed action shall carry trace IDs and emit redacted pre/post evidence; pre-audit failure blocks send.
- **Source verification:** Audit/trace tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0076` [ ] `NFR-TRD-007` - Testing

- **Execution domain:** `Trading`.
- **Execution position:** `76` of `158`.
- **Cannot start before:** Step `P12-S0075` (`NFR-TRD-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 865); matrix row `668`.
- **Source type:** Testing
- **Source responsibility:** Every `FR-TRD-*` shall have a usage example and unit test; collaborative workflows shall have integration tests; coverage shall be at least 80%.
- **Source verification:** Traceability/coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0077` [ ] `NFR-TRD-008` - Performance

- **Execution domain:** `Trading`.
- **Execution position:** `77` of `158`.
- **Cannot start before:** Step `P12-S0076` (`NFR-TRD-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 5. Package-Wide Requirements and Shared Configuration`` (line 866); matrix row `669`.
- **Source type:** Performance
- **Source responsibility:** Only owner-approved provider/workload limits shall become enforced SLOs; unapproved targets shall not be represented as approved.
- **Source verification:** Configuration review/benchmark
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-TRD-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 7 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0078` [ ] `NFR-SIM-001` - Determinism

- **Execution domain:** `Simulation`.
- **Execution position:** `78` of `158`.
- **Cannot start before:** Step `P12-S0077` (`NFR-TRD-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 823); matrix row `749`.
- **Source type:** Determinism
- **Source responsibility:** Identical approved inputs, versions, configuration, and seeds shall produce byte-identical canonical reports and journal identities.
- **Source verification:** Golden and replay tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0079` [ ] `NFR-SIM-002` - Precision

- **Execution domain:** `Simulation`.
- **Execution position:** `79` of `158`.
- **Cannot start before:** Step `P12-S0078` (`NFR-SIM-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 824); matrix row `750`.
- **Source type:** Precision
- **Source responsibility:** Prices, volumes, costs, margin, balances, equity, and PnL shall use finite `Decimal` values with context precision at least 28 and documented quantization.
- **Source verification:** Unit/property tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0080` [ ] `NFR-SIM-003` - No lookahead

- **Execution domain:** `Simulation`.
- **Execution position:** `80` of `158`.
- **Cannot start before:** Step `P12-S0079` (`NFR-SIM-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 825); matrix row `751`.
- **Source type:** No lookahead
- **Source responsibility:** Official execution shall use only evidence whose `available_at` is not later than the current execution time.
- **Source verification:** Timing boundary tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0081` [ ] `NFR-SIM-004` - Safety

- **Execution domain:** `Simulation`.
- **Execution position:** `81` of `158`.
- **Cannot start before:** Step `P12-S0080` (`NFR-SIM-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 826); matrix row `752`.
- **Source type:** Safety
- **Source responsibility:** Importing or running Simulation shall perform no broker mutation, live-adapter import, credential resolution, network request, or unrequested filesystem write.
- **Source verification:** Import-safety and spy tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0082` [ ] `NFR-SIM-005` - API boundary

- **Execution domain:** `Simulation`.
- **Execution position:** `82` of `158`.
- **Cannot start before:** Step `P12-S0081` (`NFR-SIM-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 827); matrix row `753`.
- **Source type:** API boundary
- **Source responsibility:** Package and feature `__init__.py` files shall expose only documented public symbols; the current flat package exports additional V1 symbols and Data helpers.
- **Source verification:** Import-surface test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0083` [ ] `NFR-SIM-006` - Security

- **Execution domain:** `Simulation`.
- **Execution position:** `83` of `158`.
- **Cannot start before:** Step `P12-S0082` (`NFR-SIM-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 828); matrix row `754`.
- **Source type:** Security
- **Source responsibility:** Official requests shall reject arbitrary code and paths, redact secrets, bound payloads/diagnostics, and use vetted references only.
- **Source verification:** Security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0084` [ ] `NFR-SIM-007` - Reliability

- **Execution domain:** `Simulation`.
- **Execution position:** `84` of `158`.
- **Cannot start before:** Step `P12-S0083` (`NFR-SIM-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 829); matrix row `755`.
- **Source type:** Reliability
- **Source responsibility:** Missing evidence, persistence failure, invariant failure, unknown state, or unsupported scope shall fail closed with a deterministic code and no published completed result.
- **Source verification:** Fault-injection tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0085` [ ] `NFR-SIM-008` - Auditability

- **Execution domain:** `Simulation`.
- **Execution position:** `85` of `158`.
- **Cannot start before:** Step `P12-S0084` (`NFR-SIM-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 830); matrix row `756`.
- **Source type:** Auditability
- **Source responsibility:** Every governed transition and rejection shall be traceable through correlation/causation IDs and the canonical hash-chained journal.
- **Source verification:** Journal audit test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0086` [ ] `NFR-SIM-009` - Maintainability

- **Execution domain:** `Simulation`.
- **Execution position:** `86` of `158`.
- **Cannot start before:** Step `P12-S0085` (`NFR-SIM-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 831); matrix row `757`.
- **Source type:** Maintainability
- **Source responsibility:** Modules/files shall match Sections 2 and 4, remain acyclic, and contain Google-style typed public APIs without speculative layers.
- **Source verification:** Structure, Ruff, mypy review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0087` [ ] `NFR-SIM-010` - Testing

- **Execution domain:** `Simulation`.
- **Execution position:** `87` of `158`.
- **Cannot start before:** Step `P12-S0086` (`NFR-SIM-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 832); matrix row `758`.
- **Source type:** Testing
- **Source responsibility:** Every public functional requirement shall have one usage example, at least one unit test, and collaborative workflow coverage, with package coverage at least 80%.
- **Source verification:** Traceability and coverage gate
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0088` [ ] `NFR-SIM-011` - Performance

- **Execution domain:** `Simulation`.
- **Execution position:** `88` of `158`.
- **Cannot start before:** Step `P12-S0087` (`NFR-SIM-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 833); matrix row `759`.
- **Source type:** Performance
- **Source responsibility:** Phase 1 shall record non-blocking deterministic runtime and memory baselines; no blocking numeric gate applies until measured evidence supports a separately approved domain limit.
- **Source verification:** Benchmark report
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0089` [ ] `NFR-SIM-012` - Compatibility

- **Execution domain:** `Simulation`.
- **Execution position:** `89` of `158`.
- **Cannot start before:** Step `P12-S0088` (`NFR-SIM-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 5. Package-Wide Requirements and Shared Configuration`` (line 834); matrix row `760`.
- **Source type:** Compatibility
- **Source responsibility:** `SimulationResult` and owned request contracts shall be versioned; breaking changes require a new version and coordinated consumer migration.
- **Source verification:** Producer-consumer contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-SIM-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 8 - Analytics

Implement `Analytics` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0090` [ ] `NFR-ANLT-001` - API boundary

- **Execution domain:** `Analytics`.
- **Execution position:** `90` of `158`.
- **Cannot start before:** Step `P12-S0089` (`NFR-SIM-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 864); matrix row `823`.
- **Source type:** API boundary
- **Source responsibility:** Package-root exports shall contain only the static catalog-approved high-level operations and owned contracts; deep cross-domain imports and mutable registries are prohibited.
- **Source verification:** Import/catalog tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0091` [ ] `NFR-ANLT-002` - Safety

- **Execution domain:** `Analytics`.
- **Execution position:** `91` of `158`.
- **Cannot start before:** Step `P12-S0090` (`NFR-ANLT-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 865); matrix row `824`.
- **Source type:** Safety
- **Source responsibility:** All behavior shall remain read-only, non-binding, stateless, retry-safe, and free of file/database/network/broker/trading mutations.
- **Source verification:** Side-effect tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0092` [ ] `NFR-ANLT-003` - Determinism

- **Execution domain:** `Analytics`.
- **Execution position:** `92` of `158`.
- **Cannot start before:** Step `P12-S0091` (`NFR-ANLT-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 866); matrix row `825`.
- **Source type:** Determinism
- **Source responsibility:** Identical inputs, configuration, seed, and engine version shall produce identical metrics, warning order, payloads, and hashes in sequential and parallel execution.
- **Source verification:** Replay/parallel tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0093` [ ] `NFR-ANLT-004` - Serialization

- **Execution domain:** `Analytics`.
- **Execution position:** `93` of `158`.
- **Cannot start before:** Step `P12-S0092` (`NFR-ANLT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 867); matrix row `826`.
- **Source type:** Serialization
- **Source responsibility:** Final responses shall be finite JSON-safe values with UTC timestamps and no pandas/NumPy/provider objects.
- **Source verification:** Serialization tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0094` [ ] `NFR-ANLT-005` - Precision

- **Execution domain:** `Analytics`.
- **Execution position:** `94` of `158`.
- **Cannot start before:** Step `P12-S0093` (`NFR-ANLT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 868); matrix row `827`.
- **Source type:** Precision
- **Source responsibility:** Monetary sums and base-currency aggregation shall use `Decimal`; ratios may use deterministic float64 only with cataloged tolerance and report metadata.
- **Source verification:** Golden precision tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0095` [ ] `NFR-ANLT-006` - Security

- **Execution domain:** `Analytics`.
- **Execution position:** `95` of `158`.
- **Cannot start before:** Step `P12-S0094` (`NFR-ANLT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 869); matrix row `828`.
- **Source type:** Security
- **Source responsibility:** Inputs, warnings, errors, logs, metadata, and diagnostics shall redact sensitive keys and values before emission.
- **Source verification:** Redaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0096` [ ] `NFR-ANLT-007` - Reliability

- **Execution domain:** `Analytics`.
- **Execution position:** `96` of `158`.
- **Cannot start before:** Step `P12-S0095` (`NFR-ANLT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 870); matrix row `829`.
- **Source type:** Reliability
- **Source responsibility:** Missing required evidence, incompatible schemas, missing FX, non-finite values, and required-section failures shall fail closed; optional evidence shall be explicitly skipped/degraded.
- **Source verification:** Failure-path tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0097` [ ] `NFR-ANLT-008` - Performance

- **Execution domain:** `Analytics`.
- **Execution position:** `97` of `158`.
- **Cannot start before:** Step `P12-S0096` (`NFR-ANLT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 871); matrix row `830`.
- **Source type:** Performance
- **Source responsibility:** Input, iterations, runtime, memory, response, and dashboard limits shall be measurable on approved reference hardware and enforced before production handoff.
- **Source verification:** Limits ADR and benchmarks
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0098` [ ] `NFR-ANLT-009` - Observability

- **Execution domain:** `Analytics`.
- **Execution position:** `98` of `158`.
- **Cannot start before:** Step `P12-S0097` (`NFR-ANLT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 872); matrix row `831`.
- **Source type:** Observability
- **Source responsibility:** Public operations shall log start, validation failure, controlled warning, success, and failure using request/correlation IDs without raw private payloads.
- **Source verification:** Log-capture/security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0099` [ ] `NFR-ANLT-010` - Compatibility

- **Execution domain:** `Analytics`.
- **Execution position:** `99` of `158`.
- **Cannot start before:** Step `P12-S0098` (`NFR-ANLT-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 873); matrix row `832`.
- **Source type:** Compatibility
- **Source responsibility:** Source and output contracts shall follow the approved compatibility matrix and system versioning policy.
- **Source verification:** Producer-consumer contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0100` [ ] `NFR-ANLT-011` - Testing

- **Execution domain:** `Analytics`.
- **Execution position:** `100` of `158`.
- **Cannot start before:** Step `P12-S0099` (`NFR-ANLT-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 874); matrix row `833`.
- **Source type:** Testing
- **Source responsibility:** Every `FR-ANLT-*` shall have one runnable usage example, at least one unit test, and every collaborative workflow an integration test.
- **Source verification:** Traceability audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0101` [ ] `NFR-ANLT-012` - Dependencies

- **Execution domain:** `Analytics`.
- **Execution position:** `101` of `158`.
- **Cannot start before:** Step `P12-S0100` (`NFR-ANLT-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 875); matrix row `834`.
- **Source type:** Dependencies
- **Source responsibility:** Any direct `numpy`/`pandas` use shall be declared in `pyproject.toml`; no optional/speculative dependency is permitted.
- **Source verification:** Dependency audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0102` [ ] `NFR-ANLT-013` - Coverage

- **Execution domain:** `Analytics`.
- **Execution position:** `102` of `158`.
- **Cannot start before:** Step `P12-S0101` (`NFR-ANLT-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Analytics` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/analytics/README.md` - ``Analytics > 5. Package-Wide Requirements and Shared Configuration`` (line 876); matrix row `835`.
- **Source type:** Coverage
- **Source responsibility:** Final implementation shall maintain at least 80% statement coverage and cover documented errors, boundaries, and retained behavior.
- **Source verification:** Targeted pytest with coverage
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-ANLT-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 9 - Optimization

Implement `Optimization` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0103` [ ] `NFR-OPT-001` - Architecture

- **Execution domain:** `Optimization`.
- **Execution position:** `103` of `158`.
- **Cannot start before:** Step `P12-S0102` (`NFR-ANLT-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 898); matrix row `908`.
- **Source type:** Architecture
- **Source responsibility:** Other domains shall use only documented public contracts; Optimization shall not import another domain's internals.
- **Source verification:** Import/dependency test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0104` [ ] `NFR-OPT-002` - Determinism

- **Execution domain:** `Optimization`.
- **Execution position:** `104` of `158`.
- **Cannot start before:** Step `P12-S0103` (`NFR-OPT-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 899); matrix row `909`.
- **Source type:** Determinism
- **Source responsibility:** Identical deterministic inputs shall produce identical candidates, hashes, ordering, scores, and evidence.
- **Source verification:** Replay test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0105` [ ] `NFR-OPT-003` - Safety

- **Execution domain:** `Optimization`.
- **Execution position:** `105` of `158`.
- **Cannot start before:** Step `P12-S0104` (`NFR-OPT-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 900); matrix row `910`.
- **Source type:** Safety
- **Source responsibility:** Optimization shall never place or close trades, access live brokers, mutate Strategy state, or return live approval.
- **Source verification:** Production safety test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0106` [ ] `NFR-OPT-004` - Reliability

- **Execution domain:** `Optimization`.
- **Execution position:** `106` of `158`.
- **Cannot start before:** Step `P12-S0105` (`NFR-OPT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 901); matrix row `911`.
- **Source type:** Reliability
- **Source responsibility:** Missing policy, resource caps, provenance, adapter compatibility, or required evidence shall fail closed before expensive work.
- **Source verification:** Failure-path tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0107` [ ] `NFR-OPT-005` - Security

- **Execution domain:** `Optimization`.
- **Execution position:** `107` of `158`.
- **Cannot start before:** Step `P12-S0106` (`NFR-OPT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 902); matrix row `912`.
- **Source type:** Security
- **Source responsibility:** Logs, errors, events, reports, and packages shall redact credentials, authorization data, private payloads, sensitive paths, and environment variables.
- **Source verification:** Security/redaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0108` [ ] `NFR-OPT-006` - Serialization

- **Execution domain:** `Optimization`.
- **Execution position:** `108` of `158`.
- **Cannot start before:** Step `P12-S0107` (`NFR-OPT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 903); matrix row `913`.
- **Source type:** Serialization
- **Source responsibility:** Every public result shall be JSON-safe and reject unsupported provider/backend objects with structured errors.
- **Source verification:** Golden serialization tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0109` [ ] `NFR-OPT-007` - Import safety

- **Execution domain:** `Optimization`.
- **Execution position:** `109` of `158`.
- **Cannot start before:** Step `P12-S0108` (`NFR-OPT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 904); matrix row `914`.
- **Source type:** Import safety
- **Source responsibility:** Importing the package shall perform no broker/database/network/multiprocessing/heavy-dependency initialization.
- **Source verification:** Import side-effect test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0110` [ ] `NFR-OPT-008` - Observability

- **Execution domain:** `Optimization`.
- **Execution position:** `110` of `158`.
- **Cannot start before:** Step `P12-S0109` (`NFR-OPT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 905); matrix row `915`.
- **Source type:** Observability
- **Source responsibility:** Governed workflows shall carry request/correlation IDs and emit redacted events containing validation failures, cap rejections, duration, and candidate counts.
- **Source verification:** Event inspection/integration test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0111` [ ] `NFR-OPT-009` - Time

- **Execution domain:** `Optimization`.
- **Execution position:** `111` of `158`.
- **Cannot start before:** Step `P12-S0110` (`NFR-OPT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 906); matrix row `916`.
- **Source type:** Time
- **Source responsibility:** All cross-domain times and split boundaries shall be timezone-aware UTC; timeouts use a monotonic clock.
- **Source verification:** UTC and clock tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0112` [ ] `NFR-OPT-010` - Compatibility

- **Execution domain:** `Optimization`.
- **Execution position:** `112` of `158`.
- **Cannot start before:** Step `P12-S0111` (`NFR-OPT-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 907); matrix row `917`.
- **Source type:** Compatibility
- **Source responsibility:** Breaking changes to the approved public API or `OptimizationResult v1` require a version bump.
- **Source verification:** Contract compatibility tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0113` [ ] `NFR-OPT-011` - Persistence truth

- **Execution domain:** `Optimization`.
- **Execution position:** `113` of `158`.
- **Cannot start before:** Step `P12-S0112` (`NFR-OPT-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 908); matrix row `918`.
- **Source type:** Persistence truth
- **Source responsibility:** Packaging/report functions shall never imply persistence; any public durable-success claim requires an `OptimizationPersistenceReceipt` from the injected Optimization store.
- **Source verification:** Side-effect tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0114` [ ] `NFR-OPT-012` - Testing

- **Execution domain:** `Optimization`.
- **Execution position:** `114` of `158`.
- **Cannot start before:** Step `P12-S0113` (`NFR-OPT-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Optimization` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/optimization/README.md` - ``Optimization > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 909); matrix row `919`.
- **Source type:** Testing
- **Source responsibility:** Every public requirement shall have a unit test and runnable usage example; package statement coverage shall be at least 80%.
- **Source verification:** Traceability and coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-OPT-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 10 - Research

Implement `Research` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0115` [ ] `NFR-RES-001` - Safety

- **Execution domain:** `Research`.
- **Execution position:** `115` of `158`.
- **Cannot start before:** Step `P12-S0114` (`NFR-OPT-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1111); matrix row `1040`.
- **Source type:** Safety
- **Source responsibility:** Research shall remain advisory and shall never place, modify, cancel, route, approve, or block live orders or mutate Strategy/Risk/Trading state.
- **Source verification:** `tests/research/integration/test_advisory_boundary.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0116` [ ] `NFR-RES-002` - Reliability

- **Execution domain:** `Research`.
- **Execution position:** `116` of `158`.
- **Cannot start before:** Step `P12-S0115` (`NFR-RES-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1112); matrix row `1041`.
- **Source type:** Reliability
- **Source responsibility:** Any attempted live-state mutation or governance bypass shall fail closed before side effects.
- **Source verification:** Boundary failure-path test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0117` [ ] `NFR-RES-003` - Reproducibility

- **Execution domain:** `Research`.
- **Execution position:** `117` of `158`.
- **Cannot start before:** Step `P12-S0116` (`NFR-RES-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1113); matrix row `1042`.
- **Source type:** Reproducibility
- **Source responsibility:** Fixed data, effective config, seed, dependency versions, and schema version shall produce equivalent outputs; hashes and effective seeds are recorded.
- **Source verification:** Seeded replay tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0118` [ ] `NFR-RES-004` - Leakage

- **Execution domain:** `Research`.
- **Execution position:** `118` of `158`.
- **Cannot start before:** Step `P12-S0117` (`NFR-RES-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1114); matrix row `1043`.
- **Source type:** Leakage
- **Source responsibility:** Forward-looking fields shall be declared, detectable, excluded from feature inputs, and gated before publication.
- **Source verification:** Generated-case leakage tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0119` [ ] `NFR-RES-005` - Statistical quality

- **Execution domain:** `Research`.
- **Execution position:** `119` of `158`.
- **Cannot start before:** Step `P12-S0118` (`NFR-RES-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1115); matrix row `1044`.
- **Source type:** Statistical quality
- **Source responsibility:** Results shall expose relevant uncertainty and multiple-comparison controls, sample sizes, null assumptions, and warnings.
- **Source verification:** Statistical contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0120` [ ] `NFR-RES-006` - API boundary

- **Execution domain:** `Research`.
- **Execution position:** `120` of `158`.
- **Cannot start before:** Step `P12-S0119` (`NFR-RES-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1116); matrix row `1045`.
- **Source type:** API boundary
- **Source responsibility:** Other domains shall use only documented package exports; `__all__` and classifications are unique, resolvable, and stable.
- **Source verification:** Import/API audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0121` [ ] `NFR-RES-007` - Import safety

- **Execution domain:** `Research`.
- **Execution position:** `121` of `158`.
- **Cannot start before:** Step `P12-S0120` (`NFR-RES-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1117); matrix row `1046`.
- **Source type:** Import safety
- **Source responsibility:** Importing Research shall perform no network, disk write, provider/credential initialization, live-state read, or heavy computation.
- **Source verification:** Import-time safety test
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0122` [ ] `NFR-RES-008` - Security

- **Execution domain:** `Research`.
- **Execution position:** `122` of `158`.
- **Cannot start before:** Step `P12-S0121` (`NFR-RES-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1118); matrix row `1047`.
- **Source type:** Security
- **Source responsibility:** Secrets, credentials, broker/account identifiers, private fields, and forbidden forward fields shall not appear in artifacts, warnings, logs, errors, or audit metadata.
- **Source verification:** Nested masking/security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0123` [ ] `NFR-RES-009` - Persistence safety

- **Execution domain:** `Research`.
- **Execution position:** `123` of `158`.
- **Cannot start before:** Step `P12-S0122` (`NFR-RES-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1119); matrix row `1048`.
- **Source type:** Persistence safety
- **Source responsibility:** Artifact writes shall prevent traversal and accidental overwrite, enforce size/encoding/root policy, and use atomic replacement where approved.
- **Source verification:** Persistence/concurrency tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0124` [ ] `NFR-RES-010` - Resource safety

- **Execution domain:** `Research`.
- **Execution position:** `124` of `158`.
- **Cannot start before:** Step `P12-S0123` (`NFR-RES-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1120); matrix row `1049`.
- **Source type:** Resource safety
- **Source responsibility:** Heavy operations shall enforce approved row/iteration/duration/artifact bounds and fail explicitly rather than attempt unbounded work.
- **Source verification:** Resource tests against the explicit resource limits
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0125` [ ] `NFR-RES-011` - Observability

- **Execution domain:** `Research`.
- **Execution position:** `125` of `158`.
- **Cannot start before:** Step `P12-S0124` (`NFR-RES-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1121); matrix row `1050`.
- **Source type:** Observability
- **Source responsibility:** Validation failures, cleaning actions, masking, insufficiency, partial stages, and duration shall emit structured redacted warnings/logs with trace identifiers.
- **Source verification:** Observability tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0126` [ ] `NFR-RES-012` - Platform

- **Execution domain:** `Research`.
- **Execution position:** `126` of `158`.
- **Cannot start before:** Step `P12-S0125` (`NFR-RES-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1122); matrix row `1051`.
- **Source type:** Platform
- **Source responsibility:** Deterministic library behavior and safe persistence shall work on the project's supported Python 3.14 Windows baseline; platform atomicity differences are explicit.
- **Source verification:** Windows CI
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0127` [ ] `NFR-RES-013` - Maintainability

- **Execution domain:** `Research`.
- **Execution position:** `127` of `158`.
- **Cannot start before:** Step `P12-S0126` (`NFR-RES-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1123); matrix row `1052`.
- **Source type:** Maintainability
- **Source responsibility:** No recursive facade scan, duplicate formula wrapper, generic helper/service/manager, mutable global registry, or cross-domain internal import shall exist.
- **Source verification:** Structure/dependency audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0128` [ ] `NFR-RES-014` - Testing

- **Execution domain:** `Research`.
- **Execution position:** `128` of `158`.
- **Cannot start before:** Step `P12-S0127` (`NFR-RES-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1124); matrix row `1053`.
- **Source type:** Testing
- **Source responsibility:** Every `FR-RES-*` shall have its mapped usage and unit test; every collaborative workflow shall have its mapped integration test; coverage shall be at least 80%.
- **Source verification:** Traceability/coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0129` [ ] `NFR-RES-015` - Documentation

- **Execution domain:** `Research`.
- **Execution position:** `129` of `158`.
- **Cannot start before:** Step `P12-S0128` (`NFR-RES-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Research` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/research/README.md` - ``Research > 5. Package-Wide Requirements and Shared Configuration`` (line 1125); matrix row `1054`.
- **Source type:** Documentation
- **Source responsibility:** Every module, class, function, and method shall use Google-style docstrings and every public DataFrame contract shall document columns, index, timezone, alignment, NaNs, and mutation.
- **Source verification:** Documentation contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-RES-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 11 - Portfolio

Implement `Portfolio` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0130` [ ] `NFR-PORT-001` - Google Python Style, complete types, Google docstrings, absolute imports, and no print.

- **Execution domain:** `Portfolio`.
- **Execution position:** `130` of `158`.
- **Cannot start before:** Step `P12-S0129` (`NFR-RES-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 457); matrix row `1107`.
- **Source requirement:** Google Python Style, complete types, Google docstrings, absolute imports, and no `print`.
- **Source verification:** Ruff/mypy/review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0131` [ ] `NFR-PORT-002` - Deterministic output for identical versioned inputs and explicit configuration.

- **Execution domain:** `Portfolio`.
- **Execution position:** `131` of `158`.
- **Cannot start before:** Step `P12-S0130` (`NFR-PORT-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 458); matrix row `1108`.
- **Source requirement:** Deterministic output for identical versioned inputs and explicit configuration.
- **Source verification:** Reproducibility tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0132` [ ] `NFR-PORT-003` - Fail closed on missing evidence, authorization, policy, configuration, or ownership ambiguity.

- **Execution domain:** `Portfolio`.
- **Execution position:** `132` of `158`.
- **Cannot start before:** Step `P12-S0131` (`NFR-PORT-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 459); matrix row `1109`.
- **Source requirement:** Fail closed on missing evidence, authorization, policy, configuration, or ownership ambiguity.
- **Source verification:** Negative tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0133` [ ] `NFR-PORT-004` - Never log secrets, raw approval tokens, credentials, or unredacted account data.

- **Execution domain:** `Portfolio`.
- **Execution position:** `133` of `158`.
- **Cannot start before:** Step `P12-S0132` (`NFR-PORT-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 460); matrix row `1110`.
- **Source requirement:** Never log secrets, raw approval tokens, credentials, or unredacted account data.
- **Source verification:** Security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0134` [ ] `NFR-PORT-005` - Maintain at least 80% package test coverage.

- **Execution domain:** `Portfolio`.
- **Execution position:** `134` of `158`.
- **Cannot start before:** Step `P12-S0133` (`NFR-PORT-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 461); matrix row `1111`.
- **Source requirement:** Maintain at least 80% package test coverage.
- **Source verification:** Coverage report
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0135` [ ] `NFR-PORT-006` - No live side effect originates in Portfolio; Trading remains the sole execution authority.

- **Execution domain:** `Portfolio`.
- **Execution position:** `135` of `158`.
- **Cannot start before:** Step `P12-S0134` (`NFR-PORT-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 462); matrix row `1112`.
- **Source requirement:** No live side effect originates in Portfolio; Trading remains the sole execution authority.
- **Source verification:** Dependency/integration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0136` [ ] `NFR-PORT-007` - All money, rates, weights, and tolerances use documented decimal/precision rules; no binary-float ambiguity at boundaries.

- **Execution domain:** `Portfolio`.
- **Execution position:** `136` of `158`.
- **Cannot start before:** Step `P12-S0135` (`NFR-PORT-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 463); matrix row `1113`.
- **Source requirement:** All money, rates, weights, and tolerances use documented decimal/precision rules; no binary-float ambiguity at boundaries.
- **Source verification:** Numeric tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0137` [ ] `NFR-PORT-008` - All timestamps are timezone-aware UTC.

- **Execution domain:** `Portfolio`.
- **Execution position:** `137` of `158`.
- **Cannot start before:** Step `P12-S0136` (`NFR-PORT-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 464); matrix row `1114`.
- **Source requirement:** All timestamps are timezone-aware UTC.
- **Source verification:** Validation tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0138` [ ] `NFR-PORT-009` - No hidden numeric defaults; every cap, threshold, tolerance, schedule, expiry, and observation minimum is required configuration.

- **Execution domain:** `Portfolio`.
- **Execution position:** `138` of `158`.
- **Cannot start before:** Step `P12-S0137` (`NFR-PORT-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 465); matrix row `1115`.
- **Source requirement:** No hidden numeric defaults; every cap, threshold, tolerance, schedule, expiry, and observation minimum is required configuration.
- **Source verification:** Configuration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0139` [ ] `NFR-PORT-010` - Package errors extend Utils canonical exceptions and map to structured Portfolio codes.

- **Execution domain:** `Portfolio`.
- **Execution position:** `139` of `158`.
- **Cannot start before:** Step `P12-S0138` (`NFR-PORT-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Portfolio` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/portfolio/README.md` - ``Portfolio > 5. Package-Wide Requirements and Shared Configuration`` (line 466); matrix row `1116`.
- **Source requirement:** Package errors extend Utils canonical exceptions and map to structured Portfolio codes.
- **Source verification:** Error tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-PORT-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 12 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P12-S0140` [ ] `NFR-API-001` - Architecture

- **Execution domain:** `UI/API`.
- **Execution position:** `140` of `158`.
- **Cannot start before:** Step `P12-S0139` (`NFR-PORT-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 817); matrix row `1210`.
- **Source type:** Architecture
- **Source responsibility:** UI/API shall import only documented public domain APIs and contain no domain calculations or direct persistence/broker access.
- **Source verification:** Import and thin-route tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0141` [ ] `NFR-API-002` - Security

- **Execution domain:** `UI/API`.
- **Execution position:** `141` of `158`.
- **Cannot start before:** Step `P12-S0140` (`NFR-API-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 818); matrix row `1211`.
- **Source type:** Security
- **Source responsibility:** Protected endpoints require validated user/service context; governed writes require permission, audit, idempotency, fresh evidence, and approval when applicable.
- **Source verification:** Security integration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0142` [ ] `NFR-API-003` - Safety

- **Execution domain:** `UI/API`.
- **Execution position:** `142` of `158`.
- **Cannot start before:** Step `P12-S0141` (`NFR-API-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 819); matrix row `1212`.
- **Source type:** Safety
- **Source responsibility:** Live/paper mutations cannot bypass Trading/Risk live flags, broker readiness, reconciliation, idempotency, audit, or kill-switch gates.
- **Source verification:** Live safety tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0143` [ ] `NFR-API-004` - Contracts

- **Execution domain:** `UI/API`.
- **Execution position:** `143` of `158`.
- **Cannot start before:** Step `P12-S0142` (`NFR-API-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 820); matrix row `1213`.
- **Source type:** Contracts
- **Source responsibility:** Non-stream responses use `ApiResponse`; streams use `StreamEvent`; API/UI drift fails CI.
- **Source verification:** OpenAPI/DTO snapshot tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0144` [ ] `NFR-API-005` - Security

- **Execution domain:** `UI/API`.
- **Execution position:** `144` of `158`.
- **Cannot start before:** Step `P12-S0143` (`NFR-API-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 821); matrix row `1214`.
- **Source type:** Security
- **Source responsibility:** Logs, errors, traces, telemetry, examples, and screenshots contain no tokens, credentials, passwords, CSRF values, raw secrets, or private broker data.
- **Source verification:** Redaction tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0145` [ ] `NFR-API-006` - Reliability

- **Execution domain:** `UI/API`.
- **Execution position:** `145` of `158`.
- **Cannot start before:** Step `P12-S0144` (`NFR-API-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 822); matrix row `1215`.
- **Source type:** Reliability
- **Source responsibility:** Required-route/dependency failures block startup/readiness; only explicitly optional routes degrade with a visible reason.
- **Source verification:** Startup failure tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0146` [ ] `NFR-API-007` - Streaming

- **Execution domain:** `UI/API`.
- **Execution position:** `146` of `158`.
- **Cannot start before:** Step `P12-S0145` (`NFR-API-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 823); matrix row `1216`.
- **Source type:** Streaming
- **Source responsibility:** Disconnect stops delivery, releases resources, preserves authoritative owner state, and emits no later client events.
- **Source verification:** Stream lifecycle tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0147` [ ] `NFR-API-008` - Freshness

- **Execution domain:** `UI/API`.
- **Execution position:** `147` of `158`.
- **Cannot start before:** Step `P12-S0146` (`NFR-API-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 824); matrix row `1217`.
- **Source type:** Freshness
- **Source responsibility:** UI shows stale/unavailable state and blocks governed decisions until authoritative refresh.
- **Source verification:** Frontend integration tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0148` [ ] `NFR-API-009` - Accessibility

- **Execution domain:** `UI/API`.
- **Execution position:** `148` of `158`.
- **Cannot start before:** Step `P12-S0147` (`NFR-API-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 825); matrix row `1218`.
- **Source type:** Accessibility
- **Source responsibility:** Core workflows meet approved accessibility target (prefer WCAG 2.1 AA) and remain usable without horizontal-scroll-only critical controls.
- **Source verification:** Automated and manual accessibility tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0149` [ ] `NFR-API-010` - Observability

- **Execution domain:** `UI/API`.
- **Execution position:** `149` of `158`.
- **Cannot start before:** Step `P12-S0148` (`NFR-API-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 826); matrix row `1219`.
- **Source type:** Observability
- **Source responsibility:** Boundary actions carry request/correlation IDs and emit redacted audit/telemetry with route, intent, actor when available, status, duration, and error code.
- **Source verification:** Trace inspection tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0150` [ ] `NFR-API-011` - Pagination

- **Execution domain:** `UI/API`.
- **Execution position:** `150` of `158`.
- **Cannot start before:** Step `P12-S0149` (`NFR-API-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 827); matrix row `1220`.
- **Source type:** Pagination
- **Source responsibility:** Every list route uses opaque cursors, stable ordering, default 50, maximum 200, and empty list plus null next cursor.
- **Source verification:** Pagination contract tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0151` [ ] `NFR-API-012` - Timeouts

- **Execution domain:** `UI/API`.
- **Execution position:** `151` of `158`.
- **Cannot start before:** Step `P12-S0150` (`NFR-API-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 828); matrix row `1221`.
- **Source type:** Timeouts
- **Source responsibility:** Non-stream endpoints complete or return a structured timeout within 30 seconds; no initial Simulation/Optimization async contract exists.
- **Source verification:** Deadline tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0152` [ ] `NFR-API-013` - Resilience

- **Execution domain:** `UI/API`.
- **Execution position:** `152` of `158`.
- **Cannot start before:** Step `P12-S0151` (`NFR-API-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 829); matrix row `1222`.
- **Source type:** Resilience
- **Source responsibility:** Only opt-in idempotent reads retry once for classified transient failures; governed writes and unknown broker outcomes never retry blindly.
- **Source verification:** Retry tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0153` [ ] `NFR-API-014` - Imports

- **Execution domain:** `UI/API`.
- **Execution position:** `153` of `158`.
- **Cannot start before:** Step `P12-S0152` (`NFR-API-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 830); matrix row `1223`.
- **Source type:** Imports
- **Source responsibility:** Import routes validate content type/size, duplicates, parse failure, cleanup, and compensating behavior before state publication.
- **Source verification:** Import security tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0154` [ ] `NFR-API-015` - Documentation

- **Execution domain:** `UI/API`.
- **Execution position:** `154` of `158`.
- **Cannot start before:** Step `P12-S0153` (`NFR-API-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 831); matrix row `1224`.
- **Source type:** Documentation
- **Source responsibility:** Docs I/O accepts safe relative Markdown paths only and rejects traversal, symlink escape, unsupported content, and disallowed environments.
- **Source verification:** Filesystem boundary tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0155` [ ] `NFR-API-016` - Testing

- **Execution domain:** `UI/API`.
- **Execution position:** `155` of `158`.
- **Cannot start before:** Step `P12-S0154` (`NFR-API-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 832); matrix row `1225`.
- **Source type:** Testing
- **Source responsibility:** Every public symbol has one usage example and unit test; every collaborative workflow has an integration test; coverage is at least 80%.
- **Source verification:** Traceability and coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0156` [ ] `NFR-API-017` - Quality

- **Execution domain:** `UI/API`.
- **Execution position:** `156` of `158`.
- **Cannot start before:** Step `P12-S0155` (`NFR-API-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 833); matrix row `1226`.
- **Source type:** Quality
- **Source responsibility:** Backend and frontend build, lint, format, type, contract, security, and targeted tests are runnable in CI.
- **Source verification:** CI pipeline
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P12-S0157` [ ] `NFR-API-018` - Determinism

- **Execution domain:** `UI/API`.
- **Execution position:** `157` of `158`.
- **Cannot start before:** Step `P12-S0156` (`NFR-API-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T3 Complete; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 5. Package-Wide Requirements and Shared Configuration > Non-functional requirements`` (line 834); matrix row `1227`.
- **Source type:** Determinism
- **Source responsibility:** Contract registration, route ordering, cursor ordering, and idempotency conflict behavior are deterministic.
- **Source verification:** Replay/property tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-API-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 13 - System phase completion

Perform the final assurance, parity, or release-completion work after all implementation and verification steps above.

#### Step `P12-S0158` [ ] `P-SYS-006` - Production assurance, release hardening, and quality-gate evidence (provisional)

- **Execution domain:** `System`.
- **Execution position:** `158` of `158`.
- **Cannot start before:** Step `P12-S0157` (`NFR-API-018`).
- **Authoritative dependency evidence:** `P-SYS-004` completed in Phase 11 before this phase opened.
- **Ordering basis:** Final phase assurance after implementation and verification.
- **Delivery type:** Resolve specification before implementation.
- **Classification:** T3 Complete; size `M`; source status `Pending`.
- **Dependencies:** `P-SYS-004`.
- **Authoritative source:** `docs/PROJECT.md` - ``No exact source section located`` (anchor pending); matrix row `29`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SYS-006`.
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

- **Expected assigned IDs:** 158.
- **Plan requirement entries:** 158.
- **Matrix phase:** `12`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (1):** `P-SYS-006`
- **Utils (0):** None.
- **Brokers (19):** `CAP-BRK-019`, `FR-BRK-109`, `FR-BRK-134`, `NFR-BRK-001`, `NFR-BRK-002`, `NFR-BRK-003`, `NFR-BRK-004`, `NFR-BRK-005`, `NFR-BRK-006`, `NFR-BRK-007`, `NFR-BRK-008`, `NFR-BRK-009`, `NFR-BRK-010`, `NFR-BRK-011`, `NFR-BRK-012`, `NFR-BRK-013`, `NFR-BRK-014`, `NFR-BRK-015`, `P-BRK-009`
- **Data (12):** `NFR-DATA-001`, `NFR-DATA-002`, `NFR-DATA-003`, `NFR-DATA-004`, `NFR-DATA-005`, `NFR-DATA-006`, `NFR-DATA-007`, `NFR-DATA-008`, `NFR-DATA-009`, `NFR-DATA-010`, `NFR-DATA-011`, `NFR-DATA-012`
- **Indicators (14):** `NFR-INDI-001`, `NFR-INDI-002`, `NFR-INDI-003`, `NFR-INDI-004`, `NFR-INDI-005`, `NFR-INDI-006`, `NFR-INDI-007`, `NFR-INDI-008`, `NFR-INDI-009`, `NFR-INDI-010`, `NFR-INDI-011`, `NFR-INDI-012`, `NFR-INDI-013`, `NFR-INDI-014`
- **Strategy (12):** `NFR-STR-001`, `NFR-STR-002`, `NFR-STR-003`, `NFR-STR-004`, `NFR-STR-005`, `NFR-STR-006`, `NFR-STR-007`, `NFR-STR-008`, `NFR-STR-009`, `NFR-STR-010`, `NFR-STR-011`, `NFR-STR-012`
- **Risk (12):** `NFR-RISK-001`, `NFR-RISK-002`, `NFR-RISK-003`, `NFR-RISK-004`, `NFR-RISK-005`, `NFR-RISK-006`, `NFR-RISK-007`, `NFR-RISK-008`, `NFR-RISK-009`, `NFR-RISK-010`, `NFR-RISK-011`, `NFR-RISK-012`
- **Trading (8):** `NFR-TRD-001`, `NFR-TRD-002`, `NFR-TRD-003`, `NFR-TRD-004`, `NFR-TRD-005`, `NFR-TRD-006`, `NFR-TRD-007`, `NFR-TRD-008`
- **Simulation (12):** `NFR-SIM-001`, `NFR-SIM-002`, `NFR-SIM-003`, `NFR-SIM-004`, `NFR-SIM-005`, `NFR-SIM-006`, `NFR-SIM-007`, `NFR-SIM-008`, `NFR-SIM-009`, `NFR-SIM-010`, `NFR-SIM-011`, `NFR-SIM-012`
- **Analytics (13):** `NFR-ANLT-001`, `NFR-ANLT-002`, `NFR-ANLT-003`, `NFR-ANLT-004`, `NFR-ANLT-005`, `NFR-ANLT-006`, `NFR-ANLT-007`, `NFR-ANLT-008`, `NFR-ANLT-009`, `NFR-ANLT-010`, `NFR-ANLT-011`, `NFR-ANLT-012`, `NFR-ANLT-013`
- **Optimization (12):** `NFR-OPT-001`, `NFR-OPT-002`, `NFR-OPT-003`, `NFR-OPT-004`, `NFR-OPT-005`, `NFR-OPT-006`, `NFR-OPT-007`, `NFR-OPT-008`, `NFR-OPT-009`, `NFR-OPT-010`, `NFR-OPT-011`, `NFR-OPT-012`
- **Research (15):** `NFR-RES-001`, `NFR-RES-002`, `NFR-RES-003`, `NFR-RES-004`, `NFR-RES-005`, `NFR-RES-006`, `NFR-RES-007`, `NFR-RES-008`, `NFR-RES-009`, `NFR-RES-010`, `NFR-RES-011`, `NFR-RES-012`, `NFR-RES-013`, `NFR-RES-014`, `NFR-RES-015`
- **Portfolio (10):** `NFR-PORT-001`, `NFR-PORT-002`, `NFR-PORT-003`, `NFR-PORT-004`, `NFR-PORT-005`, `NFR-PORT-006`, `NFR-PORT-007`, `NFR-PORT-008`, `NFR-PORT-009`, `NFR-PORT-010`
- **UI/API (18):** `NFR-API-001`, `NFR-API-002`, `NFR-API-003`, `NFR-API-004`, `NFR-API-005`, `NFR-API-006`, `NFR-API-007`, `NFR-API-008`, `NFR-API-009`, `NFR-API-010`, `NFR-API-011`, `NFR-API-012`, `NFR-API-013`, `NFR-API-014`, `NFR-API-015`, `NFR-API-016`, `NFR-API-017`, `NFR-API-018`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
