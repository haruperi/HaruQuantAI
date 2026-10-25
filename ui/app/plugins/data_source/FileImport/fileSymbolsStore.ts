import { normalizeSymbolContract } from '../Common/symbolContract';
import { normalizeLegacyBranding } from '../../../host/branding';
import { reservedDarwinex } from '../Darwinex/darwinexStore';
import { reservedCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo } from '../Yahoo/yahooStore';
import { reservedSQDefinitions } from '../SQData/sqDataStore';
import { reservedMt5 } from '../MetaTrader/mt5ImportStore';
import { activeImport, useFileImports } from './fileImportStore';
import { create } from 'zustand';
import { canonicalSymbol, effectiveSymbols, seedSymbols, validateSymbol, validateName, type FileDefinition, type FileSymbol } from './fileSymbols';
interface FileState { definitions: FileDefinition[]; symbols: FileSymbol[]; overrides: Record<string, FileSymbol>; removed: string[]; storageError: string;
  addSymbolDefinition: (item: FileSymbol, brokers: string[]) => void;
  editSymbol: (original: string, item: FileSymbol, brokers: string[]) => void;
  replaceSymbols: (items: FileSymbol[], brokers: string[]) => void;
  removeSymbols: (names: string[], referenced: string[]) => void;
  importSymbols: (items: FileSymbol[], overwrite: string[], brokers: string[]) => void;
  addSymbol: (symbol: string, symbolDefinition: FileSymbol, barType: 'start' | 'end', existing: string[]) => void;
}
const key = 'sqx-file-symbols-v1';
export const useFileSymbols = create<FileState>((set, get) => {
  let initial: Pick<FileState, 'definitions' | 'symbols' | 'overrides' | 'removed' | 'storageError'> = { definitions: [], symbols: [], overrides: {}, removed: [], storageError: '' };
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const value = normalizeLegacyBranding(normalizeSymbolContract(JSON.parse(raw)));
      if (![1,2,3].includes(value.version) || !Array.isArray(value.definitions) || !Array.isArray(value.symbols) || value.definitions.length > 10000 || value.symbols.length > 10000) throw new Error('Invalid saved file data');
      const names = seedSymbols.map(item => item.symbol);
      for (const item of value.symbols as FileSymbol[]) { validateSymbol(item, names, [item.broker]); names.push(item.symbol); }
      const symbols: string[] = [];
      for (const row of value.definitions as FileDefinition[]) {
        validateName(row.symbol, symbols); symbols.push(row.symbol);
        if (['symbol','symbolDefinition','underlying','source','timeframe','broker','brokerName','timezone','category','connection'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.id !== `file:${row.symbol}` || row.source !== 'File import' || row.bars !== 0 || row.from !== '' || row.to !== '' || !['start','end'].includes(row.barType) || !names.includes(row.symbolDefinition)) throw new Error('Invalid saved definition');
      }
      const overrides = value.version >= 2 && value.overrides && typeof value.overrides === 'object' ? value.overrides as Record<string, FileSymbol> : {};
      const removed = value.version >= 2 && Array.isArray(value.removed) ? value.removed as string[] : [];
      if (Object.keys(overrides).length > 10000 || removed.length > 10000) throw new Error('Invalid saved symbol changes');
      for (const [name, item] of Object.entries(overrides)) { if (name !== item.symbol) throw new Error('Invalid symbol override'); validateSymbol(item, [], [item.broker]); }
      initial = { definitions: value.definitions, symbols: value.symbols, overrides, removed, storageError: '' };
    }
  } catch { initial.storageError = 'Saved file symbols could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<FileState>) {
    if (get().storageError) throw new Error(get().storageError);
    const next = { ...get(), ...patch };
    try { localStorage.setItem(key, JSON.stringify({ version: 3, definitions: next.definitions, symbols: next.symbols.map(canonicalSymbol), overrides: Object.fromEntries(Object.entries(next.overrides).map(([name,item])=>[name,canonicalSymbol(item)])), removed: next.removed })); }
    catch { throw new Error('Unable to save in browser storage. No changes were applied.'); }
    set(patch);
  }
  return { ...initial,
    addSymbolDefinition: (item, brokers) => {
      validateSymbol(item, effectiveSymbols(get().symbols, get().overrides, get().removed).map(row => row.symbol), brokers);
      if (get().symbols.length >= 10000) throw new Error('Mock symbol limit reached.');
      persist({ symbols: [...get().symbols, structuredClone({ ...item, name: item.name || 'not set' })] });
    },
    editSymbol: (original, item, brokers) => {
      if (item.symbol !== original) throw new Error('Symbol identity cannot be changed while editing.');
      validateSymbol(item, effectiveSymbols(get().symbols, get().overrides, get().removed).filter(row => row.symbol !== original).map(row => row.symbol), brokers);
      const index = get().symbols.findIndex(row => row.symbol === original);
      if (index >= 0) { const symbols = [...get().symbols]; symbols[index] = structuredClone(item); persist({ symbols }); }
      else if (seedSymbols.some(row => row.symbol === original)) persist({ overrides: { ...get().overrides, [original]: structuredClone(item) } });
      else throw new Error('Symbol no longer exists.');
    },
    replaceSymbols: (items, brokers) => {
      const names = new Set(items.map(item => item.symbol)); const current = effectiveSymbols(get().symbols, get().overrides, get().removed);
      for (const item of items) validateSymbol(item, current.filter(row => row.symbol !== item.symbol).map(row => row.symbol), brokers);
      const symbols = get().symbols.map(item => names.has(item.symbol) ? structuredClone(items.find(row => row.symbol === item.symbol)!) : item);
      const overrides = { ...get().overrides }; for (const item of items) if (seedSymbols.some(row => row.symbol === item.symbol)) overrides[item.symbol] = structuredClone(item);
      persist({ symbols, overrides });
    },
    removeSymbols: (names, referenced) => {
      if (!names.length) throw new Error('You have to select some record.');
      const blocked = names.find(name => referenced.includes(name)); if (blocked) throw new Error(`Symbol '${blocked}' is used by existing data and cannot be removed.`);
      const set = new Set(names); persist({ symbols: get().symbols.filter(item => !set.has(item.symbol)), overrides: Object.fromEntries(Object.entries(get().overrides).filter(([name]) => !set.has(name))), removed: [...new Set([...get().removed, ...names.filter(name => seedSymbols.some(row => row.symbol === name))])] });
    },
    importSymbols: (items, overwrite, brokers) => {
      const current = effectiveSymbols(get().symbols, get().overrides, get().removed); const overwriteSet = new Set(overwrite);
      const additions: FileSymbol[] = []; const replacements: FileSymbol[] = [];
      for (const item of items) { const found = current.find(row => row.symbol.toLowerCase() === item.symbol.toLowerCase()); if (found) { if (overwriteSet.has(found.symbol)) replacements.push({ ...item, symbol: found.symbol }); } else additions.push(item); }
      for (const item of additions) validateSymbol(item, [...current, ...additions.filter(row => row !== item)].map(row => row.symbol), brokers);
      const symbols = [...get().symbols, ...additions]; const overrides = { ...get().overrides };
      for (const item of replacements) { const index = symbols.findIndex(row => row.symbol === item.symbol); if (index >= 0) symbols[index] = structuredClone(item); else overrides[item.symbol] = structuredClone(item); }
      persist({ symbols, overrides, removed: get().removed.filter(name => !additions.some(item => item.symbol === name)) });
    },
    addSymbol: (symbol, symbolDefinition, barType, existing) => {
      if (useFileImports.getState().storageError) throw new Error(useFileImports.getState().storageError);
      validateName(symbol, [...reservedYahoo().map(row => row.symbol), ...reservedCrypto().map(row => row.symbol), ...reservedDarwinex().map(row => row.symbol), ...reservedSQDefinitions().map(row => row.symbol), ...reservedMt5().map(row => row.symbol), ...existing, ...get().definitions.map(row => row.symbol), ...useFileImports.getState().records.map(row => row.symbol), ...(activeImport(useFileImports.getState().job?.state) ? useFileImports.getState().job?.tasks.map(task => task.record.symbol) ?? [] : [])]);
      const item = effectiveSymbols(get().symbols, get().overrides, get().removed).find(row => row.symbol === symbolDefinition.symbol);
      if (!item || !['start','end'].includes(barType)) throw new Error('Choose an symbol and timestamp convention.');
      if (get().definitions.length >= 10000) throw new Error('Mock dataset limit reached.');
      persist({ definitions: [...get().definitions, { id: `file:${symbol}`, symbol, symbolDefinition: item.symbol, underlying: item.symbol, source: 'File import', connection: 'History', barType, timeframe: '—', broker: item.broker, brokerName: item.brokerName, timezone: item.timezone, category: item.type, from: '', to: '', bars: 0 }] });
    },
  };
});
