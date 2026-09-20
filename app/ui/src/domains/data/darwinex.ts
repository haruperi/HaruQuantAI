import raw from '../../../../../data/market/darwinex/darwinex.csv?raw';
import { validateName } from './fileSymbols';
import type { BrokerProfile } from './dukascopy';
import { today, validDate, type Interval, type Preset } from './dukascopyDownload';
export interface DarwinexSymbol { symbol: string; dateFrom: string; metadata: number[] }
export function parseDarwinex(text: string): DarwinexSymbol[] {
  const seen = new Set<string>();
  return text.split(/\r?\n/).filter(line => line.trim()).map(line => {
    const [symbol, date, ...values] = line.split(';'); const parts = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec(date);
    const dateFrom = parts ? `${parts[3]}-${parts[2].padStart(2, '0')}-${parts[1].padStart(2, '0')}` : '';
    if (!symbol || seen.has(symbol) || values.length !== 6 || values.some(value => !value.trim() || !Number.isFinite(Number(value))) || !validDate(dateFrom)) throw new Error('Invalid Darwinex catalogue');
    seen.add(symbol); return { symbol, dateFrom, metadata: values.map(Number) };
  });
}
export const darwinexCatalogue = parseDarwinex(raw);
export interface DarwinexDefinition { id: string; symbol: string; underlying: string; instrument: string; source: 'Darwinex'; timeframe: 'TICK'; broker: string; brokerName: string; timezone: string; category: string; from: string; to: string; bars: number; sourceDataId?: string }
export interface DarwinexManifest { folder: string; symbols: string[]; fileCount: number }
export function discoverDarwinex(paths: string[]): DarwinexManifest {
  if (!paths.length || paths.length > 20000) throw new Error('Select a folder containing at most 20,000 files.');
  const parts = paths.map(path => { const fields = path.split('/'); if (path.length > 1024 || fields.length < 2 || fields.some(value => !value || value === '.' || value === '..' || /[\\:\x00-\x1f]/.test(value))) throw new Error('Invalid folder structure.'); return fields; });
  const folder = parts[0][0]; if (parts.some(row => row[0] !== folder)) throw new Error('Select one Darwinex data folder.');
  let symbols = [...new Set(parts.filter(row => row.length === 3 && row[2].endsWith('log.gz')).map(row => row[1]))];
  if (!symbols.length && darwinexCatalogue.some(row => row.symbol === folder) && parts.some(row => row.length === 2 && row[1].endsWith('log.gz'))) symbols = [folder];
  if (symbols.length > 1000) throw new Error('Select at most 1,000 symbols.');
  return { folder, symbols, fileCount: paths.length };
}
export function darwinexDefinitions(symbols: string[], postfix: string, existing: string[], broker?: BrokerProfile, mappings: Record<string, string> = {}, requireCatalogue = true): DarwinexDefinition[] {
  if (!symbols.length) throw new Error('No symbols selected');
  if (symbols.length > 1000 || new Set(symbols).size !== symbols.length || postfix.length > 64) throw new Error('Invalid selection or postfix.');
  const names = [...existing];
  return symbols.flatMap(symbol => {
    if (requireCatalogue && !darwinexCatalogue.some(row => row.symbol === symbol)) throw new Error('Unknown Darwinex symbol.');
    const mapping = broker ? mappings[symbol] : '-1';
    if (mapping === '-1000') return [];
    if (broker && mapping !== '-1' && (!mapping || mapping.startsWith('[') || !broker.instruments.includes(mapping))) throw new Error('Select proper instrument or skip the symbol');
    const name = symbol + postfix; validateName(name, names); names.push(name);
    return [{ id: `darwinex:${name}`, symbol: name, underlying: symbol, instrument: mapping === '-1' ? symbol : mapping, source: 'Darwinex' as const, timeframe: 'TICK' as const, broker: broker?.id ?? '-1', brokerName: broker?.name ?? 'Default', timezone: broker?.timezone ?? 'UTC', category: 'Tick data', from: '', to: '', bars: 0 }];
  });
}
export interface DarwinexDownload { targets: DarwinexDefinition[]; dateFrom: string; dateTo: string; dateType: Preset; overwrite: boolean }
export function darwinexStart(row: DarwinexDefinition): string { return darwinexCatalogue.find(item => item.symbol === row.underlying)?.dateFrom ?? (row.from || today()); }
export function darwinexTargets(rows: DarwinexDefinition[]): DarwinexDefinition[] {
  const targets = rows.filter(row => row.source === 'Darwinex');
  if (!targets.length) throw new Error('You must select at least one Darwinex record.');
  if (targets.some(row => row.sourceDataId)) throw new Error('You cannot download to cloned data.');
  return targets;
}
export function darwinexDownloadRanges(request: DarwinexDownload, now = today()): Record<string, Interval> {
  const targets = darwinexTargets(request.targets);
  if (targets.length !== request.targets.length || targets.length > 1000 || new Set(targets.map(row => row.id)).size !== targets.length) throw new Error('Invalid Darwinex targets.');
  if (!['sinceLast','sixMonths','year','fiveYears','tenYears','allTime','custom'].includes(request.dateType) || typeof request.overwrite !== 'boolean') throw new Error('Invalid download options.');
  if (!validDate(request.dateFrom) || !validDate(request.dateTo) || request.dateFrom > request.dateTo || request.dateTo > now) throw new Error('Choose a valid date range with From on or before To, no later than today.');
  return Object.fromEntries(targets.map(row => {
    const minimum = darwinexStart(row);
    const from = request.dateType === 'sinceLast' ? row.to || minimum : request.dateType === 'allTime' ? minimum : request.dateFrom < minimum ? minimum : request.dateFrom;
    if (from > request.dateTo) throw new Error(`Selected range is before data availability for ${row.symbol}.`);
    return [row.id, { from, to: request.dateTo }];
  }));
}
