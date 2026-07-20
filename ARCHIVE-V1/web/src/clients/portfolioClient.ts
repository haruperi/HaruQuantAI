"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const portfolioClient = {
  getOverview() {
    return agenticApiData("/api/portfolio/overview", {
      schema: unknownRecordSchema,
      contractName: "PortfolioOverview",
      staleWarningLabel: "portfolio overview",
    })
  },
  listAllocations() {
    return agenticApiData("/api/portfolio/allocations", {
      schema: unknownRecordListSchema,
      contractName: "PortfolioAllocationList",
    })
  },
  getLifecycle() {
    return agenticApiData("/api/portfolio/lifecycle", {
      schema: unknownRecordSchema,
      contractName: "PortfolioLifecycle",
    })
  },
  listRecommendations() {
    return agenticApiData("/api/portfolio/recommendations", {
      schema: unknownRecordListSchema,
      contractName: "PortfolioRecommendationList",
    })
  },
}
