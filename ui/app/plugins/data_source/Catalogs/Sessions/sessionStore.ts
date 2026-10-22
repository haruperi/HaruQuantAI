import { create } from 'zustand';
import type { CatalogSession, SessionDefinition, SessionElement } from './sessions';
import { cloneRemoteSession, deleteRemoteSession, fetchRemoteSessions, saveRemoteSession, saveSessionElement } from './sessionApiClient';

interface SessionState {
  sessions: CatalogSession[]; error: string; loaded: boolean; isSyncing: boolean; epoch: number; request: number;
  reset: () => void;
  refreshFromServer: () => Promise<void>;
  save: (item: SessionDefinition) => Promise<CatalogSession>;
  clone: (source: CatalogSession, name: string, minutes: number) => Promise<CatalogSession>;
  element: (id: string, action: 'add' | 'update' | 'remove', index?: number, window?: SessionElement) => Promise<CatalogSession>;
  remove: (ids: string[]) => Promise<{ deleted: string[]; failed: string[] }>;
}
export const useSessions = create<SessionState>((set,get) => {
  function accept(row: CatalogSession, epoch: number): CatalogSession {
    if (get().epoch !== epoch) throw new Error('The host session changed. Reopen the session form.');
    set(state => ({ sessions: [...state.sessions.filter(item => item.id !== row.id), row], loaded: true, isSyncing: false, request: state.request + 1 }));
    return row;
  }
  return {
    sessions: [], error: '', loaded: false, isSyncing: false, epoch: 0, request: 0,
    reset: () => set(state => ({ sessions: [], error: '', loaded: false, isSyncing: false, epoch: state.epoch + 1, request: state.request + 1 })),
    refreshFromServer: async () => {
      const epoch = get().epoch, request = get().request + 1;
      set({ request, isSyncing: true, error: '' });
      try {
        const rows = await fetchRemoteSessions();
        if (epoch === get().epoch && request === get().request) set({ sessions: rows, loaded: true });
      } catch (cause) {
        if (epoch === get().epoch && request === get().request) set({ error: cause instanceof Error ? cause.message : 'Unable to load sessions.' });
      } finally { if (epoch === get().epoch && request === get().request) set({ isSyncing: false }); }
    },
    save: async item => { const epoch = get().epoch; return accept(await saveRemoteSession(item), epoch); },
    clone: async (source, name, minutes) => { const epoch = get().epoch; return accept(await cloneRemoteSession(source.id, name, minutes), epoch); },
    element: async (id, action, index, window) => { const epoch = get().epoch; return accept(await saveSessionElement(id, action, index, window), epoch); },
    remove: async ids => {
      if (!ids.length) throw new Error('Select sessions to delete.');
      const epoch = get().epoch;
      const result = { deleted: [] as string[], failed: [] as string[] };
      for (const id of new Set(ids)) {
        try {
          await deleteRemoteSession(id);
          if (epoch !== get().epoch) throw new Error('The host session changed.');
          set(state => ({ sessions: state.sessions.filter(row => row.id !== id), request: state.request + 1, isSyncing: false }));
          result.deleted.push(id);
        } catch (cause) {
          if (epoch !== get().epoch) throw cause;
          result.failed.push(id);
        }
      }
      return result;
    },
  };
});
