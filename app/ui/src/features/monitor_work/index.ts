export { SPEC, SPEC as monitorWorkManifest } from "./manifest";
export {
  MonitorWorkFeature,
  createFeature,
  MonitorWorkClientProvider,
  useMonitorWorkClient,
  useActivitySnapshot,
  type MonitorWorkClientProviderProps,
  type MonitorWorkFeatureOptions,
} from "./feature";
export {
  detectGaps,
  ingestSnapshot,
  isStale,
  DEFAULT_BUFFER_CAP,
  type ActivityEvent,
  type ActivityGapMarker,
  type ActivityTruncationMarker,
  type ActivityEventEntry,
  type ActivityEntry,
  type ActivitySnapshot,
  type IngestResult,
} from "./activity_model";
