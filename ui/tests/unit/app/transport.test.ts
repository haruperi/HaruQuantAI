import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import {
  ApiClientError,
  createDomainClient,
  getAuthToken,
  login,
  setAuthToken,
  subscribeAuthExpired,
  restoreSavedSession,
  getSessionPersistenceWarning,
} from '../../../app/host/transport';

const asFetch = (fn: unknown) => fn as unknown as typeof fetch;

const okFetch = (data: unknown) =>
  vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ status: 'success', data }) });

describe('UI host transport', () => {
  beforeEach(() => {
    setAuthToken(null);
  });

  it('joins base url, route base, and path and returns envelope data', async () => {
    const mockFetch = okFetch({ ready: true });
    const client = createDomainClient('/executions', { baseUrl: '/api/v1', fetchFn: asFetch(mockFetch) });

    const result = await client.get<{ ready: boolean }>('/health');

    expect(mockFetch).toHaveBeenCalledWith('/api/v1/executions/health', expect.objectContaining({ method: 'GET' }));
    expect(result).toEqual({ ready: true });
  });

  it('sends a request id and JSON content type on post', async () => {
    const mockFetch = okFetch({});
    const client = createDomainClient('/executions', { baseUrl: '', fetchFn: asFetch(mockFetch) });

    await client.post('/evaluate', { trial_id: 'a' });

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/executions/evaluate');
    const headers = init.headers as Headers;
    expect(headers.get('X-Request-Id')).toMatch(/^req-/);
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('attaches Bearer token from global auth token store', async () => {
    setAuthToken('test-token-123');
    expect(getAuthToken()).toBe('test-token-123');

    const mockFetch = okFetch({ data: 'ok' });
    const client = createDomainClient('/executions', { baseUrl: '/api/v1', fetchFn: asFetch(mockFetch) });

    await client.get('/status');

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer test-token-123');
  });

  it('allows config-level token string and factory override', async () => {
    setAuthToken('global-token');
    const mockFetch = okFetch({});

    const clientString = createDomainClient('/custom', {
      baseUrl: '',
      authToken: 'client-token',
      fetchFn: asFetch(mockFetch),
    });
    await clientString.get('/a');
    let [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Headers).get('Authorization')).toBe('Bearer client-token');

    const clientFn = createDomainClient('/custom', {
      baseUrl: '',
      authToken: () => 'dynamic-token',
      fetchFn: asFetch(mockFetch),
    });
    await clientFn.get('/b');
    [, init] = mockFetch.mock.calls[1] as [string, RequestInit];
    expect((init.headers as Headers).get('Authorization')).toBe('Bearer dynamic-token');
  });

  it('login helper performs authentication and sets the active token', async () => {
    const mockFetch = okFetch({ token: 'jwt-session-xyz' });
    const result = await login({ password: 'secret' }, { baseUrl: '/api/v1', fetchFn: asFetch(mockFetch) });

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ password: 'secret' }),
      }),
    );
    expect(result.token).toBe('jwt-session-xyz');
    expect(getAuthToken()).toBe('jwt-session-xyz');
  });

  it('supports PUT and clears the session on a protected 401', async () => {
    setAuthToken('expired');
    const expired = vi.fn();
    const unsubscribe = subscribeAuthExpired(expired);
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false, status: 401,
      json: async () => ({ status: 'error', error: { code: 'UNAUTHORIZED', message: 'Expired' } }),
    });
    const client = createDomainClient('', { baseUrl: '/api/v1', fetchFn: asFetch(mockFetch) });
    await expect(client.put('/settings', { ui: {} })).rejects.toMatchObject({ status: 401 });
    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/v1/settings');
    expect(init.method).toBe('PUT');
    expect(getAuthToken()).toBeNull();
    expect(expired).toHaveBeenCalledOnce();
    unsubscribe();
  });

  it('maps error envelopes to ApiClientError with code and issues', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        status: 'error',
        error: {
          code: 'SCHEMA_INVALID',
          message: 'Graph document rejected',
          issues: [{ path: '$.nodes', code: 'required', message: 'missing nodes' }],
        },
      }),
    });
    const client = createDomainClient('/executions', { baseUrl: '', fetchFn: asFetch(mockFetch) });

    await expect(client.post('/evaluate', {})).rejects.toMatchObject({
      name: 'ApiClientError',
      code: 'SCHEMA_INVALID',
      issues: [{ path: '$.nodes' }],
    });
  });

  it('fails closed with MALFORMED_RESPONSE on non-JSON bodies', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => {
        throw new Error('not JSON');
      },
    });
    const client = createDomainClient('/executions', { baseUrl: '', fetchFn: asFetch(mockFetch) });

    const rejection = expect(client.get('/health')).rejects;
    await rejection.toMatchObject({ code: 'MALFORMED_RESPONSE' });
    await rejection.toBeInstanceOf(ApiClientError);
  });
});


describe('login response ownership', () => {
  it('rejects a response without a valid token', async () => {
    setAuthToken('old-session');
    await expect(login({ password: 'test-password' }, { fetchFn: asFetch(okFetch({ token: '' })) })).rejects.toMatchObject({ code: 'MALFORMED_RESPONSE' });
    expect(getAuthToken()).toBeNull();
  });

  it('never installs a token from a canceled login response', async () => {
    setAuthToken(null);
    const controller = new AbortController();
    const fetchFn = vi.fn().mockImplementation(async () => {
      controller.abort();
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: { token: 'obsolete-token' } }) };
    });
    await expect(login({ password: 'test-password' }, { signal: controller.signal, fetchFn: asFetch(fetchFn) })).rejects.toMatchObject({ name: 'AbortError' });
    expect(getAuthToken()).toBeNull();
  });
});


describe('saved browser sessions', () => {
  let values: Map<string, string>;
  let storage: Storage;
  beforeEach(() => {
    values = new Map();
    storage = { get length() { return values.size; }, clear: () => values.clear(), getItem: key => values.get(key) ?? null, setItem: (key, value) => { values.set(key, value); }, removeItem: key => { values.delete(key); }, key: index => [...values.keys()][index] ?? null };
    vi.stubGlobal('window', { location: { origin: 'http://localhost:4173', port: '4173', hostname: 'localhost' }, localStorage: storage });
    setAuthToken(null);
  });
  afterEach(() => { setAuthToken(null); vi.unstubAllGlobals(); vi.useRealTimers(); });

  it('retains only the token and server expiry and restores them until 24 hours elapse', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-10-09T00:00:00Z'));
    const expires_at = '2026-10-10T00:00:00Z';
    await login({ password: 'never-store-this-password' }, { fetchFn: asFetch(okFetch({ token: 'retained-token', expires_at })) });
    const serialized = [...values.values()][0];
    expect(JSON.parse(serialized)).toEqual({ version: 1, token: 'retained-token', expires_at });
    expect(serialized).not.toContain('never-store-this-password');
    setAuthToken('different-memory-token');
    vi.setSystemTime(new Date('2026-10-09T23:59:59Z'));
    expect(restoreSavedSession()).toBe(true);
    expect(getAuthToken()).toBe('retained-token');
    vi.setSystemTime(new Date(expires_at));
    expect(restoreSavedSession()).toBe(false);
    expect(getAuthToken()).toBeNull();
    expect(values.size).toBe(0);
  });

  it('does not restore a session saved for another host', async () => {
    await login({ password: 'test-password' }, { baseUrl: 'http://localhost:8000/api/v1', fetchFn: asFetch(okFetch({ token: 'host-a', expires_at: new Date(Date.now() + 86400000).toISOString() })) });
    expect(restoreSavedSession('http://localhost:8001/api/v1')).toBe(false);
    expect(restoreSavedSession('http://localhost:8000/api/v1')).toBe(true);
  });

  it('rejects malformed records and removes revoked tokens after HTTP 401', async () => {
    values.set('haruquantai.host-session.v1:http://localhost:4173/api/v1', 'broken JSON');
    expect(restoreSavedSession()).toBe(false);
    expect(values.size).toBe(0);
    await login({ password: 'test-password' }, { fetchFn: asFetch(okFetch({ token: 'revoked', expires_at: new Date(Date.now() + 86400000).toISOString() })) });
    const client = createDomainClient('', { fetchFn: asFetch(vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ status: 'error', error: { code: 'UNAUTHORIZED', message: 'Revoked' } }) })) });
    await expect(client.get('/sessions/me')).rejects.toMatchObject({ status: 401 });
    expect(values.size).toBe(0);
    expect(getAuthToken()).toBeNull();
  });

  it('does not persist login responses without a valid server expiry', async () => {
    await expect(login({ password: 'test-password' }, { fetchFn: asFetch(okFetch({ token: 'bad-expiry', expires_at: 'invalid' })) })).rejects.toMatchObject({ code: 'MALFORMED_RESPONSE' });
    expect(values.size).toBe(0);
    await login({ password: 'test-password' }, { fetchFn: asFetch(okFetch({ token: 'transient-fixture' })) });
    expect(values.size).toBe(0);
  });

  it('reports unavailable browser storage without breaking authenticated memory access', async () => {
    vi.spyOn(storage, 'setItem').mockImplementation(() => { throw new Error('Storage blocked'); });
    await login({ password: 'test-password' }, { fetchFn: asFetch(okFetch({ token: 'memory-token', expires_at: new Date(Date.now() + 86400000).toISOString() })) });
    expect(getAuthToken()).toBe('memory-token');
    expect(getSessionPersistenceWarning()).toContain('Browser storage is unavailable');
  });
});
