import { create } from 'zustand';
import type { FileSymbol, SymbolBroker, SymbolMassPatch } from '../../FileImport/fileSymbols';
import { cloneRemoteSymbol, deleteRemoteSymbols, fetchRemoteSymbols, refreshRemoteSymbols, symbolPatch, massEditRemoteSymbols, saveRemoteSymbol, toFileSymbol, type CatalogSymbol, type RemoteSymbolDefinition } from './symbolsApiClient';

export interface SymbolsState {
  symbols: CatalogSymbol[];
  error: string; isSyncing: boolean; loaded: boolean; generation: number; requestVersion: number;
  reset: () => void;
  refreshFromServer: (brokers?: SymbolBroker[]) => Promise<void>;
  addSymbolDefinition: (item: FileSymbol, datasource?: string) => Promise<void>;
  editSymbol: (original: CatalogSymbol, item: FileSymbol) => Promise<void>;
  cloneSymbol: (source: CatalogSymbol, name: string) => Promise<void>;
  massEditSymbols: (ids: string[], patch: SymbolMassPatch) => Promise<void>;
  refreshSymbols: (symbols?: string[]) => Promise<number>;
  removeSymbols: (ids: string[]) => Promise<number>;
}
export const useSymbols = create<SymbolsState>((set, get) => {
  function accept(records: RemoteSymbolDefinition[], generation: number): void {
    if (generation !== get().generation) throw new Error('The host session changed. Reopen the symbol form.');
    const mapped = records.map(row => toFileSymbol(row));
    set(state => ({ requestVersion: state.requestVersion + 1, isSyncing: false, symbols: [...state.symbols.filter(row => !mapped.some(item => item.id === row.id)), ...mapped], loaded: true }));
  }
  return {
    symbols: [], error: '', isSyncing: false, loaded: false, generation: 0, requestVersion: 0,
    reset: () => set(state => ({ symbols: [], error: '', loaded: false, isSyncing: false, generation: state.generation + 1, requestVersion: state.requestVersion + 1 })),
    refreshFromServer: async (brokers = []) => {
      const generation = get().generation;
      const requestVersion = get().requestVersion + 1;
      set({ requestVersion, isSyncing: true, error: '' });
      try {
        const records = await fetchRemoteSymbols();
        if (generation === get().generation && requestVersion === get().requestVersion) set({ symbols: records.map(row => toFileSymbol(row, brokers)), loaded: true });
      } catch (cause) {
        if (generation === get().generation && requestVersion === get().requestVersion) set({ error: cause instanceof Error ? cause.message : 'Unable to load symbols.' });
      } finally { if (generation === get().generation && requestVersion === get().requestVersion) set({ isSyncing: false }); }
    },
    addSymbolDefinition: async (item, datasource) => {
      const generation = get().generation;
      accept([await saveRemoteSymbol(item, datasource)], generation);
    },
    editSymbol: async (original, item) => {
      if (item.symbol !== original.symbol || item.broker !== original.broker) throw new Error('Symbol identity cannot be changed while editing.');
      const fields: SymbolMassPatch['fields'] = {};
      const keys = ['name','type','pointValue','tickSize','tickStep','spread','slippage','minDistance','multiplier','sizeStep','commission','swap','contractSize','pipSize','marginRate','decimals','minVolume','maxVolume','lotStep','tickValue'] as const;
      for (const key of keys) if (JSON.stringify(original[key]) !== JSON.stringify(item[key])) fields[key] = true;
      if (!Object.keys(fields).length) return;
      const generation = get().generation;
      accept(await massEditRemoteSymbols([original.id], symbolPatch(item, fields)), generation);
    },
    cloneSymbol: async (source, name) => {
      const generation = get().generation;
      accept([await cloneRemoteSymbol(source.id, name)], generation);
    },
    massEditSymbols: async (ids, patch) => {
      const updates = symbolPatch(patch.value, patch.fields);
      if (!ids.length || !Object.keys(updates).length) throw new Error('Select symbols and at least one field for change.');
      const generation = get().generation;
      accept(await massEditRemoteSymbols(ids, updates), generation);
    },
    refreshSymbols: async symbols => {
      const result = await refreshRemoteSymbols(symbols);
      await get().refreshFromServer();
      if (get().error) throw new Error(get().error);
      return result.inserted_count;
    },
    removeSymbols: async ids => {
      const count = await deleteRemoteSymbols(ids);
      set(state => ({ requestVersion: state.requestVersion + 1, symbols: state.symbols.filter(row => !ids.includes(row.id)) }));
      return count;
    },
  };
});
