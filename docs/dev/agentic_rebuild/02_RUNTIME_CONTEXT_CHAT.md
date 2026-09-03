# Agentic Rebuild — Phase 2 Runtime, Context, Memory, Evaluation, and Chat Bot

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Prerequisite:** Phase 1 capability foundation  
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts

## Purpose

Deliver bounded durable workflow execution, point-in-time context, governed memory, profile eligibility, and the website **Chat Bot**. These features must remain independently removable: losing memory may yield stateless operation; losing a model provider makes model work unready; losing Chat Bot does not remove specialists or the UI shell.

---

## AGT-2.06 — `FEAT-AGT-RUN_WORKFLOWS`

**Provides:** `agentic.workflows@1`  
**Requires:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.operations@1`, ratified persistence/worker-admission capability.  
**Optional:** `agentic.tool-governance@1`, `agentic.model-inference@1`, `agentic.context@1`, `agentic.memory@1`.  
**State:** `agentic.workflows`, schema v1, `RETAIN`.  
**Roles:** `research_planner`, `artifact_planner`.  
**Primary module:** `workflow_runtime.py`.

**Donor evidence**

```text
app/agentic/orchestration/**
app/agentic/migrations/workflow.py
tests/agentic/unit/test_orchestration.py
tests/agentic/integration/test_durable_runtime.py
tests/agentic/usage/04_orchestration.py
```

**Production paths**

```text
app/contracts/agentic/workflows.py
app/services/agentic/run_workflows/
  README.md __init__.py manifest.py config.py feature.py
  workflow_runtime.py workflow_models.py workflow_registry.py routing.py state_machine.py
  migrations.py _store.py
  roles/research_planner/{role.json,prompt.md}
  roles/artifact_planner/{role.json,prompt.md}
tests/contracts/agentic/test_workflows.py
tests/services/agentic/run_workflows/**
```

**Config keys:** `max_active_runs`, `max_queue_depth`, `max_steps`, `max_fanout`, `max_retries`, `default_deadline_seconds`, `drain_timeout_seconds`.

**Implementation**

- [ ] Define immutable workflow definitions, nodes, transitions, waits, budgets, deadlines, attempts, checkpoints, idempotency, revisions, and terminal reasons.
- [ ] Persist the initial checkpoint before asynchronous execution.
- [ ] Enforce expected-version transitions and terminal states; a terminal run never resumes under the same identity.
- [ ] Apply bounded fan-out, loops, retry, backpressure, cancellation, expiry, pause, resume, reconciliation, and drain.
- [ ] Resolve only mandate-enabled, registered, eligible, conflict-safe roles/capabilities.
- [ ] Implement adaptive escalation: deterministic baseline → one specialist → challenger when material → council only when uncertainty-adjusted value warrants it.
- [ ] Planner roles may propose only registered bounded graphs and cannot widen budgets, authorize tools, consume holdouts, approve receiver actions, or alter policy.
- [ ] Use `context.spawn()` for every worker/run and exact cleanup for role contributions/subscriptions.

**Tests**

- idempotent submit and first-checkpoint atomicity;
- CAS conflicts and terminal-state refusal;
- retry/loop/fan-out/queue/deadline bounds;
- crash/restart/resume and human wait;
- optional capability absence/arrival/removal/recovery;
- planner prompt/manifest integrity and authority-negative tests;
- migration/reconstruction, drain, replacement, churn, retained-state removal, physical deletion.

**Usage:** `uv run python -m app.services.agentic.run_workflows.workflow_runtime`  
**Commit:** `feat(agentic): implement durable workflow orchestration`

---

## AGT-2.07 — `FEAT-AGT-ASSEMBLE_CONTEXT`

**Provides:** `agentic.context@1`  
**Requires:** `agentic.mandate@1`, `agentic.tool-governance@1`, `agentic.operations@1`, exact read-only evidence capabilities.  
**State:** none.  
**Primary module:** `context_assembly.py`.

**Donor evidence**

```text
app/agentic/context_memory/context.py
app/agentic/context_memory/models.py
tests/agentic/unit/test_context_memory.py
tests/agentic/integration/test_research_council.py
```

**Production paths**

```text
app/contracts/agentic/context.py
app/services/agentic/assemble_context/
  README.md __init__.py manifest.py config.py feature.py
  context_assembly.py context_filters.py context_budget.py injection_classification.py
tests/contracts/agentic/test_context.py
tests/services/agentic/assemble_context/**
```

**Config keys:** `max_items`, `max_bytes`, `max_tokens`, `default_freshness_seconds`, `allowed_trust_levels`, `require_license`, `deduplication_algorithm`.

**Implementation**

- [ ] Pin task/principal/objective, asset/account/session scope, observation instant, availability cutoff, required/optional evidence classes, and output budget.
- [ ] Apply deterministic filters in order: scope, schema, availability, licensing, trust, freshness, revision, deduplication, contradiction, injection, relevance, redaction, and size.
- [ ] Keep system/role instructions, trusted task input, untrusted evidence, peer messages, UI context, and memory in structurally separate fields.
- [ ] Treat page/widget context as orientation only; refresh material prices, metrics, states, and results through the owner before claim creation.
- [ ] Return every exclusion with a stable reason; required evidence absence refuses, optional absence yields explicit partial coverage.
- [ ] Never add acquisition or calculation behavior owned by another domain.

**Tests**

- look-ahead and availability-time rejection;
- stale/revised/unlicensed/low-trust/wrong-scope evidence;
- deterministic deduplication/contradiction handling;
- prompt/tool/page/memory injection separation;
- UI value refresh and removed-widget exclusion;
- exact token/byte/item bounds;
- required versus optional coverage, cancellation, replacement, and physical removal.

**Usage:** `uv run python -m app.services.agentic.assemble_context.context_assembly`  
**Commit:** `feat(agentic): implement point-in-time context assembly`

---

## AGT-2.08 — `FEAT-AGT-MANAGE_MEMORY`

**Provides:** `agentic.memory@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, ratified persistence/clock/redaction/retention capabilities.  
**State:** `agentic.memory`, schema v1; use only Phase-0-supported retention enum plus feature-level TTL/purge policy.  
**Primary module:** `memory_management.py`.

**Donor evidence**

```text
app/agentic/context_memory/repository.py
app/agentic/context_memory/runtime.py
app/agentic/migrations/memory.py
tests/agentic/unit/test_context_memory.py
tests/agentic/integration/test_governed_memory.py
```

**Production paths**

```text
app/contracts/agentic/memory.py
app/services/agentic/manage_memory/
  README.md __init__.py manifest.py config.py feature.py
  memory_management.py memory_models.py promotion.py retrieval.py retention.py
  migrations.py _store.py
tests/contracts/agentic/test_memory.py
tests/services/agentic/manage_memory/**
```

**Config keys:** `max_record_bytes`, `max_query_records`, `working_ttl_seconds`, `conversation_summary_ttl_seconds`, `validated_memory_requires_approval`, `retention_days_by_class`, `allowed_sensitivity_classes`.

**Implementation**

- [ ] Separate `WORKFLOW`, `WORKING`, `EPISODIC`, `VALIDATED_SEMANTIC`, and `OPERATIONAL_AUDIT` memory.
- [ ] Promotion validates scope, evidence/provenance, redaction, trust, freshness, injection, sensitivity, retention, deduplication, supersession, and required human action.
- [ ] Retrieval is bounded by principal/task/asset/account/time and revalidates freshness/authorization.
- [ ] Memory is context only; a remembered claim cannot substitute for owner evidence.
- [ ] Corrections append through `supersedes`; no silent overwrite.
- [ ] TTL/purge/legal hold/export are deterministic and class-specific.
- [ ] Model reflection cannot alter mandate, permissions, prompts, thresholds, evaluation policy, eligibility, or receiver state.

**Tests**

- class isolation and unknown class;
- redact-before-persist and secret rejection;
- poisoning/injection/stale/duplicate promotion;
- approval and supersession;
- scoped retrieval and no-evidence-authority;
- TTL, purge, legal hold, export, restart/import;
- stateless degradation, retained-state removal, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.manage_memory.memory_management`  
**Commit:** `feat(agentic): implement governed memory`

---

## AGT-2.09 — `FEAT-AGT-EVALUATE_PROFILES`

**Provides:** `agentic.profile-evaluation@1`  
**Requires:** mandate, roles, operations, tools, model inference, workflows, and ratified evaluation persistence.  
**State:** `agentic.profile_evaluation`, schema v1, `RETAIN`.  
**Primary module:** `profile_evaluation.py`.

**Donor evidence**

```text
app/agentic/agents/operations/evaluation_manager/**
tests/agentic/unit/test_evaluation_manager.py
tests/agentic/usage/17_evaluation.py
docs/dev/agentic_firm/04_evaluation_standard.md
```

**Production paths**

```text
app/contracts/agentic/profile_evaluation.py
app/services/agentic/evaluate_profiles/
  README.md __init__.py manifest.py config.py feature.py
  profile_evaluation.py evaluation_sets.py graders.py ablation.py eligibility.py
  migrations.py _store.py
tests/contracts/agentic/test_profile_evaluation.py
tests/services/agentic/evaluate_profiles/**
```

**Config keys:** `evaluation_set_refs`, `grader_profile_refs`, `eligibility_ttl_seconds`, `minimum_human_labels`, `maximum_regression_rate`, `maximum_safety_failure_rate`, `maximum_cost_ratio`, `require_ablation`.

**Implementation**

- [ ] Evaluate roles, prompts, models, tools, workflows, and council topologies against versioned contract reliability, grounding, tool correctness, safety, reasoning utility, reproducibility, economic value, and operational quality.
- [ ] Include golden, ambiguous, refusal, point-in-time, injection/poisoning, approval-forgery, provider regression, null/random-label, regime, stress, and OOD sets where applicable.
- [ ] Deterministic graders own schemas/calculations/permissions; human rubrics record agreement; model graders require calibration and cannot self-promote.
- [ ] Compare deterministic-only, best single-agent, full council, each-role-removed, and no-peer-visibility under matched inputs/budgets.
- [ ] Apply the Phase-0 bootstrap without circular eligibility.
- [ ] Compute eligibility, restrictions, expiry, suspension, revocation, and retirement deterministically; never edit manifests/prompts/providers directly.

**Tests**

- evaluation-set completeness and version binding;
- deterministic/human/model grader rules and self-grading rejection;
- ablation input/budget parity and uncertainty/cost arithmetic;
- safety veto, tie, expiry, regression, revocation;
- bootstrap provider confinement;
- migration/restart, role/provider removal, replacement, physical deletion.

**Usage:** `uv run python -m app.services.agentic.evaluate_profiles.profile_evaluation`  
**Commit:** `feat(agentic): implement profile and topology evaluation`

---

## AGT-2.10 — `FEAT-AGT-ASSIST_OPERATOR`

**Provides:** `agentic.operator-assistance@1`  
**Requires:** mandate, operations, roles, model inference, workflows; context is required by context-aware workflow policy and memory/tools are optional.  
**External prerequisite:** Phase-0-ratified D-IFACE Chat Bot transport and workspace-context capability.  
**State:** Phase 0 decides Agentic versus D-IFACE/Workspace session ownership; no implementation may guess.  
**Role:** **Chat Bot**, ID `chat_bot`.  
**Primary module:** `operator_assistance.py`.

**Donor evidence**

```text
ADD_TO_V3 — no direct donor Chat Bot feature
Behavioral clues only: app/agentic/public_api/** and executive-coordination specifications
```

**Production paths**

```text
app/contracts/agentic/operator_assistance.py
app/services/agentic/assist_operator/
  README.md __init__.py manifest.py config.py feature.py
  operator_assistance.py specialist_routing.py context_validation.py
  optional conversation storage only if Phase 0 assigns it here
  roles/chat_bot/{role.json,prompt.md}
tests/contracts/agentic/test_operator_assistance.py
tests/services/agentic/assist_operator/**
```

**Config keys:** `max_message_chars`, `max_context_contributions`, `context_ttl_seconds`, `max_delegations_per_turn`, `allow_direct_ui_answers`, `allow_navigation_suggestions`, `streaming_enabled`.

**Implementation**

- [ ] Canonical public and role name is exactly **Chat Bot** / `chat_bot`; do not restore CEO, Firm Coordinator, or Copilot aliases as authority-bearing identities.
- [ ] Validate authenticated conversation scope and a newly captured bounded `WorkspaceContextSnapshot` containing page/route/focused-widget identity, versioned contributions, public entity refs, filters, permissions, redaction metadata, and observation time.
- [ ] Reject raw DOM, credentials, provider objects, unrestricted screenshots, executable content, unknown contributions, cross-user/session snapshots, stale context, and oversize input.
- [ ] Answer directly only for safe UI explanation, navigation suggestion, public definitions, and summaries of already validated results.
- [ ] For specialist work, Chat Bot proposes a route; deterministic code verifies role eligibility, capability support, conflicts, evidence, permission, budget, limits, and readiness.
- [ ] Return specialist output in the same conversation with role/version attribution, evidence, uncertainty, refusal/failure, partial coverage, dissent, causation, and provenance preserved.
- [ ] Initial verbs are only read context, answer, explain, delegate, summarize, and suggest navigation.
- [ ] Expose no widget/settings, strategy, simulation, portfolio, Risk, Trading, order, broker, holdout, or deployment mutation.

**Tests**

- fresh per-turn context and contribution hash/version;
- stale/cross-user/wrong-session/unknown/removed widget rejection;
- direct-answer versus delegation matrix;
- disabled/ineligible/conflicted/unsupported specialist;
- no silent provider/specialist substitution;
- same-conversation lineage and specialist attribution;
- streaming order, cancellation, backpressure, specialist failure/refusal;
- prompt injection and action-authority negative suite;
- optional memory absent/arrival/removal and conversation TTL;
- feature removal leaves UI/specialists usable through other interfaces.

**Usage:** `uv run python -m app.services.agentic.assist_operator.operator_assistance`  
**Commit:** `feat(agentic): implement website chat bot and specialist delegation`

---

## Phase 2 exit gate

- [ ] Durable workflows survive restart and terminate deterministically.
- [ ] Context is point-in-time, bounded, injection-separated, and owner-refreshed.
- [ ] Memory is classed, scoped, promoted, retained, and removable without becoming evidence authority.
- [ ] Eligibility is non-circular, evidence-based, expiring, and revocable.
- [ ] Chat Bot passes direct-answer and at least one specialist-delegation path using an offline deterministic provider.
- [ ] Every role contribution is hash-verified and exactly disposable.
- [ ] Every feature passes lifecycle, replacement, readiness, primary usage, targeted quality, and physical-removal evidence.
