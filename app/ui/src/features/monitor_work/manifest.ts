import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-MONITOR_WORK",
  name: "Monitor Work",
  description: "Job progress, activity logging, structured failures, and monitoring presentation",
  providesCapabilities: ["ui.monitor-work@1"],
  requiredCapabilities: [],
  optionalCapabilities: [],
};
