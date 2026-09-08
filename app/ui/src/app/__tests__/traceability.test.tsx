import { describe, expect, it } from "vitest";

import { currentSessionScopeGeneration, currentSessionScopeSignal, rotateSessionScope } from "@/clients/session-scope";

describe("FEAT-UI-SESSION_ACCESS traceability", () => {
  it("aborts stale account-scoped work and advances generation", () => {
    const before = currentSessionScopeGeneration();
    const signal = currentSessionScopeSignal();
    expect(signal.aborted).toBe(false);
    rotateSessionScope("test-account-change");
    expect(signal.aborted).toBe(true);
    expect(currentSessionScopeGeneration()).toBe(before + 1);
    expect(currentSessionScopeSignal().aborted).toBe(false);
  });
});
