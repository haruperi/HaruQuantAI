/** Data Manager's authenticated Dukascopy acquisition client. */
import { createDomainClient } from '../../../host/transport';
import type { DownloadMode } from './dukascopyDownload';

const client = createDomainClient('/contributions/workspace.data_manager');

export interface BackendDataset {
  id: string;
  symbol: string;
  source: 'Dukascopy';
  underlying: string;
  instrument: string;
  timeframe: 'M1' | 'TICK';
  broker: string;
  brokerName: string;
  timezone: string;
  category: string;
  from: string;
  to: string;
  bars: number;
}

export interface DukascopyCapability {
  definitions_available: boolean;
  source: 'dukascopy';
  formats: string[];
  modes: { standard: 'available' | 'unavailable'; cdn: 'available' | 'unavailable'; 'cdn-cn': 'available' | 'unavailable' };
  reason: string;
  datasets: BackendDataset[];
  broker_catalog_status: 'available' | 'unavailable';
  brokers: BackendBroker[];
}

export interface BackendBroker {
  id: string;
  name: string;
  postfix: string;
  timezone: string;
  mtUse: true;
  instruments: string[];
}

export interface BackendJob {
  job_id: string;
  state: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'timed_out';
  completed_days: number;
  published_days: number;
  missing_days: number;
  skipped_days: number;
  progress: number;
  error?: string;
  outcome?: 'pending' | 'complete' | 'partial' | 'empty';
  failed_chunks?: number;
  missing_chunks?: number;
}

export function getCapability(): Promise<DukascopyCapability> {
  return client.post('/sources.dukascopy.catalog', {});
}

export function addDataset(symbol: string, kind: 'm1' | 'ticks', instrument: string): Promise<{ id: string }> {
  return client.post('/sources.dukascopy.add', { symbol, kind, instrument });
}

export function startDownload(datasetId: string, from: string, to: string, overwrite: boolean, mode: DownloadMode = 'standard'): Promise<{ job_id: string; request_id: string }> {
  return client.post('/sources.dukascopy.download.start', {
    dataset_id: datasetId, date_from: from, date_to: to, overwrite, mode,
  });
}

export function statusDownload(jobId: string): Promise<BackendJob> {
  return client.post('/sources.dukascopy.download.status', { job_id: jobId });
}

export function cancelDownload(jobId: string): Promise<BackendJob> {
  return client.post('/sources.dukascopy.download.cancel', { job_id: jobId });
}

export function addDefinitions(request: { symbols: string[]; dataType: 'TICK' | 'M1'; broker: string; postfix: string; instruments: string[] }): Promise<{ ids: string[] }> {
  return client.post('/sources.dukascopy.definitions.add', {
    symbols: request.symbols, kind: request.dataType === 'M1' ? 'm1' : 'ticks',
    broker: request.broker, postfix: request.postfix, instruments: request.instruments,
  });
}

export function getDisclaimer(): Promise<{ dukascopy_disclaimer: string; cdn_disclaimer: string }> {
  return client.post('/sources.dukascopy.disclaimer', {});
}
