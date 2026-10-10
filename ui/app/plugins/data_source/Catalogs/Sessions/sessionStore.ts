import { normalizeLegacyBranding } from '../../../../host/branding';
import { create } from 'zustand';
import {
  effectiveSessions,
  seedSessions,
  validateSession,
  type SessionDefinition,
} from './sessions';
import {
  fetchRemoteSessions,
  massDeleteRemoteSessions,
  saveRemoteSession,
} from './sessionApiClient';

interface SessionState {
  sessions: SessionDefinition[];
  overrides: Record<string, SessionDefinition>;
  removed: string[];
  storageError: string;
  isSyncing: boolean;
  refreshFromServer: () => Promise<void>;
  add: (item: SessionDefinition, brokers: string[]) => void;
  edit: (original: string, item: SessionDefinition, brokers: string[]) => void;
  clone: (item: SessionDefinition, brokers: string[]) => void;
  remove: (names: string[], referenced: string[]) => void;
  importSessions: (items: SessionDefinition[], overwrite: string[]) => void;
  importForBroker: (items: SessionDefinition[], overwrite: string[]) => void;
}

const key = 'haru-data-sessions-v1';

export const useSessions = create<SessionState>((set, get) => {
  let initial: Pick<
    SessionState,
    'sessions' | 'overrides' | 'removed' | 'storageError' | 'isSyncing'
  > = {
    sessions: [],
    overrides: {},
    removed: [],
    storageError: '',
    isSyncing: false,
  };

  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null;
    if (raw) {
      const value = normalizeLegacyBranding(JSON.parse(raw));
      if (Array.isArray(value.sessions) && value.sessions.length <= 10000) {
        initial = {
          sessions: value.sessions as SessionDefinition[],
          overrides: (value.overrides && typeof value.overrides === 'object' ? value.overrides : {}) as Record<string, SessionDefinition>,
          removed: Array.isArray(value.removed) ? (value.removed as string[]) : [],
          storageError: '',
          isSyncing: false,
        };
      }
    }
  } catch {
    initial.storageError =
      'Saved sessions could not be read. Existing browser storage has been preserved.';
  }

  function persist(patch: Partial<SessionState>): void {
    if (get().storageError && patch.storageError === undefined) {
      throw new Error(get().storageError);
    }
    const next = { ...get(), ...patch, storageError: patch.storageError ?? '' };
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(
          key,
          JSON.stringify({
            version: 1,
            sessions: next.sessions,
            overrides: next.overrides,
            removed: next.removed,
          }),
        );
      }
    } catch {
      throw new Error(
        'Unable to save sessions in browser storage. No changes were applied.',
      );
    }
    set({ ...patch, storageError: patch.storageError ?? '' });
  }

  const store: SessionState = {
    ...initial,
    refreshFromServer: async () => {
      set({ isSyncing: true, storageError: '' });
      try {
        const remote = await fetchRemoteSessions();
        if (remote && remote.length > 0) {
          const remoteNames = new Set(remote.map((r) => r.name.toLowerCase()));
          const preservedCustom = get().sessions.filter(
            (s) => !remoteNames.has(s.name.toLowerCase()),
          );
          const activeRemoved = get().removed.filter(
            (name) => !remoteNames.has(name.toLowerCase()),
          );
          persist({
            sessions: [...remote, ...preservedCustom],
            removed: activeRemoved,
            storageError: '',
          });
        }
      } catch {
        // Fallback silently to cached / seed sessions if offline
      } finally {
        set({ isSyncing: false });
      }
    },
    add: (item, brokers) => {
      validateSession(
        item,
        effectiveSessions(get().sessions, get().overrides, get().removed).map(
          (row) => row.name,
        ),
        brokers,
      );
      persist({ sessions: [...get().sessions, structuredClone(item)] });
      void saveRemoteSession(item).catch(() => {});
    },
    edit: (original, item, brokers) => {
      if (item.name !== original) {
        throw new Error('Session identity cannot be changed while editing.');
      }
      const all = effectiveSessions(get().sessions, get().overrides, get().removed);
      validateSession(
        item,
        all.filter((row) => row.name !== original).map((row) => row.name),
        brokers,
        false,
      );
      const index = get().sessions.findIndex((row) => row.name === original);
      if (index >= 0) {
        const sessions = [...get().sessions];
        sessions[index] = structuredClone(item);
        persist({ sessions });
      } else if (seedSessions.some((row) => row.name === original)) {
        persist({ overrides: { ...get().overrides, [original]: structuredClone(item) } });
      } else {
        throw new Error('Session no longer exists.');
      }
      void saveRemoteSession(item).catch(() => {});
    },
    clone: (item, brokers) => {
      validateSession(
        item,
        effectiveSessions(get().sessions, get().overrides, get().removed).map(
          (row) => row.name,
        ),
        brokers,
      );
      persist({ sessions: [...get().sessions, structuredClone(item)] });
      void saveRemoteSession(item).catch(() => {});
    },
    remove: (names, referenced) => {
      if (!names.length) throw new Error('No session selected');
      const blocked = names.find((name) => referenced.includes(name));
      if (blocked) {
        throw new Error(`Session '${blocked}' is used by an instrument and cannot be removed.`);
      }
      const selected = new Set(names);
      persist({
        sessions: get().sessions.filter((row) => !selected.has(row.name)),
        overrides: Object.fromEntries(
          Object.entries(get().overrides).filter(([name]) => !selected.has(name)),
        ),
        removed: [
          ...new Set([
            ...get().removed,
            ...names.filter((name) => seedSessions.some((row) => row.name === name)),
          ]),
        ],
      });
      void massDeleteRemoteSessions(names).catch(() => {});
    },
    importSessions: (items, overwrite) => {
      const current = effectiveSessions(get().sessions, get().overrides, get().removed);
      const replace = new Set(overwrite);
      const sessions = [...get().sessions];
      const overrides = { ...get().overrides };
      for (const item of items) {
        const found = current.find(
          (row) => row.name.toLowerCase() === item.name.toLowerCase(),
        );
        if (found) {
          if (!replace.has(found.name)) continue;
          const value = {
            ...item,
            name: found.name,
            broker: found.broker,
            brokerName: found.brokerName,
          };
          const index = sessions.findIndex((row) => row.name === found.name);
          if (index >= 0) sessions[index] = value;
          else overrides[found.name] = value;
        } else {
          sessions.push(item);
        }
        void saveRemoteSession(item).catch(() => {});
      }
      persist({ sessions, overrides });
    },
    importForBroker: (items, overwrite) => {
      const current = effectiveSessions(get().sessions, get().overrides, get().removed);
      const replace = new Set(overwrite);
      const sessions = [...get().sessions];
      const overrides = { ...get().overrides };
      for (const item of items) {
        const found = current.find(
          (row) => row.name.toLowerCase() === item.name.toLowerCase(),
        );
        if (found) {
          if (!replace.has(found.name)) continue;
          const value = { ...structuredClone(item), name: found.name };
          const index = sessions.findIndex((row) => row.name === found.name);
          if (index >= 0) sessions[index] = value;
          else overrides[found.name] = value;
        } else {
          sessions.push(structuredClone(item));
        }
        void saveRemoteSession(item).catch(() => {});
      }
      persist({ sessions, overrides });
    },
  };

  return store;
});
