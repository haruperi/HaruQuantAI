# P17 — Product shells, business, help, MCP and desktop/distribution completion

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P01,P02,P07,P08,P13,P14,P15,P16.
- **Scope:** 14 JAR feature tasks, 2 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 17.1 FEAT-PRODUCT-JFX-2-4-9-SQ - jfx_2.4.9_sq.jar

## 1. Objective

- **Goal:** Adapt consumed desktop/window/theme behavior to the existing React shell.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/jfx_2.4.9_sq.jar`; 261 class declarations; SHA-256 `b05ca416555206d0dc5282431cd690c088d6481cf07c1d4a24ec91737bd8b2d5`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PRODUCT-JFX-2-4-9-SQ`.
- **Owner:** `app/host/desktop/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Native Java desktop/webview support; retain React equivalent and audit residual OS behavior; downstream P01,P02,P07,P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/jfx_2.4.9_sq.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/jfx_2.4.9_sq.jar" com.jfx.ADXIndicatorLines`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds product shell through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/desktop/bridge.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/desktop/lifecycle.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/desktop/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_jfx_2_4_9_sq.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_jfx_2_4_9_sq.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed desktop/window/theme behavior to the existing React shell; verify startup/exit, window lifecycle, skin persistence and unsupported native behavior.
- [ ] **Step 4:** `FR-PRODUCT-JFX-2-4-9-SQ-ADX-INDICATOR-LINES-CONTRACT` → `com.jfx.ADXIndicatorLines`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-JFX-2-4-9-SQ-ADX-INDICATOR-LINES-GET-ADX-INDICATOR-LINES` → `com.jfx.ADXIndicatorLines.getADXIndicatorLines`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-JFX-2-4-9-SQ-ADX-INDICATOR-LINES-GET-VAL` → `com.jfx.ADXIndicatorLines.getVal`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_jfx_2_4_9_sq.py --no-cov`; expect startup/exit, window lifecycle, skin persistence and unsupported native behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup/exit, window lifecycle, skin persistence and unsupported native behavior and visible failures.

# 17.2 FEAT-PRODUCT-MCP-CORE - mcp-core.jar

## 1. Objective

- **Goal:** Expose typed MCP discovery and permitted tool execution through host capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/mcp-core.jar`; 301 class declarations; SHA-256 `f6eb396f98b5f8f1ef6d7bea1ce79c9914c6b99d8f10f918579c6fb8992ee9d7`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PRODUCT-MCP-CORE`.
- **Owner:** `app/plugins/mcp/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optional MCP server/schema/serialization integration; downstream P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/mcp-core.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/mcp-core.jar" io.modelcontextprotocol.client.LifecycleInitializer`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS`; `SQX_REFERENCE_ROOT/internal/plugins/ServletMCP`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS/index.html`.
- **Existing UI connection:** Business/MCP; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Business/BusinessWorkspace.tsx`; wire MCP configuration, capability lifecycle and bounded command outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/mcp/server.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/mcp/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/mcp/tools.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/mcp/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_mcp_core.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_mcp_core.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/ConfigureMcpModal.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Business/businessClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-product-mcp-core.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose typed MCP discovery and permitted tool execution through host capabilities; verify tool schema, authority, timeout, cancellation and unavailable capability.
- [ ] **Step 4:** `FR-PRODUCT-MCP-CORE-LIFECYCLE-INITIALIZER-CONTRACT` → `io.modelcontextprotocol.client.LifecycleInitializer`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-MCP-CORE-LIFECYCLE-INITIALIZER-IS-INITIALIZED` → `io.modelcontextprotocol.client.LifecycleInitializer.isInitialized`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-MCP-CORE-LIFECYCLE-INITIALIZER-CURRENT-INITIALIZATION-RESULT` → `io.modelcontextprotocol.client.LifecycleInitializer.currentInitializationResult`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_mcp_core.py --no-cov`; expect tool schema, authority, timeout, cancellation and unavailable capability; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture tool schema, authority, timeout, cancellation and unavailable capability and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-mcp-core.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Business/MCP for FEAT-PRODUCT-MCP-CORE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.3 FEAT-PRODUCT-MCP-JSON-JACKSON2 - mcp-json-jackson2.jar

## 1. Objective

- **Goal:** Encode and validate typed JSON documents without Java object coupling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/mcp-json-jackson2.jar`; 5 class declarations; SHA-256 `eda0173d9183e272576cc5581ae58ff437bdadd9e6d0c3410045f86e3de10c8a`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PRODUCT-MCP-JSON-JACKSON2`.
- **Owner:** `app/plugins/mcp/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optional MCP server/schema/serialization integration; downstream P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/mcp-json-jackson2.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/mcp-json-jackson2.jar" io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS`; `SQX_REFERENCE_ROOT/internal/plugins/ServletMCP`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS/index.html`.
- **Existing UI connection:** Business/MCP; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Business/BusinessWorkspace.tsx`; wire MCP configuration, capability lifecycle and bounded command outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/mcp/server.py` (proposed earlier in FEAT-PRODUCT-MCP-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/mcp/contracts.py` (proposed earlier in FEAT-PRODUCT-MCP-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/mcp/tools.py` (proposed earlier in FEAT-PRODUCT-MCP-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/mcp/README.md` (proposed earlier in FEAT-PRODUCT-MCP-CORE)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_mcp_json_jackson2.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_mcp_json_jackson2.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/ConfigureMcpModal.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Business/businessClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-product-mcp-json-jackson2.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Encode and validate typed JSON documents without Java object coupling; verify null/number handling, unknown fields and malformed payload.
- [ ] **Step 4:** `FR-PRODUCT-MCP-JSON-JACKSON2-JACKSON-MCP-JSON-MAPPER-CONTRACT` → `io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-MCP-JSON-JACKSON2-JACKSON-MCP-JSON-MAPPER-GET-OBJECT-MAPPER` → `io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper.getObjectMapper`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-MCP-JSON-JACKSON2-JACKSON-MCP-JSON-MAPPER-READ-VALUE` → `io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper.readValue`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_mcp_json_jackson2.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-mcp-json-jackson2.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Business/MCP for FEAT-PRODUCT-MCP-JSON-JACKSON2; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.4 FEAT-PRODUCT-SWINGX - swingx.jar

## 1. Objective

- **Goal:** Adapt consumed desktop/window/theme behavior to the existing React shell.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/swingx.jar`; 958 class declarations; SHA-256 `78d9b983a58e2e218e98414e2b25e3a6594bc6014a272ccd49f175dfd4af9a25`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PRODUCT-SWINGX`.
- **Owner:** `app/host/desktop/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Native Java desktop/webview support; retain React equivalent and audit residual OS behavior; downstream P01,P02,P07,P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/swingx.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/swingx.jar" org.jdesktop.beans.AbstractBean`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds product shell through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/desktop/bridge.py` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/desktop/lifecycle.py` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/desktop/README.md` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_swingx.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_swingx.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed desktop/window/theme behavior to the existing React shell; verify startup/exit, window lifecycle, skin persistence and unsupported native behavior.
- [ ] **Step 4:** `FR-PRODUCT-SWINGX-ABSTRACT-BEAN-CONTRACT` → `org.jdesktop.beans.AbstractBean`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-SWINGX-ABSTRACT-BEAN-ADD-PROPERTY-CHANGE-LISTENER` → `org.jdesktop.beans.AbstractBean.addPropertyChangeListener`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-SWINGX-ABSTRACT-BEAN-REMOVE-PROPERTY-CHANGE-LISTENER` → `org.jdesktop.beans.AbstractBean.removePropertyChangeListener`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_swingx.py --no-cov`; expect startup/exit, window lifecycle, skin persistence and unsupported native behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup/exit, window lifecycle, skin persistence and unsupported native behavior and visible failures.

# 17.5 FEAT-PRODUCT-WEBLAF - weblaf.jar

## 1. Objective

- **Goal:** Adapt consumed desktop/window/theme behavior to the existing React shell.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/weblaf.jar`; 1706 class declarations; SHA-256 `a9f586d858fb731c1301f18cc67535855247f66502de5ac56c506df1b3ac1e94`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-PRODUCT-WEBLAF`.
- **Owner:** `app/host/desktop/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Native Java desktop/webview support; retain React equivalent and audit residual OS behavior; downstream P01,P02,P07,P18.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/weblaf.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/weblaf.jar" com.alee.extended.breadcrumb.BreadcrumbElement`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds product shell through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/desktop/bridge.py` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/desktop/lifecycle.py` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/desktop/README.md` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_weblaf.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_weblaf.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Adapt consumed desktop/window/theme behavior to the existing React shell; verify startup/exit, window lifecycle, skin persistence and unsupported native behavior.
- [ ] **Step 4:** `FR-PRODUCT-WEBLAF-BREADCRUMB-ELEMENT-CONTRACT` → `com.alee.extended.breadcrumb.BreadcrumbElement`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-WEBLAF-BREADCRUMB-ELEMENT-SET-SHOW-PROGRESS` → `com.alee.extended.breadcrumb.BreadcrumbElement.setShowProgress`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-WEBLAF-BREADCRUMB-ELEMENT-IS-SHOW-PROGRESS` → `com.alee.extended.breadcrumb.BreadcrumbElement.isShowProgress`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_weblaf.py --no-cov`; expect startup/exit, window lifecycle, skin persistence and unsupported native behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup/exit, window lifecycle, skin persistence and unsupported native behavior and visible failures.

# 17.6 FEAT-PRODUCT-APP-HELP - AppHelp.jar

## 1. Objective

- **Goal:** Mount the Help workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppHelp/AppHelp.jar`; 0 class declarations; SHA-256 `a94608f3b7ba05e1b6f17a2c2fe45ab0e5f8ba435cc4f62c0c5e21ecb7a75ffa`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Resources/AppHelp.md`; roadmap allocation `FEAT-PRODUCT-APP-HELP`.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppHelp/AppHelp.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppHelp`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Home/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Home/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Home/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Home/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_help.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_help.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-help.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Help workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-HELP-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 8:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_help.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-help.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-HELP; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.7 FEAT-PRODUCT-APP-HOME - AppHome.jar

## 1. Objective

- **Goal:** Mount the Home workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppHome/AppHome.jar`; 0 class declarations; SHA-256 `d03a78caf34de8f78c5cda2649fea7728e6fdd59c7046c4680f1e40e498b499b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Resources/AppHome.md`; roadmap allocation `FEAT-PRODUCT-APP-HOME`.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppHome/AppHome.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppHome`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Home/workspace.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/contracts.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_home.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_home.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-home.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Home workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-HOME-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 8:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_home.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-home.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-HOME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.8 FEAT-PRODUCT-APP-PAYMENT-DIALOG - AppPaymentDialog.jar

## 1. Objective

- **Goal:** Mount the PaymentDialog workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppPaymentDialog/AppPaymentDialog.jar`; 0 class declarations; SHA-256 `a94608f3b7ba05e1b6f17a2c2fe45ab0e5f8ba435cc4f62c0c5e21ecb7a75ffa`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Resources/AppPaymentDialog.md`; roadmap allocation `FEAT-PRODUCT-APP-PAYMENT-DIALOG`.
- **Owner:** `app/workspace/Business/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppPaymentDialog/AppPaymentDialog.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppPaymentDialog`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** The shell has simulated license updates; a payment/checkout UI counterpart is not established. Keep unsupported payment capabilities unavailable; resolve scope before completion.

## 3. File Changes

- **Create:** `app/workspace/Business/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Business/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Business/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Business/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_payment_dialog.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_payment_dialog.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-payment-dialog.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the PaymentDialog workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-PAYMENT-DIALOG-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 8:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_payment_dialog.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-payment-dialog.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-PAYMENT-DIALOG; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.9 FEAT-PRODUCT-APP-QUANT-DATA-MANAGER - AppQuantDataManager.jar

## 1. Objective

- **Goal:** Mount the QuantDataManager workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppQuantDataManager/AppQuantDataManager.jar`; 3 class declarations; SHA-256 `234080d1be94dfc801ede5b8fe287a2142b1d152da4d4a18cad37a6f8fc4cad3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/ProductShells/AppQuantDataManager.md`; roadmap allocation `FEAT-PRODUCT-APP-QUANT-DATA-MANAGER`.
- **Owner:** `app/workspace/DataManager/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppQuantDataManager/AppQuantDataManager.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppQuantDataManager/AppQuantDataManager.jar" com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppQuantDataManager`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/web/QDM/layout/QDMService.js`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataService.js`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/DataManager/workspace.py` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/DataManager/routes.py` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/DataManager/contracts.py` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/DataManager/README.md` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_quant_data_manager.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_quant_data_manager.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-quant-data-manager.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the QuantDataManager workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-QUANT-DATA-MANAGER-QUANT-DATA-MANAGER-SERVLET-CONTRACT` → `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-APP-QUANT-DATA-MANAGER-QUANT-DATA-MANAGER-SERVLET-EXECUTE` → `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_quant_data_manager.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-quant-data-manager.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-PRODUCT-APP-QUANT-DATA-MANAGER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.10 FEAT-PRODUCT-APP-SQX-BUSINESS - AppSQXBusiness.jar

## 1. Objective

- **Goal:** Mount the SQXBusiness workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/AppSQXBusiness.jar`; 10 class declarations; SHA-256 `1629d659fc78cb2553b16103616b4fd321f12e5096f0c6f50ab18f8c4f0c2530`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/SQXBusiness/AppSQXBusiness.md`; roadmap allocation `FEAT-PRODUCT-APP-SQX-BUSINESS`.
- **Owner:** `app/workspace/Business/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/AppSQXBusiness.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/AppSQXBusiness.jar" com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppSQXBusiness`; `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS`; `SQX_REFERENCE_ROOT/internal/plugins/ServletMCP`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/module.js`.
- **Existing UI connection:** Business/MCP; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Business/BusinessWorkspace.tsx`; wire MCP configuration, capability lifecycle and bounded command outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Business/workspace.py` (proposed earlier in FEAT-PRODUCT-APP-PAYMENT-DIALOG)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Business/routes.py` (proposed earlier in FEAT-PRODUCT-APP-PAYMENT-DIALOG)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Business/contracts.py` (proposed earlier in FEAT-PRODUCT-APP-PAYMENT-DIALOG)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Business/README.md` (proposed earlier in FEAT-PRODUCT-APP-PAYMENT-DIALOG)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_sqx_business.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_sqx_business.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/ConfigureMcpModal.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Business/businessClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-sqx-business.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the SQXBusiness workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-SQX-BUSINESS-MQL-MARKET-BUILD-EXECUTOR-CONTRACT` → `com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-APP-SQX-BUSINESS-MQL-MARKET-BUILD-EXECUTOR-INIT` → `com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor.init`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-APP-SQX-BUSINESS-MQL-MARKET-BUILD-EXECUTOR-EXECUTE` → `com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_sqx_business.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-sqx-business.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Business/MCP for FEAT-PRODUCT-APP-SQX-BUSINESS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.11 FEAT-PRODUCT-APP-SQX-HOME - AppSQXHome.jar

## 1. Objective

- **Goal:** Mount the SQXHome workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome/AppSQXHome.jar`; 2 class declarations; SHA-256 `46d2b8e1068a9df0bacac2ff33c02c6b5e00d4edd58a1bf8d13df0e4c8d113ef`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/GettingStarted/AppSQXHome.md`; roadmap allocation `FEAT-PRODUCT-APP-SQX-HOME`.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome/AppSQXHome.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome/AppSQXHome.jar" com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome/offline/index.html`; `SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome/offline/offline/index.html`; `SQX_REFERENCE_ROOT/internal/plugins/AppSQXHome/module.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Home/workspace.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/contracts.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_sqx_home.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_sqx_home.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-sqx-home.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the SQXHome workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-SQX-HOME-SQX-HOME-SERVLET-CONTRACT` → `com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-APP-SQX-HOME-SQX-HOME-SERVLET-EXECUTE` → `com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_sqx_home.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-sqx-home.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-SQX-HOME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.12 FEAT-PRODUCT-APP-STRATEGY-QUANT - AppStrategyQuant.jar

## 1. Objective

- **Goal:** Mount the StrategyQuant workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant/AppStrategyQuant.jar`; 1 class declarations; SHA-256 `a103c73636b10f550ce969796703d910b3e4a0cc6df2b13c4d1045430d3ece6c`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/ProductShells/AppStrategyQuant.md`; roadmap allocation `FEAT-PRODUCT-APP-STRATEGY-QUANT`.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant/AppStrategyQuant.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant/AppStrategyQuant.jar" com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Home/workspace.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/contracts.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_app_strategy_quant.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_app_strategy_quant.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-product-app-strategy-quant.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the StrategyQuant workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-PRODUCT-APP-STRATEGY-QUANT-STRATEGY-QUANT-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-APP-STRATEGY-QUANT-STRATEGY-QUANT-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-APP-STRATEGY-QUANT-STRATEGY-QUANT-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_strategy_quant.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-strategy-quant.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-STRATEGY-QUANT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.13 FEAT-PRODUCT-HOME-ABOUT - HomeAbout.jar

## 1. Objective

- **Goal:** Deliver the consumed HomeAbout capability in host.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/HomeAbout/HomeAbout.jar`; 2 class declarations; SHA-256 `b874cd7ea9634c21fe493b37b508a5b1d64f288e8b6225b959a568f913c34c53`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/HomeAbout.md`; roadmap allocation `FEAT-PRODUCT-HOME-ABOUT`.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Product information or MCP integration; distinct ownership; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/HomeAbout/HomeAbout.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/HomeAbout/HomeAbout.jar" com.strategyquant.plugin.Home.impl.About.AboutServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/HomeAbout`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/HomeAbout/services/AboutService.js`; `SQX_REFERENCE_ROOT/internal/plugins/HomeAbout/AboutCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/HomeAbout/views/about.html`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Home/about.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_home_about.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_home_about.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-product-home-about.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Deliver the consumed HomeAbout capability in host; verify product navigation, theme/language reload, tool capability discovery and distribution launch.
- [ ] **Step 4:** `FR-PRODUCT-HOME-ABOUT-ABOUT-SERVLET-CONTRACT` → `com.strategyquant.plugin.Home.impl.About.AboutServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-HOME-ABOUT-ABOUT-SERVLET-EXECUTE` → `com.strategyquant.plugin.Home.impl.About.AboutServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_home_about.py --no-cov`; expect product navigation, theme/language reload, tool capability discovery and distribution launch; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture product navigation, theme/language reload, tool capability discovery and distribution launch and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-home-about.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-HOME-ABOUT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.14 FEAT-PRODUCT-SERVLET-MCP - ServletMCP.jar

## 1. Objective

- **Goal:** Expose typed MCP discovery and permitted tool execution through host capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletMCP/ServletMCP.jar`; 1 class declarations; SHA-256 `a61879f1a764312fa9d1614020a7538b38a2529cb2049f856b67add9689b1685`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletMCP.md`; roadmap allocation `FEAT-PRODUCT-SERVLET-MCP`.
- **Owner:** `app/plugins/mcp/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Product information or MCP integration; distinct ownership; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletMCP/ServletMCP.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletMCP/ServletMCP.jar" com.strategyquant.plugin.Servlet.impl.MCP.MCPPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ServletMCP`; `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXBUSINESS/index.html`.
- **Existing UI connection:** Business/MCP; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Business/BusinessWorkspace.tsx`; wire MCP configuration, capability lifecycle and bounded command outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/mcp/routes.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/mcp/contracts.py` (proposed earlier in FEAT-PRODUCT-MCP-CORE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/mcp/README.md` (proposed earlier in FEAT-PRODUCT-MCP-CORE)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_product_servlet_mcp.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/product_servlet_mcp.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/ConfigureMcpModal.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Business/fixtures.ts`
  - Keep fixtures explicit for tests/demo; production consumers read backend projections.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display MCP configuration, capability lifecycle and bounded command outcomes from backend responses; preserve layout.
- **Create:** `ui/app/workspace/Business/businessClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-product-servlet-mcp.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose typed MCP discovery and permitted tool execution through host capabilities; verify tool schema, authority, timeout, cancellation and unavailable capability.
- [ ] **Step 4:** `FR-PRODUCT-SERVLET-MCP-MCP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.MCP.MCPPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PRODUCT-SERVLET-MCP-MCP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Servlet.impl.MCP.MCPPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PRODUCT-SERVLET-MCP-MCP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Servlet.impl.MCP.MCPPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_servlet_mcp.py --no-cov`; expect tool schema, authority, timeout, cancellation and unavailable capability; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture tool schema, authority, timeout, cancellation and unavailable capability and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-servlet-mcp.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Business/MCP for FEAT-PRODUCT-SERVLET-MCP; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.15 FEAT-UI-SKIN-DARK - SkinDark resource contribution

## 1. Objective

- **Goal:** Qualify and connect SkinDark without assuming a missing backend JAR.
- **Context / Problem Solved:** SkinDark is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SkinDark`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/SkinDark/module.js`.
- **FR:** `FR-UI-SKIN-DARK-RESOURCE-WORKFLOW`; proposed owning README `app/host/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SkinDark`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SkinDark/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/SkinDark/dark.skin.css`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/host/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/host/README.md` (proposed earlier in P00)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_skin_dark.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-skin-dark.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-SKIN-DARK-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_skin_dark.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Launch a clean distribution; switch product/theme/language; inspect help/about; test MCP in an isolated authorized session. Inspect the SkinDark contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-skin-dark.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-UI-SKIN-DARK; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.16 FEAT-UI-SKIN-LIGHT - SkinLight resource contribution

## 1. Objective

- **Goal:** Qualify and connect SkinLight without assuming a missing backend JAR.
- **Context / Problem Solved:** SkinLight is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SkinLight`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/SkinLight/module.js`.
- **FR:** `FR-UI-SKIN-LIGHT-RESOURCE-WORKFLOW`; proposed owning README `app/host/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SkinLight`; `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SkinLight/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/SkinLight/light.skin.css`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/host/resource_contributions.py` (proposed earlier in FEAT-UI-SKIN-DARK)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/host/README.md` (proposed earlier in P00)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_skin_light.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-skin-light.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-SKIN-LIGHT-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_skin_light.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Launch a clean distribution; switch product/theme/language; inspect help/about; test MCP in an isolated authorized session. Inspect the SkinLight contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-skin-light.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-UI-SKIN-LIGHT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 17.17 P17 integration — Complete product shells, help, business/MCP capabilities and distributable startup

## 1. Objective

- **Goal:** Complete product shells, help, business/MCP capabilities and distributable startup.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P17; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Home/HomeScreen.tsx`, `ui/app/workspace/Business/BusinessWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** `ui/tests/unit/workspace/Business/business.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/HOME`; `SQX_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/host/desktop/bridge.py` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/desktop/lifecycle.py` (proposed earlier in FEAT-PRODUCT-JFX-2-4-9-SQ)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/product/catalog.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/host/mcp/server.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-PRODUCT-APP-HELP)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Business/routes.py` (proposed earlier in FEAT-PRODUCT-APP-PAYMENT-DIALOG)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Home/HomeScreen.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/Home/homeClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/Business/BusinessWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/Business/businessClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/host/README.md` (proposed earlier in P00)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_product_distribution_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-product-distribution-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/host/HeaderApplications.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/GlobalSettingsMenu.tsx`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Modify:** `ui/app/host/hostSettings.ts`
  - Display host product capability, startup/help availability and backend-owned shell settings from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-17-17.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Verify active product registrations, skins/help/about and licensed/vendor-owned availability.
- [ ] **Step 3:** Implement supported shell/preferences/desktop lifecycle and typed MCP/business capabilities.
- [ ] **Step 4:** Connect product controls and distribution startup; qualify optional/unavailable states explicitly.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_product_distribution_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Business/business.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-product-distribution-backend.spec.ts`. Assert product navigation, theme/language reload, tool capability discovery and distribution launch; reject unavailable entitlement/vendor service, rejected tool authority and missing desktop adapter.
- **Manual / Browser Verification:** Launch a clean distribution; switch product/theme/language; inspect help/about; test MCP in an isolated authorized session.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-17-17.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for 17.17; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
