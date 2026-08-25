import type { WidgetDefinition } from "../types";
import { systemStatusManifest } from "./manifest";
import { SystemStatusWidget } from "./Component";

export const systemStatusWidgetDefinition: WidgetDefinition = {
  descriptor: systemStatusManifest,
  component: SystemStatusWidget,
};

export { systemStatusManifest, SystemStatusWidget };
