import { normalizeLegacyBranding } from '../../../app/branding';
import { datasets } from '../../../mocks/fixtures';
import { validateName } from './fileSymbols';
import { create } from 'zustand';
import { builtInFormats, limits, timezones, validateFormat, type ImportFormat, type ImportJob, type ImportRecord, type ImportTask } from './fileImport';
interface Saved { formats: ImportFormat[]; records: ImportRecord[]; groups: { name: string; symbols: string[] }[]; timezone: string; job: ImportJob | null }
interface Store extends Saved { storageError: string; saveFormat: (format: ImportFormat, replace?: boolean) => void; deleteFormat: (name: string) => void; start: (tasks: ImportTask[], timezone: string, group: string, skipped: number, externalActive: boolean) => void; advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void }
const key = 'sqx-file-import-v1';
export const activeImport = (state: string | undefined) => state === 'running' || state === 'paused';
function validateSaved(value: Saved) {
  if (!Array.isArray(value.formats) || value.formats.length > 100 || !Array.isArray(value.records) || value.records.length > 10000 || !Array.isArray(value.groups) || value.groups.length > 1000 || !timezones.some(([id]) => id === value.timezone)) throw new Error('Invalid saved imports.');
  value.formats.forEach(format => { validateFormat(format); if (!format.name || format.name.length > 80 || format.predefined || ['Custom', ...builtInFormats.map(f => f.name)].includes(format.name)) throw new Error('Invalid saved format.'); });
  if (new Set(value.formats.map(f => f.name)).size !== value.formats.length || new Set(value.records.map(r => r.id)).size !== value.records.length) throw new Error('Duplicate saved entries.');
  const records = [...value.records, ...(value.job?.tasks?.map(task => task.record) ?? [])];
  let count = 0;
  for (const record of records) {
    if (!record || record.source !== 'File import' || ['id', 'symbol', 'instrument', 'underlying', 'timeframe', 'broker', 'brokerName', 'timezone', 'category', 'from', 'to'].some(field => typeof (record as unknown as Record<string, unknown>)[field] !== 'string') || !['start', 'end'].includes(record.barType) || !Array.isArray(record.timestamps) || record.timestamps.length > limits.timestamps || !Number.isInteger(record.unknownBars) || record.unknownBars < 0 || record.bars !== record.timestamps.length + record.unknownBars || record.timestamps.some((stamp, i) => !Number.isFinite(stamp) || !Number.isFinite(new Date(stamp).getTime()) || (i > 0 && stamp <= record.timestamps[i - 1]))) throw new Error('Invalid saved records.');
    validateName(record.symbol, []);
    if (record.id !== `file:${record.symbol}` && !datasets.some(row => row.source === 'File import' && row.id === record.id && row.symbol === record.symbol)) throw new Error('Invalid imported record identity.');
    if ((record.from || record.to) && (!/^\d{4}-\d{2}-\d{2}$/.test(record.from) || !/^\d{4}-\d{2}-\d{2}$/.test(record.to) || record.from > record.to)) throw new Error('Invalid imported range.');
    count += record.timestamps.length;
  }
  if (count > limits.timestamps * 2) throw new Error('Saved timestamp limit exceeded.');
  for (const group of value.groups) if (!group || typeof group.name !== 'string' || !group.name || group.name.length > 300 || !Array.isArray(group.symbols) || group.symbols.length > 10000 || group.symbols.some(symbol => typeof symbol !== 'string')) throw new Error('Invalid saved group.');
  if (value.job && (!Array.isArray(value.job.tasks) || value.job.tasks.length > limits.files || !['running', 'paused', 'completed', 'failed', 'cancelled'].includes(value.job.state) || !Number.isInteger(value.job.progress) || value.job.progress < 0 || value.job.progress > 100 || !Number.isInteger(value.job.completed) || value.job.completed < 0 || value.job.completed > value.job.tasks.length || typeof value.job.group !== 'string' || value.job.group.length > 300 || !Number.isInteger(value.job.skipped) || value.job.skipped < 0 || value.job.tasks.some(task => typeof task.filename !== 'string' || task.filename.length > 300 || !Number.isInteger(task.ignored) || task.ignored < 0 || (task.error !== undefined && typeof task.error !== 'string')) || new Set(value.job.tasks.map(task => task.record.id)).size !== value.job.tasks.length)) throw new Error('Invalid saved job.');
}
export const useFileImports = create<Store>((set, get) => {
  let initial: Saved = { formats: [], records: [], groups: [], timezone: 'EETUS', job: null }; let storageError = '';
  try { const raw = localStorage.getItem(key); if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; } }
  catch { storageError = 'Saved file imports could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<Saved>) {
    if (get().storageError) throw new Error(get().storageError);
    const { formats, records, groups, timezone, job } = { ...get(), ...patch };
    const saved = { formats, records, groups, timezone, job }; validateSaved(saved);
    try { localStorage.setItem(key, JSON.stringify({ version: 1, ...saved })); }
    catch { throw new Error('Unable to save file import in browser storage. No changes were applied.'); }
    set(patch);
  }
  function fail(cause: unknown) { const job = get().job; if (job) set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to persist import.' } }); }
  return { ...initial, storageError,
    saveFormat: (format, replace = false) => {
      validateFormat(format); const name = format.name.trim();
      if (!name || name.length > 80 || ['Custom', ...builtInFormats.map(row => row.name)].includes(name)) throw new Error('Enter a unique custom format name (1–80 characters).');
      if (!replace && get().formats.some(row => row.name === name)) throw new Error('A format with this name already exists.');
      const formats = get().formats.filter(row => row.name !== name);
      persist({ formats: [...formats, { ...format, name, predefined: false }] });
    },
    deleteFormat: name => persist({ formats: get().formats.filter(row => row.name !== name) }),
    start: (tasks, timezone, group, skipped, externalActive) => {
      if (externalActive || activeImport(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      if (!tasks.length) throw new Error(skipped ? `All ${skipped} files were skipped. No import started.` : 'Choose data to import.');
      const planned = new Map(get().records.map(row => [row.id, row])); tasks.forEach(task => planned.set(task.record.id, task.record));
      if ([...planned.values()].reduce((n, row) => n + row.timestamps.length, 0) > limits.timestamps) throw new Error('Browser mock limit: 200,000 tracked timestamps. Import a smaller selection.');
      let name = group; let n = 2; while (name && get().groups.some(row => row.name === name)) name = `${group} ${n++}`;
      persist({ timezone, job: { tasks, state: 'running', progress: 0, completed: 0, skipped, group: name } });
    },
    advance: () => {
      const { job, records, groups } = get(); if (!job || job.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5);
      const count = Math.floor(progress * job.tasks.length / 100);
      let next = [...records]; let completed = job.completed; let error: string | undefined;
      for (; completed < count; completed++) { const task = job.tasks[completed]; if (task.error) { error = `${task.filename}: ${task.error}`; break; } next = [...next.filter(row => row.id !== task.record.id), task.record]; }
      const updatedGroups = [...groups];
      if (job.group && completed > 0) { const symbols = job.tasks.slice(0, completed).map(task => task.record.symbol); const index = updatedGroups.findIndex(row => row.name === job.group); if (index < 0) updatedGroups.push({ name: job.group, symbols }); else updatedGroups[index] = { name: job.group, symbols }; }
      try { persist({ records: next, groups: updatedGroups, job: { ...job, progress, completed, state: error ? 'failed' : progress === 100 ? 'completed' : 'running', error } }); } catch (cause) { fail(cause); }
    },
    action: action => { const job = get().job; if (!job || !activeImport(job.state)) return; try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); } catch (cause) { fail(cause); } },
  };
});
