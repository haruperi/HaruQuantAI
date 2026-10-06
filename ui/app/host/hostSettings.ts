/** Host-owned shell settings and authenticated settings event stream. */

import { applicationLanguages, createInitialAppSettings, validateConfiguration } from './globalSettings';
import { ApiClientError, createDomainClient, getAuthToken, hostBaseUrl, type TransportConfig } from './transport';
import type { AppSettings, ConfigurationSettings } from './types';

export type ShellPreferences = Pick<AppSettings, 'theme' | 'language' | 'zoom' | 'configuration' | 'remoteAccess' | 'smtp'>;
export interface HostSettingsSnapshot { revision: number; preferences: ShellPreferences }

export function shellPreferences(settings: AppSettings): ShellPreferences {
  const { theme, language, zoom, configuration, remoteAccess, smtp } = settings;
  return { theme, language, zoom, configuration, remoteAccess, smtp };
}

function object(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error(`${label} must be an object`);
  return value as Record<string, unknown>;
}

const languageCodes: Record<string, string> = {
  English: 'en', Cesky: 'cs', 'Chinese (Simplified)': 'zh-CN',
  'Chinese (Traditional)': 'zh-TW', French: 'fr', German: 'de',
  Indonesia: 'id', Italiano: 'it', Polski: 'pl', Portuguese: 'pt',
  Russian: 'ru', Spanish: 'es',
};
const languageLabels = Object.fromEntries(Object.entries(languageCodes).map(([label, code]) => [code, label]));
const cpuModes: Record<ConfigurationSettings['coreUsage'], string> = {
  single: 'single', 'reserve-one': 'all_except_one', custom: 'custom', maximum: 'all',
};
const gcModes: Record<ConfigurationSettings['garbageCollector'], string> = {
  parallel: 'ParallelGC', g1: 'G1GC', automatic: 'Automatic',
};
const cleanupMinutes: Record<ConfigurationSettings['cleanupInterval'], number> = {
  '5 minutes': 5, '15 minutes': 15, '30 minutes': 30, '1 hour': 60,
};
const syncMinutes: Record<ConfigurationSettings['databankSyncInterval'], number | null> = {
  Never: null, Immediately: 0, 'Every 5 minutes': 5,
  'Every 10 minutes': 10, 'Every 15 minutes': 15, 'Every hour': 60,
};

function record(values: Record<string, unknown>, key: string): Record<string, unknown> {
  return values[key] === undefined ? {} : object(values[key], `Host ${key}`);
}

function stringField(row: Record<string, unknown>, key: string, fallback: string): string {
  const value = row[key];
  if (value === undefined) return fallback;
  if (typeof value !== 'string') throw new Error(`Host ${key} is invalid`);
  return value;
}

function boolField(row: Record<string, unknown>, key: string, fallback: boolean): boolean {
  const value = row[key];
  if (value === undefined) return fallback;
  if (typeof value !== 'boolean') throw new Error(`Host ${key} is invalid`);
  return value;
}

function numberField(row: Record<string, unknown>, key: string, fallback: number): number {
  const value = row[key];
  if (value === undefined) return fallback;
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`Host ${key} is invalid`);
  return value;
}

function mappedField<T extends string>(value: unknown, map: Record<T, unknown>, label: string): T {
  const found = (Object.entries(map) as [T, unknown][]).find(([, stored]) => stored === value)?.[0];
  if (!found) throw new Error(`Host ${label} is unsupported`);
  return found;
}

function parsePreferences(values: Record<string, unknown>): ShellPreferences {
  const defaults = createInitialAppSettings();
  const app = record(values, 'app.general');
  const global = record(values, 'config.global');
  const cpu = record(values, 'config.cpu');
  const performance = record(values, 'config.performance');
  const memory = record(values, 'config.memory');
  const databanks = record(values, 'config.databanks');
  const optimizations = record(values, 'config.optimizations');
  const troubleshooting = record(values, 'config.troubleshooting');
  const remote = record(values, 'connect.remote');
  const email = record(values, 'notify.email');
  const rawLanguage = stringField(app, 'language', stringField(global, 'language', 'en'));
  const language = languageLabels[rawLanguage];
  if (!language || !applicationLanguages.some(item => item === language)) throw new Error('Host language is unsupported');
  const theme = stringField(app, 'theme', stringField(global, 'theme', defaults.theme));
  if (theme !== 'dark' && theme !== 'light') throw new Error('Host theme is invalid');
  const zoom = numberField(app, 'zoom', defaults.zoom);
  if (zoom < 0.7 || zoom > 1.8) throw new Error('Host zoom is invalid');
  const defaultResult = stringField(global, 'default_result_to_display', 'Portfolio').toLowerCase();
  if (defaultResult !== 'portfolio' && defaultResult !== 'main') throw new Error('Host default result is invalid');
  const interval = databanks.databank_sync_interval_mins === undefined ? 15 : databanks.databank_sync_interval_mins;
  const configuration: ConfigurationSettings = {
    ...defaults.configuration,
    soundsOff: boolField(global, 'sounds_off', defaults.configuration.soundsOff),
    rememberFileChooser: boolField(global, 'advanced_file_chooser', defaults.configuration.rememberFileChooser),
    showControlOrders: boolField(global, 'show_control_orders', defaults.configuration.showControlOrders),
    headerCustomText: stringField(global, 'header_custom_text', ''),
    footerCustomText: stringField(global, 'footer_custom_text', ''),
    defaultResult,
    coreUsage: mappedField(stringField(cpu, 'core_usage', 'all_except_one'), cpuModes, 'CPU mode'),
    customCores: numberField(cpu, 'custom_cores', defaults.configuration.customCores),
    highPriority: boolField(cpu, 'high_priority', false),
    threadAffinity: boolField(cpu, 'thread_affinity', false),
    computePipsMetrics: boolField(performance, 'compute_pips_metrics', false),
    computePercentMetrics: boolField(performance, 'compute_pcts_metrics', false),
    computeSeparateMetrics: boolField(performance, 'compute_separate_metrics', true),
    garbageCollector: mappedField(stringField(memory, 'gc_type', 'ParallelGC'), gcModes, 'garbage collector'),
    automaticMemory: boolField(memory, 'automatic_memory', false),
    memoryGb: numberField(memory, 'memory_limit_gb', defaults.configuration.memoryGb),
    dontStorePendingOrders: boolField(memory, 'dont_store_pending_orders', true),
    memoryCleanup: boolField(memory, 'memory_cleanup', false),
    cleanupInterval: mappedField(numberField(memory, 'cleanup_interval_mins', 15), cleanupMinutes, 'cleanup interval'),
    databankSyncInterval: mappedField(interval, syncMinutes, 'databank interval'),
    syncDatabanksAfterTask: boolField(databanks, 'sync_databanks_after_task_done', true),
    storeChartData: boolField(databanks, 'store_chart_data', false),
    dontStoreOptimization3d: boolField(optimizations, 'dont_store_op_3d_charts_data', true),
    gpuAccelerated: boolField(troubleshooting, 'gpu_accelerated', boolField(app, 'gpu_accelerated', true)),
    memoryProtection: boolField(troubleshooting, 'memory_protection', true),
    debugLevel: boolField(troubleshooting, 'debug_level_active', false),
  };
  const problem = validateConfiguration(configuration);
  if (problem) throw new Error(`Host configuration is invalid: ${problem}`);
  const port = numberField(email, 'smtp_port', 587);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Host SMTP port is invalid');
  return {
    theme, language: language as ShellPreferences['language'], zoom, configuration,
    remoteAccess: {
      allow: boolField(remote, 'allow', false),
      requirePassword: boolField(remote, 'require_password', false),
    },
    smtp: {
      server: stringField(email, 'smtp_server', ''), port: String(port),
      ssl: boolField(email, 'use_ssl', false) || boolField(email, 'use_tls', true),
      username: stringField(email, 'username', ''),
      emailFrom: stringField(email, 'from_address', ''),
    },
  };
}

export function parseHostPreferences(value: unknown): HostSettingsSnapshot {
  const snapshot = object(value, 'Host settings snapshot');
  if (!Number.isInteger(snapshot.revision) || (snapshot.revision as number) < 0) throw new Error('Host settings revision is invalid');
  const values = object(snapshot.values, 'Host settings values');
  return { revision: snapshot.revision as number, preferences: parsePreferences(values) };
}

export async function readHostPreferences(config: TransportConfig = {}): Promise<HostSettingsSnapshot> {
  return parseHostPreferences(await createDomainClient('', config).get<unknown>('/settings'));
}

export async function writeHostPreferences(
  preferences: ShellPreferences, previous: ShellPreferences,
  expectedRevision: number, config: TransportConfig = {},
): Promise<HostSettingsSnapshot & { wrote: boolean }> {
  const changes: Record<string, Record<string, unknown>> = {};
  const put = (key: string, field: string, value: unknown) => {
    (changes[key] ??= {})[field] = value;
  };
  const changed = (key: string, field: string, value: unknown, before: unknown) => {
    if (!Object.is(value, before)) put(key, field, value);
  };
  changed('app.general', 'theme', preferences.theme, previous.theme);
  changed('config.global', 'theme', preferences.theme, previous.theme);
  changed('app.general', 'language', languageCodes[preferences.language], languageCodes[previous.language]);
  changed('config.global', 'language', languageCodes[preferences.language], languageCodes[previous.language]);
  changed('app.general', 'zoom', preferences.zoom, previous.zoom);
  const next = preferences.configuration;
  const old = previous.configuration;
  const field = (key: string, name: string, current: keyof ConfigurationSettings, value: unknown = next[current], before: unknown = old[current]) => changed(key, name, value, before);
  field('config.global', 'sounds_off', 'soundsOff');
  field('config.global', 'advanced_file_chooser', 'rememberFileChooser');
  field('config.global', 'show_control_orders', 'showControlOrders');
  field('config.global', 'header_custom_text', 'headerCustomText');
  field('config.global', 'footer_custom_text', 'footerCustomText');
  field('config.global', 'default_result_to_display', 'defaultResult', next.defaultResult === 'main' ? 'Main' : 'Portfolio', old.defaultResult === 'main' ? 'Main' : 'Portfolio');
  field('config.cpu', 'core_usage', 'coreUsage', cpuModes[next.coreUsage], cpuModes[old.coreUsage]);
  field('config.cpu', 'custom_cores', 'customCores');
  field('config.cpu', 'high_priority', 'highPriority');
  field('config.cpu', 'thread_affinity', 'threadAffinity');
  field('config.performance', 'compute_pips_metrics', 'computePipsMetrics');
  field('config.performance', 'compute_pcts_metrics', 'computePercentMetrics');
  field('config.performance', 'compute_separate_metrics', 'computeSeparateMetrics');
  field('config.memory', 'gc_type', 'garbageCollector', gcModes[next.garbageCollector], gcModes[old.garbageCollector]);
  field('config.memory', 'automatic_memory', 'automaticMemory');
  field('config.memory', 'memory_limit_gb', 'memoryGb');
  field('config.memory', 'dont_store_pending_orders', 'dontStorePendingOrders');
  field('config.memory', 'memory_cleanup', 'memoryCleanup');
  field('config.memory', 'cleanup_interval_mins', 'cleanupInterval', cleanupMinutes[next.cleanupInterval], cleanupMinutes[old.cleanupInterval]);
  field('config.databanks', 'databank_sync_interval_mins', 'databankSyncInterval', syncMinutes[next.databankSyncInterval], syncMinutes[old.databankSyncInterval]);
  field('config.databanks', 'sync_databanks_after_task_done', 'syncDatabanksAfterTask');
  field('config.databanks', 'store_chart_data', 'storeChartData');
  field('config.optimizations', 'dont_store_op_3d_charts_data', 'dontStoreOptimization3d');
  field('config.troubleshooting', 'gpu_accelerated', 'gpuAccelerated');
  field('app.general', 'gpu_accelerated', 'gpuAccelerated');
  field('config.troubleshooting', 'memory_protection', 'memoryProtection');
  field('config.troubleshooting', 'debug_level_active', 'debugLevel');
  changed('connect.remote', 'allow', preferences.remoteAccess.allow, previous.remoteAccess.allow);
  changed('connect.remote', 'require_password', preferences.remoteAccess.requirePassword, previous.remoteAccess.requirePassword);
  changed('notify.email', 'smtp_server', preferences.smtp.server, previous.smtp.server);
  if (preferences.smtp.port !== previous.smtp.port) {
    const port = Number(preferences.smtp.port);
    if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('SMTP port must be between 1 and 65535');
    put('notify.email', 'smtp_port', port);
  }
  if (preferences.smtp.ssl !== previous.smtp.ssl) {
    put('notify.email', 'use_ssl', false);
    put('notify.email', 'use_tls', preferences.smtp.ssl);
  }
  changed('notify.email', 'username', preferences.smtp.username, previous.smtp.username);
  changed('notify.email', 'from_address', preferences.smtp.emailFrom, previous.smtp.emailFrom);
  if (Object.keys(changes).length === 0) return { revision: expectedRevision, preferences: previous, wrote: false };
  const saved = await createDomainClient('', config).put<unknown>('/settings', {
    expected_revision: expectedRevision, changes,
  });
  const snapshot = parseHostPreferences(saved);
  return { ...snapshot, wrote: true };
}

export interface SettingsStreamOptions {
  signal: AbortSignal;
  onChanged: () => Promise<void>;
  onConnection: (connected: boolean) => void;
  fetchFn?: typeof fetch;
  baseUrl?: string;
}

function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { resolve(); return; }
    const timer = setTimeout(resolve, ms);
    signal.addEventListener('abort', () => { clearTimeout(timer); reject(signal.reason); }, { once: true });
  });
}

export async function watchSettingsChanges(options: SettingsStreamOptions): Promise<void> {
  const { signal, onChanged, onConnection } = options;
  const fetchFn = options.fetchFn ?? fetch;
  const baseUrl = options.baseUrl ?? hostBaseUrl();
  let backoffMs = 1000;
  while (!signal.aborted) {
    try {
      const token = getAuthToken();
      if (!token) throw new ApiClientError('UNAUTHORIZED', 'Host session required', [], 401);
      const response = await fetchFn(`${baseUrl}/events?channels=settings.changed`, {
        headers: { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
        signal,
      });
      if (response.status === 401) throw new ApiClientError('UNAUTHORIZED', 'Host session expired', [], 401);
      if (!response.ok || !response.body) throw new Error(`Settings stream failed (${response.status})`);
      await onChanged();
      onConnection(true);
      backoffMs = 1000;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        while (!signal.aborted) {
          const chunk = await reader.read();
          if (chunk.done) break;
          buffer += decoder.decode(chunk.value, { stream: true }).replace(/\r\n/g, '\n');
          let frameEnd = buffer.indexOf('\n\n');
          while (frameEnd >= 0) {
            const frame = buffer.slice(0, frameEnd);
            buffer = buffer.slice(frameEnd + 2);
            for (const line of frame.split('\n')) {
              if (!line.startsWith('data:')) continue;
              const payload: unknown = JSON.parse(line.slice(5).trim());
              if (typeof payload === 'object' && payload !== null &&
                  (payload as { channel?: unknown }).channel === 'settings.changed') await onChanged();
            }
            frameEnd = buffer.indexOf('\n\n');
          }
        }
      } finally {
        await reader.cancel().catch(() => undefined);
      }
    } catch (error) {
      if (signal.aborted) return;
      if (error instanceof ApiClientError && error.status === 401) throw error;
    }
    if (signal.aborted) return;
    onConnection(false);
    await delay(backoffMs, signal);
    backoffMs = Math.min(backoffMs * 2, 10000);
  }
}
