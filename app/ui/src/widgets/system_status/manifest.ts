import type { WidgetTypeDescriptor } from "../../contracts/generated/ui";

export const systemStatusManifest: WidgetTypeDescriptor = {
  widget_type: "system_status",
  owning_feature: "FEAT-UI-COMPOSE_SHELL",
  type_version: 1,
  time_domains: ["LIVE"],
  schema_version: 1,
};
