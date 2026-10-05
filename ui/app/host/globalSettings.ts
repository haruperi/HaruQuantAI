import type { AppSettings, ConfigurationSettings, McpSettings, RemoteAccessSettings, SmtpSettings, TelegramSettings } from './types';

export const configurationTabs = [
  'Global', 'CPU', 'Performance', 'Memory', 'Databanks', 'Optimizations', 'Troubleshooting',
  'Directories', 'Backtest Engine',
] as const;

export const credentialsTabs = [
  'MetaTrader 5', 'cTrader', 'AI Agents',
] as const;

export const globalMenuGroups = [
  ['configuration', 'credentials', 'benchmark', 'remote-access', 'mcp-server', 'notifications'],
  ['skin'],
  ['zoom'],
  ['reload-ui', 'exit'],
] as const;

export const globalMenuLabels: Record<string, string> = {
  configuration: 'Configuration...', credentials: 'Credentials...', benchmark: 'Benchmark...', 'remote-access': 'Remote access...',
  'mcp-server': 'MCP Server...', notifications: 'Notifications...', 'smtp-server': 'Notifications...',
  skin: 'Skin', zoom: 'Zoom',
  'reload-ui': 'Reload UI', exit: 'Exit',
};

export const applicationLanguages = [
  'English', 'Cesky', 'Chinese (Simplified)', 'Chinese (Traditional)', 'French', 'German',
  'Indonesia', 'Italiano', 'Polski', 'Portuguese', 'Russian', 'Spanish',
] as const;

export const applicationSkins = ['Dark skin', 'Light skin'] as const;

export function createDefaultConfiguration(): ConfigurationSettings {
  return {
    soundsOff: false, rememberFileChooser: true, showControlOrders: false,
    headerCustomText: '', footerCustomText: '', defaultResult: 'portfolio', totalCores: 8,
    coreUsage: 'reserve-one', customCores: 7, highPriority: false, threadAffinity: false,
    computePipsMetrics: false, computePercentMetrics: false, computeSeparateMetrics: true,
    garbageCollector: 'parallel', automaticMemory: false, memoryGb: 10,
    dontStorePendingOrders: true, memoryCleanup: false, cleanupInterval: '15 minutes',
    databankSyncInterval: 'Every 15 minutes', syncDatabanksAfterTask: true,
    storeChartData: false, dontStoreOptimization3d: true, gpuAccelerated: true,
    memoryProtection: true, debugLevel: false,
    mt5: {
      enabled: false, terminalPath: '',
      accountId: '', password: '', server: '', environment: 'demo',
      timeoutMs: 60000, portable: false, useTicks: true,
    },
    ctrader: {
      enabled: false, clientId: '', clientSecret: '',
      accessToken: '', refreshToken: '', redirectUrl: '',
      environment: 'demo', accountId: '', gatewayHost: '', gatewayPort: 5035,
    },
    agents: {
      activeProvider: 'gemini',
      gemini: {
        apiKey: '', model: '', fastModel: '',
        premiumModel: '', fallbackModel: '', temperature: 0.2, maxTokens: 8192, useVertexAi: false,
      },
      openai: {
        apiKey: '', baseUrl: '', model: '',
        temperature: 0.2, maxTokens: 4096,
      },
      ollama: {
        baseUrl: '', model: '', temperature: 0.2, timeoutSeconds: 120,
      },
      systemPromptPreset: 'quant_researcher',
      agentTimeoutSeconds: 180,
    },
    directories: {
      configsDir: '', projectsDir: '',
      strategiesDir: '', customdataDir: '',
    },
    backtestEngine: {
      maxThreads: 4, memoryLimitMb: 8192, enableCaching: true, precisionMode: 'high',
      benchmarkTimePerTickMs: 0.000017, dontStorePendingOrders: true, dontStoreOp3dCharts: true,
      computeSeparateMetrics: true, computePctsMetrics: false, computePipsMetrics: false,
      sourceCodeConstantsParams: true,
    },
  };
}

export function createInitialAppSettings(): AppSettings {
  return {
    theme: 'dark', language: 'English', autosave: true, workers: 8, memoryGb: 10,
    profile: 'Full', zoom: 1, configuration: createDefaultConfiguration(),
    remoteAccess: { allow: false, requirePassword: false },
    smtp: { enabled: true, server: '', port: '587', ssl: true, username: '', emailFrom: '' },
    telegram: { enabled: false, chatId: '', parseMode: 'HTML', disableNotification: false },
    desktopNotification: { enabled: true, soundEnabled: true, durationSeconds: 5, minPriority: 'normal' },
    mcp: {
      enabled: false, host: '127.0.0.1', port: 5055, transport: 'sse',
      allowedTools: [],
      maxContextItems: 50,
    },
  };
}

export function mergeAppSettings(saved?: Partial<AppSettings> & { navigationCollapsed?: boolean }): AppSettings {
  const defaults = createInitialAppSettings();
  const { navigationCollapsed: _legacyCollapsed, ...rest } = saved ?? {};
  return {
    ...defaults,
    ...rest,
    configuration: {
      ...defaults.configuration,
      ...saved?.configuration,
      mt5: { ...defaults.configuration.mt5, ...saved?.configuration?.mt5 },
      ctrader: { ...defaults.configuration.ctrader, ...saved?.configuration?.ctrader },
      agents: {
        ...defaults.configuration.agents,
        ...saved?.configuration?.agents,
        gemini: { ...defaults.configuration.agents.gemini, ...saved?.configuration?.agents?.gemini },
        openai: { ...defaults.configuration.agents.openai, ...saved?.configuration?.agents?.openai },
        ollama: { ...defaults.configuration.agents.ollama, ...saved?.configuration?.agents?.ollama },
      },
      directories: { ...defaults.configuration.directories, ...saved?.configuration?.directories },
      backtestEngine: { ...defaults.configuration.backtestEngine, ...saved?.configuration?.backtestEngine },
    },
    remoteAccess: { ...defaults.remoteAccess, ...saved?.remoteAccess },
    smtp: { ...defaults.smtp, ...saved?.smtp },
    telegram: { ...defaults.telegram, ...saved?.telegram },
    desktopNotification: { ...defaults.desktopNotification, ...saved?.desktopNotification },
    mcp: { ...defaults.mcp, ...saved?.mcp },
  };
}

export function validateConfiguration(value: ConfigurationSettings): string | null {
  if (!Number.isInteger(value.customCores) || value.customCores < 1 || value.customCores > Math.max(1, value.totalCores)) return 'Custom cores must be a whole number between 1 and the available core count.';
  if (!Number.isFinite(value.memoryGb) || value.memoryGb < 2 || value.memoryGb > 1024) return 'Maximum memory must be between 2 and 1024 GB.';
  if (value.headerCustomText.length > 30 || value.footerCustomText.length > 30) return 'Window header and footer text must contain at most 30 characters.';
  return null;
}

export function clampZoom(value: number): number {
  return Math.min(1.8, Math.max(0.7, Math.round(value * 10) / 10));
}

export function safeRemoteSettings(value: RemoteAccessSettings & { password?: string }): RemoteAccessSettings {
  return { allow: value.allow, requirePassword: value.allow && value.requirePassword };
}

export function safeSmtpSettings(value: Omit<SmtpSettings, 'enabled'> & { enabled?: boolean; password?: string }): SmtpSettings {
  return { enabled: value.enabled ?? true, server: value.server.trim(), port: value.port.trim(), ssl: value.ssl, username: value.username.trim(), emailFrom: value.emailFrom.trim() };
}

export function safeTelegramSettings(value: Omit<TelegramSettings, 'enabled'> & { enabled?: boolean; botToken?: string }): TelegramSettings {
  return {
    enabled: value.enabled ?? false,
    chatId: value.chatId.trim(),
    parseMode: value.parseMode,
    disableNotification: value.disableNotification,
  };
}

export function safeMcpSettings(value: Omit<McpSettings, 'enabled'> & { enabled?: boolean; authToken?: string }): McpSettings {
  return {
    enabled: value.enabled ?? true,
    host: value.host.trim() || '127.0.0.1',
    port: Number(value.port) || 5055,
    transport: value.transport,
    allowedTools: [...value.allowedTools],
    maxContextItems: Number(value.maxContextItems) || 50,
  };
}

export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export const benchmarkResults = {
  duration: '2.4 s / 8.7 s', strategyAverageTime: '0.087 s.', timePerTick: '0.0042 ms.',
  totalTicks: '2,040,000', avgStrategiesPerHour: '41,379',
} as const;
