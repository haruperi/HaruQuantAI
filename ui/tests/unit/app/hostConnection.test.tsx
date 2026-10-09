import { describe, expect, it, vi } from 'vitest';
import { connectHost } from '../../../app/host/HostConnection';
import { getAuthToken, setAuthToken } from '../../../app/host/transport';
import { createInitialAppSettings } from '../../../app/host/globalSettings';
import { shellPreferences } from '../../../app/host/hostSettings';

const asFetch = (fn: unknown) => fn as unknown as typeof fetch;
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
      if (url.endsWith('/settings')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { revision: 1, values: { 'app.general': { theme: 'light', language: 'en', zoom: 1.1 } } } }),
      };
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: { acknowledged: true } }) };
    });
    const onSettings = vi.fn();
    await connectHost({ signal: controller.signal, password: 'test-password', fetchFn: asFetch(fetchFn), onStatus: status, onSettings, onError: vi.fn() });
    expect(fetchFn.mock.calls.map(call => call[0])).toEqual([
      '/api/v1/auth/login', '/api/v1/settings', '/api/v1/app-loaded',
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
    await connectHost({ signal: new AbortController().signal, password: 'incorrect', fetchFn: asFetch(fetchFn), onStatus: status, onSettings: vi.fn(), onError: vi.fn() });
    expect(fetchFn).toHaveBeenCalledTimes(1);
    expect((fetchFn.mock.calls[0][1] as RequestInit).body).toBe(JSON.stringify({ password: 'incorrect' }));
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
      if (url.endsWith('/settings')) return {
        ok: true, status: 200,
        json: async () => ({ status: 'success', data: { revision: 1, values: { 'app.general': { theme: 'invalid' } } } }),
      };
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: {} }) };
    });
    await connectHost({
      signal: controller.signal,
      password: 'test-password',
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
});


it('requires password re-entry when the authenticated stream expires', async () => {
  setAuthToken(null);
  const statuses: string[] = [];
  const fetchFn = vi.fn().mockImplementation(async (url: string) => {
    if (url.endsWith('/auth/login')) return { ok: true, status: 200, json: async () => ({ status: 'success', data: { token: 'new-session' } }) };
    if (url.endsWith('/settings')) return { ok: true, status: 200, json: async () => ({ status: 'success', data: { revision: 1, values: {} } }) };
    if (url.includes('/events?')) return { ok: false, status: 401 };
    return { ok: true, status: 200, json: async () => ({ status: 'success', data: {} }) };
  });
  await connectHost({ signal: new AbortController().signal, password: 'test-password', fetchFn: asFetch(fetchFn), onStatus: value => statuses.push(value), onSettings: vi.fn(), onError: vi.fn() });
  expect(statuses).toEqual(['online', 'locked']);
  expect(fetchFn.mock.calls.filter(call => call[0].endsWith('/auth/login'))).toHaveLength(1);
  expect(getAuthToken()).toBeNull();
});


it('clears submitted credentials after the login attempt completes', async () => {
  const options = { signal: new AbortController().signal, password: 'test-password', fetchFn: asFetch(vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ status: 'error', error: { code: 'INVALID_CREDENTIALS', message: 'Invalid' } }) })), onStatus: vi.fn(), onSettings: vi.fn(), onError: vi.fn() };
  await connectHost(options);
  expect(options.password).toBeUndefined();
});


it('validates an existing session instead of posting another login', async () => {
  setAuthToken('existing-session');
  const controller = new AbortController();
  const fetchFn = vi.fn().mockImplementation(async (url: string) => ({ ok: true, status: 200, json: async () => ({ status: 'success', data: url.endsWith('/settings') ? { revision: 1, values: {} } : {} }) }));
  await connectHost({ signal: controller.signal, fetchFn: asFetch(fetchFn), onStatus: status => { if (status === 'online') controller.abort(); }, onSettings: vi.fn(), onError: vi.fn() });
  expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/sessions/me');
  expect(fetchFn.mock.calls.some(call => call[0].endsWith('/auth/login'))).toBe(false);
  expect(getAuthToken()).toBe('existing-session');
  setAuthToken(null);
});

it('keeps a valid session available after a transient network failure', async () => {
  setAuthToken('existing-session');
  const status = vi.fn();
  await connectHost({ signal: new AbortController().signal, fetchFn: asFetch(vi.fn().mockRejectedValue(new TypeError('Network unavailable'))), onStatus: status, onSettings: vi.fn(), onError: vi.fn() });
  expect(status).toHaveBeenCalledWith('offline');
  expect(getAuthToken()).toBe('existing-session');
  setAuthToken(null);
});

it('discards a saved session rejected by the host and requires a password', async () => {
  setAuthToken('revoked-session');
  const fetchFn = vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ status: 'error', error: { code: 'INVALID_SESSION', message: 'Revoked' } }) });
  const status = vi.fn();
  await connectHost({ signal: new AbortController().signal, fetchFn: asFetch(fetchFn), onStatus: status, onSettings: vi.fn(), onError: vi.fn() });
  expect(status).toHaveBeenCalledWith('locked');
  expect(getAuthToken()).toBeNull();
  expect(fetchFn).toHaveBeenCalledTimes(1);
});
