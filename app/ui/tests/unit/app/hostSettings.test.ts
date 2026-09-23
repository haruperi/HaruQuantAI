import { describe, expect, it, vi } from 'vitest';
import { parseHostPreferences, readHostPreferences, shellPreferences, watchSettingsChanges, writeHostPreferences } from '../../../src/app/hostSettings';
import { createInitialAppSettings } from '../../../src/app/globalSettings';
import { setAuthToken } from '../../../src/app/transport';

const shell = { ...shellPreferences(createInitialAppSettings()), theme: 'light' as const, zoom: 1.2 };
const snapshot = { revision: 1, values: { 'app.general': { theme: 'light', language: 'en', zoom: 1.2 } } };
const asFetch = (fn: unknown) => fn as unknown as typeof fetch;

describe('host shell preferences', () => {
  it('translates scoped host records without accepting invalid values', () => {
    expect(parseHostPreferences({ revision: 0, values: {} })).toEqual({ revision: 0, preferences: shellPreferences(createInitialAppSettings()) });
    expect(parseHostPreferences(snapshot)).toEqual({ revision: 1, preferences: shell });
    expect(() => parseHostPreferences({ revision: 1, values: { 'app.general': { zoom: 3 } } })).toThrow('zoom');
    expect(() => parseHostPreferences({ revision: 1, values: { 'app.general': { theme: 'blue' } } })).toThrow('theme');
    expect(() => parseHostPreferences({ revision: 1, values: { 'config.memory': { memory_limit_gb: 'huge' } } })).toThrow('memory_limit_gb');
    expect(parseHostPreferences({ revision: 1, values: { 'config.databanks': { databank_sync_interval_mins: 10 } } }).preferences.configuration.databankSyncInterval).toBe('Every 10 minutes');
  });

  it('reads and writes the host settings envelope', async () => {
    const fetchFn = vi.fn().mockResolvedValue({
      ok: true, status: 200,
      json: async () => ({ status: 'success', data: snapshot }),
    });
    const config = { fetchFn: asFetch(fetchFn), baseUrl: '/api/v1' };
    expect(await readHostPreferences(config)).toEqual({ revision: 1, preferences: shell });
    expect(await writeHostPreferences(shell, shellPreferences(createInitialAppSettings()), 1, config)).toEqual({ revision: 1, preferences: shell, wrote: true });
    expect(fetchFn.mock.calls[1][0]).toBe('/api/v1/settings');
    expect((fetchFn.mock.calls[1][1] as RequestInit).method).toBe('PUT');
    expect(JSON.parse((fetchFn.mock.calls[1][1] as RequestInit).body as string)).toEqual({ expected_revision: 1, changes: { 'app.general': { theme: 'light', zoom: 1.2 }, 'config.global': { theme: 'light' } } });
  });

  it('writes edited fields to their scoped records', async () => {
    const before = shellPreferences(createInitialAppSettings());
    const next = {
      ...before,
      theme: 'light' as const, language: 'German', zoom: 1.1,
      configuration: { ...before.configuration, soundsOff: true, customCores: 4, computePipsMetrics: true, memoryGb: 12, databankSyncInterval: 'Every 10 minutes' as const, dontStoreOptimization3d: false, gpuAccelerated: false },
      smtp: { ...before.smtp, server: 'mail.example.test' },
      remoteAccess: { ...before.remoteAccess, allow: true },
    };
    const fetchFn = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ status: 'success', data: snapshot }) });
    await writeHostPreferences(next, before, 1, { fetchFn: asFetch(fetchFn), baseUrl: '/api/v1' });
    const body = JSON.parse((fetchFn.mock.calls[0][1] as RequestInit).body as string);
    expect(body.changes).toEqual({
      'config.cpu': { custom_cores: 4 },
      'config.global': { theme: 'light', language: 'de', sounds_off: true },
      'config.performance': { compute_pips_metrics: true },
      'config.memory': { memory_limit_gb: 12 },
      'config.databanks': { databank_sync_interval_mins: 10 },
      'config.optimizations': { dont_store_op_3d_charts_data: false },
      'config.troubleshooting': { gpu_accelerated: false },
      'app.general': { theme: 'light', language: 'de', zoom: 1.1, gpu_accelerated: false },
      'notify.email': { smtp_server: 'mail.example.test' },
      'connect.remote': { allow: true },
    });
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
