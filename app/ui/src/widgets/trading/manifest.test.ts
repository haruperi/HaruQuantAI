import { describe, expect, it } from "vitest";

import { TRADING_MANIFEST } from "./manifest";

describe("TRADING_MANIFEST (FEAT-UI-06)", () => {
  it("declares the permanent feature identity and type", () => {
    expect(TRADING_MANIFEST.featureId).toBe("FEAT-UI-06");
    expect(TRADING_MANIFEST.widgetType).toBe("trading");
    expect(TRADING_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares the transport capability dependency", () => {
    expect(TRADING_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.operate-trading@1",
    ]);
  });

  it("declares commands and subscriptions", () => {
    expect(TRADING_MANIFEST.commands.map((c) => c.id)).toContain(
      "trading.submit-order",
    );
    expect(TRADING_MANIFEST.subscriptions.map((s) => s.capability)).toContain(
      "interfaces.operate-trading@1",
    );
  });
});
