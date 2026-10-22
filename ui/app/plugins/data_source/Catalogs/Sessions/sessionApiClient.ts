/** Confirmed session profile transport; calendar fields round-trip unchanged. */
import { createDomainClient, type DomainClient } from '../../../../host/transport';
import { sessionDays, validateIntervals, type CatalogSession, type SessionDefinition, type SessionElement, type SessionHoliday } from './sessions';

export interface RemoteSessionWindow {
  day_from: string; day_to: string; start_time: string; end_time: string; eod: boolean;
  session_type?: string; day_of_week?: number | null;
}
export interface RemoteSessionDefinition {
  id: string; name: string; broker_id: number; description: string; timezone: string;
  windows: RemoteSessionWindow[]; holidays: SessionHoliday[]; is_default: boolean; normalization_warnings?: string[];
}
export interface NtTemplateInfo { folder: string; exists: boolean; templates: string[]; count: number }
export interface NtImportResult { imported: string[]; skipped: string[]; failed: Array<{ template: string; reason: string }>; dropped_holidays: number; dropped_partial_holidays: number; success: string }
let client: DomainClient = createDomainClient('/data');
export function setSessionApiClient(value: DomainClient): void { client = value; }

export function toSessionDefinition(record: RemoteSessionDefinition): CatalogSession {
  if (!record || typeof record.id !== 'string' || !/^[1-9]\d*$/.test(record.id) || typeof record.name !== 'string' || !record.name.trim() ||
    typeof record.description !== 'string' || typeof record.timezone !== 'string' || !record.timezone ||
    !Number.isSafeInteger(record.broker_id) || typeof record.is_default !== 'boolean' || !Array.isArray(record.windows) ||
    !Array.isArray(record.holidays) || record.holidays.length > 1000) throw new Error('The host returned an invalid session profile.');
  if (record.normalization_warnings !== undefined && (!Array.isArray(record.normalization_warnings) || record.normalization_warnings.some(value => typeof value !== 'string' || !value.trim()))) throw new Error('Invalid session normalization warnings.');
  const elements = record.windows.map(window => {
    if (!window || (window.session_type !== undefined && (typeof window.session_type !== 'string' || !window.session_type.trim())) ||
      (window.day_of_week != null && (!Number.isInteger(window.day_of_week) || window.day_of_week !== sessionDays.indexOf(window.day_from as SessionElement['dayFrom'])))) throw new Error('Invalid session window metadata.');
    return { dayFrom: window.day_from as SessionElement['dayFrom'], dayTo: window.day_to as SessionElement['dayTo'], timeFrom: window.start_time, timeTo: window.end_time, eod: window.eod,
      sessionType: window.session_type ?? 'Regular', ...(window.day_of_week !== undefined ? { dayOfWeek: window.day_of_week } : {}) };
  });
  validateIntervals(elements);
  for (const holiday of record.holidays) {
    if (!holiday || !/^\d{4}-\d{2}-\d{2}$/.test(holiday.date_str) || typeof holiday.description !== 'string' ||
      !Number.isFinite(Date.parse(holiday.date_str)) || new Date(holiday.date_str).toISOString().slice(0,10) !== holiday.date_str) throw new Error('Invalid holiday calendar.');
  }
  if (new Set(record.holidays.map(day => day.date_str)).size !== record.holidays.length) throw new Error('Duplicate holiday dates.');
  return { id: record.id, name: record.name, broker: String(record.broker_id), brokerName: [-1,0].includes(record.broker_id) ? 'Default' : 'Broker ' + record.broker_id,
    timezone: record.timezone, description: record.description, holidays: structuredClone(record.holidays), isDefault: record.is_default, elements, ...(record.normalization_warnings ? { normalizationWarnings: [...record.normalization_warnings] } : {}) };
}
export function toRemoteWindow(element: SessionElement): RemoteSessionWindow {
  return { day_from: element.dayFrom, day_to: element.dayTo, start_time: element.timeFrom, end_time: element.timeTo, eod: element.eod,
    session_type: element.sessionType ?? 'Regular', ...(element.dayOfWeek !== undefined ? { day_of_week: element.dayOfWeek } : {}) };
}
export function fromSessionDefinition(item: SessionDefinition): Omit<RemoteSessionDefinition, 'id'> & { id?: string } {
  if (!/^-?\d+$/.test(item.broker) || !Number.isSafeInteger(Number(item.broker))) throw new Error('Choose a configured numeric broker ID.');
  validateIntervals(item.elements);
  return { ...(item.id !== undefined ? { id: item.id } : {}), name: item.name, broker_id: Number(item.broker),
    description: item.description ?? '', timezone: item.timezone ?? 'UTC', holidays: item.holidays ?? [], is_default: item.isDefault ?? false,
    windows: item.elements.map(toRemoteWindow) };
}
export async function fetchRemoteSessions(params?: Record<string, string | number>): Promise<CatalogSession[]> {
  const query = new URLSearchParams(Object.entries(params ?? {}).map(([key,value]) => [key, String(value)]));
  const records = await client.get<RemoteSessionDefinition[]>('/sessions' + (query.size ? '?' + query : ''));
  if (!Array.isArray(records)) throw new Error('The host returned an invalid session catalog.');
  const result = records.map(toSessionDefinition);
  if (new Set(result.map(row => row.id)).size !== result.length || new Set(result.map(row => row.name)).size !== result.length) throw new Error('Duplicate session identities.');
  return result;
}
export async function saveRemoteSession(item: SessionDefinition): Promise<CatalogSession> {
  const result = toSessionDefinition(await client.post('/sessions', fromSessionDefinition(item)));
  if (result.name !== item.name || item.id && result.id !== item.id) throw new Error('The host returned a different session identity.');
  return result;
}
export async function cloneRemoteSession(id: string, name: string, minutes = 0): Promise<CatalogSession> {
  if (!Number.isInteger(minutes) || Math.abs(minutes) > 1440) throw new Error('Shift requires integer minutes within +/-1440.');
  const result = toSessionDefinition(await client.post('/sessions/clone', { session_id: id, new_name: name, timezone_offset: minutes }));
  if (result.name !== name || result.id === id) throw new Error('The host did not confirm a new session identity.');
  return result;
}
export async function deleteRemoteSession(id: string): Promise<void> {
  const result = await client.delete<{ id: string; deleted: boolean }>('/sessions/' + encodeURIComponent(id));
  if (!result || result.id !== id || result.deleted !== true) throw new Error('The host did not confirm session deletion.');
}
export async function saveSessionElement(id: string, action: 'add' | 'update' | 'remove', index?: number, window?: SessionElement): Promise<CatalogSession> {
  const result = toSessionDefinition(await client.post('/sessions/' + encodeURIComponent(id) + '/elements', {
    action, ...(action !== 'add' ? { index } : {}), ...(window ? { window: toRemoteWindow(window) } : {}),
  }));
  if (result.id !== id) throw new Error('The host returned a different session identity.');
  return result;
}
// These legacy import clients have no workspace entry point in this implementation.
export async function listNtTemplates(folderPath?: string): Promise<NtTemplateInfo> { return client.get('/sessions/nt-templates' + (folderPath ? '?folder_path=' + encodeURIComponent(folderPath) : '')); }
export async function importNtRemote(payload: { xml_content?: string; folder_path?: string; conflict_policy?: string }): Promise<NtImportResult> { return client.post('/sessions/import-nt', payload); }
