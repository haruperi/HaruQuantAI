import { createDomainClient } from '../../../host/transport';
import type { SQConfig, SQProvider } from './sqData';
const client = createDomainClient('/contributions/workspace.data_manager');
export interface SQSymbol { ticker: string; name: string; exchange: string; timeframe: string; date_from: string; date_to: string; commodity_code: string | null }
export interface SQRecord { id: string; symbol: string; underlying: string; instrument: string; source: string; timeframe: string; timezone: string; broker: string; bars: number; date_from: string; date_to: string; options: { metadata: SQSymbol } }
export interface SQCatalog { available: boolean; reason: string; datasets: SQRecord[]; exchanges: string[]; credentials_configured: boolean; catalog_rows: number }
export const sqCatalog = (provider: SQProvider) => client.post<SQCatalog>(`/sources.sq_${provider}.catalog`, {});
export const sqLookup = (provider: SQProvider, config: SQConfig) => client.post<{ symbols: SQSymbol[] }>(`/sources.sq_${provider}.lookup`, { query: config.symbols, exchange: config.exchange, exact: config.exact, search_ticker: config.searchInTicker, search_name: config.searchInName, continuous_only: provider === 'futures' && config.onlyContFutures });
export const sqAdd = (provider: SQProvider, symbol: SQSymbol, config: SQConfig) => client.post<{ id: string }>(`/sources.sq_${provider}.add`, { symbol: symbol.ticker, postfix: config.postfix, timeframe: symbol.timeframe === 'D' ? 'D1' : 'M1' });
