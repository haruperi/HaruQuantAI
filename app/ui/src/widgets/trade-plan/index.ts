/**
 * Trade plan widget barrel (FEAT-UI-10).
 */

export { TRADE_PLAN_MANIFEST } from "./manifest";
export {
  DEFAULT_TRADE_PLAN_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseTradePlanConfig,
  resolveTradePlanConfig,
  tradePlanConfigSchema,
  type TradePlanConfig,
} from "./config";
export { TradePlanFeature, type TradePlanFeatureProps } from "./feature";
export { TradePlanWidget, type TradePlanWidgetProps } from "./TradePlanWidget";
