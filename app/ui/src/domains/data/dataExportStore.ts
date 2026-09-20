import { normalizeLegacyBranding } from '../../app/branding';
import { create } from 'zustand';
import { builtInCsvFormats, validateCsvFormat, type CsvFormat, type ExportArtifact, type ExportJobState, type ExportKind } from './dataExport';

export interface ExportHistory { id: string; kind: ExportKind; names: string[]; targetIds: string[]; completedAt: string }
export interface ExportJob { id: string; kind: ExportKind; label: string; targetIds: string[]; artifacts: ExportArtifact[]; state: ExportJobState; progress: number; error?: string }
interface Saved { formats: CsvFormat[]; history: ExportHistory[]; settings: Record<string, string | number | boolean>; job: ExportJob | null }
interface Store extends Saved {
  storageError: string;
  saveFormat: (format: CsvFormat, replace?: boolean) => void;
  deleteFormat: (name: string) => void;
  start: (kind: ExportKind, label: string, targetIds: string[], artifacts: ExportArtifact[], settings: Record<string, string | number | boolean>, externalActive: boolean) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}

const key = 'haru-data-export-v1';
export const exportActive = (state: string | undefined) => state === 'running' || state === 'paused';

function validateSaved(saved: Saved): void {
  if (!Array.isArray(saved.formats) || saved.formats.length > 100 || !Array.isArray(saved.history) || saved.history.length > 200 || typeof saved.settings !== 'object' || saved.settings === null) throw new Error('Invalid saved export settings.');
  for (const format of saved.formats) {
    validateCsvFormat(format);
    if (format.predefined || builtInCsvFormats.some(row => row.name === format.name)) throw new Error('Invalid custom format.');
  }
  if (new Set(saved.formats.map(row => row.name)).size !== saved.formats.length) throw new Error('Duplicate custom formats.');
  for (const item of saved.history) if (!item || !['csv', 'mt4', 'mt5'].includes(item.kind) || !Array.isArray(item.names) || !Array.isArray(item.targetIds) || typeof item.completedAt !== 'string') throw new Error('Invalid export history.');
  const job = saved.job;
  if (job && (!['csv', 'mt4', 'mt5'].includes(job.kind) || !['running', 'paused', 'cancelled', 'completed', 'failed'].includes(job.state) || !Number.isInteger(job.progress) || job.progress < 0 || job.progress > 100 || !Array.isArray(job.targetIds) || !job.targetIds.length || job.targetIds.length > 100 || !Array.isArray(job.artifacts) || job.artifacts.length > 100 || job.artifacts.some(item => typeof item.content !== 'string' || item.content.length > 1_000_000 || typeof item.name !== 'string' || typeof item.targetId !== 'string'))) throw new Error('Invalid saved export job.');
}

export const useDataExports = create<Store>((set, get) => {
  let initial: Saved = { formats: [], history: [], settings: {}, job: null }; let storageError = '';
  try {
    const raw = localStorage.getItem(key);
    if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; }
  } catch { storageError = 'Saved export settings could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>): void {
    if (get().storageError) throw new Error(get().storageError);
    const saved = { formats: get().formats, history: get().history, settings: get().settings, job: get().job, ...patch };
    validateSaved(saved);
    try { localStorage.setItem(key, JSON.stringify({ version: 1, ...saved })); }
    catch { throw new Error('Unable to save export state in browser storage. No changes were applied.'); }
    set(patch);
  }
  function fail(cause: unknown): void { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to persist export state.' } }); }
  return { ...initial, storageError,
    saveFormat: (format, replace = false) => {
      validateCsvFormat(format); const name = format.name.trim();
      if (builtInCsvFormats.some(row => row.name === name)) throw new Error('Predefined formats cannot be replaced.');
      if (!replace && get().formats.some(row => row.name === name)) throw new Error('A format with this name already exists.');
      persist({ formats: [...get().formats.filter(row => row.name !== name), { ...format, name, predefined: false }] });
    },
    deleteFormat: name => persist({ formats: get().formats.filter(row => row.name !== name) }),
    start: (kind, label, targetIds, artifacts, settings, externalActive) => {
      if (externalActive || exportActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      if (!targetIds.length || !artifacts.length || new Set(targetIds).size !== targetIds.length) throw new Error('Choose eligible data to export.');
      persist({ settings: { ...get().settings, ...settings }, job: { id: `${kind}-${Date.now()}`, kind, label, targetIds, artifacts, state: 'running', progress: 0 } });
    },
    advance: () => {
      const job = get().job; if (job?.state !== 'running') return;
      const progress = Math.min(100, job.progress + 10); const state = progress === 100 ? 'completed' : 'running';
      const history = state === 'completed' ? [...get().history, { id: job.id, kind: job.kind, names: job.artifacts.map(item => item.name), targetIds: job.targetIds, completedAt: new Date().toISOString() }].slice(-200) : get().history;
      try { persist({ history, job: { ...job, progress, state } }); } catch (cause) { fail(cause); }
    },
    action: action => { const job = get().job; if (!job || !exportActive(job.state)) return; try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); } catch (cause) { fail(cause); } },
  };
});
