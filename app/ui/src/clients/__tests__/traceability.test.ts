/** Requirement-level evidence for FEAT-UI-14. */

import { describe, expect, it } from "vitest";
import { z } from "zod";

import { apiResponseSchema, streamEventSchema } from "../contracts";
import { TYPED_BACKEND_MANIFEST } from "../manifest";

function metadata(): Record<string, unknown> {
  return {
    contract_version: "v1",
    schema_id: "api.metadata.v1",
    request_id: "req-trace",
    route: "/api/v1/health/liveness",
    operation: "api.health.liveness",
    timestamp: "2026-09-08T00:00:00Z",
    schema_version: 1,
  };
}

describe("FEAT-UI-14 traceability", () => {
  it("test_trc_call_typed_backend_001", () => {
    const schema = apiResponseSchema(
      z.object({ status: z.literal("healthy") }).strict(),
    );
    const valid = schema.parse({
      status: "success",
      message: "ok",
      data: { status: "healthy" },
      error: null,
      metadata: metadata(),
      schema_version: 1,
    });
    expect(valid.status).toBe("success");

    expect(() =>
      schema.parse({
        status: "success",
        message: "ok",
        data: { status: "invented", unchecked: true },
        error: null,
        metadata: metadata(),
        schema_version: 1,
      }),
    ).toThrow();
    expect(() =>
      schema.parse({
        status: "success",
        message: "ok",
        data: { status: "healthy" },
        error: null,
        metadata: { ...metadata(), drift: "unknown" },
        schema_version: 1,
      }),
    ).toThrow();
    expect(() =>
      streamEventSchema.parse({
        sequence: 1,
        request_id: "req-stream",
        route: "/api/v1/data/snapshot-stream",
        event_type: "error",
        timestamp: "2026-09-08T00:00:00Z",
        payload: null,
        error: { message: "backpressure" },
        cursor: "cursor-1",
        schema_version: 1,
        unchecked: true,
      }),
    ).toThrow();
  });

  it("test_trc_call_typed_backend_002", () => {
    expect(TYPED_BACKEND_MANIFEST).toMatchObject({
      featureId: "FEAT-UI-14",
      provides: ["ui.typed-backend@1"],
      requiredCapabilities: [],
      configKeys: [],
    });
  });
});
