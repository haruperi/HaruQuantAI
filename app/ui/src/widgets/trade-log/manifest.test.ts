import { describe, expect, it } from "vitest";

import { TRADE_LOG_MANIFEST } from "./manifest";

describe("TRADE_LOG_MANIFEST (FEAT-UI-08)", () => {
  it("declares the permanent feature identity and type", () => {
    expect(TRADE_LOG_MANIFEST.featureId).toBe("FEAT-UI-08");
    expect(TRADE_LOG_MANIFEST.widgetType).toBe("tradeLog");
    expect(TRADE_LOG_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares optional capabilities", () => {
    expect(TRADE_LOG_MANIFEST.optionalCapabilities).toEqual([
      "interfaces.operate-trading@1",
    ]);
  });
});
