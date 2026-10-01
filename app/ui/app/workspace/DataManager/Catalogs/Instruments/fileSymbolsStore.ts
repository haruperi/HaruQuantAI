import { createDomainClient } from '../../../../host/transport';
import { catalogPort } from '../../Common/catalogClient';
import { normalizeLegacyBranding } from '../../../../host/branding';
import { create } from 'zustand';
import { canonicalInstrument, effectiveInstruments, validateInstrument, type FileInstrument } from './fileSymbols';
interface FileState { instruments: FileInstrument[]; overrides: Record<string, FileInstrument>; removed: string[]; storageError: string; refresh:()=>Promise<void>; importLegacy:()=>Promise<void>;
  addInstrument: (item: FileInstrument, brokers: string[]) => Promise<void>;
  editInstrument: (original: string, item: FileInstrument, brokers: string[]) => Promise<void>;
  replaceInstruments: (items: FileInstrument[], brokers: string[]) => Promise<void>;
  removeInstruments: (names: string[], referenced: string[]) => Promise<void>;
  importInstruments: (items: FileInstrument[], overwrite: string[], brokers: string[]) => Promise<void>;
  addSymbol: (symbol: string, instrument: FileInstrument, barType: 'start' | 'end', existing: string[]) => Promise<void>;
}
const key = 'sqx-file-symbols-v1';
export const useFileSymbols = create<FileState>((set, get) => {
  let initial: Pick<FileState, 'instruments' | 'overrides' | 'removed' | 'storageError'> = { instruments: [], overrides: {}, removed: [], storageError: '' };
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const value = normalizeLegacyBranding(JSON.parse(raw));
      if (![1,2,3].includes(value.version) || !Array.isArray(value.instruments) || value.instruments.length > 10000) throw new Error('Invalid saved file data');
      const names: string[] = [];
      for (const item of value.instruments as FileInstrument[]) { validateInstrument(item, names, [item.broker]); names.push(item.symbol); }
      const overrides = value.version >= 2 && value.overrides && typeof value.overrides === 'object' ? value.overrides as Record<string, FileInstrument> : {};
      const removed = value.version >= 2 && Array.isArray(value.removed) ? value.removed as string[] : [];
      if (Object.keys(overrides).length > 10000 || removed.length > 10000) throw new Error('Invalid saved instrument changes');
      for (const [name, item] of Object.entries(overrides)) { if (name !== item.symbol) throw new Error('Invalid instrument override'); validateInstrument(item, [], [item.broker]); }
      initial = { instruments: value.instruments, overrides, removed, storageError: '' };
    }
  } catch { initial.storageError = 'Saved file symbols could not be read. Existing storage is preserved.'; }
  initial = { instruments: [], overrides: {}, removed: [], storageError: '' };
  const port = catalogPort<any>('instruments');
  async function refresh(): Promise<void> { try { set({ ...await port.read(), storageError: '' }); } catch (cause) { set({ storageError: cause instanceof Error ? cause.message : 'Catalog unavailable.' }); } }
  async function importLegacy(): Promise<void> { const raw = localStorage.getItem('sqx-file-symbols-v1'); if (!raw) throw new Error('No saved browser catalog.'); const saved = normalizeLegacyBranding(JSON.parse(raw)); await persist(saved); }
  async function persist(patch: any): Promise<void> { const next = { ...get(), ...patch }; const state = await port.write({ instruments: next.instruments.map(canonicalInstrument), overrides: Object.fromEntries(Object.entries(next.overrides).map(([name,item])=>[name,canonicalInstrument(item as FileInstrument)])), removed: next.removed }); set({ ...state, storageError: '' }); }
  return { ...initial, refresh, importLegacy,
    addInstrument: async (item, brokers) => {
      validateInstrument(item, effectiveInstruments(get().instruments, get().overrides, get().removed).map(row => row.symbol), brokers);
      if (get().instruments.length >= 10000) throw new Error('Local instrument limit reached.');
      await persist({ instruments: [...get().instruments, structuredClone({ ...item, name: item.name || 'not set' })] });
    },
    editInstrument: async (original, item, brokers) => {
      if (item.symbol !== original) throw new Error('Instrument identity cannot be changed while editing.');
      validateInstrument(item, effectiveInstruments(get().instruments, get().overrides, get().removed).filter(row => row.symbol !== original).map(row => row.symbol), brokers);
      const index = get().instruments.findIndex(row => row.symbol === original);
      if (index >= 0) { const instruments = [...get().instruments]; instruments[index] = structuredClone(item); await persist({ instruments }); }
      else if (Boolean(get().overrides[original])) await persist({ overrides: { ...get().overrides, [original]: structuredClone(item) } });
      else throw new Error('Instrument no longer exists.');
    },
    replaceInstruments: async (items, brokers) => {
      const names = new Set(items.map(item => item.symbol)); const current = effectiveInstruments(get().instruments, get().overrides, get().removed);
      for (const item of items) validateInstrument(item, current.filter(row => row.symbol !== item.symbol).map(row => row.symbol), brokers);
      const instruments = get().instruments.map(item => names.has(item.symbol) ? structuredClone(items.find(row => row.symbol === item.symbol)!) : item);
      const overrides = { ...get().overrides }; for (const item of items) if (Boolean(get().overrides[item.symbol])) overrides[item.symbol] = structuredClone(item);
      await persist({ instruments, overrides });
    },
    removeInstruments: async (names, referenced) => {
      if (!names.length) throw new Error('You have to select some record.');
      const blocked = names.find(name => referenced.includes(name)); if (blocked) throw new Error(`Instrument '${blocked}' is used by existing data and cannot be removed.`);
      const set = new Set(names); await persist({ instruments: get().instruments.filter(item => !set.has(item.symbol)), overrides: Object.fromEntries(Object.entries(get().overrides).filter(([name]) => !set.has(name))), removed: [...new Set([...get().removed, ...names.filter(name => Boolean(get().overrides[name]))])] });
    },
    importInstruments: async (items, overwrite, brokers) => {
      const current = effectiveInstruments(get().instruments, get().overrides, get().removed); const overwriteSet = new Set(overwrite);
      const additions: FileInstrument[] = []; const replacements: FileInstrument[] = [];
      for (const item of items) { const found = current.find(row => row.symbol.toLowerCase() === item.symbol.toLowerCase()); if (found) { if (overwriteSet.has(found.symbol)) replacements.push({ ...item, symbol: found.symbol }); } else additions.push(item); }
      for (const item of additions) validateInstrument(item, [...current, ...additions.filter(row => row !== item)].map(row => row.symbol), brokers);
      const instruments = [...get().instruments, ...additions]; const overrides = { ...get().overrides };
      for (const item of replacements) { const index = instruments.findIndex(row => row.symbol === item.symbol); if (index >= 0) instruments[index] = structuredClone(item); else overrides[item.symbol] = structuredClone(item); }
      await persist({ instruments, overrides, removed: get().removed.filter(name => !additions.some(item => item.symbol === name)) });
    },
    addSymbol: async (symbol, instrument, _barType, existing) => {
      validateInstrument(instrument, [], [instrument.broker]);
      if (existing.includes(symbol)) throw new Error('Dataset name already exists.');
      const client = createDomainClient('/contributions/workspace.data_manager');
      await client.post('/sources.file_import.add', { symbol, instrument: instrument.symbol, timeframe: 'M1' });
    },
  };
});
