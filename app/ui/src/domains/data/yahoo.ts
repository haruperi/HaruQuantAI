import { today, validDate, type Interval, type Preset } from './dukascopyDownload';

export interface YahooTicker {
  ticker: string; name: string; exchange: string; category: 'Stocks' | 'ETF' | 'Index' | 'Forex' | 'Crypto'; mockAvailableFrom: string;
}

export const yahooTickers: readonly YahooTicker[] = [
  { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', category: 'Stocks', mockAvailableFrom: '1980-12-12' },
  { ticker: 'AMZN', name: 'Amazon.com, Inc.', exchange: 'NASDAQ', category: 'Stocks', mockAvailableFrom: '1997-05-15' },
  { ticker: 'MSFT', name: 'Microsoft Corporation', exchange: 'NASDAQ', category: 'Stocks', mockAvailableFrom: '1986-03-13' },
  { ticker: 'NVDA', name: 'NVIDIA Corporation', exchange: 'NASDAQ', category: 'Stocks', mockAvailableFrom: '1999-01-22' },
  { ticker: 'TSLA', name: 'Tesla, Inc.', exchange: 'NASDAQ', category: 'Stocks', mockAvailableFrom: '2010-06-29' },
  { ticker: 'SPY', name: 'SPDR S&P 500 ETF Trust', exchange: 'NYSE Arca', category: 'ETF', mockAvailableFrom: '1993-01-29' },
  { ticker: '^GSPC', name: 'S&P 500 Index', exchange: 'SNP', category: 'Index', mockAvailableFrom: '1950-01-03' },
  { ticker: 'EURUSD=X', name: 'EUR/USD', exchange: 'CCY', category: 'Forex', mockAvailableFrom: '2003-12-01' },
  { ticker: 'BTC-USD', name: 'Bitcoin USD', exchange: 'CCC', category: 'Crypto', mockAvailableFrom: '2014-09-17' },
] as const;

export function parseYahooSymbols(value: string): string[] {
  const tokens = value.split(/[\n,;]+/).map(item => item.trim()).filter(Boolean);
  if (!tokens.length) throw new Error('Enter at least one Yahoo ticker.');
  if (tokens.length > 1000) throw new Error('A maximum of 1000 Yahoo tickers can be added at once.');
  const canonical = tokens.map(token => yahooTickers.find(item => item.ticker.toLowerCase() === token.toLowerCase())?.ticker ?? token);
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
  category: YahooTicker['category']; barType: 'start'; from: string; to: string; bars: number; sourceDataId?: string;
}

export function yahooDefinitions(value: string, postfix: string, existing: string[]): YahooDefinition[] {
  if (postfix.length > 64 || /[\x00-\x1f]/.test(postfix)) throw new Error('Data postfix must be 64 characters or fewer and contain no control characters.');
  const names = [...existing];
  return parseYahooSymbols(value).map(symbol => {
    const ticker = yahooTickers.find(item => item.ticker === symbol);
    if (!ticker) throw new Error(`Symbol '${symbol}' not found in the offline Yahoo catalog.`);
    const finalName = ticker.ticker + postfix; validateYahooName(finalName, names); names.push(finalName);
    return { id: `yahoo:${finalName}`, symbol: finalName, underlying: ticker.ticker, instrument: ticker.ticker,
      name: ticker.name, exchange: ticker.exchange, source: 'Yahoo', timeframe: 'D1', broker: '-1', brokerName: '—',
      timezone: 'UTC', category: ticker.category, barType: 'start', from: '', to: '', bars: 0 };
  });
}

export interface YahooDownload { targets: YahooDefinition[]; dateFrom: string; dateTo: string; dateType: Preset; overwrite: boolean }
export function yahooStart(row: YahooDefinition): string {
  return yahooTickers.find(item => item.ticker === row.underlying)?.mockAvailableFrom ?? (row.from || today());
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
    if (from > request.dateTo) throw new Error(`Selected range is before mock data availability for ${row.symbol}.`);
    return [row.id, { from, to: request.dateTo }];
  }));
}
