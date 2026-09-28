import { presetRange, simulationSummary, today, validDate, type Interval, type Preset } from './presentation';

export interface Mt5Symbol {
  name: string;
  description: string;
  path: string;
  category: 'Forex' | 'Metals' | 'Indices' | 'Stocks' | 'Crypto';
  mockAvailableFrom: string;
}

/** Bounded stand-in for the runtime catalogue returned by a selected MT5 terminal. */
export const mt5Symbols: readonly Mt5Symbol[] = ([
  { name: 'EURUSD', description: 'Euro vs US Dollar', path: 'Forex\\Majors', category: 'Forex', mockAvailableFrom: '2010-01-04' },
  { name: 'GBPUSD', description: 'Great Britain Pound vs US Dollar', path: 'Forex\\Majors', category: 'Forex', mockAvailableFrom: '2010-01-04' },
  { name: 'USDJPY', description: 'US Dollar vs Japanese Yen', path: 'Forex\\Majors', category: 'Forex', mockAvailableFrom: '2010-01-04' },
  { name: 'AUDCAD', description: 'Australian Dollar vs Canadian Dollar', path: 'Forex\\Crosses', category: 'Forex', mockAvailableFrom: '2012-01-03' },
  { name: 'EURGBP', description: 'Euro vs Great Britain Pound', path: 'Forex\\Crosses', category: 'Forex', mockAvailableFrom: '2012-01-03' },
  { name: 'XAUUSD', description: 'Gold vs US Dollar', path: 'Metals', category: 'Metals', mockAvailableFrom: '2012-01-03' },
  { name: 'XAGUSD', description: 'Silver vs US Dollar', path: 'Metals', category: 'Metals', mockAvailableFrom: '2012-01-03' },
  { name: 'US500', description: 'US 500 Index', path: 'Indices', category: 'Indices', mockAvailableFrom: '2014-01-02' },
  { name: 'USTEC', description: 'US Tech 100 Index', path: 'Indices', category: 'Indices', mockAvailableFrom: '2014-01-02' },
  { name: 'AAPL', description: 'Apple Inc.', path: 'Stocks\\US', category: 'Stocks', mockAvailableFrom: '2015-01-02' },
  { name: 'MSFT', description: 'Microsoft Corporation', path: 'Stocks\\US', category: 'Stocks', mockAvailableFrom: '2015-01-02' },
  { name: 'BTCUSD', description: 'Bitcoin vs US Dollar', path: 'Crypto', category: 'Crypto', mockAvailableFrom: '2017-01-02' },
] satisfies Mt5Symbol[]).sort((a, b) => a.path.localeCompare(b.path) || a.name.localeCompare(b.name));

export interface Mt5Folder { folder: string; fileCount: number }

export function discoverMt5Folder(paths: string[]): Mt5Folder {
  if (!paths.length) throw new Error('Select an MT5 installation folder.');
  if (paths.length > 20000) throw new Error('Select a folder with at most 20,000 files for this mock import.');
  const parts = paths.map(path => {
    if (path.length > 1024) throw new Error('Invalid MT5 folder structure.');
    const segments = path.replaceAll('\\', '/').split('/');
    if (segments.some(part => !part || part === '.' || part === '..' || /[:\x00-\x1f]/.test(part))) throw new Error('Invalid MT5 folder structure.');
    return segments;
  });
  const folder = parts[0][0];
  if (parts.some(path => path[0] !== folder)) throw new Error('Select one MT5 installation folder.');
  const looksLikeMt5 = parts.some(path => /^(terminal64?\.exe)$/i.test(path.at(-1) ?? '')
    || path.some(part => /^(mql5|bases)$/i.test(part)));
  if (!looksLikeMt5) throw new Error('Selected folder does not look like a MetaTrader 5 installation.');
  return { folder, fileCount: paths.length };
}

export function filterMt5Symbols(query: string, category: string): Mt5Symbol[] {
  const needle = query.trim().toLowerCase();
  return mt5Symbols.filter(row => (!category || row.path === category)
    && (!needle || row.name.toLowerCase().includes(needle) || row.description.toLowerCase().includes(needle)));
}

export interface Mt5Definition {
  id: string; symbol: string; underlying: string; instrument: string; source: 'MT5'; timeframe: 'M1';
  broker: string; brokerName: string; timezone: string; category: Mt5Symbol['category']; barType: 'start';
  from: string; to: string; bars: number; path: string; description: string;
}

export interface Mt5ImportRequest {
  folder: string; symbols: string[]; dateFrom: string; dateTo: string; dateType: Preset;
  broker: string; brokerName: string; timezone: string; postfix: string;
}

export function nextMt5Name(base: string, existing: string[]): string {
  if (!existing.includes(base)) return base;
  let index = 1;
  while (existing.includes(`${base}_${index}`)) index += 1;
  return `${base}_${index}`;
}

export function mt5Definitions(request: Mt5ImportRequest, existing: string[]): Mt5Definition[] {
  if (!request.folder || request.folder.length > 255 || /[\\/\x00-\x1f]/.test(request.folder)) throw new Error('Select an MT5 installation folder.');
  if (!request.symbols.length) throw new Error('Select at least one MT5 symbol.');
  if (request.symbols.length > 1000) throw new Error('Select at most 1,000 MT5 symbols.');
  if (!request.broker || !request.brokerName || !request.timezone) throw new Error('Choose a valid broker profile.');
  if (request.postfix.length > 64 || /[\\/\x00-\x1f]/.test(request.postfix)) throw new Error('Data postfix must be 64 characters or fewer and contain no path separators.');
  if (!validDate(request.dateFrom) || !validDate(request.dateTo) || request.dateFrom > request.dateTo || request.dateTo > today()) throw new Error('Choose a valid date range with From on or before To, no later than today.');
  if (!['sinceLast', 'sixMonths', 'year', 'fiveYears', 'tenYears', 'allTime', 'custom'].includes(request.dateType)) throw new Error('Choose a valid date range.');
  const names = [...existing];
  return request.symbols.map(symbol => {
    const source = mt5Symbols.find(row => row.name === symbol);
    if (!source) throw new Error('Select symbols fetched from the chosen MT5 folder.');
    const name = nextMt5Name(source.name + request.postfix, names);
    names.push(name);
    if (name.length > 128) throw new Error('Generated MT5 data name is too long.');
    return { id: `mt5:${name}`, symbol: name, underlying: source.name, instrument: source.name,
      source: 'MT5', timeframe: 'M1', broker: request.broker, brokerName: request.brokerName,
      timezone: request.timezone, category: source.category, barType: 'start', from: '', to: '', bars: 0,
      path: source.path, description: source.description };
  });
}

export function mt5ImportRanges(request: Mt5ImportRequest): Record<string, Interval> {
  const now = today();
  if (!validDate(request.dateFrom) || !validDate(request.dateTo) || request.dateFrom > request.dateTo || request.dateTo > now) throw new Error('Choose a valid date range with From on or before To, no later than today.');
  return Object.fromEntries(request.symbols.map(symbol => {
    const source = mt5Symbols.find(row => row.name === symbol);
    if (!source) throw new Error('Select symbols fetched from the chosen MT5 folder.');
    const from = request.dateType === 'allTime' ? source.mockAvailableFrom
      : [request.dateFrom, source.mockAvailableFrom].sort().at(-1)!;
    if (from > request.dateTo) throw new Error(`Selected range is before mock data availability for ${symbol}.`);
    return [symbol, { from, to: request.dateTo }];
  }));
}

export function mt5Preset(preset: Preset, from: string, to: string): Interval {
  const minimum = mt5Symbols.map(row => row.mockAvailableFrom).sort()[0];
  return presetRange(preset, from, minimum, from, to);
}

export function mt5Summary(row: Mt5Definition, ranges: Interval[]) {
  return simulationSummary(row, ranges);
}
