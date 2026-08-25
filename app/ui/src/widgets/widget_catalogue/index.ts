import type { WidgetDefinition } from "../types";
import { widgetCatalogueManifest } from "./manifest";
import { WidgetCatalogueWidget } from "./Component";

export const widgetCatalogueWidgetDefinition: WidgetDefinition = {
  descriptor: widgetCatalogueManifest,
  component: WidgetCatalogueWidget,
};

export { widgetCatalogueManifest, WidgetCatalogueWidget };
