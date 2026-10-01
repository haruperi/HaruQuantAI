/** Authenticated Yahoo operations; market truth remains in the backend. */
import { createDomainClient } from '../../../host/transport';

const client = createDomainClient('/contributions/workspace.data_manager');

export interface YahooRecord {
  id: string; symbol: string; underlying: string; instrument: string;
  timeframe: string; date_from: string; date_to: string; bars: number;
  options: { metadata: { shortName?: string; longName?: string; exchangeName?: string;
    instrumentType?: string; firstTradeDate?: number } };
}
export interface YahooStatus {
  job_id: string; state: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'timed_out';
  completed_chunks: number; total_chunks: number; published_partitions: number; rows: number;
}
export const yahooCatalog = () => client.post<{ available: boolean; reason: string; datasets: YahooRecord[] }>('/sources.yahoo.catalog', {});
export const yahooAdd = (symbol: string, postfix: string) => client.post<{ id: string }>('/sources.yahoo.add', { symbol, postfix });
export const yahooDownload = (dataset_id: string, date_from: string, date_to: string, overwrite: boolean) => client.post<{ job_id: string }>('/sources.yahoo.download.start', { dataset_id, date_from, date_to, overwrite });
export const yahooStatus = (job_id: string) => client.post<YahooStatus>('/sources.yahoo.download.status', { job_id });
export const yahooCancel = (job_id: string) => client.post<YahooStatus>('/sources.yahoo.download.cancel', { job_id });
