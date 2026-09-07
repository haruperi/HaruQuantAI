/** Lifecycle/removal evidence for FEAT-UI-14. */

import { describe, expect, it, vi } from "vitest";

import type { ApiResponse, StreamEvent } from "../contracts";
import {
  TypedBackendCapabilityRegistry,
  TypedBackendFeature,
} from "../feature";
import {
  TypedBackendLifecycle,
  type RequestTransport,
  type StreamTransport,
} from "../lifecycle";
import { ApiClientError } from "../request";
import { dataRoutes, healthRoutes } from "../routes";

function success(label: string): ApiResponse<{ label: string }> {
  return {
    status: "success",
    message: "ok",
    data: { label },
    error: null,
    metadata: {
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      request_id: `req-${label}`,
      route: "/api/v1/health/liveness",
      operation: "api.health.liveness",
      side_effect: "read",
      timestamp: "2026-09-08T00:00:00Z",
      stale: false,
      idempotency_replayed: false,
    },
  };
}

function event(sequence: number): StreamEvent {
  return {
    sequence,
    request_id: "req-stream",
    route: "/api/v1/data/snapshot-stream",
    event_type: "payload",
    timestamp: "2026-09-08T00:00:00Z",
    payload: { sequence },
    error: null,
    cursor: `cursor-${sequence}`,
    schema_version: 1,
  };
}

describe("FEAT-UI-14 lifecycle", () => {
  it("test_trc_call_typed_backend_002", async () => {
    const calls: AbortSignal[] = [];
    const requestTransport = (<T>(
      _contract: unknown,
      options: { signal?: AbortSignal },
    ): Promise<ApiResponse<T>> => {
      calls.push(options.signal as AbortSignal);
      const label = String(calls.length);
      return new Promise((resolve, reject) => {
        options.signal?.addEventListener(
          "abort",
          () =>
            reject(
              new ApiClientError({
                message: "stale",
                status: 0,
                code: "GOVERNED_REQUEST_STALE",
              }),
            ),
          { once: true },
        );
        if (label === "2") {
          resolve(success(label) as ApiResponse<T>);
        }
      });
    }) as RequestTransport;

    const streamCalls: Array<number | undefined> = [];
    const streamTransport = (async function* (
      _contract,
      options,
    ): AsyncIterable<StreamEvent> {
      streamCalls.push(options?.resumeAfter);
      if (streamCalls.length === 1) {
        yield event(4);
        throw new ApiClientError({
          message: "disconnect",
          status: 0,
          code: "UPSTREAM_UNAVAILABLE",
          retryable: true,
        });
      }
      yield event(5);
    }) as StreamTransport;

    const lifecycle = new TypedBackendLifecycle(
      requestTransport,
      streamTransport,
    );
    const stale = lifecycle.requestLatest("health", healthRoutes.liveness);
    const latest = lifecycle.requestLatest<{ label: string }>(
      "health",
      healthRoutes.liveness,
    );
    await expect(stale).rejects.toMatchObject({
      code: "GOVERNED_REQUEST_STALE",
    });
    await expect(latest).resolves.toMatchObject({ data: { label: "2" } });
    expect(calls[0].aborted).toBe(true);

    const observedA: number[] = [];
    const observedB: number[] = [];
    const first = lifecycle.subscribe(
      "market",
      dataRoutes.stream,
      {},
      (value) => observedA.push(value.sequence),
    );
    const second = lifecycle.subscribe(
      "market",
      dataRoutes.stream,
      {},
      (value) => observedB.push(value.sequence),
    );
    await Promise.all([first.done, second.done]);
    expect(streamCalls).toEqual([undefined, 4]);
    expect(observedA).toEqual([4, 5]);
    expect(observedB).toEqual([4, 5]);
    first.dispose();
    second.dispose();
    await lifecycle.dispose();
    expect(lifecycle.isDisposed).toBe(true);
  });

  it("test_trc_call_typed_backend_nfr_001", async () => {
    const registry = new TypedBackendCapabilityRegistry();
    const unrelated = Object.freeze({ capability: "ui.unrelated@1" });
    registry.register("ui.unrelated@1", unrelated);
    const feature = new TypedBackendFeature();
    const withdraw = registry.registerTypedBackend(feature);
    expect(registry.requireTypedBackend()).toBe(feature);

    await withdraw();
    await withdraw();
    expect(() => registry.requireTypedBackend()).toThrowError(
      expect.objectContaining({ code: "DEPENDENCY_UNAVAILABLE" }),
    );
    expect(registry.resolve("ui.unrelated@1")).toBe(unrelated);
    expect(feature.lifecycle.isDisposed).toBe(true);
    expect(vi.isMockFunction(registry.resolve("ui.unrelated@1"))).toBe(false);
  });
});
