import { normalizeLegacyBranding } from '../../app/branding';
import { create } from 'zustand';
import { yahooDownloadRanges, validateYahooName, type YahooDefinition, type YahooDownload } from './yahoo';
import { mergeRanges, validDate, type Interval } from './dukascopyDownload';

export const yahooActive = (state?: string) => state === 'running' || state === 'paused';
export const yahooKey = 'sqx-yahoo-data-v1';
export interface YahooJob { kind: 'add' | 'download'; definitions: YahooDefinition[]; request?: YahooDownload; state: 'running' | 'paused' | 'completed' | 'cancelled' | 'failed'; progress: number; completed: number; error?: string }
interface Saved { definitions: YahooDefinition[]; ranges: Record<string, Interval[]>; job: YahooJob | null }
interface Store extends Saved { storageError: string; startAdd: (definitions: YahooDefinition[], externalActive: boolean) => void; startDownload: (request: YahooDownload, externalActive: boolean) => void; advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void }

function validateDefinition(row: YahooDefinition) {
  if (!row || row.id !== `yahoo:${row.symbol}` || row.source !== 'Yahoo' || row.timeframe !== 'D1' || row.barType !== 'start' || row.broker !== '-1' || row.brokerName !== '—' || row.timezone !== 'UTC' || row.bars !== 0 || row.from !== '' || row.to !== '' || !['Stocks','ETF','Index','Forex','Crypto'].includes(row.category) || ['symbol','underlying','instrument','name','exchange'].some(key => typeof row[key as keyof YahooDefinition] !== 'string')) throw new Error('Invalid saved Yahoo definition.');
}
function validateSaved(value: Saved) {
  if (!Array.isArray(value.definitions) || value.definitions.length > 10000 || !value.ranges || typeof value.ranges !== 'object' || Array.isArray(value.ranges)) throw new Error('Invalid saved Yahoo state.');
  const names: string[] = []; for (const row of value.definitions) { validateDefinition(row); validateYahooName(row.symbol, names); names.push(row.symbol); }
  if (Object.keys(value.ranges).length > 10000) throw new Error('Too many saved Yahoo ranges.');
  for (const [id, ranges] of Object.entries(value.ranges)) if (!value.definitions.some(row => row.id === id) || !Array.isArray(ranges) || ranges.length > 1000 || ranges.some(range => !validDate(range.from) || !validDate(range.to) || range.from > range.to)) throw new Error('Invalid saved Yahoo coverage.');
  const job = value.job; if (!job) return;
  if (!['add','download'].includes(job.kind) || !Array.isArray(job.definitions) || !job.definitions.length || job.definitions.length > 1000 || job.definitions.some(row => { try { validateDefinition(row); return false; } catch { return true; } }) || !['running','paused','completed','cancelled','failed'].includes(job.state) || !Number.isInteger(job.progress) || job.progress < 0 || job.progress > 100 || !Number.isInteger(job.completed) || job.completed < 0 || job.completed > job.definitions.length) throw new Error('Invalid saved Yahoo job.');
  if (job.kind === 'download') { if (!job.request) throw new Error('Missing Yahoo request.'); yahooDownloadRanges(job.request); if (job.request.targets.some(row => !value.definitions.some(item => item.id === row.id))) throw new Error('Missing Yahoo target.'); }
}

export const useYahoo = create<Store>((set, get) => {
  let initial: Saved = { definitions: [], ranges: {}, job: null }; let storageError = '';
  try { const raw = localStorage.getItem(yahooKey); if (raw) { const saved = normalizeLegacyBranding(JSON.parse(raw)); if (saved.version !== 1) throw new Error('Version'); validateSaved(saved); initial = saved; if (initial.job?.state === 'running') initial.job.state = 'paused'; } } catch { storageError = 'Saved Yahoo data could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>) { if (get().storageError) throw new Error(get().storageError); const { definitions, ranges, job } = { ...get(), ...patch }; const saved = { definitions, ranges, job }; validateSaved(saved); try { localStorage.setItem(yahooKey, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save Yahoo data in browser storage. No changes were applied.'); } set(patch); }
  function guard(external: boolean) { if (external || yahooActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.'); }
  return { ...initial, storageError,
    startAdd: (definitions, external) => { guard(external); const names = get().definitions.map(row => row.symbol); for (const row of definitions) { validateDefinition(row); validateYahooName(row.symbol, names); names.push(row.symbol); } if (names.length > 10000) throw new Error('Mock dataset limit reached.'); persist({ job: { kind: 'add', definitions, state: 'running', progress: 0, completed: 0 } }); },
    startDownload: (request, external) => { guard(external); yahooDownloadRanges(request); const definitions = request.targets.map(row => { const saved = get().definitions.find(item => item.id === row.id); if (!saved) throw new Error('Unknown Yahoo record.'); return saved; }); persist({ job: { kind: 'download', request, definitions, state: 'running', progress: 0, completed: 0 } }); },
    advance: () => { const { job, definitions } = get(); if (job?.state !== 'running') return; const progress = Math.min(100, job.progress + 5), completed = Math.floor(progress * job.definitions.length / 100), ready = job.definitions.slice(job.completed, completed), ranges = { ...get().ranges }; try { if (job.kind === 'download') { const incoming = yahooDownloadRanges(job.request!); for (const row of ready) ranges[row.id] = mergeRanges(ranges[row.id] ?? [], incoming[row.id], job.request!.overwrite); } persist({ definitions: job.kind === 'download' ? definitions : [...definitions, ...ready], ranges, job: { ...job, progress, completed, state: progress === 100 ? 'completed' : 'running' } }); } catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save Yahoo data.' } }); } },
    action: action => { const job = get().job; if (!job || !yahooActive(job.state)) return; try { persist({ job: { ...job, state: action === 'stop' ? 'cancelled' : action === 'pause' ? 'paused' : 'running' } }); } catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save Yahoo action.' } }); } },
  };
});
export function reservedYahoo() { const state = useYahoo.getState(); if (state.storageError) throw new Error(state.storageError); return [...state.definitions, ...(yahooActive(state.job?.state) && state.job?.kind === 'add' ? state.job.definitions : [])]; }
