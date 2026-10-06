import { normalizeLegacyBranding } from '../../../../app/branding';
import { create } from 'zustand';
import { makeGeneratedDataset, normalizeGroupName, validateGroup, type StockGroupDataset, type StockGroupDefinition, type StockGroupUpdateJob, type StockMembership } from './stockGroups';

interface Saved { groups: StockGroupDefinition[]; generated: StockGroupDataset[]; job: StockGroupUpdateJob | null }
interface Store extends Saved {
  storageError: string;
  saveGroup: (name: string, description: string, source?: StockGroupDefinition) => StockGroupDefinition;
  replaceMembers: (id: string, members: StockMembership[]) => void;
  remove: (ids: string[]) => void;
  syncImports: (groups: { name: string; symbols: string[] }[]) => void;
  start: (ids: string[], existingSymbols: string[], externalActive: boolean) => void;
  advance: () => void;
  action: (action: 'pause'|'resume'|'stop') => void;
  applyImported: (items: StockGroupDefinition[], decisions: Record<string, 'skip'|'overwrite'>) => void;
}
const key = 'sqx-stock-groups-v1';
export const stockGroupJobActive = (state?: string) => state === 'running' || state === 'paused';
const fingerprint = (symbols: string[]) => [...symbols].sort().join('\u001f');

function validateSaved(value: Saved): void {
  if (!Array.isArray(value.groups) || value.groups.length > 1_000 || !Array.isArray(value.generated) || value.generated.length > 10_000) throw new Error('Invalid saved stock groups.');
  value.groups.forEach(group => validateGroup(group, value.groups));
  if (new Set(value.groups.map(group => group.id)).size !== value.groups.length || new Set(value.generated.map(row => row.id)).size !== value.generated.length) throw new Error('Duplicate saved stock-group entries.');
  value.generated.forEach(row => { if (!row.id.startsWith('stock-group:') || !row.symbol || row.bars < 0 || !row.from || !row.to) throw new Error('Invalid generated stock-group data.'); });
  if (value.job && (!Array.isArray(value.job.groupIds) || !Array.isArray(value.job.tickers) || !['running','paused','completed','failed','cancelled'].includes(value.job.state) || !Number.isInteger(value.job.progress) || value.job.progress < 0 || value.job.progress > 100 || !Number.isInteger(value.job.completed) || value.job.completed < 0 || value.job.completed > value.job.tickers.length)) throw new Error('Invalid stock-group job.');
}

export const useStockGroups = create<Store>((set, get) => {
  let initial: Saved = { groups: [], generated: [], job: null }; let storageError = '';
  try { const raw = localStorage.getItem(key); if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = value; if (initial.job?.state === 'running') initial.job.state = 'paused'; } }
  catch { storageError = 'Saved stock groups could not be read. Existing storage is preserved.'; }
  const persist = (patch: Partial<Saved>) => {
    if (get().storageError) throw new Error(get().storageError);
    const saved = { groups: get().groups, generated: get().generated, job: get().job, ...patch }; validateSaved(saved);
    try { localStorage.setItem(key, JSON.stringify({ version: 1, ...saved })); }
    catch { throw new Error('Unable to save stock groups in browser storage. No changes were applied.'); }
    set(patch);
  };
  return { ...initial, storageError,
    saveGroup: (name, description, source) => {
      if (source?.system) throw new Error("This group can't be edited.");
      const normalized = normalizeGroupName(name); const item: StockGroupDefinition = source ? { ...source, name: normalized, description: description.trim(), origin: undefined, originName: undefined, originFingerprint: undefined } : { id: `group:${Date.now()}:${Math.random().toString(36).slice(2)}`, name: normalized, description: description.trim(), system: false, members: [] };
      validateGroup(item, get().groups); persist({ groups: source ? get().groups.map(group => group.id === source.id ? item : group) : [...get().groups, item] }); return item;
    },
    replaceMembers: (id, members) => {
      const source = get().groups.find(group => group.id === id); if (!source) throw new Error('Stockgroup was not found.'); if (source.system) throw new Error("This group can't be edited.");
      const item = { ...source, members, origin: undefined, originName: undefined, originFingerprint: undefined } as StockGroupDefinition; validateGroup(item, get().groups); persist({ groups: get().groups.map(group => group.id === id ? item : group) });
    },
    remove: ids => { const deletable = get().groups.filter(group => ids.includes(group.id) && !group.system); if (!deletable.length) throw new Error('You have to select some non default group.'); persist({ groups: get().groups.filter(group => !deletable.some(item => item.id === group.id)) }); },
    syncImports: imported => {
      let changed = false; const groups = [...get().groups];
      for (const source of imported) {
        const originFingerprint = fingerprint(source.symbols); const existing = groups.find(group => group.origin === 'file-import' && group.originName === source.name);
        if (existing) { if (existing.originFingerprint !== originFingerprint) { existing.members = source.symbols.map(ticker => ({ ticker })); existing.originFingerprint = originFingerprint; changed = true; } continue; }
        const name = normalizeGroupName(source.name); if (groups.some(group => group.name.toLowerCase() === name.toLowerCase())) continue;
        groups.push({ id: `file-group:${source.name}`, name, description: 'Imported from folder', system: false, members: source.symbols.map(ticker => ({ ticker })), origin: 'file-import', originName: source.name, originFingerprint }); changed = true;
      }
      if (changed) persist({ groups });
    },
    start: (ids, existingSymbols, externalActive) => {
      if (externalActive || stockGroupJobActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      const selected = get().groups.filter(group => ids.includes(group.id)); if (!selected.length) throw new Error('You have to select some group.');
      if (selected.some(group => group.name === '[[S&P 100 limited]]')) throw new Error('Group S&P 100 limited cannot be updated, it is only in clean installation.');
      const tickers = [...new Set(selected.flatMap(group => group.members.map(member => member.ticker)))]; if (!tickers.length) throw new Error('Nothing to update. Group is without any stocks.');
      const missing = tickers.filter(ticker => !existingSymbols.some(symbol => symbol.toUpperCase() === ticker.toUpperCase()));
      persist({ job: { groupIds: ids, tickers: missing, state: 'running', progress: 0, completed: 0 } });
    },
    advance: () => {
      const job = get().job; if (!job || job.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5); const completed = Math.floor(progress * job.tickers.length / 100);
      const additions = job.tickers.slice(0, completed).map(makeGeneratedDataset); const generated = [...new Map([...get().generated, ...additions].map(row => [row.id, row])).values()];
      try { persist({ generated, job: { ...job, progress, completed, state: progress === 100 ? 'completed' : 'running' } }); }
      catch (cause) { set({ job: { ...job, state: 'failed', error: cause instanceof Error ? cause.message : 'Unable to persist stock-group update.' } }); }
    },
    action: action => { const job = get().job; if (!job || !stockGroupJobActive(job.state)) return; persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); },
    applyImported: (items, decisions) => {
      const groups = [...get().groups];
      for (const source of items) { const index = groups.findIndex(group => group.name.toLowerCase() === source.name.toLowerCase()); if (index >= 0) { if (decisions[source.name] !== 'overwrite') continue; if (groups[index].system) throw new Error("This group can't be edited."); groups[index] = { ...source, id: groups[index].id }; } else groups.push({ ...source, id: `group:${Date.now()}:${Math.random().toString(36).slice(2)}` }); }
      groups.forEach(group => validateGroup(group, groups)); persist({ groups });
    },
  };
});
