import type { WidgetTypeDescriptor } from "../../contracts/generated/ui";

export const activityLogManifest: WidgetTypeDescriptor = {
  widget_type: "activity_log",
  owning_feature: "FEAT-UI-MONITOR_WORK",
  type_version: 1,
  time_domains: ["LIVE"],
  schema_version: 1,
};
