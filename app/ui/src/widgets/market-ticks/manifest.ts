/**
 * FEAT-UI-25 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: the manifest declares identity, dependencies, placement,
 * effects, accessibility, and removal semantics. It is consumed by the
 * UI composition boundary and never performs registration at import
 * time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const MARKET_TICKS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-25",
  widgetType: "marketTicks",
  widgetVersion: 1,
  title: "Market Ticks",
  description:
    "Like-for-like MT5 market tick diagnostic table over the ratified " +
    "observation stream, owning presentation and reconnection only.",
  requiredCapabilities: ["interfaces.observe-market-data@1"],
  optionalCapabilities: ["data.stream-market-events@1"],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 560, height: 320 },
  minimumDimensions: { width: 360, height: 200 },
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
    systemSettings: true,
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
      "and from saved workspaces; the workspace renders an explicit " +
      "missing-widget placeholder and the backend observation boundary " +
      "is unaffected.",
  },
};
