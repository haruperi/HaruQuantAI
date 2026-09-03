import { describe, expect, it } from "vitest";

import { PRICE_LADDER_MANIFEST } from "./manifest";

describe("PRICE_LADDER_MANIFEST (FEAT-UI-05)", () => {
  it("declares the permanent feature identity and type", () => {
    expect(PRICE_LADDER_MANIFEST.featureId).toBe("FEAT-UI-05");
    expect(PRICE_LADDER_MANIFEST.widgetType).toBe("priceLadder");
    expect(PRICE_LADDER_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares the transport capability dependency", () => {
    expect(PRICE_LADDER_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.operate-trading@1",
    ]);
  });

  it("declares commands and subscriptions", () => {
    expect(PRICE_LADDER_MANIFEST.commands.map((c) => c.id)).toContain(
      "trading.submit-order",
    );
    expect(PRICE_LADDER_MANIFEST.subscriptions.map((s) => s.capability)).toContain(
      "data.stream-depth-events@1",
    );
  });
});
