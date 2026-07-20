"use client"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const backtestClient = {
  listBacktests() {
    return agenticApiData("/api/backtests", {
      schema: unknownRecordListSchema,
      contractName: "BacktestList",
      staleWarningLabel: "backtest list",
    })
  },
  getBacktest(runId: string) {
    return agenticApiData(`/api/backtests/${runId}`, {
      schema: unknownRecordSchema,
      contractName: "BacktestDetail",
      staleWarningLabel: `backtest ${runId}`,
    })
  },
  listTrades(runId: string) {
    return agenticApiData(`/api/backtests/${runId}/trades`, {
      schema: unknownRecordListSchema,
      contractName: "BacktestTradeList",
    })
  },
  getEquity(runId: string) {
    return agenticApiData(`/api/backtests/${runId}/equity`, {
      schema: unknownRecordSchema,
      contractName: "BacktestEquity",
    })
  },
  getMetrics(runId: string) {
    return agenticApiData(`/api/backtests/${runId}/metrics`, {
      schema: unknownRecordSchema,
      contractName: "BacktestMetrics",
    })
  },
  getReport(runId: string) {
    return agenticApiData(`/api/backtests/${runId}/report`, {
      schema: unknownRecordSchema,
      contractName: "BacktestReport",
    })
  },
}
