/**
 * Unit tests for the stream consumer (FR-UI-009).
 *
 * The SSE transport is faked by stubbing `globalThis.fetch` with a ReadableStream
 * that emits canned SSE frames, so no network is touched.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { consumeStream, StreamGapError } from "./streams";
import { ApiClientError } from "@/clients";
import { dataRoutes } from "@/clients/routes";

/** Encode one SSE frame carrying a StreamEvent-shaped data payload. */
function frame(event: Record<string, unknown>): Uint8Array {
  const data = JSON.stringify(event);
  return new TextEncoder().encode(`id: ${event.sequence}\nevent: ${event.event_type}\ndata: ${data}\n\n`);
}

/** Build a fake fetch returning a ReadableStream of the given frames. */
function fakeFetchSse(frames: Uint8Array[]) {
  return vi.fn(async () => {
    const stream = new ReadableStream({
      start(controller) {
        for (const f of frames) controller.enqueue(f);
        controller.close();
      },
    });
    return new Response(stream, {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    });
  }) as unknown as typeof fetch;
}

function baseEvent(sequence: number, overrides: Partial<Record<string, unknown>> = {}): Record<string, unknown> {
  return {
    sequence,
    request_id: "req_s",
    trace_id: null,
    route: "/api/v1/data/stream",
    event_type: "payload",
    timestamp: "2026-08-03T12:00:00Z",
    payload: { price: 1.1 + sequence * 0.01 },
    error: null,
    cursor: String(sequence),
    ...overrides,
  };
}

const realFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = realFetch;
  vi.restoreAllMocks();
});

describe("consumeStream — FR-UI-009", () => {
  beforeEach(() => {
    // Keep NEXT_PUBLIC_API_URL empty so resolveBaseUrl returns "" (same-origin).
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it("yields ordered payload events and ignores heartbeats", async () => {
    globalThis.fetch = fakeFetchSse([
      frame(baseEvent(0, { event_type: "heartbeat", payload: null })),
      frame(baseEvent(1)),
      frame(baseEvent(2)),
    ]);

    const events: number[] = [];
    for await (const event of consumeStream(dataRoutes.stream, {
      query: { symbol: "EURUSD", mode: "ticks", timeframe: "M1" },
    })) {
      events.push(event.sequence);
    }
    expect(events).toEqual([1, 2]);
  });

  it("terminal error from the gateway raises ApiClientError", async () => {
    globalThis.fetch = fakeFetchSse([
      frame(baseEvent(0, { event_type: "error", error: "backpressure", payload: null })),
    ]);
    await expect(
      (async () => {
        for await (const _ of consumeStream(dataRoutes.stream, {
          query: { symbol: "EURUSD", mode: "ticks", timeframe: "M1" },
        })) {
          void _;
        }
      })()
    ).rejects.toBeInstanceOf(ApiClientError);
  });

  it("gapTriggersRefresh: a sequence gap raises StreamGapError after retries", async () => {
    globalThis.fetch = fakeFetchSse([
      frame(baseEvent(1)),
      // Gap: next is 5, skipping 2..4.
      frame(baseEvent(5)),
    ]);
    await expect(
      (async () => {
        for await (const _ of consumeStream(dataRoutes.stream, {
          query: { symbol: "EURUSD", mode: "ticks", timeframe: "M1" },
          maxReconnects: 0,
          reconnectDelayMs: 1,
        })) {
          void _;
        }
      })()
    ).rejects.toBeInstanceOf(StreamGapError);
  });

  it("onGap is called with the gap info before reconnect", async () => {
    let captured: { last: number | null; next: number | null } | null = null;
    globalThis.fetch = fakeFetchSse([
      frame(baseEvent(1)),
      frame(baseEvent(5)),
    ]);
    try {
      for await (const _ of consumeStream(dataRoutes.stream, {
        query: { symbol: "EURUSD", mode: "ticks", timeframe: "M1" },
        maxReconnects: 0,
        reconnectDelayMs: 1,
        onGap: (info) => {
          captured = { last: info.lastSequence, next: info.nextSequence };
        },
      })) {
        void _;
      }
    } catch {
      // StreamGapError expected after onGap runs with no reconnects left.
    }
    expect(captured).toEqual({ last: 1, next: 5 });
  });

  it("rejects a non-stream route contract", async () => {
    await expect(
      (async () => {
        // dataRoutes.symbols is not a stream route.
        for await (const _ of consumeStream(
          { ...dataRoutes.symbols } as never,
          { query: { symbol: "EURUSD", mode: "ticks", timeframe: "M1" } }
        )) {
          void _;
        }
      })()
    ).rejects.toBeInstanceOf(ApiClientError);
  });
});
