import { catalogPort } from '../../Common/catalogClient';
import { normalizeLegacyBranding } from '../../../../host/branding';
import { create } from 'zustand';
import { normalizeGroupName, validateGroup, type StockGroupDefinition, type StockMembership } from './stockGroups';

interface Saved { groups: StockGroupDefinition[]; }
interface Store extends Saved {
  storageError: string; refresh:()=>Promise<void>; importLegacy:()=>Promise<void>;
  saveGroup: (name: string, description: string, source?: StockGroupDefinition) => Promise<StockGroupDefinition>;
  replaceMembers: (id: string, members: StockMembership[]) => Promise<void>;
  remove: (ids: string[]) => Promise<void>;
  syncImports: (groups: { name: string; symbols: string[] }[]) => Promise<void>;
  applyImported: (items: StockGroupDefinition[], decisions: Record<string, 'skip'|'overwrite'>) => Promise<void>;
}
const key = 'sqx-stock-groups-v1';
const fingerprint = (symbols: string[]) => [...symbols].sort().join('\u001f');

function validateSaved(value: Saved): void {
  if (!Array.isArray(value.groups) || value.groups.length > 1_000) throw new Error('Invalid saved stock groups.');
  value.groups.forEach(group => validateGroup(group, value.groups));
  if (new Set(value.groups.map(group => group.id)).size !== value.groups.length) throw new Error('Duplicate saved stock-group entries.');
}

export const useStockGroups = create<Store>((set, get) => {
  let initial: Saved = { groups: [] }; let storageError = '';
  try { const raw = localStorage.getItem(key); if (raw) { const value = normalizeLegacyBranding(JSON.parse(raw)); if (value.version !== 1) throw new Error('Version'); validateSaved(value); initial = { groups: value.groups }; } }
  catch { storageError = 'Saved stock groups could not be read. Existing storage is preserved.'; }
  initial = { groups: [] };
  const port = catalogPort<any>('groups');
  async function refresh(): Promise<void> { try { set({ ...await port.read(), storageError: '' }); } catch (cause) { set({ storageError: cause instanceof Error ? cause.message : 'Catalog unavailable.' }); } }
  async function importLegacy(): Promise<void> { const raw = localStorage.getItem('sqx-stock-groups-v1'); if (!raw) throw new Error('No saved browser catalog.'); const saved = normalizeLegacyBranding(JSON.parse(raw)); await persist(saved); }
  async function persist(patch: any): Promise<void> { const next = { ...get(), ...patch }; const state = await port.write({ groups: next.groups }); set({ ...state, storageError: '' }); }
  return { ...initial, refresh, importLegacy, storageError,
    saveGroup: async (name, description, source) => {
      if (source?.system) throw new Error("This group can't be edited.");
      const normalized = normalizeGroupName(name); const item: StockGroupDefinition = source ? { ...source, name: normalized, description: description.trim(), origin: undefined, originName: undefined, originFingerprint: undefined } : { id: `group:${Date.now()}:${Math.random().toString(36).slice(2)}`, name: normalized, description: description.trim(), system: false, members: [] };
      validateGroup(item, get().groups); await persist({ groups: source ? get().groups.map(group => group.id === source.id ? item : group) : [...get().groups, item] }); return item;
    },
    replaceMembers: async (id, members) => {
      const source = get().groups.find(group => group.id === id); if (!source) throw new Error('Stockgroup was not found.'); if (source.system) throw new Error("This group can't be edited.");
      const item = { ...source, members, origin: undefined, originName: undefined, originFingerprint: undefined } as StockGroupDefinition; validateGroup(item, get().groups); await persist({ groups: get().groups.map(group => group.id === id ? item : group) });
    },
    remove: async ids => { const deletable = get().groups.filter(group => ids.includes(group.id) && !group.system); if (!deletable.length) throw new Error('You have to select some non default group.'); await persist({ groups: get().groups.filter(group => !deletable.some(item => item.id === group.id)) }); },
    syncImports: async imported => {
      let changed = false; const groups = [...get().groups];
      for (const source of imported) {
        const originFingerprint = fingerprint(source.symbols); const existing = groups.find(group => group.origin === 'file-import' && group.originName === source.name);
        if (existing) { if (existing.originFingerprint !== originFingerprint) { existing.members = source.symbols.map(ticker => ({ ticker })); existing.originFingerprint = originFingerprint; changed = true; } continue; }
        const name = normalizeGroupName(source.name); if (groups.some(group => group.name.toLowerCase() === name.toLowerCase())) continue;
        groups.push({ id: `file-group:${source.name}`, name, description: 'Imported from folder', system: false, members: source.symbols.map(ticker => ({ ticker })), origin: 'file-import', originName: source.name, originFingerprint }); changed = true;
      }
      if (changed) await persist({ groups });
    },
    applyImported: async (items, decisions) => {
      const groups = [...get().groups];
      for (const source of items) { const index = groups.findIndex(group => group.name.toLowerCase() === source.name.toLowerCase()); if (index >= 0) { if (decisions[source.name] !== 'overwrite') continue; if (groups[index].system) throw new Error("This group can't be edited."); groups[index] = { ...source, id: groups[index].id }; } else groups.push({ ...source, id: `group:${Date.now()}:${Math.random().toString(36).slice(2)}` }); }
      groups.forEach(group => validateGroup(group, groups)); await persist({ groups });
    },
  };
});
