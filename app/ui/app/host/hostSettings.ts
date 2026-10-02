/** Host-owned shell settings and authenticated settings event stream. */

import { applicationLanguages, createInitialAppSettings, validateConfiguration } from './globalSettings';
import { ApiClientError, createDomainClient, getAuthToken, hostBaseUrl, type TransportConfig } from './transport';
import type { AppSettings, ConfigurationSettings } from './types';

export type ShellPreferences = Pick<
  AppSettings,
  'theme' | 'language' | 'zoom' | 'configuration' | 'remoteAccess' | 'smtp' | 'telegram' | 'desktopNotification' | 'mcp'
>;
export interface HostSettingsSnapshot { revision: number; preferences: ShellPreferences }

export function shellPreferences(settings: AppSettings): ShellPreferences {
  const { theme, language, zoom, configuration, remoteAccess, smtp, telegram, desktopNotification, mcp } = settings;
  return { theme, language, zoom, configuration, remoteAccess, smtp, telegram, desktopNotification, mcp };
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
  const mt5Record = record(values, 'config.metatrader5');
  const ctraderRecord = record(values, 'config.ctrader');
  const agentsRecord = record(values, 'config.agents');
  const pathsRecord = record(values, 'workspace.paths');
  const engineRecord = record(values, 'engine.backtest');
  const remote = record(values, 'connect.remote');
  const email = record(values, 'notify.email');
  const telegramRecord = record(values, 'notify.telegram');
  const desktopRecord = record(values, 'notify.desktop');
  const mcpRecord = record(values, 'connect.mcp');

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
    mt5: {
      enabled: boolField(mt5Record, 'enabled', defaults.configuration.mt5.enabled),
      terminalPath: stringField(mt5Record, 'terminal_path', defaults.configuration.mt5.terminalPath),
      accountId: String(mt5Record.account_id ?? defaults.configuration.mt5.accountId),
      password: stringField(mt5Record, 'password', defaults.configuration.mt5.password),
      server: stringField(mt5Record, 'server', defaults.configuration.mt5.server),
      environment: (stringField(mt5Record, 'environment', defaults.configuration.mt5.environment) as 'demo' | 'live' | 'real'),
      timeoutMs: numberField(mt5Record, 'timeout_ms', defaults.configuration.mt5.timeoutMs),
      portable: boolField(mt5Record, 'portable', defaults.configuration.mt5.portable),
      useTicks: boolField(mt5Record, 'use_ticks', defaults.configuration.mt5.useTicks),
    },
    ctrader: {
      enabled: boolField(ctraderRecord, 'enabled', defaults.configuration.ctrader.enabled),
      clientId: stringField(ctraderRecord, 'client_id', defaults.configuration.ctrader.clientId),
      clientSecret: stringField(ctraderRecord, 'client_secret', defaults.configuration.ctrader.clientSecret),
      accessToken: stringField(ctraderRecord, 'access_token', defaults.configuration.ctrader.accessToken),
      refreshToken: stringField(ctraderRecord, 'refresh_token', defaults.configuration.ctrader.refreshToken),
      redirectUrl: stringField(ctraderRecord, 'redirect_url', defaults.configuration.ctrader.redirectUrl),
      environment: (stringField(ctraderRecord, 'environment', defaults.configuration.ctrader.environment) as 'demo' | 'live' | 'real'),
      accountId: String(ctraderRecord.account_id ?? defaults.configuration.ctrader.accountId),
      gatewayHost: stringField(ctraderRecord, 'gateway_host', defaults.configuration.ctrader.gatewayHost),
      gatewayPort: numberField(ctraderRecord, 'gateway_port', defaults.configuration.ctrader.gatewayPort),
    },
    agents: {
      activeProvider: (stringField(agentsRecord, 'active_provider', defaults.configuration.agents.activeProvider) as 'gemini' | 'openai' | 'ollama'),
      gemini: {
        apiKey: stringField(record(agentsRecord, 'gemini'), 'api_key', defaults.configuration.agents.gemini.apiKey),
        model: stringField(record(agentsRecord, 'gemini'), 'model', defaults.configuration.agents.gemini.model),
        fastModel: stringField(record(agentsRecord, 'gemini'), 'fast_model', defaults.configuration.agents.gemini.fastModel),
        premiumModel: stringField(record(agentsRecord, 'gemini'), 'premium_model', defaults.configuration.agents.gemini.premiumModel),
        fallbackModel: stringField(record(agentsRecord, 'gemini'), 'fallback_model', defaults.configuration.agents.gemini.fallbackModel),
        temperature: numberField(record(agentsRecord, 'gemini'), 'temperature', defaults.configuration.agents.gemini.temperature),
        maxTokens: numberField(record(agentsRecord, 'gemini'), 'max_tokens', defaults.configuration.agents.gemini.maxTokens),
        useVertexAi: boolField(record(agentsRecord, 'gemini'), 'use_vertex_ai', defaults.configuration.agents.gemini.useVertexAi),
      },
      openai: {
        apiKey: stringField(record(agentsRecord, 'openai'), 'api_key', defaults.configuration.agents.openai.apiKey),
        baseUrl: stringField(record(agentsRecord, 'openai'), 'base_url', defaults.configuration.agents.openai.baseUrl),
        model: stringField(record(agentsRecord, 'openai'), 'model', defaults.configuration.agents.openai.model),
        temperature: numberField(record(agentsRecord, 'openai'), 'temperature', defaults.configuration.agents.openai.temperature),
        maxTokens: numberField(record(agentsRecord, 'openai'), 'max_tokens', defaults.configuration.agents.openai.maxTokens),
      },
      ollama: {
        baseUrl: stringField(record(agentsRecord, 'ollama'), 'base_url', defaults.configuration.agents.ollama.baseUrl),
        model: stringField(record(agentsRecord, 'ollama'), 'model', defaults.configuration.agents.ollama.model),
        temperature: numberField(record(agentsRecord, 'ollama'), 'temperature', defaults.configuration.agents.ollama.temperature),
        timeoutSeconds: numberField(record(agentsRecord, 'ollama'), 'timeout_seconds', defaults.configuration.agents.ollama.timeoutSeconds),
      },
      systemPromptPreset: stringField(agentsRecord, 'system_prompt_preset', defaults.configuration.agents.systemPromptPreset),
      agentTimeoutSeconds: numberField(agentsRecord, 'agent_timeout_seconds', defaults.configuration.agents.agentTimeoutSeconds),
    },
    directories: {
      configsDir: stringField(pathsRecord, 'configs_dir', defaults.configuration.directories.configsDir),
      projectsDir: stringField(pathsRecord, 'projects_dir', defaults.configuration.directories.projectsDir),
      strategiesDir: stringField(pathsRecord, 'strategies_dir', defaults.configuration.directories.strategiesDir),
      customdataDir: stringField(pathsRecord, 'customdata_dir', defaults.configuration.directories.customdataDir),
    },
    backtestEngine: {
      maxThreads: numberField(engineRecord, 'max_threads', defaults.configuration.backtestEngine.maxThreads),
      memoryLimitMb: numberField(engineRecord, 'memory_limit_mb', defaults.configuration.backtestEngine.memoryLimitMb),
      enableCaching: boolField(engineRecord, 'enable_caching', defaults.configuration.backtestEngine.enableCaching),
      precisionMode: (stringField(engineRecord, 'precision_mode', defaults.configuration.backtestEngine.precisionMode) as 'high' | 'standard' | 'low'),
      benchmarkTimePerTickMs: numberField(engineRecord, 'benchmark_time_per_tick_ms', defaults.configuration.backtestEngine.benchmarkTimePerTickMs),
      dontStorePendingOrders: boolField(engineRecord, 'dont_store_pending_orders', defaults.configuration.backtestEngine.dontStorePendingOrders),
      dontStoreOp3dCharts: boolField(engineRecord, 'dont_store_op3d_charts', defaults.configuration.backtestEngine.dontStoreOp3dCharts),
      computeSeparateMetrics: boolField(engineRecord, 'compute_separate_metrics', defaults.configuration.backtestEngine.computeSeparateMetrics),
      computePctsMetrics: boolField(engineRecord, 'compute_pcts_metrics', defaults.configuration.backtestEngine.computePctsMetrics),
      computePipsMetrics: boolField(engineRecord, 'compute_pips_metrics', defaults.configuration.backtestEngine.computePipsMetrics),
      sourceCodeConstantsParams: boolField(engineRecord, 'source_code_constants_params', defaults.configuration.backtestEngine.sourceCodeConstantsParams),
    },
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
      enabled: boolField(email, 'enabled', true),
      server: stringField(email, 'smtp_server', ''), port: String(port),
      ssl: boolField(email, 'use_ssl', false) || boolField(email, 'use_tls', true),
      username: stringField(email, 'username', ''),
      emailFrom: stringField(email, 'from_address', ''),
    },
    telegram: {
      enabled: boolField(telegramRecord, 'enabled', defaults.telegram.enabled),
      chatId: stringField(telegramRecord, 'chat_id', defaults.telegram.chatId),
      parseMode: (stringField(telegramRecord, 'parse_mode', defaults.telegram.parseMode) as 'HTML' | 'Markdown' | 'MarkdownV2'),
      disableNotification: boolField(telegramRecord, 'disable_notification', defaults.telegram.disableNotification),
    },
    desktopNotification: {
      enabled: boolField(desktopRecord, 'enabled', defaults.desktopNotification.enabled),
      soundEnabled: boolField(desktopRecord, 'sound_enabled', defaults.desktopNotification.soundEnabled),
      durationSeconds: numberField(desktopRecord, 'duration_seconds', defaults.desktopNotification.durationSeconds),
      minPriority: (stringField(desktopRecord, 'min_priority', defaults.desktopNotification.minPriority) as 'low' | 'normal' | 'high' | 'critical'),
    },
    mcp: {
      enabled: boolField(mcpRecord, 'enabled', defaults.mcp.enabled),
      host: stringField(mcpRecord, 'host', defaults.mcp.host),
      port: numberField(mcpRecord, 'port', defaults.mcp.port),
      transport: (stringField(mcpRecord, 'transport', defaults.mcp.transport) as 'sse' | 'stdio' | 'websocket' | 'http'),
      allowedTools: Array.isArray(mcpRecord.allowed_tools) ? mcpRecord.allowed_tools as string[] : defaults.mcp.allowedTools,
      maxContextItems: numberField(mcpRecord, 'max_context_items', defaults.mcp.maxContextItems),
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

  // MT5
  changed('config.metatrader5', 'enabled', next.mt5.enabled, old.mt5.enabled);
  changed('config.metatrader5', 'terminal_path', next.mt5.terminalPath, old.mt5.terminalPath);
  changed('config.metatrader5', 'account_id', next.mt5.accountId, old.mt5.accountId);
  changed('config.metatrader5', 'password', next.mt5.password, old.mt5.password);
  changed('config.metatrader5', 'server', next.mt5.server, old.mt5.server);
  changed('config.metatrader5', 'environment', next.mt5.environment, old.mt5.environment);
  changed('config.metatrader5', 'timeout_ms', next.mt5.timeoutMs, old.mt5.timeoutMs);
  changed('config.metatrader5', 'portable', next.mt5.portable, old.mt5.portable);
  changed('config.metatrader5', 'use_ticks', next.mt5.useTicks, old.mt5.useTicks);

  // cTrader
  changed('config.ctrader', 'enabled', next.ctrader.enabled, old.ctrader.enabled);
  changed('config.ctrader', 'client_id', next.ctrader.clientId, old.ctrader.clientId);
  changed('config.ctrader', 'client_secret', next.ctrader.clientSecret, old.ctrader.clientSecret);
  changed('config.ctrader', 'access_token', next.ctrader.accessToken, old.ctrader.accessToken);
  changed('config.ctrader', 'refresh_token', next.ctrader.refreshToken, old.ctrader.refreshToken);
  changed('config.ctrader', 'redirect_url', next.ctrader.redirectUrl, old.ctrader.redirectUrl);
  changed('config.ctrader', 'environment', next.ctrader.environment, old.ctrader.environment);
  changed('config.ctrader', 'account_id', next.ctrader.accountId, old.ctrader.accountId);
  changed('config.ctrader', 'gateway_host', next.ctrader.gatewayHost, old.ctrader.gatewayHost);
  changed('config.ctrader', 'gateway_port', next.ctrader.gatewayPort, old.ctrader.gatewayPort);

  // AI Agents
  changed('config.agents', 'active_provider', next.agents.activeProvider, old.agents.activeProvider);
  changed('config.agents', 'system_prompt_preset', next.agents.systemPromptPreset, old.agents.systemPromptPreset);
  changed('config.agents', 'agent_timeout_seconds', next.agents.agentTimeoutSeconds, old.agents.agentTimeoutSeconds);
  if (JSON.stringify(next.agents.gemini) !== JSON.stringify(old.agents.gemini)) {
    put('config.agents', 'gemini', {
      api_key: next.agents.gemini.apiKey, model: next.agents.gemini.model, fast_model: next.agents.gemini.fastModel,
      premium_model: next.agents.gemini.premiumModel, fallback_model: next.agents.gemini.fallbackModel,
      temperature: next.agents.gemini.temperature, max_tokens: next.agents.gemini.maxTokens, use_vertex_ai: next.agents.gemini.useVertexAi,
    });
  }
  if (JSON.stringify(next.agents.openai) !== JSON.stringify(old.agents.openai)) {
    put('config.agents', 'openai', {
      api_key: next.agents.openai.apiKey, base_url: next.agents.openai.baseUrl, model: next.agents.openai.model,
      temperature: next.agents.openai.temperature, max_tokens: next.agents.openai.maxTokens,
    });
  }
  if (JSON.stringify(next.agents.ollama) !== JSON.stringify(old.agents.ollama)) {
    put('config.agents', 'ollama', {
      base_url: next.agents.ollama.baseUrl, model: next.agents.ollama.model,
      temperature: next.agents.ollama.temperature, timeout_seconds: next.agents.ollama.timeoutSeconds,
    });
  }

  // Paths
  changed('workspace.paths', 'configs_dir', next.directories.configsDir, old.directories.configsDir);
  changed('workspace.paths', 'projects_dir', next.directories.projectsDir, old.directories.projectsDir);
  changed('workspace.paths', 'strategies_dir', next.directories.strategiesDir, old.directories.strategiesDir);
  changed('workspace.paths', 'customdata_dir', next.directories.customdataDir, old.directories.customdataDir);

  // Backtest engine
  changed('engine.backtest', 'max_threads', next.backtestEngine.maxThreads, old.backtestEngine.maxThreads);
  changed('engine.backtest', 'memory_limit_mb', next.backtestEngine.memoryLimitMb, old.backtestEngine.memoryLimitMb);
  changed('engine.backtest', 'enable_caching', next.backtestEngine.enableCaching, old.backtestEngine.enableCaching);
  changed('engine.backtest', 'precision_mode', next.backtestEngine.precisionMode, old.backtestEngine.precisionMode);
  changed('engine.backtest', 'benchmark_time_per_tick_ms', next.backtestEngine.benchmarkTimePerTickMs, old.backtestEngine.benchmarkTimePerTickMs);
  changed('engine.backtest', 'dont_store_pending_orders', next.backtestEngine.dontStorePendingOrders, old.backtestEngine.dontStorePendingOrders);
  changed('engine.backtest', 'dont_store_op3d_charts', next.backtestEngine.dontStoreOp3dCharts, old.backtestEngine.dontStoreOp3dCharts);
  changed('engine.backtest', 'compute_separate_metrics', next.backtestEngine.computeSeparateMetrics, old.backtestEngine.computeSeparateMetrics);
  changed('engine.backtest', 'compute_pcts_metrics', next.backtestEngine.computePctsMetrics, old.backtestEngine.computePctsMetrics);
  changed('engine.backtest', 'compute_pips_metrics', next.backtestEngine.computePipsMetrics, old.backtestEngine.computePipsMetrics);
  changed('engine.backtest', 'source_code_constants_params', next.backtestEngine.sourceCodeConstantsParams, old.backtestEngine.sourceCodeConstantsParams);

  changed('connect.remote', 'allow', preferences.remoteAccess.allow, previous.remoteAccess.allow);
  changed('connect.remote', 'require_password', preferences.remoteAccess.requirePassword, previous.remoteAccess.requirePassword);

  // SMTP
  changed('notify.email', 'enabled', preferences.smtp.enabled, previous.smtp.enabled);
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

  // Telegram
  changed('notify.telegram', 'enabled', preferences.telegram.enabled, previous.telegram.enabled);
  changed('notify.telegram', 'chat_id', preferences.telegram.chatId, previous.telegram.chatId);
  changed('notify.telegram', 'parse_mode', preferences.telegram.parseMode, previous.telegram.parseMode);
  changed('notify.telegram', 'disable_notification', preferences.telegram.disableNotification, previous.telegram.disableNotification);

  // Desktop
  changed('notify.desktop', 'enabled', preferences.desktopNotification.enabled, previous.desktopNotification.enabled);
  changed('notify.desktop', 'sound_enabled', preferences.desktopNotification.soundEnabled, previous.desktopNotification.soundEnabled);
  changed('notify.desktop', 'duration_seconds', preferences.desktopNotification.durationSeconds, previous.desktopNotification.durationSeconds);
  changed('notify.desktop', 'min_priority', preferences.desktopNotification.minPriority, previous.desktopNotification.minPriority);

  // MCP
  changed('connect.mcp', 'enabled', preferences.mcp.enabled, previous.mcp.enabled);
  changed('connect.mcp', 'host', preferences.mcp.host, previous.mcp.host);
  changed('connect.mcp', 'port', preferences.mcp.port, previous.mcp.port);
  changed('connect.mcp', 'transport', preferences.mcp.transport, previous.mcp.transport);
  changed('connect.mcp', 'max_context_items', preferences.mcp.maxContextItems, previous.mcp.maxContextItems);
  if (JSON.stringify(preferences.mcp.allowedTools) !== JSON.stringify(previous.mcp.allowedTools)) {
    put('connect.mcp', 'allowed_tools', preferences.mcp.allowedTools);
  }
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
