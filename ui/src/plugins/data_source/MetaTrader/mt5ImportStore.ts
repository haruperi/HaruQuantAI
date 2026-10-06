import { normalizeLegacyBranding } from '../../../app/branding';
import { create } from 'zustand';
import { mergeRanges, validDate, type Interval } from '../Dukascopy/dukascopyDownload';
import { mt5Definitions, mt5ImportRanges, type Mt5Definition, type Mt5ImportRequest } from './mt5Import';

export const mt5Active = (state?: string) => state === 'running' || state === 'paused';
export const mt5ImportKey = 'sqx-mt5-import-v1';

export interface Mt5Job {
  request: Mt5ImportRequest;
  definitions: Mt5Definition[];
  state: 'running' | 'paused' | 'completed' | 'cancelled' | 'failed';
  progress: number;
  completed: number;
  error?: string;
}

interface Saved { definitions: Mt5Definition[]; ranges: Record<string, Interval[]>; job: Mt5Job | null; folder: string; postfix: string }
interface Store extends Saved {
  storageError: string;
  start: (request: Mt5ImportRequest, definitions: Mt5Definition[], externalActive: boolean) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}

function validateDefinition(row: Mt5Definition): void {
  if (!row || row.id !== `mt5:${row.symbol}` || row.source !== 'MT5' || row.timeframe !== 'M1'
    || row.barType !== 'start' || !['Forex', 'Metals', 'Indices', 'Stocks', 'Crypto'].includes(row.category)
    || row.bars !== 0 || row.from !== '' || row.to !== ''
    || ['symbol', 'underlying', 'instrument', 'broker', 'brokerName', 'timezone', 'path', 'description']
      .some(key => typeof row[key as keyof Mt5Definition] !== 'string')) throw new Error('Invalid saved MT5 definition.');
}

function validateSaved(value: Saved): void {
  if (!Array.isArray(value.definitions) || value.definitions.length > 10000 || !value.ranges
    || typeof value.ranges !== 'object' || Array.isArray(value.ranges) || typeof value.folder !== 'string'
    || typeof value.postfix !== 'string' || value.folder.length > 255 || value.postfix.length > 64) throw new Error('Invalid saved MT5 state.');
  const names = new Set<string>();
  for (const row of value.definitions) { validateDefinition(row); if (names.has(row.symbol)) throw new Error('Duplicate saved MT5 definition.'); names.add(row.symbol); }
  if (Object.keys(value.ranges).length > 10000) throw new Error('Too many saved MT5 ranges.');
  for (const [id, ranges] of Object.entries(value.ranges)) {
    if (!value.definitions.some(row => row.id === id) || !Array.isArray(ranges) || ranges.length > 1000
      || ranges.some(range => !validDate(range.from) || !validDate(range.to) || range.from > range.to)) throw new Error('Invalid saved MT5 coverage.');
  }
  const job = value.job;
  if (!job) return;
  if (!Array.isArray(job.definitions) || !job.definitions.length || job.definitions.length > 1000
    || job.definitions.some(row => { try { validateDefinition(row); return false; } catch { return true; } })
    || !['running', 'paused', 'completed', 'cancelled', 'failed'].includes(job.state)
    || !Number.isInteger(job.progress) || job.progress < 0 || job.progress > 100
    || !Number.isInteger(job.completed) || job.completed < 0 || job.completed > job.definitions.length) throw new Error('Invalid saved MT5 job.');
  mt5Definitions(job.request, []);
  mt5ImportRanges(job.request);
}

export const useMt5Import = create<Store>((set, get) => {
  let initial: Saved = { definitions: [], ranges: {}, job: null, folder: '', postfix: '' };
  let storageError = '';
  try {
    const raw = localStorage.getItem(mt5ImportKey);
    if (raw) {
      const saved = normalizeLegacyBranding(JSON.parse(raw));
      if (saved.version !== 1) throw new Error('Version');
      validateSaved(saved);
      initial = saved;
      if (initial.job?.state === 'running') initial.job.state = 'paused';
    }
  } catch { storageError = 'Saved MT5 import data could not be read. Existing storage is preserved.'; }

  function persist(patch: Partial<Saved>): void {
    if (get().storageError) throw new Error(get().storageError);
    const { definitions, ranges, job, folder, postfix } = { ...get(), ...patch };
    const saved = { definitions, ranges, job, folder, postfix };
    validateSaved(saved);
    try { localStorage.setItem(mt5ImportKey, JSON.stringify({ version: 1, ...saved })); }
    catch { throw new Error('Unable to save MT5 import data in browser storage. No changes were applied.'); }
    set(patch);
  }

  return {
    ...initial,
    storageError,
    start: (request, definitions, externalActive) => {
      if (externalActive || mt5Active(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      if (!definitions.length || definitions.length !== request.symbols.length || get().definitions.length + definitions.length > 10000) throw new Error('Invalid MT5 import selection.');
      definitions.forEach(validateDefinition);
      mt5ImportRanges(request);
      persist({ folder: request.folder, postfix: request.postfix,
        job: { request: structuredClone(request), definitions: structuredClone(definitions), state: 'running', progress: 0, completed: 0 } });
    },
    advance: () => {
      const { job, definitions } = get();
      if (job?.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5);
      const completed = Math.floor(progress * job.definitions.length / 100);
      const ready = job.definitions.slice(job.completed, completed);
      const ranges = { ...get().ranges };
      const incoming = mt5ImportRanges(job.request);
      for (const row of ready) ranges[row.id] = mergeRanges([], incoming[row.underlying], true);
      try {
        persist({ definitions: [...definitions, ...ready], ranges,
          job: { ...job, progress, completed, state: progress === 100 ? 'completed' : 'running' } });
      } catch (cause) {
        set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save MT5 import progress.' } });
      }
    },
    action: action => {
      const job = get().job;
      if (!job || !mt5Active(job.state)) return;
      try { persist({ job: { ...job, state: action === 'stop' ? 'cancelled' : action === 'pause' ? 'paused' : 'running' } }); }
      catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save MT5 import action.' } }); }
    },
  };
});

export function reservedMt5(): Mt5Definition[] {
  const state = useMt5Import.getState();
  if (state.storageError) throw new Error(state.storageError);
  return [...state.definitions, ...(mt5Active(state.job?.state)
    ? state.job!.definitions.filter(row => !state.definitions.some(item => item.id === row.id)) : [])];
}
