"use client"

import { agenticApiData, type AgenticApiContext, governedWriteContext } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"

export const executionClient = {
  getReadiness() {
    return agenticApiData("/api/execution/readiness", {
      schema: unknownRecordSchema,
      contractName: "ExecutionReadiness",
      staleWarningLabel: "execution readiness",
    })
  },
  listOrders() {
    return agenticApiData("/api/execution/orders", {
      schema: unknownRecordListSchema,
      contractName: "ExecutionOrderList",
      staleWarningLabel: "execution orders",
    })
  },
  getBrokerHealth() {
    return agenticApiData("/api/execution/broker-health", {
      schema: unknownRecordSchema,
      contractName: "ExecutionBrokerHealth",
      staleWarningLabel: "broker health",
    })
  },
  listIncidents() {
    return agenticApiData("/api/execution/incidents", {
      schema: unknownRecordListSchema,
      contractName: "ExecutionIncidentList",
    })
  },
  enableLiveTrading(
    payload: { reason: string; strategyId?: string },
    context: AgenticApiContext,
    workflowId: string,
    approvalId: string,
    boardApprovalId: string,
  ) {
    return agenticApiData("/api/execution/live-mode/enable", {
      method: "POST",
      body: payload,
      schema: unknownRecordSchema,
      contractName: "ExecutionLiveModeEnable",
      ...governedWriteContext(context, workflowId, approvalId, {
        requiredPermission: "board_approver",
        auditEventType: "live_trading_enable_requested",
        governedAction: "live_activation",
        boardApprovalId,
      }),
    })
  },
}
