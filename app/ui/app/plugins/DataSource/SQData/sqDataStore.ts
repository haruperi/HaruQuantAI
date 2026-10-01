import { create } from 'zustand';
import { sqAdd, sqCatalog, sqLookup, type SQSymbol } from './backend';
import { defaultSQConfig, validateName, type SQConfig, type SQDefinition, type SQProfile, type SQProvider } from './sqData';

export interface SQJob { provider: SQProvider; definitions: SQDefinition[]; state: 'running' | 'cancelled' | 'failed' | 'completed'; progress: number; completed: number; error?: string; canPause: false }
interface Store {
  definitions: SQDefinition[]; preferred: Record<SQProvider, SQConfig>; job: SQJob | null;
  backendAvailable: boolean; storageError: string; exchanges: Record<SQProvider, string[]>; credentials: Record<SQProvider, boolean>;
  refresh: () => Promise<void>;
  start: (provider: SQProvider, config: SQConfig, tickers: string[], agreed: boolean, profile: SQProfile, existing: string[], externalActive: boolean) => void;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
export const sqActive = (state?: string) => state === 'running';
export const sqStorageKey = 'sqx-sq-data-v1';
export const useSQData = create<Store>((set, get) => {
  let cancelled = false;
  const refresh = async () => {
    const results = await Promise.allSettled((['equity', 'futures'] as const).map(async provider => ({ provider, catalog: await sqCatalog(provider) })));
    const definitions: SQDefinition[] = [];
    const exchanges = { equity: [] as string[], futures: [] as string[] };
    const credentials = { equity: false, futures: false }; const errors: string[] = [];
    for (const result of results) {
      if (result.status === 'rejected') { errors.push(result.reason instanceof Error ? result.reason.message : 'SQ source unavailable.'); continue; }
      const { provider, catalog } = result.value;
      exchanges[provider] = catalog.exchanges; credentials[provider] = catalog.credentials_configured;
      if (!catalog.available) errors.push(catalog.reason);
      for (const row of catalog.datasets) definitions.push({ ...row, provider, brokerName: row.broker === '-1' ? 'Default' : row.broker, category: provider === 'equity' ? 'Equity' : 'Futures', availableTimeframes: [row.timeframe], timezoneType: 2, timezoneShift: 0, barType: 'end', from: row.date_from || '', to: row.date_to || '', availableFrom: row.options.metadata.date_from || '' });
    }
    set({ backendAvailable: results.some(result => result.status === "fulfilled" && result.value.catalog.available), definitions, exchanges, credentials, storageError: errors.join(' ') });
  };
  async function add(provider: SQProvider, config: SQConfig, tickers: string[]) {
    try {
      const found = new Map<string, SQSymbol>();
      for (const ticker of tickers) {
        if (cancelled) break;
        const result = await sqLookup(provider, { ...config, symbols: ticker, exact: true, searchInTicker: true, searchInName: false });
        const symbol = result.symbols.find(row => row.ticker === ticker);
        if (!symbol) throw new Error(`Source catalog no longer contains ${ticker}.`);
        found.set(ticker, symbol);
      }
      for (const ticker of tickers) {
        if (cancelled) break;
        const symbol = found.get(ticker); if (!symbol) throw new Error('Source symbol unavailable.');
        await sqAdd(provider, symbol, config);
        const job = get().job!; const completed = job.completed + 1;
        set({ job: { ...job, completed, progress: completed / tickers.length * 100 } });
      }
      set({ job: { ...get().job!, state: cancelled ? 'cancelled' : 'completed' } });
    } catch (error) { set({ job: { ...get().job!, state: 'failed', error: error instanceof Error ? error.message : 'Source addition failed.' } }); }
    await refresh();
  }
  return {
    definitions: [], preferred: { equity: defaultSQConfig(), futures: defaultSQConfig() }, job: null, backendAvailable: false, storageError: '', exchanges: { equity: [], futures: [] }, credentials: { equity: false, futures: false }, refresh,
    start(provider, config, tickers, agreed, _profile, existing, externalActive) {
      if (externalActive || sqActive(get().job?.state)) throw new Error('Finish or stop the active operation first.');
      if (!agreed) throw new Error('Read and accept the data usage conditions first.');
      if (!tickers.length || tickers.length > 1000 || new Set(tickers).size !== tickers.length) throw new Error('Select 1–1,000 distinct tickers.');
      if (config.timezoneType !== 2) throw new Error('Source timestamps currently retain their original UTC canonical representation.');
      const names = [...existing]; for (const ticker of tickers) { validateName(ticker + config.postfix, names); names.push(ticker + config.postfix); }
      cancelled = false;
      set({ preferred: { ...get().preferred, [provider]: { ...config, symbols: '' } }, job: { provider, definitions: [], state: 'running', progress: 0, completed: 0, canPause: false } });
      void add(provider, config, tickers);
    },
    advance() { /* Progress follows completed backend operations. */ },
    action(action) { if (action === 'stop') cancelled = true; },
  };
});
export function reservedSQDefinitions() { return useSQData.getState().definitions; }
