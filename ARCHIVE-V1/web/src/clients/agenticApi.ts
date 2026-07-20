"use client"

import type { z } from "zod"

import { getErrorMessage } from "@/lib/api-error"
import { trackAgenticTelemetry } from "@/lib/agentic-firm/telemetry"
import type { UiActionIntent } from "@/types/agentic-core"
import { validateContract } from "@/validators/agentic-contracts"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
const AUTH_TOKEN_STORAGE_KEY = "hq_auth_token"
const DEFAULT_STALE_AFTER_MS = 60_000

export type AgenticApiMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

export interface AgenticApiContext {
  requestId?: string
  traceId?: string
  sessionId?: string | number | null
  userId?: string | null
  permissionProfile?: string | null
  serverPermissionCheckId?: string | null
  csrfToken?: string | null
}

export interface AgenticApiOptions<T> {
  method?: AgenticApiMethod
  body?: unknown
  schema?: z.ZodType<T>
  contractName?: string
  context?: AgenticApiContext
  governedWrite?: boolean
  governedAction?: UiActionIntent
  workflowId?: string
  userApprovalId?: string
  requiredPermission?: string
  auditEventType?: string
  boardApprovalId?: string
  criticalIncidentApprovalId?: string
  retryReadOnly?: boolean
  staleAfterMs?: number
  staleWarningLabel?: string
}

export interface AgenticApiEnvelope<T> {
  data: T
  requestId: string
  traceId: string
  stale: boolean
  staleWarning?: string
}

export class AgenticApiError extends Error {
  readonly requestId?: string
  readonly traceId?: string
  readonly status?: number

  constructor(message: string, options: { requestId?: string; traceId?: string; status?: number } = {}) {
    super(message)
    this.name = "AgenticApiError"
    this.requestId = options.requestId
    this.traceId = options.traceId
    this.status = options.status
  }
}

function makeId(prefix: string): string {
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return `${prefix}-${random}`
}

function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null
  }
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
}

function buildHeaders(context: Required<Pick<AgenticApiContext, "requestId" | "traceId">> & AgenticApiContext): Headers {
  const headers = new Headers({
    "Content-Type": "application/json",
    "X-Request-ID": context.requestId,
    "X-Trace-ID": context.traceId,
  })

  const token = getAuthToken()
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }
  if (context.sessionId !== undefined && context.sessionId !== null) {
    headers.set("X-Session-ID", String(context.sessionId))
  }
  if (context.userId) {
    headers.set("X-User-ID", context.userId)
  }
  if (context.permissionProfile) {
    headers.set("X-Permission-Profile", context.permissionProfile)
  }
  if (context.serverPermissionCheckId) {
    headers.set("X-Server-Permission-Check-ID", context.serverPermissionCheckId)
  }
  if (context.csrfToken) {
    headers.set("X-CSRF-Token", context.csrfToken)
  }

  return headers
}

function validateGovernedWrite(options: AgenticApiOptions<unknown>, method: AgenticApiMethod) {
  if (!options.governedWrite && method === "GET") {
    return
  }

  if (!options.governedWrite) {
    return
  }

  const missing: string[] = []
  if (!options.context?.requestId) missing.push("request ID")
  if (!options.workflowId) missing.push("workflow ID")
  if (!options.userApprovalId) missing.push("explicit user approval")
  if (!options.requiredPermission) missing.push("required server-side permission")
  if (!options.context?.permissionProfile) missing.push("permission profile")
  if (!options.context?.serverPermissionCheckId) missing.push("server-side permission check ID")
  if (!options.context?.csrfToken) missing.push("CSRF token")
  if (!options.auditEventType) missing.push("audit record intent")
  if (
    (options.governedAction === "live_activation" || options.governedAction === "live_order") &&
    !options.boardApprovalId
  ) {
    missing.push("Board approval")
  }
  if (options.governedAction === "kill_switch_reset" && !options.criticalIncidentApprovalId) {
    missing.push("critical-incident recovery approval")
  }

  if (missing.length > 0) {
    throw new AgenticApiError(`Governed write blocked before request: missing ${missing.join(", ")}.`)
  }
}

function makeStaleWarning(label: string, elapsedMs: number): string {
  return `${label} is stale by ${Math.round(elapsedMs / 1000)}s. Refresh before using it for governed decisions.`
}

async function parsePayload(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined
  }

  const text = await response.text()
  if (!text) {
    return undefined
  }

  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

async function executeFetch(
  path: string,
  init: RequestInit,
  retry: boolean,
): Promise<Response> {
  try {
    const response = await fetch(`${API_URL}${path}`, init)
    if (retry && response.status >= 500) {
      return fetch(`${API_URL}${path}`, init)
    }
    return response
  } catch (error) {
    if (retry) {
      return fetch(`${API_URL}${path}`, init)
    }
    throw error
  }
}

export async function agenticApiRequest<T = unknown>(
  path: string,
  options: AgenticApiOptions<T> = {},
): Promise<AgenticApiEnvelope<T>> {
  const method = options.method ?? "GET"
  const requestId = options.context?.requestId ?? makeId("ui-req")
  const traceId = options.context?.traceId ?? makeId("ui-trace")
  const startedAt = Date.now()

  validateGovernedWrite(options as AgenticApiOptions<unknown>, method)
  const headers = buildHeaders({
    ...options.context,
    requestId,
    traceId,
  })
  if (options.governedWrite) {
    headers.set("X-Governed-Write", "server-enforced")
    headers.set("X-Required-Permission", options.requiredPermission ?? "")
    headers.set("X-Audit-Event-Type", options.auditEventType ?? "")
    if (options.workflowId) headers.set("X-Workflow-ID", options.workflowId)
    if (options.userApprovalId) headers.set("X-User-Approval-ID", options.userApprovalId)
    if (options.boardApprovalId) headers.set("X-Board-Approval-ID", options.boardApprovalId)
    if (options.criticalIncidentApprovalId) {
      headers.set("X-Critical-Incident-Approval-ID", options.criticalIncidentApprovalId)
    }
  }

  let response: Response
  let payload: unknown

  try {
    response = await executeFetch(
      path,
      {
        method,
        headers,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
      },
      Boolean((options.retryReadOnly ?? true) && method === "GET" && !options.governedWrite),
    )

    payload = await parsePayload(response)

    if (!response.ok) {
      trackAgenticTelemetry("agentic.api_failed", {
        path,
        method,
        status: response.status,
        requestId,
        traceId,
      })
      throw new AgenticApiError(getErrorMessage(payload, "Request failed"), {
        requestId,
        traceId,
        status: response.status,
      })
    }
  } catch (error) {
    if (!(error instanceof AgenticApiError)) {
      trackAgenticTelemetry("agentic.api_failed", {
        path,
        method,
        status: "network",
        requestId,
        traceId,
      })
    }
    throw error
  }

  const data = options.schema
    ? validateContract(options.schema, payload, options.contractName ?? path)
    : payload as T

  const elapsedMs = Date.now() - startedAt
  const staleAfterMs = options.staleAfterMs ?? DEFAULT_STALE_AFTER_MS
  const stale = elapsedMs > staleAfterMs
  trackAgenticTelemetry("agentic.api_latency", {
    path,
    method,
    latencyMs: elapsedMs,
    requestId,
    traceId,
    stale,
  })

  if (stale) {
    trackAgenticTelemetry("agentic.stale_data", {
      source: options.staleWarningLabel ?? path,
      latencyMs: elapsedMs,
      requestId,
      traceId,
    })
  }

  return {
    data,
    requestId,
    traceId,
    stale,
    staleWarning: stale
      ? makeStaleWarning(options.staleWarningLabel ?? path, elapsedMs)
      : undefined,
  }
}

export async function agenticApiData<T = unknown>(
  path: string,
  options: AgenticApiOptions<T> = {},
): Promise<T> {
  const envelope = await agenticApiRequest(path, options)
  return envelope.data
}

export function governedWriteContext(
  context: AgenticApiContext,
  workflowId: string,
  userApprovalId: string,
  rules: {
    requiredPermission: string
    auditEventType: string
    governedAction?: UiActionIntent
    boardApprovalId?: string
    criticalIncidentApprovalId?: string
  },
) {
  return {
    context,
    workflowId,
    userApprovalId,
    requiredPermission: rules.requiredPermission,
    auditEventType: rules.auditEventType,
    governedAction: rules.governedAction,
    boardApprovalId: rules.boardApprovalId,
    criticalIncidentApprovalId: rules.criticalIncidentApprovalId,
    governedWrite: true,
    retryReadOnly: false,
  } as const
}
