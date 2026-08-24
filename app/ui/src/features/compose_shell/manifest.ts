import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-COMPOSE_SHELL",
  name: "Compose Shell",
  description: "Capability-aware application shell and navigation",
  providesCapabilities: ["ui.compose-shell@1"],
  requiredCapabilities: [],
  optionalCapabilities: [
    "workspace.manage-workspaces@1",
    "workspace.build-diagnostics@1",
    "plugins.declare-manifests@1",
    "interfaces.serve-api-events@1",
  ],
};
