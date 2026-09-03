/**
 * Price ladder widget barrel (FEAT-UI-05).
 */

export { PRICE_LADDER_MANIFEST } from "./manifest";
export {
  DEFAULT_PRICE_LADDER_CONFIG,
  PERSISTED_STATE_SCHEMA_VERSION,
  parsePriceLadderConfig,
  resolvePriceLadderConfig,
  priceLadderConfigSchema,
  type PriceLadderConfig,
} from "./config";
export {
  PriceLadderFeature,
  type PriceLadderFeatureProps,
} from "./feature";
export { PriceLadderWidget } from "./PriceLadderWidget";
export { useDepthStream } from "./useDepthStream";
