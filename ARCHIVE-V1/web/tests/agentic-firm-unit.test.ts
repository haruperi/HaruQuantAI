import assert from "node:assert/strict"
import { test } from "node:test"

import { createAgenticFirmClient } from "../src/lib/agentic-firm/api-clients"
import {
  agentResponseSchema,
  evidenceItemSchema,
  validateAgenticPayload,
} from "../src/lib/agentic-firm/validators"
import {
  evaluateEvidenceFirstUi,
  evaluateGovernedUiAction,
  type ExecutionSafetyState,
} from "../src/types/agentic-core"

const safeExecutionState: ExecutionSafetyState = {
  accountMode: "micro-live",
  boardApproved: true,
  riskGovernorApproved: true,
  riskGovernorApprovalToken: "RG-TOKEN-001",
  killSwitchActive: false,
  orderRouterAvailable: true,
  brokerHeartbeatOk: true,
  auditLoggerAvailable: true,
}

test("governed action evaluator blocks unsafe live activation", () => {
  const result = evaluateGovernedUiAction(
    {
      intent: "live_activation",
      requestId: "REQ-1",
      workflowId: "WF-1",
      userApprovalId: "APP-1",
      userPermission: "board_approver",
      serverPermissionCheck: true,
      auditRecordIntent: "live_activation_attempted",
      evidenceRefs: ["EV-1"],
    },
    { ...safeExecutionState, boardApproved: false, brokerHeartbeatOk: false },
  )

  assert.equal(result.allowed, false)
  assert.equal(result.requiredRoute, "order_router")
  assert.ok(result.reasons.includes("Missing Board approval."))
  assert.ok(result.reasons.includes("Broker heartbeat is not healthy."))
})

test("governed action evaluator allows complete paper order through order router", () => {
  const result = evaluateGovernedUiAction(
    {
      intent: "paper_order",
      requestId: "REQ-2",
      workflowId: "WF-2",
      userApprovalId: "APP-2",
      userPermission: "board_approver",
      serverPermissionCheck: true,
      auditRecordIntent: "paper_order_requested",
      evidenceRefs: ["EV-2"],
      approvalToken: "RG-TOKEN-001",
    },
    safeExecutionState,
  )

  assert.equal(result.allowed, true)
  assert.equal(result.requiredRoute, "order_router")
  assert.deepEqual(result.reasons, [])
})

test("governed action evaluator requires server permission and audit intent", () => {
  const result = evaluateGovernedUiAction(
    {
      intent: "paper_order",
      requestId: "REQ-2B",
      workflowId: "WF-2B",
      evidenceRefs: ["EV-2B"],
      approvalToken: "RG-TOKEN-001",
    },
    safeExecutionState,
  )

  assert.equal(result.allowed, false)
  assert.ok(result.reasons.includes("Missing server-side permission check."))
  assert.ok(result.reasons.includes("Missing explicit user approval."))
  assert.ok(result.reasons.includes("Missing audit record intent."))
})

test("evidence-first evaluator requires lineage by surface type", () => {
  assert.equal(
    evaluateEvidenceFirstUi({
      surface: "live_execution",
      evidenceRefs: ["EV-EXEC-1"],
      approvalToken: "RG-TOKEN-001",
      brokerResponseId: "BROKER-RESP-001",
    }).complete,
    true,
  )

  const missingRiskBlock = evaluateEvidenceFirstUi({
    surface: "risk_block",
    evidenceRefs: ["EV-RISK-1"],
    riskThreshold: "30 min minimum",
  })

  assert.equal(missingRiskBlock.complete, false)
  assert.ok(missingRiskBlock.missing.includes("observed value"))
})

test("validators accept complete agent responses and reject malformed decisions", () => {
  const validPayload = {
    request_id: "REQ-3",
    agent_name: "ceo_agent",
    status: "success",
    evidence: [{ source: "risk_review", description: "Risk review attached.", confidence: "high" }],
    decision: {
      status: "success",
      decision: "Approve paper-only workflow.",
      confidence: "high",
      risk_level: "medium",
      allowed_actions: ["request_paper_admission"],
      blocked_actions: ["enable_live"],
      reasons: ["Board live approval is missing."],
    },
    artifacts: {},
    audit: {
      agent_name: "ceo_agent",
      policy_version: "ceo_policy:v1",
      llm_used: true,
      tools_used: ["planner", "evidence_lookup"],
      permission_profile: "ceo_orchestrator",
      evidence_refs: ["EV-1"],
    },
  }

  assert.equal(validateAgenticPayload(agentResponseSchema, validPayload).ok, true)
  assert.equal(validateAgenticPayload(agentResponseSchema, { ...validPayload, decision: {} }).ok, false)
})

test("evidence validator requires source, description, and confidence", () => {
  assert.equal(
    validateAgenticPayload(evidenceItemSchema, {
      source: "research_report",
      description: "Hypothesis support.",
      confidence: "medium",
    }).ok,
    true,
  )
  assert.equal(validateAgenticPayload(evidenceItemSchema, { source: "research_report" }).ok, false)
})

test("agentic firm API client propagates request, trace, session, and auth headers", async () => {
  const calls: Request[] = []
  const client = createAgenticFirmClient({
    baseUrl: "https://api.example.test",
    getAuthToken: () => "token-1",
    fetchImpl: async (input, init) => {
      const request = new Request(input, init)
      calls.push(request)
      return Response.json({
        source: "research_report",
        description: "Hypothesis support.",
        confidence: "high",
      })
    },
  })

  await client.evidence.getEvidence("EV-1", "REQ-4")

  assert.equal(calls.length, 1)
  assert.equal(calls[0].url, "https://api.example.test/agentic-firm/evidence/EV-1")
  assert.equal(calls[0].headers.get("X-Request-ID"), "REQ-4")
  assert.equal(calls[0].headers.get("Authorization"), "Bearer token-1")
})
