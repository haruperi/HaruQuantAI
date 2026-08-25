import type { WidgetDefinition } from "../types";
import { settingsManifest } from "./manifest";
import { SettingsWidget } from "./Component";

export { settingsManifest } from "./manifest";
export { SettingsWidget } from "./Component";

export const settingsWidgetDefinition: WidgetDefinition = {
  descriptor: settingsManifest,
  component: SettingsWidget,
};
