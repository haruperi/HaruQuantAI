export type WorkflowTaskStatus =
  | "queued"
  | "planned"
  | "running"
  | "waiting_for_evidence"
  | "waiting_for_approval"
  | "blocked"
  | "failed"
  | "rejected"
  | "completed"
  | "cancelled"

export type WorkflowTaskPriority = "low" | "normal" | "high" | "critical"

export interface WorkflowTask {
  workflow_id: string
  task_id: string
  parent_task_id?: string | null
  agent_service_name: string
  department: string
  title: string
  status: WorkflowTaskStatus
  priority: WorkflowTaskPriority
  dependencies: string[]
  started_at?: string | null
  completed_at?: string | null
  duration_ms?: number | null
  cost_usd?: number | null
  evidence_refs: string[]
  output_artifact_refs: string[]
  error_details?: string | null
  retry_count: number
  blocked_reason?: string | null
}
