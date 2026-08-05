/**
 * Agentic operator client (7 operations).
 *
 * The Agentic firm has never executed for real: `submitRun` *reserves* a run
 * identifier and never starts an agent. Reads stay available while the firm is
 * disabled so an operator can determine why it stopped. Containment operations
 * — quarantine and the firm-wide disable kill switch — are requests to Agentic,
 * which remains the sole authority over its own runtime state.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { agenticRoutes } from "./routes";
import { request, type RequestOptions } from "./request";

/** Opaque Agentic-owned record. */
export const agenticRecordSchema = z.record(z.string(), z.unknown());
export type AgenticRecord = z.infer<typeof agenticRecordSchema>;

/** Reserve one Agentic run identifier (requires `agentic:submit`). */
export function submitRun(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.submitRun, {
    schema: agenticRecordSchema,
    body,
    ...options,
  });
}

/** Inspect one reserved run (requires `agentic:read_run`). */
export function getRun(
  runId: string,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.getRun, {
    schema: agenticRecordSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Cancel one reserved run (requires `agentic:cancel_run`). */
export function cancelRun(
  runId: string,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.cancelRun, {
    schema: agenticRecordSchema,
    pathParams: { run_id: runId },
    ...options,
  });
}

/** Read one immutable run audit trail (requires `agentic:read_audit`). */
export function runAudit(
  runId: string,
  taskId?: string,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.runAudit, {
    schema: agenticRecordSchema,
    pathParams: { run_id: runId },
    ...(taskId === undefined ? {} : { query: { task_id: taskId } }),
    ...options,
  });
}

/** Record one human handoff approval (requires `agentic:approve_promotion`). */
export function approveHandoff(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.approveHandoff, {
    schema: agenticRecordSchema,
    body,
    ...options,
  });
}

/** Quarantine one agent (requires `agentic:operate`). */
export function quarantine(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.quarantine, {
    schema: agenticRecordSchema,
    body,
    ...options,
  });
}

/** Trip the firm-wide Agentic kill switch (requires `agentic:operate`). */
export function disable(
  body: Record<string, unknown>,
  options?: RequestOptions
): Promise<ApiResponse<AgenticRecord>> {
  return request<AgenticRecord>(agenticRoutes.disable, {
    schema: agenticRecordSchema,
    body,
    ...options,
  });
}

/** Aggregated Agentic client. */
export const agentic = {
  submitRun,
  getRun,
  cancelRun,
  runAudit,
  approveHandoff,
  quarantine,
  disable,
};
