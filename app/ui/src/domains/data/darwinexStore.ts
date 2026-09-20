import { normalizeLegacyBranding } from '../../app/branding';
import { create } from 'zustand';
import { darwinexDownloadRanges, type DarwinexDefinition, type DarwinexDownload } from './darwinex';
import { mergeRanges, validDate, type Interval } from './dukascopyDownload';
import { validateName } from './fileSymbols';
export const darwinexActive = (state?: string) => state === 'running' || state === 'paused';
export const darwinexKey = 'sqx-darwinex-v1';
export interface DarwinexJob { kind: 'add' | 'import' | 'download'; definitions: DarwinexDefinition[]; request?: DarwinexDownload; state: 'running' | 'paused' | 'completed' | 'cancelled' | 'failed'; progress: number; completed: number; error?: string }
interface Saved { definitions: DarwinexDefinition[]; ranges: Record<string, Interval[]>; job: DarwinexJob | null; folder: string; postfix: string }
interface Store extends Saved { storageError: string; start: (kind: 'add' | 'import', definitions: DarwinexDefinition[], externalActive: boolean, folder?: string, postfix?: string) => void; download: (request: DarwinexDownload, full: boolean, externalActive: boolean) => void; advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void }
function validateSaved(value: Saved) {
  if (!Array.isArray(value.definitions) || value.definitions.length > 10000 || !value.ranges || typeof value.ranges !== 'object' || Array.isArray(value.ranges) || typeof value.folder !== 'string' || value.folder.length > 255 || /[\\/\x00-\x1f]/.test(value.folder) || typeof value.postfix !== 'string' || value.postfix.length > 64) throw new Error('Invalid saved Darwinex state.');
  const job = value.job;
  if (job && (!['add','import','download'].includes(job.kind) || !Array.isArray(job.definitions) || !job.definitions.length || job.definitions.length > 1000 || !['running','paused','completed','cancelled','failed'].includes(job.state) || !Number.isInteger(job.progress) || job.progress < 0 || job.progress > 100 || !Number.isInteger(job.completed) || job.completed < 0 || job.completed > job.definitions.length || (job.state === 'completed' && (job.completed !== job.definitions.length || job.progress !== 100)))) throw new Error('Invalid saved job.');
  for (const rows of [value.definitions, job?.definitions ?? []]) {
    const names: string[] = [];
    for (const row of rows) {
      validateName(row.symbol, names); names.push(row.symbol);
      if (row.id !== `darwinex:${row.symbol}` || row.source !== 'Darwinex' || row.timeframe !== 'TICK' || row.bars !== 0 || row.from !== '' || row.to !== '' || ['underlying','instrument','broker','brokerName','timezone','category'].some(key => typeof row[key as keyof DarwinexDefinition] !== 'string')) throw new Error('Invalid saved definition.');
    }
  }
  if (Object.keys(value.ranges).length > 10000) throw new Error('Too many saved ranges.');
  for (const [id, ranges] of Object.entries(value.ranges)) if (!value.definitions.some(row => row.id === id) || !Array.isArray(ranges) || ranges.length > 1000 || ranges.some(range => !validDate(range.from) || !validDate(range.to) || range.from > range.to)) throw new Error('Invalid saved coverage.');
  if (job?.kind === 'download') { if (!job.request) throw new Error('Missing download request'); darwinexDownloadRanges(job.request); if (job.request.targets.some(row => !value.definitions.some(item => item.id === row.id))) throw new Error('Missing download target'); }
}
export const useDarwinex = create<Store>((set, get) => {
  let initial: Saved = { definitions: [], ranges: {}, job: null, folder: '', postfix: '' }; let storageError = '';
  try { const raw = localStorage.getItem(darwinexKey); if (raw) { const saved = normalizeLegacyBranding(JSON.parse(raw)); if (saved.version !== 1) throw new Error('Version'); validateSaved(saved); initial = saved; if (initial.job?.state === 'running') initial.job.state = 'paused'; } } catch { storageError = 'Saved Darwinex data could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>) {
    if (get().storageError) throw new Error(get().storageError);
    const { definitions, ranges, job, folder, postfix } = { ...get(), ...patch }; const saved = { definitions, ranges, job, folder, postfix }; validateSaved(saved);
    try { localStorage.setItem(darwinexKey, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save Darwinex data in browser storage. No changes were applied.'); }
    set(patch);
  }
  function guard(external: boolean) { if (external || darwinexActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.'); }
  return { ...initial, storageError,
    start: (kind, definitions, external, folder = get().folder, postfix = get().postfix) => {
      guard(external); const names = get().definitions.map(row => row.symbol); for (const row of definitions) { validateName(row.symbol, names); names.push(row.symbol); }
      if (names.length > 10000) throw new Error('Mock dataset limit reached.');
      persist({ folder, postfix, job: { kind, definitions, state: 'running', progress: 0, completed: 0 } });
    },
    download: (request, full, external) => { guard(external); if (!full) throw new Error('Darwinex CDN download is available only for users of full license.'); darwinexDownloadRanges(request);
      const definitions = request.targets.map(row => { const saved = get().definitions.find(item => item.id === row.id); if (!saved) throw new Error('Unknown Darwinex record.'); return saved; });
      persist({ job: { kind: 'download', request, definitions, state: 'running', progress: 0, completed: 0 } });
    },
    advance: () => {
      const { job, definitions } = get(); if (job?.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5), completed = Math.floor(progress * job.definitions.length / 100), ready = job.definitions.slice(job.completed, completed);
      const ranges = { ...get().ranges };
      try {
        if (job.kind === 'download') { const incoming = darwinexDownloadRanges(job.request!); for (const row of ready) ranges[row.id] = mergeRanges(ranges[row.id] ?? [], incoming[row.id], job.request!.overwrite); }
        persist({ definitions: job.kind === 'download' ? definitions : [...definitions, ...ready], ranges, job: { ...job, progress, completed, state: progress === 100 ? 'completed' : 'running' } });
      } catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save data.' } }); }
    },
    action: action => { const job = get().job; if (!job || !darwinexActive(job.state)) return; try { persist({ job: { ...job, state: action === 'stop' ? 'cancelled' : action === 'pause' ? 'paused' : 'running' } }); } catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save data.' } }); } },
  };
});
export function reservedDarwinex() { const state = useDarwinex.getState(); if (state.storageError) throw new Error(state.storageError); return [...state.definitions, ...(darwinexActive(state.job?.state) && state.job?.kind !== 'download' ? state.job!.definitions : [])]; }
