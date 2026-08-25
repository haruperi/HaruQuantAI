import type { UiFeatureManifest } from "../../runtime/composition_bridge";

export const SPEC: UiFeatureManifest = {
  featureId: "FEAT-UI-EDIT_INPUTS",
  name: "Edit Inputs",
  description: "Forms, pickers, tables, validation, drafts, and confirmations",
  providesCapabilities: ["ui.edit-inputs@1"],
  requiredCapabilities: [],
  optionalCapabilities: [],
};
