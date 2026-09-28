import { normalizeLegacyBranding } from '../../../host/branding';
import { create } from 'zustand';
import { createCloneDefinitions, validateCloneSettings, validateReviewChange, type CloneDefinition, type CloneSettings, type ReviewMutation, type ReviewRow, type ToolJobState, type ToolTarget } from './dataTools';

export interface CloneTask { source: ToolTarget; definition: CloneDefinition }
export interface CloneJob { id: string; tasks: CloneTask[]; completed: number; state: ToolJobState; progress: number; error?: string }
interface Saved { settings: CloneSettings; definitions: CloneDefinition[]; reviews: Record<string, ReviewMutation>; job: CloneJob | null }
interface Store extends Saved {
  storageError: string;
  startClone: (targets: ToolTarget[], settings: CloneSettings, existingNames: string[], externalActive: boolean) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
  saveReview: (key: string, rows: ReviewRow[], changed: Record<string, Partial<ReviewRow>>, deleted: string[], tick: boolean) => void;
}

const storageKey = 'haru-data-tools-v1';
export const toolsActive = (state: string | undefined) => state === 'running' || state === 'paused';
const defaults: Saved = { settings: { postfix: '_{timeframe}_{cloneTime}', timezoneType: 'shift', shiftHours: 5, timezone: 'UTC', removeWeekends: false }, definitions: [], reviews: {}, job: null };

function validateSaved(value: Saved): void {
  validateCloneSettings(value.settings);
  if (!Array.isArray(value.definitions) || value.definitions.length > 500 || typeof value.reviews !== 'object' || value.reviews === null || Object.keys(value.reviews).length > 500) throw new Error('Invalid saved Tools data.');
  for (const definition of value.definitions) if (!definition?.id || !definition.sourceDataId || !definition.symbol || definition.symbol.length > 120) throw new Error('Invalid cloned definition.');
  for (const mutation of Object.values(value.reviews)) if (!mutation || !Array.isArray(mutation.deleted) || mutation.deleted.length > 1000 || typeof mutation.changed !== 'object' || Object.keys(mutation.changed).length > 1000) throw new Error('Invalid review mutation.');
  if (value.job && (!Array.isArray(value.job.tasks) || !value.job.tasks.length || value.job.tasks.length > 100 || !['running', 'paused', 'cancelled', 'completed', 'failed'].includes(value.job.state) || value.job.progress < 0 || value.job.progress > 100)) throw new Error('Invalid clone job.');
}

export const useDataTools = create<Store>((set, get) => {
  let initial: Saved = structuredClone(defaults); let storageError = '';
  try { const raw = localStorage.getItem(storageKey); if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; } }
  catch { storageError = 'Saved Tools state could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>): void {
    if (get().storageError) throw new Error(get().storageError);
    const saved = { settings: get().settings, definitions: get().definitions, reviews: get().reviews, job: get().job, ...patch }; validateSaved(saved);
    try { localStorage.setItem(storageKey, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save Tools state in browser storage. No changes were applied.'); }
    set(patch);
  }
  function fail(cause: unknown): void { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save Tools state.' } }); }
  return { ...initial, storageError,
    startClone: (targets, settings, existingNames, externalActive) => {
      if (externalActive || toolsActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      const generated = createCloneDefinitions(targets, settings, existingNames);
      persist({ settings: { ...settings }, job: { id: `clone-${Date.now()}`, tasks: targets.map((source, index) => ({ source, definition: generated[index] })), completed: 0, state: 'running', progress: 0 } });
    },
    advance: () => {
      const job = get().job; if (job?.state !== 'running') return;
      const progress = Math.min(100, job.progress + 10); const completed = Math.min(job.tasks.length, Math.floor(progress / 100 * job.tasks.length));
      const done = progress === 100; const definitions = done ? [...get().definitions, ...job.tasks.map(task => task.definition).filter(item => !get().definitions.some(row => row.id === item.id))] : get().definitions;
      try { persist({ definitions, job: { ...job, progress, completed: done ? job.tasks.length : completed, state: done ? 'completed' : 'running' } }); } catch (cause) { fail(cause); }
    },
    action: action => { const job = get().job; if (!job || !toolsActive(job.state)) return; try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); } catch (cause) { fail(cause); } },
    saveReview: (key, rows, changed, deleted, tick) => {
      for (const row of rows) validateReviewChange({ ...row, ...(changed[row.id] ?? {}) }, tick);
      const previous = get().reviews[key];
      persist({ reviews: { ...get().reviews, [key]: { changed: { ...(previous?.changed ?? {}), ...changed }, deleted: [...new Set([...(previous?.deleted ?? []), ...deleted])] } } });
    },
  };
});
