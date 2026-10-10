import { normalizeLegacyBranding } from '../../../../host/branding';
import { create } from 'zustand';
import {
  canonicalInstrument,
  effectiveInstruments,
  seedInstruments,
  validateInstrument,
  type FileInstrument,
  type InstrumentBroker,
  type InstrumentMassPatch,
} from '../../FileImport/fileSymbols';
import {
  cloneRemoteInstrument,
  exportInstrumentsXmlRemote,
  fetchRemoteInstruments,
  fromFileInstrument,
  importInstrumentsXmlRemote,
  massDeleteRemoteInstruments,
  massEditRemoteInstruments,
  saveRemoteInstrument,
  toFileInstrument,
  updateRemoteInstrument,
} from './instrumentsApiClient';

export interface InstrumentsState {
  instruments: FileInstrument[];
  overrides: Record<string, FileInstrument>;
  removed: string[];
  storageError: string;
  isSyncing: boolean;
  refreshFromServer: (brokers?: InstrumentBroker[]) => Promise<void>;
  addInstrument: (item: FileInstrument, brokers: string[]) => Promise<void>;
  editInstrument: (original: string, item: FileInstrument, brokers: string[]) => Promise<void>;
  cloneInstrument: (source: FileInstrument, cloneName: string, brokerId: number, postfix?: string) => Promise<void>;
  removeInstruments: (symbols: string[]) => Promise<void>;
  massEditInstruments: (symbols: string[], patch: InstrumentMassPatch) => Promise<void>;
  exportXml: (symbols?: string[]) => Promise<string>;
  importXml: (xmlContent: string, conflictPolicy?: 'skip' | 'overwrite_all' | 'cancel') => Promise<void>;
}

const key = 'sqx-instruments-catalog-v1';

export const useInstruments = create<InstrumentsState>((set, get) => {
  let initial: Pick<InstrumentsState, 'instruments' | 'overrides' | 'removed' | 'storageError' | 'isSyncing'> = {
    instruments: [],
    overrides: {},
    removed: [],
    storageError: '',
    isSyncing: false,
  };

  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null;
    if (raw) {
      const value = normalizeLegacyBranding(JSON.parse(raw));
      if (Array.isArray(value.instruments) && value.instruments.length <= 10000) {
        initial = {
          instruments: value.instruments as FileInstrument[],
          overrides: (value.overrides && typeof value.overrides === 'object' ? value.overrides : {}) as Record<string, FileInstrument>,
          removed: Array.isArray(value.removed) ? (value.removed as string[]) : [],
          storageError: '',
          isSyncing: false,
        };
      }
    }
  } catch {
    initial.storageError = 'Saved instruments could not be read. Existing storage preserved.';
  }

  function persist(patch: Partial<InstrumentsState>): void {
    if (get().storageError) throw new Error(get().storageError);
    const next = { ...get(), ...patch };
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(
          key,
          JSON.stringify({
            version: 1,
            instruments: next.instruments.map(canonicalInstrument),
            overrides: Object.fromEntries(
              Object.entries(next.overrides).map(([name, item]) => [name, canonicalInstrument(item)]),
            ),
            removed: next.removed,
          }),
        );
      }
    } catch {
      throw new Error('Unable to save in browser storage. No changes were applied.');
    }
    set(patch);
  }

  return {
    ...initial,

    refreshFromServer: async (brokers: InstrumentBroker[] = []) => {
      set({ isSyncing: true });
      try {
        const remote = await fetchRemoteInstruments();
        if (remote && remote.length > 0) {
          const mapped = remote.map((r) => toFileInstrument(r, brokers));
          persist({ instruments: mapped, overrides: {}, removed: [] });
        }
      } catch {
        // Fallback silently to cached / seed state if offline
      } finally {
        set({ isSyncing: false });
      }
    },

    addInstrument: async (item: FileInstrument, brokers: string[]) => {
      const currentList = get().instruments.length > 0 ? get().instruments : seedInstruments;
      validateInstrument(
        item,
        currentList.map((row) => row.symbol),
        brokers,
      );
      const cleanItem = canonicalInstrument(item);
      const nextList = [...get().instruments.filter((row) => row.symbol !== cleanItem.symbol), cleanItem];
      persist({ instruments: nextList });
      try {
        await saveRemoteInstrument(cleanItem);
      } catch {
        // Optimistic write preserved locally
      }
    },

    editInstrument: async (original: string, item: FileInstrument, brokers: string[]) => {
      if (item.symbol !== original) {
        throw new Error('Instrument identity cannot be changed while editing.');
      }
      const currentList = get().instruments.length > 0 ? get().instruments : seedInstruments;
      validateInstrument(
        item,
        currentList.filter((row) => row.symbol !== original).map((row) => row.symbol),
        brokers,
      );
      const cleanItem = canonicalInstrument(item);
      const nextList = get().instruments.map((row) => (row.symbol === original ? cleanItem : row));
      if (!nextList.some((row) => row.symbol === original)) {
        nextList.push(cleanItem);
      }
      persist({ instruments: nextList });
      try {
        await updateRemoteInstrument(original, fromFileInstrument(cleanItem));
      } catch {
        // Optimistic write preserved locally
      }
    },

    cloneInstrument: async (
      source: FileInstrument,
      cloneName: string,
      brokerId: number,
      postfix = '',
    ) => {
      const cleanTargetName = cloneName.trim();
      if (!cleanTargetName) throw new Error('Please enter a valid target instrument symbol.');
      try {
        const remoteRes = await cloneRemoteInstrument(source.symbol, cleanTargetName, brokerId, postfix);
        const mapped = toFileInstrument(remoteRes);
        const nextList = [...get().instruments.filter((row) => row.symbol !== mapped.symbol), mapped];
        persist({ instruments: nextList });
      } catch (err) {
        // Local fallback clone if backend is unreachable
        const cloned: FileInstrument = {
          ...structuredClone(source),
          symbol: cleanTargetName,
          name: `${source.name || source.symbol} (Clone)`,
          broker: String(brokerId),
        };
        const nextList = [...get().instruments.filter((row) => row.symbol !== cloned.symbol), cloned];
        persist({ instruments: nextList });
        throw err;
      }
    },

    removeInstruments: async (symbols: string[]) => {
      if (!symbols.length) throw new Error('You have to select some record.');
      const toRemove = new Set(symbols.map((s) => s.toLowerCase()));
      const nextList = get().instruments.filter((row) => !toRemove.has(row.symbol.toLowerCase()));
      persist({
        instruments: nextList,
        removed: [...new Set([...get().removed, ...symbols])],
      });
      try {
        await massDeleteRemoteInstruments(symbols);
      } catch {
        // Optimistic delete preserved
      }
    },

    massEditInstruments: async (symbols: string[], patch: InstrumentMassPatch) => {
      if (!symbols.length) return;
      const targetSymbols = new Set(symbols);
      const nextList = get().instruments.map((row) => {
        if (!targetSymbols.has(row.symbol)) return row;
        const next = structuredClone(row);
        for (const key of Object.keys(patch.fields) as (keyof InstrumentMassPatch['fields'])[]) {
          if (patch.fields[key]) {
            (next as unknown as Record<string, unknown>)[key] = structuredClone(patch.value[key]);
          }
        }
        return next;
      });
      persist({ instruments: nextList });
      try {
        await massEditRemoteInstruments(symbols, patch.value as unknown as Record<string, unknown>, patch.fields);
      } catch {
        // Local patch preserved
      }
    },

    exportXml: async (symbols?: string[]) => {
      return await exportInstrumentsXmlRemote(symbols);
    },

    importXml: async (xmlContent: string, conflictPolicy: 'skip' | 'overwrite_all' | 'cancel' = 'overwrite_all') => {
      await importInstrumentsXmlRemote(xmlContent, conflictPolicy);
      await get().refreshFromServer();
    },
  };
});
