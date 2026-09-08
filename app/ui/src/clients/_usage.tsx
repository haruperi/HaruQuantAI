/** Bounded offline executable TSX usage for FEAT-UI-TYPED_BACKEND. */

import assert from "node:assert/strict";
import { z } from "zod";

import { apiResponseSchema, type ApiResponse, type StreamEvent } from "./contracts";
import {
  TypedBackendCapabilityRegistry,
  TypedBackendFeature,
} from "./feature";
import {
  TypedBackendLifecycle,
  type RequestTransport,
  type StreamTransport,
} from "./lifecycle";
import { ApiClientError } from "./request";
import { dataRoutes, healthRoutes } from "./routes";

function response(label: string): ApiResponse<{ label: string }> {
  return {
    status: "success",
    message: "ok",
    data: { label },
    error: null,
    metadata: {
      request_id: `req-${label}`,
      route: "/api/v1/health/liveness",
      operation: "api.health.liveness",
      timestamp: "2026-09-08T00:00:00Z",
      contract_version: "v1",
      schema_id: "api.metadata.v1",
      side_effect: "read",
      stale: false,
      idempotency_replayed: false,
    },
  };
}

function streamEvent(sequence: number): StreamEvent {
  return {
    sequence,
    request_id: "req-usage-stream",
    route: "/api/v1/data/snapshot-stream",
    event_type: "payload",
    timestamp: "2026-09-08T00:00:00Z",
    payload: { source: "offline-fixture" },
    error: null,
    cursor: `cursor-${sequence}`,
    schema_version: 1,
  };
}

async function main(): Promise<void> {
  const envelope = apiResponseSchema(
    z.object({ label: z.string().min(1) }).strict(),
  );
  assert.equal(
    envelope.parse({
      ...response("validated"),
      schema_version: 1,
      metadata: { ...response("validated").metadata, schema_version: 1 },
    }).status,
    "success",
  );
  assert.equal(
    envelope.safeParse({ ...response("invalid"), unchecked: true }).success,
    false,
  );

  const requestSignals: AbortSignal[] = [];
  const requestTransport = (<T,>(
    _contract: unknown,
    options: { signal?: AbortSignal },
  ): Promise<ApiResponse<T>> => {
    requestSignals.push(options.signal as AbortSignal);
    const ordinal = requestSignals.length;
    if (ordinal === 2) {
      return Promise.resolve(response("latest") as ApiResponse<T>);
    }
    return new Promise((_resolve, reject) => {
      options.signal?.addEventListener(
        "abort",
        () =>
          reject(
            new ApiClientError({
              message: "superseded",
              status: 0,
              code: "GOVERNED_REQUEST_STALE",
            }),
          ),
        { once: true },
      );
    });
  }) as RequestTransport;

  const resumes: Array<number | undefined> = [];
  const streamTransport = (async function* (
    _contract,
    options,
  ): AsyncIterable<StreamEvent> {
    resumes.push(options?.resumeAfter);
    if (resumes.length === 1) {
      yield streamEvent(10);
      throw new ApiClientError({
        message: "offline disconnect",
        status: 0,
        code: "UPSTREAM_UNAVAILABLE",
        retryable: true,
      });
    }
    yield streamEvent(11);
  }) as StreamTransport;

  const lifecycle = new TypedBackendLifecycle(requestTransport, streamTransport);
  const stale = lifecycle.requestLatest("usage.health", healthRoutes.liveness);
  const latest = lifecycle.requestLatest<{ label: string }>(
    "usage.health",
    healthRoutes.liveness,
  );
  await assert.rejects(stale, { code: "GOVERNED_REQUEST_STALE" });
  assert.equal((await latest).data?.label, "latest");

  const firstEvents: number[] = [];
  const secondEvents: number[] = [];
  const first = lifecycle.subscribe(
    "usage.market",
    dataRoutes.stream,
    {},
    (event) => firstEvents.push(event.sequence),
  );
  const second = lifecycle.subscribe(
    "usage.market",
    dataRoutes.stream,
    {},
    (event) => secondEvents.push(event.sequence),
  );
  await first.done;
  assert.deepEqual(resumes, [undefined, 10]);
  assert.deepEqual(firstEvents, [10, 11]);
  assert.deepEqual(secondEvents, [10, 11]);
  first.dispose();
  second.dispose();

  const registry = new TypedBackendCapabilityRegistry();
  const unrelated = Object.freeze({ state: "retained" });
  registry.register("ui.unrelated@1", unrelated);
  const feature = new TypedBackendFeature(lifecycle);
  const withdraw = registry.registerTypedBackend(feature);
  assert.equal(registry.requireTypedBackend(), feature);
  await withdraw();
  await assert.rejects(
    async () => registry.requireTypedBackend(),
    { code: "DEPENDENCY_UNAVAILABLE" },
  );
  assert.equal(registry.resolve("ui.unrelated@1"), unrelated);

  console.log(
    "FEAT-UI-TYPED_BACKEND usage passed: typed schema rejection, latest-only request, shared cursor resume, exact withdrawal, and cleanup verified offline.",
  );
}

await main();
