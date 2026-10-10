/**
 * REST API client for HaruQuantAI Instruments.
 *
 * Communicates with backend endpoints (/data/instruments, /api/v1/data/instruments)
 * to provide full SQX-parity instrument lifecycle operations:
 * - Instrument CRUD (list, get, save, delete)
 * - Instrument cloning with broker profile postfixes
 * - Batch (mass) deletion
 * - Mass editing with change flags
 * - Native StrategyQuant X Instruments.xml import and export
 * - Broker symbol alias resolution & management
 */

import { createDomainClient, type DomainClient } from '../../../../host/transport';
import type { FileInstrument, InstrumentBroker, InstrumentMassPatch } from '../../FileImport/fileSymbols';

export interface RemoteInstrumentDefinition {
  id?: number;
  symbol: string;
  connection?: string;
  broker_id: number;
  description: string;
  tick_size: number;
  tick_step: number;
  tick_value_in_money: number;
  point_value: number;
  decimals: number;
  default_spread: number;
  default_slippage: number;
  min_volume: number;
  max_volume: number;
  lot_step: number;
  margin_rate: number;
  swap_long: number;
  swap_short: number;
  swap_3day_day: number;
  commissions: string;
  data_type: string;
  alias: string;
  exchange: string;
  country: string;
  sector: string;
  min_distance: number;
  order_size_multiplier: number;
  order_size_step: number;
  cot: string | null;
  created_at_utc?: string;
  updated_at_utc?: string;
}

export interface AliasRecord {
  alias: string;
  instrument: string;
  description: string;
}

let client: DomainClient = createDomainClient('/data');

export function setInstrumentApiClient(customClient: DomainClient): void {
  client = customClient;
}

export function toFileInstrument(
  record: RemoteInstrumentDefinition,
  brokers: InstrumentBroker[] = [],
): FileInstrument {
  const brokerProfile = brokers.find((b) => Number(b.id) === record.broker_id);
  const tripleSwapDay = record.swap_3day_day === 5 ? 'FRIDAY' : 'WEDNESDAY';
  const hasSwap = record.swap_long !== 0 || record.swap_short !== 0;

  return {
    symbol: record.symbol,
    name: record.description || record.symbol,
    type: record.data_type || 'Forex',
    broker: String(record.broker_id ?? -1),
    brokerName: brokerProfile?.name || (record.broker_id === -1 ? 'Default' : `Broker ${record.broker_id}`),
    timezone: brokerProfile?.timezone || 'UTC',
    pointValue: record.point_value,
    tickSize: record.tick_size,
    tickStep: record.tick_step,
    spread: record.default_spread,
    slippage: record.default_slippage,
    minDistance: record.min_distance,
    multiplier: record.order_size_multiplier,
    sizeStep: record.order_size_step,
    commission: {
      model: 'None',
      value: 0,
      unit: 'share',
      min: 0,
      minUnit: 'money',
      max: 0,
      maxUnit: 'equity',
    },
    swap: {
      use: hasSwap,
      type: 'points',
      long: record.swap_long,
      short: record.swap_short,
      tripleSwapOn: tripleSwapDay,
      rolloutHour: '23:00',
    },
  };
}

export function fromFileInstrument(item: FileInstrument): RemoteInstrumentDefinition {
  const tripleDayNum = item.swap.tripleSwapOn === 'FRIDAY' ? 5 : 3;
  return {
    symbol: item.symbol,
    description: item.name || item.symbol,
    broker_id: parseInt(item.broker, 10) || -1,
    data_type: item.type,
    point_value: item.pointValue,
    tick_size: item.tickSize,
    tick_step: item.tickStep,
    tick_value_in_money: 10.0,
    decimals: item.tickSize < 0.0001 ? 5 : item.tickSize < 0.01 ? 4 : item.tickSize < 0.1 ? 2 : 0,
    default_spread: item.spread,
    default_slippage: item.slippage,
    min_distance: item.minDistance,
    order_size_multiplier: item.multiplier,
    order_size_step: item.sizeStep,
    min_volume: 0.01,
    max_volume: 100.0,
    lot_step: 0.01,
    margin_rate: 0.05,
    swap_long: item.swap.long,
    swap_short: item.swap.short,
    swap_3day_day: tripleDayNum,
    commissions: '0.0',
    alias: '',
    exchange: '',
    country: '',
    sector: '',
    cot: null,
  };
}

export async function fetchRemoteInstruments(params?: {
  connection?: string;
  data_type?: string;
  broker_id?: number;
  search?: string;
}): Promise<RemoteInstrumentDefinition[]> {
  const query = new URLSearchParams();
  if (params?.connection) query.set('connection', params.connection);
  if (params?.data_type) query.set('data_type', params.data_type);
  if (params?.broker_id !== undefined && params.broker_id !== null) {
    query.set('broker_id', String(params.broker_id));
  }
  if (params?.search) query.set('search', params.search);
  const qStr = query.toString();
  const path = qStr ? `/instruments?${qStr}` : '/instruments';
  const records = await client.get<RemoteInstrumentDefinition[]>(path);
  return records || [];
}

export async function saveRemoteInstrument(item: FileInstrument): Promise<void> {
  const payload = fromFileInstrument(item);
  await client.post('/instruments', payload);
}

export async function updateRemoteInstrument(
  symbol: string,
  updates: Partial<RemoteInstrumentDefinition>,
): Promise<void> {
  await client.put(`/instruments/${encodeURIComponent(symbol)}`, updates);
}

export async function deleteRemoteInstrument(symbol: string): Promise<boolean> {
  const res = await client.delete<{ deleted: boolean }>(`/instruments/${encodeURIComponent(symbol)}`);
  return Boolean(res?.deleted);
}

export async function cloneRemoteInstrument(
  symbol: string,
  cloneName: string,
  brokerId = -1,
  brokerPostfix = '',
): Promise<RemoteInstrumentDefinition> {
  return await client.post<RemoteInstrumentDefinition>('/instruments/clone', {
    symbol,
    clone_name: cloneName,
    broker_id: brokerId,
    broker_postfix: brokerPostfix,
  });
}

export async function massEditRemoteInstruments(
  symbols: string[],
  updates: Record<string, unknown>,
  changeFlags?: InstrumentMassPatch['fields'],
): Promise<number> {
  const res = await client.post<{ updated_count: number }>('/instruments/mass-edit', {
    symbols,
    updates,
    change_flags: changeFlags,
  });
  return res?.updated_count ?? 0;
}

export async function massDeleteRemoteInstruments(
  symbols: string[],
): Promise<{ deleted_count: number; is_async: boolean }> {
  return await client.post<{ deleted_count: number; is_async: boolean }>('/instruments/mass-delete', {
    symbols,
  });
}

export async function exportInstrumentsXmlRemote(symbols?: string[]): Promise<string> {
  const res = await client.post<{ xml: string }>('/instruments/save', { symbols: symbols || [] });
  return res?.xml ?? '';
}

export async function importInstrumentsXmlRemote(
  xmlContent: string,
  conflictPolicy = 'overwrite_all',
): Promise<{ imported: number; overwritten: number; skipped: number; symbols: string[] }> {
  return await client.post<{
    imported: number;
    overwritten: number;
    skipped: number;
    symbols: string[];
  }>('/instruments/load', { xml_content: xmlContent, conflict_policy: conflictPolicy });
}

export async function listAliasesRemote(): Promise<AliasRecord[]> {
  const res = await client.get<AliasRecord[]>('/instruments/aliases');
  return res || [];
}

export async function addAliasRemote(alias: string, instrument: string, description = ''): Promise<void> {
  await client.post('/instruments/aliases', { alias, instrument, description });
}

export async function editAliasRemote(alias: string, instrument: string, description = ''): Promise<void> {
  await client.put(`/instruments/aliases/${encodeURIComponent(alias)}`, { alias, instrument, description });
}

export async function deleteAliasRemote(alias: string): Promise<boolean> {
  const res = await client.delete<{ removed: boolean }>(`/instruments/aliases/${encodeURIComponent(alias)}`);
  return Boolean(res?.removed);
}
