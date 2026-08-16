# Risk Domain Audit Remediation Implementation Plan

> **Target package:** `app/services/risk/`
> **Plan status:** Ready for coding-agent dry run
> **Audit baseline date:** 2026-08-06
> **Implementation authorization:** Not granted by this document

This document is the self-contained implementation specification for correcting every
non-conformant Risk-domain audit control. A coding agent must read `AGENTS.md`,
`docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, this plan, and the
current `app/services/risk/README.md` before acting. It must then issue its own numbered
implementation dry run and wait for a new standalone `APPROVED: EXECUTE`. Approval to
create this plan does not authorize any remediation below.

The authority order is Owner -> `AGENTS.md` -> `docs/PROJECT.md` ->
`docs/ARCHITECTURE.md` -> `docs/CHANGELOG.md`. The owning Risk README remains the sole
canonical current-state registry for Risk feature IDs, requirements, APIs, contracts,
and usage evidence. Applied migration history is immutable.

## 1. Objective and audit baseline

The Risk audit produced 15 passes and seven failures. Remediate these failures without
broad refactoring or adding speculative capabilities:

| Control | Baseline finding | Required end state |
|---|---|---|
| `USE` | All 69 functional-requirement examples run and print at least two values, but 67 lack an explicit success message. | Every `fr_risk_NNN()` prints exactly one explicit success line and at least one bounded actual-data line; automated output validation enforces both. |
| `COV` | Total Risk branch-aware coverage is 86%, but `audit/runtime.py` is 76% and `governor/runtime.py` is 53%. | Every production Risk Python file is at or above 80% branch-aware coverage. |
| `SCHEMA` | Applied Risk DDL omits target JSON/enum constraints and one partial-index predicate; reconciliation incorrectly says the seven tables match exactly. | Target model, migration definitions, applied-live reconciliation, and application vocabulary agree without modifying applied `risk-0001`. |
| `REACH` | `risk_policy_versions` has no CRUD builder/executor or production operation outside `persistence/`. | The table has an explicit Risk-owned registration/read path through Data-owned transaction infrastructure. |
| `CONTRACT` | Contracts are documented and versioned, but compatibility evidence covers only Strategy intent and Data market context; some declared consumers are not implemented. | Every declared producer-consumer relationship has an explicit compatibility test, or the unsupported counterparty claim is removed. |
| `LOG` | Material governor/token/audit paths log, but public relational state entry points do not log their semantic read/write boundaries. | Public Risk persistence operations log bounded entry, outcome, and failure evidence without payloads or secrets. |
| `DOCS` | README test/coverage/workflow claims, migration application statements, schema reconciliation, and Architecture API status disagree with code. | README, Architecture, schema model/reconciliation, API README, and changelog accurately describe the final implementation. |

Preserve all controls that already pass: `REG`, `TASK`, `GATE`, `FUNC`, `DEEP`, `ROOT`,
`WFE`, `UT`, `IT`, `HYG`, `DB`, `SAFE`, `QUANT`, `NFR`, and `UI`.

## 2. Non-negotiable decisions

### 2.1 No applied migration edits

`risk-0001-initial-state` is applied in `data/database/haruquant-dev.db`; its ledger
checksum matched source during the audit. Do not edit, reorder, reformat, or delete its
statement tuple. If the working tree still represents the applied step in
`app/services/risk/migrations/definitions.py`, preserve the existing bytes as step 0001
and add a new step.

Never apply a new migration to `data/database/haruquant-dev.db` during iterative work.
All migration tests use `tmp_path`, a disposable directory, and a database created
through `data_settings_context(build_data_settings(...))`. Applying a migration to the
repository development database requires separate explicit owner approval.

### 2.2 Canonical kill-switch vocabulary

The implemented Risk contracts and system workflows use:

- scope levels: `global`, `portfolio`, `strategy`, `symbol`;
- states: `active`, `inactive`.

These values are canonical for this remediation because they are used by Risk's public
contracts, the UI/API route, Trading enforcement, and `docs/PROJECT.md`. Update the
target schema model away from the stale `account` scope and
`armed`/`tripped`/`resetting` vocabulary. Do not change public contract values merely
to match stale schema prose.

### 2.3 No speculative consumers

Do not build a Research or UI scenario workflow solely to justify an inaccurate
contract-counterparty claim. A counterparty remains documented only when production
code consumes the exact package-root contract. Otherwise remove that counterparty from
the current-state documentation while retaining the Risk capability itself.

### 2.4 Function-only public API

Any new Risk public symbol must be a standalone function re-exported by
`app/services/risk/__init__.py`. Do not export `RiskConfig`, protocols, stores,
repository classes, enums, constants, or persistence builders.

## 3. Scope and implementation order

Implement in this order so documentation never authorizes unimplemented behavior:

1. Update the Risk README specification and register the new policy persistence
   requirements as `Missing` during implementation.
2. Add schema step 0002 and its disposable-database tests.
3. Add `risk_policy_versions` persistence builders and feature-owned runtime functions.
4. Add semantic logging at public state boundaries.
5. Correct and extend producer-consumer compatibility tests.
6. Correct all usage outputs and strengthen their integration test.
7. Raise the two deficient production files to the per-file coverage floor using tests.
8. Reconcile Risk README, schema documents, Architecture, API README if required, and
   changelog; mark new requirements `Completed` only after all gates pass.
9. Execute targeted and final validation.

If any implementation discovery materially expands these files or changes a public
contract beyond the signatures below, stop and issue a plan delta for owner approval.

## 4. Workstream A — executable usage evidence (`USE`)

### 4.1 Files to edit

Edit all numbered feature programs and no workflow program unless a test exposes a
pre-existing workflow failure:

```text
tests/risk/usage/features/01_contracts.py
tests/risk/usage/features/02_config.py
tests/risk/usage/features/03_portfolio.py
tests/risk/usage/features/04_sizing.py
tests/risk/usage/features/05_audit.py
tests/risk/usage/features/06_limits.py
tests/risk/usage/features/07_regimes.py
tests/risk/usage/features/08_admission.py
tests/risk/usage/features/09_allocation.py
tests/risk/usage/features/10_approvals.py
tests/risk/usage/features/11_validity.py
tests/risk/usage/features/12_governor.py
tests/risk/usage/features/13_kill_switch.py
tests/risk/usage/features/14_scenarios.py
tests/risk/usage/features/15_reporting.py
tests/risk/integration/test_usage_scripts.py
```

### 4.2 Output contract

Every top-level function matching `fr_risk_\d{3}` must, on success, print both:

```text
SUCCESS: FR-RISK-NNN
Data -> <bounded actual result fields>
```

The data line must be derived from the operation's returned value or mutated in-memory
test state. It must not print a synthetic claim, an entire unbounded payload, a secret,
signing material, token signature, credential, or full sensitive trading state.

Use a shared private helper in each usage program only if it reduces repetition without
moving behavior into a second support implementation. An acceptable local signature is:

```python
def _print_success(requirement_id: str, data: str) -> None:
    """Print explicit success and bounded actual-data evidence."""
```

The helper prints the two lines above. Existing feature banners and type summaries may
remain, but they do not substitute for either required line.

### 4.3 Test enforcement

Extend `tests/risk/integration/test_usage_scripts.py` with a structural and runtime
assertion. Preserve its isolated subprocess execution. For every README-documented FR:

- the corresponding `fr_risk_NNN()` remains top-level and reachable from `main()`;
- captured stdout contains exactly one `SUCCESS: FR-RISK-NNN` line;
- the function's output contains at least one `Data -> ` line after its requirement
  heading and before the next requirement heading;
- no secret-like key/value pattern appears in stdout.

Do not weaken the existing exact README-to-function reconciliation.

### 4.4 Acceptance

- 15 numbered files for 15 registered features.
- All 69 current FR example functions execute.
- All 69 emit success plus actual data.
- `features.py` may remain the full-domain demonstration but is not a sixteenth feature.

## 5. Workstream B — schema and migration reconciliation (`SCHEMA`)

### 5.1 Files to edit

```text
app/services/risk/migrations/definitions.py
tests/risk/unit/test_migrations.py
tests/risk/integration/test_runtime_state.py
docs/schema/02_entity_specs_execution.md
docs/schema/04_indexing_and_performance.md
docs/schema/05_reconciliation.md
```

Update `docs/schema/README.md` only if its counts or decision summary change after the
schema verifier is run. Do not touch unrelated domain schema discrepancies.

### 5.2 Manifest composition

Keep `run_risk_migrations(request_id: str) -> object` public and keep delegation through
Data's package root:

```python
request = build_migration_request(
    domain="risk",
    steps=_RISK_MIGRATION_STEPS,
    request_id=request_id,
    complete_manifest=True,
)
return run_domain_migrations(request)
```

`_RISK_MIGRATION_STEPS` becomes the ordered tuple of preserved step 0001 and new step
0002. Each checksum remains SHA-256 over the exact ordered SQL statement tuple.

### 5.3 New migration

Add migration ID:

```text
risk-0002-schema-constraints
```

The migration must bring the seven current Risk tables to these invariants:

| Table | Required constraints/index behavior |
|---|---|
| `risk_policy_versions` | `profile IN ('research','simulation','demo','live')`; `json_valid(payload_json)` |
| `risk_eligibility_decisions` | `json_valid(payload_json)` |
| `risk_allocation_decisions` | existing `active IN (0,1)` retained; `json_valid(payload_json)` |
| `risk_kill_switch_states` | `scope_level IN ('global','portfolio','strategy','symbol')`; `json_valid(scope_json)`; `state IN ('active','inactive')`; `json_valid(payload_json)` |
| `risk_approval_tokens` | `json_valid(scope_json)`; `state IN ('issued','reserved','consumed','expired','revoked')`; `json_valid(payload_json)` |
| `risk_decision_snapshots` | `json_valid(payload_json)` |
| `risk_audit_records` | `json_valid(payload_json)`; `json_valid(evidence_refs_json)`; `idx_risk_audit_decision` is partial with `WHERE decision_id IS NOT NULL` |

SQLite cannot add table `CHECK` constraints in place. Implement a guarded table-rebuild
sequence inside the single Data-owned transaction used for the migration step:

1. Validate every existing row with explicit `SELECT CASE WHEN ... THEN 1 ELSE
   RAISE/guard failure END`-equivalent statements supported by the repository's
   migration executor. If the statement-plan boundary cannot return and branch during a
   manifest step, use `CREATE TABLE ... AS SELECT` guards whose constraints reject an
   invalid row during `INSERT ... SELECT`.
2. Create `risk_<name>__new` with the authoritative constrained DDL.
3. Copy columns explicitly in canonical order; never use `SELECT *`.
4. Verify row preservation within the same transaction using SQL guards.
5. Drop the old table only after the copy succeeds.
6. Rename the new table to the canonical name.
7. Recreate every canonical index.
8. Let Data append the migration ledger record in the same transaction.

Because all operations are one migration transaction under Data's write lock, any
constraint or copy failure must roll back tables and ledger together. Do not introduce
foreign-key toggles, autocommit, raw `sqlite3` connections, or direct database paths in
Risk.

If the repository migration request model cannot safely express a rebuild with the
required validations in one statement plan, stop and issue a plan delta. Do not split
the migration transaction or silently replace constraints with application-only checks.

### 5.4 Migration tests

Add tests that:

- assert step IDs, order, domains, and source checksums;
- assert `complete_manifest=True` by testing that an injected orphan ledger ID fails;
- migrate a fresh disposable database through 0001 and 0002;
- migrate a disposable 0001 database containing one valid row per table and prove exact
  row preservation;
- insert invalid JSON and invalid enums after 0002 and prove SQLite rejects them;
- prove active/inactive kill-switch rows are accepted and stale schema values are
  rejected;
- prove a failure during copy leaves 0001 tables and ledger unchanged;
- prove a second run skips both steps with checksum equality;
- query `sqlite_master` and compare Risk DDL/indexes with the target schema.

No test may open or mutate `data/database/haruquant-dev.db`.

## 6. Workstream C — policy-table production reachability (`REACH`)

### 6.1 Requirement ownership

Keep this behavior under `FEAT-RISK-02` (`config/`); do not create `FEAT-RISK-16`.
Register these rows in Risk README Section 4.2 before implementation:

| Status during build | Requirement | Responsibility |
|---|---|---|
| Missing -> Completed | `FR-RISK-076` | Idempotently register an immutable validated Risk configuration under its canonical hash in `risk_policy_versions`; conflicting identity or payload fails closed. |
| Missing -> Completed | `FR-RISK-077` | Read one immutable registered Risk configuration by exact 64-character lowercase SHA-256 hash; missing records remain explicit and malformed stored rows fail closed. |

### 6.2 Production files

Create:

```text
app/services/risk/config/runtime.py
```

Edit:

```text
app/services/risk/config/__init__.py
app/services/risk/persistence/create.py
app/services/risk/persistence/read.py
app/services/risk/persistence/__init__.py
app/services/risk/__init__.py
```

Do not add a sixth persistence file. `update.py` and `delete.py` remain unchanged because
policy versions are immutable.

### 6.3 Public operations

Expose exactly these standalone functions from `app.services.risk`:

```python
def register_risk_policy(
    config: object,
    *,
    effective_at: datetime,
    request_id: str,
    correlation_id: str,
) -> object:
    """Register an immutable Risk configuration through the standard response boundary."""


def get_risk_policy(config_hash: str) -> object:
    """Return a registered Risk configuration through the standard response boundary."""
```

The opaque `object` annotations preserve the package-root function-only surface and
avoid exporting `RiskConfig`. Each function must be wrapped using the same
`guard_risk_boundary`/`StandardResponse` pattern used by existing Risk operations.
Successful `register_risk_policy` returns the canonical configuration hash in `data`.
Successful `get_risk_policy` returns the reconstructed internal `RiskConfig` in `data`.
A missing hash returns the established Risk error code selected in the README contract;
do not return an invented empty configuration.

Before finalizing the requirement row, use the existing Risk error catalogue. Prefer an
existing exact code such as `MISSING_EVIDENCE` only if its documented semantics fit.
Otherwise a new error code is a material public-contract expansion and requires a plan
delta rather than inventing one during implementation.

### 6.4 Private persistence boundary

Add private persistence exports with focused responsibilities:

```python
def create_policy_version(
    config_hash: str,
    policy_version: str,
    profile: str,
    payload_json: str,
    effective_at: str,
    request_id: str,
    correlation_id: str,
) -> bool:
    """Insert one immutable Risk policy version or verify an idempotent replay."""


def read_policy_version(config_hash: str) -> Mapping[str, object] | None:
    """Read one normalized Risk policy row by exact hash."""
```

Match the existing persistence calling convention exactly: build bounded
`StatementPlan`/transaction requests, delegate only through `app.services.data`, and
normalize rows before handing them to `config/runtime.py`. Do not import Data private
modules, open SQLite directly, or place policy validation in `persistence/`.

`register_risk_policy` must:

1. Verify the opaque value is the internal validated `RiskConfig` type.
2. Compute the hash with existing `compute_config_hash` raw behavior rather than hashing
   a second serialization.
3. Require aware UTC `effective_at` and valid prefixed UUID4 request/correlation IDs
   according to existing Risk conventions.
4. Serialize with canonical JSON and no secrets.
5. Insert idempotently when hash and payload match.
6. Fail closed when an existing hash has different policy identity or payload.

`get_risk_policy` must validate hash form, deserialize the stored canonical payload into
the internal `RiskConfig`, recompute and compare the hash, and fail closed on malformed
or tampered storage.

### 6.5 Tests and usage

Create or extend:

```text
tests/risk/unit/test_runtime_policy.py
tests/risk/integration/test_runtime_state.py
tests/risk/usage/features/02_config.py
tests/risk/integration/test_usage_scripts.py
```

Add `fr_risk_076()` and `fr_risk_077()` to `02_config.py`, invoke them from `main()`,
and follow the success/data output contract. Integration evidence must run migrations in
a disposable database, reconstruct the runtime between write/read, and prove the record
survives. Tests must cover idempotent replay, conflicting payload, malformed hash,
missing record, corrupted payload, UTC validation, and secret-free logging.

Update `app/services/risk/__init__.py`'s literal `__all__` with only
`register_risk_policy` and `get_risk_policy`; the runtime/store helpers remain private.

## 7. Workstream D — semantic persistence logging (`LOG`)

### 7.1 Files to edit

```text
app/services/risk/audit/runtime.py
app/services/risk/config/runtime.py
app/services/risk/approvals/runtime.py   # only if tests expose equivalent gaps
tests/risk/unit/test_runtime_decisions.py
tests/risk/unit/test_runtime_policy.py
```

### 7.2 Required events

Add bounded logs at these public functions:

| Function | Entry/outcome fields |
|---|---|
| `execute_risk_state_store_operation` | operation name; success/failure classification only |
| `get_kill_switch_state` | scope level; found/not-found; never full scope payload |
| `persist_risk_decision` | decision ID, request/workflow/correlation IDs, verdict; never full decision/token |
| `list_risk_decisions` | requested bound and returned count |
| `register_risk_policy` | config hash, policy version, profile, trace IDs, idempotent/created result |
| `get_risk_policy` | requested hash and found/not-found result |

Use the system logger obtained from `app.utils`. Log state transitions and persistence
failures at appropriate levels and re-raise/map failures; do not swallow exceptions.
Never log configuration payload JSON, signing-key references beyond an already-approved
non-secret reference, approval signatures, token values/nonces, credentials, or full
scope mappings.

Tests must use the existing logging capture convention and assert both required fields
and absence of secret-like values.

## 8. Workstream E — producer-consumer compatibility (`CONTRACT`)

### 8.1 Authoritative inventory

Start from the owned/consumed contract tables in Risk README and the system contract
registry in `docs/PROJECT.md`. For each row, search production code—not usage fixtures—for
a package-root import or a typed receiver boundary. Apply this deterministic rule:

- If production consumption exists, retain the counterparty and add an explicit
  producer-consumer compatibility test using both domains' public package roots.
- If no production consumption exists, remove that counterparty from current-state
  documentation. Do not create a consumer merely to make the table true.
- If PROJECT and the owning README disagree, correct both according to verified code
  ownership, preserving system-level relationships only in PROJECT.

### 8.2 Existing relationships to retain and test

At minimum retain and cover these verified relationships:

| Producer | Contract | Consumer/test destination |
|---|---|---|
| Strategy | `create_trade_intent_value v1` | Risk: retain `tests/risk/integration/test_contract_compatibility.py::test_risk_embeds_the_exact_strategy_intent` |
| Data | `build_market_context_evidence v1` | Risk: retain the direct validation compatibility test |
| Data | `build_account_state_snapshot v1`, `build_fx_conversion_evidence v1` | Risk: add direct construction/snapshot compatibility cases in Risk integration tests |
| Utils | `create_auth_context v1` | Risk: test governor and kill-switch acceptance/rejection using the Utils package-root value |
| Risk | `RiskDecisionPackage v1`, `ActionPolicyVerdict v1`, `KillSwitchState v1` | Trading: add/rename an explicit integration compatibility file using Risk and Trading package roots |
| Risk | `AllocationRiskDecision v1`, `StrategyOperationalEligibilityDecision v1`, `KillSwitchState v1` | Portfolio: add/rename an explicit integration compatibility file using Risk and Portfolio package roots |
| Risk | `KillSwitchCommand v1`, `KillSwitchState v1`, `ApprovalAttestation v1`, bounded decision reads | UI/API: extend Risk route/composition integration tests using API and Risk package roots |

Candidate test files are:

```text
tests/risk/integration/test_contract_compatibility.py
tests/trading/integration/test_risk_contract_compatibility.py
tests/portfolio/integration/test_risk_contract_compatibility.py
tests/api/integration/test_risk_contract_compatibility.py
```

Before creating a candidate file, confirm an equivalent compatibility test does not
already exist. Prefer extending or renaming existing focused evidence over duplicating
it.

### 8.3 Claims requiring correction unless a real consumer is found

The audit found no production Research or UI/API consumer of `ScenarioResult`. Unless
current code has changed by implementation time:

- retain `ScenarioResult v1` as a Risk-owned public advisory result;
- document its counterparty as no registered cross-domain consumer/current Risk caller;
- remove Research/UI/API consumer claims from Risk README and API README;
- do not add a scenario HTTP endpoint or frontend workflow under this remediation.

Apply the same rule to Simulation's declared consumption of the complete
`RiskDecisionPackage`: if Simulation production code stores only a decision ID or a
receiver-owned projection, document that exact relationship instead of claiming it
consumes the complete Risk object.

### 8.4 Compatibility acceptance

Every retained contract row must name an exact test path. Tests must verify version,
schema ID, required fields, failure on incompatible version/shape, and preservation of
producer-owned values without redefinition by the consumer.

## 9. Workstream F — per-file coverage (`COV`)

### 9.1 Target files

Do not add coverage-only production branches. Add focused tests for real behavior in:

```text
tests/risk/unit/test_relational_persistence_branches.py
tests/risk/unit/test_runtime_composition.py
tests/risk/unit/test_runtime_decisions.py
tests/risk/unit/test_function_facades.py
```

Create a new focused test file only when none of these owns the behavior.

### 9.2 `audit/runtime.py` cases

Cover at least:

- malformed and missing relational rows;
- invalid serialized audit, eligibility, allocation, decision, and kill-switch payloads;
- every allowlisted `execute_risk_state_store_operation` dispatch;
- forged store handles and unsupported operation names;
- exact-scope kill-switch miss and hit;
- decision persistence type rejection, idempotent replay, and conflict;
- list bounds, empty list, ordered list, and malformed stored decision;
- logging outcomes added by Workstream D.

### 9.3 `governor/runtime.py` cases

Cover at least:

- building allocation and governance runtime operations with all required dependencies;
- missing/`None` dependency rejection;
- supported operation dispatch to the public function;
- unsupported operation rejection;
- preservation of positional and keyword arguments without exposing an internal class;
- forged operation handle rejection where applicable;
- fail-closed propagation of a Risk `StandardResponse` error.

### 9.4 Acceptance

Run branch-aware coverage against `app/services/risk` only. Overall coverage is not a
substitute for the per-file rule. Every listed production file, including runtime
facades and `__init__.py` files, must report at least 80%.

## 10. Workstream G — documentation reconciliation (`DOCS`)

### 10.1 Risk README

Edit `app/services/risk/README.md` to:

- register `FR-RISK-076` and `FR-RISK-077` under `FEAT-RISK-02`;
- add the two public policy operations to the exact public API table and `__all__`
  evidence;
- document `config/runtime.py` in the package tree and module specification;
- preserve exactly 15 registered features and 15 numbered feature programs;
- change workflow statements from stale “thirteen” to 15 active workflows;
- replace hard-coded test counts and coverage percentages with newly measured values, or
  use durable statements that do not become stale immediately;
- name the two new usage functions and tests;
- state that `risk-0001` is applied and immutable and `risk-0002` is the constraint
  reconciliation step after it passes;
- correct the package tree's stale `audit/migrations.py` entry to the actual
  `migrations/definitions.py` support package;
- state that migration execution is explicitly invoked by deployment/bootstrap code;
  do not claim automatic application composition unless a production composition call
  exists;
- retain `No open decisions` only if no unresolved owner choice remains;
- mark every new requirement and checklist item `Completed` only after code, tests,
  usage, and documentation pass.

### 10.2 Schema documents

Update `docs/schema/02_entity_specs_execution.md` with exact constrained DDL and the
canonical active/inactive vocabulary. Update `docs/schema/04_indexing_and_performance.md`
so its kill-switch query/index examples use actual table and state names. Update
`docs/schema/05_reconciliation.md` to:

- remove the false claim that all seven tables matched before 0002;
- record the pre-0002 missing constraints and index predicate;
- record 0002 as the closing migration only after tests pass;
- distinguish target-only `risk_limits`, `risk_limit_checks`, and
  `risk_exposure_snapshots` from the seven current tables;
- remove stale statements that Risk's initial step was never applied;
- update schema counts only from the verifier output, never manually estimate them.

Do not fix unrelated Indicators or other-domain schema-verifier failures under this
Risk remediation.

### 10.3 Architecture and project

Edit `docs/ARCHITECTURE.md` to remove stale claims that Risk HTTP routes are absent.
Describe the implemented boundary exactly:

- authenticated exact-scope kill-switch read;
- bounded immutable decision reads;
- governed kill-switch command requiring explicit Risk dependency composition;
- frontend `RiskView` read presentation;
- no frontend auto-mutation and no Risk policy/scenario endpoint unless separately
  implemented.

Edit `docs/PROJECT.md` only where contract counterparties or system relationships are
factually wrong after Workstream E. Do not duplicate Risk feature internals there.

### 10.4 API README

Edit `app/services/api/README.md` only for verified Risk boundary corrections, including
removal of unsupported `ScenarioResult` consumption if still absent. Preserve API's own
feature registry and requirement ownership.

### 10.5 Changelog

Add one concise Risk remediation headline under the top `## [Unreleased]` section of
`docs/CHANGELOG.md`. Use canonical category order and exact counts. Summarize only
release-visible effects:

- `Added`: immutable Risk schema-constraint migration and policy-version public
  operations, if implemented;
- `Changed`: compatibility evidence, logging, usage output, and corrected active docs;
- `Fixed`: per-file coverage and target/live schema mismatch.

Do not add a test inventory, audit matrix, mutable feature registry, or detailed current
state to the changelog.

## 11. Exact anticipated file set

The coding agent must confirm this set during its dry run. This is the maximum expected
scope; omit files proven unnecessary and request a plan delta before adding unrelated
paths.

### Production

```text
app/services/risk/__init__.py
app/services/risk/config/__init__.py
app/services/risk/config/runtime.py                         # new
app/services/risk/migrations/definitions.py
app/services/risk/persistence/__init__.py
app/services/risk/persistence/create.py
app/services/risk/persistence/read.py
app/services/risk/audit/runtime.py
```

`app/services/risk/approvals/runtime.py` and
`app/services/risk/governor/runtime.py` may be edited only if logging or a genuine bug
requires production change; coverage alone authorizes tests, not production edits.

### Risk tests and usage

```text
tests/risk/unit/test_migrations.py
tests/risk/unit/test_runtime_policy.py                      # new
tests/risk/unit/test_relational_persistence_branches.py
tests/risk/unit/test_runtime_composition.py
tests/risk/unit/test_runtime_decisions.py
tests/risk/unit/test_function_facades.py
tests/risk/integration/test_runtime_state.py
tests/risk/integration/test_contract_compatibility.py
tests/risk/integration/test_usage_scripts.py
tests/risk/usage/features/01_contracts.py
tests/risk/usage/features/02_config.py
tests/risk/usage/features/03_portfolio.py
tests/risk/usage/features/04_sizing.py
tests/risk/usage/features/05_audit.py
tests/risk/usage/features/06_limits.py
tests/risk/usage/features/07_regimes.py
tests/risk/usage/features/08_admission.py
tests/risk/usage/features/09_allocation.py
tests/risk/usage/features/10_approvals.py
tests/risk/usage/features/11_validity.py
tests/risk/usage/features/12_governor.py
tests/risk/usage/features/13_kill_switch.py
tests/risk/usage/features/14_scenarios.py
tests/risk/usage/features/15_reporting.py
```

### Cross-domain compatibility tests

Create or extend only after checking for equivalent focused tests:

```text
tests/trading/integration/test_risk_contract_compatibility.py
tests/portfolio/integration/test_risk_contract_compatibility.py
tests/api/integration/test_risk_contract_compatibility.py
```

### Active documents

```text
app/services/risk/README.md
app/services/api/README.md
docs/PROJECT.md
docs/ARCHITECTURE.md
docs/CHANGELOG.md
docs/schema/README.md                    # only if verifier-derived counts change
docs/schema/02_entity_specs_execution.md
docs/schema/04_indexing_and_performance.md
docs/schema/05_reconciliation.md
```

## 12. Dependencies and contracts

Use only these verified package-root dependencies:

- `app.services.data`: migration request/step construction, domain migration execution,
  statement-plan and transaction execution, typed Data settings in tests;
- `app.utils`: logger, canonical JSON/hash behavior, UTC/identity validation helpers,
  response metadata/error mapping already approved by Risk;
- `app.services.strategy`: `create_trade_intent_value v1` compatibility evidence;
- public Data evidence factories used by Risk;
- public Trading, Portfolio, and API operations only in cross-domain compatibility tests.

Do not add a dependency, upgrade a library, import another domain's private module, or
introduce direct SQLite access. Use versions pinned in `pyproject.toml`.

## 13. Validation commands

Run targeted commands during development, then the final gate. Use `--no-cov` for
test-pass checks because repository-wide default coverage can obscure a targeted suite.
Use an explicit Risk-only source for the coverage gate.

```powershell
uv run ruff check app/services/risk tests/risk
uv run ruff format --check app/services/risk tests/risk
uv run mypy app/services/risk

uv run pytest tests/risk/unit/test_migrations.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/unit/test_runtime_policy.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/unit/test_runtime_decisions.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/unit/test_runtime_composition.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/unit/test_relational_persistence_branches.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/integration/test_runtime_state.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/integration/test_contract_compatibility.py -q --no-cov -p no:cacheprovider
uv run pytest tests/risk/integration/test_usage_scripts.py -q --no-cov -p no:cacheprovider

uv run python -B tests/risk/usage/features/02_config.py
uv run python -B tests/risk/usage/workflows/run_all.py

uv run pytest tests/risk/unit -q --no-cov -p no:cacheprovider --durations=0
uv run pytest tests/risk/integration -q --no-cov -p no:cacheprovider

$env:COVERAGE_FILE = Join-Path $env:TEMP 'haruquant-risk-remediation.coverage'
$json = Join-Path $env:TEMP 'haruquant-risk-remediation-coverage.json'
uv run pytest tests/risk -q -p no:cacheprovider -o addopts='' `
  --cov=app/services/risk --cov-branch --cov-report=term-missing `
  --cov-report="json:$json" --cov-fail-under=80

uv run python -B docs/schema/compare_model_to_code.py
uv run python -B docs/schema/verify_persistence_sql.py
uv run python -B docs/schema/verify_schema.py
```

For schema scripts with unrelated pre-existing failures, capture the full output and
prove every Risk row passes. Do not fix another domain without a separate approved plan.

Run applicable cross-domain targeted tests after creating/extending them:

```powershell
uv run pytest tests/trading/integration/test_risk_contract_compatibility.py -q --no-cov -p no:cacheprovider
uv run pytest tests/portfolio/integration/test_risk_contract_compatibility.py -q --no-cov -p no:cacheprovider
uv run pytest tests/api/integration/test_risk_contract_compatibility.py -q --no-cov -p no:cacheprovider
```

If UI/API documentation is corrected without frontend behavior changes, existing Risk
route and view tests are sufficient. If any API/frontend code changes become necessary,
that is a plan delta; after approval run:

```powershell
uv run pytest tests/api/unit/test_risk_routes.py tests/api/unit/test_risk_command_routes.py -q --no-cov -p no:cacheprovider
Set-Location app/ui
npm test -- --run src/components/workflow/risk.test.tsx
```

## 14. Acceptance criteria

The remediation is complete only when all are true:

- [ ] 15 Risk feature IDs equal 15 feature directories and 15 numbered usage files.
- [ ] All README status and checklist rows are `Completed`, with truthful evidence.
- [ ] Root `__all__` remains literal and function-only.
- [ ] Repository consumer scan finds no deep Risk imports.
- [ ] All 69 existing FR examples plus `FR-RISK-076` and `FR-RISK-077` print explicit success and actual data.
- [ ] All 15 active workflow programs and `run_all.py` execute.
- [ ] Unit and integration suites pass.
- [ ] Every production Risk file is at least 80% branch-aware coverage.
- [ ] No bare `except`, application `print`, literal secret, or sensitive log payload exists.
- [ ] Risk migration requests use the complete manifest and retain immutable applied-step checksums.
- [ ] Step 0002 is proven transactionally on disposable databases and is not applied to the repository development database.
- [ ] Target Risk DDL and migration-result DDL match, including checks and partial indexes.
- [ ] Every current Risk table has a production operation outside `persistence/`; `risk_policy_versions` is no longer orphaned.
- [ ] Every retained shared-contract counterparty has explicit compatibility evidence.
- [ ] Public state reads/writes have secret-safe semantic logs.
- [ ] Safety, determinism, no-live-action defaults, and the 100 ms unit-test ceiling remain passing.
- [ ] Risk API reads/command composition and frontend Risk view remain passing.
- [ ] README, Architecture, schema documents, PROJECT where necessary, API README, and changelog match code.
- [ ] No unrelated user changes are modified.

## 15. Rollback plan

Before implementation, record the exact pre-change `git status --short`. Roll back only
files changed under the approved implementation plan; never use `git reset --hard`,
`git clean`, or broad checkout commands.

Logical rollback order:

1. Remove the new root exports for `register_risk_policy` and `get_risk_policy`.
2. Revert `config/runtime.py` and policy persistence builders/exports.
3. Remove step 0002 only if it has never been applied anywhere. If applied, it is
   immutable and requires a new forward migration; never delete or edit it.
4. Revert test and usage additions tied only to removed behavior.
5. Reconcile README/schema/Architecture/changelog back to the actual remaining code.
6. Re-run Risk import, unit, integration, usage, and schema verification commands.

No rollback may delete or replace `data/database/haruquant-dev.db` or its backups.

## 16. Coding-agent final report

The coding agent's final response must report:

- exact files changed;
- requirements implemented and their feature owner;
- decisions and implications;
- dependencies and public contracts used;
- schema migration IDs and confirmation that no repository database was mutated;
- every validation command and result;
- per-file Risk coverage, explicitly naming the lowest file;
- usage and workflow execution results;
- affected active documents updated;
- any unrelated pre-existing failures;
- rollback path;
- checklist confirmation that approved scope was strictly followed.

Every completed implementation-plan checklist item added to an active document must end
with supporting code/test file paths and line numbers, as required by `AGENTS.md`.
