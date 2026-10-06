import { describe, expect, it, vi, beforeEach } from 'vitest';
import {
  ApiClientError,
  createDomainClient,
  getAuthToken,
  login,
  setAuthToken,
  subscribeAuthExpired,
} from '../../../src/app/transport';

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
    const result = await login({ username: 'operator', password: 'secret' }, { baseUrl: '/api/v1', fetchFn: asFetch(mockFetch) });

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'operator', password: 'secret' }),
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
