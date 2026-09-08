import { describe, expect, it } from "vitest";

import { currentSessionScopeSignal, rotateSessionScope } from "@/clients/session-scope";

describe("FEAT-UI-SESSION_ACCESS lifecycle", () => {
  it("repeated scope rotation leaves one current live signal", () => {
    const stale: AbortSignal[] = [];
    for (let index = 0; index < 100; index += 1) {
      stale.push(currentSessionScopeSignal());
      rotateSessionScope(`cycle-${index}`);
    }
    expect(stale.every((signal) => signal.aborted)).toBe(true);
    expect(currentSessionScopeSignal().aborted).toBe(false);
  });
});
