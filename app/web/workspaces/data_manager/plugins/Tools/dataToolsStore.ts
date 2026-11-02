import { useHistoricalSources, type SourceJob } from '../Common/historicalSourceStore';
import { normalizeSymbolContract } from '../Common/symbolContract';
import { createSymbolDataClient } from '../Common/symbolContract';
import { normalizeLegacyBranding } from '../../../../shell/branding';
import { create } from 'zustand';
import {type DomainClient } from '../../../../shell/transport';
import { createCloneDefinitions, validateCloneSettings, validateReviewChange, type CloneDefinition, type CloneSettings, type ReviewMutation, type ReviewRow, type ReviewPage, type RemoteQualityResult, type ToolJobState, type ToolTarget } from './dataTools';

let dataClient = createSymbolDataClient('/data');

export function setDataClient(client: DomainClient): void {
  dataClient = client;
}

export interface CloneTask { source: ToolTarget; definition: CloneDefinition }
export interface CloneJob { id: string; tasks: CloneTask[]; completed: number; state: ToolJobState; progress: number; error?: string }
interface Saved { settings: CloneSettings; definitions: CloneDefinition[]; reviews: Record<string, ReviewMutation>; job: CloneJob | null }
interface Store extends Saved {
  storageError: string;
  startClone: (targets: ToolTarget[], settings: CloneSettings, existingNames: string[], externalActive: boolean) => Promise<void>;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
  saveReview: (key: string, rows: ReviewRow[], changed: Record<string, Partial<ReviewRow>>, deleted: string[], tick: boolean) => void;
  cloneRemote: (payload: { dataset_id: string; timezone_type?: string; shift_hours?: number; timezone?: string; remove_weekends?: boolean; postfix?: string }) => Promise<unknown>;
  fetchReviewRows: (datasetId: string, limit?: number, offset?: number, timeframe?: string, session?: string) => Promise<ReviewPage>;
  saveRemoteReviewChanges: (datasetId: string, changedBars: Array<Record<string, unknown>>, deletedTimestamps: string[], revision?: string) => Promise<unknown>;
  fetchQualitySummary: (datasetId: string) => Promise<unknown>;
  fetchQualityDetails: (datasetId: string, limit?: number, offset?: number, timeframe?: string, session?: string) => Promise<RemoteQualityResult>;
  getIndexForDate: (datasetId: string, targetDate: string) => Promise<number>;
  massDeleteRemote: (datasetIds: string[], action?: 'remove' | 'clear', force?: boolean) => Promise<unknown>;
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
  try { const raw = localStorage.getItem(storageKey); if (raw) { const value = normalizeLegacyBranding(normalizeSymbolContract(JSON.parse(raw))); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; } }
  catch { storageError = 'Saved Tools state could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>): void {
    if (get().storageError) throw new Error(get().storageError);
    const saved = { settings: get().settings, definitions: get().definitions, reviews: get().reviews, job: get().job, ...patch }; validateSaved(saved);
    try { localStorage.setItem(storageKey, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save Tools state in browser storage. No changes were applied.'); }
    set(patch);
  }
  function fail(cause: unknown): void { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to save Tools state.' } }); }
  return { ...initial, storageError,
    startClone: async (targets, settings, existingNames, externalActive) => {
      if (externalActive || toolsActive(get().job?.state)) throw new Error('Finish or stop the active operation first.');
      validateCloneSettings(settings);
      if (targets.length !== 1) throw new Error('Clone one saved dataset at a time.');
      const job = await dataClient.post<SourceJob>('/datasets/clone-timezone', { dataset_id: targets[0].id, timezone_type: settings.timezoneType, shift_hours: settings.shiftHours, timezone: settings.timezone, remove_weekends: settings.removeWeekends, postfix: settings.postfix });
      useHistoricalSources.getState().trackJob(job);
      persist({ settings, job: null });
    },
    advance: () => { void useHistoricalSources.getState().poll(); },
    action: action => { void useHistoricalSources.getState().action(action); },
    saveReview: (key, rows, changed, deleted, tick) => {
      for (const row of rows) validateReviewChange({ ...row, ...(changed[row.id] ?? {}) }, tick);
      const previous = get().reviews[key];
      persist({ reviews: { ...get().reviews, [key]: { changed: { ...(previous?.changed ?? {}), ...changed }, deleted: [...new Set([...(previous?.deleted ?? []), ...deleted])] } } });
    },
    cloneRemote: async (payload) => {
      return dataClient.post('/datasets/clone-timezone', payload);
    },
    fetchReviewRows: async (datasetId, limit = 500, offset = 0, timeframe, session) => {
      return dataClient.get<ReviewPage>(`/datasets/${encodeURIComponent(datasetId)}/review-data?limit=${limit}&offset=${offset}${timeframe ? `&timeframe=${encodeURIComponent(timeframe)}` : ''}${session ? `&session=${encodeURIComponent(session)}` : ''}`);
    },
    saveRemoteReviewChanges: async (datasetId, changedBars, deletedTimestamps, revision) => {
      return dataClient.post(`/datasets/${encodeURIComponent(datasetId)}/save-changes`, {
        dataset_id: datasetId,
        changed_bars: changedBars,
        deleted_timestamps: deletedTimestamps, revision,
      });
    },
    fetchQualitySummary: async (datasetId) => {
      return dataClient.get(`/datasets/${encodeURIComponent(datasetId)}/quality-summary`);
    },
    fetchQualityDetails: async (datasetId, limit = 100, offset = 0, timeframe, session) => {
      return dataClient.get<RemoteQualityResult>(`/datasets/${encodeURIComponent(datasetId)}/quality-details?limit=${limit}&offset=${offset}${timeframe ? `&timeframe=${encodeURIComponent(timeframe)}` : ''}${session ? `&session=${encodeURIComponent(session)}` : ''}`);
    },
    getIndexForDate: async (datasetId, targetDate) => {
      const res = await dataClient.get<{ index: number }>(`/datasets/${encodeURIComponent(datasetId)}/index-for-date?target_date=${encodeURIComponent(targetDate)}`);
      return res?.index ?? 0;
    },
    massDeleteRemote: async (datasetIds, action = 'remove', force = false) => {
      return dataClient.post('/datasets/mass-delete', {
        dataset_ids: datasetIds,
        action,
        force,
      });
    },
  };
});
