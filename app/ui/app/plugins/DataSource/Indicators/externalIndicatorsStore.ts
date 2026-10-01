import { normalizeLegacyBranding } from '../../../host/branding';
import { create } from 'zustand';
import { indicatorState, replaceIndicatorState, importIndicator, indicatorJob, cancelIndicator } from './backend';
import { builtInExternalFormats, externalLimits, summarizeExternal, validateExternalDefinition, validateExternalFormat, type ExternalImportFormat, type ExternalImportJob, type ExternalIndicatorDefinition } from './externalIndicators';

interface Saved { definitions: ExternalIndicatorDefinition[]; formats: ExternalImportFormat[]; job: ExternalImportJob | null }
interface ExternalIndicatorsState extends Saved {
  backendAvailable: boolean; storageError: string; refresh: () => Promise<void>; importLegacy: () => Promise<void>;
  add: (item: ExternalIndicatorDefinition) => Promise<void>; edit: (original: string, item: ExternalIndicatorDefinition) => Promise<void>;
  clear: (names: string[]) => Promise<void>; remove: (names: string[]) => Promise<void>;
  importDefinitions: (items: ExternalIndicatorDefinition[], overwrite: string[]) => Promise<void>;
  saveFormat: (item: ExternalImportFormat, replace?: boolean) => Promise<void>; deleteFormat: (name: string) => Promise<void>;
  startImport: (indicator: string, text: string, format: ExternalImportFormat, ignoreErrors: boolean, externalActive: boolean) => Promise<void>;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
const key = 'haru-external-indicators-v1';
export const externalJobActive = (state?: string): boolean => state === 'running' || state === 'paused';
function validateSaved(value: Saved): void {
  if (!Array.isArray(value.definitions) || value.definitions.length > 10_000 || !Array.isArray(value.formats) || value.formats.length > 100) throw new Error('Invalid saved external indicators.');
  const names: string[] = []; let records = 0;
  value.definitions.forEach(item => { validateExternalDefinition(item, names); names.push(item.name); records += item.records.length; });
  if (records > externalLimits.records) throw new Error('Saved record limit exceeded.');
  value.formats.forEach(format => { if (format.predefined || builtInExternalFormats.some(item => item.name === format.name)) throw new Error('Invalid saved format.'); validateExternalFormat(format, Math.max(1, format.columns.filter(item => item.startsWith('Value ')).length)); });
  if (new Set(value.formats.map(item => item.name.toLowerCase())).size !== value.formats.length) throw new Error('Duplicate saved formats.');
  if (value.job && (!value.definitions.some(item => item.name === value.job!.indicator) || !['running', 'paused', 'cancelled', 'failed', 'completed'].includes(value.job.state) || !Number.isInteger(value.job.progress) || value.job.progress < 0 || value.job.progress > 100 || !Array.isArray(value.job.records) || value.job.records.length > externalLimits.records || value.job.records.some(row => !Number.isFinite(row.timestamp) || row.values.some(number => !Number.isFinite(number))))) throw new Error('Invalid saved external indicator job.');
}
export const useExternalIndicators = create<ExternalIndicatorsState>((set, get) => {
  let initial: Saved = { definitions: [], formats: [], job: null }; let storageError = '';
  try { const raw = localStorage.getItem(key); if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; } }
  catch { storageError = 'Saved external indicators could not be read. Existing browser storage has been preserved.'; }
  initial = { definitions: [], formats: [], job: null }; storageError = '';
  let jobId = ''; let timer: ReturnType<typeof setTimeout> | null = null;
  async function refresh(): Promise<void> {
    try { const state = await indicatorState(); set({ ...state, backendAvailable: true, storageError: '' }); }
    catch (cause) { set({ backendAvailable: false, storageError: cause instanceof Error ? cause.message : 'Indicator backend unavailable.' }); }
  }
  async function persist(patch: Partial<Saved>): Promise<void> {
    const saved = { definitions: get().definitions, formats: get().formats, job: get().job, ...patch }; validateSaved(saved);
    const state = await replaceIndicatorState({ definitions: saved.definitions, formats: saved.formats });
    set({ ...state, job: saved.job, storageError: '' });
  }
  async function poll(): Promise<void> {
    try {
      const status = await indicatorJob(jobId); const job = get().job; if (!job) return;
      if (status.state === 'succeeded') { await refresh(); set({ job: { ...job, state: 'completed', progress: 100, ignored: status.ignored } }); }
      else if (status.state === 'failed' || status.state === 'timed_out' || status.state === 'cancelled') set({ job: { ...job, state: status.state === 'cancelled' ? 'cancelled' : 'failed', error: status.state !== 'cancelled' ? 'Backend indicator import failed.' : undefined } });
      else timer = setTimeout(() => void poll(), 500);
    } catch (cause) { fail(cause); }
  }
  function fail(cause: unknown): void { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to persist import.' } }); }
  return { ...initial, backendAvailable: false, storageError, refresh,
    importLegacy: async () => { const raw = localStorage.getItem(key); if (!raw) throw new Error("No saved browser indicator data."); const saved = normalizeLegacyBranding(JSON.parse(raw)); validateSaved(saved); await persist({ definitions: saved.definitions, formats: saved.formats }); },
    add: async item => { const copy = structuredClone(item); validateExternalDefinition(copy, get().definitions.map(row => row.name)); await persist({ definitions: [...get().definitions, copy] }); },
    edit: async (original, item) => { const index = get().definitions.findIndex(row => row.name === original); if (index < 0) throw new Error('Custom indicator no longer exists.'); if (item.name !== original) throw new Error('Custom indicator cannot be renamed'); const copy = structuredClone(item); const previous = get().definitions[index]; if (previous.records.length && previous.values.filter(line => line.name).length !== copy.values.filter(line => line.name).length) throw new Error('Clear existing data before changing the number of indicator values.'); validateExternalDefinition(copy, get().definitions.filter(row => row.name !== original).map(row => row.name)); const definitions = [...get().definitions]; definitions[index] = copy; await persist({ definitions }); },
    clear: async names => { if (!names.length) throw new Error('You have to select at least one indicator.'); const selected = new Set(names); await persist({ definitions: get().definitions.map(item => selected.has(item.name) ? summarizeExternal({ ...item, records: [] }) : item), job: selected.has(get().job?.indicator ?? '') ? null : get().job }); },
    remove: async names => { if (!names.length) throw new Error('You have to select at least one indicator.'); const selected = new Set(names); await persist({ definitions: get().definitions.filter(item => !selected.has(item.name)), job: selected.has(get().job?.indicator ?? '') ? null : get().job }); },
    importDefinitions: async (items, overwrite) => { const definitions = [...get().definitions]; const replace = new Set(overwrite); for (const source of items) { const found = definitions.findIndex(item => item.name.toLowerCase() === source.name.toLowerCase()); if (found < 0) definitions.push(structuredClone(source)); else if (replace.has(definitions[found].name)) definitions[found] = { ...structuredClone(source), name: definitions[found].name, records: [], timeframe: '—', dateFrom: '', dateTo: '', totalDays: 0 }; } const names: string[] = []; definitions.forEach(item => { validateExternalDefinition(item, names); names.push(item.name); }); await persist({ definitions }); },
    saveFormat: async (format, replace = false) => { const name = format.name.trim(); const valueCount = format.columns.filter(item => item.startsWith('Value ')).length; validateExternalFormat({ ...format, name }, valueCount); if (builtInExternalFormats.some(item => item.name === name)) throw new Error('Choose another format name.'); if (!replace && get().formats.some(item => item.name.toLowerCase() === name.toLowerCase())) throw new Error(`Data format with name '${name}' already exists. Please choose another name.`); await persist({ formats: [...get().formats.filter(item => item.name.toLowerCase() !== name.toLowerCase()), { ...structuredClone(format), name, predefined: false }] }); },
    deleteFormat: async name => await persist({ formats: get().formats.filter(item => item.name !== name) }),
    startImport: async (indicator, text, format, ignoreErrors, externalActive) => {
      if (externalActive || externalJobActive(get().job?.state)) throw new Error('Finish or stop the active operation first.');
      const started = await importIndicator(indicator, text, format, ignoreErrors); jobId = started.job_id;
      set({ job: { canPause: false, indicator, state: 'running', progress: 0, records: [], timeframe: '', ignored: 0 } });
      void poll();
    },
    advance: () => { /* Backend jobs own execution and completion. */ },
    action: action => { if (action === 'stop' && jobId) { if (timer) clearTimeout(timer); void cancelIndicator(jobId).then(() => poll()).catch(fail); } },
  };
});
