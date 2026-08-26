import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-ENSURE_ACCESS",
  name: "Ensure Access",
  description:
    "Keyboard, nonvisual, focus management, scale, and safety accessibility guarantees",
  providesCapabilities: ["ui.ensure-access@1"],
  requiredCapabilities: ["ui.compose-shell@1"],
  optionalCapabilities: [],
};
