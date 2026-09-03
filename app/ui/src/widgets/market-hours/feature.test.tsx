import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WIDGET_TYPES } from "../workspaces";

vi.mock("./MarketHoursWidget", () => ({
  MarketHoursWidget: () => <div>market-hours-widget-stub</div>,
}));

import { MarketHoursFeature } from "./feature";
import { MARKET_HOURS_MANIFEST } from "./manifest";

describe("FEAT-UI-30 D-UI artifacts — Phase 6", () => {
  it("declares the registered widget type and no backend capabilities", () => {
    expect(MARKET_HOURS_MANIFEST.featureId).toBe("FEAT-UI-30");
    expect(MARKET_HOURS_MANIFEST.widgetType).toBe("market-hours");
    expect(WIDGET_TYPES).toContain("market-hours");
    expect(MARKET_HOURS_MANIFEST.requiredCapabilities).toEqual([]);
    expect(MARKET_HOURS_MANIFEST.subscriptions).toEqual([]);
    expect(MARKET_HOURS_MANIFEST.effects.network).toBe(true);
    expect(MARKET_HOURS_MANIFEST.removal.persistedState).toBe("none");
  });

  it("renders the focused presentation through the adapter", () => {
    const { container } = render(<MarketHoursFeature />);
    expect(container.textContent).toContain("market-hours-widget-stub");
  });
});
