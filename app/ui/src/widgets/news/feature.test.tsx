import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WIDGET_TYPES } from "../workspaces";

import { DEFAULT_NEWS_CONFIG, parseNewsConfig, resolveNewsConfig } from "./config";
import { NewsFeature } from "./feature";
import { NEWS_MANIFEST } from "./manifest";
import { NewsWidget } from "./NewsWidget";

void NewsWidget;

describe("FEAT-UI-29 D-UI artifacts — Phase 6", () => {
  it("declares the registered widget type and no backend capabilities", () => {
    expect(NEWS_MANIFEST.featureId).toBe("FEAT-UI-29");
    expect(NEWS_MANIFEST.widgetType).toBe("news");
    expect(WIDGET_TYPES).toContain("news");
    expect(NEWS_MANIFEST.requiredCapabilities).toEqual([]);
    expect(NEWS_MANIFEST.subscriptions).toEqual([]);
    expect(NEWS_MANIFEST.effects.network).toBe(true);
    expect(NEWS_MANIFEST.removal.persistedState).toBe("none");
  });

  it("rejects unknown configuration fields", () => {
    expect(() =>
      parseNewsConfig({ ...DEFAULT_NEWS_CONFIG, extra: 1 }),
    ).toThrow();
    expect(resolveNewsConfig(undefined)).toEqual(DEFAULT_NEWS_CONFIG);
    expect(resolveNewsConfig({ showHeader: false })).toEqual({
      ...DEFAULT_NEWS_CONFIG,
      showHeader: false,
    });
  });

  it("renders the explicit invalid-configuration state", () => {
    render(<NewsFeature config={{ defaultLanguage: "en", extra: true }} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
