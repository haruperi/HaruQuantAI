import { normalizeLegacyBranding } from '../../../host/branding';
import { emptyDownload, resolveDownloadModes, downloadStep, validateDownload, availableStart, mergeRanges, validDate, type DownloadState, type DownloadRequest, type Interval } from './dukascopyDownload';
import { create } from 'zustand';

export function dukascopyActive(state?: string): boolean {
  return ['running', 'paused'].includes(state ?? '');
}

const downloadKey = 'sqx-data-download-v1';
function readDownloads(): DownloadState {
  const raw = localStorage.getItem(downloadKey);
  if (!raw) return { ...emptyDownload, ranges: {} };
  const saved = normalizeLegacyBranding(JSON.parse(raw));
  if (saved.version !== 1 || !saved.ranges || typeof saved.ranges !== 'object' || Array.isArray(saved.ranges)
    || Object.keys(saved.ranges).length > 10000 || ![null, 'standard', 'cdn', 'cdn-cn'].includes(saved.preferred)) throw new Error('Invalid saved downloads');
  for (const ranges of Object.values(saved.ranges) as Interval[][]) {
    if (!Array.isArray(ranges) || ranges.length > 1000 || ranges.some(row => !validDate(row.from) || !validDate(row.to) || row.from > row.to)) throw new Error('Invalid saved ranges');
  }
  if (saved.job) {
    if (!['running', 'paused', 'cancelled', 'completed', 'failed'].includes(saved.job.state) || !Number.isFinite(saved.job.progress) || saved.job.progress < 0 || saved.job.progress > 100) throw new Error('Invalid saved job');
    validateDownload(saved.job.request);
    saved.job.resolvedModes = resolveDownloadModes(saved.job.request);
    if (saved.job.state === 'running') saved.job.state = 'paused';
  }
  return { job: saved.job ?? null, preferred: saved.preferred, ranges: saved.ranges };
}

export interface DownloadStore extends DownloadState {
  storageError: string;
  start: (request: DownloadRequest, otherActive?: boolean) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}

export const useDukascopyDownloads = create<DownloadStore>((set, get) => {
  let initial: DownloadState = { ...emptyDownload, ranges: {} };
  let storageError = '';
  try { initial = readDownloads(); } catch { storageError = 'Saved mock downloads could not be read. Existing storage is preserved.'; }
  function persist(next: DownloadState) {
    if (get().storageError) throw new Error(get().storageError);
    localStorage.setItem(downloadKey, JSON.stringify({ version: 1, ...next }));
    set(next);
  }
  function snapshot(): DownloadState { const { job, ranges, preferred } = get(); return { job, ranges, preferred }; }
  return {
    ...initial, storageError,
    start: (request, otherActive = false) => {
      if (otherActive) throw new Error('Finish or stop the active data operation first.');
      if (get().job && ['running', 'paused'].includes(get().job!.state)) throw new Error('Finish or stop the active mock download first.');
      validateDownload(request);
      try { persist({ ...snapshot(), preferred: request.downloadType, job: { request: structuredClone(request), resolvedModes: resolveDownloadModes(request), state: 'running', progress: 0 } }); }
      catch (cause) { throw new Error(cause instanceof Error && get().storageError ? cause.message : 'Unable to save mock download. No job was started.'); }
    },
    advance: () => {
      const state = snapshot(); if (!state.job || state.job.state !== 'running') return;
      const job = { ...state.job, progress: Math.min(100, state.job.progress + downloadStep(state.job)) };
      const ranges = { ...state.ranges };
      if (job.progress === 100) {
        job.state = 'completed';
        for (const target of job.request.targets) {
          const from = [job.request.dateFrom, availableStart(target, true)].sort().at(-1)!;
          ranges[target.id] = mergeRanges(ranges[target.id] ?? [], { from, to: job.request.dateTo }, job.request.overwrite);
        }
      }
      try { persist({ ...state, ranges, job }); }
      catch { set({ job: { ...state.job, state: 'failed', error: 'Unable to persist mock download progress. Previous saved coverage is unchanged.' } }); }
    },
    action: action => {
      const state = snapshot(); if (!state.job || !['running', 'paused'].includes(state.job.state)) return;
      const job = { ...state.job, state: action === 'pause' ? 'paused' as const : action === 'resume' ? 'running' as const : 'cancelled' as const };
      try { persist({ ...state, job }); }
      catch { set({ job: { ...state.job, state: 'failed', error: 'Unable to persist mock download action.' } }); }
    },
  };
});
