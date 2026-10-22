/** Confirmed host transport for broker profiles, stocks and JSON catalog imports. */
import { createDomainClient, type DomainClient } from '../../../../host/transport';
import { validateBroker, type BrokerProfile } from './brokerProfiles';

export interface RemoteBrokerRecord {
  id: string; name: string; description: string; timezone: string; postfix: string;
  stockpicker_use: boolean; mt_use: boolean; is_system: boolean; stocks: string[];
  customized_stocks: number; total_instruments: number; total_sessions: number;
  spread_model: NonNullable<BrokerProfile['spreadModel']>;
  commission_model: NonNullable<BrokerProfile['commissionModel']>;
}
export interface BrokerImportResult {
  broker_id: string; imported_count: number; created_count: number; updated_count: number;
  records: Array<Record<string, unknown>>; failed: Array<{name: string; reason: string}>; unattempted: string[];
}
let client: DomainClient = createDomainClient('/data');
export function setBrokerApiClient(value: DomainClient): void { client = value; }
function id(value: string | number): string {
  const text = String(value);
  if (!/^[1-9]\d*$/.test(text) || !Number.isSafeInteger(Number(text))) throw new Error('Choose a saved broker profile.');
  return text;
}
export function toBrokerProfile(record: RemoteBrokerRecord): BrokerProfile {
  if (!record || typeof record.id !== 'string' || id(record.id) !== record.id ||
    typeof record.name !== 'string' || typeof record.description !== 'string' || typeof record.timezone !== 'string' ||
    typeof record.postfix !== 'string' || [record.stockpicker_use, record.mt_use, record.is_system].some(value => typeof value !== 'boolean') ||
    !Array.isArray(record.stocks) || record.stocks.some(stock => typeof stock !== 'string' || !stock.trim()) ||
    [record.customized_stocks, record.total_instruments, record.total_sessions].some(value => !Number.isSafeInteger(value) || value < 0) ||
    record.customized_stocks !== record.stocks.length || !record.spread_model || !record.commission_model) {
    throw new Error('The host returned an invalid broker profile.');
  }
  return validateBroker({id: record.id, name: record.name, desc: record.description, timezone: record.timezone,
    postfix: record.postfix, mtUse: record.mt_use, stockPickerUse: record.stockpicker_use, system: record.is_system,
    stocks: [...record.stocks], instruments: [], spreadModel: record.spread_model, commissionModel: record.commission_model,
    instrumentCount: record.total_instruments, sessionCount: record.total_sessions}, []);
}
export async function fetchBrokers(): Promise<BrokerProfile[]> {
  const records = await client.get<RemoteBrokerRecord[]>('/brokers');
  if (!Array.isArray(records)) throw new Error('The host returned an invalid broker catalog.');
  const profiles = records.map(toBrokerProfile);
  if (new Set(profiles.map(row => row.id)).size !== profiles.length || new Set(profiles.map(row => row.name.toLowerCase())).size !== profiles.length) throw new Error('Duplicate broker identities returned.');
  return profiles;
}
export async function getBroker(value: string | number): Promise<BrokerProfile> {
  const result = toBrokerProfile(await client.get<RemoteBrokerRecord>('/brokers/' + id(value)));
  if (result.id !== String(value)) throw new Error('The host returned a different broker.');
  return result;
}
export async function saveBroker(profile: BrokerProfile): Promise<BrokerProfile> {
  const clean = validateBroker(profile, []);
  const record = await client.post<RemoteBrokerRecord>('/brokers', {
    ...(clean.id ? {id: id(clean.id)} : {}), name: clean.name, description: clean.desc,
    stockpicker_use: clean.stockPickerUse, mt_use: clean.mtUse, timezone: clean.timezone,
    postfix: clean.postfix, spread_model: clean.spreadModel ?? {model: 'inherit'},
    commission_model: clean.commissionModel ?? {model: 'inherit'},
  });
  const result = toBrokerProfile(record);
  if (result.name !== clean.name || (clean.id && result.id !== clean.id)) throw new Error('The host did not confirm this profile.');
  return result;
}
export async function fetchBrokerStocks(value: string | number): Promise<string[]> {
  const result = await client.get<{broker_id: string; stocks: string[]}>(`/brokers/${id(value)}/stocks`);
  if (!result || result.broker_id !== String(value) || !Array.isArray(result.stocks) || result.stocks.some(stock => typeof stock !== 'string' || !stock.trim())) throw new Error('Invalid saved stocks response.');
  return result.stocks;
}
export async function saveBrokerStocks(value: string | number, stocks: string[]): Promise<string[]> {
  const result = await client.put<{broker_id: string; count: number; stocks: string[]}>(`/brokers/${id(value)}/stocks`, {stocks});
  if (!result || result.broker_id !== String(value) || !Array.isArray(result.stocks) || result.count !== result.stocks.length || result.stocks.some(stock => typeof stock !== 'string' || !stock.trim())) throw new Error('The host did not confirm the stock list.');
  return result.stocks;
}
export async function importBrokerRecords(
  kind: 'instrument' | 'session', brokerId: string, records: Array<Record<string, unknown>>,
  options: {selected_names: string[]; postfix: string; conflict_policy: 'error' | 'overwrite'; use_profile_costs: boolean},
): Promise<BrokerImportResult> {
  const target = ['-1','0'].includes(brokerId) ? '-1' : id(brokerId);
  const plural = kind === 'instrument' ? 'instruments' : 'sessions';
  const result = await client.post<BrokerImportResult>(`/brokers/${target}/import-${plural}`, {version: 1, kind: plural, [plural]: records, options});
  if (!result || result.broker_id !== target || !Array.isArray(result.records) || !Array.isArray(result.failed) || !Array.isArray(result.unattempted) ||
    [result.imported_count, result.created_count, result.updated_count].some(value => !Number.isSafeInteger(value) || value < 0) ||
    result.imported_count !== result.records.length || result.imported_count !== result.created_count + result.updated_count ||
    result.imported_count + result.failed.length + result.unattempted.length !== options.selected_names.length ||
    result.failed.some(row => !row || typeof row.name !== 'string' || typeof row.reason !== 'string') || result.unattempted.some(name => typeof name !== 'string')) throw new Error('The host returned an invalid import result. Refresh catalogs before retrying.');
  const field = kind === 'instrument' ? 'symbol' : 'name';
  const expected = new Set(options.selected_names.map(name => name + options.postfix));
  const reported = [...result.records.map(row => row?.[field]),...result.failed.map(row => row.name),...result.unattempted];
  if (result.records.some(row => !row || typeof row.id !== 'string' || !/^[1-9]\d*$/.test(row.id) || String(row.broker_id) !== target) ||
    reported.some(name => typeof name !== 'string' || !expected.has(name)) || new Set(reported).size !== expected.size) throw new Error('The host returned different import identities. Refresh catalogs before retrying.');
  return result;
}

export async function deleteBrokers(values: string[]): Promise<string[]> {
  if (!Array.isArray(values) || !values.length || values.length > 10000) throw new Error('Select broker profiles to remove.');
  const ids = [...new Set(values.map(id))];
  const result = await client.post<{deleted_ids: string[]; deleted_count: number}>('/brokers/delete', {ids});
  if (!result || !Array.isArray(result.deleted_ids) || result.deleted_count !== ids.length ||
    result.deleted_ids.length !== ids.length || new Set(result.deleted_ids).size !== ids.length ||
    result.deleted_ids.some(value => typeof value !== 'string' || !ids.includes(value))) {
    throw new Error('The host did not confirm the selected broker deletions. Refresh before retrying.');
  }
  return result.deleted_ids;
}
