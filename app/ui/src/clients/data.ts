/**
 * Data client for symbol discovery, the market stream, governed dataset
 * preparation, and external import (6 operations).
 *
 * The Data domain owns the exact row shape; the gateway returns it opaquely.
 * The client validates a minimal structural contract (opaque rows) and leaves
 * field-level interpretation to consumers.
 */

import { z } from "zod";

import type { ApiResponse, StreamEvent } from "./contracts";
import { dataRoutes } from "./routes";
import { request, type RequestOptions, type QueryValue } from "./request";
import { openStream, type StreamTransportOptions } from "./stream";

/** One symbol row. Data-owned; field set may grow, so rows are open records. */
export const symbolRowSchema = z.record(z.string(), z.unknown());
export type SymbolRow = z.infer<typeof symbolRowSchema>;

/**
 * Symbol discovery page.
 *
 * Data returns provider-native symbol *names* here, not rows — this route is
 * the cheap read (no quote or OHLC evidence), which is what makes walking the
 * whole broker universe affordable. `next_cursor` is opaque and provider-owned;
 * pass it back verbatim to get the following page.
 */
export const symbolPageSchema = z.object({
  source_id: z.string().min(1),
  items: z.array(z.string()),
  limit: z.number().int().min(1),
  next_cursor: z.string().nullable().nullish(),
  revision: z.string().min(1),
  request_id: z.string().min(1),
});
export type SymbolPage = z.infer<typeof symbolPageSchema>;

/** One bounded Data feature summary. */
export const dataCapabilitySchema = z.object({
  feature_id: z.string(),
  name: z.string(),
  summary: z.string(),
  availability: z.literal("available"),
});
export type DataCapability = z.infer<typeof dataCapabilitySchema>;

/** Complete Data feature catalogue returned by the authenticated gateway. */
export const dataCapabilitiesSchema = z.object({
  capabilities: z.array(dataCapabilitySchema).length(14),
});
export type DataCapabilities = z.infer<typeof dataCapabilitiesSchema>;

/** List the complete Data capability surface (requires `data:read`). */
export function capabilities(
  options?: RequestOptions
): Promise<ApiResponse<DataCapabilities>> {
  return request<DataCapabilities>(dataRoutes.capabilities, {
    schema: dataCapabilitiesSchema,
    ...options,
  });
}

/** One market-data series reference row (Data-owned summary). */
export const marketSeriesRowSchema = z.object({
  series_id: z.number().int(),
  symbol: z.string().min(1),
  instrument: z.string().nullable(),
  document: z.string().nullable(),
  broker_id: z.number().int().nullable(),
  usymbol: z.string().nullable(),
  timeframe: z.string().nullable(),
  timezone: z.string().nullable(),
  date_from: z.number().int().nullable(),
  date_to: z.number().int().nullable(),
  total_days: z.number().int().nullable(),
  row_count: z.number().int().nullable(),
  decimals: z.number().int().nullable(),
  source: z.number().int().nullable(),
  /** Bar timestamp reference; invariant "start_of_bar" for stored series. */
  bar_type: z.literal("start_of_bar"),
  data_type: z.number().int().nullable(),
  /** Legacy visibility flag inverted: 0 means hidden from workspaces. */
  show: z.number().int().nullable(),
  remove_weekends: z.number().int().nullable(),
});
export type MarketSeriesRow = z.infer<typeof marketSeriesRowSchema>;

/** Bounded market-data series catalogue page. */
export const marketSeriesSchema = z.object({
  series: z.array(marketSeriesRowSchema),
});
export type MarketSeries = z.infer<typeof marketSeriesSchema>;

/** Query parameters for the market series catalogue. */
export interface MarketSeriesQuery {
  /** Page size 1..200; defaults to the backend `API_DEFAULT_PAGE_SIZE`. */
  limit?: number;
}

/** List the market-data series reference catalogue (requires `data:read`). */
export function marketSeries(
  params: MarketSeriesQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<MarketSeries>> {
  const query: Record<string, QueryValue> = {};
  if (params.limit !== undefined) query.limit = params.limit;
  return request<MarketSeries>(dataRoutes.series, {
    schema: marketSeriesSchema,
    query,
    ...options,
  });
}

/** One instrument specification row (Data-owned summary). */
export const instrumentRowSchema = z.object({
  instrument: z.string().min(1),
  description: z.string().nullable(),
  broker_id: z.number().int().nullable(),
  point_value: z.number().nullable(),
  tick_size: z.number().nullable(),
  tick_step: z.number().nullable(),
  default_spread: z.number().nullable(),
  default_slippage: z.number().nullable(),
  data_type: z.number().int().nullable(),
  order_size_multiplier: z.number().nullable(),
  order_size_step: z.number().nullable(),
});
export type InstrumentRow = z.infer<typeof instrumentRowSchema>;

/** Bounded instrument specification page. */
export const instrumentsSchema = z.object({
  instruments: z.array(instrumentRowSchema),
});
export type Instruments = z.infer<typeof instrumentsSchema>;

/** List instrument specifications (requires `data:read`). */
export function instruments(
  options?: RequestOptions
): Promise<ApiResponse<Instruments>> {
  return request<Instruments>(dataRoutes.instruments, {
    schema: instrumentsSchema,
    ...options,
  });
}

/** One broker profile row with its customized-instrument count. */
export const brokerRowSchema = z.object({
  broker_id: z.number().int().nullable(),
  name: z.string().nullable(),
  description: z.string().nullable(),
  postfix: z.string().nullable(),
  timezone: z.string().nullable(),
  customized_instruments: z.number().int().nullable(),
});
export type BrokerRow = z.infer<typeof brokerRowSchema>;

/** Bounded broker profile page. */
export const brokersSchema = z.object({
  brokers: z.array(brokerRowSchema),
});
export type Brokers = z.infer<typeof brokersSchema>;

/** List broker profiles (requires `data:read`). */
export function brokers(options?: RequestOptions): Promise<ApiResponse<Brokers>> {
  return request<Brokers>(dataRoutes.brokers, {
    schema: brokersSchema,
    ...options,
  });
}

/** Editable governed payload for one series and its instrument spec. */
export interface SeriesUpdateBody {
  symbol: string;
  instrument: string;
  broker_id?: number | null;
  timeframe?: string | null;
  timezone?: string | null;
  date_from?: number | null;
  date_to?: number | null;
  data_type?: number | null;
  decimals?: number | null;
  source?: number | null;
  row_count?: number | null;
  remove_weekends: number;
  show: number;
  description?: string | null;
  point_value?: number | null;
  tick_size?: number | null;
  tick_step?: number | null;
  default_spread?: number | null;
  default_slippage?: number | null;
  min_distance?: number | null;
  order_size_multiplier?: number | null;
  order_size_step?: number | null;
}

/** Updated series summary returned by the governed edit. */
export const updatedSeriesSchema = z.object({
  series_id: z.number().int(),
  symbol: z.string().min(1),
  instrument: z.string().min(1),
  bar_type: z.literal("start_of_bar"),
});
export type UpdatedSeries = z.infer<typeof updatedSeriesSchema>;

/** Governed edit of one series and its linked instrument (requires `data:write`). */
export function updateSeries(
  seriesId: number,
  body: SeriesUpdateBody,
  options?: RequestOptions
): Promise<ApiResponse<UpdatedSeries>> {
  return request<UpdatedSeries>(dataRoutes.updateSeries, {
    schema: updatedSeriesSchema,
    body,
    pathParams: { series_id: seriesId },
    ...options,
  });
}

/** Editable governed payload for one instrument specification. */
export interface InstrumentUpdateBody {
  description?: string | null;
  point_value?: number | null;
  tick_size?: number | null;
  tick_step?: number | null;
  default_spread?: number | null;
  default_slippage?: number | null;
  min_distance?: number | null;
  order_size_multiplier?: number | null;
  order_size_step?: number | null;
}

/** Governed edit of one instrument specification (requires `data:write`). */
export function updateInstrument(
  instrumentId: string,
  body: InstrumentUpdateBody,
  options?: RequestOptions
): Promise<ApiResponse<InstrumentSpec>> {
  return request<InstrumentSpec>(dataRoutes.updateInstrument, {
    schema: instrumentSpecSchema,
    body,
    pathParams: { instrument: instrumentId },
    ...options,
  });
}

/** Full instrument specification including the raw swap rule text. */
export const instrumentSpecSchema = z.object({
  instrument: z.string().min(1),
  description: z.string().nullable(),
  broker_id: z.number().int().nullable(),
  point_value: z.number().nullable(),
  tick_size: z.number().nullable(),
  tick_step: z.number().nullable(),
  default_spread: z.number().nullable(),
  default_slippage: z.number().nullable(),
  data_type: z.number().int().nullable(),
  order_size_multiplier: z.number().nullable(),
  order_size_step: z.number().nullable(),
  min_distance: z.number().nullable(),
  swap: z.string().nullable(),
});
export type InstrumentSpec = z.infer<typeof instrumentSpecSchema>;

/** Read one full instrument specification (requires `data:read`). */
export function instrument(
  instrumentId: string,
  options?: RequestOptions
): Promise<ApiResponse<InstrumentSpec>> {
  return request<InstrumentSpec>(dataRoutes.instrument, {
    schema: instrumentSpecSchema,
    pathParams: { instrument: instrumentId },
    ...options,
  });
}

/** Query parameters for symbol discovery. */
export interface SymbolsQuery {
  source_id?: string;
  query?: string;
  cursor?: string;
  /** Page size 1..200; defaults to the backend `API_DEFAULT_PAGE_SIZE`. */
  limit?: number;
}

/** Discover symbols (requires `data:read`). */
export function symbols(
  params: SymbolsQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<SymbolPage>> {
  const query: Record<string, QueryValue> = {};
  if (params.source_id !== undefined) query.source_id = params.source_id;
  if (params.query !== undefined) query.query = params.query;
  if (params.cursor !== undefined) query.cursor = params.cursor;
  if (params.limit !== undefined) query.limit = params.limit;
  return request<SymbolPage>(dataRoutes.symbols, {
    schema: symbolPageSchema,
    query,
    ...options,
  });
}

/** One categorized tradable-symbol row from the market directory. */
export const marketRowSchema = z.object({
  symbol: z.string().min(1),
  name: z.string().min(1),
  asset_class: z.string().min(1),
  source_id: z.string().min(1),
  digits: z.number().int().nullable(),
  last: z.number().nullable(),
  bid: z.number().nullable(),
  ask: z.number().nullable(),
  spread: z.number().nullable(),
  volume: z.number().nullable(),
  open: z.number().nullable(),
  high: z.number().nullable(),
  low: z.number().nullable(),
  close: z.number().nullable(),
  change: z.number().nullable(),
  change_percent: z.number().nullable(),
  /**
   * API-composed technical overlays (Data's D1 bars plus Indicators'
   * formulas). Present only when the request opted in via
   * `includeTechnicals`; absent (not merely null) otherwise.
   */
  volatility: z.number().nullable().optional(),
  adr: z.number().nullable().optional(),
  range_percent_of_adr: z.number().nullable().optional(),
  change_pips: z.number().nullable().optional(),
});
export type MarketRow = z.infer<typeof marketRowSchema>;

/** Categorized market-directory page (Data-owned row shape). */
export const marketDirectorySchema = z.object({
  source_id: z.string().min(1),
  rows: z.array(marketRowSchema),
  limit: z.number().int().min(1),
  next_cursor: z.string().nullable().nullish(),
  revision: z.string().min(1),
  generated_at: z.string().min(1),
  request_id: z.string().min(1),
});
export type MarketDirectory = z.infer<typeof marketDirectorySchema>;

/** Query parameters for the categorized market directory. */
export interface MarketsQuery {
  /** Defaults to the configured runtime broker when omitted. */
  source_id?: string;
  query?: string;
  cursor?: string;
  /** Page size 1..200; defaults to the backend `API_DEFAULT_PAGE_SIZE`. */
  limit?: number;
  /** Compose each row with the API-owned Volatility/ADR/Range overlay. */
  includeTechnicals?: boolean;
}

/** Read the categorized market directory (requires `data:read`). */
export function markets(
  params: MarketsQuery = {},
  options?: RequestOptions
): Promise<ApiResponse<MarketDirectory>> {
  const query: Record<string, QueryValue> = {};
  if (params.source_id !== undefined) query.source_id = params.source_id;
  if (params.query !== undefined) query.query = params.query;
  if (params.cursor !== undefined) query.cursor = params.cursor;
  if (params.limit !== undefined) query.limit = params.limit;
  if (params.includeTechnicals) query.include_technicals = "true";
  return request<MarketDirectory>(dataRoutes.markets, {
    schema: marketDirectorySchema,
    query,
    ...options,
  });
}

/** Optional parameters for {@link quotes}. */
export interface QuotesParams {
  /** Defaults to the configured runtime broker when omitted. */
  sourceId?: string;
  /**
   * Compose each row with the API-owned Volatility/ADR/Range overlay.
   * Opt-in: it costs a historical fetch and two indicator calculations per
   * symbol, well above a plain quote.
   */
  includeTechnicals?: boolean;
}

/**
 * Read categorized quotes for an explicit symbol list (requires `data:read`).
 *
 * Unlike `markets`, this never walks the full broker catalog — it enriches
 * exactly the named symbols (e.g. one watchlist's contents), so cost scales
 * with the list size, not the broker's universe.
 */
export function quotes(
  symbols: string[],
  params: QuotesParams = {},
  options?: RequestOptions
): Promise<ApiResponse<MarketDirectory>> {
  const query: Record<string, QueryValue> = { symbols: symbols.join(",") };
  if (params.sourceId !== undefined) query.source_id = params.sourceId;
  if (params.includeTechnicals) query.include_technicals = "true";
  return request<MarketDirectory>(dataRoutes.quotes, {
    schema: marketDirectorySchema,
    query,
    ...options,
  });
}

/**
 * Canonical timeframe keys Data can serve.
 *
 * Restated from the backend's accepted query domain so the UI never offers a
 * timeframe the broker has no bars for.
 */
export const BAR_TIMEFRAMES = [
  "M1",
  "M5",
  "M15",
  "M30",
  "H1",
  "H4",
  "D1",
  "W1",
  "MN1",
] as const;
export type BarTimeframe = (typeof BAR_TIMEFRAMES)[number];

/** One broker-owned OHLCV bar. `time` is an ISO-8601 UTC bar-open instant. */
export const barSchema = z.object({
  time: z.string().nullable(),
  open: z.number().nullable(),
  high: z.number().nullable(),
  low: z.number().nullable(),
  close: z.number().nullable(),
  volume: z.number().nullable(),
});
export type Bar = z.infer<typeof barSchema>;

/** Ordered bar history for one symbol and timeframe (Data-owned values). */
export const barSeriesSchema = z.object({
  source_id: z.string().min(1),
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  bars: z.array(barSchema),
  count: z.number().int().min(0),
  start: z.string().nullable(),
  end: z.string().nullable(),
  cache_status: z.string(),
  request_id: z.string().min(1),
});
export type BarSeries = z.infer<typeof barSeriesSchema>;

/** Query parameters for {@link bars}. */
export interface BarsQuery {
  symbol: string;
  /** Canonical timeframe key; defaults to `H1` at the backend. */
  timeframe?: BarTimeframe;
  /** Most-recent bar count, 1..1,000,000; defaults to 500 at the backend. */
  limit?: number;
  /** Defaults to the configured runtime broker when omitted. */
  sourceId?: string;
  /** Optional ISO-8601 inclusive window start. */
  start?: string;
  /** Optional ISO-8601 inclusive window end. */
  end?: string;
}

/**
 * Read broker bar history for one symbol (requires `data:read`).
 *
 * The series is whatever the runtime broker holds — an unavailable provider
 * returns an error envelope rather than a generated fallback, so a chart never
 * renders invented history as real.
 */
export function bars(
  params: BarsQuery,
  options?: RequestOptions
): Promise<ApiResponse<BarSeries>> {
  const query: Record<string, QueryValue> = { symbol: params.symbol };
  if (params.timeframe !== undefined) query.timeframe = params.timeframe;
  if (params.limit !== undefined) query.limit = params.limit;
  if (params.sourceId !== undefined) query.source_id = params.sourceId;
  if (params.start !== undefined) query.start = params.start;
  if (params.end !== undefined) query.end = params.end;
  return request<BarSeries>(dataRoutes.bars, {
    schema: barSeriesSchema,
    query,
    ...options,
  });
}

/** Query parameters for the SSE market stream. */
export interface StreamQuery {
  symbol: string;
  mode: "ticks";
  timeframe: string;
  source_id?: "mt5";
}

/** One latest-value quote received from the MT5 bridge EA. */
export interface SnapshotQuote {
  symbol: string;
  time: string;
  bid: string;
  ask: string;
  last: string | null;
  spread: string;
  digits: number;
}

/** Validated shape carried inside a snapshot stream event payload. */
export interface SnapshotPayload {
  quotes: SnapshotQuote[];
  stale: boolean;
  gap: number;
  kind: "snapshot";
}

/**
 * Open the authenticated SSE market stream and yield validated events.
 *
 * Delegates to the low-level SSE transport. Higher-level gap/reconnect
 * handling is provided by `context/streams.ts::consumeStream`.
 */
export function stream(
  params: StreamQuery,
  options?: Omit<StreamTransportOptions, "query">
): AsyncIterable<StreamEvent> {
  const query: Record<string, QueryValue> = {
    symbol: params.symbol,
    mode: params.mode,
    timeframe: params.timeframe,
  };
  if (params.source_id !== undefined) query.source_id = params.source_id;
  return openStream(dataRoutes.stream, { query, ...options });
}

/** Open one authenticated multi-symbol MT5 snapshot stream. */
export function snapshotStream(
  symbols: string[],
  options?: Omit<StreamTransportOptions, "query">
): AsyncIterable<StreamEvent> {
  if (symbols.length === 0 || symbols.length > 200) {
    throw new Error("snapshot stream requires 1..200 symbols");
  }
  return openStream(dataRoutes.snapshotStream, {
    query: { symbols: symbols.join(",") },
    ...options,
  });
}

/** Open one authenticated multi-symbol MT5 Depth-of-Market stream. */
export function depthStream(
  symbols: string[],
  options?: Omit<StreamTransportOptions, "query">
): AsyncIterable<StreamEvent> {
  if (symbols.length === 0 || symbols.length > 200) {
    throw new Error("depth stream requires 1..200 symbols");
  }
  return openStream(dataRoutes.depthStream, {
    query: { symbols: symbols.join(",") },
    ...options,
  });
}

/** Aggregated data client. */
/**
 * Fetch and persist one market dataset through Data (requires `data:write`).
 *
 * Data performs both steps and authors the returned storage manifest; the
 * gateway holds no dataset and chooses no storage location.
 */
export function prepareDataset(
  body: { market_request: Record<string, unknown>; save_request: Record<string, unknown> },
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(dataRoutes.prepareDataset, {
    schema: z.record(z.string(), z.unknown()),
    body,
    ...options,
  });
}

const datasetSummarySchema = z.object({
  dataset_id: z.string().min(1),
  label: z.string().min(1),
  dataset_kind: z.string().min(1),
  symbol: z.string().nullable(),
  timeframe: z.string().nullable(),
  revision: z.string().min(1),
  content_hash: z.string().length(64),
  row_count: z.number().int().nonnegative(),
  active: z.literal(true),
});

export type DatasetSummary = z.infer<typeof datasetSummarySchema>;

/** List integrity-verified datasets eligible for SIM session binding. */
export function datasets(options?: RequestOptions): Promise<ApiResponse<DatasetSummary[]>> {
  return request<DatasetSummary[]>(dataRoutes.datasets, {
    schema: z.array(datasetSummarySchema),
    ...options,
  });
}

/** Read the import dialects Data supports (requires `data:read`). */
export function importDialects(
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(dataRoutes.importDialects, {
    schema: z.record(z.string(), z.unknown()),
    ...options,
  });
}

/**
 * Import one external dataset through Data (requires `data:write`).
 *
 * Data parses, validates, and persists the source and authors the returned
 * manifest; the payload is forwarded unchanged.
 */
export function importDataset(
  body: { payload: Record<string, unknown> },
  options?: RequestOptions
): Promise<ApiResponse<Record<string, unknown>>> {
  return request<Record<string, unknown>>(dataRoutes.importDataset, {
    schema: z.record(z.string(), z.unknown()),
    body,
    ...options,
  });
}

export const data = {
  capabilities,
  symbols,
  marketSeries,
  instruments,
  brokers,
  instrument,
  updateSeries,
  updateInstrument,
  markets,
  quotes,
  bars,
  stream,
  snapshotStream,
  depthStream,
  prepareDataset,
  datasets,
  importDialects,
  importDataset,
};
