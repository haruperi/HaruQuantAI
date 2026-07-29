# Optimization Coordinator

> **Package:** `app/agentic/agents/experimentation/optimization_coordinator`
> **Feature:** `FEAT-AGT-15` Optimization Coordination
> **Status:** `Completed`
> **Last updated:** `2026-07-29`

> This README documents one registered leaf agent package. It is **subordinate
> to the canonical Agentic Feature Registry** in `app/agentic/README.md`, which
> remains the sole authority for feature IDs, statuses, public APIs, contracts,
> and requirements. This file contains no Feature Registry section and defines
> no requirement of its own.

---

## 1. Purpose and Boundary

### Purpose

Declare a bounded search in full before it runs, then read the returned
evidence for robustness rather than for rank.

### Owns

- The provider-neutral Optimization Coordinator agent definition.
- The immutable base role instruction in `prompt.md`.
- `SweepPlan`, `TrialLedger`, and `SweepVerdict`.

### Does not own

- Execution. Optimization runs searches; this role declares and reads.
- Any search request or result. Both belong to the receiver and are never
  constructed here.
- Any robustness score, stability percentage, or overfit measure. Each is a
  deterministic public operation whose output is read, never computed.
- Holdout state. That belongs to the `FEAT-AGT-14` experiment ledger; this
  feature reserves from it.
- Any approval, position size, or recommendation to trade.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `SweepPlan` | `v1` | Agentic, UI/API | Bounded search declared in full before execution |
| Completed | `TrialLedger` | `v1` | Agentic | Reconciled accounting of every attempted trial |
| Completed | `SweepVerdict` | `v1` | Agentic, UI/API | Robustness-focused reading bound to the returned search |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `AgentPolicy` / `ToolPolicy` / `call_governed_tool` | `v1` | Agentic `FEAT-AGT-05` | Deny-by-default tool authorization |
| `ExperimentSpec` / `AgenticExperimentStore` | `v1` | Agentic `FEAT-AGT-14` | Pre-registered protocol and holdout scarcity |
| `optimization.search_request.v1` / `optimization.result.v1` | `v1` | Optimization | Receiver-owned request and result |

---

## 2. Package Structure

```text
optimization_coordinator/
├── __init__.py     # Feature Registry public API only
├── agent.py        # Provider-neutral definition and both public use cases
├── prompt.md       # Immutable base role instruction
├── schemas.py      # Feature-owned typed plan, ledger, and verdict
├── tools.py        # Governed Optimization bindings and result-binding check
└── README.md       # This file
```

No `migrations.py`, `repository.py`, `evaluator.py`, or sandbox file exists,
because the canonical module specification (§4.15) declares none. Holdout state
lives in the `FEAT-AGT-14` ledger.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `design_sweep` | function | Declare one bounded sweep before execution |
| `coordinate_optimization` | function | Run one pre-declared sweep and bind a verdict |
| `SweepPlan` / `SweepVerdict` | classes | Typed contracts |
| `build_sweep_plan` / `build_sweep_verdict` | functions | Validated constructors |

---

## 3. Prompt Integrity

`prompt.md` is data, never code. `agent.py` loads it, normalizes line endings,
hashes it, and compares the digest against the enabled `RoleManifest` before
constructing anything. A mutated, missing, or empty prompt fails closed before
any model call. The shared implementation is
`app.agentic.governance.registry.verify_prompt_artifact`.

---

## 4. Behaviour

### The plan is declared first, and the digest proves it

`build_sweep_plan` derives `plan_hash` over the whole declaration — space,
objective, method, budget, seed, early-stop policy, and holdout consumption.
Widening a budget afterwards produces a different plan, so a verdict carrying
the original digest cannot have been matched against a budget invented later.

The configuration comes from the caller. The model contributes the early-stop
policy and the justification — the design judgement — not the budget or the
seed. A model that emits its own `trial_budget` is ignored.

### The budget must balance

`TrialLedger` requires `attempted == completed + failed`, requires one reason
per failed trial, and rejects a search that exceeded the budget it was granted.

This is the sharp edge of the feature. A sweep that reports a winning parameter
set while quietly dropping failed trials is describing a different experiment
from the one that ran, and the arithmetic makes that unrepresentable. If a
receiver reports numbers that do not reconcile, the run is refused as
`TRIALS_NOT_RECONCILED` **before** the verdict model is invoked.

### Robustness comes from the receiver, and rank comes last

`robustness_evidence`, `instability_evidence`, and `overfit_evidence` are each
assembled from what `calculate_robustness_score`,
`calculate_parameter_stability`, and `detect_overfit_parameters` returned. The
model reads them; it cannot supply one. A model emitting its own
`robustness_evidence` has no effect.

`SweepVerdict` requires all three plus `economic_effect` and
`unresolved_risk`, so a verdict consisting only of `selected_parameters`
cannot be represented. Two unresolved risks are added deterministically rather
than left to the model: a cumulative search at or above
`LIFETIME_TRIAL_WARNING` trials, and any search in which trials failed.

`search_id` and `reproducibility_hash` come from the receiver. The
`receiver_decision` is carried verbatim — note that `ready_for_risk_review`
means the deterministic Risk gate is next, **not** that anything was approved,
and this feature neither produces nor overrides it.

### Holdout is one look, shared with the experiment designer

A plan declaring `holdout_consumption = "consumes"` reserves the thesis's
single look through the same `AgenticExperimentStore` an experiment would.
Without this, `FEAT-AGT-14`'s scarcity guarantee would have a hole the size of
the whole optimization path: an experiment could spend holdout, and a sweep
could spend it again.

Refused at design time and again at coordination time, before the receiver is
reached.

### Refusal is a complete outcome

| Reason | Operation | Condition |
|---|---|---|
| `SPACE_NOT_BOUNDED` | design | No bounded parameter space |
| `BUDGET_NOT_DECLARED` | design | Trial budget not positive |
| `PROTOCOL_NOT_REGISTERED` | design | The protocol was not pre-registered |
| `HOLDOUT_ALREADY_CONSUMED` | both | The thesis's one look is spent |
| `OPTIMIZATION_TOOL_DENIED` | coordinate | A required tool is unregistered or denied |
| `RESULT_NOT_FOR_PLAN` | coordinate | Missing evidence, or a seed the plan did not declare |
| `ROBUSTNESS_EVIDENCE_UNAVAILABLE` | coordinate | A deterministic evidence operation returned nothing |
| `TRIALS_NOT_RECONCILED` | coordinate | The trial accounting does not balance |
| *model reasons* | both | The coordinator itself declined |

Every design refusal and both pre-receiver coordination refusals occur before
the model is reached.

---

## 5. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_optimization_coordinator.py` |
| Usage | `tests/agentic/usage/15_optimization.py` |
| Integration | `tests/agentic/integration/test_bounded_optimization.py` |

```bash
uv run pytest tests/agentic/unit/test_optimization_coordinator.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/15_optimization.py
```

### Known limits

- Optimization arrives through `build_optimization_port`, which binds an
  injected facade. Wiring it to the real Optimization package root is a
  composition-root concern and is not exercised here; tests use deterministic
  doubles, and **no search executes**. This matters more than usual:
  `run_parameter_sweep` is declared `requires_network=True`.
- **Trial preservation has no dedicated table.** The accounting lives in the
  `SweepVerdict` contract, not a ledger row, so it is durable only as far as
  whatever persists the verdict. §4.15 declares no repository.
- `run_walk_forward_optimization`, `run_walk_forward_matrix`,
  `run_robustness_analysis`, `rank_parameter_sets`, and
  `compare_optimization_runs` are public Optimization operations this role does
  not yet bind. `method = "walk_forward"` is representable in a plan but has no
  distinct coordination path.
- `prior_trials_consumed` is supplied by the caller. Nothing here verifies it
  against a durable per-thesis counter, so the cumulative-search warning is
  only as honest as its input.
- `WF-AGT-004` remains `Missing`: `build_sweep_plan` and `build_sweep_verdict`
  are public-root exports assigned to `FEAT-AGT-22`. Every one of its five
  steps is otherwise implemented here.

---

## 6. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Never relax the trial arithmetic. If a receiver reports numbers that cannot
   reconcile, fix the reporting, not the validator.
5. Update `schemas.py`, `tools.py`, tests, and the usage program.
6. Change status only after every gate passes.
