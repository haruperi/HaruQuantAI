import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-START_WORK",
  name: "Start Work",
  description: "Home landing view with capability-aware entry points and product news",
  providesCapabilities: ["ui.start-work@1"],
  requiredCapabilities: [],
  optionalCapabilities: ["workspace.manage-workspaces@1"],
};
