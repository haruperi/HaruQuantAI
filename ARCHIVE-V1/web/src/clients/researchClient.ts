"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema } from "@/validators/agentic-generic"

export const researchClient = {
  listReports() {
    return agenticApiData("/api/research/reports", {
      schema: unknownRecordListSchema,
      contractName: "ResearchReportList",
      staleWarningLabel: "research reports",
    })
  },
  listHypotheses() {
    return agenticApiData("/api/research/hypotheses", {
      schema: unknownRecordListSchema,
      contractName: "ResearchHypothesisList",
      staleWarningLabel: "research hypotheses",
    })
  },
}
