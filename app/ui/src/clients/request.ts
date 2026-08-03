/**
 * Typed frontend transport primitive.
 *
 * One single transport entry point (`request`) sends an authenticated,
 * traced, contract-validated HTTP request through the FastAPI gateway and
 * returns a validated `ApiResponse<T>` envelope. There is no parallel generic
 * helper stack: every typed client in this package delegates through
 * `request`. Authentication attaches only through the opaque-cookie or
 * bearer-service-account transport specified in the API README.
 */

import { z } from "zod";

import {
  type ApiResponse,
  type ApiSuccessResponse,
  apiResponseSchema,
  isApiSuccessResponse,
} from "./contracts";
import type { RouteContract } from "./routes";

/**
 * Typed failure raised by the transport for any HTTP, contract, or transport
 * error. Carries the stable status, code, request/trace identifiers,
 * retryability flag, and bounded structured details so callers can render a
 * traceable, redacted failure without re-parsing the envelope.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly requestId: string | null;
  public readonly traceId: string | null;
  public readonly retryable: boolean;
  public readonly details: Readonly<Record<string, unknown>>;

  public constructor(config: {
    message: string;
    status: number;
    code: string;
    requestId?: string | null;
    traceId?: string | null;
    retryable?: boolean;
    details?: Record<string, unknown> | null;
    cause?: unknown;
  }) {
    super(config.message, { cause: config.cause });
    this.name = "ApiClientError";
    this.status = config.status;
    this.code = config.code;
    this.requestId = config.requestId ?? null;
    this.traceId = config.traceId ?? null;
    this.retryable = config.retryable ?? false;
    this.details = Object.freeze({ ...(config.details ?? {}) });
  }
}

/**
 * Generate a request identifier.
 *
 * Mirrors the backend request-id shape (`req_` prefix + base62). Used only
 * when the caller has not supplied one explicitly.
 */
function generateRequestId(): string {
  const bytes = new Uint8Array(12);
  globalThis.crypto.getRandomValues(bytes);
  const alphabet =
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  let id = "";
  for (const byte of bytes) {
    id += alphabet[byte % alphabet.length];
  }
  return `req_${id}`;
}

/** Read a document cookie by name; returns null when unavailable (SSR, disabled). */
function readCookie(name: string): string | null {
  if (typeof document === "undefined" || typeof document.cookie !== "string") {
    return null;
  }
  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const trimmed = part.trim();
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length));
    }
  }
  return null;
}

/** The CSRF cookie name set by the backend on cookie-authenticated login. */
const CSRF_COOKIE_NAME = "hq_csrf";
/** The CSRF header name the backend validates for non-safe methods. */
const CSRF_HEADER_NAME = "X-CSRF-Token";

/**
 * Resolve the gateway base URL.
 *
 * In development, `NEXT_PUBLIC_API_URL` is empty and the request is issued
 * same-origin through the `next.config.mjs` rewrite proxy so session and CSRF
 * cookies remain first-party. In production, the variable must be set or the
 * transport falls back to same-origin (the rewrite proxy would also be
 * configured in production deployments).
 */
export function resolveBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (url.trim().length > 0) {
    return url.replace(/\/+$/, "");
  }
  // Empty value means "same-origin" (dev rewrite proxy).
  return "";
}

/** Query parameter value (string | number | boolean | null | undefined). */
export type QueryValue = string | number | boolean | null | undefined;

/** Options accepted by `request`. */
export interface RequestOptions {
  /** Payload schema used to validate the success `data` field. */
  schema?: z.ZodTypeAny;
  /** JSON request body (POST/PUT/PATCH only). */
  body?: unknown;
  /** Path parameters interpolated into the route template. */
  pathParams?: Record<string, string | number>;
  /** Query parameters. */
  query?: Record<string, QueryValue>;
  /** Explicit request id; generated when omitted. */
  requestId?: string;
  /** Explicit trace id forwarded to the gateway. */
  traceId?: string;
  /**
   * Idempotency key for governed/_write routes. When omitted on a route that
   * requires one, the transport generates a UUID (crypto.randomUUID when
   * available).
   */
  idempotencyKey?: string;
  /**
   * Bearer token for service-account transport. When set, an
   * `Authorization: Bearer <token>` header is attached and cookie credentials
   * are still included so both transports coexist if needed.
   */
  authToken?: string;
  /**
   * Opt-in single retry for transient GET failures. Defaults to true for
   * GET and false otherwise; governed writes and unknown broker outcomes
   * never retry blindly (NFR-API-013).
   */
  retry?: boolean;
  /** Abort the request via this signal. */
  signal?: AbortSignal;
}

/** Interpolate path parameters into a `/api/v1/.../{id}` template. */
function buildPath(
  template: string,
  pathParams?: Record<string, string | number>
): string {
  if (!pathParams) return template;
  return template.replace(/\{([^/{}]+)\}/g, (match, key: string) => {
    void match;
    if (!(key in pathParams)) {
      throw new ApiClientError({
        message: `missing path parameter '${key}' for route template '${template}'`,
        status: 0,
        code: "VALIDATION_FAILED",
      });
    }
    return encodeURIComponent(String(pathParams[key]));
  });
}

/** Build a query string from a record, skipping null/undefined values. */
function buildQuery(params?: Record<string, QueryValue>): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined) continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/**
 * Decide whether an HTTP failure is a safe-to-retry transient GET failure.
 *
 * Retries are allowed only for GET requests that returned a network error,
 * a 408/429, or a 5xx. Idempotency-protected writes never retry blindly.
 */
function isTransientGetFailure(method: string, status: number): boolean {
  if (method !== "GET") return false;
  return status === 0 || status === 408 || status === 429 || status >= 500;
}

/** Sleep helper used only for the single retry back-off. */
function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new Error("aborted"));
      return;
    }
    const timer = setTimeout(() => resolve(), ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(new Error("aborted"));
      },
      { once: true }
    );
  });
}

/** Build a synthetic success envelope for bodyless (204) and text routes. */
function syntheticSuccess<T>(
  contract: RouteContract,
  requestId: string,
  traceId: string | undefined,
  data: T,
  message: string
): ApiSuccessResponse<T> {
  return {
    status: "success",
    message,
    data,
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: requestId,
      route: contract.path,
      operation: contract.id,
      trace_id: traceId ?? null,
      side_effect: contract.sideEffect,
      duration_ms: null,
      timestamp: new Date().toISOString(),
      stale: false,
      stale_reason: null,
      next_cursor: null,
      page_size: null,
      idempotency_replayed: false,
    },
  };
}

/**
 * Send one typed, authenticated, contract-validated HTTP request through the
 * gateway and return the validated `ApiResponse<T>` envelope.
 *
 * Behaviour:
 * - Attaches `credentials: "include"` so the opaque `hq_session` cookie is
 *   sent and Set-Cookie responses are honoured.
 * - For non-GET methods under cookie auth, reads the `hq_csrf` cookie and
 *   attaches the `X-CSRF-Token` header (double-submit CSRF).
 * - Generates a request id when none is supplied; forwards a trace id.
 * - Attaches an idempotency-key header for routes that require one.
 * - Parses HTTP 204 as an empty success; validates JSON envelopes with the
 *   caller's Zod `schema` against `apiResponseSchema`.
 * - Performs exactly one opt-in retry for transient GET failures.
 * - Translates every failure into a traceable `ApiClientError`.
 *
 * Args:
 *   contract: One route contract from `routes.ts`.
 *   options: Request options including the success payload schema.
 *
 * Returns:
 *   The validated response envelope (success or error branch).
 *
 * Raises:
 *   ApiClientError: On network, HTTP, contract-validation, or transport
 *   failure.
 */
export async function request<T>(
  contract: RouteContract,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const schema = (options.schema ?? z.unknown()) as z.ZodTypeAny;
  const requestId = options.requestId ?? generateRequestId();
  const method = contract.method;

  // --- Text-returning routes (metrics): bypass the JSON envelope. ---------
  if (contract.returnsText) {
    const text = await sendRaw<string>(contract, options, requestId, (resp) =>
      resp.text()
    );
    return syntheticSuccess<T>(
      contract,
      requestId,
      options.traceId,
      text as unknown as T,
      "ok"
    );
  }

  const envelopeSchema = apiResponseSchema(schema);
  const retryEnabled =
    options.retry ?? (method === "GET" && !contract.governed);

  return sendEnvelope<T>(contract, options, requestId, async (response) => {
    // HTTP 204 No Content: bodyless success.
    if (response.status === 204) {
      return syntheticSuccess<T>(
        contract,
        requestId,
        options.traceId,
        null as unknown as T,
        "no content"
      );
    }

    const raw = await response.text();
    if (raw.length === 0) {
      throw new ApiClientError({
        message: `empty response body for ${contract.id}`,
        status: response.status,
        code: "UPSTREAM_NON_JSON_RESPONSE",
        requestId,
        traceId: options.traceId ?? null,
      });
    }

    let parsedJson: unknown;
    try {
      parsedJson = JSON.parse(raw);
    } catch {
      throw new ApiClientError({
        message: `non-JSON response for ${contract.id}`,
        status: response.status,
        code: "UPSTREAM_NON_JSON_RESPONSE",
        requestId,
        traceId: options.traceId ?? null,
      });
    }

    const parsed = envelopeSchema.safeParse(parsedJson);
    if (!parsed.success) {
      throw new ApiClientError({
        message: `response contract validation failed for ${contract.id}`,
        status: response.status,
        code: "UPSTREAM_NON_JSON_RESPONSE",
        requestId,
        traceId: options.traceId ?? null,
        details: { issues: parsed.error.issues },
      });
    }

    return parsed.data as ApiResponse<T>;
  }, retryEnabled);
}

/** Build and send the fetch, returning whatever `read` extracts. */
async function sendRaw<T>(
  contract: RouteContract,
  options: RequestOptions,
  requestId: string,
  read: (response: Response) => Promise<T>
): Promise<T> {
  const url =
    resolveBaseUrl() +
    buildPath(contract.path, options.pathParams) +
    buildQuery(options.query);
  const headers = buildHeaders(contract, options, requestId);
  const response = await doFetch(contract, url, headers, options);
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ApiClientError({
      message: text || `HTTP ${response.status} for ${contract.id}`,
      status: response.status,
      code: inferCodeFromStatus(response.status),
      requestId,
      traceId: options.traceId ?? null,
    });
  }
  return read(response);
}

/** Send a JSON-envelope request, with optional single retry. */
async function sendEnvelope<T>(
  contract: RouteContract,
  options: RequestOptions,
  requestId: string,
  read: (response: Response) => Promise<ApiResponse<T>>,
  retryEnabled: boolean
): Promise<ApiResponse<T>> {
  const url =
    resolveBaseUrl() +
    buildPath(contract.path, options.pathParams) +
    buildQuery(options.query);
  const headers = buildHeaders(contract, options, requestId);

  let attempt = 0;
  // Bounded retry loop: at most one retry. The retry decision is made on the
  // HTTP status BEFORE the body is consumed, so a parse failure is never
  // retried (retrying cannot repair a non-JSON response) and the body is not
  // read twice on the same Response object.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    attempt += 1;
    let response: Response;
    try {
      response = await doFetch(contract, url, headers, options);
    } catch (cause) {
      if (
        retryEnabled &&
        attempt === 1 &&
        isTransientGetFailure(contract.method, 0)
      ) {
        await delay(100, options.signal).catch(() => {});
        continue;
      }
      throw new ApiClientError({
        message: `network error for ${contract.id}`,
        status: 0,
        code: "UPSTREAM_UNAVAILABLE",
        requestId,
        traceId: options.traceId ?? null,
        cause,
      });
    }

    // Decide whether to retry based on the HTTP status alone, before the body
    // is read. Drain the body to avoid resource leaks, then back off once.
    if (
      retryEnabled &&
      attempt === 1 &&
      isTransientGetFailure(contract.method, response.status)
    ) {
      await response.text().catch(() => {});
      await delay(100, options.signal).catch(() => {});
      continue;
    }

    // Commit to processing this response. Any failure from `read` is final.
    return read(response);
  }
}

/** Build the request header bag for one call. */
function buildHeaders(
  contract: RouteContract,
  options: RequestOptions,
  requestId: string
): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Request-Id": requestId,
    Accept: contract.returnsText ? "text/plain" : "application/json",
  };
  if (options.traceId) {
    headers["X-Trace-Id"] = options.traceId;
  }
  if (options.authToken) {
    headers.Authorization = `Bearer ${options.authToken}`;
  }
  if (contract.idempotencyRequired) {
    const key = options.idempotencyKey ?? safeRandomUuid();
    if (key) headers["Idempotency-Key"] = key;
  }
  // Double-submit CSRF: read the JS-readable csrf cookie and mirror it as a
  // header for non-safe methods under cookie auth.
  if (contract.method !== "GET") {
    const csrf = readCookie(CSRF_COOKIE_NAME);
    if (csrf) headers[CSRF_HEADER_NAME] = csrf;
  }
  if (options.body !== undefined && !contract.returnsText) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

/** Generate a UUID when the platform supports it. */
function safeRandomUuid(): string | null {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return null;
}

/** Issue the underlying fetch with credentials and the serialised body. */
async function doFetch(
  contract: RouteContract,
  url: string,
  headers: Record<string, string>,
  options: RequestOptions
): Promise<Response> {
  if (typeof globalThis.fetch !== "function") {
    throw new ApiClientError({
      message: "fetch is not available in this environment",
      status: 0,
      code: "UPSTREAM_UNAVAILABLE",
    });
  }
  const init: RequestInit = {
    method: contract.method,
    headers,
    credentials: "include",
    signal: options.signal,
  };
  if (options.body !== undefined && contract.method !== "GET") {
    init.body = JSON.stringify(options.body);
  }
  return globalThis.fetch(url, init);
}

/** Map an HTTP status to a stable error code for synthetic failures. */
function inferCodeFromStatus(status: number): string {
  if (status === 401) return "AUTHENTICATION_REQUIRED";
  if (status === 403) return "AUTHORIZATION_DENIED";
  if (status === 422) return "VALIDATION_FAILED";
  if (status === 429) return "RATE_LIMITED";
  if (status === 504) return "UPSTREAM_TIMEOUT";
  if (status === 409) return "IDEMPOTENCY_CONFLICT";
  if (status >= 500) return "UPSTREAM_UNAVAILABLE";
  return "INTERNAL_ERROR";
}

/**
 * Return only the `data` field of a validated successful response.
 *
 * Throws `ApiClientError` when the response is an error branch, so callers
 * that only want the payload get a typed value or a traceable failure.
 */
export function unwrapData<T>(response: ApiResponse<T>): T {
  if (isApiSuccessResponse(response)) {
    return response.data;
  }
  throw new ApiClientError({
    message: response.error.message,
    status: 0,
    code: response.error.code,
    requestId: response.error.request_id,
    traceId: response.error.trace_id,
    retryable: response.error.retryable,
    details: response.error.details,
  });
}
