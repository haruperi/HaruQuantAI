# Phase 2 Implementation Plan - v1.2 - Trusted evidence and observability

> **Status:** Not started
> **Requirement count:** 69
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 2
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 2. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.2`.
- **Theme:** Trusted evidence and observability.
- **Entry condition:** Phase 1 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Repeat the Phase 1 workflows through persisted evidence and demonstrate stale/malformed rejection.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.2 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires weak evidence; adds bounded storage/source-policy complexity.

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
| Utils | 18 | Complete settings, audit construction, redaction, error routing, and log sinks. |
| Brokers | 7 | Add transport circuit behavior, Yahoo reads, readiness evidence, and technical observability. |
| Data | 32 | Complete quality/provenance, SQLite/files/cache/audit, source policy, resampling, and alignment. |
| Indicators | 0 | Propagate stronger evidence. |
| Strategy | 2 | Add safe diagnostics and stricter point-in-time checks. |
| Risk | 0 | Consume stronger evidence through Phase 1 gates. |
| Trading | 0 | Persist richer dependency failures. |
| Simulation | 1 | Block severe data-quality errors. |
| Analytics | 0 | Harden adapters, JSON safety, warnings, lineage, and hashes. |
| Optimization | 0 | Validate provenance before search. |
| Research | 0 | Harden dataset preparation/core profiles. |
| Portfolio | 0 | Consume validated evidence. |
| UI/API | 8 | Deepen sessions, middleware, readiness, settings, and audit views. |

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

### Stage 1 - System foundations

Resolve and evidence the phase-level system contracts and configuration prerequisites before domain implementation begins.

#### Step `P02-S0001` [ ] `P-SYS-003` - Shared configuration and limits manifest

- **Execution domain:** `System`.
- **Execution position:** `1` of `69`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** Phase-level system foundation before domain code.
- **Delivery type:** Resolve specification before implementation.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `docs/PROJECT.md` - ``§7 System-Wide Requirements`` (`P-SYS-003`); matrix row `22`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-SYS-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Utils

Implement `Utils` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P02-S0002` [ ] `P-UTL-006` - security feature/component (provisional)

- **Execution domain:** `Utils`.
- **Execution position:** `2` of `69`.
- **Cannot start before:** Step `P02-S0001` (`P-SYS-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.6` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-UTL-006`); matrix row `83`
- **Source file:** `logger.py`
- **Source responsibility:** Provide import-safe bound logger access, thread-safe lazy default activation, explicit override configuration and synchronization, source-aware human rendering, compressed rotation, color, lifecycle, and specialized routing.
- **Source key exports:** `BoundLogger`, `logger`, `get_logger`, `configure_logging`, `flush_logging`, `shutdown_logging`, `RedactingFilter`, `StructuredFormatter`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-UTL-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0003` [ ] `FR-UTL-016` - Define immutable denylist-first redaction policy with narrow reviewed field-path allowlists.

- **Execution domain:** `Utils`.
- **Execution position:** `3` of `69`.
- **Cannot start before:** Step `P02-S0002` (`P-UTL-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.6 `security/` — Shared Payload Redaction > Functional requirements`` (line 344); matrix row `69`.
- **Source responsibility:** Define immutable denylist-first redaction policy with narrow reviewed field-path allowlists.
- **Source class / function / method:** `RedactionPolicy`
- **Source side effects:** None
- **Source raises:** `ValidationError`: malformed policy definition
- **Source usage / test:** **Usage:** `tests/utils/usage/06_security.py::example_redaction()`<br>**Unit:** `tests/utils/unit/test_redaction.py::test_redaction_policy_is_immutable()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0004` [ ] `FR-UTL-017` - Detect sensitive keys case-insensitively.

- **Execution domain:** `Utils`.
- **Execution position:** `4` of `69`.
- **Cannot start before:** Step `P02-S0003` (`FR-UTL-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.6 `security/` — Shared Payload Redaction > Functional requirements`` (line 345); matrix row `70`.
- **Source responsibility:** Detect sensitive keys case-insensitively.
- **Source class / function / method:** `is_sensitive_key`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/utils/usage/06_security.py::example_key_classification()`<br>**Unit:** `tests/utils/unit/test_redaction.py::test_is_sensitive_key_is_case_insensitive()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0005` [ ] `FR-UTL-018` - Redact bounded text without mutating input.

- **Execution domain:** `Utils`.
- **Execution position:** `5` of `69`.
- **Cannot start before:** Step `P02-S0004` (`FR-UTL-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.6 `security/` — Shared Payload Redaction > Functional requirements`` (line 346); matrix row `71`.
- **Source responsibility:** Redact bounded text without mutating input.
- **Source class / function / method:** `redact_text_value`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/utils/usage/06_security.py::example_redaction()`<br>**Unit:** `tests/utils/unit/test_redaction.py::test_redact_text_value_does_not_mutate_input()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0006` [ ] `FR-UTL-019` - Recursively redact a JSON-safe mapping without mutating input.

- **Execution domain:** `Utils`.
- **Execution position:** `6` of `69`.
- **Cannot start before:** Step `P02-S0005` (`FR-UTL-018`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.6 `security/` — Shared Payload Redaction > Functional requirements`` (line 347); matrix row `72`.
- **Source responsibility:** Recursively redact a JSON-safe mapping without mutating input.
- **Source class / function / method:** `redact_mapping_value`
- **Source side effects:** None
- **Source raises:** `ValidationError`: non-JSON-safe mapping
- **Source usage / test:** **Usage:** `tests/utils/usage/06_security.py::example_redaction()`<br>**Unit:** `tests/utils/unit/test_redaction.py::test_redact_mapping_value_is_recursive()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0007` [ ] `FR-UTL-020` - Return redacted paths and truncation diagnostics without secret values.

- **Execution domain:** `Utils`.
- **Execution position:** `7` of `69`.
- **Cannot start before:** Step `P02-S0006` (`FR-UTL-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.6` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.6 `security/` — Shared Payload Redaction > Functional requirements`` (line 348); matrix row `73`.
- **Source responsibility:** Return redacted paths and truncation diagnostics without secret values.
- **Source class / function / method:** `RedactionResult`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/utils/usage/06_security.py::example_redaction()`<br>**Unit:** `tests/utils/unit/test_redaction.py::test_redaction_result_omits_secret_values()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-020`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0008` [ ] `P-UTL-007` - settings feature/component (provisional)

- **Execution domain:** `Utils`.
- **Execution position:** `8` of `69`.
- **Cannot start before:** Step `P02-S0007` (`FR-UTL-020`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.7` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-UTL-007`); matrix row `84`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-UTL-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0009` [ ] `FR-UTL-023` - Load explicit values and centralized .env/process settings in documented precedence order only when called.

- **Execution domain:** `Utils`.
- **Execution position:** `9` of `69`.
- **Cannot start before:** Step `P02-S0008` (`P-UTL-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.7` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.7 `settings/` — Runtime Settings > Functional requirements`` (line 371); matrix row `74`.
- **Source responsibility:** Load explicit values and centralized `.env`/process settings in documented precedence order only when called.
- **Source class / function / method:** `AppSettings`, `load_settings`
- **Source side effects:** Settings read
- **Source raises:** `ConfigurationError`: unsupported or invalid runtime value
- **Source usage / test:** **Usage:** `tests/utils/usage/07_settings.py::example_load_active_configuration()`<br>**Unit:** `tests/utils/unit/test_loader.py::test_load_settings_precedence_order()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-023`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0010` [ ] `FR-UTL-024` - Reject unknown, incompatible, or unsafe deployment/runtime values without partial mutation.

- **Execution domain:** `Utils`.
- **Execution position:** `10` of `69`.
- **Cannot start before:** Step `P02-S0009` (`FR-UTL-023`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` module `4.7` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 4. Module and Requirement Specifications > 4.7 `settings/` — Runtime Settings > Functional requirements`` (line 372); matrix row `75`.
- **Source responsibility:** Reject unknown, incompatible, or unsafe deployment/runtime values without partial mutation.
- **Source class / function / method:** Settings-model validation
- **Source side effects:** None
- **Source raises:** `ConfigurationError`: unknown, incompatible, or unsafe value
- **Source usage / test:** **Usage:** `tests/utils/usage/07_settings.py::example_environment_constraints()`, `example_validate_settings()`<br>**Unit:** `tests/utils/unit/test_models.py::test_settings_reject_unknown_value_without_mutation()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-UTL-024`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0011` [ ] `WF-UTL-002` - Shared Settings Bootstrap

- **Execution domain:** `Utils`.
- **Execution position:** `11` of `69`.
- **Cannot start before:** Step `P02-S0010` (`FR-UTL-024`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 3. Workflows`` (line 169); matrix row `85`.
- **Source scope:** Cross-domain
- **Source workflow:** Shared settings bootstrap
- **Source input boundary:** Explicit mapping and environment
- **Source final outcome:** Immutable validated `RuntimeSettings`
- **Source requirement sequence:** `FR-UTL-022` through `FR-UTL-025`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-UTL-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0012` [ ] `WF-UTL-003` - Audit-Event Construction

- **Execution domain:** `Utils`.
- **Execution position:** `12` of `69`.
- **Cannot start before:** Step `P02-S0011` (`WF-UTL-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 3. Workflows`` (line 170); matrix row `86`.
- **Source scope:** Cross-domain
- **Source workflow:** Audit-event construction
- **Source input boundary:** Domain-owned action facts and trace context
- **Source final outcome:** Valid redacted `AuditEvent v1` ready for Data persistence
- **Source requirement sequence:** `FR-UTL-002`, `FR-UTL-003`, `FR-UTL-007`, `FR-UTL-008`, `FR-UTL-010`, `FR-UTL-011`, `FR-UTL-013` through `FR-UTL-021`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-UTL-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0013` [ ] `NFR-UTL-001` - Boundary

- **Execution domain:** `Utils`.
- **Execution position:** `13` of `69`.
- **Cannot start before:** Step `P02-S0012` (`WF-UTL-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 495); matrix row `76`.
- **Source type:** Boundary
- **Source responsibility:** Other packages import only documented package or feature exports; no internal imports, aliases, or fallbacks.
- **Source verification:** Dependency tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-001`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0014` [ ] `NFR-UTL-002` - Security

- **Execution domain:** `Utils`.
- **Execution position:** `14` of `69`.
- **Cannot start before:** Step `P02-S0013` (`NFR-UTL-001`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 496); matrix row `77`.
- **Source type:** Security
- **Source responsibility:** Redaction occurs before logs, errors, audit payloads, or returned diagnostics; canonical serialization remains pure.
- **Source verification:** Secret-leak tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0015` [ ] `NFR-UTL-003` - Import safety

- **Execution domain:** `Utils`.
- **Execution position:** `15` of `69`.
- **Cannot start before:** Step `P02-S0014` (`NFR-UTL-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 497); matrix row `78`.
- **Source type:** Import safety
- **Source responsibility:** Imports perform no configuration, environment/file read, filesystem write, network call, handler registration, or client initialization.
- **Source verification:** Subprocess import tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0016` [ ] `NFR-UTL-004` - Determinism

- **Execution domain:** `Utils`.
- **Execution position:** `16` of `69`.
- **Cannot start before:** Step `P02-S0015` (`NFR-UTL-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 498); matrix row `79`.
- **Source type:** Determinism
- **Source responsibility:** Serialization, time calculations, validation, and stable-ID derivation are deterministic with explicit clock/entropy inputs.
- **Source verification:** Replay tests
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0017` [ ] `NFR-UTL-005` - Maintainability

- **Execution domain:** `Utils`.
- **Execution position:** `17` of `69`.
- **Cannot start before:** Step `P02-S0016` (`NFR-UTL-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 499); matrix row `80`.
- **Source type:** Maintainability
- **Source responsibility:** Public signatures are typed and documented; files have one focused responsibility.
- **Source verification:** Ruff, mypy, and documentation review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0018` [ ] `NFR-UTL-006` - Testing

- **Execution domain:** `Utils`.
- **Execution position:** `18` of `69`.
- **Cannot start before:** Step `P02-S0017` (`NFR-UTL-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 500); matrix row `81`.
- **Source type:** Testing
- **Source responsibility:** Every requirement has a usage example and targeted unit test; collaborative workflows have integration tests; coverage is at least 80%.
- **Source verification:** Traceability and coverage audit
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0019` [ ] `NFR-UTL-007` - Persistence

- **Execution domain:** `Utils`.
- **Execution position:** `19` of `69`.
- **Cannot start before:** Step `P02-S0018` (`NFR-UTL-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Utils` quality verification after its delivery and capability-acceptance steps.
- **Delivery type:** Quality and constraint verification.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/utils/README.md` - ``Utils > 5. Package-Wide Requirements and Shared Configuration > 5.1 Normative implementation policy`` (line 501); matrix row `82`.
- **Source type:** Persistence
- **Source responsibility:** Utils owns no durable business state or migration definition.
- **Source verification:** Ownership review
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `NFR-UTL-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Brokers

Implement `Brokers` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P02-S0020` [ ] `P-BRK-008` - yahoo feature/component (provisional)

- **Execution domain:** `Brokers`.
- **Execution position:** `20` of `69`.
- **Cannot start before:** Step `P02-S0019` (`NFR-UTL-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.7` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-BRK-008`); matrix row `218`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-BRK-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0021` [ ] `FR-BRK-130` - yahoo/transport.py

- **Execution domain:** `Brokers`.
- **Execution position:** `21` of `69`.
- **Cannot start before:** Step `P02-S0020` (`P-BRK-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1337); matrix row `215`.
- **Source assigned file:** `yahoo/transport.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-130`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0022` [ ] `FR-BRK-131` - yahoo/mapping.py

- **Execution domain:** `Brokers`.
- **Execution position:** `22` of `69`.
- **Cannot start before:** Step `P02-S0021` (`FR-BRK-130`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1338); matrix row `216`.
- **Source assigned file:** `yahoo/mapping.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-131`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0023` [ ] `FR-BRK-132` - yahoo/__init__.py

- **Execution domain:** `Brokers`.
- **Execution position:** `23` of `69`.
- **Cannot start before:** Step `P02-S0022` (`FR-BRK-131`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1339); matrix row `217`.
- **Source assigned file:** `yahoo/__init__.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-132`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0024` [ ] `FR-BRK-108` - expose genuine bounded Yahoo historical bars for research/development use, report production/live availability as unavailable, attach explic...

- **Execution domain:** `Brokers`.
- **Execution position:** `24` of `69`.
- **Cannot start before:** Step `P02-S0023` (`FR-BRK-132`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `adapter.py` — Canonical Yahoo Adapter`` (line 1252); matrix row `214`.
- **Source responsibility:** The system shall expose genuine bounded Yahoo historical bars for research/development use, report production/live availability as unavailable, attach explicit provider provenance, and return deterministic unsupported for ticks, quotes, account, subscriptions, calculations, and mutations rather than generating substitutes. `connect()` verifies the session using the caller's configured `probe_symbol` when present (never a hidden default symbol) and otherwise verifies transport/session setup only.
- **Source class / function / method:** `class YahooBrokerAdapter(BrokerAdapter)`
- **Source side effects:** External API call; local session mutation
- **Source raises:** `asyncio.CancelledError`: caller cancels; operational failures are canonical results.
- **Source usage / test:** **Usage:** `tests/brokers/usage/07_yahoo.py` (standalone script, run via `python`)<br>**Unit:** `tests/brokers/unit/test_yahoo_adapter.py::test_adapter_connect_with_probe_symbol_verifies_via_transport()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-108`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0025` [ ] `CAP-BRK-005` - Symbols/metadata

- **Execution domain:** `Brokers`.
- **Execution position:** `25` of `69`.
- **Cannot start before:** Step `P02-S0024` (`FR-BRK-108`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 520); matrix row `212`.
- **Source final destination:** FR-BRK-019, 058–062 and provider adapters
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0026` [ ] `CAP-BRK-016` - Yahoo historical bars

- **Execution domain:** `Brokers`.
- **Execution position:** `26` of `69`.
- **Cannot start before:** Step `P02-S0025` (`CAP-BRK-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 531); matrix row `213`.
- **Source final destination:** `yahoo/`; FR-BRK-108
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - Data

Implement `Data` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P02-S0027` [ ] `P-DATA-002` - storage feature/component (provisional)

- **Execution domain:** `Data`.
- **Execution position:** `27` of `69`.
- **Cannot start before:** Step `P02-S0026` (`CAP-BRK-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` module `4.2` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-DATA-002`); matrix row `334`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-DATA-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0028` [ ] `P-DATA-003` - sources feature/component (provisional)

- **Execution domain:** `Data`.
- **Execution position:** `28` of `69`.
- **Cannot start before:** Step `P02-S0027` (`P-DATA-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` module `4.3` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-DATA-003`); matrix row `335`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-DATA-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0029` [ ] `P-DATA-005` - processing feature/component (provisional)

- **Execution domain:** `Data`.
- **Execution position:** `29` of `69`.
- **Cannot start before:** Step `P02-S0028` (`P-DATA-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-DATA-005`); matrix row `336`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-DATA-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0030` [ ] `FR-DATA-014` - Execute a bounded caller-owned statement plan in one short-lived SQLite transaction, return normalized results without a connection/session, and roll back at...

- **Execution domain:** `Data`.
- **Execution position:** `30` of `69`.
- **Cannot start before:** Step `P02-S0029` (`P-DATA-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `database.py`, `locking.py`, and `migrations.py``` (line 797); matrix row `315`.
- **Source responsibility:** Execute a bounded caller-owned statement plan in one short-lived SQLite transaction, return normalized results without a connection/session, and roll back atomically on failure.
- **Source class / function / method:** `execute_transaction(request: TransactionRequest) -> TransactionResult`
- **Source side effects:** Persistence write
- **Source raises:** `DataError[DB_CONNECTION_ERROR|DATABASE_ERROR|DB_WRITE_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_014_transaction()`<br>**Unit:** `tests/data/unit/test_database.py::test_execute_transaction_rolls_back_atomically()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0031` [ ] `FR-DATA-015` - Validate ownership/order/checksums, acquire the shared lock, and execute domain-owned migration definitions exactly once while preserving an immutable ledger.

- **Execution domain:** `Data`.
- **Execution position:** `31` of `69`.
- **Cannot start before:** Step `P02-S0030` (`FR-DATA-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `database.py`, `locking.py`, and `migrations.py``` (line 798); matrix row `316`.
- **Source responsibility:** Validate ownership/order/checksums, acquire the shared lock, and execute domain-owned migration definitions exactly once while preserving an immutable ledger.
- **Source class / function / method:** `run_domain_migrations(request: MigrationRequest) -> MigrationResult`
- **Source side effects:** Persistence write
- **Source raises:** `DataError[SCHEMA_MIGRATION_FAILED|CONCURRENT_WRITE_LOCKED]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_015_migration()`<br>**Unit:** `tests/data/unit/test_migrations.py::test_run_domain_migrations_rejects_modified_applied_step()`<br>**Evidence:** `app/services/data/storage/migrations.py:246`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0032` [ ] `FR-DATA-017` - Load CSV/Parquet plus manifest only from an approved root, verify hash/schema/normalization metadata, normalize records, and reject corruption without hidden...

- **Execution domain:** `Data`.
- **Execution position:** `32` of `69`.
- **Cannot start before:** Step `P02-S0031` (`FR-DATA-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `datasets.py`, `cache.py`, and `audit.py``` (line 805); matrix row `317`.
- **Source responsibility:** Load CSV/Parquet plus manifest only from an approved root, verify hash/schema/normalization metadata, normalize records, and reject corruption without hidden migration.
- **Source class / function / method:** `load_dataset(request: DatasetLoadRequest) -> MarketDataset`
- **Source side effects:** Read-only
- **Source raises:** `DataError[PERMISSION_DENIED|FILE_CORRUPTED|DATA_QUALITY_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_017_load_dataset()`<br>**Unit:** `tests/data/unit/test_datasets.py::test_load_dataset_rejects_hash_mismatch()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-017`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0033` [ ] `FR-DATA-018` - Validate license/quality/path, lock the target, write artifact and manifest through a temporary file, and atomically commit or quarantine failure.

- **Execution domain:** `Data`.
- **Execution position:** `33` of `69`.
- **Cannot start before:** Step `P02-S0032` (`FR-DATA-017`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `datasets.py`, `cache.py`, and `audit.py``` (line 806); matrix row `318`.
- **Source responsibility:** Validate license/quality/path, lock the target, write artifact and manifest through a temporary file, and atomically commit or quarantine failure.
- **Source class / function / method:** `save_dataset(request: DatasetSaveRequest) -> StorageManifest`
- **Source side effects:** Persistence write
- **Source raises:** `DataError[PERMISSION_DENIED|CONCURRENT_WRITE_LOCKED|DATA_QUALITY_FAILED|DB_WRITE_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_018_save_dataset()`<br>**Unit:** `tests/data/unit/test_datasets.py::test_save_dataset_commits_artifact_and_manifest_atomically()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-018`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0034` [ ] `FR-DATA-019` - Return a cache entry only when request dimensions, schema/normalization, source revision/raw hash, and stale policy match; stale data is never silent.

- **Execution domain:** `Data`.
- **Execution position:** `34` of `69`.
- **Cannot start before:** Step `P02-S0033` (`FR-DATA-018`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `datasets.py`, `cache.py`, and `audit.py``` (line 807); matrix row `319`.
- **Source responsibility:** Return a cache entry only when request dimensions, schema/normalization, source revision/raw hash, and stale policy match; stale data is never silent.
- **Source class / function / method:** `get_cache_entry(request: CacheReadRequest) -> CacheEntry | None`
- **Source side effects:** Read-only
- **Source raises:** `DataError[DATABASE_ERROR]`; stale policy may yield warning metadata or miss
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_019_read_cache()`<br>**Unit:** `tests/data/unit/test_cache.py::test_cache_invalidates_on_source_revision()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-019`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0035` [ ] `FR-DATA-020` - Write a bounded cache entry with complete identity/TTL metadata and surface an optional cache-write failure without corrupting a successful retrieval result.

- **Execution domain:** `Data`.
- **Execution position:** `35` of `69`.
- **Cannot start before:** Step `P02-S0034` (`FR-DATA-019`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `datasets.py`, `cache.py`, and `audit.py``` (line 808); matrix row `320`.
- **Source responsibility:** Write a bounded cache entry with complete identity/TTL metadata and surface an optional cache-write failure without corrupting a successful retrieval result.
- **Source class / function / method:** `put_cache_entry(request: CacheWriteRequest) -> CacheWriteResult`
- **Source side effects:** Persistence write
- **Source raises:** `DataError[DB_WRITE_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_020_write_cache()`<br>**Unit:** `tests/data/unit/test_cache.py::test_cache_write_failure_is_not_silent()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-020`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0036` [ ] `FR-DATA-021` - Persist a redacted AuditEvent v1 idempotently with trace identifiers and surface every persistence failure.

- **Execution domain:** `Data`.
- **Execution position:** `36` of `69`.
- **Cannot start before:** Step `P02-S0035` (`FR-DATA-020`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `datasets.py`, `cache.py`, and `audit.py``` (line 809); matrix row `321`.
- **Source responsibility:** Persist a redacted `AuditEvent v1` idempotently with trace identifiers and surface every persistence failure.
- **Source class / function / method:** `persist_audit_event(event: AuditEvent) -> AuditPersistenceResult`
- **Source side effects:** Persistence write
- **Source raises:** `DataError[DATABASE_ERROR|DB_WRITE_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_021_persist_audit()`<br>**Unit:** `tests/data/unit/test_audit_storage.py::test_persist_audit_event_is_idempotent()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-021`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0037` [ ] `FR-DATA-077` - Authorize and execute a bounded, deterministically ordered audit query without exposing storage handles or unredacted payloads.

- **Execution domain:** `Data`.
- **Execution position:** `37` of `69`.
- **Cannot start before:** Step `P02-S0036` (`FR-DATA-021`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `datasets.py`, `cache.py`, and `audit.py``` (line 810); matrix row `328`.
- **Source responsibility:** Authorize and execute a bounded, deterministically ordered audit query without exposing storage handles or unredacted payloads.
- **Source class / function / method:** `query_audit_events(request: AuditEventQuery, auth_context: AuthContext) -> AuditEventPage`
- **Source side effects:** Read-only
- **Source raises:** `DataError[PERMISSION_DENIED|INVALID_INPUT|LIMIT_EXCEEDED|DATABASE_ERROR]`
- **Source usage / test:** **Usage:** `tests/data/usage/02_storage.py::example_fr_data_077_query_audit()`<br>**Unit:** `tests/data/unit/test_audit_storage.py::test_query_is_authorized_bounded_and_cursor_ordered()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-077`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0038` [ ] `FR-DATA-022` - Require every adapter to perform one bounded read and return provider-neutral raw records plus source metadata without broker mutation.

- **Execution domain:** `Data`.
- **Execution position:** `38` of `69`.
- **Cannot start before:** Step `P02-S0037` (`FR-DATA-077`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public source API`` (line 863); matrix row `322`.
- **Source responsibility:** Require every adapter to perform one bounded read and return provider-neutral raw records plus source metadata without broker mutation.
- **Source class / function / method:** `MarketDataSource.fetch(request: SourceReadRequest) -> RawSourceBatch`
- **Source side effects:** External API call or Read-only
- **Source raises:** `DataError[SOURCE_UNAVAILABLE|NETWORK_ERROR|TIMEOUT]`
- **Source usage / test:** **Usage:** `tests/data/usage/03_sources.py::example_fr_data_022_bounded_fetch()`<br>**Unit:** `tests/data/unit/test_source_protocol.py::test_source_fetch_contract_is_read_only()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-022`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0039` [ ] `FR-DATA-024` - Require normalized symbol metadata with provenance and explicit missing fields rather than optimistic defaults.

- **Execution domain:** `Data`.
- **Execution position:** `39` of `69`.
- **Cannot start before:** Step `P02-S0038` (`FR-DATA-022`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public source API`` (line 865); matrix row `323`.
- **Source responsibility:** Require normalized symbol metadata with provenance and explicit missing fields rather than optimistic defaults.
- **Source class / function / method:** `MarketDataSource.get_symbol_metadata(request: SymbolMetadataRequest) -> SymbolMetadata`
- **Source side effects:** External API call or Read-only
- **Source raises:** `DataError[DATA_NOT_FOUND|MISSING_ASSET_METADATA]`
- **Source usage / test:** **Usage:** `tests/data/usage/03_sources.py::example_fr_data_024_symbol_metadata()`<br>**Unit:** `tests/data/unit/test_source_protocol.py::test_symbol_metadata_does_not_invent_fields()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-024`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0040` [ ] `FR-DATA-025` - Register a source descriptor and lazy factory atomically, reject duplicate/conflicting declarations, and perform no I/O during registration/import.

- **Execution domain:** `Data`.
- **Execution position:** `40` of `69`.
- **Cannot start before:** Step `P02-S0039` (`FR-DATA-024`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public source API`` (line 866); matrix row `324`.
- **Source responsibility:** Register a source descriptor and lazy factory atomically, reject duplicate/conflicting declarations, and perform no I/O during registration/import.
- **Source class / function / method:** `register_source(descriptor: SourceDescriptor, factory: SourceFactory) -> None`
- **Source side effects:** Local state mutation
- **Source raises:** `DataError[VALIDATION_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/03_sources.py::example_fr_data_025_lazy_registration()`<br>**Unit:** `tests/data/unit/test_source_registry.py::test_registry_is_lazy_and_duplicate_safe()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-025`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0041` [ ] `FR-DATA-027` - Change readiness only from a complete authenticated evidence package, record an audit event, and permit immediate reversible demotion.

- **Execution domain:** `Data`.
- **Execution position:** `41` of `69`.
- **Cannot start before:** Step `P02-S0040` (`FR-DATA-025`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public source API`` (line 868); matrix row `325`.
- **Source responsibility:** Change readiness only from a complete authenticated evidence package, record an audit event, and permit immediate reversible demotion.
- **Source class / function / method:** `promote_source(request: SourcePromotionRequest, auth: AuthContext) -> SourceDescriptor`
- **Source side effects:** Persistence write; Event publication
- **Source raises:** `DataError[PERMISSION_DENIED|VALIDATION_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/03_sources.py::example_fr_data_027_source_promotion()`<br>**Unit:** `tests/data/unit/test_source_policy.py::test_promotion_requires_all_evidence()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-027`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0042` [ ] `FR-DATA-080` - Align a private tabular market-data copy to an aware UTC datetime field/index without mutating caller input.

- **Execution domain:** `Data`.
- **Execution position:** `42` of `69`.
- **Cannot start before:** Step `P02-S0041` (`FR-DATA-027`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Private tabular and OHLC implementation`` (line 988); matrix row `329`.
- **Source responsibility:** Align a private tabular market-data copy to an aware UTC datetime field/index without mutating caller input.
- **Source class / function / method:** `align_dataframe_datetime`
- **Source side effects:** None
- **Source raises:** `DataError[VALIDATION_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/05_processing.py::example_fr_data_080_align_private_tabular_copy()`<br>**Unit:** `tests/data/unit/test_tabular.py::test_align_dataframe_datetime_success()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-080`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0043` [ ] `FR-DATA-081` - Convert bar rows or private DataFrames to deterministic JSON-safe records with canonical UTC timestamps.

- **Execution domain:** `Data`.
- **Execution position:** `43` of `69`.
- **Cannot start before:** Step `P02-S0042` (`FR-DATA-080`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Private tabular and OHLC implementation`` (line 989); matrix row `330`.
- **Source responsibility:** Convert bar rows or private DataFrames to deterministic JSON-safe records with canonical UTC timestamps.
- **Source class / function / method:** `bars_to_records`, `serialize_dataframe_records`
- **Source side effects:** None
- **Source raises:** `DataError[VALIDATION_FAILED|PRECISION_MISMATCH]`
- **Source usage / test:** **Usage:** `tests/data/usage/05_processing.py::example_fr_data_081_json_safe_records()`<br>**Unit:** `tests/data/unit/test_tabular.py::test_serialize_dataframe_rejects_unsafe_values()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-081`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0044` [ ] `FR-DATA-082` - Compare aligned private DataFrames using explicit finite tolerance and bounded diagnostics.

- **Execution domain:** `Data`.
- **Execution position:** `44` of `69`.
- **Cannot start before:** Step `P02-S0043` (`FR-DATA-081`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Private tabular and OHLC implementation`` (line 990); matrix row `331`.
- **Source responsibility:** Compare aligned private DataFrames using explicit finite tolerance and bounded diagnostics.
- **Source class / function / method:** `compare_dataframes`
- **Source side effects:** None
- **Source raises:** `DataError[VALIDATION_FAILED|LIMIT_EXCEEDED|PRECISION_MISMATCH]`
- **Source usage / test:** **Usage:** `tests/data/usage/05_processing.py::example_fr_data_082_compare_dataframes()`<br>**Unit:** `tests/data/unit/test_tabular.py::test_compare_dataframes_mismatch()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-082`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0045` [ ] `FR-DATA-083` - Compare OHLC or OHLCV columns only after schema and alignment validation.

- **Execution domain:** `Data`.
- **Execution position:** `45` of `69`.
- **Cannot start before:** Step `P02-S0044` (`FR-DATA-082`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Private tabular and OHLC implementation`` (line 991); matrix row `332`.
- **Source responsibility:** Compare OHLC or OHLCV columns only after schema and alignment validation.
- **Source class / function / method:** `compare_ohlc`, `compare_ohlcv`
- **Source side effects:** None
- **Source raises:** `DataError[VALIDATION_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/05_processing.py::example_fr_data_083_compare_ohlcv()`<br>**Unit:** `tests/data/unit/test_tabular.py::test_compare_ohlcv_success()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-083`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0046` [ ] `FR-DATA-084` - Keep ingestion chunking private to the bounded backfill workflow; expose no generic sequence helper.

- **Execution domain:** `Data`.
- **Execution position:** `46` of `69`.
- **Cannot start before:** Step `P02-S0045` (`FR-DATA-083`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Private tabular and OHLC implementation`` (line 992); matrix row `333`.
- **Source responsibility:** Keep ingestion chunking private to the bounded backfill workflow; expose no generic sequence helper.
- **Source class / function / method:** `execute_backfill_chunk`
- **Source side effects:** Persistence write
- **Source raises:** Existing job errors
- **Source usage / test:** **Usage:** `tests/data/usage/06_update_jobs.py::example_fr_data_084_private_chunking_boundary()`<br>**Unit:** `tests/data/unit/test_backfill.py::test_backfill_key_is_canonical()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-084`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0047` [ ] `FR-DATA-037` - Backward-align multiple datasets using only values available by each target timestamp, preserving source availability metadata and failing atomically on look...

- **Execution domain:** `Data`.
- **Execution position:** `47` of `69`.
- **Cannot start before:** Step `P02-S0046` (`FR-DATA-084`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public processing API`` (line 999); matrix row `326`.
- **Source responsibility:** Backward-align multiple datasets using only values available by each target timestamp, preserving source availability metadata and failing atomically on lookahead.
- **Source class / function / method:** `align_datasets(datasets: Mapping[str, MarketDataset], target: Sequence[datetime]) -> Mapping[str, MarketDataset]`
- **Source side effects:** None
- **Source raises:** `DataError[VALIDATION_FAILED|DATA_QUALITY_FAILED]`
- **Source usage / test:** **Usage:** `tests/data/usage/05_processing.py::example_fr_data_037_no_lookahead_alignment()`<br>**Unit:** `tests/data/unit/test_transforms.py::test_align_datasets_prevents_lookahead()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-037`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0048` [ ] `FR-DATA-038` - Aggregate sorted canonical ticks into OHLCV bars with explicit timeframe and spread policy, rejecting disorder or ambiguous spread units.

- **Execution domain:** `Data`.
- **Execution position:** `48` of `69`.
- **Cannot start before:** Step `P02-S0047` (`FR-DATA-037`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Public processing API`` (line 1000); matrix row `327`.
- **Source responsibility:** Aggregate sorted canonical ticks into OHLCV bars with explicit timeframe and spread policy, rejecting disorder or ambiguous spread units.
- **Source class / function / method:** `aggregate_ticks(dataset: MarketDataset, timeframe: str, spread_policy: str) -> MarketDataset`
- **Source side effects:** None
- **Source raises:** `DataError[VALIDATION_FAILED|UNSUPPORTED_TIMEFRAME]`
- **Source usage / test:** **Usage:** `tests/data/usage/05_processing.py::example_fr_data_038_ticks_to_bars()`<br>**Unit:** `tests/data/unit/test_transforms.py::test_aggregate_ticks_rejects_disordered_input()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-DATA-038`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0049` [ ] `WF-DATA-002` - Cross-domain

- **Execution domain:** `Data`.
- **Execution position:** `49` of `69`.
- **Cannot start before:** Step `P02-S0048` (`FR-DATA-038`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 362); matrix row `337`.
- **Source scope:** Cross-domain
- **Source workflow:** Internal analytical data access
- **Source requirement sequence:** `FR-DATA-006 → 030 → 005`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0050` [ ] `WF-DATA-003` - Local Dataset Load and Save

- **Execution domain:** `Data`.
- **Execution position:** `50` of `69`.
- **Cannot start before:** Step `P02-S0049` (`WF-DATA-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 363); matrix row `338`.
- **Source scope:** Internal
- **Source workflow:** Local dataset load/save
- **Source requirement sequence:** `FR-DATA-016 → 017/018`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-003`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0051` [ ] `WF-DATA-004` - Resample, Align, and Aggregate

- **Execution domain:** `Data`.
- **Execution position:** `51` of `69`.
- **Cannot start before:** Step `P02-S0050` (`WF-DATA-003`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 364); matrix row `339`.
- **Source scope:** Internal
- **Source workflow:** Resample, align, and aggregate
- **Source requirement sequence:** `FR-DATA-036 → 037/038`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0052` [ ] `WF-DATA-005` - Cross-domain

- **Execution domain:** `Data`.
- **Execution position:** `52` of `69`.
- **Cannot start before:** Step `P02-S0051` (`WF-DATA-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 365); matrix row `340`.
- **Source scope:** Cross-domain
- **Source workflow:** Synthetic generation
- **Source requirement sequence:** `FR-DATA-039`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0053` [ ] `WF-DATA-009` - Cross-domain

- **Execution domain:** `Data`.
- **Execution position:** `53` of `69`.
- **Cannot start before:** Step `P02-S0052` (`WF-DATA-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 369); matrix row `341`.
- **Source scope:** Cross-domain
- **Source workflow:** Symbol discovery, metadata, availability
- **Source requirement sequence:** `FR-DATA-023/024 → 031/032/033`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0054` [ ] `WF-DATA-010` - Cross-domain

- **Execution domain:** `Data`.
- **Execution position:** `54` of `69`.
- **Cannot start before:** Step `P02-S0053` (`WF-DATA-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 370); matrix row `342`.
- **Source scope:** Cross-domain
- **Source workflow:** Current hours, sessions, and volume
- **Source requirement sequence:** `FR-DATA-034/035`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0055` [ ] `WF-DATA-011` - Source Readiness and Promotion

- **Execution domain:** `Data`.
- **Execution position:** `55` of `69`.
- **Cannot start before:** Step `P02-S0054` (`WF-DATA-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 3. Workflows > Workflow scope values`` (line 371); matrix row `343`.
- **Source scope:** Internal
- **Source workflow:** Source readiness and promotion
- **Source requirement sequence:** `FR-DATA-026 → 027`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-DATA-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0056` [ ] `CAP-DATA-007` - Local CSV/Parquet and atomic storage

- **Execution domain:** `Data`.
- **Execution position:** `56` of `69`.
- **Cannot start before:** Step `P02-S0055` (`WF-DATA-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 317); matrix row `312`.
- **Source capability:** `CAP-DATA-007` Local CSV/Parquet and atomic storage
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0057` [ ] `CAP-DATA-015` - License/fallback/rate/breaker/source safety

- **Execution domain:** `Data`.
- **Execution position:** `57` of `69`.
- **Cannot start before:** Step `P02-S0056` (`CAP-DATA-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 325); matrix row `313`.
- **Source capability:** `CAP-DATA-015` License/fallback/rate/breaker/source safety
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-015`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0058` [ ] `CAP-DATA-016` - Symbol discovery and metadata

- **Execution domain:** `Data`.
- **Execution position:** `58` of `69`.
- **Cannot start before:** Step `P02-S0057` (`CAP-DATA-015`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 326); matrix row `314`.
- **Source capability:** `CAP-DATA-016` Symbol discovery and metadata
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 5 - Strategy

Implement `Strategy` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P02-S0059` [ ] `P-STR-002` - diagnostics feature/component (provisional)

- **Execution domain:** `Strategy`.
- **Execution position:** `59` of `69`.
- **Cannot start before:** Step `P02-S0058` (`CAP-DATA-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` module `4.2` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Appendix P — Provisional Component Requirements`` (`P-STR-002`); matrix row `469`
**Specification control:** Promoted roadmap requirement (authoritative): implement the named component seam and the behavior in the authoritative source, fixing the public seam from first implementation and adding depth behind it in later phases; if a normative contract or acceptance condition is still absent, stop for owner resolution.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-STR-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0060` [ ] `WF-STR-006` - Export Structured Diagnostics

- **Execution domain:** `Strategy`.
- **Execution position:** `60` of `69`.
- **Cannot start before:** Step `P02-S0059` (`P-STR-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Strategy` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/strategy/README.md` - ``Strategy > 3. Workflows > Status values`` (line 301); matrix row `470`.
- **Source scope:** Cross-domain
- **Source workflow:** Export structured diagnostics
- **Source requirement sequence:** `FR-STR-019`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-STR-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 6 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P02-S0061` [ ] `CAP-SIM-009` - Data authority and quality gate

- **Execution domain:** `Simulation`.
- **Execution position:** `61` of `69`.
- **Cannot start before:** Step `P02-S0060` (`WF-STR-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 456); matrix row `723`.
- **Source final destination:** `validation/`: `FR-SIM-002`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 7 - UI/API

Implement `UI/API` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P02-S0062` [ ] `FR-API-009` - Hash new non-empty passwords and verify stored hashes within UI/API, then authenticate valid active and verified credentials, update last-login evidence, rat...

- **Execution domain:** `UI/API`.
- **Execution position:** `62` of `69`.
- **Cannot start before:** Step `P02-S0061` (`CAP-SIM-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 4. Module and Requirement Specifications > 4.2 `identity/` — Authentication and authorization`` (line 477); matrix row `1193`.
- **Source responsibility:** Hash new non-empty passwords and verify stored hashes within UI/API, then authenticate valid active and verified credentials, update last-login evidence, rate-limit failures, and never log secrets. No silent hashing-algorithm fallback is allowed.
- **Source class / function / method:** `hash_password`, `verify_password`, `authenticate_user`
- **Source side effects:** Read-only; persistence write
- **Source raises:** `AuthenticationError`: credentials invalid; `AccountStateError`: inactive/unverified; `DependencyUnavailableError`: approved hashing implementation unavailable
- **Source usage / test:** **Usage:** `tests/api/usage/test_usage_identity.py::test_usage_authenticate_user()`<br>**Unit:** `tests/api/unit/test_passwords.py::test_hash_and_verify_remain_api_owned()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-API-009`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0063` [ ] `FR-API-010` - Replace the user's prior active session and create one configurable-expiry opaque server-side session in the UI/API-owned store; return it through a secure H...

- **Execution domain:** `UI/API`.
- **Execution position:** `63` of `69`.
- **Cannot start before:** Step `P02-S0062` (`FR-API-009`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 4. Module and Requirement Specifications > 4.2 `identity/` — Authentication and authorization`` (line 478); matrix row `1194`.
- **Source responsibility:** Replace the user's prior active session and create one configurable-expiry opaque server-side session in the UI/API-owned store; return it through a secure HttpOnly SameSite cookie with CSRF validation for browser state changes.
- **Source class / function / method:** `create_session(user: AuthenticatedUser) -> SessionCredential`
- **Source side effects:** Persistence write
- **Source raises:** `DependencyUnavailableError`: session state unavailable
- **Source usage / test:** **Usage:** `tests/api/usage/test_usage_identity.py::test_usage_create_session()`<br>**Unit:** `tests/api/unit/test_sessions.py::test_new_login_revokes_old_session()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-API-010`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0064` [ ] `FR-API-011` - Validate standard session credentials, expiry, revocation, and current account status and delete expired sessions.

- **Execution domain:** `UI/API`.
- **Execution position:** `64` of `69`.
- **Cannot start before:** Step `P02-S0063` (`FR-API-010`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 4. Module and Requirement Specifications > 4.2 `identity/` — Authentication and authorization`` (line 479); matrix row `1195`.
- **Source responsibility:** Validate standard session credentials, expiry, revocation, and current account status and delete expired sessions.
- **Source class / function / method:** `validate_session(credential: SessionCredential) -> AuthenticatedPrincipal`
- **Source side effects:** Read-only; conditional persistence write
- **Source raises:** `AuthenticationError`: missing, malformed, expired, revoked, or inactive
- **Source usage / test:** **Usage:** `tests/api/usage/test_usage_identity.py::test_usage_validate_session()`<br>**Unit:** `tests/api/unit/test_sessions.py::test_deactivated_user_token_rejected()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-API-011`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0065` [ ] `FR-API-012` - Revoke the caller's persisted session on logout; repeated logout is deterministic.

- **Execution domain:** `UI/API`.
- **Execution position:** `65` of `69`.
- **Cannot start before:** Step `P02-S0064` (`FR-API-011`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.2` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 4. Module and Requirement Specifications > 4.2 `identity/` — Authentication and authorization`` (line 480); matrix row `1196`.
- **Source responsibility:** Revoke the caller's persisted session on logout; repeated logout is deterministic.
- **Source class / function / method:** `revoke_session(credential: SessionCredential) -> None`
- **Source side effects:** Persistence write
- **Source raises:** `DependencyUnavailableError`: revocation cannot be confirmed
- **Source usage / test:** **Usage:** `tests/api/usage/test_usage_identity.py::test_usage_revoke_session()`<br>**Unit:** `tests/api/unit/test_sessions.py::test_logout_is_idempotent()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-API-012`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0066` [ ] `FR-API-016` - Redact secrets before any log/trace/metric emission and log only allowlisted method, route, identifiers, status, duration, and error code.

- **Execution domain:** `UI/API`.
- **Execution position:** `66` of `69`.
- **Cannot start before:** Step `P02-S0065` (`FR-API-012`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` module `4.3` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 4. Module and Requirement Specifications > 4.3 `middleware/` — Request security and context`` (line 512); matrix row `1197`.
- **Source responsibility:** Redact secrets before any log/trace/metric emission and log only allowlisted method, route, identifiers, status, duration, and error code.
- **Source class / function / method:** `SecretRedactionMiddleware`
- **Source side effects:** Log publication
- **Source raises:** `TelemetryError`: safe telemetry cannot be emitted where required
- **Source usage / test:** **Usage:** `tests/api/usage/test_usage_middleware.py::test_usage_redacted_request()`<br>**Unit:** `tests/api/unit/test_redaction.py::test_tokens_never_logged()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-API-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0067` [ ] `WF-API-016` - Cross-domain

- **Execution domain:** `UI/API`.
- **Execution position:** `67` of `69`.
- **Cannot start before:** Step `P02-S0066` (`FR-API-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 3. Workflows > Workflow manifest`` (line 368); matrix row `1198`.
- **Source scope:** Cross-domain
- **Source workflow:** Frontend stream consumption
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-API-016`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0068` [ ] `CAP-UI-008` - settings

- **Execution domain:** `UI/API`.
- **Execution position:** `68` of `69`.
- **Cannot start before:** Step `P02-S0067` (`WF-API-016`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 300); matrix row `1191`.
- **Source final destination:** `routes/settings.py`; `FR-API-023`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P02-S0069` [ ] `CAP-UI-009` - market data/prepared datasets

- **Execution domain:** `UI/API`.
- **Execution position:** `69` of `69`.
- **Cannot start before:** Step `P02-S0068` (`CAP-UI-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `UI/API` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/api/README.md` - ``UI/API > 2. Final Package Structure > Reconciliation coverage manifest`` (line 301); matrix row `1192`.
- **Source final destination:** `routes/data.py`; `FR-API-024`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-UI-009`.
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
- **Matrix phase:** `2`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (1):** `P-SYS-003`
- **Utils (18):** `FR-UTL-016`, `FR-UTL-017`, `FR-UTL-018`, `FR-UTL-019`, `FR-UTL-020`, `FR-UTL-023`, `FR-UTL-024`, `NFR-UTL-001`, `NFR-UTL-002`, `NFR-UTL-003`, `NFR-UTL-004`, `NFR-UTL-005`, `NFR-UTL-006`, `NFR-UTL-007`, `P-UTL-006`, `P-UTL-007`, `WF-UTL-002`, `WF-UTL-003`
- **Brokers (7):** `CAP-BRK-005`, `CAP-BRK-016`, `FR-BRK-108`, `FR-BRK-130`, `FR-BRK-131`, `FR-BRK-132`, `P-BRK-008`
- **Data (32):** `CAP-DATA-007`, `CAP-DATA-015`, `CAP-DATA-016`, `FR-DATA-014`, `FR-DATA-015`, `FR-DATA-017`, `FR-DATA-018`, `FR-DATA-019`, `FR-DATA-020`, `FR-DATA-021`, `FR-DATA-022`, `FR-DATA-024`, `FR-DATA-025`, `FR-DATA-027`, `FR-DATA-037`, `FR-DATA-038`, `FR-DATA-077`, `FR-DATA-080`, `FR-DATA-081`, `FR-DATA-082`, `FR-DATA-083`, `FR-DATA-084`, `P-DATA-002`, `P-DATA-003`, `P-DATA-005`, `WF-DATA-002`, `WF-DATA-003`, `WF-DATA-004`, `WF-DATA-005`, `WF-DATA-009`, `WF-DATA-010`, `WF-DATA-011`
- **Indicators (0):** None.
- **Strategy (2):** `P-STR-002`, `WF-STR-006`
- **Risk (0):** None.
- **Trading (0):** None.
- **Simulation (1):** `CAP-SIM-009`
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (8):** `CAP-UI-008`, `CAP-UI-009`, `FR-API-009`, `FR-API-010`, `FR-API-011`, `FR-API-012`, `FR-API-016`, `WF-API-016`

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
