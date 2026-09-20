import { normalizeLegacyBranding } from '../../app/branding';
import { reservedDarwinex } from './darwinexStore';
import { reservedCrypto } from './cryptoStore';
import { reservedYahoo } from './yahooStore';
import { reservedSQDefinitions } from './sqDataStore';
import { reservedMt5 } from './mt5ImportStore';
import { activeImport, useFileImports } from './fileImportStore';
import { create } from 'zustand';
import { canonicalInstrument, effectiveInstruments, seedInstruments, validateInstrument, validateName, type FileDefinition, type FileInstrument } from './fileSymbols';
interface FileState { definitions: FileDefinition[]; instruments: FileInstrument[]; overrides: Record<string, FileInstrument>; removed: string[]; storageError: string;
  addInstrument: (item: FileInstrument, brokers: string[]) => void;
  editInstrument: (original: string, item: FileInstrument, brokers: string[]) => void;
  replaceInstruments: (items: FileInstrument[], brokers: string[]) => void;
  removeInstruments: (names: string[], referenced: string[]) => void;
  importInstruments: (items: FileInstrument[], overwrite: string[], brokers: string[]) => void;
  addSymbol: (symbol: string, instrument: FileInstrument, barType: 'start' | 'end', existing: string[]) => void;
}
const key = 'sqx-file-symbols-v1';
export const useFileSymbols = create<FileState>((set, get) => {
  let initial: Pick<FileState, 'definitions' | 'instruments' | 'overrides' | 'removed' | 'storageError'> = { definitions: [], instruments: [], overrides: {}, removed: [], storageError: '' };
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const value = normalizeLegacyBranding(JSON.parse(raw));
      if (![1,2,3].includes(value.version) || !Array.isArray(value.definitions) || !Array.isArray(value.instruments) || value.definitions.length > 10000 || value.instruments.length > 10000) throw new Error('Invalid saved file data');
      const names = seedInstruments.map(item => item.symbol);
      for (const item of value.instruments as FileInstrument[]) { validateInstrument(item, names, [item.broker]); names.push(item.symbol); }
      const symbols: string[] = [];
      for (const row of value.definitions as FileDefinition[]) {
        validateName(row.symbol, symbols); symbols.push(row.symbol);
        if (['symbol','instrument','underlying','source','timeframe','broker','brokerName','timezone','category','connection'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.id !== `file:${row.symbol}` || row.source !== 'File import' || row.bars !== 0 || row.from !== '' || row.to !== '' || !['start','end'].includes(row.barType) || !names.includes(row.instrument)) throw new Error('Invalid saved definition');
      }
      const overrides = value.version >= 2 && value.overrides && typeof value.overrides === 'object' ? value.overrides as Record<string, FileInstrument> : {};
      const removed = value.version >= 2 && Array.isArray(value.removed) ? value.removed as string[] : [];
      if (Object.keys(overrides).length > 10000 || removed.length > 10000) throw new Error('Invalid saved instrument changes');
      for (const [name, item] of Object.entries(overrides)) { if (name !== item.symbol) throw new Error('Invalid instrument override'); validateInstrument(item, [], [item.broker]); }
      initial = { definitions: value.definitions, instruments: value.instruments, overrides, removed, storageError: '' };
    }
  } catch { initial.storageError = 'Saved file symbols could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<FileState>) {
    if (get().storageError) throw new Error(get().storageError);
    const next = { ...get(), ...patch };
    try { localStorage.setItem(key, JSON.stringify({ version: 3, definitions: next.definitions, instruments: next.instruments.map(canonicalInstrument), overrides: Object.fromEntries(Object.entries(next.overrides).map(([name,item])=>[name,canonicalInstrument(item)])), removed: next.removed })); }
    catch { throw new Error('Unable to save in browser storage. No changes were applied.'); }
    set(patch);
  }
  return { ...initial,
    addInstrument: (item, brokers) => {
      validateInstrument(item, effectiveInstruments(get().instruments, get().overrides, get().removed).map(row => row.symbol), brokers);
      if (get().instruments.length >= 10000) throw new Error('Mock instrument limit reached.');
      persist({ instruments: [...get().instruments, structuredClone({ ...item, name: item.name || 'not set' })] });
    },
    editInstrument: (original, item, brokers) => {
      if (item.symbol !== original) throw new Error('Instrument identity cannot be changed while editing.');
      validateInstrument(item, effectiveInstruments(get().instruments, get().overrides, get().removed).filter(row => row.symbol !== original).map(row => row.symbol), brokers);
      const index = get().instruments.findIndex(row => row.symbol === original);
      if (index >= 0) { const instruments = [...get().instruments]; instruments[index] = structuredClone(item); persist({ instruments }); }
      else if (seedInstruments.some(row => row.symbol === original)) persist({ overrides: { ...get().overrides, [original]: structuredClone(item) } });
      else throw new Error('Instrument no longer exists.');
    },
    replaceInstruments: (items, brokers) => {
      const names = new Set(items.map(item => item.symbol)); const current = effectiveInstruments(get().instruments, get().overrides, get().removed);
      for (const item of items) validateInstrument(item, current.filter(row => row.symbol !== item.symbol).map(row => row.symbol), brokers);
      const instruments = get().instruments.map(item => names.has(item.symbol) ? structuredClone(items.find(row => row.symbol === item.symbol)!) : item);
      const overrides = { ...get().overrides }; for (const item of items) if (seedInstruments.some(row => row.symbol === item.symbol)) overrides[item.symbol] = structuredClone(item);
      persist({ instruments, overrides });
    },
    removeInstruments: (names, referenced) => {
      if (!names.length) throw new Error('You have to select some record.');
      const blocked = names.find(name => referenced.includes(name)); if (blocked) throw new Error(`Instrument '${blocked}' is used by existing data and cannot be removed.`);
      const set = new Set(names); persist({ instruments: get().instruments.filter(item => !set.has(item.symbol)), overrides: Object.fromEntries(Object.entries(get().overrides).filter(([name]) => !set.has(name))), removed: [...new Set([...get().removed, ...names.filter(name => seedInstruments.some(row => row.symbol === name))])] });
    },
    importInstruments: (items, overwrite, brokers) => {
      const current = effectiveInstruments(get().instruments, get().overrides, get().removed); const overwriteSet = new Set(overwrite);
      const additions: FileInstrument[] = []; const replacements: FileInstrument[] = [];
      for (const item of items) { const found = current.find(row => row.symbol.toLowerCase() === item.symbol.toLowerCase()); if (found) { if (overwriteSet.has(found.symbol)) replacements.push({ ...item, symbol: found.symbol }); } else additions.push(item); }
      for (const item of additions) validateInstrument(item, [...current, ...additions.filter(row => row !== item)].map(row => row.symbol), brokers);
      const instruments = [...get().instruments, ...additions]; const overrides = { ...get().overrides };
      for (const item of replacements) { const index = instruments.findIndex(row => row.symbol === item.symbol); if (index >= 0) instruments[index] = structuredClone(item); else overrides[item.symbol] = structuredClone(item); }
      persist({ instruments, overrides, removed: get().removed.filter(name => !additions.some(item => item.symbol === name)) });
    },
    addSymbol: (symbol, instrument, barType, existing) => {
      if (useFileImports.getState().storageError) throw new Error(useFileImports.getState().storageError);
      validateName(symbol, [...reservedYahoo().map(row => row.symbol), ...reservedCrypto().map(row => row.symbol), ...reservedDarwinex().map(row => row.symbol), ...reservedSQDefinitions().map(row => row.symbol), ...reservedMt5().map(row => row.symbol), ...existing, ...get().definitions.map(row => row.symbol), ...useFileImports.getState().records.map(row => row.symbol), ...(activeImport(useFileImports.getState().job?.state) ? useFileImports.getState().job?.tasks.map(task => task.record.symbol) ?? [] : [])]);
      const item = effectiveInstruments(get().instruments, get().overrides, get().removed).find(row => row.symbol === instrument.symbol);
      if (!item || !['start','end'].includes(barType)) throw new Error('Choose an instrument and timestamp convention.');
      if (get().definitions.length >= 10000) throw new Error('Mock dataset limit reached.');
      persist({ definitions: [...get().definitions, { id: `file:${symbol}`, symbol, instrument: item.symbol, underlying: item.symbol, source: 'File import', connection: 'History', barType, timeframe: '—', broker: item.broker, brokerName: item.brokerName, timezone: item.timezone, category: item.type, from: '', to: '', bars: 0 }] });
    },
  };
});
