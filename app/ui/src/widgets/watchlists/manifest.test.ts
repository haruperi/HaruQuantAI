import { describe, expect, it } from "vitest";

import { WIDGET_TYPES } from "../workspaces";

import { WATCHLISTS_MANIFEST } from "./manifest";

describe("FEAT-UI-03 manifest — D-UI §4.8", () => {
  it("declares the permanent owning feature and registered widget type", () => {
    expect(WATCHLISTS_MANIFEST.featureId).toBe("FEAT-UI-03");
    expect(WATCHLISTS_MANIFEST.widgetType).toBe("watchlist");
    expect(WIDGET_TYPES).toContain(WATCHLISTS_MANIFEST.widgetType);
    expect(WATCHLISTS_MANIFEST.widgetVersion).toBe(1);
  });

  it("declares the exact backend capability dependency and no streams", () => {
    expect(WATCHLISTS_MANIFEST.requiredCapabilities).toEqual([
      "interfaces.operate-watchlists@1",
    ]);
    expect(WATCHLISTS_MANIFEST.optionalCapabilities).toEqual([]);
    expect(WATCHLISTS_MANIFEST.subscriptions).toEqual([]);
  });

  it("declares sane placement and dimension metadata", () => {
    const { defaultDimensions, minimumDimensions } = WATCHLISTS_MANIFEST;
    expect(defaultDimensions.width).toBeGreaterThanOrEqual(
      minimumDimensions.width,
    );
    expect(defaultDimensions.height).toBeGreaterThanOrEqual(
      minimumDimensions.height,
    );
  });

  it("declares effects, accessibility, and truthful removal semantics", () => {
    expect(WATCHLISTS_MANIFEST.effects).toEqual({
      network: true,
      browserStorage: false,
      systemSettings: false,
    });
    expect(WATCHLISTS_MANIFEST.accessibility.ariaLive).toBe("polite");
    expect(WATCHLISTS_MANIFEST.removal.persistedState).toBe("none");
    expect(WATCHLISTS_MANIFEST.removal.description).toContain(
      "backend watchlist store",
    );
  });
});
