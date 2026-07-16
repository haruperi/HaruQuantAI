# Phase 5 Implementation Plan - v1.5 - Execution robustness

> **Status:** Not started
> **Requirement count:** 23
> **Source of phase assignment:** `docs/dev/TRACEABILITY_MATRIX.md`
> **Release contract:** `docs/dev/AGILE_ROADMAP.md`, Phase 5
> **Completion evidence rule:** every checked item ends with implementation and test `path:line` evidence.

## 1. Purpose and authority

This document is the execution ledger for Phase 5. It translates the roadmap commitment and assigned traceability IDs into dependency-ordered work suitable for implementation by junior developers under review. It does not replace `AGENTS.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, or a domain README. Those sources alone remain authoritative for behavior and boundaries. This plan is only a delivery ledger recording sequence, status, evidence, and phase acceptance; it creates no product requirement or implementation rule.

If this plan conflicts with an authoritative source, stop, record the item as `Pending`, and obtain an owner decision. Do not resolve ambiguity by inventing a trading rule, risk limit, provider behavior, result, or compatibility surface.

## 2. Phase outcome

- **Version:** `v1.5`.
- **Theme:** Execution robustness.
- **Entry condition:** Phase 4 exit evidence is complete and accepted.
- **Definition of done:** every requirement in Section 8 is checked with evidence, all domain and cross-domain gates pass, the phase exit demonstration succeeds, and phase-close documentation reconciliation is complete.

### 2.1 Public-interface commitment

No breaking v1 seam change. Activate or harden operations already declared by stable ports; additive behavior requires compatibility tests.

### 2.2 Exit criteria

- **Functional:** Repeat an idempotent demo action and resolve an induced reconciliation discrepancy.
- **Integration:** The phase demo and every earlier demo pass only through public domain boundaries.
- **Coverage:** Changed code has targeted unit, integration, usage, and system evidence with at least 80% coverage.
- **Quality:** `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, and affected tests pass.
- **Safety:** No invented data, fills, identifiers, or performance; no secret leakage; broker mutations are limited to the explicit MT5 demo proof.
- **Release:** Tag v1.5 only after documented automated checks and the phase exit demo pass.

### 2.3 Phase risks

Retires minimal reconciliation; unknown outcomes remain fail-closed.

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
| Utils | 0 | Trace/redaction regression. |
| Brokers | 17 | Complete cTrader/Binance execution profiles and transport mapping. |
| Data | 1 | Refresh authority facts. |
| Indicators | 0 | No change. |
| Strategy | 0 | Supply paper/demo decisions. |
| Risk | 0 | Revalidate evidence/tokens. |
| Trading | 4 | Complete state projections, routing, retry guard, discrepancy handling, and richer reconciliation. |
| Simulation | 1 | Sim compatibility. |
| Analytics | 0 | Adapt richer factual records. |
| Optimization | 0 | No change. |
| Research | 0 | No change. |
| Portfolio | 0 | Consume factual execution outcomes. |
| UI/API | 0 | Expose idempotency/reconciliation incidents. |

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

#### Step `P05-S0001` [ ] `P-BRK-002` - runtime feature/component (provisional)

- **Execution domain:** `Brokers`.
- **Execution position:** `1` of `23`.
- **Cannot start before:** Phase entry gate.
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.2` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Standalone real-behavior usage scripts (run individually, not via pytest):`` (line 1449); matrix row `230`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-BRK-002`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0002` [ ] `P-BRK-005` - ctrader feature/component (provisional)

- **Execution domain:** `Brokers`.
- **Execution position:** `2` of `23`.
- **Cannot start before:** Step `P05-S0001` (`P-BRK-002`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.4` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Standalone real-behavior usage scripts (run individually, not via pytest):`` (line 1451); matrix row `231`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-BRK-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0003` [ ] `P-BRK-006` - binance feature/component (provisional)

- **Execution domain:** `Brokers`.
- **Execution position:** `3` of `23`.
- **Cannot start before:** Step `P05-S0002` (`P-BRK-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.5` component/package establishment before its functional behavior.
- **Delivery type:** Confirm component contract, then implement.
- **Classification:** T1 Core; size `M`; source status `Provisional`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Standalone real-behavior usage scripts (run individually, not via pytest):`` (line 1452); matrix row `232`.
- **Specification control:** Provisional planning item: implement only behavior explicitly specified by the referenced component and stop for owner resolution if a normative contract or acceptance condition is absent.
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `P-BRK-006`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0004` [ ] `FR-BRK-119` - ctrader/transport.py

- **Execution domain:** `Brokers`.
- **Execution position:** `4` of `23`.
- **Cannot start before:** Step `P05-S0003` (`P-BRK-006`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1326); matrix row `223`.
- **Source assigned file:** `ctrader/transport.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-119`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0005` [ ] `FR-BRK-120` - ctrader/mapping.py

- **Execution domain:** `Brokers`.
- **Execution position:** `5` of `23`.
- **Cannot start before:** Step `P05-S0004` (`FR-BRK-119`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1327); matrix row `224`.
- **Source assigned file:** `ctrader/mapping.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-120`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0006` [ ] `FR-BRK-121` - ctrader/__init__.py

- **Execution domain:** `Brokers`.
- **Execution position:** `6` of `23`.
- **Cannot start before:** Step `P05-S0005` (`FR-BRK-120`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1328); matrix row `225`.
- **Source assigned file:** `ctrader/__init__.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-121`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0007` [ ] `FR-BRK-122` - binance/profiles.py

- **Execution domain:** `Brokers`.
- **Execution position:** `7` of `23`.
- **Cannot start before:** Step `P05-S0006` (`FR-BRK-121`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1329); matrix row `226`.
- **Source assigned file:** `binance/profiles.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-122`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0008` [ ] `FR-BRK-123` - binance/transport.py

- **Execution domain:** `Brokers`.
- **Execution position:** `8` of `23`.
- **Cannot start before:** Step `P05-S0007` (`FR-BRK-122`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1330); matrix row `227`.
- **Source assigned file:** `binance/transport.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-123`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0009` [ ] `FR-BRK-124` - binance/mapping.py

- **Execution domain:** `Brokers`.
- **Execution position:** `9` of `23`.
- **Cannot start before:** Step `P05-S0008` (`FR-BRK-123`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1331); matrix row `228`.
- **Source assigned file:** `binance/mapping.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-124`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0010` [ ] `FR-BRK-125` - binance/__init__.py

- **Execution domain:** `Brokers`.
- **Execution position:** `10` of `23`.
- **Cannot start before:** Step `P05-S0009` (`FR-BRK-124`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` module `4.10` functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > 4.10 Private Helper and Export Requirements`` (line 1332); matrix row `229`.
- **Source assigned file:** `binance/__init__.py`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-125`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0011` [ ] `FR-BRK-115` - The runtime package initializer shall expose no public symbol and cause no provider import or state mutation.

- **Execution domain:** `Brokers`.
- **Execution position:** `11` of `23`.
- **Cannot start before:** Step `P05-S0010` (`FR-BRK-125`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Requirements`` (line 860); matrix row `222`.
- **Source responsibility:** The runtime package initializer shall expose no public symbol and cause no provider import or state mutation.
- **Source class / function / method:** `runtime.__init__`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/brokers/usage/02_runtime.py` (standalone script, run via `python`)<br>**Unit:** `tests/brokers/unit/test_import_boundaries.py::test_runtime_package_is_private()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-115`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0012` [ ] `FR-BRK-106` - expose genuine Binance Spot market data through the canonical adapter, keep the selected product profile immutable, and keep every Futures/a...

- **Execution domain:** `Brokers`.
- **Execution position:** `12` of `23`.
- **Cannot start before:** Step `P05-S0011` (`FR-BRK-115`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Configuration and Limits Manifest > `adapter.py` — Canonical Binance Adapter`` (line 1142); matrix row `221`.
- **Source responsibility:** The system shall expose genuine Binance Spot market data through the canonical adapter, keep the selected product profile immutable, and keep every Futures/account/mutation capability unavailable until authenticated permission, shared contract tests, provider sandbox/testnet tests, rejection/unknown-outcome tests, recorded evidence, and explicit Owner approval satisfy FR-BRK-010.
- **Source class / function / method:** `class BinanceBrokerAdapter(BrokerAdapter)`
- **Source side effects:** External API call; broker mutation only for separately verified supported methods; local session/subscription mutation
- **Source raises:** `asyncio.CancelledError`: caller cancels; operational failures are canonical results.
- **Source usage / test:** **Usage:** `tests/brokers/usage/05_binance.py` (standalone script, run via `python`)<br>**Unit:** `tests/brokers/unit/test_binance_adapter.py::test_futures_profiles_remain_registry_only_for_connect()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-BRK-106`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0013` [ ] `WF-BRK-004` - Submit One Broker Mutation

- **Execution domain:** `Brokers`.
- **Execution position:** `13` of `23`.
- **Cannot start before:** Step `P05-S0012` (`FR-BRK-106`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 3. Workflows > Workflow scope values`` (line 309); matrix row `233`.
- **Source scope:** Cross-domain (`SYS-WF-002`, `SYS-WF-008`)
- **Source workflow:** Submit one mutation
- **Source requirement sequence:** `FR-BRK-091 → FR-BRK-097`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-BRK-004`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0014` [ ] `WF-BRK-005` - Read Account and Execution State

- **Execution domain:** `Brokers`.
- **Execution position:** `14` of `23`.
- **Cannot start before:** Step `P05-S0013` (`WF-BRK-004`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 3. Workflows > Workflow scope values`` (line 310); matrix row `234`.
- **Source scope:** Cross-domain
- **Source workflow:** Read account and execution state
- **Source requirement sequence:** `FR-BRK-079 → FR-BRK-090`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-BRK-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0015` [ ] `WF-BRK-007` - Correlate cTrader Response

- **Execution domain:** `Brokers`.
- **Execution position:** `15` of `23`.
- **Cannot start before:** Step `P05-S0014` (`WF-BRK-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 3. Workflows > Workflow scope values`` (line 312); matrix row `235`.
- **Source scope:** Internal
- **Source workflow:** Correlate cTrader response
- **Source requirement sequence:** `FR-BRK-105`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-BRK-007`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0016` [ ] `CAP-BRK-013` - cTrader adapter

- **Execution domain:** `Brokers`.
- **Execution position:** `16` of `23`.
- **Cannot start before:** Step `P05-S0015` (`WF-BRK-007`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 528); matrix row `219`.
- **Source final destination:** `ctrader/`; FR-BRK-105
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-013`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0017` [ ] `CAP-BRK-014` - Binance profiles

- **Execution domain:** `Brokers`.
- **Execution position:** `17` of `23`.
- **Cannot start before:** Step `P05-S0016` (`CAP-BRK-013`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Brokers` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/brokers/README.md` - ``Brokers > 4. Module and Requirement Specifications > Approved capability traceability`` (line 529); matrix row `220`.
- **Source final destination:** `binance/`; FR-BRK-106
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-BRK-014`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 2 - Data

Implement `Data` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P05-S0018` [ ] `CAP-DATA-008` - SQLite state and transactional infrastructure

- **Execution domain:** `Data`.
- **Execution position:** `18` of `23`.
- **Cannot start before:** Step `P05-S0017` (`CAP-BRK-014`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Data` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/data/README.md` - ``Data > 2. Final Package Structure > Reconciliation capability coverage`` (line 318); matrix row `344`.
- **Source capability:** `CAP-DATA-008` SQLite state and transactional infrastructure
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-DATA-008`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 3 - Trading

Implement `Trading` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P05-S0019` [ ] `FR-TRD-040` - apply deduplicated authority events in logical order with optimistic version checks.

- **Execution domain:** `Trading`.
- **Execution position:** `19` of `23`.
- **Cannot start before:** Step `P05-S0018` (`CAP-DATA-008`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 4. Module and Requirement Specifications > Configuration and Limits Manifest > State requirements`` (line 572); matrix row `654`.
- **Source responsibility:** The system shall apply deduplicated authority events in logical order with optimistic version checks.
- **Source class / function / method:** `apply_execution_event(event: TradingEvent, store: TradingStateStore) -> TradingProjection`
- **Source side effects:** Persistence write
- **Source raises:** `TradingError`: duplicate conflict or stale version
- **Source usage / test:** **Usage:** `tests/trading/usage/test_usage_state.py::test_usage_projections_apply_event()`<br>**Unit:** `tests/trading/unit/state/test_projections.py::test_apply_event_rejects_stale_version()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-TRD-040`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0020` [ ] `FR-TRD-041` - expose the current Trading schema version.

- **Execution domain:** `Trading`.
- **Execution position:** `20` of `23`.
- **Cannot start before:** Step `P05-S0019` (`FR-TRD-040`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 4. Module and Requirement Specifications > Configuration and Limits Manifest > State requirements`` (line 573); matrix row `655`.
- **Source responsibility:** The system shall expose the current Trading schema version.
- **Source class / function / method:** `TRADING_SCHEMA_VERSION: str`
- **Source side effects:** None
- **Source raises:** None
- **Source usage / test:** **Usage:** `tests/trading/usage/test_usage_state.py::test_usage_migrations_schema_version()`<br>**Unit:** `tests/trading/unit/state/test_migrations.py::test_schema_version_matches_events()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-TRD-041`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0021` [ ] `FR-TRD-029` - reject adapters lacking approved provider, API/schema, action, security, timeout, malformed-response, rate-limit, retry, and redaction decla...

- **Execution domain:** `Trading`.
- **Execution position:** `21` of `23`.
- **Cannot start before:** Step `P05-S0020` (`FR-TRD-041`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` package-wide functional behavior in authoritative source order.
- **Delivery type:** Functional implementation.
- **Classification:** T1 Core; size `S`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 4. Module and Requirement Specifications > Configuration and Limits Manifest > Routing requirements`` (line 655); matrix row `653`.
- **Source responsibility:** The system shall reject adapters lacking approved provider, API/schema, action, security, timeout, malformed-response, rate-limit, retry, and redaction declarations.
- **Source class / function / method:** `validate_adapter_capability(intent: OrderIntent, capability: Mapping[str, JsonValue]) -> None`
- **Source side effects:** None
- **Source raises:** `TradingError`: incompatible/unsafe adapter
- **Source usage / test:** **Usage:** `tests/trading/usage/test_usage_routing.py::test_usage_capabilities_validate()`<br>**Unit:** `tests/trading/unit/routing/test_capabilities.py::test_missing_security_contract_blocks()`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `FR-TRD-029`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

#### Step `P05-S0022` [ ] `WF-TRD-005` - Resolve an unknown route outcome

- **Execution domain:** `Trading`.
- **Execution position:** `22` of `23`.
- **Cannot start before:** Step `P05-S0021` (`FR-TRD-029`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Trading` workflow integration after all component and functional steps in this phase.
- **Delivery type:** Workflow integration.
- **Classification:** T1 Core; size `M`; source status `Missing`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/trading/README.md` - ``Trading > 3. Workflows > Workflow scope values`` (line 262); matrix row `656`.
- **Source scope:** Cross-domain
- **Source workflow:** Resolve an unknown route outcome
- **Source requirement sequence:** `FR-TRD-030 → FR-TRD-044`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `WF-TRD-005`.
  2. Implement only the behavior, boundary, side effects, and failure semantics in the authoritative source; preserve final public seams from the first implementation.
  3. Add or update the source-named unit and usage tests. Add integration and negative-path coverage when the item crosses a domain or performs I/O.
  4. Run the narrow test files first, then the phase quality gates. Do not mark complete on mocked proof when the requirement demands an actual provider or persisted-state boundary.
- **Acceptance evidence required:** implementation `path:line`; targeted test `path:line`; passing command/result; contract or runtime artifact when specified.
- **Evidence:** Pending. Replace this line only at completion with concrete `path:line` evidence.

### Stage 4 - Simulation

Implement `Simulation` in authoritative order: all component and functional work first, then domain workflows, capability acceptance, and NFR verification.

#### Step `P05-S0023` [ ] `CAP-SIM-005` - Simulated Trader and authoritative state

- **Execution domain:** `Simulation`.
- **Execution position:** `23` of `23`.
- **Cannot start before:** Step `P05-S0022` (`WF-TRD-005`).
- **Authoritative dependency evidence:** `P-SYS-001` completed in Phase 1 before this phase opened.
- **Ordering basis:** `Simulation` capability acceptance after its functional and workflow steps.
- **Delivery type:** Capability delivery.
- **Classification:** T1 Core; size `M`; source status `Specified`.
- **Dependencies:** `P-SYS-001`.
- **Authoritative source:** `app/services/simulator/README.md` - ``Simulation > 4. Module and Requirement Specifications > Approved capability traceability`` (line 452); matrix row `727`.
- **Source final destination:** `execution/`: `FR-SIM-021`–`FR-SIM-023`
- **Implementation instructions:**
  1. Confirm every dependency above is complete and evidenced before starting `CAP-SIM-005`.
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

- **Expected assigned IDs:** 23.
- **Plan requirement entries:** 23.
- **Matrix phase:** `5`.
- **Unchecked items at plan creation:** all.
- **Completion rule:** zero unchecked requirement entries, zero missing evidence references, and all exit/close gates checked.

### 11.1 Assigned ID manifest

This manifest is a coverage index only. It must not be used to choose the next implementation task.

- **System (0):** None.
- **Utils (0):** None.
- **Brokers (17):** `CAP-BRK-013`, `CAP-BRK-014`, `FR-BRK-106`, `FR-BRK-115`, `FR-BRK-119`, `FR-BRK-120`, `FR-BRK-121`, `FR-BRK-122`, `FR-BRK-123`, `FR-BRK-124`, `FR-BRK-125`, `P-BRK-002`, `P-BRK-005`, `P-BRK-006`, `WF-BRK-004`, `WF-BRK-005`, `WF-BRK-007`
- **Data (1):** `CAP-DATA-008`
- **Indicators (0):** None.
- **Strategy (0):** None.
- **Risk (0):** None.
- **Trading (4):** `FR-TRD-029`, `FR-TRD-040`, `FR-TRD-041`, `WF-TRD-005`
- **Simulation (1):** `CAP-SIM-005`
- **Analytics (0):** None.
- **Optimization (0):** None.
- **Research (0):** None.
- **Portfolio (0):** None.
- **UI/API (0):** None.

## 12. Rollback boundary

Rollback is phase-scoped and evidence-driven. Revert only files introduced or changed by the failing work package; do not erase unrelated owner work or use destructive Git commands. Broker-side demo actions must be reconciled and safely closed through the governed Trading/Brokers path before local rollback. Persisted schema rollback follows the owning domain migration contract. If safe rollback cannot be proven, stop the phase and record the exact blocked state.
