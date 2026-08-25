import type { WidgetDefinition } from "../types";
import { workspaceTemplatesManifest } from "./manifest";
import { WorkspaceTemplatesWidget } from "./Component";

export const workspaceTemplatesWidgetDefinition: WidgetDefinition = {
  descriptor: workspaceTemplatesManifest,
  component: WorkspaceTemplatesWidget,
};

export { workspaceTemplatesManifest, WorkspaceTemplatesWidget };
