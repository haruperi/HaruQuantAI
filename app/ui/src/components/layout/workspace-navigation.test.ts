import { describe, expect, it } from "vitest";

import {
  buildNavigationCommands,
  isNavigationActivationKey,
} from "./workspace-navigation";

describe("workspace navigation", () => {
  it("disables only commands whose required capability is absent", () => {
    const commands = buildNavigationCommands(
      [
        { id: "jobs", label: "Jobs", requiredCapabilities: ["interfaces.operate-jobs@1"] },
        { id: "settings", label: "Settings", requiredCapabilities: ["interfaces.operate-settings@1"] },
      ],
      new Set(["interfaces.operate-settings@1"]),
    );
    expect(commands[0]).toMatchObject({ available: false });
    expect(commands[0]?.reason).toContain("interfaces.operate-jobs@1");
    expect(commands[1]).toMatchObject({ available: true, reason: null });
  });

  it("uses button-equivalent keyboard activation", () => {
    expect(isNavigationActivationKey("Enter")).toBe(true);
    expect(isNavigationActivationKey(" ")).toBe(true);
    expect(isNavigationActivationKey("Escape")).toBe(false);
  });
});
