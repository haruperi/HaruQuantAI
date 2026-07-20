"use client"

import { agenticApiData, type AgenticApiContext, governedWriteContext } from "@/clients/agenticApi"
import { approvalRequestSchema } from "@/validators/agentic-contracts"
import { z } from "zod"

export const boardClient = {
  listApprovalQueue() {
    return agenticApiData("/api/board/approval-queue", {
      schema: z.array(approvalRequestSchema),
      contractName: "BoardApprovalQueue",
      staleWarningLabel: "board approval queue",
    })
  },
  approveApproval(
    approvalId: string,
    payload: { reason: string },
    context: AgenticApiContext,
    workflowId: string,
  ) {
    return agenticApiData(`/api/board/approvals/${approvalId}/approve`, {
      method: "POST",
      body: payload,
      schema: approvalRequestSchema,
      contractName: "BoardApprovalDecision",
      ...governedWriteContext(context, workflowId, approvalId, {
        requiredPermission: "board_approver",
        auditEventType: "approval_approved",
      }),
    })
  },
  rejectApproval(
    approvalId: string,
    payload: { reason: string },
    context: AgenticApiContext,
    workflowId: string,
  ) {
    return agenticApiData(`/api/board/approvals/${approvalId}/reject`, {
      method: "POST",
      body: payload,
      schema: approvalRequestSchema,
      contractName: "BoardRejectionDecision",
      ...governedWriteContext(context, workflowId, approvalId, {
        requiredPermission: "board_approver",
        auditEventType: "approval_rejected",
      }),
    })
  },
}
