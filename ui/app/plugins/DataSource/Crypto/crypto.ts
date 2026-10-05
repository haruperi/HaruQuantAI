import { today, validDate, type Interval, type Preset } from './presentation';

export type CryptoExchangeId = 'Binance' | 'BinanceCoinM' | 'BinanceUsdtM' | 'Bitfinex' | 'Poloniex' | 'Coinbase';
export interface CryptoExchange {
  id: CryptoExchangeId;
  menuLabel: string;
  title: string;
  timeframes: readonly string[];
  symbols: readonly CryptoSymbol[];
}
export interface CryptoSymbol { symbol: string; availableFrom?: string }

export const cryptoExchanges: readonly CryptoExchange[] = [
  { id: 'Binance', menuLabel: 'Binance spot', title: 'Add Binance symbol(s)', timeframes: [], symbols: [] },
  { id: 'BinanceCoinM', menuLabel: 'Binance Coin-M', title: 'Add Binance Coin-M symbol(s)', timeframes: [], symbols: [] },
  { id: 'BinanceUsdtM', menuLabel: 'Binance USDT-M', title: 'Add Binance USDT-M symbol(s)', timeframes: [], symbols: [] },
  { id: 'Bitfinex', menuLabel: 'Bitfinex', title: 'Add Bitfinex symbol(s)', timeframes: [], symbols: [] },
  { id: 'Poloniex', menuLabel: 'Poloniex', title: 'Add Poloniex symbol(s)', timeframes: [], symbols: [] },
  { id: 'Coinbase', menuLabel: 'Coinbase Pro', title: 'Add Coinbase Pro symbol(s)', timeframes: [], symbols: [] },
];

export function cryptoExchange(id: string): CryptoExchange {
  const exchange = cryptoExchanges.find(item => item.id === id);
  if (!exchange) throw new Error('Unknown Crypto exchange.');
  return exchange;
}

export function validateCryptoName(name: string, existing: string[]): void {
  if (!name || name.length > 128 || !/^[a-zA-Z0-9_@.\-:$]+$/.test(name)) throw new Error('Symbol name is required (maximum 128 characters); use letters, numbers, or _ @ . - : $.');
  if (existing.includes(name)) throw new Error(`Symbol ${name} already exists.`);
}

export interface CryptoDefinition {
  id: string; symbol: string; underlying: string; instrument: string; source: 'Crypto';
  exchange: CryptoExchangeId; timeframe: string; broker: '-1'; brokerName: '—'; timezone: 'UTC';
  category: 'Crypto'; barType: 'start'; from: string; to: string; bars: number; sourceDataId?: string; availableFrom?: string;
}

export function cryptoDefinitions(exchangeId: CryptoExchangeId, symbols: string[], timeframe: string, postfix: string, existing: string[]): CryptoDefinition[] {
  cryptoExchange(exchangeId);
  if (!symbols.length) throw new Error('No symbols selected');
  if (symbols.length > 1000 || new Set(symbols).size !== symbols.length || postfix.length > 64 || /[\x00-\x1f]/.test(postfix)) throw new Error('Invalid selection or postfix.');
  const names = [...existing];
  return symbols.map(symbol => {
    const name = symbol + postfix; validateCryptoName(name, names); names.push(name);
    return { id: `crypto:${exchangeId}:${name}`, symbol: name, underlying: symbol, instrument: symbol,
      source: 'Crypto', exchange: exchangeId, timeframe, broker: '-1', brokerName: '—', timezone: 'UTC',
      category: 'Crypto', barType: 'start', from: '', to: '', bars: 0 };
  });
}

export interface CryptoDownload { targets: CryptoDefinition[]; dateFrom: string; dateTo: string; dateType: Preset; overwrite: boolean }
export function cryptoStart(row: CryptoDefinition): string {
  return row.availableFrom || row.from || '2020-01-01';
}
export function cryptoTargets(rows: CryptoDefinition[], activeIds: string[] = []): CryptoDefinition[] {
  const targets = rows.filter(row => row.source === 'Crypto');
  if (!targets.length) throw new Error('You must select at least one Crypto record.');
  if (targets.some(row => row.sourceDataId)) throw new Error('You cannot download to cloned data.');
  const available = targets.filter(row => !activeIds.includes(row.id));
  if (!available.length) throw new Error('Cannot start another action on data in progress.');
  return available;
}
export function cryptoDownloadRanges(request: CryptoDownload, now = today()): Record<string, Interval> {
  if (!request.targets.length || request.targets.length > 1000 || new Set(request.targets.map(row => row.id)).size !== request.targets.length || request.targets.some(row => row.source !== 'Crypto' || row.sourceDataId)) throw new Error('Select eligible Crypto records.');
  if (!['sinceLast','sixMonths','year','fiveYears','tenYears','allTime','custom'].includes(request.dateType) || typeof request.overwrite !== 'boolean') throw new Error('Invalid download options.');
  if (!validDate(request.dateFrom) || !validDate(request.dateTo) || request.dateFrom > request.dateTo || request.dateTo > now) throw new Error('Choose a valid date range with From on or before To, no later than today.');
  return Object.fromEntries(request.targets.map(row => {
    const minimum = cryptoStart(row);
    const from = request.dateType === 'sinceLast' ? row.to || minimum : request.dateType === 'allTime' ? minimum : request.dateFrom < minimum ? minimum : request.dateFrom;
    if (from > request.dateTo) throw new Error(`Selected range is before the acquisition start for ${row.symbol}.`);
    return [row.id, { from, to: request.dateTo }];
  }));
}
