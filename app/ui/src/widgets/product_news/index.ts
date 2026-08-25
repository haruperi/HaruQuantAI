import type { WidgetDefinition } from "../types";
import { productNewsManifest } from "./manifest";
import { ProductNewsWidget } from "./Component";

export const productNewsWidgetDefinition: WidgetDefinition = {
  descriptor: productNewsManifest,
  component: ProductNewsWidget,
};

export { productNewsManifest, ProductNewsWidget };
