/**
 * FEAT-UI-03 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const WATCHLISTS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-03",
  widgetType: "watchlist",
  widgetVersion: 1,
  title: "Watchlists",
  description:
    "Account-owned named watchlists with symbol curation over the " +
    "ratified watchlist CRUD boundary.",
  requiredCapabilities: ["interfaces.operate-watchlists@1"],
  optionalCapabilities: [],
  placement: { defaultPanel: "left" },
  defaultDimensions: { width: 420, height: 520 },
  minimumDimensions: { width: 320, height: 280 },
  commands: [],
  subscriptions: [],
  effects: {
    network: true,
    browserStorage: false,
    systemSettings: false,
  },
  accessibility: {
    ariaLive: "polite",
    landmarkRole: "region",
    keyboardNavigable: true,
  },
  removal: {
    persistedState: "none",
    description:
      "Removing the widget removes its contribution from the catalogue " +
      "and saved workspaces; the workspace renders the explicit " +
      "missing-widget state, the backend watchlist store and its data " +
      "are unaffected, and the Markets widget degrades to the full " +
      "directory view.",
  },
};
