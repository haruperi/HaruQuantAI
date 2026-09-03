/**
 * FEAT-UI-02 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const MARKETS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-02",
  widgetType: "markets",
  widgetVersion: 1,
  title: "Markets",
  description:
    "Categorized tradable market directory over the ratified catalogue " +
    "browse boundary, with live snapshot enrichment when available.",
  requiredCapabilities: ["interfaces.observe-market-catalogue@1"],
  optionalCapabilities: ["interfaces.observe-market-data@1"],
  placement: { defaultPanel: "left" },
  defaultDimensions: { width: 480, height: 560 },
  minimumDimensions: { width: 360, height: 320 },
  commands: [],
  subscriptions: [
    {
      kind: "sse",
      route: "/api/v1/data/snapshot-stream",
      contract: "StreamEvent",
      contractVersion: "v1",
      capability: "interfaces.observe-market-data@1",
    },
  ],
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
      "missing-widget state and the backend catalogue boundary is " +
      "unaffected.",
  },
};
