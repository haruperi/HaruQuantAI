# P13 — Custom projects, Task Manager, conditions and task actions

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P02,P04,P07,P08,P09,P10,P11,P12.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 46 tasks; current archive allocations and resource/integration tasks only.

# 13.1 FEAT-PROJECT-ACTIVATION - activation-1.1.1.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/activation-1.1.1.jar`; 38 raw class entries; SHA-256 `ae475120e9fcd99b4b00b38329bd61cdc5eb754eee03fe66c01f50e137724f99`.
- **Inspected reference:** [activation-1.1.1.md](sqx/Libraries/activation-1.1.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/activation-1.1.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/activation-1.1.1.jar" com.sun.activation.registries.LineTokenizer`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Custom Projects through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/plugins/tasks/notifications.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/external_process.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_activation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_activation.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-PROJECT-ACTIVATION-LINE-TOKENIZER-CONTRACT` → `com.sun.activation.registries.LineTokenizer`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-PROJECT-ACTIVATION-LINE-TOKENIZER-SKIP-WHITE-SPACE` → `com.sun.activation.registries.LineTokenizer.skipWhiteSpace()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-ACTIVATION-LINE-TOKENIZER-HAS-MORE-TOKENS` → `com.sun.activation.registries.LineTokenizer.hasMoreTokens()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_activation.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.


# 13.2 FEAT-PROJECT-COMMONS-EMAIL - commons-email-1.4.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-email-1.4.jar`; 20 raw class entries; SHA-256 `685de61b5987602a7170b1c64969d966ab0616e5aff170b78c4c109638662151`.
- **Inspected reference:** [commons-email-1.4.md](sqx/Libraries/commons-email-1.4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-email-1.4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-email-1.4.jar" org.apache.commons.mail.ByteArrayDataSource`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Custom Projects through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/tasks/notifications.py` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/tasks/external_process.py` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/tasks/README.md` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_commons_email.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_commons_email.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-PROJECT-COMMONS-EMAIL-BYTE-ARRAY-DATA-SOURCE-CONTRACT` → `org.apache.commons.mail.ByteArrayDataSource`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-PROJECT-COMMONS-EMAIL-BYTE-ARRAY-DATA-SOURCE-BYTE-ARRAY-DATA-SOURCE` → `org.apache.commons.mail.ByteArrayDataSource.byteArrayDataSource(Ljava/io/InputStream;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-COMMONS-EMAIL-BYTE-ARRAY-DATA-SOURCE-GET-CONTENT-TYPE` → `org.apache.commons.mail.ByteArrayDataSource.getContentType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_commons_email.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.


# 13.3 FEAT-PROJECT-COMMONS-EXEC - commons-exec-1.3.jar

## 1. Objective

- **Goal:** Execute qualified external processes with scoped authority and owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-exec-1.3.jar`; 37 raw class entries; SHA-256 `cb49812dc1bfb0ea4f20f398bcae1a88c6406e213e67f7524fb10d4f8ad9347b`.
- **Inspected reference:** [commons-exec-1.3.md](sqx/Libraries/commons-exec-1.3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-exec-1.3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-exec-1.3.jar" org.apache.commons.exec.CommandLine`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Custom Projects through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/tasks/notifications.py` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/tasks/external_process.py` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/tasks/README.md` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_commons_exec.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_commons_exec.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute qualified external processes with scoped authority and owned lifecycle; verify allowlisted invocation, timeout, exit failure, cancellation and redacted output.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-PROJECT-COMMONS-EXEC-COMMAND-LINE-CONTRACT` → `org.apache.commons.exec.CommandLine`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-PROJECT-COMMONS-EXEC-COMMAND-LINE-PARSE` → `org.apache.commons.exec.CommandLine.parse(Ljava/lang/String;)Lorg/apache/commons/exec/CommandLine;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-COMMONS-EXEC-COMMAND-LINE-PARSE-B4A8BEDE` → `org.apache.commons.exec.CommandLine.parse(Ljava/lang/String;Ljava/util/Map;)Lorg/apache/commons/exec/CommandLine;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_commons_exec.py --no-cov`; expect allowlisted invocation, timeout, exit failure, cancellation and redacted output; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture allowlisted invocation, timeout, exit failure, cancellation and redacted output and visible failures.


# 13.4 FEAT-PROJECT-JAVAX-MAIL - javax.mail-1.5.2.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/javax.mail-1.5.2.jar`; 319 raw class entries; SHA-256 `fb3becba9b18c010b243e32211c26fcda1115e8a47b759d8d0cf288f929029b2`.
- **Inspected reference:** [javax.mail-1.5.2.md](sqx/Libraries/javax.mail-1.5.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/javax.mail-1.5.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/javax.mail-1.5.2.jar" com.sun.mail.auth.MD4`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Custom Projects through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/tasks/notifications.py` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/tasks/external_process.py` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/tasks/README.md` (proposed earlier in FEAT-PROJECT-ACTIVATION)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_javax_mail.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_javax_mail.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-PROJECT-JAVAX-MAIL-MD4-CONTRACT` → `com.sun.mail.auth.MD4`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-PROJECT-JAVAX-MAIL-MD4-DIGEST` → `com.sun.mail.auth.MD4.digest([B)[B`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-JAVAX-MAIL-MD4-IMPL-RESET` → `com.sun.mail.auth.MD4.implReset()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_javax_mail.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.


# 13.5 FEAT-PROJECT-APP-TASK-MANAGER - AppTaskManager.jar

## 1. Objective

- **Goal:** Mount the TaskManager workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppTaskManager/AppTaskManager.jar`; 2 raw class entries; SHA-256 `c6d7819512130bf30f32f2368f0fc64f2532718b71dc0df5d0b2089d1d9db8d7`.
- **Inspected reference:** [AppTaskManager.md](sqx/CustomProjects/AppTaskManager.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppTaskManager/AppTaskManager.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppTaskManager/AppTaskManager.jar" com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/CustomProjects/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppTaskManager`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppTaskManager/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/CustomProjects/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CustomProjects/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CustomProjects/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CustomProjects/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_app_task_manager.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_app_task_manager.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-app-task-manager.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the TaskManager workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-APP-TASK-MANAGER-TASK-MANAGER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-APP-TASK-MANAGER-TASK-MANAGER-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-APP-TASK-MANAGER-TASK-MANAGER-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_app_task_manager.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-app-task-manager.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-APP-TASK-MANAGER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.6 FEAT-PROJECT-PROJECT-CONDITION-CYCLES-COUNT - ProjectConditionCyclesCount.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar`; 1 raw class entries; SHA-256 `73105bf7c747bc010b92e5141ab59d3b5140bf3285834f6eccd47210d819b9cf`.
- **Inspected reference:** [ProjectConditionCyclesCount.md](sqx/Shared/ProjectConditionCyclesCount.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar" com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/ProjectConditionCyclesCount/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/ProjectConditionCyclesCount/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionCyclesCount/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionCyclesCount/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionCyclesCount/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_project_condition_cycles_count.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_project_condition_cycles_count.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-project-condition-cycles-count.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-PROJECT-CONDITION-CYCLES-COUNT-CYCLES-COUNT-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-PROJECT-CONDITION-CYCLES-COUNT-CYCLES-COUNT-CONDITION-PLUGIN-GET-NAME` → `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-PROJECT-CONDITION-CYCLES-COUNT-CYCLES-COUNT-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin.getTitle()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_cycles_count.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-project-condition-cycles-count.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-PROJECT-CONDITION-CYCLES-COUNT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.7 FEAT-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED - ProjectConditionGoToActivated.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated/ProjectConditionGoToActivated.jar`; 1 raw class entries; SHA-256 `c33c5c93ee9ed6790eebd354ea632699431b77d5708305e196af8432582acdfe`.
- **Inspected reference:** [ProjectConditionGoToActivated.md](sqx/Shared/ProjectConditionGoToActivated.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated/ProjectConditionGoToActivated.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated/ProjectConditionGoToActivated.jar" com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/ProjectConditionGoToActivated/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/ProjectConditionGoToActivated/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionGoToActivated/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionGoToActivated/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionGoToActivated/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_project_condition_go_to_activated.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_project_condition_go_to_activated.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-project-condition-go-to-activated.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED-GO-TO-ACTIVATED-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED-GO-TO-ACTIVATED-CONDITION-PLUGIN-GET-NAME` → `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED-GO-TO-ACTIVATED-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin.getTitle()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_go_to_activated.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-project-condition-go-to-activated.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.8 FEAT-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED - ProjectConditionGoToEvaluated.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated/ProjectConditionGoToEvaluated.jar`; 1 raw class entries; SHA-256 `519f150819c222c443ffef6678eeb201a5114579db0aaf8c4dfda88cc058def8`.
- **Inspected reference:** [ProjectConditionGoToEvaluated.md](sqx/Shared/ProjectConditionGoToEvaluated.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated/ProjectConditionGoToEvaluated.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated/ProjectConditionGoToEvaluated.jar" com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/ProjectConditionGoToEvaluated/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/ProjectConditionGoToEvaluated/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionGoToEvaluated/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionGoToEvaluated/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionGoToEvaluated/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_project_condition_go_to_evaluated.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_project_condition_go_to_evaluated.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-project-condition-go-to-evaluated.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED-GO-TO-EVALUATED-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED-GO-TO-EVALUATED-CONDITION-PLUGIN-GET-NAME` → `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED-GO-TO-EVALUATED-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin.getTitle()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_go_to_evaluated.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-project-condition-go-to-evaluated.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.9 FEAT-PROJECT-PROJECT-CONDITION-RESULTS-COUNT - ProjectConditionResultsCount.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount/ProjectConditionResultsCount.jar`; 1 raw class entries; SHA-256 `d2dd220f69c28409deec1c210b910f716eee3033ad47b49d55b278e6f644d60e`.
- **Inspected reference:** [ProjectConditionResultsCount.md](sqx/Shared/ProjectConditionResultsCount.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount/ProjectConditionResultsCount.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount/ProjectConditionResultsCount.jar" com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/ProjectConditionResultsCount/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/ProjectConditionResultsCount/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionResultsCount/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionResultsCount/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionResultsCount/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_project_condition_results_count.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_project_condition_results_count.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-project-condition-results-count.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-PROJECT-CONDITION-RESULTS-COUNT-RESULTS-COUNT-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-PROJECT-CONDITION-RESULTS-COUNT-RESULTS-COUNT-CONDITION-PLUGIN-GET-NAME` → `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-PROJECT-CONDITION-RESULTS-COUNT-RESULTS-COUNT-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin.getTitle()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_results_count.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-project-condition-results-count.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-PROJECT-CONDITION-RESULTS-COUNT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.10 FEAT-PROJECT-PROJECT-CONDITION-RUN-TIME - ProjectConditionRunTime.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime/ProjectConditionRunTime.jar`; 1 raw class entries; SHA-256 `9886a4ee0450601cbebbe68cd1ff3bff426cb095e02d0fe0201907eab197dad9`.
- **Inspected reference:** [ProjectConditionRunTime.md](sqx/Shared/ProjectConditionRunTime.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime/ProjectConditionRunTime.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime/ProjectConditionRunTime.jar" com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/ProjectConditionRunTime/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/ProjectConditionRunTime/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionRunTime/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionRunTime/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionRunTime/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_project_condition_run_time.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_project_condition_run_time.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-project-condition-run-time.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-PROJECT-CONDITION-RUN-TIME-RUNTIME-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-PROJECT-CONDITION-RUN-TIME-RUNTIME-CONDITION-PLUGIN-GET-NAME` → `com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-PROJECT-CONDITION-RUN-TIME-RUNTIME-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin.getTitle()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_run_time.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-project-condition-run-time.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-PROJECT-CONDITION-RUN-TIME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.11 FEAT-PROJECT-SERVLET-PROJECT - ServletProject.jar

## 1. Objective

- **Goal:** Expose Project commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletProject/ServletProject.jar`; 13 raw class entries; SHA-256 `39cb9a77afca650b62226815fe1a5e43f465da620b291eab0a9f0be98036d7ed`.
- **Inspected reference:** [ServletProject.md](sqx/CustomProjects/ServletProject.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletProject/ServletProject.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletProject/ServletProject.jar" com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/ServletProject/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletProject`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/ServletProject/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ServletProject/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ServletProject/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ServletProject/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_servlet_project.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_servlet_project.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-servlet-project.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose Project commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SERVLET-PROJECT-PROJECT-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SERVLET-PROJECT-PROJECT-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SERVLET-PROJECT-PROJECT-SERVLET-GET-CUSTOM-ANALYSIS-INFO` → `com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet.getCustomAnalysisInfo(Ljava/util/Map;)Lcom/strategyquant/tradinglib/customanalysis/CustomAnalysisInfo;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_servlet_project.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-servlet-project.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SERVLET-PROJECT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.12 FEAT-PROJECT-SETTINGS-APPLY-MASS-CONFIG - SettingsApplyMassConfig.jar

## 1. Objective

- **Goal:** Apply validated configuration across selected resources transactionally.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/SettingsApplyMassConfig.jar`; 1 raw class entries; SHA-256 `c6ce1b92dae7d4dd00f3bc495978230628bacd0b81c004b85c083eb48f492e6f`.
- **Inspected reference:** [SettingsApplyMassConfig.md](sqx/Shared/SettingsApplyMassConfig.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/SettingsApplyMassConfig.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/SettingsApplyMassConfig.jar" com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsApplyMassConfig/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/ApplyMassConfigService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/ApplyMassConfigCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/applyMassConfig.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsApplyMassConfig/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsApplyMassConfig/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsApplyMassConfig/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_apply_mass_config.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_apply_mass_config.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-apply-mass-config.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Apply validated configuration across selected resources transactionally; verify target selection, compatibility, rollback and unaffected settings.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-APPLY-MASS-CONFIG-SETTINGS-APPLY-MASS-CONFIG-CONTRACT` → `com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-APPLY-MASS-CONFIG-SETTINGS-APPLY-MASS-CONFIG-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-APPLY-MASS-CONFIG-SETTINGS-APPLY-MASS-CONFIG-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_apply_mass_config.py --no-cov`; expect target selection, compatibility, rollback and unaffected settings; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target selection, compatibility, rollback and unaffected settings and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-apply-mass-config.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-APPLY-MASS-CONFIG; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.13 FEAT-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT - SettingsCallExternalScript.jar

## 1. Objective

- **Goal:** Execute qualified external processes with scoped authority and owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScript.jar`; 1 raw class entries; SHA-256 `29fab77fa8681e74516379fd4083aa8af33e7cd960cea5c0143614645daf788f`.
- **Inspected reference:** [SettingsCallExternalScript.md](sqx/Shared/SettingsCallExternalScript.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScript.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScript.jar" com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsCallExternalScript/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScriptService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScriptCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/settingsCallExternalScript.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsCallExternalScript/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsCallExternalScript/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsCallExternalScript/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_call_external_script.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_call_external_script.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-call-external-script.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute qualified external processes with scoped authority and owned lifecycle; verify allowlisted invocation, timeout, exit failure, cancellation and redacted output.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT-SETTINGS-CALL-EXTERNAL-SCRIPT-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT-SETTINGS-CALL-EXTERNAL-SCRIPT-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT-SETTINGS-CALL-EXTERNAL-SCRIPT-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_call_external_script.py --no-cov`; expect allowlisted invocation, timeout, exit failure, cancellation and redacted output; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture allowlisted invocation, timeout, exit failure, cancellation and redacted output and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-call-external-script.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.14 FEAT-PROJECT-SETTINGS-CLEAR-DATABANKS - SettingsClearDatabanks.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanks.jar`; 1 raw class entries; SHA-256 `428575e646c03d4e8b1f353f2d05fc1061d9728f6ac47311886fbd2b0c2ad215`.
- **Inspected reference:** [SettingsClearDatabanks.md](sqx/Shared/SettingsClearDatabanks.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanks.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanks.jar" com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsClearDatabanks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanksCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/clearDatabanks.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsClearDatabanks/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsClearDatabanks/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsClearDatabanks/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_clear_databanks.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_clear_databanks.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-clear-databanks.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-CLEAR-DATABANKS-SETTINGS-FILTERING-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-CLEAR-DATABANKS-SETTINGS-FILTERING-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-CLEAR-DATABANKS-SETTINGS-FILTERING-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_clear_databanks.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-clear-databanks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-CLEAR-DATABANKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.15 FEAT-PROJECT-SETTINGS-CUSTOM-ANALYSIS - SettingsCustomAnalysis.jar

## 1. Objective

- **Goal:** Implement validated CustomAnalysis settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar`; 1 raw class entries; SHA-256 `7e59d1b49adda5886ecbdc49a06ade5ea2c54fecb05e599283c08b00b6e75cee`.
- **Inspected reference:** [SettingsCustomAnalysis.md](sqx/Shared/SettingsCustomAnalysis.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar" com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsCustomAnalysis/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysisService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysisCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/settingsCustomAnalysis.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsCustomAnalysis/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsCustomAnalysis/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsCustomAnalysis/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_custom_analysis.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_custom_analysis.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-custom-analysis.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated CustomAnalysis settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_custom_analysis.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-custom-analysis.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-CUSTOM-ANALYSIS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.16 FEAT-PROJECT-SETTINGS-DELETE-FILE - SettingsDeleteFile.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFile.jar`; 1 raw class entries; SHA-256 `d2e634544c965f7c1e7b9dfc91564e382d315ac11bbb3dfe2b7f6e109fed20fa`.
- **Inspected reference:** [SettingsDeleteFile.md](sqx/Shared/SettingsDeleteFile.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFile.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFile.jar" com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsDeleteFile/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFileService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFileCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/settingsDeleteFile.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsDeleteFile/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsDeleteFile/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsDeleteFile/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_delete_file.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_delete_file.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-delete-file.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-DELETE-FILE-SETTINGS-DELETE-FILE-CONTRACT` → `com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-DELETE-FILE-SETTINGS-DELETE-FILE-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-DELETE-FILE-SETTINGS-DELETE-FILE-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_delete_file.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-delete-file.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-DELETE-FILE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.17 FEAT-PROJECT-SETTINGS-FILTERING - SettingsFiltering.jar

## 1. Objective

- **Goal:** Implement validated Filtering settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFiltering.jar`; 1 raw class entries; SHA-256 `1431d0dd1b620a5cd495eda8f480ce9850abeac81736b718fd9f4049c342d95c`.
- **Inspected reference:** [SettingsFiltering.md](sqx/Shared/SettingsFiltering.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFiltering.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFiltering.jar" com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsFiltering/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFilteringService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFilteringCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsFiltering/settingsFiltering.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsFiltering/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsFiltering/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsFiltering/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_filtering.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_filtering.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-filtering.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Filtering settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-FILTERING-SETTINGS-FILTERING-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-FILTERING-SETTINGS-FILTERING-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-FILTERING-SETTINGS-FILTERING-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_filtering.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-filtering.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-FILTERING; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.18 FEAT-PROJECT-SETTINGS-GO-TO-TASK - SettingsGoToTask.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTask.jar`; 1 raw class entries; SHA-256 `a591e48eb3da111a334b8ab7b1a8aa2b6eb793d1336a51b86e2d74a9e8d9038b`.
- **Inspected reference:** [SettingsGoToTask.md](sqx/Shared/SettingsGoToTask.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTask.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTask.jar" com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsGoToTask/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTaskService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTaskCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/settingsGoToTask.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsGoToTask/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsGoToTask/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsGoToTask/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_go_to_task.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_go_to_task.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-go-to-task.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-GO-TO-TASK-SETTINGS-GO-TO-TASK-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-GO-TO-TASK-SETTINGS-GO-TO-TASK-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-GO-TO-TASK-SETTINGS-GO-TO-TASK-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_go_to_task.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-go-to-task.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-GO-TO-TASK; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.19 FEAT-PROJECT-SETTINGS-LOAD-FROM-FILES - SettingsLoadFromFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFiles.jar`; 1 raw class entries; SHA-256 `e2d006dc4011cf1915f610add048c56d73cfcd4843b8f9a72accefb1339bcf7b`.
- **Inspected reference:** [SettingsLoadFromFiles.md](sqx/Shared/SettingsLoadFromFiles.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFiles.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFiles.jar" com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsLoadFromFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFilesService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFilesCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/settingsLoadFromFiles.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsLoadFromFiles/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsLoadFromFiles/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsLoadFromFiles/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_load_from_files.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_load_from_files.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-load-from-files.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-LOAD-FROM-FILES-SETTINGS-LOAD-FROM-FILES-CONTRACT` → `com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-LOAD-FROM-FILES-SETTINGS-LOAD-FROM-FILES-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-LOAD-FROM-FILES-SETTINGS-LOAD-FROM-FILES-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_load_from_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-load-from-files.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-LOAD-FROM-FILES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.20 FEAT-PROJECT-SETTINGS-LOG-DATABANK-STATS - SettingsLogDatabankStats.jar

## 1. Objective

- **Goal:** Project and log qualified databank statistics.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/SettingsLogDatabankStats.jar`; 1 raw class entries; SHA-256 `1db122546ead382c13548e6ee1a377c93498e0ef210f827c83c5f02ee235baaa`.
- **Inspected reference:** [SettingsLogDatabankStats.md](sqx/Shared/SettingsLogDatabankStats.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/SettingsLogDatabankStats.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/SettingsLogDatabankStats.jar" com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsLogDatabankStats/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/LogDatabankStatsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/LogDatabankStatsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/directives/LogDatabankStatsTypeCtrl.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsLogDatabankStats/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsLogDatabankStats/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsLogDatabankStats/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_log_databank_stats.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_log_databank_stats.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-log-databank-stats.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project and log qualified databank statistics; verify sample basis, empty bank, metric provenance and redacted diagnostics.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-LOG-DATABANK-STATS-SETTINGS-LOG-DATABANK-STATS-CONTRACT` → `com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-LOG-DATABANK-STATS-SETTINGS-LOG-DATABANK-STATS-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-LOG-DATABANK-STATS-SETTINGS-LOG-DATABANK-STATS-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_log_databank_stats.py --no-cov`; expect sample basis, empty bank, metric provenance and redacted diagnostics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sample basis, empty bank, metric provenance and redacted diagnostics and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-log-databank-stats.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-LOG-DATABANK-STATS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.21 FEAT-PROJECT-SETTINGS-NOTES - SettingsNotes.jar

## 1. Objective

- **Goal:** Implement validated Notes settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes/SettingsNotes.jar`; 1 raw class entries; SHA-256 `a64003858bd5eb317304a28a2f1ecaf7ea83064526f4d334a582020117c4bbd9`.
- **Inspected reference:** [SettingsNotes.md](sqx/Shared/SettingsNotes.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes/SettingsNotes.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes/SettingsNotes.jar" com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsNotes/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes/NotesCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes/notes.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotes/module.js`.
- **Existing UI connection:** Custom Projects; exact retained source-map `ui/app/plugins/project/SettingsNotes/source-map.json`. Target `ui/app/plugins/project/SettingsNotes/NotesCtrl.ts`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsNotes/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsNotes/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsNotes/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_notes.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_notes.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsNotes/NotesCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsNotes/notes.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsNotes/module.ts`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/plugins/project/SettingsNotes/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-notes.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Notes settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-NOTES-NOTES-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-NOTES-NOTES-SETTINGS-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-NOTES-NOTES-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_notes.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-notes.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-NOTES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.22 FEAT-PROJECT-SETTINGS-NOTIFICATION - SettingsNotification.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotification.jar`; 3 raw class entries; SHA-256 `24c1973db874306ab3b8fa40ae1c64dde32ae7c2de0f22f51536f13ca655b148`.
- **Inspected reference:** [SettingsNotification.md](sqx/Shared/SettingsNotification.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotification.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotification.jar" com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsNotification/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotificationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotificationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsNotification/settingsNotification.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsNotification/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsNotification/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsNotification/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_notification.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_notification.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-notification.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-NOTIFICATION-NOTIFICATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-NOTIFICATION-NOTIFICATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-NOTIFICATION-NOTIFICATION-SERVLET-GET-TYPES` → `com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet.getTypes()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_notification.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-notification.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-NOTIFICATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.23 FEAT-PROJECT-SETTINGS-SAVE-TO-FILES - SettingsSaveToFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFiles.jar`; 1 raw class entries; SHA-256 `d26e9384c34926df90ecb4added3147503d6af808e753f0246c7d6d25871cd96`.
- **Inspected reference:** [SettingsSaveToFiles.md](sqx/Shared/SettingsSaveToFiles.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFiles.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFiles.jar" com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsSaveToFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFilesService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFilesCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/settingsSaveToFiles.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsSaveToFiles/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsSaveToFiles/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsSaveToFiles/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_save_to_files.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_save_to_files.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-save-to-files.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-SAVE-TO-FILES-SETTINGS-SAVE-TO-FILES-CONTRACT` → `com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-SAVE-TO-FILES-SETTINGS-SAVE-TO-FILES-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-SAVE-TO-FILES-SETTINGS-SAVE-TO-FILES-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_save_to_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-save-to-files.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-SAVE-TO-FILES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.24 FEAT-PROJECT-SETTINGS-STOP-AND-START - SettingsStopAndStart.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStart.jar`; 1 raw class entries; SHA-256 `9f850d7aa0c52ed082f30f4ceada82f8b914d9151b9a100b3ddeab9fa3a32689`.
- **Inspected reference:** [SettingsStopAndStart.md](sqx/Shared/SettingsStopAndStart.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStart.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStart.jar" com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsStopAndStart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStartService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStartCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/settingsStopAndStart.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsStopAndStart/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsStopAndStart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsStopAndStart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_stop_and_start.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_stop_and_start.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-stop-and-start.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-STOP-AND-START-SETTINGS-STOP-AND-START-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-STOP-AND-START-SETTINGS-STOP-AND-START-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin.getHandler()Lorg/eclipse/jetty/server/Handler;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-STOP-AND-START-SETTINGS-STOP-AND-START-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_stop_and_start.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-stop-and-start.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-STOP-AND-START; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.25 FEAT-PROJECT-SETTINGS-UPDATE-DATA - SettingsUpdateData.jar

## 1. Objective

- **Goal:** Implement validated UpdateData settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateData.jar`; 1 raw class entries; SHA-256 `e198bb9ad5f7a9398a8424c026e42444d43d1ac6b1d38fdea22523d2bf570b63`.
- **Inspected reference:** [SettingsUpdateData.md](sqx/Shared/SettingsUpdateData.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateData.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateData.jar" com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsUpdateData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateDataService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateDataCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/settingsUpdateData.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsUpdateData/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsUpdateData/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsUpdateData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_update_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_update_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-update-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated UpdateData settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-UPDATE-DATA-SETTINGS-UPDATE-DATA-CONTRACT` → `com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-UPDATE-DATA-SETTINGS-UPDATE-DATA-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-UPDATE-DATA-SETTINGS-UPDATE-DATA-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_update_data.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-update-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-UPDATE-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.26 FEAT-PROJECT-SETTINGS-WAIT-FOR - SettingsWaitFor.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitFor.jar`; 1 raw class entries; SHA-256 `30a12b228d6db02d9a29f72590bcf92fd6761344e40a1786877a65a549176e35`.
- **Inspected reference:** [SettingsWaitFor.md](sqx/Shared/SettingsWaitFor.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitFor.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitFor.jar" com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/SettingsWaitFor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitForService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitForCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/settingsWaitFor.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsWaitFor/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsWaitFor/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsWaitFor/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_wait_for.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_wait_for.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-settings-wait-for.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-SETTINGS-WAIT-FOR-SETTINGS-WAIT-FOR-CONTRACT` → `com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-SETTINGS-WAIT-FOR-SETTINGS-WAIT-FOR-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-SETTINGS-WAIT-FOR-SETTINGS-WAIT-FOR-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_wait_for.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-settings-wait-for.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-SETTINGS-WAIT-FOR; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.27 FEAT-PROJECT-TASK-APPLY-MASS-CONFIG - TaskApplyMassConfig.jar

## 1. Objective

- **Goal:** Apply validated configuration across selected resources transactionally.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/TaskApplyMassConfig.jar`; 1 raw class entries; SHA-256 `dd297040e457ec86da4a17c93d2cb8165ef2baa2b3a4bf10390d08b87f2f4241`.
- **Inspected reference:** [TaskApplyMassConfig.md](sqx/CustomProjects/TaskApplyMassConfig.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/TaskApplyMassConfig.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/TaskApplyMassConfig.jar" com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskApplyMassConfig/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/simpleSettings/SimpleApplyMassConfigCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskApplyMassConfig/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskApplyMassConfig/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskApplyMassConfig/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_apply_mass_config.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_apply_mass_config.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-apply-mass-config.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Apply validated configuration across selected resources transactionally; verify target selection, compatibility, rollback and unaffected settings.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-APPLY-MASS-CONFIG-APPLY-MASS-CONFIG-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-APPLY-MASS-CONFIG-APPLY-MASS-CONFIG-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-APPLY-MASS-CONFIG-APPLY-MASS-CONFIG-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_apply_mass_config.py --no-cov`; expect target selection, compatibility, rollback and unaffected settings; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target selection, compatibility, rollback and unaffected settings and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-apply-mass-config.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-APPLY-MASS-CONFIG; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.28 FEAT-PROJECT-TASK-CALL-EXTERNAL-SCRIPT - TaskCallExternalScript.jar

## 1. Objective

- **Goal:** Execute qualified external processes with scoped authority and owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/TaskCallExternalScript.jar`; 2 raw class entries; SHA-256 `487d4460de5659572b1d9cb6f3d34e4b29593c428f97bf9af4847fab5199c46f`.
- **Inspected reference:** [TaskCallExternalScript.md](sqx/CustomProjects/TaskCallExternalScript.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/TaskCallExternalScript.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/TaskCallExternalScript.jar" com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskCallExternalScript/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/simpleSettings/SimpleCallExternalScriptSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskCallExternalScript/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskCallExternalScript/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskCallExternalScript/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_call_external_script.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_call_external_script.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-call-external-script.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute qualified external processes with scoped authority and owned lifecycle; verify allowlisted invocation, timeout, exit failure, cancellation and redacted output.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-CALL-EXTERNAL-SCRIPT-CALL-EXTERNAL-SCRIPT-CONTRACT` → `com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-CALL-EXTERNAL-SCRIPT-CALL-EXTERNAL-SCRIPT-GET-TYPE` → `com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-CALL-EXTERNAL-SCRIPT-CALL-EXTERNAL-SCRIPT-GET-NAME` → `com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_call_external_script.py --no-cov`; expect allowlisted invocation, timeout, exit failure, cancellation and redacted output; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture allowlisted invocation, timeout, exit failure, cancellation and redacted output and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-call-external-script.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-CALL-EXTERNAL-SCRIPT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.29 FEAT-PROJECT-TASK-CLEAR-DATABANKS - TaskClearDatabanks.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanks.jar`; 1 raw class entries; SHA-256 `3b1927921286adac455ac77748534af0299f8bc1f928b32e4b817bed700657f2`.
- **Inspected reference:** [TaskClearDatabanks.md](sqx/CustomProjects/TaskClearDatabanks.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanks.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanks.jar" com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskClearDatabanks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanksService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/simpleSettings/SimpleClearDatabanksCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/simpleSettings/simpleSettings.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskClearDatabanks/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskClearDatabanks/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskClearDatabanks/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_clear_databanks.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_clear_databanks.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-clear-databanks.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-CLEAR-DATABANKS-CLEAR-DATABANKS-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-CLEAR-DATABANKS-CLEAR-DATABANKS-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-CLEAR-DATABANKS-CLEAR-DATABANKS-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_clear_databanks.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-clear-databanks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-CLEAR-DATABANKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.30 FEAT-PROJECT-TASK-CUSTOM-ANALYSIS - TaskCustomAnalysis.jar

## 1. Objective

- **Goal:** Run qualified custom analysis resources against selected results.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/TaskCustomAnalysis.jar`; 1 raw class entries; SHA-256 `37dd9d562de654fdb9bd258399586fd1b33fa12c4c849b92b734e9846f3e622d`.
- **Inspected reference:** [TaskCustomAnalysis.md](sqx/CustomProjects/TaskCustomAnalysis.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/TaskCustomAnalysis.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/TaskCustomAnalysis.jar" com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskCustomAnalysis/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/simpleSettings/SimpleSettingsCACtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskCustomAnalysis/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskCustomAnalysis/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskCustomAnalysis/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_custom_analysis.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_custom_analysis.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-custom-analysis.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Run qualified custom analysis resources against selected results; verify resource trust/version, input identity and execution failure.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_custom_analysis.py --no-cov`; expect resource trust/version, input identity and execution failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource trust/version, input identity and execution failure and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-custom-analysis.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-CUSTOM-ANALYSIS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.31 FEAT-PROJECT-TASK-DELETE-FILE - TaskDeleteFile.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/TaskDeleteFile.jar`; 1 raw class entries; SHA-256 `a82d1c7287df6f5802679862c54a1dc5bd0c37640e1dc178d0ca995439fc904f`.
- **Inspected reference:** [TaskDeleteFile.md](sqx/CustomProjects/TaskDeleteFile.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/TaskDeleteFile.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/TaskDeleteFile.jar" com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskDeleteFile/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/simpleSettings/SimpleDeleteFileSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskDeleteFile/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskDeleteFile/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskDeleteFile/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_delete_file.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_delete_file.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-delete-file.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-DELETE-FILE-DELETE-FILE-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-DELETE-FILE-DELETE-FILE-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-DELETE-FILE-DELETE-FILE-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_delete_file.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-delete-file.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-DELETE-FILE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.32 FEAT-PROJECT-TASK-FILTERING - TaskFiltering.jar

## 1. Objective

- **Goal:** Execute Filtering through an owned typed task capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering/TaskFiltering.jar`; 1 raw class entries; SHA-256 `16ce6f3e668b5fe9a8769ea65c7562286fb648946eb40819f2926f3f4089cb3e`.
- **Inspected reference:** [TaskFiltering.md](sqx/CustomProjects/TaskFiltering.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering/TaskFiltering.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering/TaskFiltering.jar" com.strategyquant.plugin.Task.impl.Filtering.FilteringTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskFiltering/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering/simpleSettings/SimpleFilteringSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskFiltering/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskFiltering/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskFiltering/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskFiltering/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_filtering.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_filtering.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-filtering.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute Filtering through an owned typed task capability; verify input handles, start/stop/clone transitions, failure status and retained outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-FILTERING-FILTERING-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Filtering.FilteringTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-FILTERING-FILTERING-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.Filtering.FilteringTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-FILTERING-FILTERING-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.Filtering.FilteringTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_filtering.py --no-cov`; expect input handles, start/stop/clone transitions, failure status and retained outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture input handles, start/stop/clone transitions, failure status and retained outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-filtering.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-FILTERING; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.33 FEAT-PROJECT-TASK-GO-TO-TASK - TaskGoToTask.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask/TaskGoToTask.jar`; 1 raw class entries; SHA-256 `628a7f446e50d191ba73b01c07fe276209379659ec9fcff2f1ed45ccc42f822d`.
- **Inspected reference:** [TaskGoToTask.md](sqx/CustomProjects/TaskGoToTask.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask/TaskGoToTask.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask/TaskGoToTask.jar" com.strategyquant.plugin.Task.impl.GoToTask.GoToTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskGoToTask/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask/simpleSettings/SimpleGoToTaskSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskGoToTask/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskGoToTask/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskGoToTask/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskGoToTask/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_go_to_task.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_go_to_task.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-go-to-task.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-GO-TO-TASK-GO-TO-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.GoToTask.GoToTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-GO-TO-TASK-GO-TO-TASK-START` → `com.strategyquant.plugin.Task.impl.GoToTask.GoToTask.start()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-GO-TO-TASK-GO-TO-TASK-GET-RUNNING-STATUS` → `com.strategyquant.plugin.Task.impl.GoToTask.GoToTask.getRunningStatus()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_go_to_task.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-go-to-task.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-GO-TO-TASK; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.34 FEAT-PROJECT-TASK-LOAD-FROM-FILES - TaskLoadFromFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/TaskLoadFromFiles.jar`; 1 raw class entries; SHA-256 `b03051575ac84a5d50697392bd8915f8f0e72f3f945612c7809921811db4aac2`.
- **Inspected reference:** [TaskLoadFromFiles.md](sqx/CustomProjects/TaskLoadFromFiles.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/TaskLoadFromFiles.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/TaskLoadFromFiles.jar" com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskLoadFromFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/simpleSettings/SimpleLoadFromFilesSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskLoadFromFiles/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskLoadFromFiles/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskLoadFromFiles/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_load_from_files.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_load_from_files.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-load-from-files.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-LOAD-FROM-FILES-LOAD-FROM-FILES-CONTRACT` → `com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-LOAD-FROM-FILES-LOAD-FROM-FILES-INIT` → `com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles.init()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-LOAD-FROM-FILES-LOAD-FROM-FILES-START` → `com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles.start()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_load_from_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-load-from-files.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-LOAD-FROM-FILES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.35 FEAT-PROJECT-TASK-LOG-DATABANK-STATS - TaskLogDatabankStats.jar

## 1. Objective

- **Goal:** Project and log qualified databank statistics.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar`; 1 raw class entries; SHA-256 `c94ca21a412be8a9d251520c9533800d014946c064a7469455d53bb36d7ee68f`.
- **Inspected reference:** [TaskLogDatabankStats.md](sqx/CustomProjects/TaskLogDatabankStats.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar" com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskLogDatabankStats/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/simpleSettings/SimpleLogDatabankStatsSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskLogDatabankStats/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskLogDatabankStats/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskLogDatabankStats/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_log_databank_stats.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_log_databank_stats.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-log-databank-stats.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project and log qualified databank statistics; verify sample basis, empty bank, metric provenance and redacted diagnostics.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-LOG-DATABANK-STATS-LOG-DATABANK-STATS-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-LOG-DATABANK-STATS-LOG-DATABANK-STATS-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-LOG-DATABANK-STATS-LOG-DATABANK-STATS-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_log_databank_stats.py --no-cov`; expect sample basis, empty bank, metric provenance and redacted diagnostics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sample basis, empty bank, metric provenance and redacted diagnostics and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-log-databank-stats.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-LOG-DATABANK-STATS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.36 FEAT-PROJECT-TASK-MANAGER-PROJECTS - TaskManagerProjects.jar

## 1. Objective

- **Goal:** Execute ManagerProjects through an owned typed task capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar`; 2 raw class entries; SHA-256 `f63173a05008c4ec13ffafd8cb7d21cdf5d7fc24acb6c1191c80b8d0eb3896d5`.
- **Inspected reference:** [TaskManagerProjects.md](sqx/CustomProjects/TaskManagerProjects.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar" com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/project/TaskManagerProjects/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/directives/TMProjectControlCtrl.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/TaskManagerProjects/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/TaskManagerProjects/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/TaskManagerProjects/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/TaskManagerProjects/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_manager_projects.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_manager_projects.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-manager-projects.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute ManagerProjects through an owned typed task capability; verify input handles, start/stop/clone transitions, failure status and retained outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-MANAGER-PROJECTS-TMPROJECTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-MANAGER-PROJECTS-TMPROJECTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-MANAGER-PROJECTS-TMPROJECTS-SERVLET-ON-LIST-PROJECTS` → `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet.onListProjects()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_manager_projects.py --no-cov`; expect input handles, start/stop/clone transitions, failure status and retained outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture input handles, start/stop/clone transitions, failure status and retained outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-manager-projects.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-MANAGER-PROJECTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.37 FEAT-PROJECT-TASK-NOTIFICATION - TaskNotification.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotification.jar`; 1 raw class entries; SHA-256 `5e6c4218cc934ca7f89960ec776bee8990d38acfe0f2f26c10af777cc877417e`.
- **Inspected reference:** [TaskNotification.md](sqx/CustomProjects/TaskNotification.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotification.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotification.jar" com.strategyquant.plugin.Task.impl.Notification.NotificationTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskNotification/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotificationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification/simpleSettings/SimpleNotificationSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNotification/simpleSettings/simpleSettings.html`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskNotification/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskNotification/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskNotification/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_notification.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_notification.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-notification.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-NOTIFICATION-NOTIFICATION-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Notification.NotificationTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-NOTIFICATION-NOTIFICATION-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.Notification.NotificationTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-NOTIFICATION-NOTIFICATION-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.Notification.NotificationTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_notification.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-notification.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-NOTIFICATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.38 FEAT-PROJECT-TASK-SAVE-TO-FILES - TaskSaveToFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/TaskSaveToFiles.jar`; 1 raw class entries; SHA-256 `3ee328b7c850f82783a49835a81add1023f162c3660b8bb6678cebcc675046f9`.
- **Inspected reference:** [TaskSaveToFiles.md](sqx/CustomProjects/TaskSaveToFiles.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/TaskSaveToFiles.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/TaskSaveToFiles.jar" com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskSaveToFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/simpleSettings/SimpleSaveToFilesSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskSaveToFiles/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskSaveToFiles/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskSaveToFiles/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_save_to_files.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_save_to_files.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-save-to-files.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-SAVE-TO-FILES-SAVE-TO-FILES-CONTRACT` → `com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-SAVE-TO-FILES-SAVE-TO-FILES-INIT` → `com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles.init()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-SAVE-TO-FILES-SAVE-TO-FILES-START` → `com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles.start()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_save_to_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-save-to-files.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-SAVE-TO-FILES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.39 FEAT-PROJECT-TASK-STOP-AND-START - TaskStopAndStart.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar`; 1 raw class entries; SHA-256 `94335601c0cbc02b58f4ccfc80d081040fc802d96382d477e3c9a1566e89e14f`.
- **Inspected reference:** [TaskStopAndStart.md](sqx/CustomProjects/TaskStopAndStart.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar" com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskStopAndStart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/simpleSettings/SimpleStopAndStartSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskStopAndStart/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskStopAndStart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskStopAndStart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_stop_and_start.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_stop_and_start.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-stop-and-start.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-STOP-AND-START-STOP-AND-START-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-STOP-AND-START-STOP-AND-START-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-STOP-AND-START-STOP-AND-START-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_stop_and_start.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-stop-and-start.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-STOP-AND-START; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.40 FEAT-PROJECT-TASK-UPDATE-DATA - TaskUpdateData.jar

## 1. Objective

- **Goal:** Delegate data updates through qualified provider jobs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData/TaskUpdateData.jar`; 2 raw class entries; SHA-256 `bfa0bb75056cfc77dac3ae15b19e58fc62fc86178154d9d9a04c6f0dd3d47508`.
- **Inspected reference:** [TaskUpdateData.md](sqx/CustomProjects/TaskUpdateData.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData/TaskUpdateData.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData/TaskUpdateData.jar" com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskUpdateData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData/simpleSettings/SimpleUpdateDataSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskUpdateData/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskUpdateData/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskUpdateData/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskUpdateData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_update_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_update_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-update-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Delegate data updates through qualified provider jobs; verify selected dataset, partial failure, cancellation and updated provenance.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-UPDATE-DATA-UPDATE-DATA-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-UPDATE-DATA-UPDATE-DATA-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-UPDATE-DATA-UPDATE-DATA-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_update_data.py --no-cov`; expect selected dataset, partial failure, cancellation and updated provenance; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture selected dataset, partial failure, cancellation and updated provenance and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-update-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-UPDATE-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.41 FEAT-PROJECT-TASK-WAIT-FOR - TaskWaitFor.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor/TaskWaitFor.jar`; 2 raw class entries; SHA-256 `46957acd37eca2a2feb6b322230f323955380e952ab45d626dc47f52436ce7f8`.
- **Inspected reference:** [TaskWaitFor.md](sqx/CustomProjects/TaskWaitFor.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor/TaskWaitFor.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor/TaskWaitFor.jar" com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/tasks/TaskWaitFor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor/simpleSettings/SimpleWaitForSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskWaitFor/module.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/tasks/TaskWaitFor/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskWaitFor/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/TaskWaitFor/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_task_wait_for.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_task_wait_for.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-project-task-wait-for.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PROJECT-TASK-WAIT-FOR-WAIT-FOR-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PROJECT-TASK-WAIT-FOR-WAIT-FOR-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PROJECT-TASK-WAIT-FOR-WAIT-FOR-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_wait_for.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-project-task-wait-for.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-PROJECT-TASK-WAIT-FOR; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.42 FEAT-UI-PROJECT-SETTINGS - ProjectSettings resource contribution

## 1. Objective

- **Goal:** Qualify and connect ProjectSettings without assuming a missing backend JAR.
- **Context / Problem Solved:** ProjectSettings is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectSettings`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectSettings/module.js`.
- **FR:** `FR-UI-PROJECT-SETTINGS-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/project/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectSettings`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectSettings/SettingsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectSettings/SettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectSettings/views/settings.html`.
- **Existing UI connection:** Custom Projects; exact retained source-map `ui/app/plugins/project/ProjectSettings/source-map.json`. Target `ui/app/plugins/project/ProjectSettings/views/settings.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Create:** `app/plugins/project/README.md`
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_project_settings.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ProjectSettings/views/settings.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ProjectSettings/module.ts`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/plugins/project/ProjectSettings/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-project-settings.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-PROJECT-SETTINGS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_project_settings.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority. Inspect the ProjectSettings contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-project-settings.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-UI-PROJECT-SETTINGS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.43 FEAT-UI-SETTINGS-PANEL - SettingsPanel resource contribution

## 1. Objective

- **Goal:** Qualify and connect SettingsPanel without assuming a missing backend JAR.
- **Context / Problem Solved:** SettingsPanel is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPanel`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPanel/module.js`.
- **FR:** `FR-UI-SETTINGS-PANEL-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/project/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPanel`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPanel/SettingsPanelCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPanel/settings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPanel/module.js`.
- **Existing UI connection:** Custom Projects; exact retained source-map `ui/app/plugins/project/SettingsPanel/source-map.json`. Target `ui/app/plugins/project/SettingsPanel/SettingsPanelCtrl.ts`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/project/resource_contributions.py` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/plugins/project/README.md` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_settings_panel.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsPanel/SettingsPanelCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsPanel/settings.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsPanel/module.ts`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/plugins/project/SettingsPanel/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-settings-panel.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-SETTINGS-PANEL-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_settings_panel.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority. Inspect the SettingsPanel contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-settings-panel.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-UI-SETTINGS-PANEL; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.44 FEAT-UI-TASK-MANAGER-TASKS - TaskManagerTasks resource contribution

## 1. Objective

- **Goal:** Qualify and connect TaskManagerTasks without assuming a missing backend JAR.
- **Context / Problem Solved:** TaskManagerTasks is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerTasks`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/module.js`.
- **FR:** `FR-UI-TASK-MANAGER-TASKS-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/project/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerTasks`; `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/TMTasksService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/TMTasksCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/directives/tmtask/TMTaskCtrl.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/project/resource_contributions.py` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/plugins/project/README.md` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_task_manager_tasks.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-task-manager-tasks.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-TASK-MANAGER-TASKS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_task_manager_tasks.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority. Inspect the TaskManagerTasks contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-task-manager-tasks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for FEAT-UI-TASK-MANAGER-TASKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 13.45 FEAT-PROJECT-Q-RESEARCH-WORKFLOWS - Connected discovery, build and testing workflow

## 1. Objective

- **Goal:** Expose reusable project/research operations that Q can orchestrate through host capabilities.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletSQAI/ServletSQAI.jar`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/auto-research/plugin.json`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/web/SQAI/scripts/strategy-architect/plugin.json`.
- **Donor:** `SQX_145_REFERENCE_ROOT/docs/custom-projects`.
- **Ownership:** proposed `FEAT-PROJECT-Q-RESEARCH-WORKFLOWS` and `FR-PROJECT-Q-RESEARCH-WORKFLOWS-CONSUMED-CONTRACTS`; owner `app/plugins/tasks/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Auto-research procedure bodies/core are unavailable; integration completion depends on P19 while reusable task contracts may land earlier.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppTaskManager`, `SQX_145_REFERENCE_ROOT/internal/web/SQAI/chat`; connect retained project tasks with the approved Q bridge.

## 3. File Changes

- **Create:** `app/plugins/tasks/research_workflow.py` — Expose reusable project/research operations that Q can orchestrate through host capabilities.
- **Create:** `app/plugins/tasks/research_contracts.py` — Expose reusable project/research operations that Q can orchestrate through host capabilities.
- **Create:** `app/plugins/tasks/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_project_q_research_workflows.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-project_q_research_workflows-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Trace project creation/validation/start/results contracts; distinguish Q procedure resources from task-engine behavior.
- [ ] **Step 3:** Bind discovery hypotheses, builders/retesters, output IDs and journal observations through typed host jobs.
- [ ] **Step 4:** Pin stop/resume, bounded rounds and failure transitions without ad-hoc plugin SQL or guessed workflow defaults.
- [ ] **Step 5:** Test an isolated discovery/build/retest cycle, rejected configuration, cancellation and persisted provenance.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_project_q_research_workflows.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 13.46 P13 integration — Execute custom-project task graphs with owned conditions and bounded side effects

## 1. Objective

- **Goal:** Execute custom-project task graphs with owned conditions and bounded side effects.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P13; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/CustomProjects/customProjects.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/TASKMANAGER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TMProjectsService.js`.
- **Existing UI connection:** Custom Projects; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; wire project task/condition configuration, graph execution and server-owned outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/project/graphs.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/project/conditions.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/project/runner.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/project/contracts.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/CustomProjects/routes.py` (proposed earlier in FEAT-PROJECT-APP-TASK-MANAGER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/CustomProjects/contracts.py` (proposed earlier in FEAT-PROJECT-APP-TASK-MANAGER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/CustomProjects/customProjectsClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/plugins/project/README.md` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_custom_projects_tasks_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CustomProjects/NewTaskModal.tsx`
  - Display project task/condition configuration, graph execution and server-owned outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CustomProjects/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/tests/unit/backend-connections/task-13-46.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify task graph versions, input/output handles, conditions, jumps, loops and clone semantics.
- [ ] **Step 3:** Implement task adapters against existing build/retest/data/portfolio capabilities; bound execution.
- [ ] **Step 4:** Connect CustomProjects task controls and logs; require separate authority for destructive/external effects.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind project task/condition configuration, graph execution and server-owned outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_custom_projects_tasks_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/CustomProjects/customProjects.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`. Assert graph save/reload, condition boundaries, task ordering and delegated result handles; reject invalid jump, runaway loop, missing capability and denied external/delete action.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-13-46.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-custom-projects-tasks-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Custom Projects for 13.49; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
