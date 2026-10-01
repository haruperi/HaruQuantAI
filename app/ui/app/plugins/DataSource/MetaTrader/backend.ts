import { createDomainClient } from '../../../host/transport';
import type { Mt5Definition, Mt5Symbol } from './mt5Import';
import type { BrokerProfile } from './presentation';
const client = createDomainClient('/contributions/workspace.data_manager');
export interface MT5Record { id: string; symbol: string; underlying: string; instrument: string; timeframe: 'M1'; broker: string; date_from: string; date_to: string; bars: number; options: { metadata: { path?: string; description?: string; category?: string } } }
export const mt5Catalog = () => client.post<{ available: boolean; connected: boolean; reason: string; datasets: MT5Record[]; brokers?: BrokerProfile[] }>('/sources.meta_trader.catalog', {});
export const mt5Connect = (path: string) => client.post('/sources.meta_trader.connect', { path });
export const mt5Symbols = () => client.post<{ symbols: Mt5Symbol[] }>('/sources.meta_trader.symbols', {});
export const mt5Add = (row: Mt5Definition) => client.post<{ id: string }>('/sources.meta_trader.add', { symbol: row.underlying, postfix: row.symbol.slice(row.underlying.length), timeframe: row.timeframe, broker: row.broker });
export const mt5Download = (dataset_id: string, date_from: string, date_to: string) => client.post<{ job_id: string }>('/sources.meta_trader.download.start', { dataset_id, date_from, date_to });
export const mt5Status = (job_id: string) => client.post<{ state: string; progress: number; rows: number }>('/sources.meta_trader.download.status', { job_id });
export const mt5Cancel = (job_id: string) => client.post('/sources.meta_trader.download.cancel', { job_id });
