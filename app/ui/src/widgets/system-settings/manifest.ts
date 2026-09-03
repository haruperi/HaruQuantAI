/**
 * FEAT-UI-13 typed widget manifest (D-UI pipeline §4.8).
 *
 * Data only: declares identity, dependencies, placement, effects,
 * accessibility, and removal semantics. Never registers at import time.
 */

import type { WidgetManifest } from "../../types/widget-manifest";

export const SYSTEM_SETTINGS_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-13",
  widgetType: "systemSettings",
  widgetVersion: 1,
  title: "System Settings",
  description:
    "System-wide configuration, environment mode selection, credentials manager, " +
    "and audit history viewer.",
  requiredCapabilities: ["interfaces.serve-api-events@1"],
  optionalCapabilities: ["interfaces.manage-system-settings@1"],
  placement: { defaultPanel: "center" },
  defaultDimensions: { width: 720, height: 540 },
  minimumDimensions: { width: 400, height: 320 },
  commands: [],
  subscriptions: [],
  effects: {
    network: true,
    browserStorage: false,
    systemSettings: true,
  },
  accessibility: {
    ariaLive: "polite",
    landmarkRole: "dialog",
    keyboardNavigable: true,
  },
  removal: {
    persistedState: "none",
    description:
      "Removing the widget modal or view hides configuration UI; stored haruquantai.db " +
      "database settings and audit entries are unchanged.",
  },
};
