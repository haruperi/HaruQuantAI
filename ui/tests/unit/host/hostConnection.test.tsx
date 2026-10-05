import { describe, expect, it, vi } from 'vitest';
import { connectHost, getSavedHostPassword, saveHostPassword, HOST_PASSWORD_KEY } from '../../../app/host/HostConnection';
import { getAuthToken, setAuthToken } from '../../../app/host/transport';
import { createInitialAppSettings } from '../../../app/host/globalSettings';
import { shellPreferences } from '../../../app/host/hostSettings';

const asFetch = (fn: unknown) => fn as unknown as typeof fetch;
const boot = { schema_version: 2, state: 'SERVER_READY', sequence: 1, stages: [] };
const bootStream = () => ({ ready: Promise.resolve(), close: vi.fn() });
const shell = { ...shellPreferences(createInitialAppSettings()), theme: 'light', zoom: 1.1 };

describe('host startup sequence', () => {
  it('logs in, reads settings, signals readiness, and uses the token', async () => {
    setAuthToken(null);
    const controller = new AbortController();
    const status = vi.fn().mockImplementation(value => { if (value === 'online') controller.abort(); });
    const fetchFn = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/auth/login')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { token: 'live-session' } }),
      };
      if (url.endsWith('/status')) return { ok: true, status: 200, json: async () => ({ status: 'success', data: { boot } }) };
      if (url.endsWith('/init-data')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { boot, first_run: false, settings: { revision: 1, values: { 'app.general': { theme: 'light', language: 'en', zoom: 1.1 } } } } }),
      };
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: { acknowledged: true } }) };
    });
    const onSettings = vi.fn();
    await connectHost({ bootStream, signal: controller.signal, fetchFn: asFetch(fetchFn), onStatus: status, onSettings, onError: vi.fn() });
    expect(fetchFn.mock.calls.map(call => call[0])).toEqual([
      '/api/v1/auth/login', '/api/v1/init-data', '/api/v1/app-loaded', '/api/v1/status',
    ]);
    expect(((fetchFn.mock.calls[2][1] as RequestInit).headers as Headers).get('Authorization')).toBe('Bearer live-session');
    expect(onSettings).toHaveBeenCalledWith({ revision: 1, preferences: shell });
    expect(status).toHaveBeenCalledWith('online');
    setAuthToken(null);
  });

  it('keeps readiness unsignalled when a locked host rejects login', async () => {
    setAuthToken(null);
    const fetchFn = vi.fn().mockResolvedValue({
      ok: false, status: 401,
      json: async () => ({ status: 'error', error: { code: 'UNAUTHORIZED', message: 'Invalid credentials' } }),
    });
    const status = vi.fn();
    await connectHost({ bootStream, signal: new AbortController().signal, password: 'incorrect', fetchFn: asFetch(fetchFn), onStatus: status, onSettings: vi.fn(), onError: vi.fn() });
    expect(fetchFn).toHaveBeenCalledTimes(1);
    expect(status).toHaveBeenCalledWith('locked');
    expect(getAuthToken()).toBeNull();
  });

  it('does not apply malformed host settings', async () => {
    setAuthToken(null);
    const controller = new AbortController();
    const onSettings = vi.fn();
    const onError = vi.fn();
    const onStatus = vi.fn();
    const fetchFn = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/auth/login')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { token: 'live-session' } }),
      };
      if (url.endsWith('/status')) return { ok: true, status: 200, json: async () => ({ status: 'success', data: { boot } }) };
      if (url.endsWith('/init-data')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { boot, first_run: false, settings: { revision: 1, values: { 'app.general': { theme: 'invalid' } } } } }),
      };
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: {} }) };
    });
    await connectHost({ bootStream,
      signal: controller.signal,
      fetchFn: asFetch(fetchFn),
      onStatus,
      onSettings,
      onError,
    });
    expect(onSettings).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith('Host theme is invalid');
    expect(onStatus).toHaveBeenCalledWith('offline');
    expect(onStatus).not.toHaveBeenCalledWith('online');
    setAuthToken(null);
  });

  it('auto-fills default and saved host password on login', async () => {
    setAuthToken(null);
    if (typeof localStorage !== 'undefined') localStorage.removeItem(HOST_PASSWORD_KEY);
    expect(getSavedHostPassword()).toBe('haruquantai');

    saveHostPassword('my-saved-pass'); // pragma: allowlist secret
    expect(getSavedHostPassword()).toBe('my-saved-pass');

    const controller = new AbortController();
    let loginBody: Record<string, unknown> | null = null;
    const fetchFn = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/auth/login')) {
        loginBody = JSON.parse(String(init?.body));
        return {
          ok: true, status: 200,
          json: async () => ({ status: 'success', data: { token: 'auto-session' } }),
        };
      }
      if (url.endsWith('/status')) return { ok: true, status: 200, json: async () => ({ status: 'success', data: { boot } }) };
      if (url.endsWith('/init-data')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { boot, first_run: false, settings: { revision: 1, values: { 'app.general': { theme: 'light', language: 'en', zoom: 1.1 } } } } }),
      };
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: { acknowledged: true } }) };
    });
    const status = vi.fn().mockImplementation(val => { if (val === 'online') controller.abort(); });
    await connectHost({ bootStream, signal: controller.signal, fetchFn: asFetch(fetchFn), onStatus: status, onSettings: vi.fn(), onError: vi.fn() });
    expect(loginBody).toEqual({ username: 'haruquantai', password: 'my-saved-pass' }); // pragma: allowlist secret
    expect(getAuthToken()).toBe('auto-session');
    if (typeof localStorage !== 'undefined') localStorage.removeItem(HOST_PASSWORD_KEY);
    setAuthToken(null);
  });

  it('reads and writes password and token with localStorage and sessionStorage', () => {
    const memory = new Map<string, string>();
    const storage = {
      getItem: (key: string) => memory.get(key) ?? null,
      setItem: (key: string, value: string) => { memory.set(key, value); },
      removeItem: (key: string) => { memory.delete(key); },
      clear: () => { memory.clear(); },
    };
    vi.stubGlobal('localStorage', storage);
    vi.stubGlobal('sessionStorage', storage);

    expect(getSavedHostPassword()).toBe('haruquantai');
    saveHostPassword('persisted-pass'); // pragma: allowlist secret
    expect(memory.get(HOST_PASSWORD_KEY)).toBe('persisted-pass');
    expect(getSavedHostPassword()).toBe('persisted-pass');

    setAuthToken('token-123');
    expect(memory.get('haruquantai.host.token.v1')).toBe('token-123');
    expect(getAuthToken()).toBe('token-123');
    setAuthToken(null);
    expect(memory.has('haruquantai.host.token.v1')).toBe(false);
    expect(getAuthToken()).toBeNull();

    vi.unstubAllGlobals();
  });
});


describe('host initialization compatibility', () => {
  it.each(['/init-data', '/status'])('rejects an incompatible %s document without becoming online', async incompatiblePath => {
    const onStatus = vi.fn();
    const onError = vi.fn();
    const fetchFn = vi.fn().mockImplementation(async (url: string) => {
      const snapshot = url.endsWith(incompatiblePath) ? { ...boot, schema_version: 1 } : boot;
      const data = url.endsWith('/auth/login') ? { token: 'test-session' }
        : url.endsWith('/init-data') ? { boot: snapshot, settings: { revision: 0, values: {} }, first_run: false }
        : { boot: snapshot };
      return { ok: true, status: 200, json: async () => ({ status: 'success', data }) };
    });
    await connectHost({ bootStream, signal: new AbortController().signal, fetchFn: asFetch(fetchFn), onStatus, onError, onSettings: vi.fn() });
    expect(onError).toHaveBeenCalledWith('Incompatible host boot schema; version 2 required');
    expect(onStatus).not.toHaveBeenCalledWith('online');
  });
});
