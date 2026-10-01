import { createDomainClient } from '../../../host/transport';
import type { DarwinexDefinition } from './darwinex';
const client = createDomainClient('/contributions/workspace.data_manager');
export interface DarwinexRecord { id: string; symbol: string; underlying: string; instrument: string; timeframe: 'TICK'; broker: string; date_from: string; date_to: string; bars: number; options: { metadata: { date_from: string } } }
export interface DarwinexSymbolInfo { symbol: string; date_from: string; decimals: number }
export const darwinexCatalog = () => client.post<{ available: boolean; reason: string; datasets: DarwinexRecord[]; symbols: DarwinexSymbolInfo[] }>('/sources.darwinex.catalog', {});
export const darwinexAdd = (row: DarwinexDefinition) => client.post<{ id: string }>('/sources.darwinex.add', { symbol: row.underlying, postfix: row.symbol.slice(row.underlying.length), timeframe: row.timeframe, broker: row.broker, instrument: row.instrument });
export const darwinexDownload = (dataset_id: string, date_from: string, date_to: string, overwrite: boolean) => client.post<{ job_id: string }>('/sources.darwinex.download.start', { dataset_id, date_from, date_to, overwrite });
export const darwinexStatus = (job_id: string) => client.post<{ state: string; completed_chunks: number; total_chunks: number; rows: number }>('/sources.darwinex.download.status', { job_id });
export const darwinexCancel = (job_id: string) => client.post('/sources.darwinex.download.cancel', { job_id });
export async function darwinexImport(dataset_id: string, symbol: string, files: File[]): Promise<{ job_id: string }> {
  const pairs = new Map<string, { ask_base64: string; bid_base64: string }>();
  let total = 0;
  for (const file of files) {
    const match = /^([A-Za-z0-9]+)_(ASK|BID)_(.+)\.(?:log|csv)(?:\.gz)?$/i.exec(file.name);
    if (!match || match[1].toUpperCase() !== symbol.toUpperCase()) continue;
    total += file.size;
    if (total > 6 * 1024 * 1024) throw new Error('Choose Darwinex log batches up to 6 MiB per symbol.');
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = '';
    for (let offset = 0; offset < bytes.length; offset += 32768) binary += String.fromCharCode(...bytes.subarray(offset, offset + 32768));
    const pair = pairs.get(match[3]) || { ask_base64: '', bid_base64: '' };
    if (match[2].toUpperCase() === 'ASK') pair.ask_base64 = btoa(binary); else pair.bid_base64 = btoa(binary);
    pairs.set(match[3], pair);
  }
  if (!pairs.size) throw new Error(`No uploaded bid/ask logs found for ${symbol}.`);
  return client.post('/sources.darwinex.import.start', { dataset_id, pairs: [...pairs].sort(([a], [b]) => a.localeCompare(b)).map(([, pair]) => pair) });
}
