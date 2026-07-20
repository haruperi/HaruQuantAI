import { z } from "zod"

export const agentStatusSchema = z.enum(["success", "rejected", "needs_more_context", "error"])
export const confidenceLevelSchema = z.enum(["low", "medium", "high"])
export const riskLevelSchema = z.enum(["low", "medium", "high", "critical"])

export const evidenceItemSchema = z.object({
  source: z.string().min(1),
  description: z.string().min(1),
  value: z.unknown().optional(),
  confidence: confidenceLevelSchema,
})

export const llmAnalysisSchema = z.object({
  summary: z.string(),
  observations: z.array(z.string()),
  risks: z.array(z.string()),
  suggestions: z.array(z.string()),
  raw_model_output: z.string().nullable().optional(),
})

export const agentDecisionSchema = z.object({
  status: agentStatusSchema,
  decision: z.string(),
  confidence: confidenceLevelSchema,
  risk_level: riskLevelSchema,
  allowed_actions: z.array(z.string()),
  blocked_actions: z.array(z.string()),
  reasons: z.array(z.string()),
})

export const agentAuditSchema = z.object({
  agent_name: z.string().min(1),
  prompt_version: z.string().optional(),
  policy_version: z.string().min(1),
  llm_used: z.boolean(),
  tools_used: z.array(z.string()),
  permission_profile: z.string().min(1),
  evidence_refs: z.array(z.string()),
  context_revision: z.string().optional(),
  model_provider: z.string().optional(),
  model_name: z.string().optional(),
  fallback_used: z.boolean().optional(),
})

export const agentResponseSchema = z.object({
  request_id: z.string().min(1),
  agent_name: z.string().min(1),
  status: agentStatusSchema,
  evidence: z.array(evidenceItemSchema),
  llm_analysis: llmAnalysisSchema.nullable().optional(),
  decision: agentDecisionSchema,
  artifacts: z.record(z.string(), z.unknown()),
  audit: agentAuditSchema,
})

export const workflowTaskStatusSchema = z.enum([
  "queued",
  "planned",
  "running",
  "waiting_for_evidence",
  "waiting_for_approval",
  "blocked",
  "failed",
  "rejected",
  "completed",
  "cancelled",
])

export const workflowTaskPrioritySchema = z.enum(["low", "normal", "high", "critical"])

export const workflowTaskSchema = z.object({
  workflow_id: z.string().min(1),
  task_id: z.string().min(1),
  parent_task_id: z.string().nullable().optional(),
  agent_service_name: z.string().min(1),
  department: z.string().min(1),
  title: z.string().min(1),
  status: workflowTaskStatusSchema,
  priority: workflowTaskPrioritySchema,
  dependencies: z.array(z.string()),
  started_at: z.string().nullable().optional(),
  completed_at: z.string().nullable().optional(),
  duration_ms: z.number().nonnegative().nullable().optional(),
  cost_usd: z.number().nonnegative().nullable().optional(),
  evidence_refs: z.array(z.string()),
  output_artifact_refs: z.array(z.string()),
  error_details: z.string().nullable().optional(),
  retry_count: z.number().int().nonnegative(),
  blocked_reason: z.string().nullable().optional(),
})

export const approvalStatusSchema = z.enum([
  "draft",
  "pending_user",
  "approved",
  "rejected",
  "expired",
  "cancelled",
  "blocked_by_risk",
  "blocked_by_policy",
])

export const approvalAuditEventSchema = z.object({
  event_id: z.string().min(1),
  actor: z.string().min(1),
  action: z.string().min(1),
  reason: z.string().nullable().optional(),
  created_at: z.string().min(1),
  metadata: z.record(z.string(), z.unknown()).optional(),
})

export const approvalRequestSchema = z.object({
  approval_id: z.string().min(1),
  requested_action: z.string().min(1),
  requester_agent: z.string().min(1),
  affected_strategy: z.string().nullable().optional(),
  affected_portfolio: z.string().nullable().optional(),
  risk_level: riskLevelSchema,
  evidence_refs: z.array(z.string()),
  deterministic_policy_summary: agentDecisionSchema,
  risk_governor_output: z.record(z.string(), z.unknown()).nullable().optional(),
  expires_at: z.string().nullable().optional(),
  status: approvalStatusSchema,
  approver: z.string().nullable().optional(),
  decision_timestamp: z.string().nullable().optional(),
  audit_trail: z.array(approvalAuditEventSchema),
})

export class AgenticContractValidationError extends Error {
  readonly issues: z.ZodIssue[]

  constructor(contractName: string, issues: z.ZodIssue[]) {
    super(`${contractName} failed schema validation`)
    this.name = "AgenticContractValidationError"
    this.issues = issues
  }
}

export function formatValidationIssues(issues: z.ZodIssue[]): string[] {
  return issues.map((issue) => {
    const path = issue.path.length > 0 ? issue.path.join(".") : "root"
    return `${path}: ${issue.message}`
  })
}

export function validateContract<T>(
  schema: z.ZodType<T>,
  payload: unknown,
  contractName: string,
): T {
  const result = schema.safeParse(payload)
  if (!result.success) {
    throw new AgenticContractValidationError(contractName, result.error.issues)
  }
  return result.data
}

export function validateAgentResponse(payload: unknown) {
  return validateContract(agentResponseSchema, payload, "AgentResponse")
}

export function validateWorkflowTask(payload: unknown) {
  return validateContract(workflowTaskSchema, payload, "WorkflowTask")
}

export function validateApprovalRequest(payload: unknown) {
  return validateContract(approvalRequestSchema, payload, "ApprovalRequest")
}

export function getFailClosedAgentDecision() {
  return {
    status: "error" as const,
    decision: "Malformed agent decision blocked by UI schema validation.",
    confidence: "low" as const,
    risk_level: "critical" as const,
    allowed_actions: [],
    blocked_actions: ["render_as_approved", "execute_governed_action"],
    reasons: ["The agent response did not match the required UI contract."],
  }
}
