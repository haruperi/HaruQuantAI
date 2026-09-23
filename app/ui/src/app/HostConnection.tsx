/** Browser-shell connection to the host session, readiness, and settings services. */

import { createContext, useContext, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { Button, Field, Modal, TextInput } from '../components/ui';
import { useAppStore } from './store';
import { readHostPreferences, shellPreferences, watchSettingsChanges, writeHostPreferences, type ShellPreferences } from './hostSettings';
import { ApiClientError, createDomainClient, login, setAuthToken, subscribeAuthExpired } from './transport';

export type HostStatus = 'connecting' | 'online' | 'locked' | 'offline';

export interface ConnectHostOptions {
  signal: AbortSignal;
  password?: string;
  fetchFn?: typeof fetch;
  onStatus: (status: HostStatus) => void;
  onPreferences: (preferences: ShellPreferences) => void;
  onError: (message: string) => void;
}

export async function connectHost(options: ConnectHostOptions): Promise<void> {
  const { signal, onStatus, onPreferences, onError } = options;
  const config = { signal, fetchFn: options.fetchFn };
  const refresh = async () => {
    try {
      const preferences = await readHostPreferences(config);
      if (!signal.aborted && preferences) onPreferences(preferences);
    } catch (error) {
      if (signal.aborted) return;
      if (error instanceof ApiClientError && error.status === 401) throw error;
      onError(error instanceof Error ? error.message : 'Cannot read host settings');
    }
  };

  try {
    await login({ username: 'operator', ...(options.password ? { password: options.password } : {}) }, config);
    if (signal.aborted) return;
    await refresh();
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
    setAuthToken(null);
    if (error instanceof ApiClientError && error.status === 401) {
      onStatus('locked');
      onError('The host requires a valid password or a new session.');
    } else {
      onStatus('offline');
      onError(error instanceof Error ? error.message : 'Host connection failed');
    }
  }
}

interface HostConnectionValue {
  status: HostStatus;
  savePreference: (change: Partial<ShellPreferences>) => Promise<void>;
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
  const credentialRef = useRef<string | undefined>(undefined);
  const [attempt, setAttempt] = useState(0);
  const writeQueue = useRef<Promise<void>>(Promise.resolve());

  const updateStatus = (next: HostStatus) => { statusRef.current = next; setStatus(next); };

  useEffect(() => subscribeAuthExpired(() => {
    updateStatus('locked');
    setMessage('The host session expired. Reconnect to continue.');
  }), []);

  useEffect(() => {
    const controller = new AbortController();
    const credential = credentialRef.current;
    credentialRef.current = undefined;
    updateStatus('connecting');
    void connectHost({
      signal: controller.signal,
      password: credential,
      onStatus: updateStatus,
      onPreferences: preferences => useAppStore.getState().updateSettings(preferences),
      onError: error => setMessage(error),
    });
    return () => { controller.abort(); setAuthToken(null); };
  }, [attempt]);

  const savePreference = (change: Partial<ShellPreferences>): Promise<void> => {
    const task = writeQueue.current.then(async () => {
      const store = useAppStore.getState();
      const next = { ...shellPreferences(store.settings), ...change };
      if (statusRef.current !== 'online') {
        store.updateSettings(next);
        store.notify('Preference changed locally; host is not connected.');
        return;
      }
      try {
        const saved = await writeHostPreferences(next);
        useAppStore.getState().updateSettings(saved);
        useAppStore.getState().notify('Preference saved to host.');
      } catch (error) {
        if (error instanceof ApiClientError && error.status === 401) {
          setAuthToken(null);
          updateStatus('locked');
        }
        useAppStore.getState().notify('Preference was not saved to host.');
      }
    });
    writeQueue.current = task.catch(() => undefined);
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
    retry(password);
  };

  return <HostConnectionContext.Provider value={{ status, savePreference }}>
    {children}
    {status === 'locked' && <Modal title="Connect to HaruQuantAI host" onClose={() => updateStatus('offline')} footer={<Button form="host-login" type="submit" className="primary">Connect</Button>}>
      <form id="host-login" onSubmit={submitPassword}>
        <p role="alert">{message || 'Enter the host password to connect.'}</p>
        <Field label="Host password"><TextInput type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} /></Field>
      </form>
    </Modal>}
    {status === 'offline' && <div role="status">Host offline. Research views and preference changes are local only. <Button onClick={() => retry()}>Retry connection</Button></div>}
  </HostConnectionContext.Provider>;
}
