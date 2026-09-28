import { normalizeLegacyBranding } from '../../../host/branding';
import { create } from 'zustand';
import { cryptoDownloadRanges, validateCryptoName, type CryptoDefinition, type CryptoDownload } from './crypto';
import { mergeRanges, validDate, type Interval } from './presentation';

export const cryptoActive = (state?: string) => state === 'running' || state === 'paused';
export const cryptoKey = 'sqx-crypto-data-v1';
export interface CryptoJob { kind: 'add' | 'download'; definitions: CryptoDefinition[]; request?: CryptoDownload; state: 'running' | 'paused' | 'completed' | 'cancelled' | 'failed'; progress: number; completed: number; error?: string }
interface Saved { definitions: CryptoDefinition[]; ranges: Record<string, Interval[]>; job: CryptoJob | null }
interface Store extends Saved { storageError: string; startAdd: (definitions: CryptoDefinition[], externalActive: boolean) => void; startDownload: (request: CryptoDownload, externalActive: boolean) => void; advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void }

function validateDefinition(row: CryptoDefinition) {
  if (!row || row.id !== `crypto:${row.exchange}:${row.symbol}` || row.source !== 'Crypto' || row.category !== 'Crypto' || row.barType !== 'start' || row.broker !== '-1' || row.brokerName !== '—' || row.timezone !== 'UTC' || row.bars !== 0 || row.from !== '' || row.to !== '' || ['symbol','underlying','instrument','timeframe'].some(key => typeof row[key as keyof CryptoDefinition] !== 'string')) throw new Error('Invalid saved Crypto definition.');
}
function validateSaved(value: Saved) {
  if (!Array.isArray(value.definitions) || value.definitions.length > 10000 || !value.ranges || typeof value.ranges !== 'object' || Array.isArray(value.ranges)) throw new Error('Invalid saved Crypto state.');
  const names: string[] = []; for (const row of value.definitions) { validateDefinition(row); validateCryptoName(row.symbol, names); names.push(row.symbol); }
  if (Object.keys(value.ranges).length > 10000) throw new Error('Too many saved Crypto ranges.');
  for (const [id, ranges] of Object.entries(value.ranges)) if (!value.definitions.some(row => row.id === id) || !Array.isArray(ranges) || ranges.length > 1000 || ranges.some(range => !validDate(range.from) || !validDate(range.to) || range.from > range.to)) throw new Error('Invalid saved Crypto coverage.');
  const job = value.job; if (!job) return;
  if (!['add','download'].includes(job.kind) || !Array.isArray(job.definitions) || !job.definitions.length || job.definitions.length > 1000 || job.definitions.some(row => { try { validateDefinition(row); return false; } catch { return true; } }) || !['running','paused','completed','cancelled','failed'].includes(job.state) || !Number.isInteger(job.progress) || job.progress < 0 || job.progress > 100 || !Number.isInteger(job.completed) || job.completed < 0 || job.completed > job.definitions.length) throw new Error('Invalid saved Crypto job.');
  if (job.kind === 'download') { if (!job.request) throw new Error('Missing Crypto request.'); cryptoDownloadRanges(job.request); if (job.request.targets.some(row => !value.definitions.some(item => item.id === row.id))) throw new Error('Missing Crypto target.'); }
}

export const useCrypto = create<Store>((set, get) => {
  let initial: Saved = { definitions: [], ranges: {}, job: null }; let storageError = '';
  try { const raw = localStorage.getItem(cryptoKey); if (raw) { const saved = normalizeLegacyBranding(JSON.parse(raw)); if (saved.version !== 1) throw new Error('Version'); validateSaved(saved); initial = saved; if (initial.job?.state === 'running') initial.job.state = 'paused'; } } catch { storageError = 'Saved Crypto data could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>) { if (get().storageError) throw new Error(get().storageError); const { definitions, ranges, job } = { ...get(), ...patch }; const saved = { definitions, ranges, job }; validateSaved(saved); try { localStorage.setItem(cryptoKey, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save Crypto data in browser storage. No changes were applied.'); } set(patch); }
  function guard(external: boolean) { if (external || cryptoActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.'); }
  return { ...initial, storageError,
    startAdd: (definitions, external) => { guard(external); const names = get().definitions.map(row => row.symbol); for (const row of definitions) { validateDefinition(row); validateCryptoName(row.symbol, names); names.push(row.symbol); } if (names.length > 10000) throw new Error('Mock dataset limit reached.'); persist({ job: { kind: 'add', definitions, state: 'running', progress: 0, completed: 0 } }); },
    startDownload: (request, external) => { guard(external); cryptoDownloadRanges(request); const definitions = request.targets.map(row => { const saved = get().definitions.find(item => item.id === row.id); if (!saved) throw new Error('Unknown Crypto record.'); return saved; }); persist({ job: { kind: 'download', request, definitions, state: 'running', progress: 0, completed: 0 } }); },
    advance: () => { const { job, definitions } = get(); if (job?.state !== 'running') return; const progress = Math.min(100, job.progress + 5), completed = Math.floor(progress * job.definitions.length / 100), ready = job.definitions.slice(job.completed, completed), ranges = { ...get().ranges }; try { if (job.kind === 'download') { const incoming = cryptoDownloadRanges(job.request!); for (const row of ready) ranges[row.id] = mergeRanges(ranges[row.id] ?? [], incoming[row.id], job.request!.overwrite); } persist({ definitions: job.kind === 'download' ? definitions : [...definitions, ...ready], ranges, job: { ...job, progress, completed, state: progress === 100 ? 'completed' : 'running' } }); } catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save Crypto data.' } }); } },
    action: action => { const job = get().job; if (!job || !cryptoActive(job.state)) return; try { persist({ job: { ...job, state: action === 'stop' ? 'cancelled' : action === 'pause' ? 'paused' : 'running' } }); } catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save Crypto action.' } }); } },
  };
});
export function reservedCrypto() { const state = useCrypto.getState(); if (state.storageError) throw new Error(state.storageError); return [...state.definitions, ...(cryptoActive(state.job?.state) && state.job?.kind === 'add' ? state.job.definitions : [])]; }
