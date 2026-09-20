import type { AppSettings, ConfigurationSettings, RemoteAccessSettings, SmtpSettings } from './types';

export const configurationTabs = ['Global', 'CPU', 'Performance', 'Memory', 'Databanks', 'Optimizations', 'Troubleshooting'] as const;

export const globalMenuGroups = [
  ['configuration', 'benchmark', 'remote-access', 'mcp-server', 'smtp-server'],
  ['language'],
  ['skin'],
  ['zoom'],
  ['website', 'help-center', 'support', 'update-license', 'about'],
  ['reload-ui', 'exit'],
] as const;

export const globalMenuLabels: Record<string, string> = {
  configuration: 'Configuration...', benchmark: 'Benchmark...', 'remote-access': 'Remote access...',
  'mcp-server': 'MCP Server...', 'smtp-server': 'SMTP server...', language: 'Language', skin: 'Skin', zoom: 'Zoom',
  website: 'HaruQuantAI Website', 'help-center': 'Help center', support: 'Support', 'update-license': 'Update license',
  about: 'About', 'reload-ui': 'Reload UI', exit: 'Exit',
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
  };
}

export function createInitialAppSettings(): AppSettings {
  return {
    theme: 'dark', language: 'English', autosave: true, workers: 8, memoryGb: 10,
    profile: 'Full', zoom: 1, navigationCollapsed: false, configuration: createDefaultConfiguration(),
    remoteAccess: { allow: false, requirePassword: false },
    smtp: { server: '', port: '587', ssl: true, username: '', emailFrom: '' },
  };
}

export function mergeAppSettings(saved?: Partial<AppSettings>): AppSettings {
  const defaults = createInitialAppSettings();
  return {
    ...defaults,
    ...saved,
    configuration: { ...defaults.configuration, ...saved?.configuration },
    remoteAccess: { ...defaults.remoteAccess, ...saved?.remoteAccess },
    smtp: { ...defaults.smtp, ...saved?.smtp },
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

export function safeSmtpSettings(value: SmtpSettings & { password?: string }): SmtpSettings {
  return { server: value.server.trim(), port: value.port.trim(), ssl: value.ssl, username: value.username.trim(), emailFrom: value.emailFrom.trim() };
}

export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export const benchmarkResults = {
  duration: '2.4 s / 8.7 s', strategyAverageTime: '0.087 s.', timePerTick: '0.0042 ms.',
  totalTicks: '2,040,000', avgStrategiesPerHour: '41,379',
} as const;
