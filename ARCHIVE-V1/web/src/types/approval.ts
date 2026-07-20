import type { AgentDecision, RiskLevel } from "@/types/agent"

export type ApprovalStatus =
  | "draft"
  | "pending_user"
  | "approved"
  | "rejected"
  | "expired"
  | "cancelled"
  | "blocked_by_risk"
  | "blocked_by_policy"

export interface ApprovalAuditEvent {
  event_id: string
  actor: string
  action: string
  reason?: string | null
  created_at: string
  metadata?: Record<string, unknown>
}

export interface ApprovalRequest {
  approval_id: string
  requested_action: string
  requester_agent: string
  affected_strategy?: string | null
  affected_portfolio?: string | null
  risk_level: RiskLevel
  evidence_refs: string[]
  deterministic_policy_summary: AgentDecision
  risk_governor_output?: Record<string, unknown> | null
  expires_at?: string | null
  status: ApprovalStatus
  approver?: string | null
  decision_timestamp?: string | null
  audit_trail: ApprovalAuditEvent[]
}
