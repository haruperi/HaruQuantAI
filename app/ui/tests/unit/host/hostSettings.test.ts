import { describe, expect, it, vi } from 'vitest';
import { parseHostPreferences, readHostPreferences, shellPreferences, watchSettingsChanges, writeHostPreferences } from '../../../app/host/hostSettings';
import { createInitialAppSettings } from '../../../app/host/globalSettings';
import { setAuthToken } from '../../../app/host/transport';

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

  it('translates and persists external broker, agent, path, and notification records', async () => {
    const rawSnapshot = {
      revision: 2,
      values: {
        'config.metatrader5': { enabled: true, terminal_path: 'C:\\MT5\\terminal64.exe', account_id: '12345', password: 'mt5password', server: 'Broker-Demo', environment: 'demo', timeout_ms: 30000, portable: true, use_ticks: true },
        'config.ctrader': { enabled: true, client_id: 'cid1', client_secret: 'csec1', access_token: 'tok1', refresh_token: 'rtok1', redirect_url: 'https://oauth.test', environment: 'live', account_id: 'acc1', gateway_host: 'gateway.test', gateway_port: 5035 },
        'config.agents': {
          active_provider: 'ollama',
          system_prompt_preset: 'risk_manager',
          agent_timeout_seconds: 240,
          ollama: { model: 'llama3:latest' },
          gemini: { fallback_model: 'gemini-3.6-flash' },
        },
        'workspace.paths': { configs_dir: 'user/cfgs', projects_dir: 'user/projs', strategies_dir: 'user/strats', customdata_dir: 'user/data' },
        'engine.backtest': { max_threads: 16, memory_limit_mb: 16384, enable_caching: false, precision_mode: 'low', benchmark_time_per_tick_ms: 0.00002 },
        'notify.telegram': { enabled: true, chat_id: '98765', parse_mode: 'MarkdownV2', disable_notification: true },
        'notify.desktop': { enabled: false, sound_enabled: false, duration_seconds: 10, min_priority: 'critical' },
        'connect.mcp': { enabled: true, host: '0.0.0.0', port: 6000, transport: 'http', allowed_tools: ['backtest', 'strategies'], max_context_items: 100 },
      },
    };
    const parsed = parseHostPreferences(rawSnapshot);
    expect(parsed.preferences.configuration.mt5.terminalPath).toBe('C:\\MT5\\terminal64.exe');
    expect(parsed.preferences.configuration.mt5.password).toBe('mt5password');
    expect(parsed.preferences.configuration.mt5.portable).toBe(true);
    expect(parsed.preferences.configuration.ctrader.clientId).toBe('cid1');
    expect(parsed.preferences.configuration.ctrader.clientSecret).toBe('csec1');
    expect(parsed.preferences.configuration.ctrader.accessToken).toBe('tok1');
    expect(parsed.preferences.configuration.ctrader.refreshToken).toBe('rtok1');
    expect(parsed.preferences.configuration.agents.activeProvider).toBe('ollama');
    expect(parsed.preferences.configuration.agents.gemini.fallbackModel).toBe('gemini-3.6-flash');
    expect(parsed.preferences.configuration.directories.configsDir).toBe('user/cfgs');
    expect(parsed.preferences.configuration.backtestEngine.maxThreads).toBe(16);
    expect(parsed.preferences.configuration.backtestEngine.precisionMode).toBe('low');
    expect(parsed.preferences.telegram.chatId).toBe('98765');
    expect(parsed.preferences.desktopNotification.minPriority).toBe('critical');
    expect(parsed.preferences.mcp.port).toBe(6000);

    const before = shellPreferences(createInitialAppSettings());
    const fetchFn = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ status: 'success', data: { revision: 3, values: {} } }) });
    await writeHostPreferences(parsed.preferences, before, 2, { fetchFn: asFetch(fetchFn), baseUrl: '/api/v1' });
    const body = JSON.parse((fetchFn.mock.calls[0][1] as RequestInit).body as string);
    expect(body.changes['config.metatrader5']).toMatchObject({ terminal_path: 'C:\\MT5\\terminal64.exe', portable: true, password: 'mt5password' }); // pragma: allowlist secret
    expect(body.changes['config.ctrader']).toMatchObject({ client_id: 'cid1', client_secret: 'csec1', access_token: 'tok1', refresh_token: 'rtok1', environment: 'live' }); // pragma: allowlist secret
    expect(body.changes['config.agents']).toMatchObject({
      active_provider: 'ollama',
      system_prompt_preset: 'risk_manager',
      gemini: expect.objectContaining({ fallback_model: 'gemini-3.6-flash' }),
    });
    expect(body.changes['workspace.paths']).toEqual({ configs_dir: 'user/cfgs', projects_dir: 'user/projs', strategies_dir: 'user/strats', customdata_dir: 'user/data' });
    expect(body.changes['engine.backtest']).toMatchObject({ max_threads: 16, memory_limit_mb: 16384, precision_mode: 'low' });
    expect(body.changes['notify.telegram']).toEqual({ enabled: true, chat_id: '98765', parse_mode: 'MarkdownV2', disable_notification: true });
    expect(body.changes['notify.desktop']).toEqual({ enabled: false, sound_enabled: false, duration_seconds: 10, min_priority: 'critical' });
    expect(body.changes['connect.mcp']).toMatchObject({ host: '0.0.0.0', port: 6000, transport: 'http', allowed_tools: ['backtest', 'strategies'], max_context_items: 100 });
  });
});
