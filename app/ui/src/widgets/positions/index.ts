/**
 * Positions & Orders widget barrel (FEAT-UI-09).
 */

export { POSITIONS_MANIFEST } from "./manifest";
export {
  DEFAULT_POSITIONS_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parsePositionsConfig,
  resolvePositionsConfig,
  positionsConfigSchema,
  type PositionsConfig,
} from "./config";
export { PositionsFeature, type PositionsFeatureProps } from "./feature";
export {
  PositionsWidget,
  type PositionsWidgetProps,
} from "./PositionsWidget";
