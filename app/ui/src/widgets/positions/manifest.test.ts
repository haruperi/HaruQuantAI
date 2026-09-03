import { describe, expect, it } from "vitest";

import { POSITIONS_MANIFEST } from "./manifest";

describe("POSITIONS_MANIFEST (FEAT-UI-09)", () => {
  it("declares the permanent feature identity and type", () => {
    expect(POSITIONS_MANIFEST.featureId).toBe("FEAT-UI-09");
    expect(POSITIONS_MANIFEST.widgetType).toBe("positions");
    expect(POSITIONS_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares transport capability and commands", () => {
    expect(POSITIONS_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.operate-trading@1",
    ]);
    expect(POSITIONS_MANIFEST.commands.map((c) => c.id)).toContain(
      "trading.close-position",
    );
    expect(POSITIONS_MANIFEST.commands.map((c) => c.id)).toContain(
      "trading.cancel-order",
    );
  });
});
