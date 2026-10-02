/// <reference types="vite/client" />

export type ModuleId = string;

export type ProjectTab = 'progress' | 'settings' | 'results';
export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
export type Theme = 'dark' | 'light';
export type CoreUsage = 'single' | 'reserve-one' | 'custom' | 'maximum';
export type GarbageCollector = 'parallel' | 'g1' | 'automatic';
export type ResultPreference = 'portfolio' | 'main';

export interface Mt5Settings {
  enabled: boolean;
  terminalPath: string;
  accountId: string;
  password: string;
  server: string;
  environment: 'demo' | 'live' | 'real';
  timeoutMs: number;
  portable: boolean;
  useTicks: boolean;
}

export interface CtraderSettings {
  enabled: boolean;
  clientId: string;
  clientSecret: string;
  accessToken: string;
  refreshToken: string;
  redirectUrl: string;
  environment: 'demo' | 'live' | 'real';
  accountId: string;
  gatewayHost: string;
  gatewayPort: number;
}

export interface GeminiAgentConfig {
  apiKey: string;
  model: string;
  fastModel: string;
  premiumModel: string;
  fallbackModel: string;
  temperature: number;
  maxTokens: number;
  useVertexAi: boolean;
}

export interface OpenAiAgentConfig {
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

export interface OllamaAgentConfig {
  baseUrl: string;
  model: string;
  temperature: number;
  timeoutSeconds: number;
}

export interface AgentSettings {
  activeProvider: 'gemini' | 'openai' | 'ollama';
  gemini: GeminiAgentConfig;
  openai: OpenAiAgentConfig;
  ollama: OllamaAgentConfig;
  systemPromptPreset: string;
  agentTimeoutSeconds: number;
}

export interface DirectoriesSettings {
  configsDir: string;
  projectsDir: string;
  strategiesDir: string;
  customdataDir: string;
}

export interface BacktestEngineSettings {
  maxThreads: number;
  memoryLimitMb: number;
  enableCaching: boolean;
  precisionMode: 'high' | 'standard' | 'low';
  benchmarkTimePerTickMs: number;
  dontStorePendingOrders: boolean;
  dontStoreOp3dCharts: boolean;
  computeSeparateMetrics: boolean;
  computePctsMetrics: boolean;
  computePipsMetrics: boolean;
  sourceCodeConstantsParams: boolean;
}

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
  mt5: Mt5Settings;
  ctrader: CtraderSettings;
  agents: AgentSettings;
  directories: DirectoriesSettings;
  backtestEngine: BacktestEngineSettings;
}

export interface RemoteAccessSettings {
  allow: boolean;
  requirePassword: boolean;
}

export interface SmtpSettings {
  enabled: boolean;
  server: string;
  port: string;
  ssl: boolean;
  username: string;
  emailFrom: string;
}

export interface TelegramSettings {
  enabled: boolean;
  chatId: string;
  parseMode: 'HTML' | 'Markdown' | 'MarkdownV2';
  disableNotification: boolean;
}

export interface DesktopNotificationSettings {
  enabled: boolean;
  soundEnabled: boolean;
  durationSeconds: number;
  minPriority: 'low' | 'normal' | 'high' | 'critical';
}

export interface McpSettings {
  enabled: boolean;
  host: string;
  port: number;
  transport: 'sse' | 'stdio' | 'websocket' | 'http';
  allowedTools: string[];
  maxContextItems: number;
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
  telegram: TelegramSettings;
  desktopNotification: DesktopNotificationSettings;
  mcp: McpSettings;
}
