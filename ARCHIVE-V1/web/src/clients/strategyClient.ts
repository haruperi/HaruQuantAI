"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const strategyClient = {
  listStrategies() {
    return agenticApiData("/api/strategies", {
      schema: unknownRecordListSchema,
      contractName: "StrategyList",
      staleWarningLabel: "strategy list",
    })
  },
  getStrategy(strategyId: string) {
    return agenticApiData(`/api/strategies/${strategyId}`, {
      schema: unknownRecordSchema,
      contractName: "StrategyDetail",
      staleWarningLabel: `strategy ${strategyId}`,
    })
  },
  listSpecs(strategyId: string) {
    return agenticApiData(`/api/strategies/${strategyId}/specs`, {
      schema: unknownRecordListSchema,
      contractName: "StrategySpecList",
      staleWarningLabel: `strategy ${strategyId} specs`,
    })
  },
  listCodeVersions(strategyId: string) {
    return agenticApiData(`/api/strategies/${strategyId}/code-versions`, {
      schema: unknownRecordListSchema,
      contractName: "StrategyCodeVersionList",
    })
  },
  listReviews(strategyId: string) {
    return agenticApiData(`/api/strategies/${strategyId}/reviews`, {
      schema: unknownRecordListSchema,
      contractName: "StrategyReviewList",
    })
  },
  getLifecycle(strategyId: string) {
    return agenticApiData(`/api/strategies/${strategyId}/lifecycle`, {
      schema: unknownRecordSchema,
      contractName: "StrategyLifecycle",
    })
  },
}
