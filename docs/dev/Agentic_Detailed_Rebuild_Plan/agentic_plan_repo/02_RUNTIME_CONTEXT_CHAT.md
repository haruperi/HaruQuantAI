# Agentic Rebuild — Phase 2 Runtime, Context, Memory, Evaluation, and Chat Bot

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

### AGT-2.06 — `FEAT-AGT-RUN_WORKFLOWS` — Durable Workflow Orchestration

**Goal:** Submit, route, checkpoint, pause, resume, cancel, expire, reconcile, drain, and terminate bounded Agentic workflows while applying deterministic risk/value escalation and backpressure.

**Depends on:** `AGT-1.02`, `AGT-1.03`.
**Phase-0 blockers that must already be closed:** P0.3 durable persistence/worker-admission boundary; P0.2 terminal state/event conventions.
**Provides:** `agentic.workflows@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.operations@1`.
**Optional capabilities:** `agentic.tool-governance@1`, `agentic.model-inference@1`, `agentic.context@1`, `agentic.memory@1`.
**External prerequisites:** `workspace.persistence@1 (proposed owner key)`, `workspace.worker-admission@1 (proposed owner key)`.
**State:** namespace `agentic.workflows`, schema version `1`, retention `RETAIN`.
**Role contributions:** `research_planner`, `artifact_planner`.
**Primary method:** `AgenticWorkflowRunner.run_agentic_workflows(request)`.
**Operations:** `SUBMIT`, `RESUME`, `CANCEL`, `EXPIRE`, `INSPECT`, `DRAIN`.
**Success/domain outcomes:** `WorkflowAccepted`, `WorkflowRun`, `WorkflowCancellationReceipt`, `WorkflowExpiryReceipt`, `WorkflowDrainReceipt`.
**Events:** `WorkflowStateChanged`, `WorkflowProgressed`, `WorkflowWaitingForHuman`, `WorkflowTerminated`.

**Normalized donor bundle inputs**

- `app/agentic/orchestration/**`
- `app/agentic/migrations/workflow.py`
- `tests/agentic/unit/test_orchestration.py`
- `tests/agentic/integration/test_durable_runtime.py`
- `tests/agentic/usage/04_orchestration.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/workflows.py
app/services/agentic/run_workflows/README.md
app/services/agentic/run_workflows/__init__.py
app/services/agentic/run_workflows/manifest.py
app/services/agentic/run_workflows/config.py
app/services/agentic/run_workflows/feature.py
app/services/agentic/run_workflows/workflow_runtime.py
app/services/agentic/run_workflows/workflow_models.py
app/services/agentic/run_workflows/workflow_registry.py
app/services/agentic/run_workflows/routing.py
app/services/agentic/run_workflows/state_machine.py
app/services/agentic/run_workflows/migrations.py
app/services/agentic/run_workflows/_store.py
app/services/agentic/run_workflows/roles/research_planner/role.json
app/services/agentic/run_workflows/roles/research_planner/prompt.md
app/services/agentic/run_workflows/roles/artifact_planner/role.json
app/services/agentic/run_workflows/roles/artifact_planner/prompt.md
tests/contracts/agentic/test_workflows.py
tests/services/agentic/run_workflows/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/workflows.py` with the exact capability key `agentic.workflows@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-RUN_WORKFLOWS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_active_runs`, `max_queue_depth`, `max_steps`, `max_fanout`, `max_retries`, `default_deadline_seconds`, `drain_timeout_seconds`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Implement immutable workflow definitions, node/transition records, expected-version state transitions, idempotency keys, checkpoints, waits, budgets, deadlines, retries, cancellation, expiry, drain, and terminal reasons.
- [ ] Persist the initial checkpoint before starting asynchronous work; terminal runs never resume under the same run identity.
- [ ] Keep model, tool, context, and memory dependencies optional at feature mount but mandatory for workflow definitions that name them; expose precise readiness when they are missing.
- [ ] Implement deterministic adaptive escalation: deterministic baseline, one specialist, challenger when material, council only when unresolved value exceeds cost/risk.
- [ ] Register Research Planner and Artifact Planner role artifacts through `agentic.roles@1` with exact disposal; planners may propose bounded graphs but cannot widen limits or authorize receiver actions.
- [ ] Use `context.spawn()` for every managed run/worker and apply explicit queue depth and backpressure.

**Owned functional requirements**

- [ ] **FR-AGT-SUBMIT_WORKFLOWS** — Validate mandate, identity, idempotency, workflow/version, inputs, budgets, deadline, and required capability readiness; persist the initial run and checkpoint before execution. Side effects: Transactional persistence and admission reservation. Evidence: Idempotency, initial-commit, readiness, and queue-bound tests.
- [ ] **FR-AGT-CHECKPOINT_WORKFLOWS** — Persist expected-version checkpoints at declared boundaries and resume only the same workflow/node/profile generations with reconciled reservations. Side effects: Transactional checkpoint/write and managed task scheduling. Evidence: Crash, stale revision, changed graph, changed provider, and resume tests.
- [ ] **FR-AGT-BOUND_ADAPTIVE_ESCALATION** — Start with deterministic evidence, add one specialist only when interpretation is needed, add challenge on material uncertainty, and use councils only when policy/value warrants. Side effects: Model/tool calls through other capabilities. Evidence: Routing matrix, budget, materiality, no-unnecessary-council, and ablation tests.
- [ ] **FR-AGT-TERMINATE_WORKFLOWS** — Use explicit terminal states succeeded, refused, failed, cancelled, or expired; a terminal run never resumes under the same identity. Side effects: Transactional state transition and events. Evidence: State-machine, cancellation, deadline, drain, and terminal-resume tests.
- [ ] **FR-AGT-APPLY_BACKPRESSURE** — Bound active runs, queues, fan-out, loops, retries, provider/tool concurrency, and waits; overload is visible and never silently drops work. Side effects: Admission rejection or queued state. Evidence: Load, fairness, starvation, queue, and provider-concurrency tests.

**Mandatory focused tests**

- [ ] idempotent submit.
- [ ] initial checkpoint transaction.
- [ ] CAS conflict.
- [ ] restart/resume.
- [ ] bounded loop/fanout/retry.
- [ ] queue backpressure.
- [ ] cancellation/expiry/drain.
- [ ] optional dependency arrival/removal.
- [ ] planner authority negatives.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-RUN_WORKFLOWS`.

**Executable usage:** `uv run python -m app.services.agentic.run_workflows.workflow_runtime`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.run_workflows.workflow_runtime
uv run pytest --no-cov tests/contracts/agentic/test_workflows.py tests/services/agentic/run_workflows/
uv run ruff format --check app/contracts/agentic/workflows.py app/services/agentic/run_workflows tests/contracts/agentic/test_workflows.py tests/services/agentic/run_workflows
uv run ruff check app/contracts/agentic/workflows.py app/services/agentic/run_workflows tests/contracts/agentic/test_workflows.py tests/services/agentic/run_workflows
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-RUN_WORKFLOWS
```

**Removal acceptance:** Stop intake; deterministically cancel or drain active runs; checkpoint affected work; dispose role contributions and subscriptions; preserve terminal evidence.

**Proposed commit:** `feat(agentic): implement durable workflow orchestration`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-2.07 — `FEAT-AGT-ASSEMBLE_CONTEXT` — Point-in-Time Context Assembly

**Goal:** Select bounded point-in-time evidence through scope, schema, availability, trust, licensing, freshness, revision, deduplication, contradiction, injection, relevance, and token-budget filters while structurally separating instructions from evidence.

**Depends on:** `AGT-1.02`, `AGT-1.04`.
**Phase-0 blockers that must already be closed:** P0.5 exact evidence capability registry; P0.8 WorkspaceContextSnapshot ownership.
**Provides:** `agentic.context@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.tool-governance@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `read-only evidence capabilities from owning domains`.
**State:** `None`.
**Role contributions:** —.
**Primary method:** `AgenticContextAssembly.assemble_agentic_context(request)`.
**Operations:** `ASSEMBLE`, `INSPECT_EXCLUSIONS`.
**Success/domain outcomes:** `AgenticContextBundle`, `ContextExclusionReport`.
**Events:** —.

**Normalized donor bundle inputs**

- `app/agentic/context_memory/context.py`
- `app/agentic/context_memory/models.py`
- `tests/agentic/unit/test_context_memory.py`
- `tests/agentic/integration/test_research_council.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/context.py
app/services/agentic/assemble_context/README.md
app/services/agentic/assemble_context/__init__.py
app/services/agentic/assemble_context/manifest.py
app/services/agentic/assemble_context/config.py
app/services/agentic/assemble_context/feature.py
app/services/agentic/assemble_context/context_assembly.py
app/services/agentic/assemble_context/context_filters.py
app/services/agentic/assemble_context/context_budget.py
app/services/agentic/assemble_context/injection_classification.py
tests/contracts/agentic/test_context.py
tests/services/agentic/assemble_context/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/context.py` with the exact capability key `agentic.context@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-ASSEMBLE_CONTEXT"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_items`, `max_bytes`, `max_tokens`, `default_freshness_seconds`, `allowed_trust_levels`, `require_license`, `deduplication_algorithm`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Define context requests that pin task, principal, objective, asset/account/session scope, observation time, availability cutoff, required/optional evidence classes, and output/token limits.
- [ ] Apply filters in a deterministic order: scope, schema compatibility, availability time, licensing, trust, freshness, revision, deduplication, contradiction, injection, relevance, redaction, and size.
- [ ] Represent trusted instructions and untrusted evidence in separate fields. Page text, memory, retrieved documents, and peer messages can never occupy an instruction slot.
- [ ] Treat UI page/widget context as orientation only; refresh material prices, metrics, states, and results from the owning capability before producing evidence claims.
- [ ] Return every exclusion with a stable reason; fail on missing required evidence and expose explicit partial coverage for optional evidence.

**Owned functional requirements**

- [ ] **FR-AGT-ASSEMBLE_POINT_IN_TIME_CONTEXT** — Select only evidence available at the task observation instant and bind owner, record/version, content hash, observed/available times, trust, licence, scope, and freshness. Side effects: Read-only receiver calls through governed tools. Evidence: Look-ahead, revision, licensing, scope, freshness, and missing-evidence tests.
- [ ] **FR-AGT-SEPARATE_EVIDENCE_FROM_INSTRUCTIONS** — Place system/role instructions, trusted task input, untrusted evidence, peer messages, and memory in structurally distinct fields; evidence can never occupy an instruction slot. Side effects: Deterministic filtering. Evidence: Prompt-, memory-, peer-, and tool-injection tests.
- [ ] **FR-AGT-REPORT_CONTEXT_EXCLUSIONS** — Return deterministic exclusion codes for stale, unlicensed, duplicate, irrelevant, poisoned, over-budget, wrong-scope, or incompatible evidence. Side effects: Operations evidence write. Evidence: Exclusion completeness, deterministic ordering, and partial-coverage tests.
- [ ] **FR-AGT-BOUND_CONTEXT_SIZE** — Apply stable item, byte, token, per-source, and priority limits without allowing a model or caller to widen them. Side effects: None. Evidence: Budget boundary, truncation, priority, and adversarial-volume tests.

**Mandatory focused tests**

- [ ] point-in-time cutoff.
- [ ] trust/license/freshness/revision.
- [ ] deduplication/contradiction.
- [ ] injection slot separation.
- [ ] UI orientation refresh.
- [ ] required vs optional evidence.
- [ ] token/byte limits.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ASSEMBLE_CONTEXT`.

**Executable usage:** `uv run python -m app.services.agentic.assemble_context.context_assembly`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.assemble_context.context_assembly
uv run pytest --no-cov tests/contracts/agentic/test_context.py tests/services/agentic/assemble_context/
uv run ruff format --check app/contracts/agentic/context.py app/services/agentic/assemble_context tests/contracts/agentic/test_context.py tests/services/agentic/assemble_context
uv run ruff check app/contracts/agentic/context.py app/services/agentic/assemble_context tests/contracts/agentic/test_context.py tests/services/agentic/assemble_context
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ASSEMBLE_CONTEXT
```

**Removal acceptance:** Evidence-dependent workflows refuse or expose declared partial coverage. No alternate acquisition or stale-cache fallback is invented.

**Proposed commit:** `feat(agentic): implement point-in-time context assembly`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-2.08 — `FEAT-AGT-MANAGE_MEMORY` — Governed Memory

**Goal:** Accept memory candidates, classify state, redact, validate provenance/scope/freshness/sensitivity, deduplicate or supersede, promote eligible records, retrieve bounded task context, and enforce retention. Memory never becomes market or policy truth.

**Depends on:** `AGT-1.02`.
**Phase-0 blockers that must already be closed:** P0.3 persistence/retention boundary; P0.2 supported StateDeclaration retention enum.
**Provides:** `agentic.memory@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.operations@1`.
**Optional capabilities:** `agentic.context@1`.
**External prerequisites:** `workspace.persistence@1 (proposed owner key)`, `workspace.retention@1 (proposed owner key)`.
**State:** PROVISIONAL: namespace `agentic.memory`, schema version `1`; `StateDeclaration` retention must be translated to one Kernel-supported enum in AGT-0.02, while class TTL/purge remains business policy.
**Role contributions:** —.
**Primary method:** `AgenticMemory.manage_agentic_memory(request)`.
**Operations:** `SUBMIT_CANDIDATE`, `PROMOTE`, `RETRIEVE`, `SUPERSEDE`, `PURGE`, `EXPORT`.
**Success/domain outcomes:** `MemoryCandidateReceipt`, `MemoryPromotionDecision`, `MemoryQueryResult`, `MemorySupersessionReceipt`, `MemoryPurgeReceipt`, `MemoryExport`.
**Events:** `MemoryPromoted`, `MemorySuperseded`, `MemoryExpired`.

**Normalized donor bundle inputs**

- `app/agentic/context_memory/repository.py`
- `app/agentic/context_memory/runtime.py`
- `app/agentic/migrations/memory.py`
- `tests/agentic/unit/test_context_memory.py`
- `tests/agentic/integration/test_governed_memory.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/memory.py
app/services/agentic/manage_memory/README.md
app/services/agentic/manage_memory/__init__.py
app/services/agentic/manage_memory/manifest.py
app/services/agentic/manage_memory/config.py
app/services/agentic/manage_memory/feature.py
app/services/agentic/manage_memory/memory_management.py
app/services/agentic/manage_memory/memory_models.py
app/services/agentic/manage_memory/promotion.py
app/services/agentic/manage_memory/retrieval.py
app/services/agentic/manage_memory/retention.py
app/services/agentic/manage_memory/migrations.py
app/services/agentic/manage_memory/_store.py
tests/contracts/agentic/test_memory.py
tests/services/agentic/manage_memory/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/memory.py` with the exact capability key `agentic.memory@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-MANAGE_MEMORY"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `working_ttl_seconds`, `episodic_retention_days`, `semantic_retention_days`, `audit_retention_days`, `max_records_per_task`, `promotion_min_trust`, `purge_batch_size`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Separate workflow, working, episodic, validated-semantic, and operational-audit memory classes with explicit scope and retention behavior.
- [ ] Implement candidate submission and deterministic promotion gates for provenance, evidence, sensitivity, redaction, freshness, injection, deduplication, supersession, retention, and optional human action.
- [ ] Revalidate scope, authorization, freshness, and expiry at retrieval; memory alone cannot support a material market, risk, strategy, or trading claim.
- [ ] Append corrections through `supersedes`; never silently overwrite historical belief or outcome records.
- [ ] Use supported `StateDeclaration` retention vocabulary only. Working TTL and class-specific purge are business logic inside a retained namespace, not invented retention enum values.

**Owned functional requirements**

- [ ] **FR-AGT-CLASSIFY_MEMORY** — Separate workflow state, TTL working context, episodic outcomes, validated semantic memory, and immutable operational audit; reject unknown classes. Side effects: Candidate write. Evidence: Class separation, unknown class, and cross-class access tests.
- [ ] **FR-AGT-PROMOTE_MEMORY** — Require scope, provenance, redaction, trust, freshness, injection, sensitivity, deduplication, retention, and optional approval checks before reusable semantic promotion. Side effects: Transactional promotion write. Evidence: Poisoning, secret, stale, duplicate, approval, and authority tests.
- [ ] **FR-AGT-RETRIEVE_MEMORY** — Retrieve only bounded records authorized for the current task/account/user and revalidate freshness; remembered claims cannot substitute for authoritative evidence. Side effects: Bounded persistence read. Evidence: Scope isolation, freshness, ranking, limit, and no-evidence-authority tests.
- [ ] **FR-AGT-RETAIN_AND_PURGE_MEMORY** — Enforce class-specific TTL, retention, supersession, export, legal hold, and purge behavior; corrections append rather than rewrite history. Side effects: Transactional purge/supersession write. Evidence: TTL, legal hold, append-only correction, purge, and removal tests.

**Mandatory focused tests**

- [ ] memory class isolation.
- [ ] promotion gates.
- [ ] redaction before persist.
- [ ] scope/user/account isolation.
- [ ] memory-not-evidence.
- [ ] supersession.
- [ ] TTL/legal hold/purge.
- [ ] stateless degradation.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-MANAGE_MEMORY`.

**Executable usage:** `uv run python -m app.services.agentic.manage_memory.memory_management`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.manage_memory.memory_management
uv run pytest --no-cov tests/contracts/agentic/test_memory.py tests/services/agentic/manage_memory/
uv run ruff format --check app/contracts/agentic/memory.py app/services/agentic/manage_memory tests/contracts/agentic/test_memory.py tests/services/agentic/manage_memory
uv run ruff check app/contracts/agentic/memory.py app/services/agentic/manage_memory tests/contracts/agentic/test_memory.py tests/services/agentic/manage_memory
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-MANAGE_MEMORY
```

**Removal acceptance:** Operate statelessly where memory is optional; mark memory-required workflows unready; purge only records whose retention permits it and preserve mandated audit evidence.

**Proposed commit:** `feat(agentic): implement governed memory`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-2.09 — `FEAT-AGT-EVALUATE_PROFILES` — Profile and Topology Evaluation

**Goal:** Evaluate roles, prompts, model profiles, tools, workflows, and council topologies against versioned contract, grounding, safety, reproducibility, economic, operational, regression, and ablation evidence, then issue deterministic eligibility decisions.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.04`, `AGT-1.05`, `AGT-2.06`.
**Phase-0 blockers that must already be closed:** P0.9 bootstrap eligibility and grader authority; P0.5/P0.6 evaluation evidence owners.
**Provides:** `agentic.profile-evaluation@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.workflows@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `versioned evaluation datasets`, `human rubric evidence`, `deterministic graders`, `receiver-owned outcome evidence`.
**State:** namespace `agentic.profile_evaluation`, schema version `1`, retention `RETAIN`.
**Role contributions:** —.
**Primary method:** `AgenticProfileEvaluation.evaluate_agentic_profiles(request)`.
**Operations:** `EVALUATE`, `INSPECT_ELIGIBILITY`, `REVOKE_ELIGIBILITY`, `COMPARE_BASELINE`.
**Success/domain outcomes:** `ProfileEvaluationReport`, `EligibilityDecision`, `EligibilityRevocationReceipt`, `BaselineComparison`.
**Events:** `ProfileEligibilityChanged`.

**Normalized donor bundle inputs**

- `app/agentic/agents/operations/evaluation_manager/**`
- `app/agentic/runtime/upgrades.py`
- `tests/agentic/unit/test_evaluation_manager.py`
- `tests/agentic/integration/test_model_upgrade.py`
- `tests/agentic/usage/17_evaluation.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/profile_evaluation.py
app/services/agentic/evaluate_profiles/README.md
app/services/agentic/evaluate_profiles/__init__.py
app/services/agentic/evaluate_profiles/manifest.py
app/services/agentic/evaluate_profiles/config.py
app/services/agentic/evaluate_profiles/feature.py
app/services/agentic/evaluate_profiles/profile_evaluation.py
app/services/agentic/evaluate_profiles/evaluation_models.py
app/services/agentic/evaluate_profiles/graders.py
app/services/agentic/evaluate_profiles/ablation.py
app/services/agentic/evaluate_profiles/eligibility.py
app/services/agentic/evaluate_profiles/migrations.py
app/services/agentic/evaluate_profiles/_store.py
tests/contracts/agentic/test_profile_evaluation.py
tests/services/agentic/evaluate_profiles/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/profile_evaluation.py` with the exact capability key `agentic.profile-evaluation@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-EVALUATE_PROFILES"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `evaluation_set_refs`, `grader_profile_refs`, `eligibility_ttl_seconds`, `minimum_contract_score`, `minimum_grounding_score`, `maximum_safety_failure_rate`, `maximum_cost_ratio`, `require_ablation`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Define versioned evaluation plans, datasets, rubrics, deterministic graders, calibrated model graders, human labels, baseline comparisons, council ablations, and eligibility decisions.
- [ ] Cover contract reliability, grounding, tool correctness, safety, reasoning utility, reproducibility, economic value, latency, cost, retries, failure, and recovery.
- [ ] Implement deterministic-only, best-single-agent, full-council, each-role-removed, and no-peer-visibility comparisons.
- [ ] Apply P0.9 bootstrap rules so the first model/role can be evaluated without declaring itself eligible or creating a circular dependency.
- [ ] Eligibility, expiry, and revocation are deterministic records. This feature cannot edit role manifests, prompts, model profiles, permissions, or policies.

**Owned functional requirements**

- [ ] **FR-AGT-EVALUATE_PROFILES** — Evaluate strict-schema reliability, factual grounding, tool correctness, safety, reasoning utility, reproducibility, economic value, latency, cost, retries, and trace completeness on versioned sets. Side effects: Isolated model/tool/workflow calls and evidence persistence. Evidence: Golden, ambiguous, refusal, leakage, poisoning, privilege, regression, null, stress, and OOD tests.
- [ ] **FR-AGT-ABLATE_TOPOLOGIES** — Compare deterministic-only, best single-agent, full council, each-role-removed, and no-peer-visibility topologies under the same evidence and budgets. Side effects: Evaluation runs and ablation writes. Evidence: Ablation parity, uncertainty, cost, and correlation tests.
- [ ] **FR-AGT-DETERMINE_PROFILE_ELIGIBILITY** — Compute enable, continue, restrict, disable, or retire actions deterministically from required gates, uncertainty margin, cost, and expiry; model prose cannot override arithmetic. Side effects: Eligibility write and event publication. Evidence: Threshold, tie, expired evidence, safety veto, and disablement tests.
- [ ] **FR-AGT-CALIBRATE_GRADERS** — Bind deterministic and human graders to versions and calibration evidence; model graders cannot grade their own promotion in isolation. Side effects: Grader evidence write. Evidence: Self-grading, inter-rater, calibration drift, and version tests.

**Mandatory focused tests**

- [ ] evaluation-set completeness.
- [ ] deterministic grader truth.
- [ ] human agreement.
- [ ] model-grader calibration.
- [ ] self-grading refusal.
- [ ] baseline and ablation arithmetic.
- [ ] eligibility expiry/revocation.
- [ ] missing evidence.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-EVALUATE_PROFILES`.

**Executable usage:** `uv run python -m app.services.agentic.evaluate_profiles.profile_evaluation`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.evaluate_profiles.profile_evaluation
uv run pytest --no-cov tests/contracts/agentic/test_profile_evaluation.py tests/services/agentic/evaluate_profiles/
uv run ruff format --check app/contracts/agentic/profile_evaluation.py app/services/agentic/evaluate_profiles tests/contracts/agentic/test_profile_evaluation.py tests/services/agentic/evaluate_profiles
uv run ruff check app/contracts/agentic/profile_evaluation.py app/services/agentic/evaluate_profiles tests/contracts/agentic/test_profile_evaluation.py tests/services/agentic/evaluate_profiles
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-EVALUATE_PROFILES
```

**Removal acceptance:** Freeze new eligibility and profile changes; existing eligibility follows recorded expiry/revocation. Councils and changed profiles may become unready according to policy.

**Proposed commit:** `feat(agentic): implement profile and topology evaluation`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-2.10 — `FEAT-AGT-ASSIST_OPERATOR` — Website Chat Bot and Specialist Delegation

**Goal:** Power the website Chat Bot: consume a fresh typed workspace/page/widget context snapshot, answer safe contextual questions, propose specialist routing, preserve one conversation across handoffs, and present one evidence-preserving answer.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.05`, `AGT-2.06`, `AGT-2.07`.
**Phase-0 blockers that must already be closed:** P0.8 D-IFACE/UI companion contracts; P0.2 conversation state ownership.
**Provides:** `agentic.operator-assistance@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.workflows@1`, `agentic.operations@1`.
**Optional capabilities:** `agentic.context@1`, `agentic.memory@1`, `agentic.tool-governance@1`.
**External prerequisites:** `interfaces.operator-chat@1 (proposed D-IFACE key)`, `interfaces.workspace-context@1 (proposed D-IFACE key)`.
**State:** BLOCKED BY AGT-0.08: decide whether session/task conversation state is D-IFACE/Workspace-owned or an Agentic purge-on-uninstall namespace.
**Role contributions:** `chat_bot`.
**Primary method:** `OperatorAssistance.assist_operator(request)`.
**Operations:** `RESPOND`, `SUMMARIZE_SPECIALIST_RESULT`.
**Success/domain outcomes:** `OperatorAnswer`, `OperatorSpecialistAnswer`, `OperatorConversationSummary`.
**Events:** `OperatorTurnAccepted`, `WorkspaceContextValidated`, `SpecialistRouteProposed`, `SpecialistRouteAuthorized`, `SpecialistStarted`, `SpecialistCompleted`, `OperatorResponseDelta`, `OperatorTurnCompleted`, `OperatorTurnRefused`, `OperatorTurnFailed`.

**Normalized donor bundle inputs**

- `ADD_TO_V3: no direct donor Chat Bot feature`
- `behavioral clues only: app/agentic/public_api/** and executive-coordination specifications`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/operator_assistance.py
app/services/agentic/assist_operator/README.md
app/services/agentic/assist_operator/__init__.py
app/services/agentic/assist_operator/manifest.py
app/services/agentic/assist_operator/config.py
app/services/agentic/assist_operator/feature.py
app/services/agentic/assist_operator/operator_assistance.py
app/services/agentic/assist_operator/specialist_routing.py
app/services/agentic/assist_operator/context_validation.py
app/services/agentic/assist_operator/roles/chat_bot/role.json
app/services/agentic/assist_operator/roles/chat_bot/prompt.md
tests/contracts/agentic/test_operator_assistance.py
tests/services/agentic/assist_operator/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/operator_assistance.py` with the exact capability key `agentic.operator-assistance@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-ASSIST_OPERATOR"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_message_chars`, `max_context_contributions`, `context_ttl_seconds`, `max_delegations_per_turn`, `allow_direct_ui_answers`, `allow_navigation_suggestions`, `streaming_enabled`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Implement the exact public role identity `Chat Bot` / `chat_bot`; do not reintroduce CEO, Firm Coordinator, or Copilot as canonical aliases.
- [ ] Validate authenticated conversation scope and a fresh bounded `WorkspaceContextSnapshot` with route/page/widget identity, contribution versions, selected public entity references, filters, permissions, redaction metadata, and observation time.
- [ ] Reject raw DOM, secrets, private provider objects, arbitrary executable content, unknown contributions, cross-user snapshots, stale context, and oversize input.
- [ ] Answer directly only for safe UI explanation, navigation suggestion, public definitions, and summaries of already validated results.
- [ ] For specialist work, propose a route and let deterministic routing verify role eligibility, capability support, conflicts, evidence, user permission, budget, and readiness.
- [ ] Return specialist results in the same conversation with specialist attribution, evidence references, uncertainty, refusal/failure, partial coverage, and dissent intact.
- [ ] Expose no direct widget/settings, strategy, simulation, portfolio, risk, trading, order, or broker mutation command.

**Owned functional requirements**

- [ ] **FR-AGT-READ_WORKSPACE_CONTEXT** — Accept only a fresh bounded D-IFACE-validated workspace snapshot assembled from exact widget contributions; reject expired, tampered, wrong-session, wrong-account, oversized, or secret-bearing context. Side effects: Read-only request validation and operations evidence. Evidence: Freshness, hash, session, account, size, redaction, and widget-removal tests.
- [ ] **FR-AGT-ANSWER_CONTEXTUAL_QUESTIONS** — Answer UI meaning, definitions, navigation, and previously grounded-result questions directly when no authoritative refresh or specialist judgment is required. Side effects: Model call; no domain mutation. Evidence: Direct-answer classification, UI metadata, unsupported fact, and no-mutation tests.
- [ ] **FR-AGT-ROUTE_SPECIALIST_QUESTIONS** — Allow Chat Bot to propose a destination but require deterministic verification of role existence, eligibility, scope, permission, evidence readiness, conflict policy, and budget before handoff. Side effects: Workflow submission; optional specialist/model/tool calls through owning capabilities. Evidence: Routing matrix, unavailable specialist, conflict, permission, budget, and no-silent-substitution tests.
- [ ] **FR-AGT-PRESERVE_CHAT_HANDOFF_LINEAGE** — Return specialist output to the same conversation with role/version attribution, claim/evidence references, uncertainty, refusals, dissent, causation, and provenance intact. Side effects: Workflow/operations writes and stream publication. Evidence: Correlation, attribution, streaming order, cancellation, and specialist-failure tests.
- [ ] **FR-AGT-RESTRICT_CHAT_ACTIONS** — Initial Chat Bot verbs are read context, answer, explain, delegate, summarize, and suggest navigation. It cannot mutate widgets, settings, strategies, portfolios, risk, trading, brokers, holdouts, or deployment. Side effects: None beyond response. Evidence: Capability-negative, prompt-injection, authority, and physical-removal tests.

**Mandatory focused tests**

- [ ] fresh per-turn context.
- [ ] cross-user/stale/unknown widget rejection.
- [ ] direct answer vs delegation.
- [ ] disabled/conflicted specialist.
- [ ] same-conversation return.
- [ ] stream cancellation/backpressure.
- [ ] zero mutation authority.
- [ ] widget removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ASSIST_OPERATOR`.

**Executable usage:** `uv run python -m app.services.agentic.assist_operator.operator_assistance`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.assist_operator.operator_assistance
uv run pytest --no-cov tests/contracts/agentic/test_operator_assistance.py tests/services/agentic/assist_operator/
uv run ruff format --check app/contracts/agentic/operator_assistance.py app/services/agentic/assist_operator tests/contracts/agentic/test_operator_assistance.py tests/services/agentic/assist_operator
uv run ruff check app/contracts/agentic/operator_assistance.py app/services/agentic/assist_operator tests/contracts/agentic/test_operator_assistance.py tests/services/agentic/assist_operator
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ASSIST_OPERATOR
```

**Removal acceptance:** Stop new Chat Bot turns, cancel/drain active turns, unregister `chat_bot`, dispose streaming/context callbacks, and preserve workflow/specialist/evidence/audit records. Specialists remain available through other interfaces.

**Proposed commit:** `feat(agentic): implement website chat bot and specialist delegation`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.
