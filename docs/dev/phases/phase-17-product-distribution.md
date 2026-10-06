# P17 — Product shells, business, help, MCP and desktop/distribution completion

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P01,P02,P07,P08,P13,P14,P15,P16.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 22 tasks; current archive allocations and resource/integration tasks only.

# 17.1 FEAT-PRODUCT-JFX-2-4-9-SQ - jfx_2.4.9_sq.jar

## 1. Objective

- **Goal:** Adapt consumed desktop/window/theme behavior to the existing React shell.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jfx_2.4.9_sq.jar`; 261 raw class entries; SHA-256 `b05ca416555206d0dc5282431cd690c088d6481cf07c1d4a24ec91737bd8b2d5`.
- **Inspected reference:** [jfx_2.4.9_sq.md](../../sqx/Libraries/jfx_2.4.9_sq.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jfx_2.4.9_sq.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jfx_2.4.9_sq.jar" com.jfx.ADXIndicatorLines`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/desktop/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Native Java desktop/webview support; retain React equivalent and audit residual OS behavior; downstream P01,P02,P07,P18.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-PRODUCT-JFX-2-4-9-SQ-ADXINDICATOR-LINES-CONTRACT` → `com.jfx.ADXIndicatorLines`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-PRODUCT-JFX-2-4-9-SQ-ADXINDICATOR-LINES-GET-ADXINDICATOR-LINES` → `com.jfx.ADXIndicatorLines.getADXIndicatorLines(I)Lcom/jfx/ADXIndicatorLines;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-JFX-2-4-9-SQ-ADXINDICATOR-LINES-GET-VAL` → `com.jfx.ADXIndicatorLines.getVal(I)I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_jfx_2_4_9_sq.py --no-cov`; expect startup/exit, window lifecycle, skin persistence and unsupported native behavior; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture startup/exit, window lifecycle, skin persistence and unsupported native behavior and visible failures.


# 17.2 FEAT-PRODUCT-MCP-CORE - mcp-core.jar

## 1. Objective

- **Goal:** Expose typed MCP discovery and permitted tool execution through host capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/mcp-core.jar`; 301 raw class entries; SHA-256 `f6eb396f98b5f8f1ef6d7bea1ce79c9914c6b99d8f10f918579c6fb8992ee9d7`.
- **Inspected reference:** [mcp-core.md](../../sqx/Libraries/mcp-core.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-core.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-core.jar" io.modelcontextprotocol.client.LifecycleInitializer`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/mcp/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optional MCP server/schema/serialization integration; downstream P18.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/SQXBUSINESS`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletMCP`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/SQXBUSINESS/index.html`.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PRODUCT-MCP-CORE-LIFECYCLE-INITIALIZER-CONTRACT` → `io.modelcontextprotocol.client.LifecycleInitializer`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-MCP-CORE-LIFECYCLE-INITIALIZER-SET-PROTOCOL-VERSIONS` → `io.modelcontextprotocol.client.LifecycleInitializer.setProtocolVersions(Ljava/util/List;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-MCP-CORE-LIFECYCLE-INITIALIZER-IS-INITIALIZED` → `io.modelcontextprotocol.client.LifecycleInitializer.isInitialized()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

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

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-jackson2.jar`; 5 raw class entries; SHA-256 `eda0173d9183e272576cc5581ae58ff437bdadd9e6d0c3410045f86e3de10c8a`.
- **Inspected reference:** [mcp-json-jackson2.md](../../sqx/Libraries/mcp-json-jackson2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-jackson2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-jackson2.jar" io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/mcp/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optional MCP server/schema/serialization integration; downstream P18.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/SQXBUSINESS`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletMCP`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/SQXBUSINESS/index.html`.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PRODUCT-MCP-JSON-JACKSON2-JACKSON-MCP-JSON-MAPPER-CONTRACT` → `io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-MCP-JSON-JACKSON2-JACKSON-MCP-JSON-MAPPER-GET-OBJECT-MAPPER` → `io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper.getObjectMapper()Lcom/fasterxml/jackson/databind/ObjectMapper;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-MCP-JSON-JACKSON2-JACKSON-MCP-JSON-MAPPER-READ-VALUE` → `io.modelcontextprotocol.json.jackson2.JacksonMcpJsonMapper.readValue(Ljava/lang/String;Ljava/lang/Class;)Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_mcp_json_jackson2.py --no-cov`; expect null/number handling, unknown fields and malformed payload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture null/number handling, unknown fields and malformed payload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-mcp-json-jackson2.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Business/MCP for FEAT-PRODUCT-MCP-JSON-JACKSON2; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 17.4 FEAT-PRODUCT-APP-SQX-BUSINESS - AppSQXBusiness.jar

## 1. Objective

- **Goal:** Mount the SQXBusiness workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/AppSQXBusiness.jar`; 10 raw class entries; SHA-256 `c5d8346793a02923de19a4dbe7d146e21772af3f2d8bb29460d636be16892373`.
- **Inspected reference:** [AppSQXBusiness.md](../../sqx/SQXBusiness/AppSQXBusiness.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/AppSQXBusiness.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/AppSQXBusiness.jar" com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Business/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXBusiness`; `SQX_145_REFERENCE_ROOT/internal/web/SQXBUSINESS`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletMCP`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXBusiness/module.js`.
- **Existing UI connection:** Business/MCP; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Business/BusinessWorkspace.tsx`; wire MCP configuration, capability lifecycle and bounded command outcomes.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Business/workspace.py` (proposed earlier in FEAT-UI-APP-PAYMENT-DIALOG)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Business/routes.py` (proposed earlier in FEAT-UI-APP-PAYMENT-DIALOG)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Business/contracts.py` (proposed earlier in FEAT-UI-APP-PAYMENT-DIALOG)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Business/README.md` (proposed earlier in FEAT-UI-APP-PAYMENT-DIALOG)
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind MCP configuration, capability lifecycle and bounded command outcomes to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PRODUCT-APP-SQX-BUSINESS-MQLMARKET-BUILD-EXECUTOR-CONTRACT` → `com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-APP-SQX-BUSINESS-MQLMARKET-BUILD-EXECUTOR-INIT` → `com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor.init()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-APP-SQX-BUSINESS-MQLMARKET-BUILD-EXECUTOR-EXECUTE` → `com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor.execute(Ljava/lang/String;Lorg/jdom2/Element;Ljava/lang/String;Ljava/lang/String;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_sqx_business.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-sqx-business.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Business/MCP for FEAT-PRODUCT-APP-SQX-BUSINESS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 17.5 FEAT-PRODUCT-APP-SQX-HOME - AppSQXHome.jar

## 1. Objective

- **Goal:** Mount the SQXHome workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome/AppSQXHome.jar`; 2 raw class entries; SHA-256 `5bedd8ddbf4c457a5f9512d721092fa1f79cb16ac9d302cec46a055fb6339f52`.
- **Inspected reference:** [AppSQXHome.md](../../sqx/GettingStarted/AppSQXHome.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome/AppSQXHome.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome/AppSQXHome.jar" com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome`; `SQX_145_REFERENCE_ROOT/internal/web/HOME`; `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome/offline/index.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome/offline/offline/index.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppSQXHome/module.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Home/workspace.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/contracts.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-UI-APP-HELP)
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PRODUCT-APP-SQX-HOME-SQXHOME-SERVLET-CONTRACT` → `com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-APP-SQX-HOME-SQXHOME-SERVLET-EXECUTE` → `com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_sqx_home.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-sqx-home.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-SQX-HOME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 17.6 FEAT-PRODUCT-APP-STRATEGY-QUANT - AppStrategyQuant.jar

## 1. Objective

- **Goal:** Mount the StrategyQuant workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant/AppStrategyQuant.jar`; 1 raw class entries; SHA-256 `f2b8b5c7c6c6ceb047228bf8d479ce7420985f8e5832ba5332f8bf613bde3a01`.
- **Inspected reference:** [AppStrategyQuant.md](../../sqx/ProductShells/AppStrategyQuant.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant/AppStrategyQuant.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant/AppStrategyQuant.jar" com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`; `SQX_145_REFERENCE_ROOT/internal/web/HOME`; `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Home/workspace.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/contracts.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-UI-APP-HELP)
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PRODUCT-APP-STRATEGY-QUANT-STRATEGY-QUANT-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-APP-STRATEGY-QUANT-STRATEGY-QUANT-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-APP-STRATEGY-QUANT-STRATEGY-QUANT-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.StrategyQuant.StrategyQuantAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_app_strategy_quant.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-app-strategy-quant.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-APP-STRATEGY-QUANT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 17.7 FEAT-PRODUCT-HOME-ABOUT - HomeAbout.jar

## 1. Objective

- **Goal:** Deliver the consumed HomeAbout capability in host.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Complete product shells, help, business/MCP capabilities and distributable startup.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout/HomeAbout.jar`; 2 raw class entries; SHA-256 `950092f1f3abff3ca23295d9fccd464a05d3d4605d8b9d1c1162d03e8ad1b5bd`.
- **Inspected reference:** [HomeAbout.md](../../sqx/Shared/HomeAbout.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout/HomeAbout.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout/HomeAbout.jar" com.strategyquant.plugin.Home.impl.About.AboutServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Home/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Product information or MCP integration; distinct ownership; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout`; `SQX_145_REFERENCE_ROOT/internal/web/HOME`; `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout/services/AboutService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout/AboutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/HomeAbout/views/about.html`.
- **Existing UI connection:** product shell; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Home/HomeScreen.tsx`; wire host product capability, startup/help availability and backend-owned shell settings.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Home/about.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Home/README.md` (proposed earlier in FEAT-UI-APP-HELP)
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind host product capability, startup/help availability and backend-owned shell settings to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PRODUCT-HOME-ABOUT-ABOUT-SERVLET-CONTRACT` → `com.strategyquant.plugin.Home.impl.About.AboutServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-HOME-ABOUT-ABOUT-SERVLET-EXECUTE` → `com.strategyquant.plugin.Home.impl.About.AboutServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-HOME-ABOUT-ABOUT-SERVLET-ON-UPDATE-LICENSE` → `com.strategyquant.plugin.Home.impl.About.AboutServlet.onUpdateLicense(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_product_home_about.py --no-cov`; expect product navigation, theme/language reload, tool capability discovery and distribution launch; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture product navigation, theme/language reload, tool capability discovery and distribution launch and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-product-home-about.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for FEAT-PRODUCT-HOME-ABOUT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 17.8 FEAT-UI-SKIN-DARK - SkinDark resource contribution

## 1. Objective

- **Goal:** Qualify and connect SkinDark without assuming a missing backend JAR.
- **Context / Problem Solved:** SkinDark is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SkinDark`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/SkinDark/module.js`.
- **FR:** `FR-UI-SKIN-DARK-RESOURCE-WORKFLOW`; proposed owning README `app/host/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SkinDark`; `SQX_145_REFERENCE_ROOT/internal/web/HOME`; `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SkinDark/module.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SkinDark/dark.skin.css`.
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


# 17.9 FEAT-UI-SKIN-LIGHT - SkinLight resource contribution

## 1. Objective

- **Goal:** Qualify and connect SkinLight without assuming a missing backend JAR.
- **Context / Problem Solved:** SkinLight is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SkinLight`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/SkinLight/module.js`.
- **FR:** `FR-UI-SKIN-LIGHT-RESOURCE-WORKFLOW`; proposed owning README `app/host/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SkinLight`; `SQX_145_REFERENCE_ROOT/internal/web/HOME`; `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SkinLight/module.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SkinLight/light.skin.css`.
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


# 17.10 FEAT-PRODUCT-FILTERS - filters-2.0.235.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/filters-2.0.235.jar`; 241 raw class entries; SHA-256 `be6a1d54ebb043495e31e25e72b440f69156a5624cdd7e1c55c47e30d4fae308`.
- **Inspected reference:** [filters-2.0.235.md](../../sqx/Libraries/filters-2.0.235.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/filters-2.0.235.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/filters-2.0.235.jar" com.jhlabs.composite.AddComposite`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-FILTERS` and `FR-PRODUCT-FILTERS-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_filters.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-FILTERS-ADD-COMPOSITE-CONTRACT` → `com.jhlabs.composite.AddComposite`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-FILTERS-ADD-COMPOSITE-CREATE-CONTEXT` → `com.jhlabs.composite.AddComposite.createContext(Ljava/awt/image/ColorModel;Ljava/awt/image/ColorModel;Ljava/awt/RenderingHints;)Ljava/awt/CompositeContext;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_filters.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.11 FEAT-HOST-JPOWERSHELL - jPowerShell-3.0.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jPowerShell-3.0.jar`; 8 raw class entries; SHA-256 `706451f6a1ff22cf477957bb280593d81d1a975263c3ff2ba1bab15b749a6168`.
- **Inspected reference:** [jPowerShell-3.0.md](../../sqx/Libraries/jPowerShell-3.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jPowerShell-3.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jPowerShell-3.0.jar" com.profesorfalken.jpowershell.OSDetector`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JPOWERSHELL` and `FR-HOST-JPOWERSHELL-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jpowershell.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JPOWERSHELL-OSDETECTOR-CONTRACT` → `com.profesorfalken.jpowershell.OSDetector`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JPOWERSHELL-OSDETECTOR-IS-WINDOWS` → `com.profesorfalken.jpowershell.OSDetector.isWindows()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JPOWERSHELL-OSDETECTOR-IS-MAC` → `com.profesorfalken.jpowershell.OSDetector.isMac()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jpowershell.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.12 FEAT-PRODUCT-JCOMMON - jcommon-1.0.12.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jcommon-1.0.12.jar`; 208 raw class entries; SHA-256 `34dd367ad34ae0baa5d5430fc9a13db1d12d66e29477cbb453ca92f5084a4e7b`.
- **Inspected reference:** [jcommon-1.0.12.md](../../sqx/Libraries/jcommon-1.0.12.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jcommon-1.0.12.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jcommon-1.0.12.jar" com.keypoint.PngEncoder`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-JCOMMON` and `FR-PRODUCT-JCOMMON-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_jcommon.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-JCOMMON-PNG-ENCODER-CONTRACT` → `com.keypoint.PngEncoder`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-JCOMMON-PNG-ENCODER-SET-IMAGE` → `com.keypoint.PngEncoder.setImage(Ljava/awt/Image;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-JCOMMON-PNG-ENCODER-GET-IMAGE` → `com.keypoint.PngEncoder.getImage()Ljava/awt/Image;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_jcommon.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.13 FEAT-PRODUCT-JFREECHART - jfreechart-1.0.8a.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jfreechart-1.0.8a.jar`; 562 raw class entries; SHA-256 `ca4266fb63ebbc0523a1ff413a0c0fc09e7d4822386ff1b6834e69eff748521d`.
- **Inspected reference:** [jfreechart-1.0.8a.md](../../sqx/Libraries/jfreechart-1.0.8a.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jfreechart-1.0.8a.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jfreechart-1.0.8a.jar" org.jfree.chart.ChartColor`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-JFREECHART` and `FR-PRODUCT-JFREECHART-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_jfreechart.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-JFREECHART-CHART-COLOR-CONTRACT` → `org.jfree.chart.ChartColor`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-JFREECHART-CHART-COLOR-CREATE-DEFAULT-PAINT-ARRAY` → `org.jfree.chart.ChartColor.createDefaultPaintArray()[Ljava/awt/Paint;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_jfreechart.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.14 FEAT-HOST-JLINE - jline-3.25.1.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/jline-3.25.1.jar`; 489 raw class entries; SHA-256 `421efcde9db04c34b9c03cd66e0460e75e5cdd4a3cafde54ef370049ac092e7c`.
- **Inspected reference:** [jline-3.25.1.md](../../sqx/Libraries/jline-3.25.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/jline-3.25.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/jline-3.25.1.jar" org.jline.builtins.Commands`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-HOST-JLINE` and `FR-HOST-JLINE-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_host_jline.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-HOST-JLINE-COMMANDS-CONTRACT` → `org.jline.builtins.Commands`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-HOST-JLINE-COMMANDS-TMUX` → `org.jline.builtins.Commands.tmux(Lorg/jline/terminal/Terminal;Ljava/io/PrintStream;Ljava/io/PrintStream;Ljava/util/function/Supplier;Ljava/util/function/Consumer;Ljava/util/function/Consumer;[Ljava/lang/String;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-HOST-JLINE-COMMANDS-NANO` → `org.jline.builtins.Commands.nano(Lorg/jline/terminal/Terminal;Ljava/io/PrintStream;Ljava/io/PrintStream;Ljava/nio/file/Path;[Ljava/lang/String;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_host_jline.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.15 FEAT-PRODUCT-MCP-CORE-145 - mcp-core-0.17.2.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/mcp-core-0.17.2.jar`; 292 raw class entries; SHA-256 `2489902b00d9cfb77a9ec991adf5c3387da298a4154f526dc63cda9c187891ff`.
- **Inspected reference:** [mcp-core-0.17.2.md](../../sqx/Libraries/mcp-core-0.17.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-core-0.17.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-core-0.17.2.jar" io.modelcontextprotocol.spec.ClosedMcpTransportSession`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-MCP-CORE-145` and `FR-PRODUCT-MCP-CORE-145-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_mcp_core_145.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-MCP-CORE-145-CLOSED-MCP-TRANSPORT-SESSION-CONTRACT` → `io.modelcontextprotocol.spec.ClosedMcpTransportSession`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-MCP-CORE-145-CLOSED-MCP-TRANSPORT-SESSION-SESSION-ID` → `io.modelcontextprotocol.spec.ClosedMcpTransportSession.sessionId()Ljava/util/Optional;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-MCP-CORE-145-CLOSED-MCP-TRANSPORT-SESSION-MARK-INITIALIZED` → `io.modelcontextprotocol.spec.ClosedMcpTransportSession.markInitialized(Ljava/lang/String;)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_mcp_core_145.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.16 FEAT-PRODUCT-MCP-JSON-JACKSON2-145 - mcp-json-jackson2-0.17.2.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-jackson2-0.17.2.jar`; 5 raw class entries; SHA-256 `dbe542c16244de30872ce5edcf1795ef4101acd4ac400e8c8081b0048feac0a7`.
- **Inspected reference:** [mcp-json-jackson2-0.17.2.md](../../sqx/Libraries/mcp-json-jackson2-0.17.2.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-jackson2-0.17.2.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/mcp-json-jackson2-0.17.2.jar" io.modelcontextprotocol.json.schema.jackson.JacksonJsonSchemaValidatorSupplier`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-MCP-JSON-JACKSON2-145` and `FR-PRODUCT-MCP-JSON-JACKSON2-145-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_mcp_json_jackson2_145.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-MCP-JSON-JACKSON2-145-JACKSON-JSON-SCHEMA-VALIDATOR-SUPPLIER-CONTRACT` → `io.modelcontextprotocol.json.schema.jackson.JacksonJsonSchemaValidatorSupplier`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-MCP-JSON-JACKSON2-145-JACKSON-JSON-SCHEMA-VALIDATOR-SUPPLIER-GET` → `io.modelcontextprotocol.json.schema.jackson.JacksonJsonSchemaValidatorSupplier.get()Lio/modelcontextprotocol/json/schema/JsonSchemaValidator;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_mcp_json_jackson2_145.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.17 FEAT-PRODUCT-RSYNTAXTEXTAREA - rsyntaxtextarea-2.6.0.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/rsyntaxtextarea-2.6.0.jar`; 341 raw class entries; SHA-256 `7f6ed5d5c81976840265337a0a8fca674af1135d72c70992b8e9e6c4dc301995`.
- **Inspected reference:** [rsyntaxtextarea-2.6.0.md](../../sqx/Libraries/rsyntaxtextarea-2.6.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/rsyntaxtextarea-2.6.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/rsyntaxtextarea-2.6.0.jar" org.fife.io.DocumentReader`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-RSYNTAXTEXTAREA` and `FR-PRODUCT-RSYNTAXTEXTAREA-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_rsyntaxtextarea.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-RSYNTAXTEXTAREA-DOCUMENT-READER-CONTRACT` → `org.fife.io.DocumentReader`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-RSYNTAXTEXTAREA-DOCUMENT-READER-CLOSE` → `org.fife.io.DocumentReader.close()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-RSYNTAXTEXTAREA-DOCUMENT-READER-MARK` → `org.fife.io.DocumentReader.mark(I)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_rsyntaxtextarea.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.18 FEAT-PRODUCT-SVG-SALAMANDER - svg-salamander-1.0.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/svg-salamander-1.0.jar`; 190 raw class entries; SHA-256 `c1ca16f6d892b6267b0b7cd9b8bac0ac6b3c71e99415ab6688bb354ca1c7f7b9`.
- **Inspected reference:** [svg-salamander-1.0.md](../../sqx/Libraries/svg-salamander-1.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/svg-salamander-1.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/svg-salamander-1.0.jar" com.kitfox.svg.A`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-SVG-SALAMANDER` and `FR-PRODUCT-SVG-SALAMANDER-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_svg_salamander.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-SVG-SALAMANDER-A-CONTRACT` → `com.kitfox.svg.A`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-SVG-SALAMANDER-A-BUILD` → `com.kitfox.svg.A.build()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-SVG-SALAMANDER-A-UPDATE-TIME` → `com.kitfox.svg.A.updateTime(D)Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_svg_salamander.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.19 FEAT-PRODUCT-WEBLAF-CORE - weblaf-core-1.2.9.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/weblaf-core-1.2.9.jar`; 340 raw class entries; SHA-256 `4628977369f5510bffdbec811866241e3e218893386c34610e3a21bf93adb99f`.
- **Inspected reference:** [weblaf-core-1.2.9.md](../../sqx/Libraries/weblaf-core-1.2.9.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/weblaf-core-1.2.9.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/weblaf-core-1.2.9.jar" com.alee.managers.language.LM`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-WEBLAF-CORE` and `FR-PRODUCT-WEBLAF-CORE-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_weblaf_core.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-WEBLAF-CORE-LM-CONTRACT` → `com.alee.managers.language.LM`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-WEBLAF-CORE-LM-GET-LANGUAGE-SUPPLIER` → `com.alee.managers.language.LM.getLanguageSupplier()Lcom/alee/api/jdk/Supplier;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-WEBLAF-CORE-LM-SET-LANGUAGE-SUPPLIER` → `com.alee.managers.language.LM.setLanguageSupplier(Lcom/alee/api/jdk/Supplier;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_weblaf_core.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.20 FEAT-PRODUCT-WEBLAF-UI - weblaf-ui-1.2.9.jar

## 1. Objective

- **Goal:** Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/weblaf-ui-1.2.9.jar`; 2444 raw class entries; SHA-256 `ab416d026e7d496fac337c9087bc11fb0346f9372c40b4493962551abe52b730`.
- **Inspected reference:** [weblaf-ui-1.2.9.md](../../sqx/Libraries/weblaf-ui-1.2.9.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/weblaf-ui-1.2.9.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/weblaf-ui-1.2.9.jar" com.alee.managers.drag.view.ComponentDragViewHandler`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-WEBLAF-UI` and `FR-PRODUCT-WEBLAF-UI-CONSUMED-CONTRACTS`; owner `app/workspace/Business/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** No standalone UI contribution is established for this infrastructure archive; trace its consuming host/domain feature and connect there.

## 3. File Changes

- **Create:** `app/workspace/Business/vendor_contracts.py` — Resolve the consumed product/plugin contract; classify JVM presentation internals explicitly.
- **Create:** `app/workspace/Business/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_weblaf_ui.py` — donor-derived normal, boundary, failure and FR-log checks.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Fingerprint the selected cohort; enumerate classes, methods and actual consumers.
- [ ] **Step 3:** Inspect consumed bodies and record normal/boundary/error contracts as descriptive FRs.
- [ ] **Step 4:** Ratify ownership and a reuse/adaptation/JVM-only disposition; implement only retained behavior.
- [ ] **Step 5:** Verify fixtures, invalid inputs, lifecycle/cancellation where applicable and explicit FR logs.
- [ ] **Step 6:** Expose the typed capability to its existing host/domain consumers; no standalone UI is established for this infrastructure JAR.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

- [ ] **Step 8:** `FR-PRODUCT-WEBLAF-UI-COMPONENT-DRAG-VIEW-HANDLER-CONTRACT` → `com.alee.managers.drag.view.ComponentDragViewHandler`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PRODUCT-WEBLAF-UI-COMPONENT-DRAG-VIEW-HANDLER-GET-VIEW` → `com.alee.managers.drag.view.ComponentDragViewHandler.getView(Ljava/lang/Object;Ljava/awt/dnd/DragSourceDragEvent;)Ljava/awt/image/BufferedImage;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-WEBLAF-UI-COMPONENT-DRAG-VIEW-HANDLER-CALCULATE-VIEW-RELATIVE-LOCATION` → `com.alee.managers.drag.view.ComponentDragViewHandler.calculateViewRelativeLocation(Ljavax/swing/JComponent;Ljava/awt/dnd/DragSourceDragEvent;)Ljava/awt/Point;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_weblaf_ui.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs.
- **Manual / Browser Verification:** Inspect consumer logs, lifecycle/failure outcomes and the declared infrastructure/JVM-only disposition.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.21 FEAT-PRODUCT-APP-MARKETPLACE - AppMarketplace.jar

## 1. Objective

- **Goal:** Install/remove approved extension resources with checksum, containment and lifecycle evidence.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppMarketplace/AppMarketplace.jar`; 8 raw class entries; SHA-256 `ba60e1e5c65eca7809dc9bc43c16e64c88280e41e434a90246176b5fcfef747c`.
- **Inspected reference:** [AppMarketplace.md](../../sqx/Plugins/AppMarketplace.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppMarketplace/AppMarketplace.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppMarketplace/AppMarketplace.jar" com.strategyquant.plugin.App.impl.Marketplace.MarketplaceDb`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Ownership:** proposed `FEAT-PRODUCT-APP-MARKETPLACE` and `FR-PRODUCT-APP-MARKETPLACE-CONSUMED-CONTRACTS`; owner `app/workspace/Marketplace/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/MARKETPLACE`, `SQX_145_REFERENCE_ROOT/internal/plugins/AppMarketplace`; target Marketplace controls are absent and proposed explicitly.

## 3. File Changes

- **Create:** `app/workspace/Marketplace/service.py` — Install/remove approved extension resources with checksum, containment and lifecycle evidence.
- **Create:** `app/workspace/Marketplace/contracts.py` — Install/remove approved extension resources with checksum, containment and lifecycle evidence.
- **Create:** `app/workspace/Marketplace/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_product_app_marketplace.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Create:** `ui/app/workspace/Marketplace/MarketplaceWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/app/workspace/Marketplace/marketplaceClient.ts` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-product_app_marketplace-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
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

- [ ] **Step 9:** `FR-PRODUCT-APP-MARKETPLACE-MARKETPLACE-DB-CONTRACT` → `com.strategyquant.plugin.App.impl.Marketplace.MarketplaceDb`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PRODUCT-APP-MARKETPLACE-MARKETPLACE-DB-GET` → `com.strategyquant.plugin.App.impl.Marketplace.MarketplaceDb.get()Lcom/strategyquant/plugin/App/impl/Marketplace/MarketplaceDb;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 11:** `FR-PRODUCT-APP-MARKETPLACE-MARKETPLACE-DB-INIT-DATABASE` → `com.strategyquant.plugin.App.impl.Marketplace.MarketplaceDb.initDatabase()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_product_app_marketplace.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 17.22 P17 integration — Complete product shells, help, business/MCP capabilities and distributable startup

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

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/HOME`; `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppStrategyQuant`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/SQXHOME/layout/SQXHomeService.js`.
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
- **Modify:** `app/workspace/Home/routes.py` (proposed earlier in FEAT-UI-APP-HELP)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Business/routes.py` (proposed earlier in FEAT-UI-APP-PAYMENT-DIALOG)
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
- **Create:** `ui/tests/unit/backend-connections/task-17-22.test.ts`
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

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-17-22.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-product-distribution-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise product shell for 17.29; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
