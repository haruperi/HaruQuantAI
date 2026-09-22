import { describe, expect, it, vi } from 'vitest';
import { ApiClientError, HaruApiClient } from '../../../src/api/client';
import type { GraphDocument } from '../../../src/api/contracts.generated';

describe('HaruApiClient', () => {
  it('sends GET /health with X-Request-Id and returns success envelope data', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        api_version: '1.0.0',
        request_id: 'req-123',
        status: 'success',
        data: {
          status: 'ready',
          version: '1.0.0',
          services: { gateway: 'ready', catalog: 'ready', execution: 'ready' },
        },
      }),
    });

    const client = new HaruApiClient({ baseUrl: '/api/v1', fetchFn: mockFetch });
    const health = await client.getHealth();

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/health',
      expect.objectContaining({ method: 'GET' }),
    );
    expect(health.status).toBe('ready');
    expect(health.services.catalog).toBe('ready');
  });

  it('sends POST /graphs/validate with graph document payload', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        api_version: '1.0.0',
        request_id: 'req-val',
        status: 'success',
        data: {
          can_execute: true,
          issues: [],
          normalized_document: null,
        },
      }),
    });

    const doc: GraphDocument = {
      schema_version: 1,
      spec: { nodes: [], edges: [], designated_roots: [] },
    };

    const client = new HaruApiClient({ baseUrl: '/api/v1', fetchFn: mockFetch });
    const res = await client.validateGraph(doc);

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/graphs/validate',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ graph_document: doc }),
      }),
    );
    expect(res.can_execute).toBe(true);
  });

  it('throws ApiClientError when response status is error', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({
        api_version: '1.0.0',
        request_id: 'req-err',
        status: 'error',
        error: {
          code: 'INVALID_GRAPH',
          message: 'Malformed graph document',
          issues: [{ path: 'nodes', code: 'EMPTY', message: 'Nodes cannot be empty' }],
        },
      }),
    });

    const client = new HaruApiClient({ baseUrl: '/api/v1', fetchFn: mockFetch });
    await expect(
      client.validateGraph({
        schema_version: 1,
        spec: { nodes: [], edges: [], designated_roots: [] },
      }),
    ).rejects.toThrow(ApiClientError);
  });
});
