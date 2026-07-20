"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const auditClient = {
  listAuditEvents() {
    return agenticApiData("/api/audit", {
      schema: unknownRecordListSchema,
      contractName: "AuditList",
      staleWarningLabel: "audit events",
    })
  },
  getAudit(auditId: string) {
    return agenticApiData(`/api/audit/${auditId}`, {
      schema: unknownRecordSchema,
      contractName: "AuditDetail",
      staleWarningLabel: `audit ${auditId}`,
    })
  },
}
