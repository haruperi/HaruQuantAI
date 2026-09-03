/**
 * System settings widget barrel (FEAT-UI-13).
 */

export { SYSTEM_SETTINGS_MANIFEST } from "./manifest";
export {
  DEFAULT_SYSTEM_SETTINGS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseSystemSettingsConfig,
  resolveSystemSettingsConfig,
  systemSettingsConfigSchema,
  type SystemSettingsConfig,
} from "./config";
export {
  SystemSettingsFeature,
  type SystemSettingsFeatureProps,
} from "./feature";
export { SystemSettingsModal } from "./SystemSettingsModal";
export type { SystemSettingsModalProps } from "./contracts";
