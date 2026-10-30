import { describe, expect, it, vi } from 'vitest';

async function setup(statuses: string[]) {
  vi.resetModules();
  const memory = new Map<string, string>();
  vi.stubGlobal('localStorage', { getItem: (key: string) => memory.get(key) ?? null, setItem: (key: string, value: string) => memory.set(key, value) });
  const fetch = vi.fn(async (url: string, options?: RequestInit) => {
    if (url.endsWith('/home/datasets')) return new Response(JSON.stringify({ success: true, status: 'success', data: [] }));
    const status = statuses.shift() ?? 'RUNNING';
    return new Response(JSON.stringify({ success: true, status: 'success', data: { job_id: 'source-job', status, progress: status === 'COMPLETED' ? 100 : 25, message: status } }));
  });
  vi.stubGlobal('fetch', fetch);
  const { useHistoricalSources } = await import('../../../../workspaces/data_manager/plugins/Common/historicalSourceStore');
  return { store: useHistoricalSources, fetch, memory };
}

const records = [{ id: 'coinbase:BTC-USD:M1', source: 'coinbase', symbol: 'BTC-USD', timeframe: 'M1' }];

describe('backend-owned historical source downloads', () => {
  it('uses persisted IDs and backend progress, then refreshes the database catalog', async () => {
    const { store, fetch } = await setup(['RUNNING', 'PAUSED', 'RUNNING', 'COMPLETED']);
    await store.getState().start(records, '2025-01-01', '2025-01-02', true);
    expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toMatchObject({ provider: 'market', targets: [{ id: records[0].id }], overwrite: true });
    expect(store.getState().job?.progress).toBe(25);
    await store.getState().action('pause');
    expect(store.getState().job?.status).toBe('PAUSED');
    await store.getState().action('resume');
    await store.getState().poll();
    expect(store.getState().job?.status).toBe('COMPLETED');
    expect(store.getState().job?.targets).toEqual([records[0].id]);
    expect(fetch.mock.calls.some(([url]) => url.endsWith('/home/datasets'))).toBe(true);
  });

  it('does not fabricate completion or unlock a still-running backend job on a transport error', async () => {
    const { store, fetch } = await setup(['RUNNING']);
    await store.getState().start(records, '2025-01-01', '2025-01-02', false);
    fetch.mockRejectedValueOnce(new Error('Backend unavailable'));
    await store.getState().poll();
    expect(store.getState().job?.status).toBe('RUNNING');
    expect(store.getState().error).toContain('Backend unavailable');
    await expect(store.getState().start(records, '2025-01-01', '2025-01-02', false)).rejects.toThrow('Finish or stop');
  });

  it('recovers terminal state and accepts another job after a backend interruption', async () => {
    const { store, memory } = await setup(['RUNNING', 'INTERRUPTED', 'RUNNING']);
    await store.getState().start(records, '2025-01-01', '2025-01-02', false);
    await store.getState().poll();
    expect(store.getState().job?.status).toBe('INTERRUPTED');
    expect(JSON.parse(memory.get('haruquantai-historical-job-v1')!).status).toBe('INTERRUPTED');
    await store.getState().start(records, '2025-01-01', '2025-01-02', false);
    expect(store.getState().job?.status).toBe('RUNNING');
  });
});
