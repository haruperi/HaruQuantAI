import { describe, expect, it } from "vitest";
import { diffSettings, isSettingsDirty, settingsFailureMessage } from "./state";

describe("system settings draft state", () => {
  it("computes a deterministic diff", () => {
    expect(diffSettings({ A: "1", B: "2" }, { A: "3", B: "2" })).toEqual([
      { key: "A", before: "1", after: "3" },
    ]);
    expect(isSettingsDirty({ A: "1" }, { A: "1" })).toBe(false);
  });

  it("keeps conflicts explicit", () => {
    expect(settingsFailureMessage("SETTINGS_CONFLICT")).toContain("changed elsewhere");
  });
});
