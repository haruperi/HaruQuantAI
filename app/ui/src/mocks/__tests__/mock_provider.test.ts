import { describe, it, expect } from "vitest";
import { MockUiPresentationProvider } from "../mock_provider";

describe("MockUiPresentationProvider", () => {
  const provider = new MockUiPresentationProvider();

  it("is marked as dev-only", () => {
    expect(provider.isDevOnly).toBe(true);
  });

  it("returns ratified wire success envelopes for startWork", async () => {
    const res = await provider.startWork({
      request_id: "req-1",
      capability_snapshot_id: "snap-1",
      operation: "SHOW_HOME",
      schema_version: 1,
    });
    expect(res.outcome).toBe("SUCCESS");
    expect(res.recent_routes?.length).toBeGreaterThan(0);
  });

  it("returns ratified wire success envelopes for exploreResults with accessible data alternatives", async () => {
    const res = await provider.exploreResults({
      request_id: "req-2",
      capability_snapshot_id: "snap-1",
      operation: "SUMMARIZE",
      schema_version: 1,
    });
    expect(res.outcome).toBe("SUCCESS");
    expect(res.chart_alternative?.table_data?.length).toBeGreaterThan(0);
  });
});
