"use client"

import { z } from "zod"

import { agenticApiData } from "@/clients/agenticApi"
import { unknownRecordListSchema, unknownRecordSchema } from "@/validators/agentic-generic"
import { workflowTaskSchema } from "@/validators/agentic-contracts"

export const workflowClient = {
  listWorkflows() {
    return agenticApiData("/api/workflows", {
      schema: unknownRecordListSchema,
      contractName: "WorkflowList",
      staleWarningLabel: "workflow list",
    })
  },
  getWorkflow(workflowId: string) {
    return agenticApiData(`/api/workflows/${workflowId}`, {
      schema: unknownRecordSchema,
      contractName: "WorkflowDetail",
      staleWarningLabel: `workflow ${workflowId}`,
    })
  },
  listWorkflowTasks(workflowId: string) {
    return agenticApiData(`/api/workflows/${workflowId}/tasks`, {
      schema: z.array(workflowTaskSchema),
      contractName: "WorkflowTaskList",
      staleWarningLabel: `workflow ${workflowId} tasks`,
    })
  },
}
