export { SPEC } from "./manifest";
export {
  parseManageLayoutsConfig,
  type ManageLayoutsConfig,
} from "./config";
export {
  MANAGE_LAYOUTS_TEMPLATES,
  buildTemplateManager,
  findManageLayoutsTemplate,
} from "./templates";
export {
  createLayoutPersistence,
  truncatePlacements,
  type LayoutPersistence,
  type RestoreResult,
  type RestoreDiagnostic,
} from "./persistence";
export {
  ViewScaleProvider,
  useViewScale,
  ScaleControls,
  clampScale,
  MIN_SCALE,
  MAX_SCALE,
} from "./scale";
export {
  ManageLayoutsFeature,
  createFeature,
  ManageLayoutsClientProvider,
  useManageLayoutsClient,
  createTemplateRequestBus,
  type LayoutController,
  type TemplateRequestBus,
} from "./feature";
