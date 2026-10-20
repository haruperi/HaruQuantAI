/** Browser-shell connection to the host session, readiness, and settings services. */

import { createContext, useContext, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { Button, Field, Modal, TextInput } from '../components/ui';
import { useAppStore } from './store';
import { readHostPreferences, shellPreferences, watchSettingsChanges, writeHostPreferences, type HostSettingsSnapshot, type ShellPreferences } from './hostSettings';
import { ApiClientError, createDomainClient, getAuthToken, getSessionPersistenceWarning, login, restoreSavedSession, setAuthToken, subscribeAuthExpired } from './transport';

export type HostStatus = 'connecting' | 'online' | 'locked' | 'offline';
export type SaveSettingsResult = { ok: true } | { ok: false; message: string };

export interface ConnectHostOptions {
  signal: AbortSignal;
  password?: string;
  fetchFn?: typeof fetch;
  onStatus: (status: HostStatus) => void;
  onSettings: (snapshot: HostSettingsSnapshot) => void;
  onCoreCount?: (cores: number) => void;
  onError: (message: string) => void;
}

export async function connectHost(options: ConnectHostOptions): Promise<void> {
  const { signal, onStatus, onSettings, onError } = options;
  const config = { signal, fetchFn: options.fetchFn };
  const refresh = async () => {
    const snapshot = await readHostPreferences(config);
    if (!signal.aborted) onSettings(snapshot);
  };

  try {
    try {
      if (options.password !== undefined) {
        await login({ password: options.password }, config);
      } else if (getAuthToken() || restoreSavedSession()) {
        await createDomainClient('', config).get('/sessions/me');
      } else {
        onStatus('locked');
        onError('Enter the host password to connect.');
        return;
      }
    } finally {
      options.password = undefined;
    }
    if (signal.aborted) return;
    const persistenceIssue = getSessionPersistenceWarning();
    if (persistenceIssue) onError(persistenceIssue);
    await refresh();
    if (options.onCoreCount) {
      const status = await createDomainClient('', config).get<{ cpu_count?: number }>('/status');
      if (!signal.aborted && Number.isInteger(status.cpu_count) && (status.cpu_count ?? 0) > 0) options.onCoreCount(status.cpu_count!);
    }
    await createDomainClient('', config).post('/app-loaded', {});
    if (signal.aborted) return;
    onStatus('online');
    await watchSettingsChanges({
      signal,
      fetchFn: options.fetchFn,
      onChanged: refresh,
      onConnection: connected => { if (!signal.aborted) onStatus(connected ? 'online' : 'offline'); },
    });
  } catch (error) {
    if (signal.aborted) return;
    if (error instanceof ApiClientError && (error.status === 401 || error.status === 429)) {
      setAuthToken(null);
      onStatus('locked');
      onError(error.status === 429 ? 'Too many login attempts. Wait a minute, then try again.' : 'The host requires a valid password or a new session.');
    } else {
      onStatus('offline');
      onError(error instanceof Error ? error.message : 'Host connection failed');
    }
  }
}

type SettingsChange = Partial<ShellPreferences> | ((current: ShellPreferences) => Partial<ShellPreferences>);

interface HostConnectionValue {
  status: HostStatus;
  settingsRevision: number | null;
  saveSettings: (change: SettingsChange, openingRevision?: number | null) => Promise<SaveSettingsResult>;
}

const HostConnectionContext = createContext<HostConnectionValue | null>(null);

export function useHostConnection(): HostConnectionValue {
  const value = useContext(HostConnectionContext);
  if (!value) throw new Error('HostConnectionProvider is required');
  return value;
}

export function HostConnectionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<HostStatus>('connecting');
  const statusRef = useRef<HostStatus>('connecting');
  const [message, setMessage] = useState('');
  const [password, setPassword] = useState('');
  const [loginVisible, setLoginVisible] = useState(false);
  const credentialRef = useRef<string | undefined>(undefined);
  const connectionRef = useRef<AbortController | null>(null);
  const [attempt, setAttempt] = useState(0);
  const writeQueue = useRef<Promise<void>>(Promise.resolve());
  const revisionRef = useRef<number | null>(null);
  const [settingsRevision, setSettingsRevision] = useState<number | null>(null);
  const preferencesRef = useRef<ShellPreferences | null>(null);
  const coreCountRef = useRef<number | null>(null);

  const applySettings = (snapshot: HostSettingsSnapshot) => {
    if (revisionRef.current !== null && snapshot.revision < revisionRef.current) return;
    revisionRef.current = snapshot.revision;
    setSettingsRevision(snapshot.revision);
    preferencesRef.current = snapshot.preferences;
    const configuration = { ...snapshot.preferences.configuration };
    if (coreCountRef.current !== null) {
      configuration.totalCores = coreCountRef.current;
      configuration.customCores = Math.min(configuration.customCores, coreCountRef.current);
    }
    const workers = configuration.coreUsage === 'custom' ? configuration.customCores :
      configuration.coreUsage === 'single' ? 1 :
      Math.max(1, configuration.totalCores - (configuration.coreUsage === 'reserve-one' ? 1 : 0));
    useAppStore.getState().updateSettings({ ...snapshot.preferences, configuration, workers, memoryGb: configuration.memoryGb });
  };

  const updateStatus = (next: HostStatus) => { statusRef.current = next; setStatus(next); if (next === 'locked') setLoginVisible(true); if (next === 'online') setLoginVisible(false); };

  useEffect(() => subscribeAuthExpired(() => {
    updateStatus('locked');
    setMessage('The host session expired. Reconnect to continue.');
  }), []);

  useEffect(() => {
    const controller = new AbortController();
    connectionRef.current = controller;
    const credential = credentialRef.current;
    credentialRef.current = undefined;
    updateStatus('connecting');
    void connectHost({
      signal: controller.signal,
      password: credential,
      onStatus: updateStatus,
      onSettings: applySettings,
      onCoreCount: cores => {
        coreCountRef.current = cores;
        const current = useAppStore.getState().settings.configuration;
        const configuration = { ...current, totalCores: cores, customCores: Math.min(current.customCores, cores) };
        const workers = configuration.coreUsage === 'custom' ? configuration.customCores :
          configuration.coreUsage === 'single' ? 1 :
          Math.max(1, cores - (configuration.coreUsage === 'reserve-one' ? 1 : 0));
        useAppStore.getState().updateSettings({ configuration, workers });
      },
      onError: error => setMessage(error),
    });
    return () => { controller.abort(); };
  }, [attempt]);

  const recoverSession = async (): Promise<boolean> => {
    revisionRef.current = null;
    setSettingsRevision(null);
    preferencesRef.current = null;
    setAuthToken(null);
    updateStatus('locked');
    setMessage('Enter the host password to reconnect, then retry saving.');
    return false;
  };

  const saveSettings = (requested: SettingsChange, openingRevision?: number | null): Promise<SaveSettingsResult> => {
    const task = writeQueue.current.then(async (): Promise<SaveSettingsResult> => {
      const failure = (reason: string): SaveSettingsResult => {
        const message = `Settings were not saved: ${reason}`;
        useAppStore.getState().notify(message);
        return { ok: false, message };
      };
      if (statusRef.current !== 'online' || revisionRef.current === null || preferencesRef.current === null) {
        if (!await recoverSession()) return failure('host session unavailable. Reconnect and retry.');
      }
      if (openingRevision !== undefined && openingRevision !== revisionRef.current) {
        return failure('settings changed since this dialog opened. Close and reopen it to review the latest settings.');
      }
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          const previous = preferencesRef.current!;
          const change = typeof requested === 'function' ? requested(previous) : requested;
          const displayed = shellPreferences(useAppStore.getState().settings);
          const configuration = { ...previous.configuration };
          if (change.configuration) {
            const draft = change.configuration as unknown as Record<string, unknown>;
            const visible = displayed.configuration as unknown as Record<string, unknown>;
            const target = configuration as unknown as Record<string, unknown>;
            for (const [field, value] of Object.entries(draft)) {
              if (!Object.is(value, visible[field])) target[field] = value;
            }
            if (draft.coreUsage === 'custom' && visible.coreUsage !== 'custom') {
              target.customCores = draft.customCores;
            }
          }
          const next = { ...previous, ...change, configuration };
          const saved = await writeHostPreferences(next, previous, revisionRef.current!);
          applySettings(saved);
          useAppStore.getState().notify(saved.wrote ? 'Settings saved to host database.' : 'Settings are already up to date.');
          return { ok: true };
        } catch (error) {
          if (error instanceof ApiClientError && error.status === 401 && attempt === 0) {
            setAuthToken(null);
            if (await recoverSession()) continue;
            return failure('host session expired. Reconnect and retry.');
          }
          if (error instanceof ApiClientError && error.status === 409) {
            try { applySettings(await readHostPreferences()); } catch { /* Preserve the last valid view. */ }
            return failure('settings changed in another session. Review and retry.');
          }
          return failure(error instanceof Error ? error.message : 'host request failed.');
        }
      }
      return failure('host request failed.');
    });
    writeQueue.current = task.then(() => undefined, () => undefined);
    return task;
  };

  const retry = (submittedPassword?: string) => {
    credentialRef.current = submittedPassword;
    setPassword('');
    setMessage('');
    setAttempt(value => value + 1);
  };
  const submitPassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (statusRef.current === 'connecting') return;
    retry(password);
  };

  return <HostConnectionContext.Provider value={{ status, settingsRevision, saveSettings }}>
    {children}
    {status === 'online' && message && <div role="status">{message}</div>}
    {loginVisible && status !== 'offline' && <Modal title="Connect to HaruQuantAI host" onClose={() => { connectionRef.current?.abort(); setAuthToken(null); updateStatus('offline'); setLoginVisible(false); }} footer={<Button form="host-login" type="submit" className="primary" disabled={status === 'connecting'}>{status === 'connecting' ? 'Connecting...' : 'Connect'}</Button>}>
      <form id="host-login" onSubmit={submitPassword}>
        <p role="alert">{message || 'Enter the host password to connect.'}</p>
        <Field label="Host password"><TextInput type="password" required maxLength={1024} disabled={status === 'connecting'} autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} /></Field>
      </form>
    </Modal>}
    {status === 'offline' && <div role="status">Host offline. Settings cannot be saved. {message} <Button onClick={() => retry()}>Retry connection</Button></div>}
  </HostConnectionContext.Provider>;
}
