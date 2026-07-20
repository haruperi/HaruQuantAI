import type { ConfidenceLevel, EvidenceItem } from "@/types/evidence"

export type AgentStatus =
  | "success"
  | "rejected"
  | "needs_more_context"
  | "error"

export type RiskLevel = "low" | "medium" | "high" | "critical"

export interface LLMAnalysis {
  summary: string
  observations: string[]
  risks: string[]
  suggestions: string[]
  raw_model_output?: string | null
}

export interface AgentDecision {
  status: AgentStatus
  decision: string
  confidence: ConfidenceLevel
  risk_level: RiskLevel
  allowed_actions: string[]
  blocked_actions: string[]
  reasons: string[]
}

export interface AgentAudit {
  agent_name: string
  prompt_version?: string
  policy_version: string
  llm_used: boolean
  tools_used: string[]
  permission_profile: string
  evidence_refs: string[]
  context_revision?: string
  model_provider?: string
  model_name?: string
  fallback_used?: boolean
}

export interface AgentResponse {
  request_id: string
  agent_name: string
  status: AgentStatus
  evidence: EvidenceItem[]
  llm_analysis?: LLMAnalysis | null
  decision: AgentDecision
  artifacts: Record<string, unknown>
  audit: AgentAudit
}
