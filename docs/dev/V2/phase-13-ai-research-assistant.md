# Phase 13 — AI research assistant

**Feature group:** F13. **Tasks:** 4. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Connect Q sessions, model providers and result-tab completion to real state. This phase owns the ai research assistant capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** H07/H08/H09/H10 and only the tools selected by a turn; F09 for project orchestration. Missing AI bodies gate affected compatibility.

**Delivery:** M08 and M09. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/agentic`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P19](../V1/phase-19-agentic-research.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Q interaction | 13.1 | Config/state/session/history/projects/attachments, late replay, stopped/failed turns and result-tab cache/regenerate/concurrency/model/credit policy |
| Knowledge | 13.2 | Memory-layer evidence, AI Brain/research verdicts, versioned procedures and extension skills/commands/agents/knowledge reload |
| Execution | 13.3 | Typed tool loop, time/cost bounds, persisted schedules, isolated Python and retained artifacts |
| Procedure families | 13.4 | ac-strategy; algowizard-lab; analysis-tabs; auto-research; breakout-project-factory; custom-page |
| Procedure families | 13.4 | market-analyst (recorded payload gap); plugin-maker; quant-research; sqx-indicator-builder; sqx-project; sqx-reports |
| Procedure families | 13.4 | sqx-snippets; sqx-strategy; strategy-analyst; strategy-architect; trading-memory; ui-pilot |
| Qualification | 13.4 | Every manifest contribution needs payload/permission evidence; goal -> discovery -> build -> retest -> retained record uses actual results |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F13 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx](../../../ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 13.1 Q sessions, chat, providers and result-tab completion

## 1. Objective

Connect Q sessions, model providers and result-tab completion to real state.

## 2. Research and donors

P19 SQAI/Q core and completion consumers; missing AI bodies and provider observations remain compatibility gates.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/agentic/sessions.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/agentic/providers.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/agentic/completion.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_13/test_sessions.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover Q config/state/session/history/projects/attachments, turn events and provider model/credit contracts.
- [ ] **Step 2:** Implement a bounded provider adapter with permissions, time/cost limits, cancellation and explicit unavailable/stopped/failed turns.
- [ ] **Step 3:** Recover late subscribers from retained state; implement result-tab cache/regenerate with versioned inputs and concurrency control.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_13/test_sessions.py --no-cov`.

**Independent cases:** Independent schema/state/replay vectors, cancel races, simultaneous completion, cache invalidation, denied credits/models and isolated connected chat/result-tab journey.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 13.2 Memory, knowledge, research records and procedures

## 1. Objective

Retain editable knowledge, research memory and learned procedures with source lineage.

## 2. Research and donors

P19 Q memory/extensions and shipped resources; private user memory/accounts are excluded from donor capture.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/agentic/memory.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/agentic/procedures.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_13/test_memory.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover the actual memory-layer write/read/approval/removal contract rather than inferring four layers from names.
- [ ] **Step 2:** Represent knowledge/AI Brain/research verdicts/procedures as versioned host resources with provenance and user-authorized revisions.
- [ ] **Step 3:** Load/reload skills, commands, agents and knowledge manifests with compatibility/permission checks; preserve approved memory across removal.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_13/test_memory.py --no-cov`.

**Independent cases:** Independent revision/read/write/conflict/removal fixtures, unapproved memory changes, incompatible procedures, reload and referenced-result preservation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 13.3 Bounded tool orchestration, schedules and isolated analysis

## 1. Objective

Orchestrate approved research tools with bounded schedules and isolated analysis.

## 2. Research and donors

P19 AgentScope/scheduling/Python consumers and F09 project workflows; ordinary worker isolation is insufficient.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/agentic/tools.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/agentic/orchestration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/agentic/schedules.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_13/test_tools.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Expose typed existing data/strategy/run/result/project operations with least-scope authority and real artifact IDs.
- [ ] **Step 2:** Limit tool turns/time/cost, propagate cancellation and retain partial/failure lineage; persisted deadlines use H07 rather than another scheduler.
- [ ] **Step 3:** Enforce a genuine sandbox for Python analysis and bounded artifacts; generated code/plugins/pages remain reviewable artifacts with explicit mutation authority.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_13/test_tools.py --no-cov`.

**Independent cases:** Tool/schema/permission denial, unavailable capability, bounded schedule/restart/cancel race, sandbox escape/resource tests and no invented numerical result from chat text.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 13.4 All Q contributions and connected research qualification

## 1. Objective

Qualify every Q contribution and the goal-to-retained-research journey.

## 2. Research and donors

P19 all named Q procedures and integration; avoid a general multi-agent/shell-parsing framework unless a retained operation requires it.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/agentic/contributions.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/agentic/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_13/test_contributions.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Disposition every procedure/extension row in the matrix, binding evidenced operations to existing tools; missing market-analyst payload remains an explicit source gap.
- [ ] **Step 2:** Test each contribution inputs/outputs/permissions and its removal/reload semantics without claiming parity from a manifest name.
- [ ] **Step 3:** Connect goal -> discovery -> build -> retest -> retained research record using actual domain results, with result-tab and stopped/failed-turn behavior.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_13/test_contributions.py --no-cov`.

**Independent cases:** Independent contribution cases and real-host bounded research journey; all matrix rows accepted or explicitly unresolved, memory/artifact lineage retained and denied side effects visible.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 4 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
