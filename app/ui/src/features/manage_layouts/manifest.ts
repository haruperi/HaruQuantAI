import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-MANAGE_LAYOUTS",
  name: "Manage Layouts",
  description: "Tabs, panels, splitters, overlays, and saved view state",
  providesCapabilities: ["ui.manage-layouts@1"],
  requiredCapabilities: [],
  optionalCapabilities: ["workspace.manage-workspaces@1"],
};
