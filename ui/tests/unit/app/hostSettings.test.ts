import { describe, expect, it, vi } from 'vitest';
import { parseHostPreferences, parseSettingsCatalogue, readHostPreferences, shellPreferences, watchSettingsChanges, writeHostPreferences } from '../../../app/host/hostSettings';
import { createInitialAppSettings } from '../../../app/host/globalSettings';
import { setAuthToken } from '../../../app/host/transport';

const shell = { ...shellPreferences(createInitialAppSettings()), theme: 'light' as const, zoom: 1.2 };
const snapshot = { revision: 1, values: { 'app.general': { theme: 'light', language: 'en', zoom: 1.2 } } };
const asFetch = (fn: unknown) => fn as unknown as typeof fetch;

describe('host shell preferences', () => {
  it('round-trips every Configuration preference through scoped host records', async () => {
    const previous = shellPreferences(createInitialAppSettings());
    const values: Record<string, Record<string, unknown>> = {};
    const fetchFn = vi.fn(async (_url: string, init: RequestInit) => {
      const body = JSON.parse(init.body as string) as { changes: typeof values };
      Object.assign(values, body.changes);
      return { ok: true, status: 200, json: async () => ({ status: 'success', data: { revision: 1, values } }) };
    });
    const configuration = {
      ...previous.configuration,
      soundsOff: true, rememberFileChooser: false, showControlOrders: true,
      headerCustomText: 'Reference header', footerCustomText: 'Reference footer',
      defaultResult: 'main' as const, dataFrameGuard: 'stop' as const,
      coreUsage: 'custom' as const, customCores: 3, highPriority: true,
      computePipsMetrics: true, computePercentMetrics: true, computeSeparateMetrics: false,
      garbageCollector: 'g1' as const, automaticMemory: true, memoryGb: 6,
      dontStorePendingOrders: false, memoryCleanup: true, cleanupInterval: 'never' as const,
      databankSyncInterval: 'Every hour' as const, syncDatabanksAfterTask: false,
      storeChartData: true, dontStoreOptimization3d: false, gpuAccelerated: false,
      memoryProtection: false, debugLevel: true,
    };
    const saved = await writeHostPreferences({ ...previous, configuration }, previous, 0, { fetchFn: asFetch(fetchFn), baseUrl: '/api/v1' });
    expect(saved.preferences.configuration).toEqual(configuration);
    expect(values['config.global'].data_frame_guard).toBe('stop');
    expect(values['config.memory'].cleanup_interval_mins).toBe(0);
    expect(values['config.databanks'].databank_sync_interval_mins).toBe(60);
    expect(values['config.cpu'].thread_affinity).toBeUndefined();
    for (const data_frame_guard of ['warn', 'stop', 'off']) {
      expect(parseHostPreferences({ revision: 1, values: { 'config.global': { data_frame_guard } } }).preferences.configuration.dataFrameGuard).toBe(data_frame_guard);
    }
    expect(() => parseHostPreferences({ revision: 1, values: { 'config.global': { data_frame_guard: 'guess' } } })).toThrow('data frame guard');
    expect(() => parseHostPreferences({ revision: 1, values: { 'config.memory': { cleanup_interval_mins: 7 } } })).toThrow('cleanup interval');
    const hidden = parseHostPreferences({ revision: 1, values: { 'config.cpu': { thread_affinity: true } } }).preferences;
    await writeHostPreferences({ ...hidden, configuration: { ...hidden.configuration, headerCustomText: 'Changed' } }, hidden, 1, { fetchFn: asFetch(fetchFn), baseUrl: '/api/v1' });
    const changed = JSON.parse(fetchFn.mock.calls[1][1].body as string).changes;
    expect(changed).toEqual({ 'app.general': { header_custom_text: 'Changed' } });
  });

  it('translates scoped host records without accepting invalid values', () => {
    expect(parseHostPreferences({ revision: 0, values: {} })).toEqual({ revision: 0, preferences: shellPreferences(createInitialAppSettings()) });
    expect(parseHostPreferences(snapshot)).toEqual({ revision: 1, preferences: shell });
    expect(() => parseHostPreferences({ revision: 1, values: { 'app.general': { zoom: 3 } } })).toThrow('zoom');
    expect(() => parseHostPreferences({ revision: 1, values: { 'app.general': { theme: 'blue' } } })).toThrow('theme');
    expect(() => parseHostPreferences({ revision: 1, values: { 'config.memory': { memory_limit_gb: 'huge' } } })).toThrow('memory_limit_gb');
    expect(parseHostPreferences({ revision: 1, values: { 'config.databanks': { databank_sync_interval_mins: 10 } } }).preferences.configuration.databankSyncInterval).toBe('Every 10 minutes');
  });

  it('preserves separate TLS flags and loads core counts before runtime discovery', async () => {
    const parsed = parseHostPreferences({ revision: 4, values: { 'notify.email': { use_ssl: true, use_tls: false }, 'config.cpu': { custom_cores: 16 } } });
    expect(parsed.preferences.smtp).toMatchObject({ ssl: true, tls: false });
    expect(parsed.preferences.configuration.customCores).toBe(16);
    const fetchFn = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ status: 'success', data: { revision: 5, values: {} } }) });
    await writeHostPreferences({ ...parsed.preferences, smtp: { ...parsed.preferences.smtp, server: 'changed.test' } }, parsed.preferences, 4, { fetchFn: asFetch(fetchFn) });
    expect(JSON.parse(fetchFn.mock.calls[0][1].body).changes).toEqual({ 'notify.email': { smtp_server: 'changed.test' } });
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
    expect(JSON.parse((fetchFn.mock.calls[1][1] as RequestInit).body as string)).toEqual({ expected_revision: 1, changes: { 'app.general': { theme: 'light', zoom: 1.2 } } });
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
      'config.global': { sounds_off: true },
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
        streamController.enqueue(new TextEncoder().encode('changed","payload":{"revision":2}}\n\n'));
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
describe('catalogue secret boundaries', () => {
  const secret = { scope: 'config.agents', group: 'config_agents', key: 'openai.api_key', label: 'OpenAI API key', kind: 'str', secret: true, readonly: false, configured: true };
  it('accepts presence metadata while rejecting secret-bearing or untyped projections', () => {
    expect(parseSettingsCatalogue({ revision: 3, fields: [secret], unknown: [] }).fields[0].configured).toBe(true);
    for (const field of [{ ...secret, value: 'must-not-be-returned' }, { ...secret, secret: false, value: 'must-not-be-returned' }, { ...secret, configured: 'yes' }]) {
      expect(() => parseSettingsCatalogue({ revision: 3, fields: [field], unknown: [] })).toThrow();
    }
    expect(() => parseSettingsCatalogue({ revision: 3, fields: [{ ...secret, key: 'timeout_ms', secret: false, kind: 'int', value: '60' }], unknown: [] })).toThrow();
  });
});
