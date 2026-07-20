"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const costClient = {
  getSummary() {
    return agenticApiData("/api/costs/summary", {
      schema: unknownRecordSchema,
      contractName: "CostSummary",
      staleWarningLabel: "cost summary",
    })
  },
  listByAgent() {
    return agenticApiData("/api/costs/by-agent", {
      schema: unknownRecordListSchema,
      contractName: "CostByAgent",
    })
  },
  listByWorkflow() {
    return agenticApiData("/api/costs/by-workflow", {
      schema: unknownRecordListSchema,
      contractName: "CostByWorkflow",
    })
  },
}
