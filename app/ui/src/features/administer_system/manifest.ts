import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-ADMINISTER_SYSTEM",
  name: "Administer System",
  description:
    "Preferences, appearance, client configuration, licensing, updates, and capability administration",
  providesCapabilities: ["ui.administer-system@1"],
  requiredCapabilities: [],
  optionalCapabilities: [],
};
