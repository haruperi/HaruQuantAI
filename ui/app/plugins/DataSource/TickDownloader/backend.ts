import { createDomainClient } from '../../../host/transport';
const client = createDomainClient('/contributions/workspace.data_manager');
export interface TDFileInfo { path: string; symbol: string; hour: string; decimals: number }
export interface TDRecord { id: string; symbol: string; underlying: string; instrument: string; timeframe: string; date_from: string; date_to: string; bars: number }
export const tdCatalog = () => client.post<{ available: boolean; reason: string; datasets: TDRecord[] }>('/sources.tick_downloader.catalog', {});
export const tdInspect = (paths: string[]) => client.post<{ files: TDFileInfo[] }>('/sources.tick_downloader.inspect', { paths });
export const tdImport = (symbol: string, postfix: string, decimals: number, files: { hour: string; content_base64: string }[]) => client.post<{ job_id: string }>('/sources.tick_downloader.import.start', { symbol, postfix, decimals, files });
export const tdStatus = (job_id: string) => client.post<{ state: string; rows: number; completed_files: number; total_files: number }>('/sources.tick_downloader.import.status', { job_id });
export const tdCancel = (job_id: string) => client.post('/sources.tick_downloader.import.cancel', { job_id });
export async function encodeBI5(file: File): Promise<string> {
  if (!file.size || file.size > 6 * 1024 * 1024) throw new Error('Choose nonempty BI5 files up to 6 MiB each.');
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 32768) binary += String.fromCharCode(...bytes.subarray(offset, offset + 32768));
  return btoa(binary);
}
