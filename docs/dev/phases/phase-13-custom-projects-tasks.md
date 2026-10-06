# P13 — Custom projects, Task Manager, conditions and task actions

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02,P04,P07,P08,P09,P10,P11,P12.
- **Scope:** 44 JAR feature tasks, 3 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# 13.1 FEAT-PROJECT-ACTIVATION - activation.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/activation.jar`; 38 class declarations; SHA-256 `31c68a8743f42ac43b439a382e9b4c9116ba392dbb2d30bdebfb3529c23c753a`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PROJECT-ACTIVATION`.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/activation.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/activation.jar" com.sun.activation.registries.LineTokenizer`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-PROJECT-ACTIVATION-LINE-TOKENIZER-CONTRACT` → `com.sun.activation.registries.LineTokenizer`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-ACTIVATION-LINE-TOKENIZER-HAS-MORE-TOKENS` → `com.sun.activation.registries.LineTokenizer.hasMoreTokens`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-ACTIVATION-LINE-TOKENIZER-NEXT-TOKEN` → `com.sun.activation.registries.LineTokenizer.nextToken`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_activation.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.

# 13.2 FEAT-PROJECT-COMMONS-EMAIL - commons-email.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-email.jar`; 21 class declarations; SHA-256 `ee8479906abb2c355a46a0a9845cfa1803bcc3c520a34baea4a6cf4e1f0f0cc1`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PROJECT-COMMONS-EMAIL`.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-email.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-email.jar" org.apache.commons.mail.ByteArrayDataSource`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-PROJECT-COMMONS-EMAIL-BYTE-ARRAY-DATA-SOURCE-CONTRACT` → `org.apache.commons.mail.ByteArrayDataSource`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-COMMONS-EMAIL-BYTE-ARRAY-DATA-SOURCE-GET-CONTENT-TYPE` → `org.apache.commons.mail.ByteArrayDataSource.getContentType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-COMMONS-EMAIL-BYTE-ARRAY-DATA-SOURCE-GET-INPUT-STREAM` → `org.apache.commons.mail.ByteArrayDataSource.getInputStream`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_commons_email.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.

# 13.3 FEAT-PROJECT-COMMONS-EXEC - commons-exec.jar

## 1. Objective

- **Goal:** Execute qualified external processes with scoped authority and owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-exec.jar`; 37 class declarations; SHA-256 `cb49812dc1bfb0ea4f20f398bcae1a88c6406e213e67f7524fb10d4f8ad9347b`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PROJECT-COMMONS-EXEC`.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-exec.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-exec.jar" org.apache.commons.exec.CommandLine`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-PROJECT-COMMONS-EXEC-COMMAND-LINE-CONTRACT` → `org.apache.commons.exec.CommandLine`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-COMMONS-EXEC-COMMAND-LINE-PARSE` → `org.apache.commons.exec.CommandLine.parse`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-COMMONS-EXEC-COMMAND-LINE-GET-EXECUTABLE` → `org.apache.commons.exec.CommandLine.getExecutable`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_commons_exec.py --no-cov`; expect allowlisted invocation, timeout, exit failure, cancellation and redacted output; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture allowlisted invocation, timeout, exit failure, cancellation and redacted output and visible failures.

# 13.4 FEAT-PROJECT-JAVAX-MAIL - javax-mail.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/javax-mail.jar`; 340 class declarations; SHA-256 `45b515e7104944c09e45b9c7bb1ce5dff640486374852dd2b2e80cc3752dfa11`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PROJECT-JAVAX-MAIL`.
- **Owner:** `app/plugins/tasks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task notification/mail and external-process support with explicit authorization/lifecycle; downstream P16,P17.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/javax-mail.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/javax-mail.jar" com.sun.mail.auth.MD4`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

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
- [ ] **Step 4:** `FR-PROJECT-JAVAX-MAIL-MD4-CONTRACT` → `com.sun.mail.auth.MD4`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-JAVAX-MAIL-MD4-DIGEST` → `com.sun.mail.auth.MD4.digest`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_javax_mail.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.

# 13.5 FEAT-PROJECT-APP-TASK-MANAGER - AppTaskManager.jar

## 1. Objective

- **Goal:** Mount the TaskManager workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppTaskManager/AppTaskManager.jar`; 2 class declarations; SHA-256 `b6f06d8c73fe74ddbb08bbcc2219551c1300c508703f5ac7ca4e1b1fb79fbd80`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/AppTaskManager.md`; roadmap allocation `FEAT-PROJECT-APP-TASK-MANAGER`.
- **Owner:** `app/workspace/CustomProjects/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppTaskManager/AppTaskManager.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppTaskManager/AppTaskManager.jar" com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the TaskManager workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PROJECT-APP-TASK-MANAGER-TASK-MANAGER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-APP-TASK-MANAGER-TASK-MANAGER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-APP-TASK-MANAGER-TASK-MANAGER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.TaskManager.TaskManagerAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_app_task_manager.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.

# 13.6 FEAT-PROJECT-PROJECT-CONDITION-CYCLES-COUNT - ProjectConditionCyclesCount.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar`; 1 class declarations; SHA-256 `b1bc4d71172494dbd135988f9d5192aa12c32414d15ac4753b827ed20b659059`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectConditionCyclesCount.md`; roadmap allocation `FEAT-PROJECT-PROJECT-CONDITION-CYCLES-COUNT`.
- **Owner:** `app/plugins/project/ProjectConditionCyclesCount/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionCyclesCount/ProjectConditionCyclesCount.jar" com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** `FR-PROJECT-PROJECT-CONDITION-CYCLES-COUNT-CYCLES-COUNT-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-PROJECT-CONDITION-CYCLES-COUNT-CYCLES-COUNT-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin.getTitle`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-PROJECT-CONDITION-CYCLES-COUNT-CYCLES-COUNT-CONDITION-PLUGIN-GET-DESCRIPTION-FORMAT` → `com.strategyquant.plugin.ProjectCondition.impl.CyclesCount.CyclesCountConditionPlugin.getDescriptionFormat`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_cycles_count.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.

# 13.7 FEAT-PROJECT-PROJECT-CONDITION-DURATION - ProjectConditionDuration.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionDuration/ProjectConditionDuration.jar`; 0 class declarations; SHA-256 `7c46091c3f541197d3e76b5acada3ff01f72deaee69bb35a8c8c9a45fdf5cb0a`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectConditionDuration.md`; roadmap allocation `FEAT-PROJECT-PROJECT-CONDITION-DURATION`.
- **Owner:** `app/plugins/project/ProjectConditionDuration/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionDuration/ProjectConditionDuration.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/project/ProjectConditionDuration/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionDuration/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionDuration/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ProjectConditionDuration/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_project_condition_duration.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_project_condition_duration.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** `FR-PROJECT-PROJECT-CONDITION-DURATION-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_duration.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.

# 13.8 FEAT-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED - ProjectConditionGoToActivated.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated/ProjectConditionGoToActivated.jar`; 1 class declarations; SHA-256 `ffecb497c1fcb03e33221d48341006e27bcaac9572af2b2710e54dc1041d4944`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectConditionGoToActivated.md`; roadmap allocation `FEAT-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED`.
- **Owner:** `app/plugins/project/ProjectConditionGoToActivated/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated/ProjectConditionGoToActivated.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToActivated/ProjectConditionGoToActivated.jar" com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED-GO-TO-ACTIVATED-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED-GO-TO-ACTIVATED-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin.getTitle`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-ACTIVATED-GO-TO-ACTIVATED-CONDITION-PLUGIN-GET-DESCRIPTION-FORMAT` → `com.strategyquant.plugin.ProjectCondition.impl.GoToActivated.GoToActivatedConditionPlugin.getDescriptionFormat`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_go_to_activated.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.

# 13.9 FEAT-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED - ProjectConditionGoToEvaluated.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated/ProjectConditionGoToEvaluated.jar`; 1 class declarations; SHA-256 `0fafc05ab85a4672612fe3ca2e3c551508abb83a39f609134328de1844416f11`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectConditionGoToEvaluated.md`; roadmap allocation `FEAT-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED`.
- **Owner:** `app/plugins/project/ProjectConditionGoToEvaluated/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated/ProjectConditionGoToEvaluated.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionGoToEvaluated/ProjectConditionGoToEvaluated.jar" com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED-GO-TO-EVALUATED-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED-GO-TO-EVALUATED-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin.getTitle`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-PROJECT-CONDITION-GO-TO-EVALUATED-GO-TO-EVALUATED-CONDITION-PLUGIN-GET-DESCRIPTION-FORMAT` → `com.strategyquant.plugin.ProjectCondition.impl.GoToEvaluated.GoToEvaluatedConditionPlugin.getDescriptionFormat`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_go_to_evaluated.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.

# 13.10 FEAT-PROJECT-PROJECT-CONDITION-RESULTS-COUNT - ProjectConditionResultsCount.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount/ProjectConditionResultsCount.jar`; 1 class declarations; SHA-256 `da8fb2b019cf93d5cd4c338141cea1b1cd79dbd30b836fd28b3919db3d2d2211`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectConditionResultsCount.md`; roadmap allocation `FEAT-PROJECT-PROJECT-CONDITION-RESULTS-COUNT`.
- **Owner:** `app/plugins/project/ProjectConditionResultsCount/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount/ProjectConditionResultsCount.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionResultsCount/ProjectConditionResultsCount.jar" com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** `FR-PROJECT-PROJECT-CONDITION-RESULTS-COUNT-RESULTS-COUNT-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-PROJECT-CONDITION-RESULTS-COUNT-RESULTS-COUNT-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin.getTitle`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-PROJECT-CONDITION-RESULTS-COUNT-RESULTS-COUNT-CONDITION-PLUGIN-GET-DESCRIPTION-FORMAT` → `com.strategyquant.plugin.ProjectCondition.impl.ResultsCount.ResultsCountConditionPlugin.getDescriptionFormat`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_results_count.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.

# 13.11 FEAT-PROJECT-PROJECT-CONDITION-RUN-TIME - ProjectConditionRunTime.jar

## 1. Objective

- **Goal:** Evaluate the named project condition at the specified graph boundary.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime/ProjectConditionRunTime.jar`; 1 class declarations; SHA-256 `6cdece3f97fa852e2a16b2a903c7c513278ccc2865a93da098337a09c081c8b8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectConditionRunTime.md`; roadmap allocation `FEAT-PROJECT-PROJECT-CONDITION-RUN-TIME`.
- **Owner:** `app/plugins/project/ProjectConditionRunTime/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime/ProjectConditionRunTime.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ProjectConditionRunTime/ProjectConditionRunTime.jar" com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Evaluate the named project condition at the specified graph boundary; verify comparison equality, counter/time units, disabled condition and loop bound.
- [ ] **Step 4:** `FR-PROJECT-PROJECT-CONDITION-RUN-TIME-RUNTIME-CONDITION-PLUGIN-CONTRACT` → `com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-PROJECT-CONDITION-RUN-TIME-RUNTIME-CONDITION-PLUGIN-GET-TITLE` → `com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin.getTitle`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-PROJECT-CONDITION-RUN-TIME-RUNTIME-CONDITION-PLUGIN-GET-DESCRIPTION-FORMAT` → `com.strategyquant.plugin.ProjectCondition.impl.RunTime.RuntimeConditionPlugin.getDescriptionFormat`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_project_condition_run_time.py --no-cov`; expect comparison equality, counter/time units, disabled condition and loop bound; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture comparison equality, counter/time units, disabled condition and loop bound and visible failures.

# 13.12 FEAT-PROJECT-SERVLET-PROJECT - ServletProject.jar

## 1. Objective

- **Goal:** Expose Project commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletProject/ServletProject.jar`; 13 class declarations; SHA-256 `60935843ba2ddf41a57f589f778c8bda1adbd4ff79a1e0469d9fc7d9f22255c4`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/ServletProject.md`; roadmap allocation `FEAT-PROJECT-SERVLET-PROJECT`.
- **Owner:** `app/plugins/project/ServletProject/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletProject/ServletProject.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletProject/ServletProject.jar" com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose Project commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-PROJECT-SERVLET-PROJECT-PROJECT-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SERVLET-PROJECT-PROJECT-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_servlet_project.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.

# 13.13 FEAT-PROJECT-SERVLET-PROJECT-OLD - ServletProjectOld.jar

## 1. Objective

- **Goal:** Expose ProjectOld commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletProjectOld/ServletProjectOld.jar`; 0 class declarations; SHA-256 `7324b8a1cd65a4648a8a6deae01b16ba533a81159d22f49fdaacd92a40d4942f`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletProjectOld.md`; roadmap allocation `FEAT-PROJECT-SERVLET-PROJECT-OLD`.
- **Owner:** `app/plugins/project/ServletProjectOld/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletProjectOld/ServletProjectOld.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/project/ServletProjectOld/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ServletProjectOld/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ServletProjectOld/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/project/ServletProjectOld/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_servlet_project_old.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_servlet_project_old.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose ProjectOld commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-PROJECT-SERVLET-PROJECT-OLD-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_servlet_project_old.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.

# 13.14 FEAT-PROJECT-SETTINGS-APPLY-MASS-CONFIG - SettingsApplyMassConfig.jar

## 1. Objective

- **Goal:** Apply validated configuration across selected resources transactionally.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/SettingsApplyMassConfig.jar`; 1 class declarations; SHA-256 `d0a003545047c922a4d7d957cda69540fde1f2b2b5e36861f7830e9049095ba6`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsApplyMassConfig.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-APPLY-MASS-CONFIG`.
- **Owner:** `app/plugins/tasks/SettingsApplyMassConfig/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/SettingsApplyMassConfig.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsApplyMassConfig/SettingsApplyMassConfig.jar" com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Apply validated configuration across selected resources transactionally; verify target selection, compatibility, rollback and unaffected settings.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-APPLY-MASS-CONFIG-SETTINGS-APPLY-MASS-CONFIG-CONTRACT` → `com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-APPLY-MASS-CONFIG-SETTINGS-APPLY-MASS-CONFIG-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-APPLY-MASS-CONFIG-SETTINGS-APPLY-MASS-CONFIG-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.ApplyMassConfig.SettingsApplyMassConfig.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_apply_mass_config.py --no-cov`; expect target selection, compatibility, rollback and unaffected settings; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target selection, compatibility, rollback and unaffected settings and visible failures.

# 13.15 FEAT-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT - SettingsCallExternalScript.jar

## 1. Objective

- **Goal:** Execute qualified external processes with scoped authority and owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScript.jar`; 1 class declarations; SHA-256 `f2b82f3c269f7f4f5d34ceb44697713a72a203953093c5a06cc2227dd8966a36`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsCallExternalScript.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT`.
- **Owner:** `app/plugins/tasks/SettingsCallExternalScript/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScript.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCallExternalScript/SettingsCallExternalScript.jar" com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute qualified external processes with scoped authority and owned lifecycle; verify allowlisted invocation, timeout, exit failure, cancellation and redacted output.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT-SETTINGS-CALL-EXTERNAL-SCRIPT-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT-SETTINGS-CALL-EXTERNAL-SCRIPT-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-CALL-EXTERNAL-SCRIPT-SETTINGS-CALL-EXTERNAL-SCRIPT-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.CallExternalScript.SettingsCallExternalScript.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_call_external_script.py --no-cov`; expect allowlisted invocation, timeout, exit failure, cancellation and redacted output; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture allowlisted invocation, timeout, exit failure, cancellation and redacted output and visible failures.

# 13.16 FEAT-PROJECT-SETTINGS-CLEAR-DATABANKS - SettingsClearDatabanks.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanks.jar`; 1 class declarations; SHA-256 `233ceafc6ab1822f3a2d19765753bb940b071388d32a3a9e1fc5dd194cbe0243`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsClearDatabanks.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-CLEAR-DATABANKS`.
- **Owner:** `app/plugins/tasks/SettingsClearDatabanks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanks.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsClearDatabanks/SettingsClearDatabanks.jar" com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-CLEAR-DATABANKS-SETTINGS-FILTERING-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-CLEAR-DATABANKS-SETTINGS-FILTERING-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-CLEAR-DATABANKS-SETTINGS-FILTERING-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.ClearDatabanks.SettingsFilteringPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_clear_databanks.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.

# 13.17 FEAT-PROJECT-SETTINGS-CUSTOM-ANALYSIS - SettingsCustomAnalysis.jar

## 1. Objective

- **Goal:** Implement validated CustomAnalysis settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar`; 1 class declarations; SHA-256 `2014e1848e5e44ee88dd0d785d6b6955ec420c510724db77eaee7a0ba31c616a`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsCustomAnalysis.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-CUSTOM-ANALYSIS`.
- **Owner:** `app/plugins/tasks/SettingsCustomAnalysis/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCustomAnalysis/SettingsCustomAnalysis.jar" com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated CustomAnalysis settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.CustomAnalysis.CustomAnalysisPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_custom_analysis.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 13.18 FEAT-PROJECT-SETTINGS-DATABANKS - SettingsDatabanks.jar

## 1. Objective

- **Goal:** Implement validated Databanks settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsDatabanks/SettingsDatabanks.jar`; 0 class declarations; SHA-256 `dc097f070f4aee60c81ba35a2fa071297a66e29a571be8b1f20dee47325cd556`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsDatabanks.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-DATABANKS`.
- **Owner:** `app/plugins/tasks/SettingsDatabanks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsDatabanks/SettingsDatabanks.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/tasks/SettingsDatabanks/task.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsDatabanks/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/tasks/SettingsDatabanks/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_project_settings_databanks.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/project_settings_databanks.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Databanks settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-DATABANKS-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_databanks.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 13.19 FEAT-PROJECT-SETTINGS-DELETE-FILE - SettingsDeleteFile.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFile.jar`; 1 class declarations; SHA-256 `9b0097abd3e0fe10f963481171cb14e52b0d3538e73523316cd08e584d127d46`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsDeleteFile.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-DELETE-FILE`.
- **Owner:** `app/plugins/tasks/SettingsDeleteFile/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFile.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsDeleteFile/SettingsDeleteFile.jar" com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-DELETE-FILE-SETTINGS-DELETE-FILE-CONTRACT` → `com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-DELETE-FILE-SETTINGS-DELETE-FILE-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-DELETE-FILE-SETTINGS-DELETE-FILE-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.DeleteFile.SettingsDeleteFile.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_delete_file.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.

# 13.20 FEAT-PROJECT-SETTINGS-FILTERING - SettingsFiltering.jar

## 1. Objective

- **Goal:** Implement validated Filtering settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFiltering.jar`; 1 class declarations; SHA-256 `2b4909843e77e93393835c55cbb787cd5e30393ef0e7a9ac78e188f75f90c780`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsFiltering.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-FILTERING`.
- **Owner:** `app/plugins/tasks/SettingsFiltering/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFiltering.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsFiltering/SettingsFiltering.jar" com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Filtering settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-FILTERING-SETTINGS-FILTERING-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-FILTERING-SETTINGS-FILTERING-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-FILTERING-SETTINGS-FILTERING-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.Filtering.SettingsFilteringPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_filtering.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 13.21 FEAT-PROJECT-SETTINGS-GO-TO-TASK - SettingsGoToTask.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTask.jar`; 1 class declarations; SHA-256 `65a839042f98e71f8b63f660e6067fa5c4c2326a87ed005fea7caa51972ccb86`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsGoToTask.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-GO-TO-TASK`.
- **Owner:** `app/plugins/tasks/SettingsGoToTask/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTask.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsGoToTask/SettingsGoToTask.jar" com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-GO-TO-TASK-SETTINGS-GO-TO-TASK-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-GO-TO-TASK-SETTINGS-GO-TO-TASK-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-GO-TO-TASK-SETTINGS-GO-TO-TASK-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.GoToTask.SettingsGoToTaskPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_go_to_task.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.

# 13.22 FEAT-PROJECT-SETTINGS-LOAD-FROM-FILES - SettingsLoadFromFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFiles.jar`; 1 class declarations; SHA-256 `629dc57ef3d62662411a24d6144d6b7c491aba908b155b54ffe30cf1ac2f0a89`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsLoadFromFiles.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-LOAD-FROM-FILES`.
- **Owner:** `app/plugins/tasks/SettingsLoadFromFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFiles.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsLoadFromFiles/SettingsLoadFromFiles.jar" com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-LOAD-FROM-FILES-SETTINGS-LOAD-FROM-FILES-CONTRACT` → `com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-LOAD-FROM-FILES-SETTINGS-LOAD-FROM-FILES-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-LOAD-FROM-FILES-SETTINGS-LOAD-FROM-FILES-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.LoadFromFiles.SettingsLoadFromFiles.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_load_from_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.

# 13.23 FEAT-PROJECT-SETTINGS-LOG-DATABANK-STATS - SettingsLogDatabankStats.jar

## 1. Objective

- **Goal:** Project and log qualified databank statistics.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/SettingsLogDatabankStats.jar`; 1 class declarations; SHA-256 `8e4a151303e2580d408670f9179bec73526e5ee37bf4acc7805e70319c20f1f2`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsLogDatabankStats.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-LOG-DATABANK-STATS`.
- **Owner:** `app/plugins/tasks/SettingsLogDatabankStats/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/SettingsLogDatabankStats.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsLogDatabankStats/SettingsLogDatabankStats.jar" com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project and log qualified databank statistics; verify sample basis, empty bank, metric provenance and redacted diagnostics.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-LOG-DATABANK-STATS-SETTINGS-LOG-DATABANK-STATS-CONTRACT` → `com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-LOG-DATABANK-STATS-SETTINGS-LOG-DATABANK-STATS-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-LOG-DATABANK-STATS-SETTINGS-LOG-DATABANK-STATS-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.LogDatabankStats.SettingsLogDatabankStats.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_log_databank_stats.py --no-cov`; expect sample basis, empty bank, metric provenance and redacted diagnostics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sample basis, empty bank, metric provenance and redacted diagnostics and visible failures.

# 13.24 FEAT-PROJECT-SETTINGS-NOTES - SettingsNotes.jar

## 1. Objective

- **Goal:** Implement validated Notes settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsNotes/SettingsNotes.jar`; 1 class declarations; SHA-256 `bd9fb36e69240c03bbfae7499aa2b102d957505616d0f4b77d861506965c0272`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsNotes.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-NOTES`.
- **Owner:** `app/plugins/tasks/SettingsNotes/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsNotes/SettingsNotes.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsNotes/SettingsNotes.jar" com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Notes settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-NOTES-NOTES-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-NOTES-NOTES-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-NOTES-NOTES-SETTINGS-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.Notes.NotesSettingsPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_notes.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 13.25 FEAT-PROJECT-SETTINGS-NOTIFICATION - SettingsNotification.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotification.jar`; 3 class declarations; SHA-256 `3c6bc47ce8196c989f660a491d138429da886ca96db6f0aa6e90b95c3978e5aa`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsNotification.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-NOTIFICATION`.
- **Owner:** `app/plugins/tasks/SettingsNotification/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotification.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsNotification/SettingsNotification.jar" com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-NOTIFICATION-NOTIFICATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-NOTIFICATION-NOTIFICATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-NOTIFICATION-NOTIFICATION-SERVLET-GET-TYPES` → `com.strategyquant.plugin.Settings.impl.Notification.NotificationServlet.getTypes`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_notification.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.

# 13.26 FEAT-PROJECT-SETTINGS-SAVE-TO-FILES - SettingsSaveToFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFiles.jar`; 1 class declarations; SHA-256 `7d294a5d608c415c3d44a3c790b4a5a6091178f2a2fbe803ad414ca0e67539a8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsSaveToFiles.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-SAVE-TO-FILES`.
- **Owner:** `app/plugins/tasks/SettingsSaveToFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFiles.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsSaveToFiles/SettingsSaveToFiles.jar" com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-SAVE-TO-FILES-SETTINGS-SAVE-TO-FILES-CONTRACT` → `com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-SAVE-TO-FILES-SETTINGS-SAVE-TO-FILES-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-SAVE-TO-FILES-SETTINGS-SAVE-TO-FILES-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.SaveToFiles.SettingsSaveToFiles.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_save_to_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.

# 13.27 FEAT-PROJECT-SETTINGS-STOP-AND-START - SettingsStopAndStart.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStart.jar`; 1 class declarations; SHA-256 `71649d7db652eb2ce2e9356733368bab75c8f93686785166063d9540f0708602`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsStopAndStart.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-STOP-AND-START`.
- **Owner:** `app/plugins/tasks/SettingsStopAndStart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsStopAndStart/SettingsStopAndStart.jar" com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-STOP-AND-START-SETTINGS-STOP-AND-START-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-STOP-AND-START-SETTINGS-STOP-AND-START-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin.getHandler`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-STOP-AND-START-SETTINGS-STOP-AND-START-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.StopAndStart.SettingsStopAndStartPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_stop_and_start.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.

# 13.28 FEAT-PROJECT-SETTINGS-UPDATE-DATA - SettingsUpdateData.jar

## 1. Objective

- **Goal:** Implement validated UpdateData settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateData.jar`; 1 class declarations; SHA-256 `c4331b96cf043eb9a29f83a183486bc289175194e2ef6d3d7b25deac2ca3a1f0`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsUpdateData.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-UPDATE-DATA`.
- **Owner:** `app/plugins/tasks/SettingsUpdateData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateData.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsUpdateData/SettingsUpdateData.jar" com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated UpdateData settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-UPDATE-DATA-SETTINGS-UPDATE-DATA-CONTRACT` → `com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-UPDATE-DATA-SETTINGS-UPDATE-DATA-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-UPDATE-DATA-SETTINGS-UPDATE-DATA-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.UpdateData.SettingsUpdateData.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_update_data.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 13.29 FEAT-PROJECT-SETTINGS-WAIT-FOR - SettingsWaitFor.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitFor.jar`; 1 class declarations; SHA-256 `aa507733110171f3f9074602ed6eef809be814f43f4c53eaa88f66ccb561873d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsWaitFor.md`; roadmap allocation `FEAT-PROJECT-SETTINGS-WAIT-FOR`.
- **Owner:** `app/plugins/tasks/SettingsWaitFor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitFor.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsWaitFor/SettingsWaitFor.jar" com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** `FR-PROJECT-SETTINGS-WAIT-FOR-SETTINGS-WAIT-FOR-CONTRACT` → `com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-SETTINGS-WAIT-FOR-SETTINGS-WAIT-FOR-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-SETTINGS-WAIT-FOR-SETTINGS-WAIT-FOR-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.WaitFor.SettingsWaitFor.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_settings_wait_for.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.

# 13.30 FEAT-PROJECT-TASK-APPLY-MASS-CONFIG - TaskApplyMassConfig.jar

## 1. Objective

- **Goal:** Apply validated configuration across selected resources transactionally.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/TaskApplyMassConfig.jar`; 1 class declarations; SHA-256 `ac4a1b6bb630cd6f326157ff63357041fe3127144fde20397cab5b7f3e3edf81`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskApplyMassConfig.md`; roadmap allocation `FEAT-PROJECT-TASK-APPLY-MASS-CONFIG`.
- **Owner:** `app/plugins/tasks/TaskApplyMassConfig/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/TaskApplyMassConfig.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskApplyMassConfig/TaskApplyMassConfig.jar" com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Apply validated configuration across selected resources transactionally; verify target selection, compatibility, rollback and unaffected settings.
- [ ] **Step 4:** `FR-PROJECT-TASK-APPLY-MASS-CONFIG-APPLY-MASS-CONFIG-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-APPLY-MASS-CONFIG-APPLY-MASS-CONFIG-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-APPLY-MASS-CONFIG-APPLY-MASS-CONFIG-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.ApplyMassConfig.ApplyMassConfigTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_apply_mass_config.py --no-cov`; expect target selection, compatibility, rollback and unaffected settings; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target selection, compatibility, rollback and unaffected settings and visible failures.

# 13.31 FEAT-PROJECT-TASK-CALL-EXTERNAL-SCRIPT - TaskCallExternalScript.jar

## 1. Objective

- **Goal:** Execute qualified external processes with scoped authority and owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/TaskCallExternalScript.jar`; 2 class declarations; SHA-256 `c5addbaacb182f7aeaac86f666fc283a019641207f2a0720b261afbbe24c18e2`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskCallExternalScript.md`; roadmap allocation `FEAT-PROJECT-TASK-CALL-EXTERNAL-SCRIPT`.
- **Owner:** `app/plugins/tasks/TaskCallExternalScript/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/TaskCallExternalScript.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskCallExternalScript/TaskCallExternalScript.jar" com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute qualified external processes with scoped authority and owned lifecycle; verify allowlisted invocation, timeout, exit failure, cancellation and redacted output.
- [ ] **Step 4:** `FR-PROJECT-TASK-CALL-EXTERNAL-SCRIPT-CALL-EXTERNAL-SCRIPT-CONTRACT` → `com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-CALL-EXTERNAL-SCRIPT-CALL-EXTERNAL-SCRIPT-GET-TYPE` → `com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-CALL-EXTERNAL-SCRIPT-CALL-EXTERNAL-SCRIPT-CLONE` → `com.strategyquant.plugin.Task.impl.CallExternalScript.CallExternalScript.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_call_external_script.py --no-cov`; expect allowlisted invocation, timeout, exit failure, cancellation and redacted output; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture allowlisted invocation, timeout, exit failure, cancellation and redacted output and visible failures.

# 13.32 FEAT-PROJECT-TASK-CLEAR-DATABANKS - TaskClearDatabanks.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanks.jar`; 1 class declarations; SHA-256 `8e607eed55b134b7cfbeb8549fe7fb274a1b0a7bf40172489e962cc3ba7bba46`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskClearDatabanks.md`; roadmap allocation `FEAT-PROJECT-TASK-CLEAR-DATABANKS`.
- **Owner:** `app/plugins/tasks/TaskClearDatabanks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanks.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskClearDatabanks/TaskClearDatabanks.jar" com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** `FR-PROJECT-TASK-CLEAR-DATABANKS-CLEAR-DATABANKS-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-CLEAR-DATABANKS-CLEAR-DATABANKS-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-CLEAR-DATABANKS-CLEAR-DATABANKS-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.ClearDatabanks.ClearDatabanksTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_clear_databanks.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.

# 13.33 FEAT-PROJECT-TASK-CUSTOM-ANALYSIS - TaskCustomAnalysis.jar

## 1. Objective

- **Goal:** Run qualified custom analysis resources against selected results.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/TaskCustomAnalysis.jar`; 1 class declarations; SHA-256 `4c3b57a15910fddc9ecedb2dd705ca211d7438ded737490fdf3e2bdfb09610e1`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskCustomAnalysis.md`; roadmap allocation `FEAT-PROJECT-TASK-CUSTOM-ANALYSIS`.
- **Owner:** `app/plugins/tasks/TaskCustomAnalysis/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/TaskCustomAnalysis.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskCustomAnalysis/TaskCustomAnalysis.jar" com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Run qualified custom analysis resources against selected results; verify resource trust/version, input identity and execution failure.
- [ ] **Step 4:** `FR-PROJECT-TASK-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-CUSTOM-ANALYSIS-CUSTOM-ANALYSIS-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.CustomAnalysis.CustomAnalysisTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_custom_analysis.py --no-cov`; expect resource trust/version, input identity and execution failure; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource trust/version, input identity and execution failure and visible failures.

# 13.34 FEAT-PROJECT-TASK-DELETE-FILE - TaskDeleteFile.jar

## 1. Objective

- **Goal:** Execute the named destructive task only with scoped explicit authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/TaskDeleteFile.jar`; 1 class declarations; SHA-256 `b9d41645306dd25c981fafc5c41c18c3aabf6699a30291ec67a81215e0fef124`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskDeleteFile.md`; roadmap allocation `FEAT-PROJECT-TASK-DELETE-FILE`.
- **Owner:** `app/plugins/tasks/TaskDeleteFile/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/TaskDeleteFile.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskDeleteFile/TaskDeleteFile.jar" com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute the named destructive task only with scoped explicit authority; verify target resolution, denied action, atomic outcome and unaffected resources.
- [ ] **Step 4:** `FR-PROJECT-TASK-DELETE-FILE-DELETE-FILE-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-DELETE-FILE-DELETE-FILE-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-DELETE-FILE-DELETE-FILE-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.DeleteFile.DeleteFileTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_delete_file.py --no-cov`; expect target resolution, denied action, atomic outcome and unaffected resources; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture target resolution, denied action, atomic outcome and unaffected resources and visible failures.

# 13.35 FEAT-PROJECT-TASK-FILTERING - TaskFiltering.jar

## 1. Objective

- **Goal:** Execute Filtering through an owned typed task capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskFiltering/TaskFiltering.jar`; 1 class declarations; SHA-256 `a8c0774c1fdec537b8b8de218f650b43622486a4df239593b73b25663217066d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskFiltering.md`; roadmap allocation `FEAT-PROJECT-TASK-FILTERING`.
- **Owner:** `app/plugins/tasks/TaskFiltering/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskFiltering/TaskFiltering.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskFiltering/TaskFiltering.jar" com.strategyquant.plugin.Task.impl.Filtering.FilteringTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute Filtering through an owned typed task capability; verify input handles, start/stop/clone transitions, failure status and retained outputs.
- [ ] **Step 4:** `FR-PROJECT-TASK-FILTERING-FILTERING-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Filtering.FilteringTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-FILTERING-FILTERING-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.Filtering.FilteringTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-FILTERING-FILTERING-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.Filtering.FilteringTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_filtering.py --no-cov`; expect input handles, start/stop/clone transitions, failure status and retained outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture input handles, start/stop/clone transitions, failure status and retained outputs and visible failures.

# 13.36 FEAT-PROJECT-TASK-GO-TO-TASK - TaskGoToTask.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskGoToTask/TaskGoToTask.jar`; 1 class declarations; SHA-256 `193d01b583617106ba2644aa9e60aad38b6ccd1a3980656bace7bc4ee82e489e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskGoToTask.md`; roadmap allocation `FEAT-PROJECT-TASK-GO-TO-TASK`.
- **Owner:** `app/plugins/tasks/TaskGoToTask/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskGoToTask/TaskGoToTask.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskGoToTask/TaskGoToTask.jar" com.strategyquant.plugin.Task.impl.GoToTask.GoToTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** `FR-PROJECT-TASK-GO-TO-TASK-GO-TO-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.GoToTask.GoToTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-GO-TO-TASK-GO-TO-TASK-START` → `com.strategyquant.plugin.Task.impl.GoToTask.GoToTask.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-GO-TO-TASK-GO-TO-TASK-GET-RUNNING-STATUS` → `com.strategyquant.plugin.Task.impl.GoToTask.GoToTask.getRunningStatus`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_go_to_task.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.

# 13.37 FEAT-PROJECT-TASK-LOAD-FROM-FILES - TaskLoadFromFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/TaskLoadFromFiles.jar`; 1 class declarations; SHA-256 `c16da8329e61459143b013fa8ea953e684e7aed67c735c780a63972e1de3250f`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskLoadFromFiles.md`; roadmap allocation `FEAT-PROJECT-TASK-LOAD-FROM-FILES`.
- **Owner:** `app/plugins/tasks/TaskLoadFromFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/TaskLoadFromFiles.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskLoadFromFiles/TaskLoadFromFiles.jar" com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** `FR-PROJECT-TASK-LOAD-FROM-FILES-LOAD-FROM-FILES-CONTRACT` → `com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-LOAD-FROM-FILES-LOAD-FROM-FILES-START` → `com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-LOAD-FROM-FILES-LOAD-FROM-FILES-GET-RUNNING-STATUS` → `com.strategyquant.plugin.Task.impl.LoadFromFiles.LoadFromFiles.getRunningStatus`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_load_from_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.

# 13.38 FEAT-PROJECT-TASK-LOG-DATABANK-STATS - TaskLogDatabankStats.jar

## 1. Objective

- **Goal:** Project and log qualified databank statistics.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar`; 1 class declarations; SHA-256 `2a903db425c206f8ffaa3c22a97cca1f95fbde6379caf12f970c7954fd228188`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskLogDatabankStats.md`; roadmap allocation `FEAT-PROJECT-TASK-LOG-DATABANK-STATS`.
- **Owner:** `app/plugins/tasks/TaskLogDatabankStats/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskLogDatabankStats/TaskLogDatabankStats.jar" com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project and log qualified databank statistics; verify sample basis, empty bank, metric provenance and redacted diagnostics.
- [ ] **Step 4:** `FR-PROJECT-TASK-LOG-DATABANK-STATS-LOG-DATABANK-STATS-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-LOG-DATABANK-STATS-LOG-DATABANK-STATS-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-LOG-DATABANK-STATS-LOG-DATABANK-STATS-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.LogDatabankStats.LogDatabankStatsTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_log_databank_stats.py --no-cov`; expect sample basis, empty bank, metric provenance and redacted diagnostics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture sample basis, empty bank, metric provenance and redacted diagnostics and visible failures.

# 13.39 FEAT-PROJECT-TASK-MANAGER-PROJECTS - TaskManagerProjects.jar

## 1. Objective

- **Goal:** Execute ManagerProjects through an owned typed task capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar`; 2 class declarations; SHA-256 `6d07140b3c697f54bfebeb17f503347b341f1f10a36abc3ab21ba3793af9fd91`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskManagerProjects.md`; roadmap allocation `FEAT-PROJECT-TASK-MANAGER-PROJECTS`.
- **Owner:** `app/plugins/project/TaskManagerProjects/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Project DAG/task transitions, condition evaluation and document exchange; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskManagerProjects/TaskManagerProjects.jar" com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute ManagerProjects through an owned typed task capability; verify input handles, start/stop/clone transitions, failure status and retained outputs.
- [ ] **Step 4:** `FR-PROJECT-TASK-MANAGER-PROJECTS-TM-PROJECTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-MANAGER-PROJECTS-TM-PROJECTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.TaskManager.impl.Projects.TMProjectsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_manager_projects.py --no-cov`; expect input handles, start/stop/clone transitions, failure status and retained outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture input handles, start/stop/clone transitions, failure status and retained outputs and visible failures.

# 13.40 FEAT-PROJECT-TASK-NOTIFICATION - TaskNotification.jar

## 1. Objective

- **Goal:** Prepare typed notifications/mail through an explicitly authorized delivery capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotification.jar`; 1 class declarations; SHA-256 `18e4129e84815d9806d35901011fe9f1311e28bda374b1bd590adcea8bfbe8b3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskNotification.md`; roadmap allocation `FEAT-PROJECT-TASK-NOTIFICATION`.
- **Owner:** `app/plugins/tasks/TaskNotification/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotification.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskNotification/TaskNotification.jar" com.strategyquant.plugin.Task.impl.Notification.NotificationTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Prepare typed notifications/mail through an explicitly authorized delivery capability; verify recipient/input validation, redaction, timeout and failed delivery.
- [ ] **Step 4:** `FR-PROJECT-TASK-NOTIFICATION-NOTIFICATION-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Notification.NotificationTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-NOTIFICATION-NOTIFICATION-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.Notification.NotificationTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-NOTIFICATION-NOTIFICATION-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.Notification.NotificationTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_notification.py --no-cov`; expect recipient/input validation, redaction, timeout and failed delivery; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture recipient/input validation, redaction, timeout and failed delivery and visible failures.

# 13.41 FEAT-PROJECT-TASK-SAVE-TO-FILES - TaskSaveToFiles.jar

## 1. Objective

- **Goal:** Load/save task artifacts through host-owned bounded resource handles.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/TaskSaveToFiles.jar`; 1 class declarations; SHA-256 `9cadabab1f360b8d3ec1db9f11bcb3af244298ec13d683fceaa9af5028b20e52`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskSaveToFiles.md`; roadmap allocation `FEAT-PROJECT-TASK-SAVE-TO-FILES`.
- **Owner:** `app/plugins/tasks/TaskSaveToFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/TaskSaveToFiles.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskSaveToFiles/TaskSaveToFiles.jar" com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Load/save task artifacts through host-owned bounded resource handles; verify format version, path authority, partial write and resource identity.
- [ ] **Step 4:** `FR-PROJECT-TASK-SAVE-TO-FILES-SAVE-TO-FILES-CONTRACT` → `com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-SAVE-TO-FILES-SAVE-TO-FILES-START` → `com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-SAVE-TO-FILES-SAVE-TO-FILES-GET-RUNNING-STATUS` → `com.strategyquant.plugin.Task.impl.SaveToFiles.SaveToFiles.getRunningStatus`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_save_to_files.py --no-cov`; expect format version, path authority, partial write and resource identity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, path authority, partial write and resource identity and visible failures.

# 13.42 FEAT-PROJECT-TASK-STOP-AND-START - TaskStopAndStart.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar`; 1 class declarations; SHA-256 `1179ec5df70066f2f0bfdc60458ec3a656c074f514c5ccffc707fbce7387c99a`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskStopAndStart.md`; roadmap allocation `FEAT-PROJECT-TASK-STOP-AND-START`.
- **Owner:** `app/plugins/tasks/TaskStopAndStart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskStopAndStart/TaskStopAndStart.jar" com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** `FR-PROJECT-TASK-STOP-AND-START-STOP-AND-START-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-STOP-AND-START-STOP-AND-START-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-STOP-AND-START-STOP-AND-START-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.StopAndStart.StopAndStartTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_stop_and_start.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.

# 13.43 FEAT-PROJECT-TASK-UPDATE-DATA - TaskUpdateData.jar

## 1. Objective

- **Goal:** Delegate data updates through qualified provider jobs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskUpdateData/TaskUpdateData.jar`; 2 class declarations; SHA-256 `3d34fcd874c184c8252011f964cc0c3d7d2f841dd8c8954376db356555507b08`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskUpdateData.md`; roadmap allocation `FEAT-PROJECT-TASK-UPDATE-DATA`.
- **Owner:** `app/plugins/tasks/TaskUpdateData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskUpdateData/TaskUpdateData.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskUpdateData/TaskUpdateData.jar" com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Delegate data updates through qualified provider jobs; verify selected dataset, partial failure, cancellation and updated provenance.
- [ ] **Step 4:** `FR-PROJECT-TASK-UPDATE-DATA-UPDATE-DATA-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-UPDATE-DATA-UPDATE-DATA-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-UPDATE-DATA-UPDATE-DATA-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.UpdateData.UpdateDataTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_update_data.py --no-cov`; expect selected dataset, partial failure, cancellation and updated provenance; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture selected dataset, partial failure, cancellation and updated provenance and visible failures.

# 13.44 FEAT-PROJECT-TASK-WAIT-FOR - TaskWaitFor.jar

## 1. Objective

- **Goal:** Implement the named task-control transition under bounded graph ownership.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute custom-project task graphs with owned conditions and bounded side effects.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskWaitFor/TaskWaitFor.jar`; 2 class declarations; SHA-256 `ce277abb4da154cd5a7a0cbe9183ba0f8105c2ce81db8c62d61329319357e3c0`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskWaitFor.md`; roadmap allocation `FEAT-PROJECT-TASK-WAIT-FOR`.
- **Owner:** `app/plugins/tasks/TaskWaitFor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Task-specific settings/execution and bounded project actions; downstream P03,P08–P12.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskWaitFor/TaskWaitFor.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskWaitFor/TaskWaitFor.jar" com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named task-control transition under bounded graph ownership; verify jump target, time units, cancellation, cycles and invalid transition.
- [ ] **Step 4:** `FR-PROJECT-TASK-WAIT-FOR-WAIT-FOR-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PROJECT-TASK-WAIT-FOR-WAIT-FOR-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PROJECT-TASK-WAIT-FOR-WAIT-FOR-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.WaitFor.WaitForTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_project_task_wait_for.py --no-cov`; expect jump target, time units, cancellation, cycles and invalid transition; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture jump target, time units, cancellation, cycles and invalid transition and visible failures.

# 13.45 FEAT-UI-PROJECT-SETTINGS - ProjectSettings resource contribution

## 1. Objective

- **Goal:** Qualify and connect ProjectSettings without assuming a missing backend JAR.
- **Context / Problem Solved:** ProjectSettings is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectSettings`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/ProjectSettings/module.js`.
- **FR:** `FR-UI-PROJECT-SETTINGS-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/project/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

## 3. File Changes

- **Create:** `app/plugins/project/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Create:** `app/plugins/project/README.md`
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_project_settings.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-PROJECT-SETTINGS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_project_settings.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority. Inspect the ProjectSettings contribution; an empty or unavailable contribution must remain explicit.

# 13.46 FEAT-UI-SETTINGS-PANEL - SettingsPanel resource contribution

## 1. Objective

- **Goal:** Qualify and connect SettingsPanel without assuming a missing backend JAR.
- **Context / Problem Solved:** SettingsPanel is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsPanel`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/SettingsPanel/module.js`.
- **FR:** `FR-UI-SETTINGS-PANEL-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/project/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

## 3. File Changes

- **Modify:** `app/plugins/project/resource_contributions.py` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/plugins/project/README.md` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_settings_panel.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-SETTINGS-PANEL-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_settings_panel.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority. Inspect the SettingsPanel contribution; an empty or unavailable contribution must remain explicit.

# 13.47 FEAT-UI-TASK-MANAGER-TASKS - TaskManagerTasks resource contribution

## 1. Objective

- **Goal:** Qualify and connect TaskManagerTasks without assuming a missing backend JAR.
- **Context / Problem Solved:** TaskManagerTasks is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskManagerTasks`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/TaskManagerTasks/module.js`.
- **FR:** `FR-UI-TASK-MANAGER-TASKS-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/project/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

## 3. File Changes

- **Modify:** `app/plugins/project/resource_contributions.py` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/plugins/project/README.md` (proposed earlier in FEAT-UI-PROJECT-SETTINGS)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_task_manager_tasks.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-TASK-MANAGER-TASKS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_task_manager_tasks.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority. Inspect the TaskManagerTasks contribution; an empty or unavailable contribution must remain explicit.

# 13.48 P13 integration — Execute custom-project task graphs with owned conditions and bounded side effects

## 1. Objective

- **Goal:** Execute custom-project task graphs with owned conditions and bounded side effects.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P13; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/CustomProjects/customProjects.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify task graph versions, input/output handles, conditions, jumps, loops and clone semantics.
- [ ] **Step 3:** Implement task adapters against existing build/retest/data/portfolio capabilities; bound execution.
- [ ] **Step 4:** Connect CustomProjects task controls and logs; require separate authority for destructive/external effects.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_custom_projects_tasks_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/CustomProjects/customProjects.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-custom-projects-tasks-backend.spec.ts`. Assert graph save/reload, condition boundaries, task ordering and delegated result handles; reject invalid jump, runaway loop, missing capability and denied external/delete action.
- **Manual / Browser Verification:** Run a small build→retest→save graph on fixtures; inspect condition transitions; reject a destructive task without authority.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
