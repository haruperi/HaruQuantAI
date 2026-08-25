import type { WidgetDefinition } from "../types";
import { activityLogManifest } from "./manifest";
import { ActivityLogWidget } from "./Component";

export { activityLogManifest } from "./manifest";
export { ActivityLogWidget } from "./Component";

export const activityLogWidgetDefinition: WidgetDefinition = {
  descriptor: activityLogManifest,
  component: ActivityLogWidget,
};
