"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const evidenceClient = {
  getEvidence(evidenceId: string) {
    return agenticApiData(`/api/evidence/${evidenceId}`, {
      schema: unknownRecordSchema,
      contractName: "EvidenceDetail",
      staleWarningLabel: `evidence ${evidenceId}`,
    })
  },
  listEvidenceByReport(reportId: string) {
    return agenticApiData(`/api/evidence/by-report/${reportId}`, {
      schema: unknownRecordListSchema,
      contractName: "EvidenceByReport",
      staleWarningLabel: `evidence for report ${reportId}`,
    })
  },
}
