# Evaluation Manager

> **Package:** `app/agentic/agents/operations/evaluation_manager`
> **Feature:** `FEAT-AGT-17` Evaluation, Critique, and Economic Acceptance
> **Status:** `Completed`
> **Last updated:** `2026-07-30`

> This README documents one registered leaf agent package. It is **subordinate
> to the canonical Agentic Feature Registry** in `app/agentic/README.md`, which
> remains the sole authority for feature IDs, statuses, public APIs, contracts,
> and requirements. This file contains no Feature Registry section and defines
> no requirement of its own.

---

## 1. Purpose and Boundary

### Purpose

Decide whether a role has earned its place and whether a candidate artefact
survives adversarial challenge — from measured evidence, on arithmetic no
wording can move.

### Owns

- The provider-neutral Evaluation Manager agent definition.
- The immutable base role instruction in `prompt.md`.
- `EvaluationPlan`, `CritiqueMemo`, `EconomicAcceptanceVerdict`, and the
  internal `BaselineComparison`.
- The required set kinds, required challenge kinds, and the safety gates.
- The acceptance arithmetic: margin against uncertainty plus cost.

### Does not own

- The evaluation sets. It reads which versioned sets exist and which graders
  are calibrated; it authors neither. Both are owner-public facts.
- Grading. No score is computed here. Scores arrive as evidence.
- Role state. This feature produces a verdict; applying a disable or a retire
  belongs to `FEAT-AGT-18` lifecycle or a governance manifest re-issue. See §5.
- Promotion. `FEAT-AGT-18` decides what advances.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `EvaluationPlan` | `v1` | Agentic, UI/API | Declared coverage and calibration for one evaluation |
| Completed | `CritiqueMemo` | `v1` | Agentic, UI/API | Seven adversarial challenges against one candidate |
| Completed | `EconomicAcceptanceVerdict` | `v1` | Agentic, UI/API | Binding continue / disable / retire decision |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `AgentPolicy` / `ToolPolicy` / `call_governed_tool` | `v1` | Agentic `FEAT-AGT-05` | Deny-by-default tool authorization |
| `AgenticMemoryStore` / `store_memory` | `v1` | Agentic `FEAT-AGT-06` | Governed audit of every evidence read |
| `ExperimentVerdict` | `v1` | Agentic `FEAT-AGT-14` | Candidate evidence for grounded critique |
| `SweepVerdict` | `v1` | Agentic `FEAT-AGT-15` | Candidate evidence for grounded critique |
| `CodeArtifact` | `v1` | Agentic `FEAT-AGT-16` | Candidate evidence for grounded critique |

---

## 2. Package Structure

```text
evaluation_manager/
├── __init__.py      # Feature Registry public API only
├── agent.py         # Provider-neutral definition and public use cases
├── prompt.md        # Immutable base role instruction
├── schemas.py       # Feature-owned typed plan, memo, and verdict
├── evaluator.py     # Required kinds, safety gates, acceptance arithmetic
├── tools.py         # Governed evaluation-evidence bindings
└── README.md        # This file
```

`evaluator.py` carries more than the canonical §4.17 file list assigns it. The
list gives it the evaluation-set and grader definitions; it also holds
`survives_baseline` and `required_action`. Splitting the thresholds from the
comparison that uses them would mean `schemas.py` and `agent.py` each restating
a rule, and the point of the module is that there is one statement of it.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `evaluate_agent` | function | Evaluate one role and return a binding verdict |
| `critique_candidate` | function | Challenge one candidate artefact on seven axes |
| `EvaluationPlan` / `CritiqueMemo` / `EconomicAcceptanceVerdict` | classes | Typed contracts |
| `build_evaluation_plan` / `build_critique_memo` / `build_economic_acceptance_verdict` | functions | Validated constructors |

---

## 3. Prompt Integrity

`prompt.md` is data, never code. `agent.py` loads it, normalizes line endings,
hashes it, and compares the digest against the enabled `RoleManifest` before
constructing anything. A mutated, missing, or empty prompt fails closed before
any model call. The shared implementation is
`app.agentic.governance.registry.verify_prompt_artifact`.

---

## 4. Behaviour

### Coverage is exact, not sufficient

`FR-AGENTIC-049` names six set kinds. `EvaluationPlan` validates the declared
kinds against `REQUIRED_SET_KINDS` by **set equality**, so an evaluation
missing its poisoning set is not a weaker evaluation but an impossible one, and
a plan smuggling in a seventh kind nobody agreed to is refused just as firmly.
Each kind needs its own calibrated grader; a grader without a calibration
reference is not a grader.

`FR-AGENTIC-050` names seven challenge kinds and `CritiqueMemo` treats them the
same way. On top of coverage, each statement must be at least 24 characters and
must not read as an endorsement — `no concerns`, `looks good`, `lgtm`,
`not applicable`. The bound catches `n/a`, not brevity. A challenge that cannot
be substantiated is declared in `unsubstantiated`; it is never silently passed.

### Which sets exist is a fact, not a claim

All four evidence reads — versioned sets, grader calibrations, gate outcomes,
baseline comparison — go through `call_governed_tool`, and each writes an audit
record. The model is never asked, and never believed, about whether a set
exists at a version or whether a grader was calibrated. Coverage is checked
before any model call; a plan that does not cover its sets never reaches the
provider.

### The acceptance decision is arithmetic

```text
margin  = candidate_score - baseline_score
hurdle  = uncertainty_halfwidth + cost_delta
survives = margin > hurdle
```

`Decimal` throughout, and the comparison is strict. **An exact tie fails**: when
the candidate and the simpler baseline are not distinguishable, the baseline
wins, because complexity has to earn its place rather than merely match.

`required_action` follows from the outcome and the history:

| Failed safety gate | Survives | Prior consecutive failures | Action |
|---|---|---|---|
| No | Yes | any | `continue` |
| Yes | any | 0 | `disable` |
| No | No | 0 | `disable` |
| Yes | any | ≥ 1 | `retire` |
| No | No | ≥ 1 | `retire` |

Safety gates — adversarial, poisoning, refusal — end a role regardless of its
margin. A candidate that leaks or refuses unsafely does not get to argue about
its score.

The action is computed **before** the model is invoked. The model is given the
margin, the hurdle, the failed gates, and the action, and asked to explain the
outcome and state its uncertainty. `EconomicAcceptanceVerdict` then recomputes
the action from its own gate outcomes and comparison and rejects any verdict
whose recorded action disagrees, so a model that writes `continue` over a
failed gate produces no verdict at all.

### Grounded challenges override the model

Where the candidate evidence already says something, the evidence is what the
memo records. A `SweepVerdict` reporting failed trials produces the robustness
challenge; a `CodeArtifact` blocked on an unmerged indicator produces the
operational one; an `ExperimentVerdict` produces the causality one. These are
merged over the model's text, not under it — the model cannot soften a
challenge the evidence supports.

### Refusal is a complete outcome

| Reason | Condition | Before the model? |
|---|---|---|
| `EVALUATION_TOOL_DENIED` | An evidence tool is unregistered or denied | Yes |
| `EVALUATION_COVERAGE_INCOMPLETE` | A set kind is missing, unknown, or uncalibrated | Yes |
| `BASELINE_COMPARISON_UNAVAILABLE` | The comparison is absent, incomplete, or unreadable | Yes |
| `CANDIDATE_EVIDENCE_ABSENT` | A critique was requested with nothing to critique | Yes |
| `CRITIQUE_COVERAGE_INCOMPLETE` | A challenge is missing, too short, or an endorsement | No |
| *model reasons* | The manager itself declined | — |

---

## 5. What this feature decides and does not do

It decides. It does not mutate.

The canonical §4.17 row records `Governed role-state change` as the side effect
of `FR-AGENTIC-051`. That is narrower here: `evaluate_agent` returns a verdict
carrying `required_action`, and nothing in this package disables or retires
anything. A role's registered state lives in the governance manifest, and
changing it is `FEAT-AGT-18`'s or a mandate re-issue's business. Recording the
decision and applying it are deliberately separate, so a verdict is auditable
before it has consequences.

---

## 6. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_evaluation_manager.py` |
| Usage | `tests/agentic/usage/17_evaluation.py` |
| Integration | `tests/agentic/integration/test_evaluation.py` |

```bash
uv run pytest tests/agentic/unit/test_evaluation_manager.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/17_evaluation.py
```

### Known limits

- **No role in this firm has actually been evaluated.** This feature is the
  mechanism. No gold, adversarial, poisoning, refusal, regression, or
  economic-ablation set has been authored for any registered role, and no
  grader has been calibrated against one. Every leaf README that defers its
  quality claim to `FEAT-AGT-17` still defers it.
- Grading is not implemented and is not in scope. Scores, gate outcomes, and
  the baseline comparison arrive as evidence through the governed port; the
  deterministic double supplies them in tests.
- Whether a calibration reference describes a *good* calibration is not
  checked. The plan proves one was declared, not that it was sound.
- `consecutive_failures` is supplied by the caller. Nothing here persists an
  evaluation history, so retire-on-repeat depends on a counter this feature
  does not own.
- Google ADK binding is not implemented (`FEAT-AGT-03` is `Partial`).

---

## 7. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Never add a required set or challenge kind without the test that shows the
   old coverage is now refused; the sets are validated by equality, so widening
   one invalidates every existing plan by design.
5. Never relax `survives_baseline` to `>=` without stating why a tie should
   favour the more complex candidate.
6. Update `schemas.py`, `evaluator.py`, `tools.py`, tests, and the usage
   program.
7. Change status only after every gate passes.
