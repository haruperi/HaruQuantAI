/**
 * Runtime-validated boundary contract mirrors.
 *
 * These Zod schemas mirror the canonical FastAPI boundary contracts in
 * `app/services/api/contracts/models.py` (ApiResponse.v1, ApiError.v1,
 * ApiMetadata.v1) so that the frontend transport layer can validate any
 * gateway response before it reaches application state. The backend is the
 * single authority; these schemas exist to detect drift, not to override it.
 *
 * All types are inferred from the schemas via `z.infer` and are treated as
 * readonly at the type level (mirroring the backend `frozen=True` models).
 */

import { z } from "zod";

/**
 * Stable machine error code family.
 *
 * Source of truth: `ApiErrorCode` in `contracts/models.py`.
 */
export const apiErrorCode = z.enum([
  "AUTHENTICATION_REQUIRED",
  "AUTHORIZATION_DENIED",
  "AUTHORIZATION_FAILED",
  "VALIDATION_ERROR",
  "VALIDATION_FAILED",
  "INTERNAL_ERROR",
  "NOT_FOUND",
  "NOT_IMPLEMENTED",
  "DEPENDENCY_UNAVAILABLE",
  "RATE_LIMITED",
  "GOVERNED_REQUEST_STALE",
  "CSRF_REQUIRED",
  "CSRF_INVALID",
  "IDEMPOTENCY_KEY_REQUIRED",
  "DUPLICATE_IDEMPOTENCY_KEY",
  "IDEMPOTENCY_CONFLICT",
  "GOVERNANCE_REQUIRED",
  "STALE_DATA",
  "UPSTREAM_UNAVAILABLE",
  "UPSTREAM_TIMEOUT",
  "UPSTREAM_NON_JSON_RESPONSE",
  "UNSUPPORTED_MEDIA_TYPE",
]);
export type ApiErrorCode = z.infer<typeof apiErrorCode>;

/** Response status discriminator. Source: `ApiStatus`. */
export const apiStatus = z.enum(["success", "error"]);
export type ApiStatus = z.infer<typeof apiStatus>;

/** Route side-effect classification. Source: `RouteSideEffect`. */
export const routeSideEffect = z.enum([
  "none",
  "read",
  "write",
  "governed_write",
  "stream",
]);
export type RouteSideEffect = z.infer<typeof routeSideEffect>;

/**
 * Response metadata envelope.
 *
 * Mirrors `ApiMetadata.v1`. The optional cursor/page-size fields carry the
 * pagination surface for list routes (only `/api/v1/data/symbols` today).
 */
export const apiMetadataSchema = z
  .object({
    contract_version: z.literal("v1").default("v1"),
    schema_id: z.literal("api.metadata.v1").default("api.metadata.v1"),
    request_id: z.string().min(1),
    route: z.string().min(1).startsWith("/"),
    operation: z.string().min(1),
    trace_id: z.string().nullable().nullish(),
    side_effect: routeSideEffect.default("read"),
    duration_ms: z.number().nullish(),
    timestamp: z.string().min(1),
    stale: z.boolean().default(false),
    stale_reason: z.string().nullable().nullish(),
    next_cursor: z.string().nullable().nullish(),
    page_size: z.number().int().min(0).max(200).nullish(),
    idempotency_replayed: z.boolean().default(false),
  })
  .superRefine((value, ctx) => {
    if (value.stale && !value.stale_reason) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "stale_reason is required when stale is true",
        path: ["stale_reason"],
      });
    }
  });

export type ApiMetadata = z.infer<typeof apiMetadataSchema>;

/**
 * Structured error payload.
 *
 * Mirrors `ApiError.v1`. `details` is bounded to <=16 entries with string
 * values capped at 256 characters by the backend; the frontend performs a
 * structural check only (the bound is documented, not re-enforced here).
 */
export const apiErrorSchema = z.object({
  code: apiErrorCode,
  message: z.string().min(1),
  details: z.record(z.string(), z.unknown()).default({}),
  request_id: z.string().nullable().nullish(),
  trace_id: z.string().nullable().nullish(),
  retryable: z.boolean().default(false),
});

export type ApiError = z.infer<typeof apiErrorSchema>;

/**
 * Success branch of the response envelope.
 *
 * `data` is parameterised by the caller's payload schema so each typed client
 * validates its own response shape.
 */
function successResponseSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.object({
    status: z.literal("success"),
    message: z.string().min(1),
    data: dataSchema,
    error: z.null(),
    metadata: apiMetadataSchema,
  });
}

/** Error branch of the response envelope. */
const errorResponseSchema = z.object({
  status: z.literal("error"),
  message: z.string().min(1),
  data: z.null(),
  error: apiErrorSchema,
  metadata: apiMetadataSchema,
});

/**
 * Build a discriminated-union response schema for a given payload type.
 *
 * The backend enforces branch exclusivity (success cannot carry an error;
 * error requires `data=null`); the discriminated union preserves that here.
 */
export function apiResponseSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.discriminatedUnion("status", [
    successResponseSchema(dataSchema),
    errorResponseSchema,
  ]);
}

/** Success-only response type (after a validated successful call). */
export type ApiSuccessResponse<T> = {
  readonly status: "success";
  readonly message: string;
  readonly data: T;
  readonly error: null;
  readonly metadata: ApiMetadata;
};

/** Error response type. */
export type ApiErrorResponse = {
  readonly status: "error";
  readonly message: string;
  readonly data: null;
  readonly error: ApiError;
  readonly metadata: ApiMetadata;
};

/** Discriminated response type returned by `request`. */
export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

/** Helper: narrow a validated response to its success branch. */
export function isApiSuccessResponse<T>(
  response: ApiResponse<T>
): response is ApiSuccessResponse<T> {
  return response.status === "success";
}

/** Permissive payload schema used when a route returns opaque owner JSON. */
export const opaquePayloadSchema = z.unknown();

/** Stream event type discriminator. Source: `StreamEventType`. */
export const streamEventType = z.enum(["heartbeat", "payload", "error"]);
export type StreamEventType = z.infer<typeof streamEventType>;

/**
 * Streaming event envelope.
 *
 * Mirrors `StreamEvent.v1` as served by the SSE bridge
 * (`app/services/api/workstation/data/stream_routes.py`). Each SSE frame carries `id`
 * (sequence), `event` (event_type), and `data` (this JSON envelope).
 */
export const streamEventSchema = z.object({
  sequence: z.number().int().min(0),
  request_id: z.string().min(1),
  trace_id: z.string().nullable().nullish(),
  route: z.string().min(1).startsWith("/"),
  event_type: streamEventType,
  timestamp: z.string().min(1),
  payload: z.record(z.string(), z.unknown()).nullable().nullish(),
  error: z.string().nullable().nullish(),
  cursor: z.string().nullable().nullish(),
});

export type StreamEvent = z.infer<typeof streamEventSchema>;
