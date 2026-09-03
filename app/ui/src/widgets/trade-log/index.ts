/**
 * Trade log widget barrel (FEAT-UI-08).
 */

export { TRADE_LOG_MANIFEST } from "./manifest";
export {
  DEFAULT_TRADE_LOG_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseTradeLogConfig,
  resolveTradeLogConfig,
  tradeLogConfigSchema,
  type TradeLogConfig,
} from "./config";
export { TradeLogFeature, type TradeLogFeatureProps } from "./feature";
export {
  TradeLogWidget,
  type TradeLogWidgetProps,
} from "./TradeLogWidget";
