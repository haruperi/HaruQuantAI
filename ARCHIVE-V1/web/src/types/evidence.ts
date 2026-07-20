export type ConfidenceLevel = "low" | "medium" | "high"

export interface EvidenceItem {
  source: string
  description: string
  value?: unknown
  confidence: ConfidenceLevel
}

export interface EvidenceReference {
  evidence_id: string
  source_type?: string | null
  source_name?: string | null
  report_id?: string | null
  artifact_uri?: string | null
}
