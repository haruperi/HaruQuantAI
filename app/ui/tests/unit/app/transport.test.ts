import { describe, expect, it, vi } from 'vitest';
import { ApiClientError, createDomainClient } from '../../../src/app/transport';

const asFetch = (fn: unknown) => fn as unknown as typeof fetch;

const okFetch = (data: unknown) =>
  vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ status: 'success', data }) });

describe('UI host transport', () => {
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
