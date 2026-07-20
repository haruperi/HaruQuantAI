"use client"

import { agenticApiData, type AgenticApiContext, governedWriteContext } from "@/clients/agenticApi"
import { approvalRequestSchema } from "@/validators/agentic-contracts"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"
import { z } from "zod"

export const riskClient = {
  getOverview() {
    return agenticApiData("/api/risk/overview", {
      schema: unknownRecordSchema,
      contractName: "RiskOverview",
      staleWarningLabel: "risk overview",
    })
  },
  listApprovals() {
    return agenticApiData("/api/risk/approvals", {
      schema: z.array(approvalRequestSchema),
      contractName: "RiskApprovalList",
      staleWarningLabel: "risk approvals",
    })
  },
  listBlocks() {
    return agenticApiData("/api/risk/blocks", {
      schema: unknownRecordListSchema,
      contractName: "RiskBlockList",
    })
  },
  getVarCvar() {
    return agenticApiData("/api/risk/var-cvar", {
      schema: unknownRecordSchema,
      contractName: "RiskVarCvar",
    })
  },
  getCorrelation() {
    return agenticApiData("/api/risk/correlation", {
      schema: unknownRecordSchema,
      contractName: "RiskCorrelation",
    })
  },
  getKillSwitch() {
    return agenticApiData("/api/risk/kill-switch", {
      schema: unknownRecordSchema,
      contractName: "RiskKillSwitch",
      staleWarningLabel: "kill-switch state",
    })
  },
  resetKillSwitch(
    payload: { reason: string; incidentId: string },
    context: AgenticApiContext,
    workflowId: string,
    approvalId: string,
    criticalIncidentApprovalId: string,
  ) {
    return agenticApiData("/api/risk/kill-switch/reset", {
      method: "POST",
      body: payload,
      schema: unknownRecordSchema,
      contractName: "RiskKillSwitchReset",
      ...governedWriteContext(context, workflowId, approvalId, {
        requiredPermission: "board_approver",
        auditEventType: "kill_switch_reset_requested",
        governedAction: "kill_switch_reset",
        criticalIncidentApprovalId,
      }),
    })
  },
}
