# Agentic Rebuild — Phase 1 Foundation

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Authority:** `app/services/agentic/README.md`, current owner-domain contracts, and `docs/dev/feature_implementation_pipeline.md`  
> **Prerequisite:** `AGT-0.GATE`

## Purpose

Establish the provider-neutral public contract base and the five authority/invocation capabilities on which every later Agentic feature depends. No task in this phase may restore the old `app/agentic/` facade, expose a provider object, create a direct Brokers edge, or let a role infer authority from its title.

## Phase exit

- `app/contracts/agentic/` contains the ratified shared primitives and five capability modules.
- Each implemented feature has `README.md`, pure `__init__.py`, immutable `manifest.py`, strict `config.py`, lifecycle `feature.py`, focused modules, one primary-module usage harness, entry point, import boundary, tests, and removal evidence.
- Mandate, audit/incident, role registry, tool lease, and model invocation boundaries are independently removable and replaceable.
- Every proposed owner key from the architecture has been replaced by an exact ratified capability key.

---

## AGT-1.00 — Agentic public contract foundation

**Goal:** create shared business-neutral records; this is not a mountable feature.

**Allowed paths**

```text
app/contracts/agentic/README.md
app/contracts/agentic/__init__.py
app/contracts/agentic/common.py
app/contracts/agentic/errors.py              # only for meaningful Agentic errors
app/contracts/<ratified-event-location>/**
tests/contracts/agentic/test_common.py
tests/contracts/agentic/test_errors.py
app/contracts/README.md
```

**Implementation**

- [ ] Reuse current common UUID, UTC time, Decimal, bounded string, JSON, and content-hash primitives; do not create Agentic aliases for existing semantics.
- [ ] Add only records used by at least two capabilities: task/run/principal/scope references, deadlines, budgets and usage, provenance, content/evidence references, warnings, refusal/failure, role/prompt/model references, checkpoints/terminal reasons, uncertainty, and reliability.
- [ ] Use strict frozen Pydantic v2 models, forbid unknown fields, and make serialization deterministic.
- [ ] Ratify one canonical digest algorithm and test timezone, Decimal, mapping order, set/tuple order, optional values, and mutation behavior.
- [ ] Exclude credentials, provider clients, raw unrestricted prompts, hidden reasoning, database rows, and receiver-owned result models.
- [ ] Add construction, equality, immutability, JSON round-trip, digest, and compatibility tests.

**Checks**

```powershell
uv run pytest --no-cov tests/contracts/agentic/test_common.py tests/contracts/agentic/test_errors.py
uv run ruff format --check app/contracts/agentic tests/contracts/agentic
uv run ruff check app/contracts/agentic tests/contracts/agentic
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
```

**Commit:** `feat(agentic): establish public contract foundation`

**Rollback:** revert before consumers land. After consumers exist, breaking changes require a new major contract or explicit compatibility window.

---

## AGT-1.01 — `FEAT-AGT-ENFORCE_MANDATE`

**Provides:** `agentic.mandate@1`  
**Depends on:** `AGT-1.00`; Phase-0 Workspace/System settings, authenticated principal, clock, signature, and secret-reference decisions.  
**State:** none.  
**Primary module:** `mandate_enforcement.py`  
**Operations:** `VALIDATE`, `CHECK_SCOPE`, `INSPECT`.

**Donor evidence to normalize**

```text
app/agentic/governance/models.py
app/agentic/governance/registry.py
tests/agentic/unit/test_governance.py
tests/agentic/usage/02_governance.py
```

**Production paths**

```text
app/contracts/agentic/mandate.py
app/services/agentic/enforce_mandate/{README.md,__init__.py,manifest.py,config.py,feature.py,mandate_enforcement.py}
tests/contracts/agentic/test_mandate.py
tests/services/agentic/enforce_mandate/**
pyproject.toml
.importlinter
```

**Config keys**

```text
mandate_ref
require_signature
max_clock_skew_seconds
fail_closed_on_expiry
```

**Implementation**

- [ ] Define an immutable signed `FirmMandate` carrying identity/version, issuance/effective/expiry time, principal/deployment binding, feature and role enablement, asset/account/venue/environment scope, budgets, human-action classes, and prohibited authorities.
- [ ] Recompute the canonical digest and verify the ratified signature mechanism; never trust a supplied digest.
- [ ] Return the narrowest decision when Workspace/System, Risk, venue, runtime, or mandate rules differ.
- [ ] Make broker credentials, order creation, Risk approval, kill-switch clearing, deployment, production registration, and receiver authority structurally unrepresentable.
- [ ] Missing, future, expired, incompatible, unsigned, tampered, or narrower-than-requested mandates refuse deterministically.
- [ ] Mount publishes only after validation and leaves no state/effect on failure.

**Tests**

- valid/tampered signature and digest;
- absent/future/expired mandate and clock skew;
- narrower scope wins and unknown role/feature fails;
- forbidden authority is unrepresentable;
- required dependency loss withdraws Agentic readiness but leaves deterministic domains active;
- strict config, failed mount rollback, repeated close, 100 churn cycles, replacement, and physical removal.

**Usage:** `uv run python -m app.services.agentic.enforce_mandate.mandate_enforcement`

**Commit:** `feat(agentic): implement mandate enforcement`

**Removal:** reject all new Agentic work; deterministic startup and safety remain unchanged.

---

## AGT-1.02 — `FEAT-AGT-OPERATE_RUNS`

**Provides:** `agentic.operations@1`  
**Requires:** `agentic.mandate@1`; ratified persistence/clock/redaction/ID operations.  
**State:** `agentic.operations`, schema v1, `RETAIN`.  
**Primary module:** `run_operations.py`  
**Operations:** `RECORD`, `INSPECT_TRACE`, `REPORT_INCIDENT`, `VALIDATE_REPLAY`, `INSPECT_READINESS`, `EXPORT`.

**Donor evidence to normalize**

```text
app/agentic/operations/**
app/agentic/migrations/operations.py
tests/agentic/unit/test_operations.py
tests/agentic/integration/test_incident_recovery.py
tests/agentic/usage/21_operations.py
```

**Production paths**

```text
app/contracts/agentic/operations.py
app/services/agentic/operate_runs/
  README.md __init__.py manifest.py config.py feature.py
  run_operations.py operation_models.py incident_policy.py replay_validation.py
  migrations.py _store.py
tests/contracts/agentic/test_operations.py
tests/services/agentic/operate_runs/**
```

**Config keys**

```text
retention_days
max_trace_records
max_export_records
incident_dedup_window_seconds
replay_validation_only
```

**Implementation**

- [ ] Append redacted workflow, role, model, tool, lease, human action, handoff, policy, transition, cost, refusal, failure, cleanup, incident, replay-validation, and readiness evidence.
- [ ] Persist redaction metadata and source hashes; never persist credentials, provider objects, unrestricted prompts, or hidden reasoning.
- [ ] Derive containment from a deterministic incident matrix covering injection, poisoning, privilege, schema, drift, budget, runaway work, provider, sandbox, and removal incidents.
- [ ] Validate immutable replay references, generations, profiles, prompts, tools, policies, data, and zero-side-effect requirements; do not execute a replay.
- [ ] Publish bounded incident/readiness events using the Phase-0 event location and mode.
- [ ] Own additive strict migrations, bounded reconstruction/export, deduplication/idempotency, retention, and legacy import.

**Tests**

- redact-before-write and secret scans;
- append-only ordering, correlation/causation, bounded export;
- incident matrix, deduplication, idempotent containment, evidence preservation;
- replay tamper/missing/generation drift and `executed == false`;
- migration checksum/order/rollback, restart reconstruction, retention/export;
- dependency loss, replacement, 100 churn cycles, retained-state removal, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.operate_runs.run_operations`

**Commit:** `feat(agentic): implement operations, incidents, and replay validation`

**Removal:** stop work requiring mandatory Agentic audit, preserve committed evidence, and leave deterministic audit/safety unaffected.

---

## AGT-1.03 — `FEAT-AGT-REGISTER_ROLES`

**Provides:** `agentic.roles@1`  
**Requires:** `agentic.mandate@1`; exact Plugins contribution capability if Phase 0 retains external contribution support.  
**State:** none.  
**Primary module:** `role_registry.py`  
**Operations:** `REGISTER`, `UNREGISTER`, `RESOLVE`, `LIST`, `SET_ELIGIBILITY_REFERENCE`.

**Donor evidence to normalize**

```text
app/agentic/governance/**
app/agentic/agents/**/prompt.md
app/agentic/agents/**/agent.py
tests/agentic/unit/test_governance.py
```

**Production paths**

```text
app/contracts/agentic/roles.py
app/services/agentic/register_roles/
  README.md __init__.py manifest.py config.py feature.py
  role_registry.py role_artifacts.py contributions.py
tests/contracts/agentic/test_roles.py
tests/services/agentic/register_roles/**
```

**Config keys**

```text
max_registered_roles
allowed_manifest_versions
require_prompt_hash
allow_external_role_contributions
```

**Implementation**

- [ ] Define `RoleManifest`, prompt reference, supported task/asset classes, input/output schemas, model policy, tool IDs, conflict classes, evaluation reference, and refusal conditions.
- [ ] Normalize prompt line endings/encoding and verify prompt, manifest, and composite-instruction hashes before registration or model construction.
- [ ] Reject duplicate identity/version, wildcard scope, forbidden permission/authority class, unknown owning feature, unpinned prompt, missing evaluation reference, and digest mismatch.
- [ ] Keep registration distinct from enablement and eligibility.
- [ ] Return an exact registration/removal handle; teardown must never remove by broad name scan.
- [ ] Support external contributions only through the ratified Plugins contract and identical validation.

**Tests**

- prompt portability/hash mutation;
- duplicate/collision/unknown-owner/wildcard/forbidden authority;
- registered-but-ineligible and revoked eligibility;
- exact disposer and unrelated-contribution preservation;
- provider arrival/removal if external contributions are optional;
- failed mount, replacement, churn, and physical removal.

**Usage:** `uv run python -m app.services.agentic.register_roles.role_registry`

**Commit:** `feat(agentic): implement role contribution registry`

**Removal:** exactly unregister all current-generation role contributions; model-dependent workflows become unready without deleting retained run evidence.

---

## AGT-1.04 — `FEAT-AGT-GOVERN_TOOL_CALLS`

**Provides:** `agentic.tool-governance@1`  
**Requires:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.operations@1`, ratified principal/clock/persistence.  
**State:** `agentic.tool_governance`, schema v1, `RETAIN`.  
**Primary module:** `tool_governance.py`  
**Operations:** `REGISTER_TOOL`, `REQUEST_LEASE`, `AUTHORIZE_INVOCATION`, `FILTER_RESULT`, `REVOKE_LEASE`, `REQUEST_HUMAN_ACTION`, `DECIDE_HUMAN_ACTION`.

**Donor evidence to normalize**

```text
app/agentic/permissions/**
tests/agentic/unit/test_permissions.py
tests/agentic/integration/test_tool_permissions.py
tests/agentic/usage/05_permissions.py
```

**Production paths**

```text
app/contracts/agentic/tool_governance.py
app/services/agentic/govern_tool_calls/
  README.md __init__.py manifest.py config.py feature.py
  tool_governance.py tool_registry.py capability_leases.py
  human_actions.py result_filtering.py migrations.py _store.py
tests/contracts/agentic/test_tool_governance.py
tests/services/agentic/govern_tool_calls/**
```

**Config keys**

```text
max_registered_tools
max_active_leases_per_run
default_lease_ttl_seconds
max_result_bytes
approval_ttl_seconds
allowed_read_side_effect_classes
```

**Implementation**

- [ ] Tool descriptors bind owner/capability version, exact request/result schemas, side-effect and egress classes, scope model, observed-cost model, and approval policy.
- [ ] Capability leases bind principal, role/version, workflow/run, tool/capability, exact request/object hash, scope, environment, side-effect/egress, call/cost ceilings, issue/expiry, nonce, policy, and approval.
- [ ] Reauthorize immediately before every invocation, retry, and resumed call; denial must prove the receiver was never invoked.
- [ ] Validate/redact/filter returned schema, size, provenance, resource scope, injection status, and observed cost before any model sees it.
- [ ] Implement typed human actions: clarify, amend scope, approve tool, approve compute, approve holdout, approve staged artifact, approve receiver handoff, reject, and cancel.
- [ ] Bind approvals to exact object hash, action, scope, environment, principal, policy, expiry, signature/authentication, and single-use nonce.
- [ ] Make broker mutation, order, Risk approval, kill-switch clear, mandate override, production deployment, credential, unrestricted shell, and unrestricted network tools structurally unregistrable.

**Tests**

- full authorization matrix;
- forged/replayed/expired/wrong-object/wrong-environment approval;
- request mutation, retry/resume reauthorization, call/cost exhaustion;
- denial-never-invokes receiver;
- result schema/size/redaction/scope/injection/cost filtering;
- migration/restart/nonces/concurrency;
- lease revocation on removal/replacement and physical deletion.

**Usage:** `uv run python -m app.services.agentic.govern_tool_calls.tool_governance`

**Commit:** `feat(agentic): implement tool governance and human actions`

**Removal:** stop issuance, revoke every active lease, cancel pending actions, dispose tool contributions exactly, and preserve immutable use/decision evidence.

---

## AGT-1.05 — `FEAT-AGT-INVOKE_MODELS`

**Provides:** `agentic.model-inference@1`  
**Requires:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.operations@1`, exact provider-selection and secret-reference capabilities.  
**Optional:** `agentic.tool-governance@1` only for profiles that expose custom tools.  
**State:** none.  
**Primary module:** `model_invocation.py`  
**Operation:** `INVOKE`.

**Donor evidence to normalize**

```text
app/agentic/runtime/**
tests/agentic/unit/test_adk_runtime.py
tests/agentic/unit/test_runtime_gateway.py
tests/agentic/integration/test_model_upgrade.py
tests/agentic/usage/03_runtime.py
```

**Production paths**

```text
app/contracts/agentic/model_inference.py
app/services/agentic/invoke_models/
  README.md __init__.py manifest.py config.py feature.py
  model_invocation.py profile_validation.py provider_port.py provider_selection.py
tests/contracts/agentic/test_model_inference.py
tests/services/agentic/invoke_models/**
pyproject.toml / uv.lock only when Phase-0 provider packaging requires them
```

**Config keys**

```text
max_input_bytes
max_output_bytes
max_tokens_per_call
max_cost_per_call
invocation_timeout_seconds
allow_evaluated_fallback
```

**Implementation**

- [ ] `ModelProfile` pins provider, immutable model ID/version, structured-output mode, allowed tools, privacy/region/retention, latency, token/cost ceilings, fallback list, and eligibility reference; reject floating aliases.
- [ ] Resolve opaque credentials only inside the selected provider adapter; never include them in contracts, logs, events, prompts, or state.
- [ ] Invoke through a provider-neutral port and validate the exact output schema before returning.
- [ ] Record requested and observed provider/model identity, tokens, cost, latency, finish status, schema result, prompt/role/profile generation, and substitution evidence.
- [ ] Refuse silent substitution. Explicit fallback is allowed only to an independently eligible profile equivalent for schema, tools, privacy, region, safety, cost, and workflow risk.
- [ ] Keep Google ADK and any provider SDK behind replaceable provider features; no framework object crosses the capability or persistence boundary.
- [ ] Supply a deterministic offline provider for tests and usage; normal tests make no paid/network call.

**Tests**

- floating alias and silent substitution;
- credential isolation/redaction;
- schema-invalid/oversize/timeout/cost/token bounds;
- explicit evaluated fallback and no-fallback refusal;
- provider ambiguity, explicit selection, arrival/removal, health failure, shadow replacement, rollback;
- lazy provider imports, client/task cleanup, 100 churn cycles, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.invoke_models.model_invocation`

**Commit:** `feat(agentic): implement provider-neutral model invocation`

**Removal:** cancel/drain managed invocations, close provider clients, and make model-dependent workflows unready unless composition has an independently evaluated compatible replacement.

---

## Phase 1 verification gate

- [ ] All five capability contracts and shared primitives pass compatibility tests.
- [ ] No feature implementation imports a sibling feature or provider SDK outside its provider adapter.
- [ ] No capability can express direct broker/order/Risk approval/kill-switch/deployment authority.
- [ ] Stateful features pass migration, restart, retention, export, and retained-state removal evidence.
- [ ] Role/tool/provider contributions have exact disposers and no stale generation survives replacement.
- [ ] Each feature passes its primary-module harness and targeted physical-removal command.
- [ ] Targeted Ruff, strict mypy, Import Linter, architecture, documentation validation, and tests pass.

The full repository gate remains reserved for Phase 7 final integration.
