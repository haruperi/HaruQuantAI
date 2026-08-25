import type { WidgetDefinition } from "../types";
import { homeManifest } from "./manifest";
import { HomeWidget } from "./Component";

export const homeWidgetDefinition: WidgetDefinition = {
  descriptor: homeManifest,
  component: HomeWidget,
};

export { homeManifest, HomeWidget };
