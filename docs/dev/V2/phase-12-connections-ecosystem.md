# Phase 12 — Connections and ecosystem

**Feature group:** F12. **Tasks:** 5. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Connect terminal/test surfaces with owned read-only lifecycle and mappings. This phase owns the connections and ecosystem capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** H05/H08/H10 and selected F02/F03/F04/F09 consumers. Each external adapter needs bounded lifecycle and qualification.

**Delivery:** M08. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/gateway`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P16](../V1/phase-16-connections-trading.md), [V1 P17](../V1/phase-17-product-distribution.md), [V1 P07](../V1/phase-07-authoring-code-generation.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Terminals | 12.1 | Test/live-test/MT4; symbols/accounts/order/status, reconnect/timeouts and MT5 data boundary |
| Live operations | 12.2 | Default disabled; distinct owner/account/action authority, ambiguous-outcome reconciliation and Trading target-added surfaces |
| Business/MCP | 12.3 | Tools/nodes/configuration/lifecycle, actual schemas/version negotiation, build/export workflows and entitlements |
| AlgoCloud | 12.4 | Available service, strategy/result access, document versions and authorization |
| Marketplace | 12.5 | Catalog/stage/install/disable/remove/upgrade, manifest/checksum/contained entries, rollback and retained data; missing UI needs explicit scope |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F12 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/Trading/TradingDashboard.tsx](../../../ui/app/workspace/Trading/TradingDashboard.tsx), [ui/app/workspace/Business/BusinessWorkspace.tsx](../../../ui/app/workspace/Business/BusinessWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 12.1 Terminal lifecycle and read-only/test connections

## 1. Objective

Connect terminal/test surfaces with owned read-only lifecycle and mappings.

## 2. Research and donors

P16 all Connection/DataManagerConnections/ServletConnection donors and MT5 data boundary.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/gateway/terminals.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_12/test_terminals.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover test/live-test/MT4 handshakes, protocol versions, symbols/accounts and read-only order/status projections; separate MT5 data semantics into F02.
- [ ] **Step 2:** Implement bounded connect/disconnect/reconnect with explicit credential/version/unavailable states.
- [ ] **Step 3:** Wire Connections/Trading views to actual adapter state and release subscriptions on removal.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_12/test_terminals.py --no-cov`.

**Independent cases:** Isolated test/sandbox handshakes, mapping conflicts, timeout/reconnect, stale snapshots, denied credentials and distinguish test from real terminal operation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 12.2 Separately authorized live operations and trading surfaces

## 1. Objective

Provide live-operation capability only under distinct explicit trading authority.

## 2. Research and donors

P16 authorized trading boundary and retained Trading target-added controls; do not infer donor parity from target UI.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/gateway/trading_authority.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_12/test_trading_authority.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify accepted order/amend/cancel commands, account limits, idempotency and irreversibility before activation.
- [ ] **Step 2:** Keep live trading disabled by default; require separate owner qualification and exact account/action authorization.
- [ ] **Step 3:** Reconcile acknowledgements, fills, reconnect ambiguity and external outcomes; never blindly retry uncertain orders.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_12/test_trading_authority.py --no-cov`.

**Independent cases:** Sandbox denied/allowed authority, duplicate submission, timeout after send, partial fill and reconnect reconciliation; ordinary implementation approval never permits real orders.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 12.3 Business/MCP tools, nodes and lifecycle

## 1. Objective

Expose Business/MCP tools and node lifecycle through one qualified protocol adapter.

## 2. Research and donors

P02 MCP boundary and P17 Business/MCP resources; no duplicate adapter for each Java wrapper version.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/gateway/mcp.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/gateway/business.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_12/test_mcp.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover actual tool/node configurations, schemas, protocol/version negotiation and Business build workflows.
- [ ] **Step 2:** Adapt qualified tools to existing jobs/export/project operations with bounded lifecycle, timeouts/rates and permission checks.
- [ ] **Step 3:** Keep node-specific behavior locally owned; separate credits/licenses/entitlements from generic protocol support.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_12/test_mcp.py --no-cov`.

**Independent cases:** Independent schema/negotiation fixtures and isolated tool/node connect-call-disable journey; denied tools, malformed payload, node loss and rate/time bounds.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 12.4 AlgoCloud resources and compatibility

## 1. Objective

Access AlgoCloud strategy/results through a narrow compatible external adapter.

## 2. Research and donors

P07 ServletAlgoCloud; document parser ownership remains F03.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/gateway/algocloud.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_12/test_algocloud.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify available API/service, account entitlements, pagination, document versions and error behavior.
- [ ] **Step 2:** Retrieve/publish only explicitly authorized operations with bounded retry/rate/redaction policies.
- [ ] **Step 3:** Hand parsed strategies to F03 and results to F05; preserve remote/document lineage and cache compatibility.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_12/test_algocloud.py --no-cov`.

**Independent cases:** Version/entitlement failure, malformed documents, timeout/partial pagination and isolated connected resource round trip; no invented unavailable vendor service.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 12.5 Marketplace package lifecycle and ecosystem qualification

## 1. Objective

Stage, install and remove compatible Marketplace packages safely.

## 2. Research and donors

P17 AppMarketplace and H05 package lifecycle; no license-system emulator.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/gateway/marketplace.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/gateway/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_12/test_marketplace.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define catalog/package version/manifest, checksum/signature policy, contained entries and compatibility/entitlement requirements.
- [ ] **Step 2:** Stage and validate before H05 attachment; implement controlled install/disable/remove/upgrade rollback preserving retained data.
- [ ] **Step 3:** Propose missing Marketplace controls explicitly and qualify the ecosystem matrix per adapter; inspection must not execute packages.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_12/test_marketplace.py --no-cov`.

**Independent cases:** Checksum/traversal/incompatible dependency, failed upgrade rollback, remove-with-dependents and retained-data checks; isolated connected Marketplace lifecycle.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 5 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
