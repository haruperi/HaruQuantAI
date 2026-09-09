import { describe, expect, it } from "vitest";
import { controlLabel, outcomeLabel, progressLabel, type RunMonitorRow } from "./model";

const row: RunMonitorRow = {
  jobId: "j1",
  infrastructureState: "COMPLETED",
  domainOutcome: "REFUSED",
  desiredControl: "CANCEL",
  acknowledgedControl: "NONE",
  workerActive: false,
  completedUnits: null,
  totalUnits: null,
  exactProgress: false,
  attemptId: "a1",
  fence: 1,
  stale: false,
};

describe("run monitor semantics", () => {
  it("does not present completed refusal as domain success", () => {
    expect(outcomeLabel(row)).toContain("Refused");
  });
  it("keeps requested control separate from acknowledgement", () => {
    expect(controlLabel(row)).toContain("awaiting acknowledgement");
  });
  it("keeps unknown totals indeterminate", () => {
    expect(progressLabel(row).determinate).toBe(false);
  });
});
