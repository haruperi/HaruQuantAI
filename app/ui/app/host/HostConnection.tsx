/** Browser-shell connection to the host session, readiness, and settings services. */

import { createContext, useContext, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { Button, Field, Modal, TextInput } from '../components/ui';
import { useAppStore } from './store';
import { parseHostPreferences, readHostPreferences, shellPreferences, watchSettingsChanges, writeHostPreferences, type HostSettingsSnapshot, type ShellPreferences } from './hostSettings';
import { BootScreen } from './BootScreen';
import { FirstRunDialog } from './FirstRunDialog';
import { connectBootStream, type BootSnapshot, type BootStream, type InitializationData, ApiClientError, createDomainClient, login, setAuthToken, subscribeAuthExpired } from './transport';

export type HostStatus = 'connecting' | 'online' | 'locked' | 'offline';
export type SaveSettingsResult = { ok: true } | { ok: false; message: string };

export const HOST_PASSWORD_KEY = 'haruquantai.host.password.v1'; // pragma: allowlist secret
export const DEFAULT_HOST_PASSWORD = 'haruquantai'; // pragma: allowlist secret

let memoryPassword = DEFAULT_HOST_PASSWORD;

export function getSavedHostPassword(): string {
  try {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(HOST_PASSWORD_KEY) ?? DEFAULT_HOST_PASSWORD;
    }
  } catch {
    /* Storage unavailable in some test/sandbox environments. */
  }
  return memoryPassword;
}

export function saveHostPassword(password: string): void {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(HOST_PASSWORD_KEY, password);
      return;
    }
  } catch {
    /* Storage unavailable */
  }
  memoryPassword = password;
}

export interface ConnectHostOptions {
  signal: AbortSignal;
  password?: string;
  fetchFn?: typeof fetch;
  onStatus: (status: HostStatus) => void;
  onSettings: (snapshot: HostSettingsSnapshot) => void;
  onCoreCount?: (cores: number) => void;
  onError: (message: string) => void;
  onBoot?: (snapshot: BootSnapshot) => void;
  onFirstRun?: (requirements: string[]) => void;
  bootStream?: typeof connectBootStream;
}

export async function connectHost(options: ConnectHostOptions): Promise<void> {
  const { signal, onStatus, onSettings, onError } = options;
  const config = { signal, fetchFn: options.fetchFn };
  const refresh = async () => {
    const snapshot = await readHostPreferences(config);
    if (!signal.aborted) onSettings(snapshot);
  };

  let stream: BootStream | undefined;
  let streamFailed = false;
  try {
    const password = options.password !== undefined ? options.password : getSavedHostPassword();
    await login({ username: 'haruquantai', ...(password ? { password } : {}) }, config);
    if (signal.aborted) return;
    stream = (options.bootStream ?? connectBootStream)(signal, options.onBoot ?? (() => {}), message => { streamFailed = true; if (!signal.aborted) { onStatus('offline'); onError(message); } });
    await stream.ready;
    const initial = await createDomainClient('', config).get<InitializationData>('/init-data');
    onSettings(parseHostPreferences(initial.settings));
    options.onBoot?.(initial.boot);
    if (initial.first_run) options.onFirstRun?.(initial.requirements);
    if (options.onCoreCount) {
      const status = await createDomainClient('', config).get<{ cpu_count?: number }>('/status');
      if (!signal.aborted && Number.isInteger(status.cpu_count) && (status.cpu_count ?? 0) > 0) options.onCoreCount(status.cpu_count!);
    }
    await createDomainClient('', config).post('/app-loaded', {});
    if (signal.aborted) return;
    const deadline = Date.now() + 30000;
    let ready = false;
    while (!signal.aborted && Date.now() < deadline) {
      const snapshot = await createDomainClient('', config).get<{ boot: BootSnapshot }>('/status');
      options.onBoot?.(snapshot.boot);
      if (['STANDBY', 'DEGRADED'].includes(snapshot.boot.state)) { ready = true; break; }
      if (snapshot.boot.state === 'FAILED') throw new Error('Required host initialization failed');
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (signal.aborted) return;
    if (streamFailed) throw new Error('Host progress connection failed; reconnect');
    if (!ready) throw new Error('Host readiness timed out');
    onStatus('online');
    await watchSettingsChanges({
      signal,
      fetchFn: options.fetchFn,
      onChanged: refresh,
      onConnection: connected => { if (!signal.aborted && !connected) onStatus('offline'); },
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
  } finally { stream?.close(); }
}

interface HostConnectionValue {
  status: HostStatus;
  saveSettings: (change: Partial<ShellPreferences>) => Promise<SaveSettingsResult>;
}

const HostConnectionContext = createContext<HostConnectionValue | null>(null);

export function useHostConnection(): HostConnectionValue {
  const value = useContext(HostConnectionContext);
  if (!value) throw new Error('HostConnectionProvider is required');
  return value;
}

export function HostConnectionProvider({ children }: { children: ReactNode }) {
  const [boot, setBoot] = useState<BootSnapshot | null>(null);
  const [requirements, setRequirements] = useState<string[] | null>(null);
  const [status, setStatus] = useState<HostStatus>('connecting');
  const statusRef = useRef<HostStatus>('connecting');
  const [message, setMessage] = useState('');
  const [password, setPassword] = useState(getSavedHostPassword);
  const credentialRef = useRef<string | undefined>(getSavedHostPassword());
  const [attempt, setAttempt] = useState(0);
  const writeQueue = useRef<Promise<void>>(Promise.resolve());
  const revisionRef = useRef<number | null>(null);
  const preferencesRef = useRef<ShellPreferences | null>(null);
  const coreCountRef = useRef<number | null>(null);

  const applySettings = (snapshot: HostSettingsSnapshot) => {
    if (revisionRef.current !== null && snapshot.revision < revisionRef.current) return;
    revisionRef.current = snapshot.revision;
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

  const updateStatus = (next: HostStatus) => { statusRef.current = next; setStatus(next); };

  useEffect(() => subscribeAuthExpired(() => {
    updateStatus('locked');
    setMessage('The host session expired. Reconnect to continue.');
  }), []);

  useEffect(() => {
    const controller = new AbortController();
    const credential = credentialRef.current ?? getSavedHostPassword();
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
      onBoot: setBoot,
      onFirstRun: setRequirements,
      onError: error => setMessage(error),
    });
    return () => { controller.abort(); };
  }, [attempt]);

  const recoverSession = async (): Promise<boolean> => {
    revisionRef.current = null;
    preferencesRef.current = null;
    const currentPassword = getSavedHostPassword();
    try {
      await login({ username: 'haruquantai', ...(currentPassword ? { password: currentPassword } : {}) });
      applySettings(await readHostPreferences());
      updateStatus('online');
      setMessage('');
      return true;
    } catch (error) {
      const locked = error instanceof ApiClientError && error.status === 401;
      updateStatus(locked ? 'locked' : 'offline');
      setMessage(error instanceof Error ? error.message : 'Host reconnection failed');
      return false;
    }
  };

  const saveSettings = (change: Partial<ShellPreferences>): Promise<SaveSettingsResult> => {
    const task = writeQueue.current.then(async (): Promise<SaveSettingsResult> => {
      const failure = (reason: string): SaveSettingsResult => {
        const message = `Settings were not saved: ${reason}`;
        useAppStore.getState().notify(message);
        return { ok: false, message };
      };
      if (statusRef.current !== 'online' || revisionRef.current === null || preferencesRef.current === null) {
        if (!await recoverSession()) return failure('host session unavailable. Reconnect and retry.');
      }
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          const previous = preferencesRef.current!;
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
    const nextPassword = submittedPassword ?? getSavedHostPassword();
    if (submittedPassword !== undefined) {
      saveHostPassword(submittedPassword);
    }
    credentialRef.current = nextPassword;
    setPassword(nextPassword);
    setMessage('');
    setAttempt(value => value + 1);
  };
  const submitPassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    retry(password);
  };

  return <HostConnectionContext.Provider value={{ status, saveSettings }}>
    {children}
    {status === 'connecting' && boot && <BootScreen snapshot={boot} />}
    {status === 'online' && requirements && <FirstRunDialog requirements={requirements} onClose={() => setRequirements(null)} />}
    {status === 'locked' && <Modal title="Connect to HaruQuantAI host" onClose={() => updateStatus('offline')} footer={<Button form="host-login" type="submit" className="primary">Connect</Button>}>
      <form id="host-login" onSubmit={submitPassword}>
        <p role="alert">{message || 'Enter the host password to connect.'}</p>
        <Field label="Host password"><TextInput type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} /></Field>
      </form>
    </Modal>}
    {status === 'offline' && <div role="status">Host offline. Settings cannot be saved. {message} <Button onClick={() => retry()}>Retry connection</Button></div>}
  </HostConnectionContext.Provider>;
}
