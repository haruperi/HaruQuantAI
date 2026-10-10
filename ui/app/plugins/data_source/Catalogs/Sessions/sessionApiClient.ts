/**
 * REST API client for HaruQuantAI Trading Sessions.
 *
 * Communicates with backend endpoints (/data/sessions, /api/v1/data/sessions)
 * to provide full SQX-parity trading session lifecycle operations:
 * - Session CRUD (list, get, save, delete)
 * - Session cloning with broker profile postfixes
 * - Batch (mass) deletion
 * - NinjaTrader 8 TradingHours template discovery and import
 * - Native StrategyQuant X Sessions.xml import and export
 */

import { createDomainClient, type DomainClient } from '../../../../host/transport';
import type { SessionDay, SessionDefinition, SessionElement } from './sessions';

export interface RemoteSessionWindow {
  day_of_week?: number;
  day_from: string;
  day_to: string;
  start_time: string;
  end_time: string;
  eod: boolean;
  session_type?: string;
}

export interface RemoteTradingHoliday {
  date_str: string;
  description: string;
}

export interface RemoteSessionDefinition {
  name: string;
  broker_id: number;
  broker_name: string;
  description: string;
  timezone: string;
  windows: RemoteSessionWindow[];
  holidays?: RemoteTradingHoliday[];
  is_default?: boolean;
}

export interface NtTemplateInfo {
  folder: string;
  exists: boolean;
  templates: string[];
  count: number;
}

export interface NtImportResult {
  imported: string[];
  skipped: string[];
  failed: Array<{ template: string; reason: string }>;
  dropped_holidays: number;
  dropped_partial_holidays: number;
  success: string;
}

export interface SqxXmlImportResult {
  imported: SessionDefinition[];
  skipped: string[];
}

let client: DomainClient = createDomainClient('/data');

export function setSessionApiClient(customClient: DomainClient): void {
  client = customClient;
}

export function toSessionDefinition(record: RemoteSessionDefinition): SessionDefinition {
  const elements: SessionElement[] = (record.windows || []).map((w) => ({
    dayFrom: (w.day_from || 'Mon') as SessionDay,
    dayTo: (w.day_to || w.day_from || 'Mon') as SessionDay,
    timeFrom: w.start_time?.slice(0, 5) || '00:00',
    timeTo: w.end_time?.slice(0, 5) || '23:59',
    eod: Boolean(w.eod),
  }));

  return {
    name: record.name,
    broker: String(record.broker_id ?? -1),
    brokerName: record.broker_name || (record.broker_id === -1 ? 'Default' : `Broker ${record.broker_id}`),
    elements,
  };
}

export function fromSessionDefinition(item: SessionDefinition): RemoteSessionDefinition {
  return {
    name: item.name,
    broker_id: parseInt(item.broker, 10) || -1,
    broker_name: item.brokerName || 'SQ default',
    timezone: 'UTC',
    description: '',
    windows: item.elements.map((e) => ({
      day_from: e.dayFrom,
      day_to: e.dayTo,
      start_time: e.timeFrom,
      end_time: e.timeTo,
      eod: e.eod,
      session_type: 'Regular',
    })),
  };
}

export async function fetchRemoteSessions(params?: {
  broker_id?: number;
  search?: string;
}): Promise<SessionDefinition[]> {
  const query = new URLSearchParams();
  if (params?.broker_id !== undefined) query.set('broker_id', String(params.broker_id));
  if (params?.search) query.set('search', params.search);
  const qStr = query.toString();
  const path = qStr ? `/sessions?${qStr}` : '/sessions';
  const records = await client.get<RemoteSessionDefinition[]>(path);
  return (records || []).map(toSessionDefinition);
}

export async function saveRemoteSession(item: SessionDefinition): Promise<void> {
  const payload = fromSessionDefinition(item);
  await client.post('/sessions', payload);
}

export async function deleteRemoteSession(name: string): Promise<boolean> {
  const res = await client.delete<{ deleted: boolean }>(`/sessions/${encodeURIComponent(name)}`);
  return Boolean(res?.deleted);
}

export async function cloneRemoteSession(
  sourceName: string,
  newName: string,
  brokerId = -1,
  brokerPostfix = '',
): Promise<SessionDefinition> {
  const res = await client.post<RemoteSessionDefinition>('/sessions/clone', {
    source_name: sourceName,
    new_name: newName,
    broker_id: brokerId,
    broker_postfix: brokerPostfix,
  });
  return toSessionDefinition(res);
}

export async function massDeleteRemoteSessions(names: string[]): Promise<number> {
  const res = await client.post<{ deleted_count: number }>('/sessions/mass-delete', { names });
  return res?.deleted_count ?? 0;
}

export async function listNtTemplates(folderPath?: string): Promise<NtTemplateInfo> {
  const query = folderPath ? `?folder_path=${encodeURIComponent(folderPath)}` : '';
  return await client.get<NtTemplateInfo>(`/sessions/nt-templates${query}`);
}

export async function importNtRemote(payload: {
  xml_content?: string;
  folder_path?: string;
  conflict_policy?: string;
}): Promise<NtImportResult> {
  return await client.post<NtImportResult>('/sessions/import-nt', payload);
}

export async function exportSqxXmlRemote(names?: string[]): Promise<string> {
  return await client.post<string>('/sessions/export-xml', { names: names || [] });
}

export async function importSqxXmlRemote(
  xmlContent: string,
  policy = 'overwrite',
): Promise<SqxXmlImportResult> {
  const res = await client.post<{
    imported: RemoteSessionDefinition[];
    skipped: string[];
  }>('/sessions/import-xml', { xml_content: xmlContent, policy });
  return {
    imported: (res?.imported || []).map(toSessionDefinition),
    skipped: res?.skipped || [],
  };
}
