# P07 — AlgoWizard, CodeEditor, custom resources and platform code generation

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P02,P05,P06.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 18 tasks; current archive allocations and resource/integration tasks only.

# 7.1 FEAT-AUTHORING-FREEMARKER - freemarker-2.3.28.jar

## 1. Objective

- **Goal:** Render supported code/report templates through a ratified Python template adapter.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/freemarker-2.3.28.jar`; 1124 raw class entries; SHA-256 `de92d103d3a86c2287307218ff50dc1c941de283f7b9e1fb23e93fc7220838bf`.
- **Inspected reference:** [freemarker-2.3.28.md](sqx/Libraries/freemarker-2.3.28.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/freemarker-2.3.28.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/freemarker-2.3.28.jar" freemarker.cache.AndMatcher`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Authoring, snippet/resource loading and target-language template generation; downstream P08,P09,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds AlgoWizard through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/workspace/AlgoWizard/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/AlgoWizard/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/templates.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/emitters.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/AlgoWizard/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_freemarker.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_freemarker.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Render supported code/report templates through a ratified Python template adapter; verify escaping, missing variables, deterministic output and target syntax.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-AUTHORING-FREEMARKER-AND-MATCHER-CONTRACT` → `freemarker.cache.AndMatcher`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-AUTHORING-FREEMARKER-AND-MATCHER-MATCHES` → `freemarker.cache.AndMatcher.matches(Ljava/lang/String;Ljava/lang/Object;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_freemarker.py --no-cov`; expect escaping, missing variables, deterministic output and target syntax; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture escaping, missing variables, deterministic output and target syntax and visible failures.


# 7.2 FEAT-AUTHORING-JAVASSIST - javassist-3.21.0-GA.jar

## 1. Objective

- **Goal:** Replace consumed bytecode-extension mechanisms with an approved Python resource mechanism.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/javassist-3.21.0-GA.jar`; 399 raw class entries; SHA-256 `7aa59e031f941984af07dacc6ca85e6dc9bd3a485e9aa2494cbc034efa1225d0`.
- **Inspected reference:** [javassist-3.21.0-GA.md](sqx/Libraries/javassist-3.21.0-GA.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/javassist-3.21.0-GA.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/javassist-3.21.0-GA.jar" javassist.ByteArrayClassPath`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Authoring, snippet/resource loading and target-language template generation; downstream P08,P09,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds AlgoWizard through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/workspace/AlgoWizard/service.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/contracts.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/code_generation/templates.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/code_generation/emitters.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_javassist.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_javassist.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Replace consumed bytecode-extension mechanisms with an approved Python resource mechanism; verify trust boundary, version rejection and qualified extension lifecycle.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-AUTHORING-JAVASSIST-BYTE-ARRAY-CLASS-PATH-CONTRACT` → `javassist.ByteArrayClassPath`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-AUTHORING-JAVASSIST-BYTE-ARRAY-CLASS-PATH-CLOSE` → `javassist.ByteArrayClassPath.close()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-JAVASSIST-BYTE-ARRAY-CLASS-PATH-TO-STRING` → `javassist.ByteArrayClassPath.toString()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_javassist.py --no-cov`; expect trust boundary, version rejection and qualified extension lifecycle; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture trust boundary, version rejection and qualified extension lifecycle and visible failures.


# 7.3 FEAT-AUTHORING-APP-CODE-EDITOR - AppCodeEditor.jar

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar`; 3 raw class entries; SHA-256 `df88cbdf4baae6ee27892d389cefd6349fee81962f12d21ff45b663094826a15`.
- **Inspected reference:** [AppCodeEditor.md](sqx/CodeEditor/AppCodeEditor.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppCodeEditor/AppCodeEditor.jar" com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppCodeEditor`; `SQX_145_REFERENCE_ROOT/internal/web/SQEDITOR`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppCodeEditor/module.js`.
- **Existing UI connection:** Code Editor; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`; wire extension import/export, compilation diagnostics and real indicator test outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/CodeEditor/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_app_code_editor.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_app_code_editor.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/IndicatorTesterModal.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CodeEditor/codeEditorClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-app-code-editor.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind extension import/export, compilation diagnostics and real indicator test outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-APP-CODE-EDITOR-CODE-EDITOR-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-APP-CODE-EDITOR-CODE-EDITOR-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-APP-CODE-EDITOR-CODE-EDITOR-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_app_code_editor.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-app-code-editor.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Code Editor for FEAT-AUTHORING-APP-CODE-EDITOR; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.4 FEAT-AUTHORING-APP-WIZARD - AppWizard.jar

## 1. Objective

- **Goal:** Mount the Wizard workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard/AppWizard.jar`; 1 raw class entries; SHA-256 `227299033d9c844ebf23e4f7f48bc8ae9f77256c8971a4cec1c29b14e7c78425`.
- **Inspected reference:** [AppWizard.md](sqx/AlgoWizard/AppWizard.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard/AppWizard.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard/AppWizard.jar" com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/AlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard`; `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard/AlgoWizardService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard/module.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppWizard/styles.css`.
- **Existing UI connection:** AlgoWizard; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/AlgoWizard/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/AlgoWizard/routes.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/contracts.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_app_wizard.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_app_wizard.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-app-wizard.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Wizard workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-APP-WIZARD-WIZARD-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-APP-WIZARD-WIZARD-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-APP-WIZARD-WIZARD-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.Wizard.WizardAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_app_wizard.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-app-wizard.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for FEAT-AUTHORING-APP-WIZARD; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.5 FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT - CodeEditorImportExport.jar

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar`; 5 raw class entries; SHA-256 `64d2f79b52a571d08aa90f0e56071bbc5fe1bfee5b30865bab8f18b1822ba990`.
- **Inspected reference:** [CodeEditorImportExport.md](sqx/CodeEditor/CodeEditorImportExport.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar" com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport`; `SQX_145_REFERENCE_ROOT/internal/web/SQEDITOR`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExportService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/export/controllers/CEExportPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/import/controllers/CEImportCtrl.js`.
- **Existing UI connection:** Code Editor; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`; wire extension import/export, compilation diagnostics and real indicator test outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/CodeEditor/service.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/CodeEditor/resources.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_code_editor_import_export.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_code_editor_import_export.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/IndicatorTesterModal.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CodeEditor/codeEditorClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-code-editor-import-export.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind extension import/export, compilation diagnostics and real indicator test outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-CODE-EDITOR-IMPORT-EXPORT-IMPORT-EXPORT-SERVLET-CONTRACT` → `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-CODE-EDITOR-IMPORT-EXPORT-IMPORT-EXPORT-SERVLET-EXECUTE` → `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-CODE-EDITOR-IMPORT-EXPORT-IMPORT-EXPORT-SERVLET-ON-LIST` → `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet.onList(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_code_editor_import_export.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-code-editor-import-export.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Code Editor for FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.6 FEAT-AUTHORING-CODE-EDITOR-INDICATOR-TESTER - CodeEditorIndicatorTester.jar

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/CodeEditorIndicatorTester.jar`; 7 raw class entries; SHA-256 `f4d719de679ce6da796373e0342e3c0de70078273ebc0f69ba43a6fab49e7071`.
- **Inspected reference:** [CodeEditorIndicatorTester.md](sqx/CodeEditor/CodeEditorIndicatorTester.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/CodeEditorIndicatorTester.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/CodeEditorIndicatorTester.jar" com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester`; `SQX_145_REFERENCE_ROOT/internal/web/SQEDITOR`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/services/IndicatorTesterService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/controllers/IndicatorTesterCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/views/editIndyParamsPopup.html`.
- **Existing UI connection:** Code Editor; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`; wire extension import/export, compilation diagnostics and real indicator test outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/CodeEditor/service.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/resources.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_code_editor_indicator_tester.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_code_editor_indicator_tester.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/IndicatorTesterModal.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CodeEditor/codeEditorClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-code-editor-indicator-tester.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind extension import/export, compilation diagnostics and real indicator test outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-CODE-EDITOR-INDICATOR-TESTER-INDICATOR-TEST-EXECUTOR-CONTRACT` → `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-CODE-EDITOR-INDICATOR-TESTER-INDICATOR-TEST-EXECUTOR-GET` → `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor.get()Lcom/strategyquant/plugin/CodeEditor/impl/IndicatorTester/IndicatorTestExecutor;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-CODE-EDITOR-INDICATOR-TESTER-INDICATOR-TEST-EXECUTOR-START` → `com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor.start()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_code_editor_indicator_tester.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-code-editor-indicator-tester.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Code Editor for FEAT-AUTHORING-CODE-EDITOR-INDICATOR-TESTER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.7 FEAT-AUTHORING-LOADER-SQ3 - LoaderSQ3.jar

## 1. Objective

- **Goal:** Implement the named native strategy archive version and round-trip rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ3/LoaderSQ3.jar`; 5 raw class entries; SHA-256 `5821dfc918051a68cb9e191209479d0041cf56271ac66f4588416525cdd57fe0`.
- **Inspected reference:** [LoaderSQ3.md](sqx/Shared/LoaderSQ3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ3/LoaderSQ3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ3/LoaderSQ3.jar" com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/strategy/LoaderSQ3/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ3`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`.
- **Existing UI connection:** databank load; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/load/LoadService.ts`; wire selected archive upload/import, format validation and persisted strategy/databank resources.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/strategy/LoaderSQ3/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ3/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ3/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ3/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_loader_sq3.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_loader_sq3.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/LoadService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/LoadPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/loadPopup.tsx`
  - Display selected archive upload/import, format validation and persisted strategy/databank resources from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-loader-sq3.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named native strategy archive version and round-trip rules; verify format version, unknown fields, checksum/entry validation and preserved semantics.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected archive upload/import, format validation and persisted strategy/databank resources to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-LOADER-SQ3-SQ3-FILE-LOADER-CONTRACT` → `com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-LOADER-SQ3-SQ3-FILE-LOADER-LOAD` → `com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoader.load(Ljava/lang/String;ZLjava/lang/String;)Lcom/strategyquant/tradinglib/ResultsGroup;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_loader_sq3.py --no-cov`; expect format version, unknown fields, checksum/entry validation and preserved semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, unknown fields, checksum/entry validation and preserved semantics and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-loader-sq3.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databank load for FEAT-AUTHORING-LOADER-SQ3; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.8 FEAT-AUTHORING-LOADER-SQ4 - LoaderSQ4.jar

## 1. Objective

- **Goal:** Implement the named native strategy archive version and round-trip rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar`; 1 raw class entries; SHA-256 `fdfae28061c503d76a141611891151148f4f5940541ae2ab331c9023b260a909`.
- **Inspected reference:** [LoaderSQ4.md](sqx/Shared/LoaderSQ4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ4/LoaderSQ4.jar" com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/strategy/LoaderSQ4/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/LoaderSQ4`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`.
- **Existing UI connection:** databank load; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/load/LoadService.ts`; wire selected archive upload/import, format validation and persisted strategy/databank resources.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/strategy/LoaderSQ4/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ4/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ4/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/LoaderSQ4/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_loader_sq4.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_loader_sq4.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/LoadService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/LoadPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/load/loadPopup.tsx`
  - Display selected archive upload/import, format validation and persisted strategy/databank resources from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-loader-sq4.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named native strategy archive version and round-trip rules; verify format version, unknown fields, checksum/entry validation and preserved semantics.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected archive upload/import, format validation and persisted strategy/databank resources to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-LOADER-SQ4-SQ4-LOADER-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-LOADER-SQ4-SQ4-LOADER-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-LOADER-SQ4-SQ4-LOADER-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_loader_sq4.py --no-cov`; expect format version, unknown fields, checksum/entry validation and preserved semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, unknown fields, checksum/entry validation and preserved semantics and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-loader-sq4.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databank load for FEAT-AUTHORING-LOADER-SQ4; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.9 FEAT-AUTHORING-RESULTS-SOURCE-CODE - ResultsSourceCode.jar

## 1. Objective

- **Goal:** Implement authoritative SourceCode result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/ResultsSourceCode.jar`; 2 raw class entries; SHA-256 `3e7fcf22b7a4c6e0b38875853ceefb14592837cd8f82ce71a43715aeaaa406e6`.
- **Inspected reference:** [ResultsSourceCode.md](sqx/Results/ResultsSourceCode.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/ResultsSourceCode.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/ResultsSourceCode.jar" com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/code_generation/ResultsSourceCode/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy source-generation projection; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode`; `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/SourceCodeService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/SourceCodeCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/customIndicatorsPopup.html`.
- **Existing UI connection:** AlgoWizard; exact retained source-map `ui/app/plugins/project/ResultsSourceCode/source-map.json`. Target `ui/app/plugins/project/ResultsSourceCode/SourceCodeCtrl.ts`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.


- **Build 145 UI donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/sourceCode/ninjaTrader/module.js`; `internal/extend/Code/NinjaTrader/Main.tpl`. Connect retained source-code/save consumers; reject unsupported on-tick export explicitly.

## 3. File Changes

- **Create:** `app/plugins/code_generation/ResultsSourceCode/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/ResultsSourceCode/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/code_generation/ResultsSourceCode/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_results_source_code.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_results_source_code.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsSourceCode/SourceCodeCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsSourceCode/sourceCode.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsSourceCode/module.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsSourceCode/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-results-source-code.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative SourceCode result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-RESULTS-SOURCE-CODE-SOURCE-CODE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-RESULTS-SOURCE-CODE-SOURCE-CODE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-RESULTS-SOURCE-CODE-SOURCE-CODE-SERVLET-ON-LIST-MM` → `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet.onListMM()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_results_source_code.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-results-source-code.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for FEAT-AUTHORING-RESULTS-SOURCE-CODE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.10 FEAT-AUTHORING-SAVER-SQ3 - SaverSQ3.jar

## 1. Objective

- **Goal:** Implement the named native strategy archive version and round-trip rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SaverSQ3/SaverSQ3.jar`; 2 raw class entries; SHA-256 `f8c9e0d4853ee53e732fe2fcdf057296770b79fd7a9e0aa26fc585b991b9f0cc`.
- **Inspected reference:** [SaverSQ3.md](sqx/Shared/SaverSQ3.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SaverSQ3/SaverSQ3.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SaverSQ3/SaverSQ3.jar" com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/strategy/SaverSQ3/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SaverSQ3`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`.
- **Existing UI connection:** databank save/export; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`; wire selected format/strategy export, real generated artifact IDs and verified downloads.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/strategy/SaverSQ3/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/SaverSQ3/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/SaverSQ3/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/SaverSQ3/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_saver_sq3.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_saver_sq3.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/SaveButtonService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/saveBtnPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/savePopup.tsx`
  - Display selected format/strategy export, real generated artifact IDs and verified downloads from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-saver-sq3.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named native strategy archive version and round-trip rules; verify format version, unknown fields, checksum/entry validation and preserved semantics.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected format/strategy export, real generated artifact IDs and verified downloads to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-SAVER-SQ3-SQ3-FILE-SAVER-CONTRACT` → `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-SAVER-SQ3-SQ3-FILE-SAVER-SAVE` → `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver.save(Lcom/strategyquant/tradinglib/ResultsGroup;Ljava/lang/String;Ljava/util/Map;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-SAVER-SQ3-SQ3-FILE-SAVER-GET-PARAM` → `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver.getParam(Ljava/util/Map;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_saver_sq3.py --no-cov`; expect format version, unknown fields, checksum/entry validation and preserved semantics; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture format version, unknown fields, checksum/entry validation and preserved semantics and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-saver-sq3.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise databank save/export for FEAT-AUTHORING-SAVER-SQ3; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.11 FEAT-AUTHORING-SERVLET-ALGO-WIZARD - ServletAlgoWizard.jar

## 1. Objective

- **Goal:** Expose AlgoWizard commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar`; 4 raw class entries; SHA-256 `40595742e8d58ca30f84671dcfd5280d15a6a42222166c510efffc444a29de45`.
- **Inspected reference:** [ServletAlgoWizard.md](sqx/AlgoWizard/ServletAlgoWizard.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar" com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/strategy/ServletAlgoWizard/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard/index.html`.
- **Existing UI connection:** AlgoWizard; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/strategy/ServletAlgoWizard/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletAlgoWizard/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletAlgoWizard/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletAlgoWizard/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_algo_wizard.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_algo_wizard.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-servlet-algo-wizard.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose AlgoWizard commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-SERVLET-ALGO-WIZARD-ALGO-WIZARD-BLOCKS-TAG-CLOUD-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-SERVLET-ALGO-WIZARD-ALGO-WIZARD-BLOCKS-TAG-CLOUD-LOAD` → `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud.load()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-SERVLET-ALGO-WIZARD-ALGO-WIZARD-BLOCKS-TAG-CLOUD-LIST-JSON` → `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud.listJSON()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_algo_wizard.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-servlet-algo-wizard.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for FEAT-AUTHORING-SERVLET-ALGO-WIZARD; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.12 FEAT-AUTHORING-SERVLET-CODE-EDITOR - ServletCodeEditor.jar

## 1. Objective

- **Goal:** Qualify editor resources and execute actual indicator test fixtures.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/ServletCodeEditor.jar`; 13 raw class entries; SHA-256 `ad9b7062db2f6bc617a5e865b01b049f03f21d28f2db61b35976c122c0edbef7`.
- **Inspected reference:** [ServletCodeEditor.md](sqx/CodeEditor/ServletCodeEditor.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/ServletCodeEditor.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/ServletCodeEditor.jar" com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/CodeEditor/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Code/resource authoring, exchange and indicator qualification; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor`; `SQX_145_REFERENCE_ROOT/internal/web/SQEDITOR`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/services/CodeEditorService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/bottomtabs/BottomTabsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/maintabs/MainTabsCtrl.js`.
- **Existing UI connection:** Code Editor; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`; wire extension import/export, compilation diagnostics and real indicator test outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/CodeEditor/service.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/resources.py` (proposed earlier in FEAT-AUTHORING-CODE-EDITOR-IMPORT-EXPORT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/CodeEditor/README.md` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_code_editor.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_code_editor.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/IndicatorTesterModal.tsx`
  - Display extension import/export, compilation diagnostics and real indicator test outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/CodeEditor/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Create:** `ui/app/workspace/CodeEditor/codeEditorClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-servlet-code-editor.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify editor resources and execute actual indicator test fixtures; verify resource validation, compile/qualification errors and fixture outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind extension import/export, compilation diagnostics and real indicator test outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-SERVLET-CODE-EDITOR-CODE-EDITOR-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-SERVLET-CODE-EDITOR-CODE-EDITOR-SERVLET-GET-INFO-SENDER-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet.getInfoSenderInstance()Lcom/strategyquant/plugin/Servlet/impl/CodeEditor/CodeEditorInfoSender;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-SERVLET-CODE-EDITOR-CODE-EDITOR-SERVLET-GET-FILE-MAP-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet.getFileMapInstance()Lcom/strategyquant/plugin/Servlet/impl/CodeEditor/FileMap;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_code_editor.py --no-cov`; expect resource validation, compile/qualification errors and fixture outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture resource validation, compile/qualification errors and fixture outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-servlet-code-editor.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Code Editor for FEAT-AUTHORING-SERVLET-CODE-EDITOR; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.13 FEAT-AUTHORING-SERVLET-STRATEGY - ServletStrategy.jar

## 1. Objective

- **Goal:** Expose Strategy commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Save, validate and execute authored strategies and generated platform code.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar`; 3 raw class entries; SHA-256 `ad58850406ffb2bcdf01773459b48bae65a95737a30d023f0442f7fb35bbb5e6`.
- **Inspected reference:** [ServletStrategy.md](sqx/Shared/ServletStrategy.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletStrategy/ServletStrategy.jar" com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/strategy/ServletStrategy/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy archive exchange, authoring and strategy wire contracts; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletStrategy`; `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard/index.html`.
- **Existing UI connection:** AlgoWizard; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/strategy/ServletStrategy/codec.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletStrategy/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletStrategy/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/strategy/ServletStrategy/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_authoring_servlet_strategy.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/authoring_servlet_strategy.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-authoring-servlet-strategy.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose Strategy commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-AUTHORING-SERVLET-STRATEGY-STRATEGY-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-AUTHORING-SERVLET-STRATEGY-STRATEGY-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet.getInstance()Lcom/strategyquant/plugin/Servlet/impl/Strategy/StrategyServlet;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-SERVLET-STRATEGY-STRATEGY-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Strategy.StrategyServlet.execute(Ljava/lang/String;Lorg/json/JSONObject;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_authoring_servlet_strategy.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-authoring-servlet-strategy.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for FEAT-AUTHORING-SERVLET-STRATEGY; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.14 FEAT-UI-PROJECT-RESOURCES - ProjectResources resource contribution

## 1. Objective

- **Goal:** Qualify and connect ProjectResources without assuming a missing backend JAR.
- **Context / Problem Solved:** ProjectResources is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectResources`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectResources/module.js`.
- **FR:** `FR-UI-PROJECT-RESOURCES-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/AlgoWizard/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectResources`; `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectResources/AddedResourcesPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectResources/ResolveCustomResourcesPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ProjectResources/ResolveResourcesPopupCtrl.js`.
- **Existing UI connection:** AlgoWizard; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/AlgoWizard/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_project_resources.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-project-resources.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-PROJECT-RESOURCES-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_project_resources.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Author a fixture strategy; save/reload/run it; test an indicator in CodeEditor; export each promised target and qualify its syntax. Inspect the ProjectResources contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-project-resources.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for FEAT-UI-PROJECT-RESOURCES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 7.15 FEAT-AUTHORING-SERVLET-ALGO-CLOUD - ServletAlgoCloud.jar

## 1. Objective

- **Goal:** Import approved AlgoCloud strategy/result documents through the authoring capability.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoCloud/ServletAlgoCloud.jar`; 2 raw class entries; SHA-256 `bd40d7d7d7f71c7e7553bbfb3e08f5b700038e8d98263d3ac5dc78a4d4fdc7b7`.
- **Inspected reference:** [ServletAlgoCloud.md](sqx/Plugins/ServletAlgoCloud.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoCloud/ServletAlgoCloud.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoCloud/ServletAlgoCloud.jar" com.strategyquant.plugin.Servlet.impl.AlgoCloud.AlgoCloudServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-AUTHORING-SERVLET-ALGO-CLOUD` and `FR-AUTHORING-SERVLET-ALGO-CLOUD-CONSUMED-CONTRACTS`; owner `app/plugins/authoring/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; trace actual import callers before choosing a retained consumer or approving an absent control.

## 3. File Changes

- **Create:** `app/plugins/authoring/algocloud.py` — Import approved AlgoCloud strategy/result documents through the authoring capability.
- **Create:** `app/plugins/authoring/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_authoring_servlet_algo_cloud.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-authoring_servlet_algo_cloud-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
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

- [ ] **Step 9:** `FR-AUTHORING-SERVLET-ALGO-CLOUD-ALGO-CLOUD-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.AlgoCloud.AlgoCloudServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-AUTHORING-SERVLET-ALGO-CLOUD-ALGO-CLOUD-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.AlgoCloud.AlgoCloudServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 11:** `FR-AUTHORING-SERVLET-ALGO-CLOUD-ALGO-CLOUD-SERVLET-ON-IMPORT` → `com.strategyquant.plugin.Servlet.impl.AlgoCloud.AlgoCloudServlet.onImport(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_authoring_servlet_algo_cloud.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 7.16 FEAT-AUTHORING-NINJATRADER-EXPORT - NinjaTrader8 native NinjaScript export

## 1. Objective

- **Goal:** Generate qualified native .cs strategies and expose export through the retained Results UI.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Code/NinjaTrader/Main.tpl`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/sourceCode/ninjaTrader/module.js`.
- **Ownership:** proposed `FEAT-AUTHORING-NINJATRADER-EXPORT` and `FR-AUTHORING-NINJATRADER-EXPORT-CONSUMED-CONTRACTS`; owner `app/plugins/authoring/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Native compiler/platform verification is unavailable until separately arranged; output generation alone is not parity.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSourceCode`, `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/sourceCode/ninjaTrader/module.js`; retained Results UI lacks the new save action.

## 3. File Changes

- **Create:** `app/plugins/authoring/ninjatrader.py` — Generate qualified native .cs strategies and expose export through the retained Results UI.
- **Create:** `app/plugins/authoring/ninjatrader_validation.py` — Generate qualified native .cs strategies and expose export through the retained Results UI.
- **Create:** `app/plugins/authoring/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_authoring_ninjatrader_export.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/plugins/project/ResultsSourceCode/SourceCodeCtrl.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/plugins/project/ResultsSourceCode/sourceCode.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/sourceCode/module.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-authoring_ninjatrader_export-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Inspect all templates and consumed helpers; pin package version, parameter/identifier escaping and unsupported blocks.
- [ ] **Step 3:** Preserve bar-close calculation and explicit on-tick rejection; do not silently weaken timing semantics.
- [ ] **Step 4:** Wire existing 7.9/Results source-code clients to the nt8 format with precise unsupported/error states.
- [ ] **Step 5:** Compile/import generated fixtures in an approved isolated NinjaTrader environment and compare independent traces.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_authoring_ninjatrader_export.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 7.17 FEAT-AUTHORING-NINJATRADER-INDICATORS - NinjaTrader indicator package and COT/profile adapters

## 1. Objective

- **Goal:** Package the required native indicators with explicit exported-strategy compatibility.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/custom_indicators/NinjaTrader/Indicators`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Code/NinjaTrader/Main.tpl`.
- **Ownership:** proposed `FEAT-AUTHORING-NINJATRADER-INDICATORS` and `FR-AUTHORING-NINJATRADER-INDICATORS-CONSUMED-CONTRACTS`; owner `app/plugins/authoring/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Do not copy donor C# bodies into evidence; native output adaptations need their own approved implementation scope.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/sourceCode/ninjaTrader/module.js`; connect native package artifacts through retained export controls.

## 3. File Changes

- **Create:** `app/plugins/authoring/ninjatrader_package.py` — Package the required native indicators with explicit exported-strategy compatibility.
- **Create:** `app/plugins/authoring/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_authoring_ninjatrader_indicators.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/plugins/project/ResultsSourceCode/SourceCodeCtrl.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/plugins/project/ResultsSourceCode/sourceCode.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/plugins/databank/ResultsDatabankActions/save/sourceCode/module.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-authoring_ninjatrader_indicators-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Enumerate native indicator/calculator dependencies and compare algorithms with donor Java/template implementations.
- [ ] **Step 3:** Bind export package metadata to the emitted package version; reject missing/unsupported output/session combinations.
- [ ] **Step 4:** Verify package completeness, version mismatch and independent native execution vectors.
- [ ] **Step 5:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 6:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_authoring_ninjatrader_indicators.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 7.18 P07 integration — Save, validate and execute authored strategies and generated platform code

## 1. Objective

- **Goal:** Save, validate and execute authored strategies and generated platform code.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P07; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`, `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard/index.html`.
- **Existing UI connection:** AlgoWizard; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/AlgoWizard/workspace.py` (proposed earlier in FEAT-AUTHORING-APP-WIZARD)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/AlgoWizard/service.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/AlgoWizard/routes.py` (proposed earlier in FEAT-AUTHORING-APP-WIZARD)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/CodeEditor/workspace.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/CodeEditor/routes.py` (proposed earlier in FEAT-AUTHORING-APP-CODE-EDITOR)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/archive.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/codec.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/repository.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/code_generation/templates.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/code_generation/emitters.py` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/extensions/qualification.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts` (proposed earlier in P05 integration)
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/CodeEditor/CodeEditorWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/CodeEditor/codeEditorClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/AlgoWizard/README.md` (proposed earlier in FEAT-AUTHORING-FREEMARKER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_authoring_code_generation_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-authoring-code-generation-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-7-18.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify SQ3/SQ4 round trips, editor lowering, resource versions and extension trust boundaries.
- [ ] **Step 3:** Implement strategy archives, resource qualification and evidence-backed generation templates.
- [ ] **Step 4:** Connect AlgoWizard and CodeEditor save/reload/run/export and genuine indicator testing.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_authoring_code_generation_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-authoring-code-generation-backend.spec.ts`. Assert author/save/reload/run semantics, archive preservation and target compilation; reject malformed archive, unresolved resource, extension rejection and template failure.
- **Manual / Browser Verification:** Author a fixture strategy; save/reload/run it; test an indicator in CodeEditor; export each promised target and qualify its syntax.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-7-18.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-authoring-code-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for 7.21; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
