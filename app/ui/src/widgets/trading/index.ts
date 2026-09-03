/**
 * Trading widget barrel (FEAT-UI-06).
 */

export { TRADING_MANIFEST } from "./manifest";
export {
  DEFAULT_TRADING_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parseTradingConfig,
  resolveTradingConfig,
  tradingConfigSchema,
  type TradingConfig,
} from "./config";
export { TradingFeature, type TradingFeatureProps } from "./feature";
export { TradingWidget, type TradingWidgetProps } from "./TradingWidget";
export { OrderTicket, type OrderTicketProps } from "./OrderTicket";
