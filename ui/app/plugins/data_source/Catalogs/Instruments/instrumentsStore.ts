import { create } from 'zustand';
import type { FileInstrument, InstrumentBroker, InstrumentMassPatch } from '../../FileImport/fileSymbols';
import { cloneRemoteInstrument, deleteRemoteInstruments, fetchRemoteInstruments, refreshRemoteInstruments, instrumentPatch, massEditRemoteInstruments, saveRemoteInstrument, toFileInstrument, type CatalogInstrument, type RemoteInstrumentDefinition } from './instrumentsApiClient';

export interface InstrumentsState {
  instruments: CatalogInstrument[];
  error: string; isSyncing: boolean; loaded: boolean; generation: number; requestVersion: number;
  reset: () => void;
  refreshFromServer: (brokers?: InstrumentBroker[]) => Promise<void>;
  addInstrument: (item: FileInstrument) => Promise<void>;
  editInstrument: (original: CatalogInstrument, item: FileInstrument) => Promise<void>;
  cloneInstrument: (source: CatalogInstrument, name: string) => Promise<void>;
  massEditInstruments: (ids: string[], patch: InstrumentMassPatch) => Promise<void>;
  refreshInstruments: (symbols?: string[]) => Promise<number>;
  removeInstruments: (ids: string[]) => Promise<number>;
}
export const useInstruments = create<InstrumentsState>((set, get) => {
  function accept(records: RemoteInstrumentDefinition[], generation: number): void {
    if (generation !== get().generation) throw new Error('The host session changed. Reopen the instrument form.');
    const mapped = records.map(row => toFileInstrument(row));
    set(state => ({ requestVersion: state.requestVersion + 1, isSyncing: false, instruments: [...state.instruments.filter(row => !mapped.some(item => item.id === row.id)), ...mapped], loaded: true }));
  }
  return {
    instruments: [], error: '', isSyncing: false, loaded: false, generation: 0, requestVersion: 0,
    reset: () => set(state => ({ instruments: [], error: '', loaded: false, isSyncing: false, generation: state.generation + 1, requestVersion: state.requestVersion + 1 })),
    refreshFromServer: async (brokers = []) => {
      const generation = get().generation;
      const requestVersion = get().requestVersion + 1;
      set({ requestVersion, isSyncing: true, error: '' });
      try {
        const records = await fetchRemoteInstruments();
        if (generation === get().generation && requestVersion === get().requestVersion) set({ instruments: records.map(row => toFileInstrument(row, brokers)), loaded: true });
      } catch (cause) {
        if (generation === get().generation && requestVersion === get().requestVersion) set({ error: cause instanceof Error ? cause.message : 'Unable to load instruments.' });
      } finally { if (generation === get().generation && requestVersion === get().requestVersion) set({ isSyncing: false }); }
    },
    addInstrument: async item => {
      const generation = get().generation;
      accept([await saveRemoteInstrument(item)], generation);
    },
    editInstrument: async (original, item) => {
      if (item.symbol !== original.symbol || item.broker !== original.broker) throw new Error('Instrument identity cannot be changed while editing.');
      const fields: InstrumentMassPatch['fields'] = {};
      const keys = ['name','type','pointValue','tickSize','tickStep','spread','slippage','minDistance','multiplier','sizeStep','commission','swap','contractSize','pipSize','marginRate','decimals','minVolume','maxVolume','lotStep','tickValue'] as const;
      for (const key of keys) if (JSON.stringify(original[key]) !== JSON.stringify(item[key])) fields[key] = true;
      if (!Object.keys(fields).length) return;
      const generation = get().generation;
      accept(await massEditRemoteInstruments([original.id], instrumentPatch(item, fields)), generation);
    },
    cloneInstrument: async (source, name) => {
      const generation = get().generation;
      accept([await cloneRemoteInstrument(source.id, name)], generation);
    },
    massEditInstruments: async (ids, patch) => {
      const updates = instrumentPatch(patch.value, patch.fields);
      if (!ids.length || !Object.keys(updates).length) throw new Error('Select instruments and at least one field for change.');
      const generation = get().generation;
      accept(await massEditRemoteInstruments(ids, updates), generation);
    },
    refreshInstruments: async symbols => {
      const result = await refreshRemoteInstruments(symbols);
      await get().refreshFromServer();
      if (get().error) throw new Error(get().error);
      return result.inserted_count;
    },
    removeInstruments: async ids => {
      const count = await deleteRemoteInstruments(ids);
      set(state => ({ requestVersion: state.requestVersion + 1, instruments: state.instruments.filter(row => !ids.includes(row.id)) }));
      return count;
    },
  };
});
