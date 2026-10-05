import { today, validDate, type Interval, type Preset } from './presentation';

export interface YahooTicker {
  ticker: string; name: string; exchange: string; category: 'Stocks' | 'ETF' | 'Index' | 'Forex' | 'Crypto' | 'Unknown'; availableFrom?: string;
}

export function parseYahooSymbols(value: string): string[] {
  const tokens = value.split(/[\n,;]+/).map(item => item.trim()).filter(Boolean);
  if (!tokens.length) throw new Error('Enter at least one Yahoo ticker.');
  if (tokens.length > 1000) throw new Error('A maximum of 1000 Yahoo tickers can be added at once.');
  const canonical = tokens.map(token => token.toUpperCase());
  if (new Set(canonical).size !== canonical.length) throw new Error('Remove duplicate Yahoo tickers.');
  return canonical;
}

export function validateYahooName(name: string, existing: string[]): void {
  if (!name || name.length > 128 || !/^[a-zA-Z0-9_@.\-:$^=]+$/.test(name)) throw new Error('Yahoo symbol name is required (maximum 128 characters); use a valid ticker and postfix.');
  if (existing.includes(name)) throw new Error(`Symbol ${name} already exists.`);
}

export interface YahooDefinition {
  id: string; symbol: string; underlying: string; instrument: string; name: string; exchange: string;
  source: 'Yahoo'; timeframe: 'D1'; broker: '-1'; brokerName: '—'; timezone: 'UTC';
  category: YahooTicker['category']; barType: 'start'; from: string; to: string; bars: number; sourceDataId?: string; availableFrom?: string;
}

export function yahooDefinitions(value: string, postfix: string, existing: string[]): YahooDefinition[] {
  if (postfix.length > 64 || /[\x00-\x1f]/.test(postfix)) throw new Error('Data postfix must be 64 characters or fewer and contain no control characters.');
  const names = [...existing];
  return parseYahooSymbols(value).map(symbol => {
    const finalName = symbol + postfix; validateYahooName(finalName, names); names.push(finalName);
    return { id: `pending:${finalName}`, symbol: finalName, underlying: symbol, instrument: symbol,
      name: symbol, exchange: '', source: 'Yahoo', timeframe: 'D1', broker: '-1', brokerName: '—',
      timezone: 'UTC', category: 'Unknown', barType: 'start', from: '', to: '', bars: 0 };

  });
}

export interface YahooDownload { targets: YahooDefinition[]; dateFrom: string; dateTo: string; dateType: Preset; overwrite: boolean }
export function yahooStart(row: YahooDefinition): string {
  return row.availableFrom || row.from || '1970-01-01';
}
export function yahooTargets(rows: YahooDefinition[], activeIds: string[] = []): YahooDefinition[] {
  const targets = rows.filter(row => row.source === 'Yahoo');
  if (!targets.length) throw new Error('You must select at least one Yahoo record.');
  if (targets.some(row => row.sourceDataId)) throw new Error('You cannot download to cloned data.');
  const available = targets.filter(row => !activeIds.includes(row.id));
  if (!available.length) throw new Error('Cannot start another action on data in progress.');
  return available;
}
export function yahooDownloadRanges(request: YahooDownload, now = today()): Record<string, Interval> {
  if (!request.targets.length || request.targets.length > 1000 || new Set(request.targets.map(row => row.id)).size !== request.targets.length || request.targets.some(row => row.source !== 'Yahoo' || row.sourceDataId)) throw new Error('Select eligible Yahoo records.');
  if (!['sinceLast','sixMonths','year','fiveYears','tenYears','allTime','custom'].includes(request.dateType) || typeof request.overwrite !== 'boolean') throw new Error('Invalid Yahoo download options.');
  if (!validDate(request.dateFrom) || !validDate(request.dateTo) || request.dateFrom > request.dateTo || request.dateTo > now) throw new Error('Choose a valid date range with From on or before To, no later than today.');
  return Object.fromEntries(request.targets.map(row => {
    const minimum = yahooStart(row);
    const requested = request.dateType === 'sinceLast' ? row.to || minimum : request.dateType === 'allTime' ? minimum : request.dateFrom;
    const from = requested < minimum ? minimum : requested;
    if (from > request.dateTo) throw new Error(`Selected range is before source data availability for ${row.symbol}.`);
    return [row.id, { from, to: request.dateTo }];
  }));
}
