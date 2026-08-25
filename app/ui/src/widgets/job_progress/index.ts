import type { WidgetDefinition } from "../types";
import { jobProgressManifest } from "./manifest";
import { JobProgressWidget } from "./Component";

export { jobProgressManifest } from "./manifest";
export { JobProgressWidget } from "./Component";

export const jobProgressWidgetDefinition: WidgetDefinition = {
  descriptor: jobProgressManifest,
  component: JobProgressWidget,
};
