import { normalizeLegacyBranding } from '../../../app/branding';
import { create } from 'zustand';
import { defaultSQConfig, planSQAdd, sqCatalogues, sourceLabel, validateSQConfig, type SQConfig, type SQDefinition, type SQProfile, type SQProvider } from './sqData';
import { validateName } from '../FileImport/fileSymbols';
export interface SQJob { provider: SQProvider; definitions: SQDefinition[]; state: 'running' | 'paused' | 'cancelled' | 'failed' | 'completed'; progress: number; completed: number; error?: string }
interface Saved { definitions: SQDefinition[]; preferred: Record<SQProvider, SQConfig>; job: SQJob | null }
interface Store extends Saved { storageError: string; start: (provider: SQProvider, config: SQConfig, tickers: string[], agreed: boolean, profile: SQProfile, existing: string[], externalActive: boolean) => void; advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void }
export const sqActive = (state?: string) => state === 'running' || state === 'paused';
export const sqStorageKey = 'sqx-sq-data-v1';
function validateSaved(value: Saved) {
  if (!Array.isArray(value.definitions) || value.definitions.length > 10000 || !value.preferred) throw new Error('Invalid saved market data.');
  for (const provider of ['equity', 'futures'] as const) validateSQConfig(value.preferred[provider], provider);
  if (value.job && (!['equity', 'futures'].includes(value.job.provider) || !Array.isArray(value.job.definitions) || !value.job.definitions.length || value.job.definitions.length > 1000 || !['running', 'paused', 'cancelled', 'failed', 'completed'].includes(value.job.state) || !Number.isInteger(value.job.progress) || value.job.progress < 0 || value.job.progress > 100 || !Number.isInteger(value.job.completed) || value.job.completed < 0 || value.job.completed > value.job.definitions.length || (value.job.error !== undefined && typeof value.job.error !== 'string'))) throw new Error('Invalid saved market-data job.');
  for (const rows of [value.definitions, value.job?.definitions ?? []]) {
    const names: string[] = [];
    for (const row of rows) {
      validateName(row.symbol, names); names.push(row.symbol);
      if (!['equity', 'futures'].includes(row.provider) || row.id !== `sq:${row.provider}:${row.symbol}` || row.source !== sourceLabel(row.provider) || !sqCatalogues[row.provider].some(item => item.ticker === row.underlying) || row.instrument !== row.underlying || row.bars !== 0 || row.from !== '' || row.to !== '' || row.timeframe !== '—' || !['start', 'end'].includes(row.barType) || ![0, 1, 2].includes(row.timezoneType) || !Number.isInteger(row.timezoneShift) || Math.abs(row.timezoneShift) > 23 || !Array.isArray(row.availableTimeframes) || !row.availableTimeframes.length || row.availableTimeframes.some(tf => !['M1', 'D1'].includes(tf)) || ['timezone', 'broker', 'brokerName', 'category', 'availableFrom'].some(key => typeof row[key as keyof SQDefinition] !== 'string')) throw new Error('Invalid saved market-data definition.');
    }
  }
  if (value.job?.definitions.some(row => row.provider !== value.job!.provider)) throw new Error('Invalid job provider.');
}
export const useSQData = create<Store>((set, get) => {
  let initial: Saved = { definitions: [], preferred: { equity: defaultSQConfig(), futures: defaultSQConfig() }, job: null }; let storageError = '';
  try { const raw = localStorage.getItem(sqStorageKey); if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; } }
  catch { storageError = 'Saved market data could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>) {
    if (get().storageError) throw new Error(get().storageError);
    const { definitions, preferred, job } = { ...get(), ...patch }; const saved = { definitions, preferred, job }; validateSaved(saved);
    try { localStorage.setItem(sqStorageKey, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save market data in browser storage. No changes were applied.'); }
    set(patch);
  }
  function failure(cause: unknown) { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save market data.' } }); }
  return { ...initial, storageError,
    start: (provider, config, tickers, agreed, profile, existing, externalActive) => {
      if (externalActive || sqActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      const definitions = planSQAdd(provider, config, tickers, agreed, profile, [...existing, ...get().definitions.map(row => row.symbol)]);
      if (get().definitions.length + definitions.length > 10000) throw new Error('Mock dataset limit reached.');
      persist({ preferred: { ...get().preferred, [provider]: { ...config, symbols: '' } }, job: { provider, definitions, state: 'running', progress: 0, completed: 0 } });
    },
    advance: () => {
      const { job, definitions } = get(); if (job?.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5); const completed = Math.floor(progress * job.definitions.length / 100);
      try { persist({ definitions: [...definitions, ...job.definitions.slice(job.completed, completed)], job: { ...job, completed, progress, state: progress === 100 ? 'completed' : 'running' } }); } catch (cause) { failure(cause); }
    },
    action: action => { const job = get().job; if (!job || !sqActive(job.state)) return; try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); } catch (cause) { failure(cause); } },
  };
});
export function reservedSQDefinitions() { const state = useSQData.getState(); if (state.storageError) throw new Error(state.storageError); return [...state.definitions, ...(sqActive(state.job?.state) ? state.job!.definitions : [])]; }
