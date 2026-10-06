# P19 — Q assistant and connected agentic research

- **Delivery order:** after reusable host/data/engine/project contracts; before P18 final qualification. Depends on P00–P08, P09–P13 and product/provider authority from P17.
- **State:** proposed implementation tasks. Owning registries remain unratified; no donor activation or target parity is implied.
- **Execution:** AGENTS.md plan → approval → implementation → focused verification → walkthrough; follow PYTHON_MODULE.md and explicit descriptive FR logging.
- **UI:** Q was absent at initial research capture. Concurrent UI-only work now provides `ui/app/workspace/AIAssistant/`; reuse its native controls after reconciling the final owner-approved candidate. Backend/provider operations remain unavailable; connect actual host capabilities. Production mocks cannot qualify completion.


- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 31 tasks; current archive allocations and resource/integration tasks only.

# 19.1 Q prerequisites - core packaging, contracts and source authority

## 1. Objective

- **Goal:** Locate/qualify missing AI core behavior before translating Q.
- **Context / Problem Solved:** ServletSQAI references agent/model/session/wakeup/path-grant bodies absent from all standalone JARs.

## 2. Research and donors

- `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar`; exact referenced symbols and hashes in the published audit.
- Q official introduction/extending documentation, actual shipped chat/resources and 18 manifests; missing linked documents and skill texts remain gaps.
- Resolve classpath collisions and core packaging without launching donor applications or reading account/live database state.

## 3. File Changes

- **Modify:** `docs/dev/evidence/reimplementation.json` — approved atomic source observations and explicit unresolved behavior.
- **Modify:** `docs/dev/evidence/sqx145/ownership.json` — actual owner/disposition gaps; no fabricated registered IDs.
- **Create:** `app/plugins/agentic/README.md` — only after separate approval of actual retained FEAT/FR contracts.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Approve exact research/registry paths and core-source inspection procedure.
- [ ] **Step 2:** Locate readable bodies or independent observed contracts for loops, tools, models, memory, sessions, scheduling and permission grants.
- [ ] **Step 3:** Ratify ownership/host capability boundaries and provider/credit authority; reject missing compatibility or source evidence.
- [ ] **Step 4:** Record separate static/runtime validation and keep downstream unavailable capabilities blocked.

## 5. Verification & Testing

- **Automated Tests:** reference validator, exact symbol/hash reconciliation, ownership/permission negative gates; no invented expected results.
- **Manual / Browser Verification:** inspect the evidence/owner gaps; no paid provider interaction or donor launch implied.


# 19.2 FEAT-AGENTIC-AGENTSCOPE-CORE - agentscope-core-2.0.3.jar

## 1. Objective

- **Goal:** Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/agentscope-core-2.0.3.jar`; 441 raw class entries; SHA-256 `7f1ec0f9c5afd1388554275efc78f58cb05692b634453695cf404eb79f7cfda4`.
- **Inspected reference:** [agentscope-core-2.0.3.md](sqx/Libraries/agentscope-core-2.0.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/agentscope-core-2.0.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/agentscope-core-2.0.3.jar" io.agentscope.core.middleware.FinalAnswerFilterMiddleware`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-AGENTIC-AGENTSCOPE-CORE` and `FR-AGENTIC-AGENTSCOPE-CORE-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/agentscope_core_2_0_3.py` — Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_agentscope_core.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-AGENTIC-AGENTSCOPE-CORE-FINAL-ANSWER-FILTER-MIDDLEWARE-CONTRACT` → `io.agentscope.core.middleware.FinalAnswerFilterMiddleware`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AGENTIC-AGENTSCOPE-CORE-FINAL-ANSWER-FILTER-MIDDLEWARE-ON-REASONING` → `io.agentscope.core.middleware.FinalAnswerFilterMiddleware.onReasoning(Lio/agentscope/core/agent/Agent;Lio/agentscope/core/agent/RuntimeContext;Lio/agentscope/core/middleware/ReasoningInput;Ljava/util/function/Function;)Lreactor/core/publisher/Flux;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AGENTIC-AGENTSCOPE-CORE-FINAL-ANSWER-FILTER-MIDDLEWARE-IS-TEXT-BLOCK-EVENT` → `io.agentscope.core.middleware.FinalAnswerFilterMiddleware.isTextBlockEvent(Lio/agentscope/core/event/AgentEvent;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_agentscope_core.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.3 FEAT-AGENTIC-AGENTSCOPE-HARNESS - agentscope-harness-2.0.3.jar

## 1. Objective

- **Goal:** Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/agentscope-harness-2.0.3.jar`; 393 raw class entries; SHA-256 `e6f6f5c39d8e16ca5c2ea3727b56dbcfa8fd408ef54a0018c0c9416251beb1a0`.
- **Inspected reference:** [agentscope-harness-2.0.3.md](sqx/Libraries/agentscope-harness-2.0.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/agentscope-harness-2.0.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/agentscope-harness-2.0.3.jar" io.agentscope.harness.agent.middleware.SubagentsMiddleware`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-AGENTIC-AGENTSCOPE-HARNESS` and `FR-AGENTIC-AGENTSCOPE-HARNESS-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/agentscope_harness_2_0_3.py` — Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_agentscope_harness.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-AGENTIC-AGENTSCOPE-HARNESS-SUBAGENTS-MIDDLEWARE-CONTRACT` → `io.agentscope.harness.agent.middleware.SubagentsMiddleware`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AGENTIC-AGENTSCOPE-HARNESS-SUBAGENTS-MIDDLEWARE-ENABLE-AGENT-GENERATE-TOOL` → `io.agentscope.harness.agent.middleware.SubagentsMiddleware.enableAgentGenerateTool(Lio/agentscope/harness/agent/subagent/SubagentSpecGenerator;)Lio/agentscope/harness/agent/middleware/SubagentsMiddleware;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AGENTIC-AGENTSCOPE-HARNESS-SUBAGENTS-MIDDLEWARE-GET-TASK-REPOSITORY` → `io.agentscope.harness.agent.middleware.SubagentsMiddleware.getTaskRepository()Lio/agentscope/harness/agent/subagent/task/TaskRepository;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_agentscope_harness.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.4 FEAT-AGENTIC-TREE-SITTER - tree-sitter-0.24.4.jar

## 1. Objective

- **Goal:** Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/tree-sitter-0.24.4.jar`; 34 raw class entries; SHA-256 `1dfebefc616049956ade6c4e85534d8c656a391da2a3a56a610f8d345e715745`.
- **Inspected reference:** [tree-sitter-0.24.4.md](sqx/Libraries/tree-sitter-0.24.4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/tree-sitter-0.24.4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/tree-sitter-0.24.4.jar" org.treesitter.AnonymousLanguage`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-AGENTIC-TREE-SITTER` and `FR-AGENTIC-TREE-SITTER-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/tree_sitter_0_24_4.py` — Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_tree_sitter.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-AGENTIC-TREE-SITTER-ANONYMOUS-LANGUAGE-CONTRACT` → `org.treesitter.AnonymousLanguage`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AGENTIC-TREE-SITTER-ANONYMOUS-LANGUAGE-COPY` → `org.treesitter.AnonymousLanguage.copy()Lorg/treesitter/TSLanguage;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_tree_sitter.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.5 FEAT-AGENTIC-TREE-SITTER-BASH - tree-sitter-bash-0.23.3.jar

## 1. Objective

- **Goal:** Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/tree-sitter-bash-0.23.3.jar`; 1 raw class entries; SHA-256 `b8a9b604722836699322ad9aaf124cf1d20336b421f1f38d54bd1662060830c8`.
- **Inspected reference:** [tree-sitter-bash-0.23.3.md](sqx/Libraries/tree-sitter-bash-0.23.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/tree-sitter-bash-0.23.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/tree-sitter-bash-0.23.3.jar" org.treesitter.TreeSitterBash`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-AGENTIC-TREE-SITTER-BASH` and `FR-AGENTIC-TREE-SITTER-BASH-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/tree_sitter_bash_0_23_3.py` — Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_tree_sitter_bash.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-AGENTIC-TREE-SITTER-BASH-TREE-SITTER-BASH-CONTRACT` → `org.treesitter.TreeSitterBash`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AGENTIC-TREE-SITTER-BASH-TREE-SITTER-BASH-TREE-SITTER-BASH` → `org.treesitter.TreeSitterBash.tree_sitter_bash()J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AGENTIC-TREE-SITTER-BASH-TREE-SITTER-BASH-COPY` → `org.treesitter.TreeSitterBash.copy()Lorg/treesitter/TSLanguage;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_tree_sitter_bash.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.6 FEAT-AGENTIC-SERVLET-SQAI - ServletSQAI.jar

## 1. Objective

- **Goal:** Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar`; 2 raw class entries; SHA-256 `545ec37398014a9bec74760dd6f4b1886f5c1b30c7e2fb63c50d2e27df5a382b`.
- **Inspected reference:** [ServletSQAI.md](sqx/Plugins/ServletSQAI.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar" com.strategyquant.plugin.Servlet.impl.SQAI.SQAIPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-AGENTIC-SERVLET-SQAI` and `FR-AGENTIC-SERVLET-SQAI-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/servletsqai.py` — Adapt the inspected agent/tool contract while preserving the typed host lifecycle and permission boundary.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_servlet_sqai.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_servlet_sqai-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 9:** `FR-AGENTIC-SERVLET-SQAI-SQAIPLUGIN-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.SQAI.SQAIPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AGENTIC-SERVLET-SQAI-SQAIPLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Servlet.impl.SQAI.SQAIPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 11:** `FR-AGENTIC-SERVLET-SQAI-SQAIPLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Servlet.impl.SQAI.SQAIPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_servlet_sqai.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.7 FEAT-AGENTIC-Q-CHAT - Q chat, session and host bridge

## 1. Objective

- **Goal:** Connect chat/config/state events and session/history/project operations.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/introduction-3/`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/extending/`.
- **Ownership:** proposed `FEAT-AGENTIC-Q-CHAT` and `FR-AGENTIC-Q-CHAT-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Missing AI core bodies and runtime/provider observations remain blockers; official documentation is intended behavior, not an executed local fixture.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/chat_service.py` — Connect chat/config/state events and session/history/project operations.
- **Create:** `app/plugins/agentic/sessions.py` — Connect chat/config/state events and session/history/project operations.
- **Create:** `app/plugins/agentic/contracts.py` — Connect chat/config/state events and session/history/project operations.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_q_chat.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_q_chat-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Pin getConfig/getState/registerHandler/request, late-subscriber state replay, attachments, stopped/failed turns and reconnect.
- [ ] **Step 3:** Ratify descriptive FRs and the owning README; separate documented intent from body-confirmed behavior.
- [ ] **Step 4:** Implement the retained behavior through host sessions/jobs/resources and explicit permissions.
- [ ] **Step 5:** Test isolated normal/denied/missing/cancellation cases, FR logs and artifact lineage.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_q_chat.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.8 FEAT-AGENTIC-Q-MEMORY - Q AI Brain and persistent research memory

## 1. Objective

- **Goal:** Own editable knowledge, research verdicts and learned procedures through host resources.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/trading-memory/plugin.json`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/introduction-3/`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/extending/`.
- **Ownership:** proposed `FEAT-AGENTIC-Q-MEMORY` and `FR-AGENTIC-Q-MEMORY-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Missing AI core bodies and runtime/provider observations remain blockers; official documentation is intended behavior, not an executed local fixture.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/memory.py` — Own editable knowledge, research verdicts and learned procedures through host resources.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_q_memory.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_q_memory-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Locate missing memory/project-store bodies; define the observed four-layer layout, edit/approval/removal rules and resource custody.
- [ ] **Step 3:** Ratify descriptive FRs and the owning README; separate documented intent from body-confirmed behavior.
- [ ] **Step 4:** Implement the retained behavior through host sessions/jobs/resources and explicit permissions.
- [ ] **Step 5:** Test isolated normal/denied/missing/cancellation cases, FR logs and artifact lineage.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_q_memory.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.9 FEAT-AGENTIC-Q-SCHEDULING - Q bounded continuations and cancellation

## 1. Objective

- **Goal:** Qualify scheduled continuation and stop behavior with explicit lifecycle ownership.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/introduction-3/`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/extending/`.
- **Ownership:** proposed `FEAT-AGENTIC-Q-SCHEDULING` and `FR-AGENTIC-Q-SCHEDULING-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Missing AI core bodies and runtime/provider observations remain blockers; official documentation is intended behavior, not an executed local fixture.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/scheduling.py` — Qualify scheduled continuation and stop behavior with explicit lifecycle ownership.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_q_scheduling.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_q_scheduling-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Inspect SQAIWakeup/SQAITurns implementations; cancellation calls alone do not prove races, completion or retry defaults.
- [ ] **Step 3:** Ratify descriptive FRs and the owning README; separate documented intent from body-confirmed behavior.
- [ ] **Step 4:** Implement the retained behavior through host sessions/jobs/resources and explicit permissions.
- [ ] **Step 5:** Test isolated normal/denied/missing/cancellation cases, FR logs and artifact lineage.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_q_scheduling.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.10 FEAT-AGENTIC-Q-PYTHON - Q isolated Python analysis and result artifacts

## 1. Objective

- **Goal:** Run approved analysis helpers and produce traceable reports in bounded execution contexts.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/python/runtime`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/introduction-3/`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/extending/`.
- **Ownership:** proposed `FEAT-AGENTIC-Q-PYTHON` and `FR-AGENTIC-Q-PYTHON-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Missing AI core bodies and runtime/provider observations remain blockers; official documentation is intended behavior, not an executed local fixture.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/python_analysis.py` — Run approved analysis helpers and produce traceable reports in bounded execution contexts.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_q_python.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_q_python-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Inspect shipped compiled helpers and actual execution protocol; specify time/output/resource limits and licensed-data restrictions from evidence.
- [ ] **Step 3:** Ratify descriptive FRs and the owning README; separate documented intent from body-confirmed behavior.
- [ ] **Step 4:** Implement the retained behavior through host sessions/jobs/resources and explicit permissions.
- [ ] **Step 5:** Test isolated normal/denied/missing/cancellation cases, FR logs and artifact lineage.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_q_python.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.11 FEAT-AGENTIC-Q-EXTENSIONS - Q skills, commands, agents and knowledge resources

## 1. Objective

- **Goal:** Discover and validate approved Q extension resources without executing donor instructions as project authority.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/user/extend/AIPlugins/_templates`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/introduction-3/`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/extending/`.
- **Ownership:** proposed `FEAT-AGENTIC-Q-EXTENSIONS` and `FR-AGENTIC-Q-EXTENSIONS-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Missing AI core bodies and runtime/provider observations remain blockers; official documentation is intended behavior, not an executed local fixture.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/extensions.py` — Discover and validate approved Q extension resources without executing donor instructions as project authority.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_q_extensions.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_q_extensions-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Inspect templates/manifests, command/tool discovery and reload; record missing skill/rule/agent texts, provider/model availability and entitlement gaps.
- [ ] **Step 3:** Ratify descriptive FRs and the owning README; separate documented intent from body-confirmed behavior.
- [ ] **Step 4:** Implement the retained behavior through host sessions/jobs/resources and explicit permissions.
- [ ] **Step 5:** Test isolated normal/denied/missing/cancellation cases, FR logs and artifact lineage.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_q_extensions.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.12 FEAT-AGENTIC-Q-COMPLETION - Q result-tab completion and model/credit boundary

## 1. Objective

- **Goal:** Expose independently qualified stateless completion and model-selection contracts.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/introduction-3/`.
- **Donor:** `https://strategyquant.com/doc/q-ai-assistant/extending/`.
- **Ownership:** proposed `FEAT-AGENTIC-Q-COMPLETION` and `FR-AGENTIC-Q-COMPLETION-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Missing AI core bodies and runtime/provider observations remain blockers; official documentation is intended behavior, not an executed local fixture.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/completion.py` — Expose independently qualified stateless completion and model-selection contracts.
- **Create:** `app/plugins/agentic/models.py` — Expose independently qualified stateless completion and model-selection contracts.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_q_completion.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_q_completion-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Inspect handleComplete/handleModelSelect and result-plugin AI_COMPLETE integration; qualify concurrency/limits, cache/regenerate and provider denial without spending credits.
- [ ] **Step 3:** Ratify descriptive FRs and the owning README; separate documented intent from body-confirmed behavior.
- [ ] **Step 4:** Implement the retained behavior through host sessions/jobs/resources and explicit permissions.
- [ ] **Step 5:** Test isolated normal/denied/missing/cancellation cases, FR logs and artifact lineage.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_q_completion.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.13 FEAT-AGENTIC-PLUGIN-AC-STRATEGY - ac-strategy Q resource plugin

## 1. Objective

- **Goal:** Qualify the ac-strategy procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/ac-strategy/plugin.json — SHA-256 6e7a0119160f1cdf7bd5581dc9a8acf79601dcbfe3997cf4c1765d3aaf01dc79`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/ac-strategy`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-AC-STRATEGY` and `FR-AGENTIC-PLUGIN-AC-STRATEGY-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json; 8 .pyc; 1 .sqx; 1 .tpl. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/ac_strategy.py` — Qualify the ac-strategy procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_ac_strategy.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_ac_strategy-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_ac_strategy.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.14 FEAT-AGENTIC-PLUGIN-ALGOWIZARD-LAB - algowizard-lab Q resource plugin

## 1. Objective

- **Goal:** Qualify the algowizard-lab procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/algowizard-lab/plugin.json — SHA-256 5fda7f931dd5e14845c7b058a21b13ffd5417190f0b89e3d3dc997cfc189c5a6`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/algowizard-lab`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-ALGOWIZARD-LAB` and `FR-AGENTIC-PLUGIN-ALGOWIZARD-LAB-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json; 9 .pyc. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/algowizard_lab.py` — Qualify the algowizard-lab procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_algowizard_lab.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_algowizard_lab-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_algowizard_lab.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.15 FEAT-AGENTIC-PLUGIN-ANALYSIS-TABS - analysis-tabs Q resource plugin

## 1. Objective

- **Goal:** Qualify the analysis-tabs procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/analysis-tabs/plugin.json — SHA-256 09e96a18de870ce514c947b3c5d388f9ba411b679658d93a1d14cbec3c4ff950`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/analysis-tabs`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-ANALYSIS-TABS` and `FR-AGENTIC-PLUGIN-ANALYSIS-TABS-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 3 .html; 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/analysis_tabs.py` — Qualify the analysis-tabs procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_analysis_tabs.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_analysis_tabs-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_analysis_tabs.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.16 FEAT-AGENTIC-PLUGIN-AUTO-RESEARCH - auto-research Q resource plugin

## 1. Objective

- **Goal:** Qualify the auto-research procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/auto-research/plugin.json — SHA-256 c34dd65ad45aa95dfcff070e712be25b7c30f243f880d707e7a3e749d7df3db6`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/auto-research`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-AUTO-RESEARCH` and `FR-AGENTIC-PLUGIN-AUTO-RESEARCH-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/auto_research.py` — Qualify the auto-research procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_auto_research.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_auto_research-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_auto_research.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.17 FEAT-AGENTIC-PLUGIN-BREAKOUT-PROJECT-FACTORY - breakout-project-factory Q resource plugin

## 1. Objective

- **Goal:** Qualify the breakout-project-factory procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/breakout-project-factory/plugin.json — SHA-256 c2bed75443a9319af289ad8e63dade7fa0ebfd407d095cd05c4bd61d5692fd4b`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/breakout-project-factory`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-BREAKOUT-PROJECT-FACTORY` and `FR-AGENTIC-PLUGIN-BREAKOUT-PROJECT-FACTORY-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/breakout_project_factory.py` — Qualify the breakout-project-factory procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_breakout_project_factory.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_breakout_project_factory-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_breakout_project_factory.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.18 FEAT-AGENTIC-PLUGIN-CUSTOM-PAGE - custom-page Q resource plugin

## 1. Objective

- **Goal:** Qualify the custom-page procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/custom-page/plugin.json — SHA-256 296fa7c982561f07d56780b1f3d7923398e751ec4a08c8b9af860cd7b953d199`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/custom-page`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-CUSTOM-PAGE` and `FR-AGENTIC-PLUGIN-CUSTOM-PAGE-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/custom_page.py` — Qualify the custom-page procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_custom_page.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_custom_page-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_custom_page.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.19 FEAT-AGENTIC-PLUGIN-MARKET-ANALYST - market-analyst Q resource plugin

## 1. Objective

- **Goal:** Qualify the market-analyst procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/market-analyst/plugin.json — SHA-256 3353eecb77034124bd11315051ddab7697c4d5d5c086ab75e444950f8b3414ef`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/market-analyst`.
- **Known gap:** Readable `skills/analyze-market/engine/analyze_market.py` disappeared during final recheck (`SQX145-EV-000173`); its removal cause and remaining compiled-body equivalence are unverified. Recover or independently qualify the actual algorithm before translation.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-MARKET-ANALYST` and `FR-AGENTIC-PLUGIN-MARKET-ANALYST-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json; 2 .pyc. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/market_analyst.py` — Qualify the market-analyst procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_market_analyst.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_market_analyst-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_market_analyst.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.20 FEAT-AGENTIC-PLUGIN-PLUGIN-MAKER - plugin-maker Q resource plugin

## 1. Objective

- **Goal:** Qualify the plugin-maker procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/plugin-maker/plugin.json — SHA-256 d3b801ac0e6d0aee6c8260ac8a1f509fdf1b09fd72f938fc66c389c3e1bd73a0`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/plugin-maker`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-PLUGIN-MAKER` and `FR-AGENTIC-PLUGIN-PLUGIN-MAKER-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/plugin_maker.py` — Qualify the plugin-maker procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_plugin_maker.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_plugin_maker-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_plugin_maker.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.21 FEAT-AGENTIC-PLUGIN-QUANT-RESEARCH - quant-research Q resource plugin

## 1. Objective

- **Goal:** Qualify the quant-research procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/quant-research/plugin.json — SHA-256 51763f0f6b5532501529b7c7566693d71f331240c3c2c47c73a1653ae47f8e1e`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/quant-research`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-QUANT-RESEARCH` and `FR-AGENTIC-PLUGIN-QUANT-RESEARCH-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/quant_research.py` — Qualify the quant-research procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_quant_research.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_quant_research-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_quant_research.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.22 FEAT-AGENTIC-PLUGIN-SQX-INDICATOR-BUILDER - sqx-indicator-builder Q resource plugin

## 1. Objective

- **Goal:** Qualify the sqx-indicator-builder procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-indicator-builder/plugin.json — SHA-256 fb683eead55529e0d410941ccadf268613cff92ae85a3b44e2b80a2d3be223dc`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-indicator-builder`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-SQX-INDICATOR-BUILDER` and `FR-AGENTIC-PLUGIN-SQX-INDICATOR-BUILDER-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 2 .csv; 2 .json; 13 .ps1; 23 .pyc; 1 .sqx. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/sqx_indicator_builder.py` — Qualify the sqx-indicator-builder procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_sqx_indicator_builder.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_sqx_indicator_builder-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_sqx_indicator_builder.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.23 FEAT-AGENTIC-PLUGIN-SQX-PROJECT - sqx-project Q resource plugin

## 1. Objective

- **Goal:** Qualify the sqx-project procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-project/plugin.json — SHA-256 1c213515ac220bc6e427a43519fc41465f14b48f3fe5acbb782b0cbe13e55a00`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-project`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-SQX-PROJECT` and `FR-AGENTIC-PLUGIN-SQX-PROJECT-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json; 10 .pyc. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/sqx_project.py` — Qualify the sqx-project procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_sqx_project.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_sqx_project-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_sqx_project.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.24 FEAT-AGENTIC-PLUGIN-SQX-REPORTS - sqx-reports Q resource plugin

## 1. Objective

- **Goal:** Qualify the sqx-reports procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-reports/plugin.json — SHA-256 fae47a1c92780327bf292fe696213844dbf21b6757c1e332c45025317e271e1c`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-reports`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-SQX-REPORTS` and `FR-AGENTIC-PLUGIN-SQX-REPORTS-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .css; 1 .html; 1 .js; 1 .json; 1 .md; 9 .pyc. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/sqx_reports.py` — Qualify the sqx-reports procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_sqx_reports.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_sqx_reports-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_sqx_reports.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.25 FEAT-AGENTIC-PLUGIN-SQX-SNIPPETS - sqx-snippets Q resource plugin

## 1. Objective

- **Goal:** Qualify the sqx-snippets procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-snippets/plugin.json — SHA-256 431c22ce374439553ae3f82515f6844f4c4c49b96811ea3077adaafbd839957c`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-snippets`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-SQX-SNIPPETS` and `FR-AGENTIC-PLUGIN-SQX-SNIPPETS-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/sqx_snippets.py` — Qualify the sqx-snippets procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_sqx_snippets.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_sqx_snippets-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_sqx_snippets.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.26 FEAT-AGENTIC-PLUGIN-SQX-STRATEGY - sqx-strategy Q resource plugin

## 1. Objective

- **Goal:** Qualify the sqx-strategy procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-strategy/plugin.json — SHA-256 96a424c9852617e340571bd241f39bdc5106009f33bcc22e6b3d17336b86ec27`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/sqx-strategy`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-SQX-STRATEGY` and `FR-AGENTIC-PLUGIN-SQX-STRATEGY-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 2 .json; 16 .pyc; 1 .sqx. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/sqx_strategy.py` — Qualify the sqx-strategy procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_sqx_strategy.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_sqx_strategy-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_sqx_strategy.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.27 FEAT-AGENTIC-PLUGIN-STRATEGY-ANALYST - strategy-analyst Q resource plugin

## 1. Objective

- **Goal:** Qualify the strategy-analyst procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/strategy-analyst/plugin.json — SHA-256 05174d9356a0b28707f69ec5349c0a9a8914ad5b97e49232d16ff2b055e992c6`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/strategy-analyst`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-STRATEGY-ANALYST` and `FR-AGENTIC-PLUGIN-STRATEGY-ANALYST-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/strategy_analyst.py` — Qualify the strategy-analyst procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_strategy_analyst.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_strategy_analyst-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_strategy_analyst.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.28 FEAT-AGENTIC-PLUGIN-STRATEGY-ARCHITECT - strategy-architect Q resource plugin

## 1. Objective

- **Goal:** Qualify the strategy-architect procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/strategy-architect/plugin.json — SHA-256 774b26edb443fa07d29bbe8a7cfa3ce55556cbc4d3646639a47184ac506cc9f0`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/strategy-architect`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-STRATEGY-ARCHITECT` and `FR-AGENTIC-PLUGIN-STRATEGY-ARCHITECT-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/strategy_architect.py` — Qualify the strategy-architect procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_strategy_architect.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_strategy_architect-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_strategy_architect.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.29 FEAT-AGENTIC-PLUGIN-TRADING-MEMORY - trading-memory Q resource plugin

## 1. Objective

- **Goal:** Qualify the trading-memory procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/trading-memory/plugin.json — SHA-256 f2b60d29aefef041b61fd7fca1f9332e29c74b76c936a3d9efe8e235c89116eb`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/trading-memory`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-TRADING-MEMORY` and `FR-AGENTIC-PLUGIN-TRADING-MEMORY-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/trading_memory.py` — Qualify the trading-memory procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_trading_memory.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_trading_memory-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_trading_memory.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.30 FEAT-AGENTIC-PLUGIN-UI-PILOT - ui-pilot Q resource plugin

## 1. Objective

- **Goal:** Qualify the ui-pilot procedure/plugin contribution and its actual callable payload.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/ui-pilot/plugin.json — SHA-256 11e0bf1baaa53c6fccf1e8856931ffb3f7a8d646bd84f2bc5beba42574b3a0ce`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/ui-pilot`.
- **Ownership:** proposed `FEAT-AGENTIC-PLUGIN-UI-PILOT` and `FR-AGENTIC-PLUGIN-UI-PILOT-CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Shipped payload inventory: 1 .json. A manifest description is not the missing algorithm; compiled helper bytes are not source-confirmed logic.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the approved Q controls and typed host tools.

## 3. File Changes

- **Create:** `app/plugins/agentic/skills/ui_pilot.py` — Qualify the ui-pilot procedure/plugin contribution and its actual callable payload.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_agentic_plugin_ui_pilot.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-agentic_plugin_ui_pilot-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate manifest, helper/template/skill/command/agent/rule files; treat donor instructions as research data.
- [ ] **Step 3:** Inspect actual helper bodies or independently observed procedure behavior; record unavailable payloads explicitly.
- [ ] **Step 4:** Map each retained operation to descriptive FRs, permissions, host tools and output/resource contracts.
- [ ] **Step 5:** Test a reproducible procedure run, denied/unavailable inputs, stop behavior and evidence/journal outputs.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_agentic_plugin_ui_pilot.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 19.31 P19 - integration - Q goal through discovery, build, retest and research record

## 1. Objective

- **Goal:** Finish a qualified research request with traceable strategy/testing outputs and retained UI connected.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI`.
- **Ownership:** proposed `P19` and `FR--CONSUMED-CONTRACTS`; owner `app/plugins/agentic/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Static source discovery and UI rendering cannot qualify a research loop; P18 remains independent release qualification.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/SQAIChatService.js`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect the retained AI Assistant to approved host capabilities.

## 3. File Changes

- **Create:** `app/plugins/agentic/workflow.py` — Finish a qualified research request with traceable strategy/testing outputs and retained UI connected.
- **Create:** `app/plugins/agentic/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_p19.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AIAssistant/AIAssistantWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/AIAssistant/agenticClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/workspace/AIAssistant/catalog.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-p19-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Ratify all participating Q/project/data/engine capabilities and outstanding core/provider gates.
- [ ] **Step 3:** Run an isolated goal → hypothesis → project/build → retest → result/journal workflow with explicit bounded execution.
- [ ] **Step 4:** Exercise denial, unavailable tool/data/model, stop, partial failure and resume/reconnect; preserve provenance and no implicit result save.
- [ ] **Step 5:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 6:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_p19.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.

## Phase completion gate

- [ ] Every retained FEAT/FR has an owner, independently supported contract and normal/boundary/failure fixture.
- [ ] Every applicable backend + frontend workflow works against an isolated real host; no missing core or production mock fallback.
- [ ] Model/provider permissions, credits, licensed-data handling and cancellation are qualified without unauthorized external effects.
- [ ] Record walkthrough and tracker evidence; P18 final qualification still required.
