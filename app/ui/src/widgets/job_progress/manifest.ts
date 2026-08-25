import type { WidgetTypeDescriptor } from "../../contracts/generated/ui";

export const jobProgressManifest: WidgetTypeDescriptor = {
  widget_type: "job_progress",
  owning_feature: "FEAT-UI-MONITOR_WORK",
  type_version: 1,
  time_domains: ["LIVE"],
  schema_version: 1,
};
