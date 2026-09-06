# Agentic Rebuild — Phase 1 Foundation

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

## 7. Phase 1 — Shared Contract Foundation

### AGT-1.00 — Establish the Agentic public contract foundation

**Goal:** create only the shared, business-neutral Agentic contract primitives needed by the 20 capability modules. This is not a mountable feature.

**Depends on:** `AGT-0.GATE`.

**Allowed paths**

```text
app/contracts/agentic/README.md
app/contracts/agentic/__init__.py
app/contracts/agentic/common.py
app/contracts/agentic/errors.py              # only if semantic errors add value
app/contracts/<ratified-event-location>/**   # only if P0.2 selects a shared event package
tests/contracts/agentic/test_common.py
tests/contracts/agentic/test_errors.py
app/contracts/README.md
```

**Implementation checklist**

- [ ] Create a pure `__init__.py` with no re-exports or registration.
- [ ] Define shared strict frozen records only when at least two capabilities need them: task/run/principal/scope identities, deadlines, budgets/usage, provenance, content/evidence references, warnings, refusal/failure, role/prompt/model references, checkpoints/terminal reasons, uncertainty, and reliability.
- [ ] Reuse current common types such as UUID/time/decimal/content-hash records rather than creating Agentic duplicates.
- [ ] Define canonical JSON/hash behavior once and test field-order, timezone, Decimal, collection-order, and mutation invariants.
- [ ] Keep credentials, provider clients, raw prompts, hidden reasoning, database rows, and receiver-owned result types out of shared contracts.
- [ ] Document the 20 capability modules as future owners without predeclaring unratified external keys.
- [ ] Add compatibility tests proving public construction/serialization/equality/immutability behavior.
- [ ] Run targeted Ruff, mypy, contracts tests, Import Linter, and architecture checks.

**Usage evidence:** contract modules are pure and need no feature usage harness; their behavior is demonstrated by each consuming feature’s primary-module harness.

**Proposed commit:** `feat(agentic): establish public contract foundation`

**Rollback:** revert the commit before any capability module depends on it. After use, breaking changes require a new major or an explicit compatibility migration.

---

## 8. Feature Implementation Tasks

The following sections are the authoritative Task order after Phase 0. Every Task also performs the common feature delivery protocol in §3. Feature-specific checklists below are additional and mandatory.

### AGT-1.01 — `FEAT-AGT-ENFORCE_MANDATE` — Mandate Enforcement

**Goal:** Validate the immutable Agentic operating envelope and answer exact scope, budget, environment, role, feature, and prohibited-authority questions. The stricter system, Risk, venue, or runtime rule always wins.

**Depends on:** `AGT-1.00`.
**Phase-0 blockers that must already be closed:** P0.3 Workspace settings/auth/clock ownership.
**Provides:** `agentic.mandate@1`.
**Internal required capabilities:** —.
**Optional capabilities:** —.
**External prerequisites:** `workspace.settings@1 (proposed owner key)`, `workspace.auth-context@1 (proposed owner key)`.
**State:** `None`.
**Role contributions:** —.
**Primary method:** `MandateEnforcement.enforce_mandate(request)`.
**Operations:** `VALIDATE`, `CHECK_SCOPE`, `INSPECT`.
**Success/domain outcomes:** `MandateAccepted`, `MandateScopeDecision`, `MandateView`.
**Events:** —.

**Normalized donor bundle inputs**

- `app/agentic/governance/models.py`
- `app/agentic/governance/registry.py`
- `tests/agentic/unit/test_governance.py`
- `tests/agentic/usage/02_governance.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/mandate.py
app/services/agentic/enforce_mandate/README.md
app/services/agentic/enforce_mandate/__init__.py
app/services/agentic/enforce_mandate/manifest.py
app/services/agentic/enforce_mandate/config.py
app/services/agentic/enforce_mandate/feature.py
app/services/agentic/enforce_mandate/mandate_enforcement.py
tests/contracts/agentic/test_mandate.py
tests/services/agentic/enforce_mandate/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/mandate.py` with the exact capability key `agentic.mandate@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-ENFORCE_MANDATE"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `mandate_ref`, `require_signature`, `max_clock_skew_seconds`, `fail_closed_on_expiry`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Model `FirmMandate` as a strict frozen value with immutable identity, schema version, issued/effective/expiry times, principal/deployment binding, enabled features and roles, asset/account/venue/environment scopes, budgets, approval classes, and structurally forbidden authorities.
- [ ] Canonicalize and recompute the mandate digest; verify the approved signature/integrity mechanism selected in P0.3 rather than trusting a caller-supplied hash.
- [ ] Implement `VALIDATE`, `CHECK_SCOPE`, and `INSPECT` through one discriminated request union and one explicit success/refusal/failure union.
- [ ] Return the narrowest applicable decision when Workspace/System, Risk, venue, or runtime rules are stricter; never widen from defaults.
- [ ] Expose no credential, broker, order, risk-approval, kill-switch, deployment, or production-registration field in any Agentic-owned contract.

**Owned functional requirements**

- [ ] **FR-AGT-VALIDATE_MANDATE** — Validate identity, signature/integrity digest, effective interval, objectives, asset/account/environment scopes, enabled features and roles, budgets, human-action classes, and prohibited authority. Side effects: Read-only configuration and authority evaluation. Evidence: Mandate construction, integrity, expiry, scope, and clock-skew tests.
- [ ] **FR-AGT-ENFORCE_AUTHORITY_BOUNDARY** — Deny any request that attempts to grant broker credentials, order construction, risk approval, kill-switch clearing, deployment, or receiver-domain authority to Agentic or a role. Side effects: None. Evidence: Unrepresentable-field and privilege-escalation negative tests.
- [ ] **FR-AGT-FAIL_CLOSED_ON_MANDATE** — Fail closed when the mandate is absent, expired, invalid, incompatible, or narrower than the requested action; never infer permissive defaults. Side effects: Readiness publication. Evidence: Startup/readiness, degraded-state, and removal tests.

**Mandatory focused tests**

- [ ] valid/invalid signature and digest.
- [ ] missing/expired/future mandate.
- [ ] clock skew.
- [ ] narrower scope wins.
- [ ] forbidden authority fields.
- [ ] removal blocks only Agentic.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ENFORCE_MANDATE`.

**Executable usage:** `uv run python -m app.services.agentic.enforce_mandate.mandate_enforcement`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.enforce_mandate.mandate_enforcement
uv run pytest --no-cov tests/contracts/agentic/test_mandate.py tests/services/agentic/enforce_mandate/
uv run ruff format --check app/contracts/agentic/mandate.py app/services/agentic/enforce_mandate tests/contracts/agentic/test_mandate.py tests/services/agentic/enforce_mandate
uv run ruff check app/contracts/agentic/mandate.py app/services/agentic/enforce_mandate tests/contracts/agentic/test_mandate.py tests/services/agentic/enforce_mandate
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ENFORCE_MANDATE
```

**Removal acceptance:** Reject all new Agentic work. Retained evidence stays readable through its owning capabilities; deterministic safety remains unchanged.

**Proposed commit:** `feat(agentic): implement mandate enforcement`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-1.02 — `FEAT-AGT-OPERATE_RUNS` — Operations, Incidents, and Replay Validation

**Goal:** Record correlated redacted operational evidence, inspect traces, classify incidents, contain affected work, expose readiness/cost diagnostics, and validate side-effect-free replay references. This feature is deterministic and invokes no model.

**Depends on:** `AGT-1.01`.
**Phase-0 blockers that must already be closed:** P0.3 durable persistence and optional notification ownership; P0.2 event placement and state policy.
**Provides:** `agentic.operations@1`.
**Internal required capabilities:** `agentic.mandate@1`.
**Optional capabilities:** —.
**External prerequisites:** `workspace.persistence@1 (proposed owner key)`, `workspace.notifications@1 (optional proposed owner key)`.
**State:** namespace `agentic.operations`, schema version `1`, retention `RETAIN`.
**Role contributions:** —.
**Primary method:** `AgenticOperations.operate_agentic_runs(request)`.
**Operations:** `RECORD`, `INSPECT_TRACE`, `REPORT_INCIDENT`, `VALIDATE_REPLAY`, `INSPECT_READINESS`, `EXPORT`.
**Success/domain outcomes:** `OperationReceipt`, `AgenticRunTrace`, `IncidentRecord`, `ReplayValidation`, `AgenticReadinessView`, `OperationsExport`.
**Events:** `AgenticIncidentRaised`, `AgenticReadinessChanged`.

**Normalized donor bundle inputs**

- `app/agentic/operations/**`
- `app/agentic/migrations/operations.py`
- `tests/agentic/unit/test_operations.py`
- `tests/agentic/integration/test_incident_recovery.py`
- `tests/agentic/usage/21_operations.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/operations.py
app/services/agentic/operate_runs/README.md
app/services/agentic/operate_runs/__init__.py
app/services/agentic/operate_runs/manifest.py
app/services/agentic/operate_runs/config.py
app/services/agentic/operate_runs/feature.py
app/services/agentic/operate_runs/run_operations.py
app/services/agentic/operate_runs/operation_models.py
app/services/agentic/operate_runs/incident_policy.py
app/services/agentic/operate_runs/replay_validation.py
app/services/agentic/operate_runs/migrations.py
app/services/agentic/operate_runs/_store.py
tests/contracts/agentic/test_operations.py
tests/services/agentic/operate_runs/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/operations.py` with the exact capability key `agentic.operations@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-OPERATE_RUNS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `retention_days`, `max_trace_records`, `max_export_records`, `incident_dedup_window_seconds`, `replay_validation_only`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Define append-only operational records for workflow, role, model, tool, lease, human action, handoff, policy, state transition, cost, refusal, failure, cleanup, incident, replay-validation, and readiness evidence.
- [ ] Redact before persistence; persist redaction metadata and source hashes, never credentials, raw unrestricted prompts, private provider objects, or hidden reasoning.
- [ ] Build a deterministic incident matrix that maps injection, poisoning, privilege, schema, drift, budget, runaway loop, provider, sandbox, and removal incidents to required containment.
- [ ] Validate replay references and provider/feature generations without executing external side effects; the result must say whether replay is eligible, not perform replay.
- [ ] Publish bounded readiness and incident events using the event location and dispatch mode ratified in P0.2.

**Owned functional requirements**

- [ ] **FR-AGT-RECORD_OPERATIONS** — Record workflow, role, model, tool, lease, handoff, policy, state-transition, cost, refusal, failure, and cleanup evidence with correlation and causation lineage after redaction. Side effects: Append-only persistence and observational event publication. Evidence: Trace completeness, redaction, ordering, and bounded-export tests.
- [ ] **FR-AGT-CONTAIN_INCIDENTS** — Classify injection, poisoning, privilege, schema, drift, budget, runaway-loop, provider, sandbox, and removal incidents and derive deterministic containment. Side effects: Workflow cancellation/revocation request, append-only incident write. Evidence: Incident matrix, idempotency, evidence-preservation, and containment tests.
- [ ] **FR-AGT-VALIDATE_REPLAY** — Validate immutable references, profile generations, prompts, tools, policies, data, and side-effect prohibition before any replay-capable composition root runs a replay. Side effects: Append-only replay-validation write; no external side effect. Evidence: Tamper, missing-reference, generation-drift, and no-side-effect tests.
- [ ] **FR-AGT-PUBLISH_AGENTIC_READINESS** — Publish capability-level readiness and removal/degradation reasons without exposing secrets or provider internals. Side effects: Readiness event publication. Evidence: Readiness transition and provider-removal tests.

**Mandatory focused tests**

- [ ] redaction before write.
- [ ] append-only ordering.
- [ ] incident deduplication and containment.
- [ ] replay validation executes nothing.
- [ ] readiness transitions.
- [ ] restart/export bounds.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-OPERATE_RUNS`.

**Executable usage:** `uv run python -m app.services.agentic.operate_runs.run_operations`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.operate_runs.run_operations
uv run pytest --no-cov tests/contracts/agentic/test_operations.py tests/services/agentic/operate_runs/
uv run ruff format --check app/contracts/agentic/operations.py app/services/agentic/operate_runs tests/contracts/agentic/test_operations.py tests/services/agentic/operate_runs
uv run ruff check app/contracts/agentic/operations.py app/services/agentic/operate_runs tests/contracts/agentic/test_operations.py tests/services/agentic/operate_runs
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-OPERATE_RUNS
```

**Removal acceptance:** Stop Agentic work that requires mandatory audit. Preserve retained traces/incidents. Cancel subscriptions and exact callbacks; do not affect deterministic-domain audit or safety.

**Proposed commit:** `feat(agentic): implement operations, incidents, and replay validation`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-1.03 — `FEAT-AGT-REGISTER_ROLES` — Role Contribution Registry

**Goal:** Register, verify, resolve, list, enable, disable, and exactly dispose versioned role contributions and prompt artifacts. Registration does not grant eligibility or authority.

**Depends on:** `AGT-1.01`.
**Phase-0 blockers that must already be closed:** P0.4 Plugins contribution key and external-role packaging; P0.9 eligibility bootstrap.
**Provides:** `agentic.roles@1`.
**Internal required capabilities:** `agentic.mandate@1`.
**Optional capabilities:** `plugins.contributions@1 (proposed owner key)`.
**External prerequisites:** —.
**State:** `None`.
**Role contributions:** —.
**Primary method:** `RoleContributionRegistry.manage_role_contributions(request)`.
**Operations:** `REGISTER`, `UNREGISTER`, `RESOLVE`, `LIST`, `SET_ELIGIBILITY_REFERENCE`.
**Success/domain outcomes:** `RoleRegistrationReceipt`, `RoleRemovalReceipt`, `RoleResolution`, `RoleList`, `RoleEligibilityReferenceReceipt`.
**Events:** `RoleContributionRegistered`, `RoleContributionRemoved`, `RoleEligibilityReferenceChanged`.

**Normalized donor bundle inputs**

- `app/agentic/governance/**`
- `app/agentic/agents/**/prompt.md`
- `app/agentic/agents/**/agent.py`
- `tests/agentic/unit/test_governance.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/roles.py
app/services/agentic/register_roles/README.md
app/services/agentic/register_roles/__init__.py
app/services/agentic/register_roles/manifest.py
app/services/agentic/register_roles/config.py
app/services/agentic/register_roles/feature.py
app/services/agentic/register_roles/role_registry.py
app/services/agentic/register_roles/role_artifacts.py
app/services/agentic/register_roles/contributions.py
tests/contracts/agentic/test_roles.py
tests/services/agentic/register_roles/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/roles.py` with the exact capability key `agentic.roles@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-REGISTER_ROLES"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `allow_external_contributions`, `require_profile_eligibility`, `prompt_hash_algorithm`, `max_registered_roles`, `accepted_role_schema_majors`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Define `RoleManifest`, prompt artifact reference, model/tool policy references, supported task/asset classes, conflict classes, input/output schemas, refusal conditions, and evaluation reference.
- [ ] Normalize prompt line endings before hashing; recompute manifest, prompt, and composite-instruction digests at registration and resolution.
- [ ] Separate registration, enablement, and eligibility. Registration makes a role discoverable; it does not authorize invocation.
- [ ] Implement exact contribution handles/disposers. Never unregister by broad role-name scan.
- [ ] Support external role contributions only through the exact Plugins capability ratified in P0.4 and keep built-in roles package-local to their owning feature.

**Owned functional requirements**

- [ ] **FR-AGT-REGISTER_ROLE_CONTRIBUTIONS** — Register one immutable role manifest plus prompt artifact, schemas, model policy, tool declarations, limits, conflicts, refusals, and evaluation reference under a stable role ID/version. Side effects: In-memory contribution registration and exact disposer registration. Evidence: Uniqueness, schema, hash, exact-disposal, and import-time-safety tests.
- [ ] **FR-AGT-VERIFY_ROLE_ARTIFACTS** — Normalize prompt text, recompute prompt/manifest/composite digests, reject floating model aliases and undeclared tools, and prevent title-derived authority. Side effects: Read-only artifact access during mount or explicit registration. Evidence: Prompt tamper, line-ending, manifest-drift, and authority tests.
- [ ] **FR-AGT-RESOLVE_ELIGIBLE_ROLES** — Resolve only enabled, in-scope, non-conflicted roles carrying current eligibility evidence; missing evidence is not a default pass. Side effects: None. Evidence: Eligibility expiry/revocation, scope, account isolation, and deterministic ordering tests.

**Mandatory focused tests**

- [ ] prompt normalization and hash parity.
- [ ] duplicate identity/version.
- [ ] wildcards and forbidden authority.
- [ ] eligibility reference missing/expired.
- [ ] exact disposer.
- [ ] external contribution arrival/removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-REGISTER_ROLES`.

**Executable usage:** `uv run python -m app.services.agentic.register_roles.role_registry`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.register_roles.role_registry
uv run pytest --no-cov tests/contracts/agentic/test_roles.py tests/services/agentic/register_roles/
uv run ruff format --check app/contracts/agentic/roles.py app/services/agentic/register_roles tests/contracts/agentic/test_roles.py tests/services/agentic/register_roles
uv run ruff check app/contracts/agentic/roles.py app/services/agentic/register_roles tests/contracts/agentic/test_roles.py tests/services/agentic/register_roles
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-REGISTER_ROLES
```

**Removal acceptance:** Remove the role registry capability and exactly dispose all contributions registered through it. Model-dependent workflows become unready; retained operations/workflow evidence remains.

**Proposed commit:** `feat(agentic): implement role contribution registry`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-1.04 — `FEAT-AGT-GOVERN_TOOL_CALLS` — Tool Governance and Human Actions

**Goal:** Register eligible Agentic tools, issue invocation-bound capability leases, bind typed human actions, authorize every call/retry/resume, and validate/redact tool results before model exposure.

**Depends on:** `AGT-1.02`, `AGT-1.03`.
**Phase-0 blockers that must already be closed:** P0.3 authenticated principal/human-action identity; P0.5 receiver tool descriptors and read/write classes.
**Provides:** `agentic.tool-governance@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `workspace.auth-context@1 (proposed owner key)`, `receiver-owned public capability contracts`.
**State:** namespace `agentic.tool_governance`, schema version `1`, retention `RETAIN`.
**Role contributions:** —.
**Primary method:** `ToolCallGovernance.govern_tool_calls(request)`.
**Operations:** `REGISTER_TOOL`, `REQUEST_LEASE`, `AUTHORIZE_INVOCATION`, `FILTER_RESULT`, `REVOKE_LEASE`, `REQUEST_HUMAN_ACTION`, `DECIDE_HUMAN_ACTION`.
**Success/domain outcomes:** `ToolRegistrationReceipt`, `CapabilityLease`, `ToolAuthorizationDecision`, `FilteredToolResult`, `LeaseRevocationReceipt`, `HumanActionRequest`, `HumanActionDecision`.
**Events:** `CapabilityLeaseIssued`, `CapabilityLeaseRevoked`, `HumanActionRequested`, `HumanActionDecided`.

**Normalized donor bundle inputs**

- `app/agentic/permissions/**`
- `tests/agentic/unit/test_permissions.py`
- `tests/agentic/integration/test_tool_permissions.py`
- `tests/agentic/usage/05_permissions.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/tool_governance.py
app/services/agentic/govern_tool_calls/README.md
app/services/agentic/govern_tool_calls/__init__.py
app/services/agentic/govern_tool_calls/manifest.py
app/services/agentic/govern_tool_calls/config.py
app/services/agentic/govern_tool_calls/feature.py
app/services/agentic/govern_tool_calls/tool_governance.py
app/services/agentic/govern_tool_calls/tool_registry.py
app/services/agentic/govern_tool_calls/capability_leases.py
app/services/agentic/govern_tool_calls/human_actions.py
app/services/agentic/govern_tool_calls/result_filter.py
app/services/agentic/govern_tool_calls/migrations.py
app/services/agentic/govern_tool_calls/_store.py
tests/contracts/agentic/test_tool_governance.py
tests/services/agentic/govern_tool_calls/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/tool_governance.py` with the exact capability key `agentic.tool-governance@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-GOVERN_TOOL_CALLS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `default_lease_ttl_seconds`, `max_lease_ttl_seconds`, `max_calls_per_lease`, `result_max_bytes`, `allowed_permission_classes`, `human_action_required_classes`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Define stable `ToolDescriptor` records with capability/version, request/result schemas, side-effect class, scope model, egress class, cost model, and approval policy.
- [ ] Issue capability leases binding principal, role, workflow/run, exact request hash, capability generation, scope, environment, side-effect class, egress, call/cost ceilings, issue/expiry, nonce, policy version, and exact human action when required.
- [ ] Reauthorize immediately before every invocation, retry, resumed call, or changed provider generation; a denial must prove the receiver was never invoked.
- [ ] Filter every returned result for schema, size, redaction, provenance, resource scope, injection classification, and observed cost before any model sees it.
- [ ] Make broker mutation, order, risk approval, kill-switch clear, mandate override, credential, unrestricted shell/network, and deployment tools structurally unregistrable.

**Owned functional requirements**

- [ ] **FR-AGT-REGISTER_AGENTIC_TOOLS** — Register only tools whose stable name/version, receiver capability, schemas, permission class, environments, side effects, idempotency, cost, timeout, and result trust are declared. Side effects: Contribution registration and exact disposal. Evidence: Forbidden-class, duplicate, incomplete declaration, and removal tests.
- [ ] **FR-AGT-ISSUE_CAPABILITY_LEASES** — Bind a lease to principal, role/version, workflow/run, exact request hash, receiver capability/version, scope, environment, call/cost ceilings, issue/expiry, nonce, policy, and optional human decision. Side effects: Append-only lease write and nonce reservation. Evidence: Forgery, replay, expiry, scope, budget, and object-mutation tests.
- [ ] **FR-AGT-ENFORCE_TOOL_INVOCATIONS** — Reauthorize immediately before every invocation, retry, and resumed call; a denied call never reaches the receiver. Side effects: Receiver call only after authorization; audit write. Evidence: No-fallthrough, retry, resume, revocation, and race tests.
- [ ] **FR-AGT-FILTER_TOOL_RESULTS** — Validate schema, resource scope, provenance, size, redaction, injection classification, and cost before a result enters model context. Side effects: Result filtering and audit write. Evidence: Poisoned, oversized, wrong-scope, secret-bearing, and malformed-result tests.
- [ ] **FR-AGT-BIND_TYPED_HUMAN_ACTIONS** — Represent clarification, scope amendment, tool, compute, holdout, staged-artifact, receiver-handoff, rejection, and cancellation as exact object-bound expiring single-use actions. Side effects: Human-action persistence and decision publication. Evidence: Action/object mismatch, replay, expiry, and identity tests.

**Mandatory focused tests**

- [ ] forged/replayed/expired approval.
- [ ] request hash mutation.
- [ ] retry/resume reauthorization.
- [ ] denied call never invoked.
- [ ] result injection/oversize/redaction.
- [ ] forbidden tool classes.
- [ ] lease revocation on removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-GOVERN_TOOL_CALLS`.

**Executable usage:** `uv run python -m app.services.agentic.govern_tool_calls.tool_governance`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.govern_tool_calls.tool_governance
uv run pytest --no-cov tests/contracts/agentic/test_tool_governance.py tests/services/agentic/govern_tool_calls/
uv run ruff format --check app/contracts/agentic/tool_governance.py app/services/agentic/govern_tool_calls tests/contracts/agentic/test_tool_governance.py tests/services/agentic/govern_tool_calls
uv run ruff check app/contracts/agentic/tool_governance.py app/services/agentic/govern_tool_calls tests/contracts/agentic/test_tool_governance.py tests/services/agentic/govern_tool_calls
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-GOVERN_TOOL_CALLS
```

**Removal acceptance:** Revoke every outstanding lease, dispose tool registrations, stop all new Agentic tool/receiver calls, and preserve used/denied/expired lease evidence.

**Proposed commit:** `feat(agentic): implement tool governance and human actions`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-1.05 — `FEAT-AGT-INVOKE_MODELS` — Provider-Neutral Model Invocation

**Goal:** Execute one structured evaluated model invocation through a replaceable provider port while pinning role, prompt, profile, schemas, limits, privacy, region, and provenance. Silent substitution is prohibited.

**Depends on:** `AGT-1.02`, `AGT-1.03`.
**Phase-0 blockers that must already be closed:** P0.4 model-runtime provider contract and ADK packaging; P0.9 bootstrap evaluation policy.
**Provides:** `agentic.model-inference@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `plugins.model-runtime@1 (proposed provider key)`, `workspace.secret-resolution@1 (composition-only opaque references)`.
**State:** `None`.
**Role contributions:** —.
**Primary method:** `ModelInference.invoke_model(request)`.
**Operations:** `INVOKE`.
**Success/domain outcomes:** `ModelInvocationSuccess`, `ModelInvocationRefusal`.
**Events:** `ModelInvocationStarted`, `ModelInvocationCompleted`, `ModelInvocationRefused`.

**Normalized donor bundle inputs**

- `app/agentic/runtime/**`
- `tests/agentic/unit/test_adk_runtime.py`
- `tests/agentic/integration/test_model_upgrade.py`
- `tests/agentic/usage/03_runtime.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/model_inference.py
app/services/agentic/invoke_models/README.md
app/services/agentic/invoke_models/__init__.py
app/services/agentic/invoke_models/manifest.py
app/services/agentic/invoke_models/config.py
app/services/agentic/invoke_models/feature.py
app/services/agentic/invoke_models/model_inference.py
app/services/agentic/invoke_models/model_profiles.py
app/services/agentic/invoke_models/provider_port.py
app/services/agentic/invoke_models/fallback_policy.py
tests/contracts/agentic/test_model_inference.py
tests/services/agentic/invoke_models/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/model_inference.py` with the exact capability key `agentic.model-inference@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-INVOKE_MODELS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `allowed_profile_ids`, `default_timeout_seconds`, `max_input_tokens`, `max_output_tokens`, `max_cost_per_call`, `allow_evaluated_fallbacks`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Define a provider-neutral model-runtime port; keep provider/framework types, clients, credentials, and errors behind the adapter boundary.
- [ ] Pin provider, exact model identifier/version, prompt/role/schema/tool policy, privacy, region, retention, token/cost/latency ceilings, and evaluated fallback candidates.
- [ ] Validate structured output against the target schema and convert invalid, truncated, substituted, unsafe, or over-budget outcomes into typed refusal/failure.
- [ ] Supply a deterministic in-repository fake provider for tests and usage. Do not require network access or paid model calls in normal tests.
- [ ] Implement Google ADK only in the P0.4-approved optional provider package/extra; remove stale references to deleted `app/agentic/runtime/adk.py` and prohibit ADK objects in Agentic contracts/state.

**Owned functional requirements**

- [ ] **FR-AGT-PIN_MODEL_INVOCATIONS** — Pin provider, model, profile digest, role/version, prompt/composite hash, input/output schemas, context digest, tool declarations, region, retention, and timeout before invocation. Side effects: External model call through injected provider. Evidence: Profile pin, schema, privacy, region, and provenance tests.
- [ ] **FR-AGT-ENFORCE_MODEL_BUDGETS** — Enforce input/output token, latency, retry, and cost ceilings before and after each call and reconcile provider-reported usage. Side effects: Model call and operations write. Evidence: Preflight, overrun, missing-usage, non-finite-cost, and timeout tests.
- [ ] **FR-AGT-REFUSE_SILENT_MODEL_SUBSTITUTION** — Reject provider/model/profile drift; permit fallback only to an explicitly declared independently eligible profile for the same workflow risk class. Side effects: Optional evaluated fallback call. Evidence: Alias, drift, fallback equivalence, and provider-removal tests.
- [ ] **FR-AGT-CONTAIN_MODEL_OUTPUT** — Parse only the declared strict output schema, map invalid content to refusal/failure, and never expose provider objects or hidden reasoning as canonical output. Side effects: None beyond trace write. Evidence: Invalid-schema, extraneous-field, provider-leak, and hidden-reasoning tests.

**Mandatory focused tests**

- [ ] profile pin/floating alias.
- [ ] credential isolation.
- [ ] structured output validation.
- [ ] token/cost/timeout ceilings.
- [ ] silent substitution.
- [ ] explicit evaluated fallback.
- [ ] provider replacement/removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-INVOKE_MODELS`.

**Executable usage:** `uv run python -m app.services.agentic.invoke_models.model_inference`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.invoke_models.model_inference
uv run pytest --no-cov tests/contracts/agentic/test_model_inference.py tests/services/agentic/invoke_models/
uv run ruff format --check app/contracts/agentic/model_inference.py app/services/agentic/invoke_models tests/contracts/agentic/test_model_inference.py tests/services/agentic/invoke_models
uv run ruff check app/contracts/agentic/model_inference.py app/services/agentic/invoke_models tests/contracts/agentic/test_model_inference.py tests/services/agentic/invoke_models
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-INVOKE_MODELS
```

**Removal acceptance:** Refuse all new model-dependent work. Close provider clients through managed contexts; deterministic records and non-model capabilities remain.

**Proposed commit:** `feat(agentic): implement provider-neutral model invocation`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.
