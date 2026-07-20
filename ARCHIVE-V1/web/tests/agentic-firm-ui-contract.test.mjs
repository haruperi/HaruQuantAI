import assert from "node:assert/strict"
import { readFileSync, existsSync } from "node:fs"
import { join } from "node:path"
import { test } from "node:test"

const root = process.cwd()
const read = (path) => readFileSync(join(root, path), "utf8")

const pageRoutes = [
  "ai-ceo",
  "agents",
  "research",
  "strategy-lab",
  "backtests",
  "risk-center",
  "portfolio",
  "execution",
  "board-room",
  "audit",
  "costs",
  "settings",
]

test("agentic firm pages exist and operator UI is not present", () => {
  for (const route of pageRoutes) {
    assert.equal(existsSync(join(root, `src/app/(dashboard)/${route}/page.tsx`)), true, `${route} page exists`)
  }

  assert.equal(existsSync(join(root, "src/app/(dashboard)/operator")), false)
  assert.equal(existsSync(join(root, "src/components/operator")), false)
  assert.equal(existsSync(join(root, "src/app/api/operator")), false)
})

test("agentic firm routes use the client-backed workspace shell", () => {
  const routePages = {
    agents: "agents",
    research: "research",
    "strategy-lab": "strategy-lab",
    backtests: "backtests",
    "risk-center": "risk-center",
    portfolio: "portfolio",
    execution: "execution",
    "board-room": "board-room",
    audit: "audit",
    costs: "costs",
    settings: "settings",
  }

  for (const [route, pageKey] of Object.entries(routePages)) {
    const source = read(`src/app/(dashboard)/${route}/page.tsx`)
    assert.match(source, /BackendWorkspacePage/)
    assert.match(source, new RegExp(`page="${pageKey}"`))
  }
})

test("client-backed workspace maps each page to backend clients and avoids seeded fallbacks", () => {
  const source = read("src/components/agentic-firm/backend-workspace-page.tsx")
  for (const expected of [
    "workflowClient.listWorkflows",
    "researchClient.listReports",
    "researchClient.listHypotheses",
    "strategyClient.listStrategies",
    "backtestClient.listBacktests",
    "riskClient.getOverview",
    "riskClient.listBlocks",
    "riskClient.listApprovals",
    "riskClient.getKillSwitch",
    "portfolioClient.getOverview",
    "portfolioClient.listAllocations",
    "portfolioClient.getLifecycle",
    "portfolioClient.listRecommendations",
    "executionClient.getReadiness",
    "executionClient.getBrokerHealth",
    "executionClient.listOrders",
    "executionClient.listIncidents",
    "boardClient.listApprovalQueue",
    "auditClient.listAuditEvents",
    "costClient.getSummary",
    "costClient.listByAgent",
    "costClient.listByWorkflow",
    "settingsClient.getAgenticFirmSnapshot",
    "Seeded placeholder values are no longer shown here",
    "No backend records returned",
  ]) {
    assert.match(source, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }
})

test("CEO workspace exposes memo, planner, evidence, blocked actions, and trace metadata", () => {
  const source = read("src/components/ai-ceo/ceo-workspace.tsx")
  for (const expected of [
    "Final CEO Memo",
    "Planner Trace",
    "Planner-selected Departments",
    "Specialists Routed Through CEO",
    "Expected Outputs",
    "Evidence Requirements",
    "Evidence References",
    "Approval Request",
    "Blocked Actions",
    "Trace ID",
    "Request ID",
    "Clarification",
  ]) {
    assert.match(source, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }
})

test("client-backed workspace keeps required flow links and safety destinations visible", () => {
  const source = read("src/components/agentic-firm/backend-workspace-page.tsx")
  for (const expected of [
    "agents",
    "research",
    "strategy-lab",
    "backtests",
    "risk-center",
    "portfolio",
    "execution",
    "board-room",
    "audit",
    "costs",
    "settings",
    "Risk overview",
    "Risk approvals",
    "Kill switch",
    "Broker health",
    "Approval queue",
    "Audit events",
  ]) {
    assert.match(source, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }
})

test("global status is client-backed and does not hardcode seeded figures", () => {
  const source = read("src/components/agentic-firm/global-firm-status.tsx")
  for (const expected of [
    "executionClient.getReadiness",
    "executionClient.getBrokerHealth",
    "riskClient.getKillSwitch",
    "riskClient.getOverview",
    "portfolioClient.getOverview",
    "workflowClient.listWorkflows",
    "boardClient.listApprovalQueue",
    "initialStatusItems",
    "checking",
    "unavailable",
  ]) {
    assert.match(source, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }
  for (const seeded of ["2.1%", "+0.3R", "5 pending", "High cost anomaly", "Board approval for high-cost batch"]) {
    assert.doesNotMatch(source, new RegExp(seeded.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }
})

test("agentic firm telemetry covers UI, safety, export, and privacy rules", () => {
  const telemetry = read("src/lib/agentic-firm/telemetry.ts")
  const appShell = read("src/components/layout/app-shell.tsx")
  const apiClient = read("src/clients/agenticApi.ts")
  const globalStatus = read("src/components/agentic-firm/global-firm-status.tsx")

  for (const expected of [
    "agentic.page_load",
    "agentic.api_latency",
    "agentic.api_failed",
    "agentic.approval_interaction",
    "agentic.blocked_interaction",
    "agentic.user_clarification",
    "agentic.export_action",
    "agentic.workflow_launch",
    "agentic.chart_load_failure",
    "agentic.stale_data",
    "agentic.live_mode_visibility",
    "agentic.execution_button_render",
    "agentic.kill_switch_banner_display",
    "agentic.risk_governor_unavailable_display",
    "agentic.approval_disabled_reasons",
    "agentic.policy_mismatch_warning",
    "agentic.token_mismatch_warning",
  ]) {
    assert.match(telemetry, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }

  assert.match(telemetry, /SENSITIVE_KEY_PATTERN/)
  assert.match(telemetry, /secret\|password\|credential/)
  assert.match(apiClient, /requestId/)
  assert.match(apiClient, /traceId/)
  assert.match(appShell, /agentic\.page_load/)
  assert.match(apiClient, /agentic\.api_latency/)
  assert.match(apiClient, /agentic\.api_failed/)
  assert.match(globalStatus, /agentic\.live_mode_visibility/)
})

test("evidence-first rules are centralized and visible in Agentic Firm UI", () => {
  const core = read("src/types/agentic-core.ts")
  const workspace = read("src/components/agentic-firm/backend-workspace-page.tsx")
  const api = read("src/clients/agenticApi.ts")

  for (const expected of [
    "source reports",
    "deterministic reasons",
    "risk threshold",
    "observed value",
    "research hypothesis",
    "strategy spec version",
    "strategy code hash",
    "risk review",
    "performance evidence",
    "approval token",
    "broker response",
  ]) {
    assert.match(core, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"))
  }

  assert.match(api, /staleWarningLabel/)
  assert.match(api, /staleWarning/)
  assert.match(workspace, /Client-backed/)
  assert.match(workspace, /Backend data unavailable/)
  assert.match(workspace, /Seeded placeholder values are no longer shown here/)
})

test("governed action API rules require permission, audit, Board, and recovery proofs", () => {
  const api = read("src/clients/agenticApi.ts")
  const board = read("src/clients/boardClient.ts")
  const execution = read("src/clients/executionClient.ts")
  const risk = read("src/clients/riskClient.ts")

  for (const expected of [
    "server-side permission check ID",
    "required server-side permission",
    "CSRF token",
    "audit record intent",
    "Board approval",
    "critical-incident recovery approval",
    "X-Governed-Write",
    "X-Required-Permission",
    "X-Audit-Event-Type",
  ]) {
    assert.match(api, new RegExp(expected.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")))
  }

  assert.match(board, /approval_approved/)
  assert.match(board, /approval_rejected/)
  assert.match(execution, /live_trading_enable_requested/)
  assert.match(execution, /boardApprovalId/)
  assert.match(risk, /kill_switch_reset_requested/)
  assert.match(risk, /criticalIncidentApprovalId/)
})
