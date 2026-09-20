import { today, validDate, type Interval, type Preset } from './dukascopyDownload';

export type CryptoExchangeId = 'Binance' | 'BinanceCoinM' | 'BinanceUsdtM' | 'Bitfinex' | 'Poloniex' | 'Coinbase';
export interface CryptoExchange {
  id: CryptoExchangeId;
  menuLabel: string;
  title: string;
  timeframes: readonly string[];
  symbols: readonly CryptoSymbol[];
}
export interface CryptoSymbol { symbol: string; mockAvailableFrom: string }

const binanceTimeframes = ['M1', 'M3', 'M5', 'M15', 'M30', 'H1', 'H2', 'H4', 'H6', 'H8', 'H12', 'D1'] as const;

export const cryptoExchanges: readonly CryptoExchange[] = [
  { id: 'Binance', menuLabel: 'Binance spot', title: 'Add Binance symbol(s)', timeframes: binanceTimeframes, symbols: [
    ['BTCUSDT','2017-08-17'], ['ETHUSDT','2017-08-17'], ['BNBUSDT','2017-11-06'], ['SOLUSDT','2020-08-11'], ['XRPUSDT','2018-05-04'], ['ADAUSDT','2018-04-17'], ['DOGEUSDT','2019-07-05'], ['BTCUSDC','2018-11-17'], ['ETHBTC','2017-07-14'], ['LTCUSDT','2017-12-13'],
  ].map(([symbol, mockAvailableFrom]) => ({ symbol, mockAvailableFrom })) },
  { id: 'BinanceCoinM', menuLabel: 'Binance Coin-M', title: 'Add Binance Coin-M symbol(s)', timeframes: binanceTimeframes, symbols: [
    ['BTCUSD_PERP','2020-08-10'], ['ETHUSD_PERP','2020-08-10'], ['BNBUSD_PERP','2020-08-10'], ['XRPUSD_PERP','2020-08-10'], ['ADAUSD_PERP','2020-08-10'], ['DOGEUSD_PERP','2021-01-21'], ['SOLUSD_PERP','2021-04-02'], ['DOTUSD_PERP','2020-09-29'],
  ].map(([symbol, mockAvailableFrom]) => ({ symbol, mockAvailableFrom })) },
  { id: 'BinanceUsdtM', menuLabel: 'Binance USDT-M', title: 'Add Binance USDT-M symbol(s)', timeframes: binanceTimeframes, symbols: [
    ['BTCUSDT','2019-09-08'], ['ETHUSDT','2019-11-27'], ['BNBUSDT','2020-02-10'], ['SOLUSDT','2020-09-14'], ['XRPUSDT','2020-01-06'], ['ADAUSDT','2020-01-31'], ['DOGEUSDT','2020-07-10'], ['LINKUSDT','2020-01-16'], ['AVAXUSDT','2020-09-23'], ['1000SHIBUSDT','2021-05-10'],
  ].map(([symbol, mockAvailableFrom]) => ({ symbol, mockAvailableFrom })) },
  { id: 'Bitfinex', menuLabel: 'Bitfinex', title: 'Add Bitfinex symbol(s)', timeframes: ['M1','M5','M15','M30','H1','H3','H6','H12','D1'], symbols: [
    ['BTCUSD','2013-03-31'], ['ETHUSD','2016-03-09'], ['LTCUSD','2013-05-19'], ['XRPUSD','2017-05-19'], ['SOLUSD','2021-06-24'], ['ADAUSD','2017-11-29'], ['DOTUSD','2020-08-24'], ['BTCUST','2017-03-29'],
  ].map(([symbol, mockAvailableFrom]) => ({ symbol, mockAvailableFrom })) },
  { id: 'Poloniex', menuLabel: 'Poloniex', title: 'Add Poloniex symbol(s)', timeframes: ['M5','M15','M30','H2','H4','D1'], symbols: [
    ['BTC_USDT','2015-02-19'], ['ETH_USDT','2016-04-20'], ['TRX_USDT','2018-06-11'], ['XRP_USDT','2017-05-08'], ['DOGE_USDT','2019-04-17'], ['LTC_USDT','2015-02-19'], ['ETH_BTC','2015-08-08'], ['XMR_USDT','2016-12-30'],
  ].map(([symbol, mockAvailableFrom]) => ({ symbol, mockAvailableFrom })) },
  { id: 'Coinbase', menuLabel: 'Coinbase Pro', title: 'Add Coinbase Pro symbol(s)', timeframes: ['M1','M5','M15','H1','H6','D1'], symbols: [
    ['BTC-USD','2015-07-20'], ['ETH-USD','2016-05-18'], ['SOL-USD','2021-06-17'], ['XRP-USD','2021-02-25'], ['ADA-USD','2021-03-18'], ['DOGE-USD','2021-06-03'], ['LTC-USD','2016-08-17'], ['AVAX-USD','2021-09-30'],
  ].map(([symbol, mockAvailableFrom]) => ({ symbol, mockAvailableFrom })) },
] as const;

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
  category: 'Crypto'; barType: 'start'; from: string; to: string; bars: number; sourceDataId?: string;
}

export function cryptoDefinitions(exchangeId: CryptoExchangeId, symbols: string[], timeframe: string, postfix: string, existing: string[]): CryptoDefinition[] {
  const exchange = cryptoExchange(exchangeId);
  if (!symbols.length) throw new Error('No symbols selected');
  if (symbols.length > 1000 || new Set(symbols).size !== symbols.length || postfix.length > 64 || /[\x00-\x1f]/.test(postfix)) throw new Error('Invalid selection or postfix.');
  if (!exchange.timeframes.includes(timeframe)) throw new Error('Choose a supported timeframe.');
  const names = [...existing];
  return symbols.map(symbol => {
    if (!exchange.symbols.some(item => item.symbol === symbol)) throw new Error('Unknown Crypto symbol.');
    const name = symbol + postfix; validateCryptoName(name, names); names.push(name);
    return { id: `crypto:${exchangeId}:${name}`, symbol: name, underlying: symbol, instrument: symbol,
      source: 'Crypto', exchange: exchangeId, timeframe, broker: '-1', brokerName: '—', timezone: 'UTC',
      category: 'Crypto', barType: 'start', from: '', to: '', bars: 0 };
  });
}

export interface CryptoDownload { targets: CryptoDefinition[]; dateFrom: string; dateTo: string; dateType: Preset; overwrite: boolean }
export function cryptoStart(row: CryptoDefinition): string {
  return cryptoExchange(row.exchange).symbols.find(item => item.symbol === row.underlying)?.mockAvailableFrom ?? (row.from || today());
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
    if (from > request.dateTo) throw new Error(`Selected range is before mock data availability for ${row.symbol}.`);
    return [row.id, { from, to: request.dateTo }];
  }));
}
