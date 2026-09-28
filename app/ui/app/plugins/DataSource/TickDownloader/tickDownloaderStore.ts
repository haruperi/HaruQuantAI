import { normalizeLegacyBranding } from '../../../host/branding';
import { validateTD, type TDJob, type TDRequest } from './tickDownloader';
import { create } from 'zustand';

export function tdActive(state?: string): boolean {
  return ['running', 'paused'].includes(state ?? '');
}

export interface TDDefinition {
  id: string;
  source: string;
  symbol: string;
  underlying: string;
  instrument: string;
  timeframe: string;
  broker: string;
  brokerName: string;
  timezone: string;
  category: string;
  from: string;
  to: string;
  bars: number;
}

export interface TDState {
  definitions: TDDefinition[];
  job: TDJob | null;
  folder: string;
  postfix: string;
  storageError: string;
  start: (request: TDRequest, available: string[], existing?: string[], otherActive?: boolean) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}

const tdKey = 'sqx-tickdownloader-v1';

export const useTickDownloader = create<TDState>((set, get) => {
  let initial: Pick<TDState, 'definitions' | 'job' | 'folder' | 'postfix' | 'storageError'> = {
    definitions: [],
    job: null,
    folder: '',
    postfix: '',
    storageError: '',
  };
  try {
    const raw = localStorage.getItem(tdKey);
    if (raw) {
      const saved = normalizeLegacyBranding(JSON.parse(raw));
      if (saved.version !== 1 || !Array.isArray(saved.definitions) || saved.definitions.length > 10000 || typeof saved.folder !== 'string' || typeof saved.postfix !== 'string'
        || saved.definitions.some((row: TDDefinition) => !row || ['id','source','symbol','underlying','instrument','timeframe','broker','brokerName','timezone','category','from','to'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.bars !== 0)) throw new Error('Invalid saved import');
      if (saved.job) {
        if (!['running','paused','completed','cancelled','failed'].includes(saved.job.state) || !Number.isFinite(saved.job.progress) || saved.job.progress < 0 || saved.job.progress > 100) throw new Error('Invalid import job');
        validateTD(saved.job.request, saved.job.request.symbols, []);
        if (saved.job.state === 'running') saved.job.state = 'paused';
      }
      initial = { definitions: saved.definitions, folder: saved.folder, postfix: saved.postfix, job: saved.job ?? null, storageError: '' };
    }
  } catch { initial.storageError = 'Saved TickDownloader mock state could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<TDState>) {
    const next = { ...get(), ...patch };
    if (next.storageError) throw new Error(next.storageError);
    localStorage.setItem(tdKey, JSON.stringify({ version: 1, definitions: next.definitions, job: next.job, folder: next.folder, postfix: next.postfix }));
    set(patch);
  }
  return {
    ...initial,
    start: (request, available, existing = [], otherActive = false) => {
      if (otherActive) throw new Error('Finish or stop the active data operation first.');
      if (get().job && ['running', 'paused'].includes(get().job!.state)) throw new Error('Finish or stop the active import first.');
      validateTD(request, available, [...existing, ...get().definitions.map(row => row.symbol)]);
      if (get().definitions.length + request.symbols.length > 10000) throw new Error('Mock dataset limit reached.');
      const additions: TDDefinition[] = request.symbols.map(symbol => ({
        id: `td:${symbol + request.postfix}`,
        symbol: symbol + request.postfix,
        underlying: symbol,
        instrument: symbol,
        source: 'TickDownloader',
        timeframe: 'TICK',
        broker: '-1',
        brokerName: 'Default',
        timezone: 'UTC',
        category: 'Tick data',
        from: '',
        to: '',
        bars: 0,
      }));
      try { persist({ folder: request.folder, postfix: request.postfix, definitions: [...get().definitions, ...additions], job: { request: structuredClone(request), state: 'running', progress: 0 } }); }
      catch { throw new Error(get().storageError || 'Unable to save mock import. No import was started.'); }
    },
    advance: () => {
      const job = get().job; if (!job || job.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5);
      try { persist({ job: { ...job, progress, state: progress === 100 ? 'completed' : 'running' } }); }
      catch { set({ job: { ...job, state: 'failed', error: 'Unable to persist mock import progress.' } }); }
    },
    action: action => {
      const job = get().job; if (!job || !['running','paused'].includes(job.state)) return;
      try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); }
      catch { set({ job: { ...job, state: 'failed', error: 'Unable to persist mock import action.' } }); }
    },
  };
});
