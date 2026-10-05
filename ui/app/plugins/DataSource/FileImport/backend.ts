/** Backend authority for uploaded file interpretation and publication. */
import { createDomainClient } from '../../../host/transport';
import type { ImportFormat } from './fileImport';

const client = createDomainClient('/contributions/workspace.data_manager');
export interface FileRequest {
  content: string; symbol: string; instrument: string; timeframe: string; error_handling: 0 | 1;
  format: { name: string; separator: string; date_format: string; time_format?: string;
    skip_rows: number; skip_columns: number; columns: string[] };
}
export interface FileRow { id: string; symbol: string; underlying: string; instrument: string;
  timeframe: string; timezone: string; date_from: string; date_to: string; bars: number }
export interface FileStatus { job_id: string; state: string; rows: number; ignored_rows: number;
  published_partitions: number; total_partitions: number; dataset_id?: string }
export const fileCatalog = () => client.post<{ available: boolean; reason: string; datasets: FileRow[]; formats: any[]; custom_formats: any[] }>('/sources.file_import.catalog', {});
export const fileDetect = async (content: string): Promise<ImportFormat> => {
  const raw = await client.post<any>('/sources.file_import.detect', { content });
  return { name: raw.name, separator: raw.separator, skipRows: raw.skipRows, skipColumns: raw.skipColumns,
    dateFormat: raw.dateFormat, timeFormat: raw.timeFormat || undefined, columns: raw.columnTypes, predefined: raw.predefined };
};
export const fileStart = (request: FileRequest) => client.post<{ job_id: string }>('/sources.file_import.import.start', request);
export const fileStatus = (job_id: string) => client.post<FileStatus>('/sources.file_import.import.status', { job_id });
export const fileCancel = (job_id: string) => client.post<FileStatus>('/sources.file_import.import.cancel', { job_id });
export function wireRequest(content: string, format: ImportFormat, symbol: string, instrument: string, timeframe: string, ignore: boolean): FileRequest {
  return { content, symbol, instrument, timeframe, error_handling: ignore ? 1 : 0,
    format: { name: format.name, separator: format.separator, date_format: format.dateFormat,
      time_format: format.timeFormat, skip_rows: format.skipRows, skip_columns: format.skipColumns,
      columns: format.columns.map(value => value || 'Unused') } };
}

export const formatFromBackend = (raw: any): ImportFormat => ({ name: raw.name, separator: raw.separator,
  skipRows: raw.skipRows, skipColumns: raw.skipColumns, dateFormat: raw.dateFormat,
  timeFormat: raw.timeFormat || undefined, columns: raw.columnTypes, predefined: raw.predefined });
export const fileSaveFormat = (format: ImportFormat, replace: boolean) => client.post('/sources.file_import.formats.save', {
  format: wireRequest('', format, '', '', 'auto', false).format, replace,
});
export const fileDeleteFormat = (name: string) => client.post('/sources.file_import.formats.delete', { name });

export async function filePublishGroup(name: string, symbols: string[]): Promise<void> {
  const catalog = await client.post<{ revision: number; state: { groups: { id: string; name: string; members: { ticker: string }[] }[] } }>('/catalogs.get', { kind: 'groups' });
  if (catalog.state.groups.some(group => group.name.toLowerCase() === name.trim().toLowerCase()))
    throw new Error('Imported data is stored, but a stock group with this name already exists. Choose a different group name.');
  await client.post('/catalogs.replace', { kind: 'groups', revision: catalog.revision, state: {
    groups: [...catalog.state.groups, { id: `file-group:${crypto.randomUUID()}`, name: name.trim(), description: 'Imported from folder', system: false, members: [...new Set(symbols)].map(ticker => ({ ticker })) }],
  } });
}
