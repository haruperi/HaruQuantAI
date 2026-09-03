/** Public UI seam for Markets (FEAT-UI-02). */

export {
  DEFAULT_MARKETS_CONFIG,
  marketsConfigSchema,
  parseMarketsConfig,
  resolveMarketsConfig,
  PERSISTED_STATE_SCHEMA_VERSION,
  type MarketsConfig,
} from './config';
export { MarketsFeature } from './feature';
export { MARKETS_MANIFEST } from './manifest';
export { MarketsWidget } from './MarketsWidget';
