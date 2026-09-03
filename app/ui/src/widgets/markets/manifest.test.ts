import { describe, expect, it } from "vitest";

import { WIDGET_TYPES } from "../workspaces";

import { MARKETS_MANIFEST } from "./manifest";

describe("FEAT-UI-02 manifest — D-UI §4.8", () => {
  it("declares the permanent owning feature and registered widget type", () => {
    expect(MARKETS_MANIFEST.featureId).toBe("FEAT-UI-02");
    expect(MARKETS_MANIFEST.widgetType).toBe("markets");
    expect(WIDGET_TYPES).toContain(MARKETS_MANIFEST.widgetType);
    expect(MARKETS_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares exact backend capability dependencies", () => {
    expect(MARKETS_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.observe-market-catalogue@1",
    ]);
    expect(MARKETS_MANIFEST.optionalCapabilities).toEqual([
      "interfaces.observe-market-data@1",
    ]);
  });

  it("declares sane placement and dimension metadata", () => {
    const { defaultDimensions, minimumDimensions } = MARKETS_MANIFEST;
    expect(defaultDimensions.width).toBeGreaterThanOrEqual(
      minimumDimensions.width,
    );
    expect(defaultDimensions.height).toBeGreaterThanOrEqual(
      minimumDimensions.height,
    );
  });

  it("declares the optional live-enrichment subscription only", () => {
    expect(MARKETS_MANIFEST.subscriptions).toHaveLength(1);
    expect(MARKETS_MANIFEST.subscriptions[0].capability).toBe(
      "interfaces.observe-market-data@1",
    );
    expect(MARKETS_MANIFEST.subscriptions[0].route).toBe(
      "/api/v1/data/snapshot-stream",
    );
  });

  it("declares effects, accessibility, and truthful removal semantics", () => {
    expect(MARKETS_MANIFEST.effects).toEqual({
      network: true,
      browserStorage: false,
      systemSettings: false,
    });
    expect(MARKETS_MANIFEST.accessibility.ariaLive).toBe("polite");
    expect(MARKETS_MANIFEST.removal.persistedState).toBe("none");
    expect(MARKETS_MANIFEST.removal.description).toContain("catalogue");
  });
});
