/// <reference types="vite/client" />

export type ModuleId = string;

export type ProjectTab = 'progress' | 'settings' | 'results';
export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
export type Theme = 'dark' | 'light';
export type CoreUsage = 'single' | 'reserve-one' | 'custom' | 'maximum';
export type GarbageCollector = 'parallel' | 'g1' | 'automatic';
export type ResultPreference = 'portfolio' | 'main';

export interface ConfigurationSettings {
  soundsOff: boolean;
  rememberFileChooser: boolean;
  showControlOrders: boolean;
  headerCustomText: string;
  footerCustomText: string;
  defaultResult: ResultPreference;
  totalCores: number;
  coreUsage: CoreUsage;
  customCores: number;
  highPriority: boolean;
  threadAffinity: boolean;
  computePipsMetrics: boolean;
  computePercentMetrics: boolean;
  computeSeparateMetrics: boolean;
  garbageCollector: GarbageCollector;
  automaticMemory: boolean;
  memoryGb: number;
  dontStorePendingOrders: boolean;
  memoryCleanup: boolean;
  cleanupInterval: '5 minutes' | '15 minutes' | '30 minutes' | '1 hour';
  databankSyncInterval: 'Never' | 'Immediately' | 'Every 5 minutes' | 'Every 10 minutes' | 'Every 15 minutes' | 'Every hour';
  syncDatabanksAfterTask: boolean;
  storeChartData: boolean;
  dontStoreOptimization3d: boolean;
  gpuAccelerated: boolean;
  memoryProtection: boolean;
  debugLevel: boolean;
}

export interface RemoteAccessSettings {
  allow: boolean;
  requirePassword: boolean;
}

export interface SmtpSettings {
  server: string;
  port: string;
  ssl: boolean;
  username: string;
  emailFrom: string;
}

export interface AppSettings {
  theme: Theme;
  language: string;
  autosave: boolean;
  workers: number;
  memoryGb: number;
  profile: 'Full' | 'Starter';
  zoom: number;
  configuration: ConfigurationSettings;
  remoteAccess: RemoteAccessSettings;
  smtp: SmtpSettings;
}
