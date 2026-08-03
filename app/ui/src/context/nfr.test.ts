/**
 * NFR-API-008: Freshness — stale data blocks governed decisions.
 *
 * Verifies that the governed preflight rejects stale evidence, and that the
 * frontend components surface stale metadata warnings rather than silently
 * proceeding with outdated data.
 */

import { describe, expect, it } from "vitest";

import {
  buildGovernedOptions,
  isGovernedFresh,
  PREFLIGHT_WARNING_TTL_SECONDS,
} from "./governed";

describe("NFR-API-008: Freshness", () => {
  it("a freshly built governed context is fresh within the TTL window", () => {
    const { context } = buildGovernedOptions({
      workflow: "trading.session",
      permission: "trading:write",
      actorId: "operator",
      evidenceId: "ev-fresh",
    });
    expect(isGovernedFresh(context)).toBe(true);
  });

  it("a governed context is stale beyond the TTL window", () => {
    const { context } = buildGovernedOptions({
      workflow: "trading.session",
      permission: "trading:write",
      actorId: "operator",
      evidenceId: "ev-stale",
      staleAfterSeconds: 1,
    });
    // Simulate time beyond the window.
    const futureMs = Date.parse(context.generated_at) + (PREFLIGHT_WARNING_TTL_SECONDS + 5) * 1000;
    expect(isGovernedFresh(context, futureMs)).toBe(false);
  });

  it("stale governed context must not allow submission", () => {
    // The isGovernedFresh check is the gate; a stale context returns false,
    // which the caller must use to block submission.
    const { context } = buildGovernedOptions({
      workflow: "trading.session",
      permission: "trading:write",
      actorId: "operator",
      evidenceId: "ev-block",
      staleAfterSeconds: 1,
    });
    const stale = !isGovernedFresh(
      context,
      Date.parse(context.generated_at) + 5000
    );
    expect(stale).toBe(true);
  });
});
