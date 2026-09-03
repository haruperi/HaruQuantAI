/** Public UI seam for Watchlists (FEAT-UI-03). */

export {
  DEFAULT_WATCHLISTS_CONFIG,
  watchlistsConfigSchema,
  parseWatchlistsConfig,
  resolveWatchlistsConfig,
  PERSISTED_STATE_SCHEMA_VERSION,
  type WatchlistsConfig,
} from './config';
export { WatchlistsFeature } from './feature';
export { WATCHLISTS_MANIFEST } from './manifest';
export { WatchlistWidget } from './WatchlistWidget';
