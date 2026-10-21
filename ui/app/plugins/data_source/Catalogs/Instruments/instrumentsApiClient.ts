/** Authoritative instrument catalog transport. */
import { createDomainClient, type DomainClient } from '../../../../host/transport';
import { days, defaultCommission, type FileInstrument, type InstrumentBroker, type InstrumentMassPatch, type Swap } from '../../FileImport/fileSymbols';

export interface RemoteInstrumentDefinition {
  id: string; symbol: string; broker_id: number; description: string;
  point_value: number; point_size: number; tick_size: number; tick_step: number;
  contract_size: number | null; pip_size: number | null; margin_rate: number;
  decimals: number; tick_value_in_money: number; min_volume: number; max_volume: number; lot_step: number;
  default_spread: number; default_slippage: number; min_distance: number;
  order_size_multiplier: number; order_size_step: number; data_type: string;
  commissions: string; swap_long: number; swap_short: number; swap_3day_day: number;
  swap_settings: Swap | null;
  [key: string]: unknown;
}
export interface CatalogInstrument extends FileInstrument { id: string; record: RemoteInstrumentDefinition }
let client: DomainClient = createDomainClient('/data');
export function setInstrumentApiClient(value: DomainClient): void { client = value; }

function checked(value: RemoteInstrumentDefinition): RemoteInstrumentDefinition {
  if (!value || typeof value.id !== 'string' || !/^[1-9]\d*$/.test(value.id) || typeof value.symbol !== 'string' || !value.symbol ||
    ['point_value','point_size','tick_size','tick_step','margin_rate','decimals','tick_value_in_money','min_volume','max_volume','lot_step','default_spread','default_slippage','min_distance','order_size_multiplier','order_size_step','swap_long','swap_short','swap_3day_day','broker_id'].some(key => typeof value[key] !== 'number' || !Number.isFinite(value[key])) ||
    ['description','data_type','commissions'].some(key => typeof value[key] !== 'string') ||
    ['contract_size','pip_size'].some(key => value[key] !== null && (typeof value[key] !== 'number' || !Number.isFinite(value[key]) || Number(value[key]) <= 0))) {
    throw new Error('The host returned an invalid instrument specification.');
  }
  if (value.swap_settings !== null) {
    const swap = value.swap_settings;
    if (!swap || typeof swap.use !== 'boolean' || !['money','points','percent'].includes(swap.type) ||
      !Number.isFinite(swap.long) || !Number.isFinite(swap.short) || !days.includes(swap.tripleSwapOn) ||
      !/^([01]\d|2[0-3]):[0-5]\d$/.test(swap.rolloutHour)) throw new Error('Invalid stored swap specification.');
  }
  return value;
}

export function toFileInstrument(value: RemoteInstrumentDefinition, brokers: InstrumentBroker[] = []): CatalogInstrument {
  const record = checked(value);
  const broker = brokers.find(item => Number(item.id) === record.broker_id);
  // Legacy numeric commissions remain unchanged in record; their model is unspecified.
  const parsed: unknown = JSON.parse(record.commissions);
  const structured = typeof parsed === 'object' && parsed !== null && 'version' in parsed && parsed.version === 1 && 'settings' in parsed;
  const commission = structured ? (parsed as { settings: FileInstrument['commission'] }).settings : defaultCommission();
  if (!commission || typeof commission.model !== 'string' || !Number.isFinite(commission.value)) throw new Error('Invalid stored commission specification.');
  return {
    id: record.id, record, symbol: record.symbol, name: record.description, type: record.data_type,
    broker: String(record.broker_id), brokerName: broker?.name ?? ([-1,0].includes(record.broker_id) ? 'Default' : 'Broker ' + record.broker_id), timezone: broker?.timezone ?? 'UTC',
    pointValue: record.point_value, pointSize: record.point_size, tickSize: record.tick_size, tickStep: record.tick_step,
    contractSize: record.contract_size, pipSize: record.pip_size, marginRate: record.margin_rate, decimals: record.decimals,
    tickValue: record.tick_value_in_money, minVolume: record.min_volume, maxVolume: record.max_volume, lotStep: record.lot_step,
    spread: record.default_spread, slippage: record.default_slippage, minDistance: record.min_distance,
    multiplier: record.order_size_multiplier, sizeStep: record.order_size_step, commission,
    swap: record.swap_settings ?? { use: record.swap_long !== 0 || record.swap_short !== 0, type: 'points', long: record.swap_long,
      short: record.swap_short, tripleSwapOn: days[record.swap_3day_day], rolloutHour: '23:00' },
  };
}
export const specificationFields = {
  contractSize: 'contract_size', pipSize: 'pip_size', marginRate: 'margin_rate', decimals: 'decimals',
  minVolume: 'min_volume', maxVolume: 'max_volume', lotStep: 'lot_step', tickValue: 'tick_value_in_money',
};
export function fromFileInstrument(item: FileInstrument): Record<string, unknown> {
  if (!/^-?\d+$/.test(item.broker)) throw new Error('Choose a configured numeric broker ID.');
  const values: Record<string, unknown> = {
    symbol: item.symbol, description: item.name, broker_id: Number(item.broker), data_type: item.type,
    point_value: item.pointValue, tick_size: item.tickSize, tick_step: item.tickStep,
    default_spread: item.spread, default_slippage: item.slippage, min_distance: item.minDistance,
    order_size_multiplier: item.multiplier, order_size_step: item.sizeStep,
    commissions: JSON.stringify({ version: 1, settings: item.commission }), swap_settings: item.swap,
  };
  for (const [local, remote] of Object.entries(specificationFields)) {
    const value = item[local as keyof FileInstrument];
    if (value !== undefined) values[remote] = value;
  }
  return values;
}
const patchFields: Record<string, string> = { ...specificationFields, name: 'description', type: 'data_type', pointValue: 'point_value', tickSize: 'tick_size', tickStep: 'tick_step', spread: 'default_spread', slippage: 'default_slippage', minDistance: 'min_distance', multiplier: 'order_size_multiplier', sizeStep: 'order_size_step', commission: 'commissions', swap: 'swap_settings' };
export function instrumentPatch(item: FileInstrument, fields: InstrumentMassPatch['fields']): Record<string, unknown> {
  const complete = fromFileInstrument(item);
  return Object.fromEntries(Object.entries(fields).filter(([, enabled]) => enabled).map(([key]) => {
    const remote = patchFields[key];
    if (!remote || complete[remote] === undefined || (typeof complete[remote] === 'number' && !Number.isFinite(complete[remote]))) throw new Error('Select a valid instrument field and value.');
    return [remote, complete[remote]];
  }));
}
export async function fetchRemoteInstruments(params?: Record<string, string | number>): Promise<RemoteInstrumentDefinition[]> {
  const query = new URLSearchParams(Object.entries(params ?? {}).map(([key, value]) => [key, String(value)]));
  const rows = await client.get<RemoteInstrumentDefinition[]>('/instruments' + (query.size ? '?' + query : ''));
  if (!Array.isArray(rows)) throw new Error('The host returned an invalid instrument catalog.');
  const result = rows.map(checked);
  if (new Set(result.map(row => row.id)).size !== result.length || new Set(result.map(row => row.symbol)).size !== result.length) throw new Error('The host returned duplicate instrument identities.');
  return result;
}
export async function saveRemoteInstrument(item: FileInstrument): Promise<RemoteInstrumentDefinition> {
  const record = checked(await client.post('/instruments', fromFileInstrument(item)));
  if (record.symbol !== item.symbol) throw new Error('The host returned a different instrument symbol.');
  return record;
}
export async function cloneRemoteInstrument(sourceId: string, newSymbol: string): Promise<RemoteInstrumentDefinition> {
  const record = checked(await client.post('/instruments/clone', { source_id: sourceId, new_symbol: newSymbol }));
  if (record.symbol !== newSymbol || record.id === sourceId) throw new Error('The host did not confirm a new clone identity.');
  return record;
}
export async function massEditRemoteInstruments(instrumentIds: string[], updates: Record<string, unknown>): Promise<RemoteInstrumentDefinition[]> {
  const response = await client.post<{ updated_count: number; instruments: RemoteInstrumentDefinition[] }>('/instruments/mass-edit', { instrument_ids: instrumentIds, updates });
  if (!response || !Array.isArray(response.instruments) || response.updated_count !== new Set(instrumentIds).size || response.instruments.length !== response.updated_count) throw new Error('The host did not confirm all instrument changes.');
  const records = response.instruments.map(checked);
  if (new Set(records.map(row => row.id)).size !== records.length || records.some(row => !instrumentIds.includes(row.id))) throw new Error('The host returned different instrument identities.');
  return records;
}
