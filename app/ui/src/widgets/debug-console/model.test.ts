import { describe, expect, it } from "vitest";
import { boundedDiagnosticWindow, diagnosticText } from "./model";

describe("debug console projection", () => {
  it("bounds local rows and marks truncation", () => {
    const entries = Array.from({ length: 4 }, (_, index) => ({
      sequence: index + 1,
      timestamp: "2026-09-09T00:00:00Z",
      owner: "test",
      severity: "INFO",
      code: "X",
      message: "safe",
      sampled: false,
    }));
    const result = boundedDiagnosticWindow(entries, 2);
    expect(result.truncated).toBe(true);
    expect(result.entries.map((entry) => entry.sequence)).toEqual([3, 4]);
  });

  it("renders attacker markup as text and bounds it", () => {
    const text = diagnosticText("<script>alert(1)</script>", 12);
    expect(text.startsWith("<script>aler")).toBe(true);
    expect(text).toContain("TRUNCATED");
  });
});
