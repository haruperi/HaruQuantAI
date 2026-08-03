/**
 * Operator client for the 3 operator operations (2 reads + 1 governed write).
 *
 * The approvals POST is a governed write: the backend requires idempotency and
 * governance scope. The transport attaches the idempotency key automatically
 * when one is not supplied, and reads the CSRF cookie for the double-submit
 * header.
 */

import { z } from "zod";

import type { ApiResponse } from "./contracts";
import { operatorRoutes } from "./routes";
import { request, type RequestOptions, type QueryValue } from "./request";

/** Bounded audit-event row. Data-owned; returned opaquely. */
export const auditEventSchema = z.record(z.string(), z.unknown());
export type AuditEvent = z.infer<typeof auditEventSchema>;

/** Audit-events page (bounded list; limit only, no cursor). */
export const auditEventsPageSchema = z.object({
  events: z.array(auditEventSchema),
});
export type AuditEventsPage = z.infer<typeof auditEventsPageSchema>;

/** Trading operational event (Trading-owned `OperationalEvent`). */
export const operationalEventSchema = z.record(z.string(), z.unknown());
export type OperationalEvent = z.infer<typeof operationalEventSchema>;

/** Approval record (backend `ApprovalRecord`). */
export const approvalRecordSchema = z.object({
  approval_id: z.string().min(1),
  issuer_id: z.string().min(1),
  subject_id: z.string().min(1),
  scope: z.string().min(1),
  evidence_hash: z.string().min(1),
  created_at: z.string().min(1),
  expires_at: z.string().min(1),
  consumed_at: z.string().nullable().nullish(),
});
export type ApprovalRecord = z.infer<typeof approvalRecordSchema>;

/** Request body for a scoped approval (backend `_ApprovalRequest`). */
export interface ApprovalRequest {
  subject_id: string;
  scope: string;
  evidence: Record<string, unknown>;
  /** TTL seconds 1..86400. */
  ttl_seconds: number;
}

/** Query parameters for audit events. */
export interface AuditEventsQuery {
  /** Limit 1..200; defaults to 50. */
  limit?: number;
}

/** Read a bounded audit-events page (requires `ops:audit:read`). */
export function auditEvents(
  params: AuditEventsQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<AuditEventsPage>> {
  const query: Record<string, QueryValue> = {};
  if (params.limit !== undefined) query.limit = params.limit;
  return request<AuditEventsPage>(operatorRoutes.auditEvents, {
    schema: auditEventsPageSchema,
    query,
    ...options,
  });
}

/** Read Trading operational events (requires `ops:events:read`). */
export function events(
  options?: RequestOptions
): Promise<ApiResponse<OperationalEvent[]>> {
  return request<OperationalEvent[]>(operatorRoutes.events, {
    schema: z.array(operationalEventSchema),
    ...options,
  });
}

/** Create a scoped distinct-principal approval (governed; HTTP 201). */
export function approvals(
  input: ApprovalRequest,
  options?: RequestOptions
): Promise<ApiResponse<ApprovalRecord>> {
  return request<ApprovalRecord>(operatorRoutes.approvals, {
    schema: approvalRecordSchema,
    body: input,
    ...options,
  });
}

/** Aggregated operator client. */
export const operator = { auditEvents, events, approvals };
