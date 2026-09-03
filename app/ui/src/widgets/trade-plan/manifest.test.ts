import { describe, expect, it } from "vitest";

import { TRADE_PLAN_MANIFEST } from "./manifest";

describe("TRADE_PLAN_MANIFEST (FEAT-UI-10)", () => {
  it("declares the permanent feature identity and type", () => {
    expect(TRADE_PLAN_MANIFEST.featureId).toBe("FEAT-UI-10");
    expect(TRADE_PLAN_MANIFEST.widgetType).toBe("tradePlan");
    expect(TRADE_PLAN_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares optional capabilities", () => {
    expect(TRADE_PLAN_MANIFEST.optionalCapabilities).toEqual([
      "trading.manage-trade-plans@1",
    ]);
  });
});
