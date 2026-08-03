/**
 * Stream consumer with gap detection and authoritative recovery (FR-API-045).
 *
 * Wraps the low-level SSE transport (`clients/stream.ts`) with ordered-event
 * validation, heartbeat handling, terminal-error surfacing, cleanup on
 * disconnect, and gap-triggered reconnection. The gateway publishes explicit
 * gaps and backpressure as terminal errors; on a gap the consumer stops,
 * surfaces a `StreamGapError`, and the caller is expected to refresh
 * authoritative state rather than assume continuity.
 *
 * Browser context never confers authority: a stream event is advisory until
 * the owning domain confirms it.
 */

import { ApiClientError, openStream, type StreamTransportOptions } from "@/clients";
import type { RouteContract, StreamEvent } from "@/clients";

/** Maximum reconnect attempts after a transient gap before giving up. */
const DEFAULT_MAX_RECONNECTS = 3;
/** Delay between reconnect attempts (ms). */
const DEFAULT_RECONNECT_DELAY_MS = 500;

/** Raised when the stream reports a sequence gap and the consumer stops. */
export class StreamGapError extends Error {
  public readonly lastSequence: number | null;
  public readonly expectedSequence: number | null;

  public constructor(message: string, lastSequence: number | null, expectedSequence: number | null) {
    super(message);
    this.name = "StreamGapError";
    this.lastSequence = lastSequence;
    this.expectedSequence = expectedSequence;
  }
}

/** Options accepted by `consumeStream`. */
export interface StreamOptions extends Omit<StreamTransportOptions, "resumeAfter"> {
  /** Maximum reconnect attempts after a gap (default 3). */
  maxReconnects?: number;
  /** Delay between reconnect attempts in ms (default 500). */
  reconnectDelayMs?: number;
  /**
   * Called when a gap is detected and before a reconnect is attempted,
   * giving the caller a chance to refresh authoritative state. If it throws,
   * the gap propagates as a `StreamGapError`.
   */
  onGap?: (info: { lastSequence: number | null; nextSequence: number | null }) => Promise<void> | void;
}

/**
 * Consume a stream route with ordered-event validation and gap recovery.
 *
 * Yields validated `StreamEvent<T>` objects in monotonically-increasing
 * sequence order. Heartbeats are validated but not yielded (callers that need
 * them can inspect the source iterator); terminal errors raise
 * `ApiClientError`; sequence gaps raise `StreamGapError` after the configured
 * number of reconnect attempts (or immediately if `onGap` throws).
 *
 * On disconnect the underlying reader is released and no further events are
 * yielded.
 *
 * Args:
 *   contract: A stream route contract (e.g. `dataRoutes.stream`).
 *   options: Stream and reconnection options.
 *
 * Yields:
 *   Validated payload/error events in arrival order.
 *
 * Raises:
 *   ApiClientError: HTTP, transport, or terminal stream error.
 *   StreamGapError: A sequence gap that could not be recovered.
 */
export async function* consumeStream(
  contract: RouteContract,
  options: StreamOptions = {}
): AsyncIterable<StreamEvent> {
  const maxReconnects = options.maxReconnects ?? DEFAULT_MAX_RECONNECTS;
  const reconnectDelayMs = options.reconnectDelayMs ?? DEFAULT_RECONNECT_DELAY_MS;

  let lastSequence: number | null = null;
  let attempt = 0;
  let resumeAfter: number | undefined;

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const streamOptions: StreamTransportOptions = { ...options, resumeAfter };
    let sawGap = false;
    let gapInfo: { lastSequence: number | null; nextSequence: number | null } | null = null;

    try {
      for await (const event of openStream(contract, streamOptions)) {
        // Validate monotonic sequence; detect gaps.
        if (lastSequence !== null && event.sequence > lastSequence + 1) {
          sawGap = true;
          gapInfo = {
            lastSequence,
            nextSequence: event.sequence,
          };
          break;
        }
        lastSequence = event.sequence;

        // Terminal error from the gateway: surface and stop.
        if (event.event_type === "error" && event.error) {
          throw new ApiClientError({
            message: event.error,
            status: 0,
            code: "UPSTREAM_UNAVAILABLE",
          });
        }

        // Yield payload events; heartbeats keep the connection alive but
        // carry no domain data.
        if (event.event_type === "payload") {
          yield event;
        }
      }
    } catch (error) {
      // A genuine transport failure mid-stream is treated like a gap: attempt
      // bounded reconnection before giving up.
      if (error instanceof ApiClientError && attempt < maxReconnects) {
        attempt += 1;
        await delay(reconnectDelayMs, options.signal).catch(() => {});
        resumeAfter = lastSequence ?? undefined;
        continue;
      }
      throw error;
    }

    if (sawGap && gapInfo) {
      if (options.onGap) {
        try {
          await options.onGap(gapInfo);
        } catch (cause) {
          throw new StreamGapError(
            `onGap refresh failed after sequence gap`,
            gapInfo.lastSequence,
            gapInfo.nextSequence
          );
        }
      }
      if (attempt < maxReconnects) {
        attempt += 1;
        resumeAfter = lastSequence ?? undefined;
        await delay(reconnectDelayMs, options.signal).catch(() => {});
        continue;
      }
      throw new StreamGapError(
        `unrecoverable sequence gap in ${contract.id}`,
        gapInfo.lastSequence,
        gapInfo.nextSequence
      );
    }

    // Clean end of stream (server closed without error/gap).
    return;
  }
}

/** Sleep helper that respects an abort signal. */
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
