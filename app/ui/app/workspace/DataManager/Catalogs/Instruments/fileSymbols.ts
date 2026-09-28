import { instruments } from '../../Common/fixtures';
export const dataTypes = ['Stock', 'Futures', 'Forex', 'CFD'] as const;
export const commissionModels = ['None', 'Per trade', 'Size based', 'Percentage based', 'Stockpicker'] as const;
export type CommissionModel = typeof commissionModels[number];
export interface Swap { use: boolean; type: 'money' | 'points' | 'percent'; long: number; short: number; tripleSwapOn: string; rolloutHour: string }
export interface Commission { model: CommissionModel; value: number; unit: string; min: number; minUnit: string; max: number; maxUnit: string }
export interface FileInstrument {
  symbol: string; name: string; type: string; broker: string; brokerName: string;
  pointValue: number; tickSize: number; tickStep: number; spread: number; slippage: number;
  minDistance: number; multiplier: number; sizeStep: number; timezone: string;
  commission: Commission; swap: Swap;
}
export interface FileDefinition {
  id: string; symbol: string; instrument: string; underlying: string; source: string;
  timeframe: string; broker: string; brokerName: string; timezone: string; category: string;
  from: string; to: string; bars: number; barType: 'start' | 'end'; connection: 'History';
}
export interface InstrumentBroker { id: string; name: string; postfix: string; timezone: string }
export interface InstrumentMassPatch { fields: Partial<Record<'type'|'pointValue'|'tickSize'|'tickStep'|'spread'|'slippage'|'minDistance'|'multiplier'|'sizeStep'|'commission'|'swap', boolean>>; value: FileInstrument }
export const days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'];
export function defaultCommission(model: CommissionModel = 'None'): Commission {
  return { model, value: model === 'Stockpicker' ? 0.0035 : 0, unit: 'share', min: 0.35, minUnit: 'money', max: 1, maxUnit: 'equity' };
}
export function newInstrument(type = 'Forex'): FileInstrument {
  return { symbol: '', name: '', type, broker: '-1', brokerName: 'Default', timezone: 'UTC',
    pointValue: type === 'Stock' || type === 'Futures' ? 1 : 100000,
    tickSize: type === 'Stock' ? 0.01 : type === 'Futures' ? 0.1 : 0.0001,
    tickStep: type === 'Stock' ? 0.01 : type === 'Futures' ? 0.1 : 0.00001,
    spread: type === 'Stock' || type === 'Futures' ? 0 : 1, slippage: 0, minDistance: 0, multiplier: 1, sizeStep: 1,
    commission: defaultCommission(), swap: { use: false, type: 'money', long: 0, short: 0, tripleSwapOn: 'WEDNESDAY', rolloutHour: '23:00' } };
}
// Existing fixture values are preserved; missing specification fields use documented mock defaults.
export const seedInstruments: FileInstrument[] = instruments.map(item => ({ ...newInstrument(item.type), ...item }));
export function effectiveInstruments(custom: FileInstrument[], overrides: Record<string, FileInstrument> = {}, removed: string[] = []): FileInstrument[] {
  const hidden = new Set(removed.map(name => name.toLowerCase()));
  return [...seedInstruments, ...custom].filter(item => !hidden.has(item.symbol.toLowerCase()))
    .map(item => structuredClone(overrides[item.symbol] ?? item));
}
export function validateName(name: string, existing: string[], label = 'Symbol'): void {
  if (!name || name.length > 128 || !/^[a-zA-Z0-9_@.:$]+$/.test(name)) throw new Error(`${label} name is required (maximum 128 characters); use letters, numbers, or _ @ . : $.`);
  if (existing.some(item => item.toLowerCase() === name.toLowerCase())) throw new Error(`${label} ${name} already exists.`);
}
export function validateInstrument(item: FileInstrument, existing: string[], brokers: string[]): void {
  validateName(item.symbol, existing, 'Instrument');
  if (['name','type','broker','brokerName','timezone'].some(key => typeof (item as unknown as Record<string, unknown>)[key] !== 'string')) throw new Error('Invalid instrument metadata.');
  if (!brokers.includes(item.broker) || !dataTypes.includes(item.type as typeof dataTypes[number])) throw new Error('Choose a valid broker profile and data type.');
  for (const key of ['pointValue', 'tickSize', 'tickStep', 'spread', 'slippage', 'minDistance', 'multiplier', 'sizeStep'] as const) {
    if (!Number.isFinite(item[key]) || item[key] < (key === 'multiplier' ? 1 : 0)) throw new Error('Instrument values must be finite and within their allowed ranges.');
  }
  const c = item.commission;
  if (!commissionModels.includes(c.model) || !Number.isFinite(c.value) || Math.abs(c.value) > (c.model === 'Percentage based' ? 100 : 100000) || (c.model === 'Stockpicker' && (c.value < 0 || !['share','order','equity'].includes(c.unit) || !['money','equity'].includes(c.minUnit) || !['money','equity'].includes(c.maxUnit) || [c.min,c.max].some(value => !Number.isFinite(value) || value < 0 || value > 100000)))) throw new Error('Invalid commission settings.');
  const swap = item.swap;
  if (typeof swap.use !== 'boolean' || !['money','points','percent'].includes(swap.type) || !Number.isFinite(swap.long) || !Number.isFinite(swap.short) || !days.includes(swap.tripleSwapOn) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(swap.rolloutHour)) throw new Error('Invalid swap settings.');
}
export function canonicalInstrument(item: FileInstrument): FileInstrument {
  return { symbol:item.symbol,name:item.name,type:item.type,broker:item.broker,brokerName:item.brokerName,
    pointValue:item.pointValue,tickSize:item.tickSize,tickStep:item.tickStep,spread:item.spread,slippage:item.slippage,
    minDistance:item.minDistance,multiplier:item.multiplier,sizeStep:item.sizeStep,timezone:item.timezone,
    commission:{...item.commission},swap:{...item.swap} };
}

export function applyMassPatch(item: FileInstrument, patch: InstrumentMassPatch): FileInstrument {
  const next = structuredClone(item);
  for (const key of Object.keys(patch.fields) as (keyof InstrumentMassPatch['fields'])[]) {
    if (patch.fields[key]) (next as unknown as Record<string, unknown>)[key] = structuredClone(patch.value[key]);
  }
  return next;
}

interface InstrumentsJson { version:1; kind:'instruments'; brokers:InstrumentBroker[]; instruments:FileInstrument[] }
function jsonObject(value:unknown):value is Record<string,unknown>{return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);}
export function serializeInstrumentsJson(items: FileInstrument[], brokers: InstrumentBroker[]): string {
  const used=new Set(items.map(item=>item.broker));
  const payload:InstrumentsJson={version:1,kind:'instruments',brokers:brokers.filter(item=>item.id!=='-1'&&used.has(item.id)).map(item=>({...item})),instruments:items.map(canonicalInstrument)};
  return JSON.stringify(payload,null,2);
}
export function parseInstrumentsJson(json:string,knownBrokers:InstrumentBroker[]):FileInstrument[]{
  if(!json||new Blob([json]).size>2_000_000)throw new Error('Select a valid Instruments JSON file.');
  let raw:unknown;try{raw=JSON.parse(json);}catch{throw new Error('Select a valid Instruments JSON file.');}
  if(!jsonObject(raw)||raw.version!==1||raw.kind!=='instruments'||!Array.isArray(raw.brokers)||!Array.isArray(raw.instruments)||raw.instruments.length>10_000)throw new Error('Select a valid Instruments JSON file.');
  const imported=new Map<string,InstrumentBroker>();
  for(const value of raw.brokers){if(!jsonObject(value)||typeof value.id!=='string'||typeof value.name!=='string'||typeof value.postfix!=='string'||typeof value.timezone!=='string')throw new Error('Invalid broker metadata in Instruments JSON.');imported.set(value.id,{id:value.id,name:value.name,postfix:value.postfix,timezone:value.timezone});}
  const results:FileInstrument[]=[];
  for(const value of raw.instruments){
    if(!jsonObject(value)||!jsonObject(value.commission)||!jsonObject(value.swap))throw new Error('Invalid instrument in Instruments JSON.');
    const source=structuredClone(value) as unknown as FileInstrument;const broker=imported.get(source.broker);const mapped=knownBrokers.find(item=>item.id===source.broker||item.name===(broker?.name??source.brokerName));
    const item=canonicalInstrument({...source,broker:mapped?.id??'-1',brokerName:mapped?.name??broker?.name??source.brokerName,timezone:source.timezone||mapped?.timezone||'UTC'});
    try{validateInstrument(item,results.map(row=>row.symbol),[...knownBrokers.map(row=>row.id),'-1']);}catch(cause){throw new Error(`Invalid instrument in Instruments JSON: ${cause instanceof Error?cause.message:'validation failed'}`);}
    results.push(item);
  }
  if(!results.length)throw new Error('No Instruments found to import.');return results;
}
