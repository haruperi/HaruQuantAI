/** Remote API client for Data Manager external indicators and custom data. */

import { createDomainClient, type DomainClient } from '../../../../shell/transport';
import {
  type ExternalColumnType,
  type ExternalImportFormat,
  type ExternalIndicatorDefinition,
  type ExternalIndicatorLine,
} from './externalIndicators';

export interface RemoteIndicatorValue {
  name: string;
  mt4?: string;
  mt5?: string;
  el?: string;
}

export interface RemoteIndicatorRecord {
  id?: string;
  name: string;
  data_type?: string;
  timeframe?: string;
  system?: boolean;
  values?: RemoteIndicatorValue[];
  total_records?: number;
  date_from?: string | null;
  date_to?: string | null;
  total_days?: number;
  records?: Array<{ timestamp: string | number; values: Record<string, number> | number[] }>;
}

export interface RemoteImportFormat {
  name: string;
  separator?: string;
  date_format?: string;
  skip_rows?: number;
  skip_columns?: number;
  columns?: string[];
  error_handling?: string;
  predefined?: boolean;
}

export interface RemoteImportInfo {
  formats: RemoteImportFormat[];
  separators: string[];
  date_formats: string[];
  error_handling: string[];
  column_types: string[];
  encoding: string;
}

export interface RemoteImportJob {
  job_id: string;
  kind: string;
  status: string;
  progress: number;
  message?: string;
  error_message?: string;
  result?: {
    name?: string;
    imported_count?: number;
    skipped_rows?: number;
  };
}

let client: DomainClient = createDomainClient('/data');

export function setExternalIndicatorsApiClient(value: DomainClient): void {
  client = value;
}

export function toExternalIndicatorDefinition(record: RemoteIndicatorRecord): ExternalIndicatorDefinition {
  const lineValues: ExternalIndicatorLine[] = Array.from({ length: 3 }, (_, index) => {
    const item = record.values?.[index];
    return {
      name: item?.name ?? '',
      mt4: item?.mt4 ?? '',
      mt5: item?.mt5 ?? '',
      el: item?.el ?? '',
    };
  });
  if (record.values && record.values.length > 3) {
    for (let i = 3; i < record.values.length; i++) {
      const item = record.values[i];
      lineValues.push({
        name: item?.name ?? '',
        mt4: item?.mt4 ?? '',
        mt5: item?.mt5 ?? '',
        el: item?.el ?? '',
      });
    }
  }

  const rawType = record.data_type === 'signal' ? 10 : 1;

  return {
    name: record.name,
    type: rawType,
    values: lineValues.slice(0, 3),
    timeframe: record.timeframe || '—',
    dateFrom: record.date_from ?? '',
    dateTo: record.date_to ?? '',
    totalDays: record.total_days ?? 0,
    records: [],
  };
}

export function toExternalImportFormat(record: RemoteImportFormat): ExternalImportFormat {
  return {
    name: record.name,
    separator: record.separator ?? ',',
    skipRows: record.skip_rows ?? 0,
    skipColumns: record.skip_columns ?? 0,
    dateFormat: record.date_format ?? 'yyyy-MM-dd HH:mm:ss',
    columns: (record.columns ?? []) as ExternalColumnType[],
    predefined: Boolean(record.predefined),
  };
}

export async function fetchExternalIndicators(): Promise<ExternalIndicatorDefinition[]> {
  const rows = await client.get<RemoteIndicatorRecord[]>('/custom-data');
  if (!Array.isArray(rows)) throw new Error('Invalid host external indicators response.');
  return rows.map(toExternalIndicatorDefinition);
}

export async function saveExternalIndicator(item: ExternalIndicatorDefinition): Promise<ExternalIndicatorDefinition> {
  const payload = {
    name: item.name.trim(),
    values: item.values.filter(line => line.name.trim()),
    data_type: item.type === 10 ? 'signal' : 'custom',
    timeframe: item.timeframe && item.timeframe !== '—' ? item.timeframe : 'D1',
  };
  const saved = await client.post<RemoteIndicatorRecord>('/custom-data', payload);
  return toExternalIndicatorDefinition(saved);
}

export async function editExternalIndicator(
  original: string,
  item: ExternalIndicatorDefinition,
): Promise<ExternalIndicatorDefinition> {
  const payload = {
    indicator_name: original,
    name: item.name.trim(),
    values: item.values.filter(line => line.name.trim()),
    data_type: item.type === 10 ? 'signal' : 'custom',
    timeframe: item.timeframe && item.timeframe !== '—' ? item.timeframe : 'D1',
  };
  const updated = await client.post<RemoteIndicatorRecord>('/custom-data/edit', payload);
  return toExternalIndicatorDefinition(updated);
}

export async function deleteExternalIndicators(names: string[]): Promise<string[]> {
  if (!Array.isArray(names) || !names.length) throw new Error('Select indicators to delete.');
  const result = await client.post<{ names: string[]; cleared_records: number; deleted_count: number }>(
    '/custom-data/delete',
    { names },
  );
  return result?.names ?? names;
}

export async function clearExternalIndicators(names: string[]): Promise<{ names: string[]; cleared_records: number }> {
  if (!Array.isArray(names) || !names.length) throw new Error('Select indicators to clear.');
  return client.post<{ names: string[]; cleared_records: number }>('/custom-data/clear', { names });
}

export async function fetchExternalReview(
  name: string,
  limit = 100,
  offset = 0,
): Promise<{ name: string; columns: string[]; records: Array<{ timestamp: string; values: Record<string, number> }>; pagination?: {has_more: boolean} }> {
  return client.get(`/custom-data/review?name=${encodeURIComponent(name)}&limit=${limit}&offset=${offset}`);
}

export async function fetchExternalImportInfo(): Promise<{
  formats: ExternalImportFormat[];
  separators: string[];
  dateFormats: string[];
}> {
  const info = await client.get<RemoteImportInfo>('/custom-data/import-info');
  return {
    formats: (info?.formats ?? []).map(toExternalImportFormat),
    separators: info?.separators ?? [],
    dateFormats: info?.date_formats ?? [],
  };
}

export async function saveExternalImportFormat(
  format: ExternalImportFormat,
  replace = false,
): Promise<ExternalImportFormat> {
  const url = replace ? '/custom-data/formats/edit' : '/custom-data/formats';
  const config = {
    separator: format.separator,
    date_format: format.dateFormat,
    skip_rows: format.skipRows,
    skip_columns: format.skipColumns,
    columns: format.columns,
  };
  const saved = await client.post<RemoteImportFormat>(url, {
    name: format.name.trim(),
    config,
  });
  return toExternalImportFormat(saved);
}

export async function deleteExternalImportFormat(name: string): Promise<void> {
  await client.delete(`/custom-data/formats/${encodeURIComponent(name)}`);
}

export async function importExternalIndicatorData(
  name: string,
  content: string,
  formatName?: string,
  replace = false,
  options?: Record<string, unknown>,
  background = false,
): Promise<unknown> {
  return client.post('/custom-data/import', {
    name,
    content,
    format_name: formatName,
    replace,
    background,
    ...options,
  });
}

export async function previewExternalIndicatorImport(
  name: string,
  content: string,
  formatName?: string,
  limit = 20,
  options?: Record<string, unknown>,
): Promise<{
  name: string;
  total_records: number;
  records: Array<{ timestamp: string; values: Record<string, number> }>;
  format: Record<string, unknown>;
}> {
  return client.post('/custom-data/import-preview', {
    name,
    content,
    format_name: formatName,
    limit,
    ...options,
  });
}

export async function recognizeExternalIndicator(
  filename: string,
  content: string,
): Promise<ExternalIndicatorDefinition> {
  const record = await client.post<RemoteIndicatorRecord>('/custom-data/recognize', {
    filename,
    content,
  });
  return toExternalIndicatorDefinition(record);
}

export async function exportExternalIndicatorValues(name: string): Promise<{ content: string; count: number }> {
  return client.post<{ content: string; count: number }>('/custom-data/export', { name });
}

export async function saveExternalDefinitions(names?: string[]): Promise<{ content: string; count: number }> {
  return client.post<{ content: string; count: number }>('/custom-data/save', { names });
}

export async function loadExternalDefinitions(
  content: string,
  onConflict = 'error',
): Promise<{ loaded: ExternalIndicatorDefinition[]; loaded_count: number; skipped: string[] }> {
  const result = await client.post<{
    loaded: RemoteIndicatorRecord[];
    loaded_count: number;
    skipped: string[];
  }>('/custom-data/load', {
    content,
    on_conflict: onConflict,
  });
  return {
    loaded: (result?.loaded ?? []).map(toExternalIndicatorDefinition),
    loaded_count: result?.loaded_count ?? 0,
    skipped: result?.skipped ?? [],
  };
}

export async function updateCotIndicators(
  years?: number[],
): Promise<{ updated_count: number; records: number; years: number[] }> {
  return client.post('/custom-data/update-cot', { years });
}

export async function fetchExternalImportJob(jobId: string): Promise<RemoteImportJob> {
  return client.get<RemoteImportJob>(`/custom-data-jobs/${encodeURIComponent(jobId)}`);
}

export async function controlExternalImportJob(
  jobId: string,
  action: 'pause' | 'resume' | 'stop',
): Promise<RemoteImportJob> {
  return client.post<RemoteImportJob>(`/custom-data-jobs/${encodeURIComponent(jobId)}/${action}`, {});
}
