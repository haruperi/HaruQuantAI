/**
 * FEAT-UI-VIEW_COLLECTIONS typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const COLLECTION_GRID_MANIFEST: WidgetManifest & { readonly provides: readonly string[] } = {
  featureId: "FEAT-UI-VIEW_COLLECTIONS",
  widgetType: "collection-grid",
  widgetVersion: 1,
  provides: ["ui.collection-grid@1"] as const,
  title: "Collection Grid",
  description:
    "Accessible, virtualized tabular view over large typed collections with server-side " +
    "sorting, filtering, bounded selection tokens, and state preservation.",
  requiredCapabilities: ["ui.workspace-layout@1", "ui.typed-backend@1"],
  optionalCapabilities: ["plugins.render-panels@1"],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 800, height: 600 },
  minimumDimensions: { width: 400, height: 300 },
  commands: [
    { id: "collection-grid.select-all", title: "Select All", destructive: false },
    { id: "collection-grid.clear-selection", title: "Clear Selection", destructive: false },
    { id: "collection-grid.export-csv", title: "Export Current View", destructive: false },
  ],
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
      "Removing the collection grid panel unregisters its view contribution and releases " +
      "all virtualized buffers, scroll listeners, and timers. Backing domain jobs or datasets " +
      "remain unaffected.",
  },
};
