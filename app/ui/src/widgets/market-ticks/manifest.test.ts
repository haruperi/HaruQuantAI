import { describe, expect, it } from "vitest";

import { WIDGET_TYPES } from "../workspaces";

import { MARKET_TICKS_MANIFEST } from "./manifest";

describe("FEAT-UI-25 manifest — D-UI §4.8", () => {
  it("declares the permanent owning feature and registered widget type", () => {
    expect(MARKET_TICKS_MANIFEST.featureId).toBe("FEAT-UI-25");
    expect(MARKET_TICKS_MANIFEST.widgetType).toBe("marketTicks");
    expect(WIDGET_TYPES).toContain(MARKET_TICKS_MANIFEST.widgetType);
    expect(MARKET_TICKS_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares exact backend capability dependencies", () => {
    expect(MARKET_TICKS_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.observe-market-data@1",
    ]);
    expect(MARKET_TICKS_MANIFEST.optionalCapabilities).toEqual([
      "data.stream-market-events@1",
    ]);
  });

  it("declares sane placement and dimension metadata", () => {
    const { defaultDimensions, minimumDimensions } = MARKET_TICKS_MANIFEST;
    expect(defaultDimensions.width).toBeGreaterThanOrEqual(
      minimumDimensions.width,
    );
    expect(defaultDimensions.height).toBeGreaterThanOrEqual(
      minimumDimensions.height,
    );
  });

  it("declares the adopted SSE subscription contract", () => {
    expect(MARKET_TICKS_MANIFEST.subscriptions).toEqual([
      {
        kind: "sse",
        route: "/api/v1/data/snapshot-stream",
        contract: "StreamEvent",
        contractVersion: "v1",
        capability: "interfaces.observe-market-data@1",
      },
    ]);
  });

  it("declares effects, accessibility, and truthful removal semantics", () => {
    expect(MARKET_TICKS_MANIFEST.effects).toEqual({
      network: true,
      browserStorage: false,
      systemSettings: true,
    });
    expect(MARKET_TICKS_MANIFEST.accessibility.ariaLive).toBe("polite");
    expect(MARKET_TICKS_MANIFEST.removal.persistedState).toBe("none");
    expect(MARKET_TICKS_MANIFEST.removal.description).toContain("backend");
  });
});
