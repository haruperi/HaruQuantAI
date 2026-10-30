import { describe, expect, test } from "vitest";
import { MemoryFlushLabel } from "../../../workspaces/ai/memoryFlushLabel";

describe("MemoryFlushLabel (WO-19-01)", () => {
  test("memory flush labels", () => {
    // (false, 5) = off
    expect(MemoryFlushLabel.describe(false, 5)).toBe("off");

    // (true, -1) = off
    expect(MemoryFlushLabel.describe(true, -1)).toBe("off");

    // (true, 0) = after every turn
    expect(MemoryFlushLabel.describe(true, 0)).toBe("after every turn");

    // (true, 5) = every 5 min at most
    expect(MemoryFlushLabel.describe(true, 5)).toBe("every 5 min at most");

    // (true, 1.5) = every 1.5 min at most
    expect(MemoryFlushLabel.describe(true, 1.5)).toBe("every 1.5 min at most");

    // (true, NaN) = every NaN min at most
    expect(MemoryFlushLabel.describe(true, NaN)).toBe("every NaN min at most");
  });
});
