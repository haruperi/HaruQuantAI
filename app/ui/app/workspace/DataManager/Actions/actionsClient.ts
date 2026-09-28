/** DataManager Actions API Client.
 * Communicates with backend operations exposed by workspace.data_manager.
 */
import { createDomainClient } from '../../../host/transport';

const client = createDomainClient('/contributions/workspace.data_manager');

export interface ExportCsvParams {
  symbol: string;
  timeframe?: string;
  date_from?: string;
  date_to?: string;
  output_path?: string;
  target_timezone?: string;
  header?: string;
  include_header?: boolean;
}

export interface ExportCsvResult {
  success: boolean;
  symbol: string;
  timeframe: string;
  records: number;
  outputPath?: string | null;
  contentLength: number;
  content?: string;
}

export interface ExportMt4Params {
  symbol: string;
  mt4_symbol?: string;
  date_from?: string;
  date_to?: string;
  output_dir?: string;
  timeframe?: string;
  export_mode?: 'All' | 'hst' | 'fxt';
  target_timezone?: string;
  server_name?: string;
  spread?: number;
  digits?: number;
}

export interface ExportMt4Result {
  success: boolean;
  symbol: string;
  files: string[];
}

export interface ExportMt5Params {
  symbol: string;
  timeframe?: string;
  spread_mode?: 'real' | 'fixed';
  spread_points?: number;
  date_from?: string;
  date_to?: string;
  output_path?: string;
  target_timezone?: string;
}

export interface ExportMt5Result {
  success: boolean;
  symbol: string;
  kind: string;
  timeframe: string;
  records: number;
  outputPath?: string | null;
  contentLength: number;
  content?: string;
}

export interface CloneTimezoneParams {
  symbol: string;
  shift_hours?: number;
  timezone?: string;
  postfix?: string;
  remove_weekends?: boolean;
}

export interface CloneTimezoneResult {
  success: boolean;
  sourceSymbol: string;
  clonedSymbol: string;
  bars: number;
  shiftHours: number;
  timezone: string;
  underlying: string;
}

export interface DeleteParams {
  symbols: string[];
  mode?: 'remove' | 'clear';
}

export interface DeleteResult {
  success: boolean;
  deletedCount?: number;
  affected?: number;
  mode: string;
  deleted?: string[];
}

export interface SaveDefinitionsParams {
  symbols?: string[];
  file_path?: string;
}

export interface SaveDefinitionsResult {
  success: boolean;
  datasetsCount: number;
  instrumentsCount: number;
  filePath?: string | null;
  content?: string;
}

export interface LoadDefinitionsParams {
  file_path?: string;
  definitions?: any[];
  instruments?: any[];
}

export interface LoadDefinitionsResult {
  success: boolean;
  loadedDatasets: number;
  loadedInstruments: number;
}

export interface ReviewDataParams {
  symbol: string;
  timeframe?: string;
  session?: string;
  offset?: number;
  limit?: number;
  date_from?: string;
  date_to?: string;
}

export interface ReviewDataResult {
  symbol: string;
  timeframe: string;
  totalRows: number;
  offset: number;
  limit: number;
  rows: Array<[string, number, number, number, number, number]>;
}

export interface ReviewChartParams {
  symbol: string;
  timeframe?: string;
  session?: string;
  limit?: number;
}

export interface ReviewCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ReviewChartResult {
  symbol: string;
  timeframe: string;
  count: number;
  chart: ReviewCandle[];
}

export interface ReviewProblem {
  date: string;
  problem: string;
}

export interface ReviewQualityParams {
  symbol: string;
  timeframe?: string;
  session?: string;
}

export interface ReviewQualityResult {
  symbol: string;
  timeframe: string;
  totalBars: number;
  totalErrors: number;
  qualityScore: number;
  problems: ReviewProblem[];
}

export interface UpdateAllParams {
  provider?: string;
}

export interface UpdateAllResult {
  success: boolean;
  datasets: Array<{
    id: string;
    symbol: string;
    dateFrom: string;
    dateTo: string;
    updatedTo: string;
  }>;
  queued: number;
}

export interface UpdateSelectedParams {
  symbols: string[];
}

export interface UpdateSelectedResult {
  success: boolean;
  datasets: Array<{
    id: string;
    symbol: string;
    dateFrom: string;
    dateTo: string;
    updatedTo: string;
  }>;
  queued: number;
}

export interface BrokerDataParams {
  query?: string;
}

export interface BrokerDataResult {
  query: string;
  count: number;
  instruments: Array<{
    symbol: string;
    description: string;
    broker: string;
    pointValue: number;
    tickSize: number;
    spread: number;
    decimals: number;
  }>;
}

export interface BrokerDataUpdateResult {
  success: boolean;
  updatedDatasets: number;
  brokerProfiles: number;
}

export interface DatasetRow {
  id: string;
  source: string;
  symbol: string;
  underlying: string;
  instrument: string;
  timeframe: string;
  broker: string;
  brokerName: string;
  timezone: string;
  category: string;
  from: string;
  to: string;
  date_from?: string;
  date_to?: string;
  bars: number;
  quality?: number;
  status?: string;
  barType?: string;
}

export function downloadBlob(filename: string, content: string, mimeType = 'text/plain;charset=utf-8'): void {
  if (typeof document === 'undefined') return;
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.hidden = true;
  document.body.appendChild(link);
  link.click();
  link.remove?.();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const actionsClient = {
  listDatasets: (): Promise<DatasetRow[]> =>
    client.post('/actions.list_datasets', {}),

  exportToCsv: (params: ExportCsvParams): Promise<ExportCsvResult> =>
    client.post('/actions.export_to_csv', params),

  exportToMt4: (params: ExportMt4Params): Promise<ExportMt4Result> =>
    client.post('/actions.export_to_mt4', params),

  exportToMt5: (params: ExportMt5Params): Promise<ExportMt5Result> =>
    client.post('/actions.export_to_mt5', params),

  cloneToTimezone: (params: CloneTimezoneParams): Promise<CloneTimezoneResult> =>
    client.post('/actions.clone_to_timezone', params),

  deleteDatasets: (params: DeleteParams): Promise<DeleteResult> =>
    client.post('/actions.delete', params),

  saveDefinitions: (params: SaveDefinitionsParams = {}): Promise<SaveDefinitionsResult> =>
    client.post('/actions.save', params),

  loadDefinitions: (params: LoadDefinitionsParams): Promise<LoadDefinitionsResult> =>
    client.post('/actions.load', params),

  reviewData: (params: ReviewDataParams): Promise<ReviewDataResult> =>
    client.post('/actions.review_data', params),

  reviewChart: (params: ReviewChartParams): Promise<ReviewChartResult> =>
    client.post('/actions.review_chart', params),

  reviewQuality: (params: ReviewQualityParams): Promise<ReviewQualityResult> =>
    client.post('/actions.review_quality', params),

  updateAll: (params: UpdateAllParams = {}): Promise<UpdateAllResult> =>
    client.post('/actions.update_all', params),

  updateSelected: (params: UpdateSelectedParams): Promise<UpdateSelectedResult> =>
    client.post('/actions.update_selected', params),

  brokerData: (params: BrokerDataParams = {}): Promise<BrokerDataResult> =>
    client.post('/actions.broker_data', params),

  brokerDataUpdate: (): Promise<BrokerDataUpdateResult> =>
    client.post('/actions.broker_data_update', {}),
};
