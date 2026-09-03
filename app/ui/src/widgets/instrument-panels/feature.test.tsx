import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WIDGET_TYPES } from "../workspaces";

vi.mock("./OptionsGridWidget", () => ({
  OptionsGridWidget: ({ symbol }: { symbol?: string }) => (
    <div>options-stub:{symbol}</div>
  ),
}));

import { InstrumentPanelsFeature } from "./feature";
import { INSTRUMENT_PANELS_MANIFEST } from "./manifest";

describe("FEAT-UI-19 D-UI artifacts — Phase 6", () => {
  it("declares the registered widget type and no backend capabilities", () => {
    expect(INSTRUMENT_PANELS_MANIFEST.featureId).toBe("FEAT-UI-19");
    expect(INSTRUMENT_PANELS_MANIFEST.widgetType).toBe("optionsGrid");
    expect(WIDGET_TYPES).toContain("optionsGrid");
    expect(INSTRUMENT_PANELS_MANIFEST.requiredCapabilities).toEqual([]);
    expect(INSTRUMENT_PANELS_MANIFEST.subscriptions).toEqual([]);
    expect(INSTRUMENT_PANELS_MANIFEST.effects.network).toBe(false);
    expect(INSTRUMENT_PANELS_MANIFEST.removal.persistedState).toBe("none");
  });

  it("forwards the symbol to the focused presentation", () => {
    const { container } = render(<InstrumentPanelsFeature symbol="ESU5" />);
    expect(container.textContent).toContain("options-stub:ESU5");
  });
});
