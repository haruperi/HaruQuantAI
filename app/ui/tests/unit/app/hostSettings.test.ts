import { describe, expect, it, vi } from 'vitest';
import { parseHostPreferences, readHostPreferences, watchSettingsChanges, writeHostPreferences } from '../../../src/app/hostSettings';
import { setAuthToken } from '../../../src/app/transport';

const preferences = { theme: 'light' as const, language: 'English', zoom: 1.2 };
const asFetch = (fn: unknown) => fn as unknown as typeof fetch;

describe('host shell preferences', () => {
  it('accepts only a complete valid UI projection', () => {
    expect(parseHostPreferences({})).toBeNull();
    expect(parseHostPreferences({ ui: preferences })).toEqual(preferences);
    expect(() => parseHostPreferences({ ui: { ...preferences, zoom: 3 } })).toThrow('zoom');
    expect(() => parseHostPreferences({ ui: { ...preferences, theme: 'blue' } })).toThrow('theme');
  });

  it('reads and writes the host settings envelope', async () => {
    const fetchFn = vi.fn().mockResolvedValue({
      ok: true, status: 200,
      json: async () => ({ status: 'success', data: { ui: preferences } }),
    });
    const config = { fetchFn: asFetch(fetchFn), baseUrl: '/api/v1' };
    expect(await readHostPreferences(config)).toEqual(preferences);
    expect(await writeHostPreferences(preferences, config)).toEqual(preferences);
    expect(fetchFn.mock.calls[1][0]).toBe('/api/v1/settings');
    expect((fetchFn.mock.calls[1][1] as RequestInit).method).toBe('PUT');
  });

  it('parses split SSE frames and refreshes on connection and change', async () => {
    setAuthToken('test-session');
    const controller = new AbortController();
    const changed = vi.fn().mockImplementation(async () => {
      if (changed.mock.calls.length === 2) controller.abort();
    });
    const stream = new ReadableStream<Uint8Array>({
      start(streamController) {
        streamController.enqueue(new TextEncoder().encode('data: {"channel":"settings.'));
        streamController.enqueue(new TextEncoder().encode('changed","data":{}}\n\n'));
      },
    });
    const fetchFn = vi.fn().mockResolvedValue({ ok: true, status: 200, body: stream });
    await watchSettingsChanges({
      signal: controller.signal,
      onChanged: changed,
      onConnection: vi.fn(),
      fetchFn: asFetch(fetchFn),
      baseUrl: '/api/v1',
    });
    expect(changed).toHaveBeenCalledTimes(2);
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/events?channels=settings.changed');
    expect((fetchFn.mock.calls[0][1] as RequestInit).headers).toMatchObject({ Authorization: 'Bearer test-session' });
    setAuthToken(null);
  });

  it('re-reads settings when a stream reconnects after a gap', async () => {
    setAuthToken('test-session');
    const controller = new AbortController();
    const changed = vi.fn().mockImplementation(async () => {
      if (changed.mock.calls.length === 2) controller.abort();
    });
    const fetchFn = vi.fn().mockImplementation(async () => ({
      ok: true, status: 200,
      body: new ReadableStream<Uint8Array>({ start(streamController) { streamController.close(); } }),
    }));
    await watchSettingsChanges({
      signal: controller.signal,
      onChanged: changed,
      onConnection: vi.fn(),
      fetchFn: asFetch(fetchFn),
      baseUrl: '/api/v1',
    });
    expect(fetchFn).toHaveBeenCalledTimes(2);
    expect(changed).toHaveBeenCalledTimes(2);
    setAuthToken(null);
  });
});
