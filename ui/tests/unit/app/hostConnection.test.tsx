import { describe, expect, it, vi } from 'vitest';
import { connectHost } from '../../../src/app/HostConnection';
import { getAuthToken, setAuthToken } from '../../../src/app/transport';
import { createInitialAppSettings } from '../../../src/app/globalSettings';
import { shellPreferences } from '../../../src/app/hostSettings';

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
    await connectHost({ signal: controller.signal, fetchFn: asFetch(fetchFn), onStatus: status, onSettings, onError: vi.fn() });
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
