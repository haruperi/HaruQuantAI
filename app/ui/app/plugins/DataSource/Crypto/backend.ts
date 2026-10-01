import { createDomainClient } from '../../../host/transport';
import type { CryptoExchangeId } from './crypto';
const client = createDomainClient('/contributions/workspace.data_manager');
export const exchangeNames: Record<CryptoExchangeId, string> = { Binance: 'Binance', BinanceCoinM: 'Binance Coin-M', BinanceUsdtM: 'Binance USDT-M', Bitfinex: 'Bitfinex', Coinbase: 'Coinbase Pro', Poloniex: 'Poloniex' };
export const exchangeId = (name: string) => Object.entries(exchangeNames).find(([, value]) => value === name)?.[0] as CryptoExchangeId;
export interface CryptoRecord { id: string; symbol: string; underlying: string; instrument: string; timeframe: string;
  date_from: string; date_to: string; bars: number; options: { parameters: { exchange: string }; metadata: { date_from?: number } } }
export interface CryptoStatus { job_id: string; state: string; rows: number; published_partitions: number; progress: number }
export const cryptoCatalog = () => client.post<{ available: boolean; reason: string; datasets: CryptoRecord[]; exchanges: { name: string; timeframes: string[] }[] }>('/sources.crypto.catalog', {});
export const cryptoSymbols = (exchange: CryptoExchangeId) => client.post<{ symbols: string[] }>('/sources.crypto.symbols', { exchange: exchangeNames[exchange] });
export const cryptoAdd = (symbol: string, postfix: string, exchange: CryptoExchangeId, timeframe: string) => client.post<{ id: string }>('/sources.crypto.add', { symbol, postfix, exchange: exchangeNames[exchange], timeframe });
export const cryptoDownload = (dataset_id: string, date_from: string, date_to: string, overwrite: boolean) => client.post<{ job_id: string }>('/sources.crypto.download.start', { dataset_id, date_from, date_to, overwrite });
export const cryptoStatus = (job_id: string) => client.post<CryptoStatus>('/sources.crypto.download.status', { job_id });
export const cryptoCancel = (job_id: string) => client.post<CryptoStatus>('/sources.crypto.download.cancel', { job_id });
