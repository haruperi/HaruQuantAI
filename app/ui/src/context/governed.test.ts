/**
 * Unit tests for governed-write preflight (FR-API-044).
 */

import { describe, expect, it } from "vitest";

import {
  buildGovernedOptions,
  isGovernedFresh,
  PREFLIGHT_WARNING_TTL_SECONDS,
} from "./governed";
import { GovernedPreflightError } from "./errors";

const complete = {
  workflow: "operator.approvals",
  permission: "ops:approve",
  actorId: "u_1",
  evidenceId: "ev_1",
};

describe("buildGovernedOptions — FR-API-044", () => {
  it("builds options with an auto-generated idempotency key for a complete context", () => {
    const { options, context } = buildGovernedOptions(complete);
    expect(options.idempotencyKey).toEqual(expect.any(String));
    expect(options.idempotencyKey!.length).toBeGreaterThan(0);
    expect(context.workflow).toBe("operator.approvals");
    expect(context.actor_id).toBe("u_1");
    expect(context.stale_after_seconds).toBe(PREFLIGHT_WARNING_TTL_SECONDS);
  });

  it("honours an explicit idempotency key when supplied", () => {
    const { context } = buildGovernedOptions({
      ...complete,
      idempotencyKey: "explicit-key",
    });
    expect(context.idempotency_key).toBe("explicit-key");
  });

  it("missingApprovalBlocksFetch: rejects a missing required field", () => {
    const { approvalId, ...rest } = {
      ...complete,
      approvalId: "a_1",
    };
    void approvalId;
    // Remove actorId to trigger the missing-field path.
    const incomplete = { ...rest, actorId: "" };
    expect(() => buildGovernedOptions(incomplete)).toThrow(GovernedPreflightError);
    expect(() => buildGovernedOptions(incomplete)).toThrow(/actorId/);
  });

  it("rejects every required field when empty", () => {
    for (const field of ["workflow", "permission", "actorId", "evidenceId"] as const) {
      const bad = { ...complete, [field]: " " };
      expect(() => buildGovernedOptions(bad)).toThrow(GovernedPreflightError);
    }
  });

  it("rejects a non-positive staleAfterSeconds", () => {
    expect(() =>
      buildGovernedOptions({ ...complete, staleAfterSeconds: 0 })
    ).toThrow(GovernedPreflightError);
  });

  it("freshContextPasses: isGovernedFresh is true for a just-built context", () => {
    const { context } = buildGovernedOptions(complete);
    expect(isGovernedFresh(context)).toBe(true);
  });

  it("staleContextBlocks: isGovernedFresh is false beyond the window", () => {
    const { context } = buildGovernedOptions({ ...complete, staleAfterSeconds: 1 });
    const future = Date.parse(context.generated_at) + 2000;
    expect(isGovernedFresh(context, future)).toBe(false);
  });
});
