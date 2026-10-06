import { normalizeLegacyBranding } from '../../../app/branding';
import { create } from 'zustand';
import { builtInExternalFormats, externalLimits, summarizeExternal, validateExternalDefinition, validateExternalFormat, type ExternalImportFormat, type ExternalImportJob, type ExternalIndicatorDefinition, type ExternalIndicatorRecord } from './externalIndicators';

interface Saved { definitions: ExternalIndicatorDefinition[]; formats: ExternalImportFormat[]; job: ExternalImportJob | null }
interface ExternalIndicatorsState extends Saved {
  storageError: string;
  add: (item: ExternalIndicatorDefinition) => void; edit: (original: string, item: ExternalIndicatorDefinition) => void;
  clear: (names: string[]) => void; remove: (names: string[]) => void;
  importDefinitions: (items: ExternalIndicatorDefinition[], overwrite: string[]) => void;
  saveFormat: (item: ExternalImportFormat, replace?: boolean) => void; deleteFormat: (name: string) => void;
  startImport: (indicator: string, records: ExternalIndicatorRecord[], timeframe: string, ignored: number, externalActive: boolean) => void;
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
  function persist(patch: Partial<Saved>): void {
    if (get().storageError) throw new Error(get().storageError); const saved = { definitions: get().definitions, formats: get().formats, job: get().job, ...patch }; validateSaved(saved);
    try { localStorage.setItem(key, JSON.stringify({ version: 1, ...saved })); } catch { throw new Error('Unable to save external indicators in browser storage. No changes were applied.'); } set(patch);
  }
  function fail(cause: unknown): void { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to persist import.' } }); }
  return { ...initial, storageError,
    add: item => { const copy = structuredClone(item); validateExternalDefinition(copy, get().definitions.map(row => row.name)); persist({ definitions: [...get().definitions, copy] }); },
    edit: (original, item) => { const index = get().definitions.findIndex(row => row.name === original); if (index < 0) throw new Error('Custom indicator no longer exists.'); if (item.name !== original) throw new Error('Custom indicator cannot be renamed'); const copy = structuredClone(item); const previous = get().definitions[index]; if (previous.records.length && previous.values.filter(line => line.name).length !== copy.values.filter(line => line.name).length) throw new Error('Clear existing data before changing the number of indicator values.'); validateExternalDefinition(copy, get().definitions.filter(row => row.name !== original).map(row => row.name)); const definitions = [...get().definitions]; definitions[index] = copy; persist({ definitions }); },
    clear: names => { if (!names.length) throw new Error('You have to select at least one indicator.'); const selected = new Set(names); persist({ definitions: get().definitions.map(item => selected.has(item.name) ? summarizeExternal({ ...item, records: [] }) : item), job: selected.has(get().job?.indicator ?? '') ? null : get().job }); },
    remove: names => { if (!names.length) throw new Error('You have to select at least one indicator.'); const selected = new Set(names); persist({ definitions: get().definitions.filter(item => !selected.has(item.name)), job: selected.has(get().job?.indicator ?? '') ? null : get().job }); },
    importDefinitions: (items, overwrite) => { const definitions = [...get().definitions]; const replace = new Set(overwrite); for (const source of items) { const found = definitions.findIndex(item => item.name.toLowerCase() === source.name.toLowerCase()); if (found < 0) definitions.push(structuredClone(source)); else if (replace.has(definitions[found].name)) definitions[found] = { ...structuredClone(source), name: definitions[found].name, records: [], timeframe: '—', dateFrom: '', dateTo: '', totalDays: 0 }; } const names: string[] = []; definitions.forEach(item => { validateExternalDefinition(item, names); names.push(item.name); }); persist({ definitions }); },
    saveFormat: (format, replace = false) => { const name = format.name.trim(); const valueCount = format.columns.filter(item => item.startsWith('Value ')).length; validateExternalFormat({ ...format, name }, valueCount); if (builtInExternalFormats.some(item => item.name === name)) throw new Error('Choose another format name.'); if (!replace && get().formats.some(item => item.name.toLowerCase() === name.toLowerCase())) throw new Error(`Data format with name '${name}' already exists. Please choose another name.`); persist({ formats: [...get().formats.filter(item => item.name.toLowerCase() !== name.toLowerCase()), { ...structuredClone(format), name, predefined: false }] }); },
    deleteFormat: name => persist({ formats: get().formats.filter(item => item.name !== name) }),
    startImport: (indicator, records, timeframe, ignored, externalActive) => { if (externalActive || externalJobActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.'); if (!get().definitions.some(item => item.name === indicator)) throw new Error('Custom indicator no longer exists.'); persist({ job: { indicator, state: 'running', progress: 0, records: structuredClone(records), timeframe, ignored } }); },
    advance: () => { const job = get().job; if (!job || job.state !== 'running') return; const progress = Math.min(100, job.progress + 8); try { if (progress < 100) persist({ job: { ...job, progress } }); else { const definitions = get().definitions.map(item => item.name === job.indicator ? summarizeExternal({ ...item, records: structuredClone(job.records), timeframe: job.timeframe }) : item); persist({ definitions, job: { ...job, progress: 100, state: 'completed' } }); } } catch (cause) { fail(cause); } },
    action: action => { const job = get().job; if (!job || !externalJobActive(job.state)) return; try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); } catch (cause) { fail(cause); } },
  };
});
