/**
 * SSE transport primitive for stream routes.
 *
 * Stream routes (`response_contract = StreamEvent.v1`) serve Server-Sent
 * Events rather than the JSON envelope. This module provides the low-level
 * SSE reader: it opens a `fetch` connection, parses the `text/event-stream`
 * frames, and yields validated `StreamEvent` objects. Higher-level gap/reconnect
 * behaviour lives in `context/streams.ts` (`consumeStream`, FR-API-045).
 */

import { streamEventSchema, type StreamEvent } from "./contracts";
import type { RouteContract } from "./routes";
import { ApiClientError, type QueryValue, type RequestOptions } from "./request";

/** Options accepted by `openStream` (a subset of `RequestOptions`). */
export interface StreamTransportOptions {
  /** Query parameters. */
  query?: Record<string, QueryValue>;
  /** Explicit request id; generated when omitted. */
  requestId?: string;
  /** Explicit trace id forwarded to the gateway. */
  traceId?: string;
  /** Bearer token for service-account transport. */
  authToken?: string;
  /** Sequence to resume after (sent as the `Last-Event-ID` header). */
  resumeAfter?: number;
  /** Abort the stream via this signal. */
  signal?: AbortSignal;
}

/** Resolve the gateway base URL (mirrors `request.ts resolveBaseUrl`). */
function resolveBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (url.trim().length > 0) return url.replace(/\/+$/, "");
  return "";
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

/** Generate a request identifier. */
function generateRequestId(): string {
  const bytes = new Uint8Array(12);
  globalThis.crypto.getRandomValues(bytes);
  const alphabet =
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  let id = "";
  for (const byte of bytes) id += alphabet[byte % alphabet.length];
  return `req_${id}`;
}

/**
 * Open an authenticated SSE stream and yield validated events.
 *
 * Uses the browser `fetch` streaming response with credentials so the
 * `hq_session` cookie authorises the connection. Each SSE frame is parsed and
 * validated against `streamEventSchema`; malformed frames raise
 * `ApiClientError`.
 *
 * Args:
 *   contract: A stream route contract (e.g. `dataRoutes.stream`).
 *   options: Stream transport options.
 *
 * Yields:
 *   Validated `StreamEvent` objects in arrival order.
 *
 * Raises:
 *   ApiClientError: On network, HTTP, or frame-validation failure.
 */
export async function* openStream(
  contract: RouteContract,
  options: StreamTransportOptions = {}
): AsyncIterable<StreamEvent> {
  if (!contract.stream) {
    throw new ApiClientError({
      message: `${contract.id} is not a stream route`,
      status: 0,
      code: "VALIDATION_FAILED",
    });
  }
  if (typeof globalThis.fetch !== "function") {
    throw new ApiClientError({
      message: "fetch is not available in this environment",
      status: 0,
      code: "UPSTREAM_UNAVAILABLE",
    });
  }

  const url = resolveBaseUrl() + contract.path + buildQuery(options.query);
  const requestId = options.requestId ?? generateRequestId();
  const headers: Record<string, string> = {
    "X-Request-Id": requestId,
    Accept: "text/event-stream",
  };
  if (options.traceId) headers["X-Trace-Id"] = options.traceId;
  if (options.authToken) headers.Authorization = `Bearer ${options.authToken}`;
  if (options.resumeAfter !== undefined) {
    headers["Last-Event-ID"] = String(options.resumeAfter);
  }

  let response: Response;
  try {
    response = await globalThis.fetch(url, {
      method: "GET",
      headers,
      credentials: "include",
      signal: options.signal,
    });
  } catch (cause) {
    throw new ApiClientError({
      message: `network error opening stream ${contract.id}`,
      status: 0,
      code: "UPSTREAM_UNAVAILABLE",
      requestId,
      traceId: options.traceId ?? null,
      cause,
    });
  }

  if (!response.ok || response.body === null) {
    const text = await response.text().catch(() => "");
    throw new ApiClientError({
      message: text || `HTTP ${response.status} opening stream ${contract.id}`,
      status: response.status,
      code: response.status === 401 ? "AUTHENTICATION_REQUIRED" : "UPSTREAM_UNAVAILABLE",
      requestId,
      traceId: options.traceId ?? null,
    });
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE frames are separated by a blank line. Process complete frames.
      let separatorIndex = buffer.indexOf("\n\n");
      while (separatorIndex !== -1) {
        const frame = buffer.slice(0, separatorIndex);
        buffer = buffer.slice(separatorIndex + 2);
        const event = parseFrame(frame);
        if (event) yield event;
        separatorIndex = buffer.indexOf("\n\n");
      }
    }
    // Flush any trailing frame.
    if (buffer.trim().length > 0) {
      const event = parseFrame(buffer);
      if (event) yield event;
    }
  } catch (cause) {
    if (cause instanceof ApiClientError) throw cause;
    throw new ApiClientError({
      message: `stream read error for ${contract.id}`,
      status: 0,
      code: "UPSTREAM_UNAVAILABLE",
      requestId,
      traceId: options.traceId ?? null,
      cause,
    });
  } finally {
    try {
      reader.releaseLock();
    } catch {
      // Best-effort release.
    }
  }
}

/** Parse one SSE frame into a validated `StreamEvent`, or null to skip. */
function parseFrame(frame: string): StreamEvent | null {
  let dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
    // `id:` and `event:` lines are also present but the full envelope is in
    // `data`, so they are not needed for parsing.
  }
  if (dataLines.length === 0) return null;
  const raw = dataLines.join("\n");
  let parsedJson: unknown;
  try {
    parsedJson = JSON.parse(raw);
  } catch {
    throw new ApiClientError({
      message: "non-JSON SSE data frame",
      status: 0,
      code: "UPSTREAM_NON_JSON_RESPONSE",
    });
  }
  const parsed = streamEventSchema.safeParse(parsedJson);
  if (!parsed.success) {
    throw new ApiClientError({
      message: "SSE event contract validation failed",
      status: 0,
      code: "UPSTREAM_NON_JSON_RESPONSE",
      details: { issues: parsed.error.issues },
    });
  }
  return parsed.data;
}

/** Re-exported type for callers that import from the stream module. */
export type { RequestOptions };
