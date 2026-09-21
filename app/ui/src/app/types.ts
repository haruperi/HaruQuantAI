export type ModuleId =
  | 'home'
  | 'builder'
  | 'retester'
  | 'optimizer'
  | 'datamanager'
  | 'algowizard'
  | 'portfolio'
  | 'composer'
  | 'projects'
  | 'codeeditor'
  | 'business'
  | 'trading'
  | 'neuralnet'
  | 'mtanalyzer'
  | 'debugconsole'
  | 'gridcontrol';

export type ProjectTab = 'progress' | 'settings' | 'results';
export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
export type Theme = 'dark' | 'light';
export type CoreUsage = 'single' | 'reserve-one' | 'custom' | 'maximum';
export type GarbageCollector = 'parallel' | 'g1' | 'automatic';
export type ResultPreference = 'portfolio' | 'main';

export interface Trade {
  id: string;
  strategyId: string;
  side: 'Long' | 'Short';
  entryTime: string;
  exitTime: string;
  entry: number;
  exit: number;
  size: number;
  pnl: number;
  sample: 'IS' | 'OOS';
}

export interface EquityPoint {
  time: string;
  value: number;
  drawdown: number;
}

export interface Strategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  direction: 'Both' | 'Long' | 'Short';
  bankId: string;
  revision: number;
  note: string;
  metrics: {
    netProfit: number;
    trades: number;
    profitFactor: number;
    maxDrawdown: number;
    sharpe: number;
    stability: number;
  };
  trades: Trade[];
  equity: EquityPoint[];
  parameters: Record<string, number>;
}

export interface Databank {
  id: string;
  name: string;
  strategyIds: string[];
}

export interface Job {
  id: string;
  kind: string;
  status: JobStatus;
  progress: number;
  accepted: number;
  rejected: number;
  startedAt?: string;
  message: string;
}

export interface Dataset {
  id: string;
  source: string;
  symbol: string;
  timeframe: string;
  from: string;
  to: string;
  bars: number;
  quality: number;
  status: 'Ready' | 'Updating' | 'Error';
}

export interface Instrument {
  symbol: string;
  name: string;
  type: string;
  pointValue: number;
  spread: number;
  session: string;
  timezone: string;
}

export interface RuleNode {
  id: string;
  depth: number;
  kind: 'event' | 'if' | 'then' | 'condition' | 'action';
  label: string;
}

export interface PortfolioMember {
  strategyId: string;
  weight: number;
  enabled: boolean;
  sector: string;
}

export interface WorkflowTask {
  id: string;
  type: string;
  name: string;
  enabled: boolean;
  status: JobStatus;
  input: string;
  output: string;
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
  databankSyncInterval: 'Never' | 'Immediately' | 'Every 5 minutes' | 'Every 15 minutes' | 'Every hour';
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

export interface BuilderSettings {
  mode: 'Genetic evolution' | 'Random generation' | 'Improve existing';
  strategyType: 'Standard' | 'Multi-TF' | 'Stockpicker';
  symbol: string;
  timeframe: string;
  direction: 'Both' | 'Long' | 'Short';
  population: number;
  islands: number;
  mutation: number;
  crossover: number;
  maxConditions: number;
  stopLoss: boolean;
  profitTarget: boolean;
  slMin: number;
  slMax: number;
  ptMin: number;
  ptMax: number;
  precision: string;
  from: string;
  to: string;
  oos: number;
}

export interface OptimizationSettings {
  mode: 'Simple' | 'Sequential' | 'Walk-Forward' | 'WF Matrix';
  parameter: string;
  min: number;
  max: number;
  step: number;
  objective: string;
  keep: number;
}

/* -------------------------------------------------------------------------- */
/* LIVE TRADING TYPES (FEAT-UI-TRADING)                                       */
/* -------------------------------------------------------------------------- */
export type OrderSide = 'Buy' | 'Sell';
export type OrderKind = 'Market' | 'Limit' | 'Stop';

export interface Position {
  id: string;
  ticket: number;
  symbol: string;
  side: OrderSide;
  lots: number;
  openPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  swap: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  magicNumber: number;
  comment: string;
}

export interface PendingOrder {
  id: string;
  ticket: number;
  symbol: string;
  kind: 'Buy Limit' | 'Sell Limit' | 'Buy Stop' | 'Sell Stop';
  lots: number;
  orderPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  expiration: string;
  magicNumber: number;
  comment: string;
}

export interface BrokerAccount {
  id: string;
  broker: string;
  accountNumber: string;
  server: string;
  connected: boolean;
  latencyMs: number;
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  marginLevel: number;
  currency: string;
  leverage: number;
}

export interface ExecutionLogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
  source: string;
  message: string;
}

/* -------------------------------------------------------------------------- */
/* NEURAL NETWORK TYPES (FEAT-UI-NEURAL-NETWORK)                              */
/* -------------------------------------------------------------------------- */
export type NNActivation = 'ReLU' | 'LeakyReLU' | 'Sigmoid' | 'Tanh' | 'Linear' | 'ELU';
export type NNOptimizer = 'Adam' | 'SGD' | 'RMSprop' | 'AdaGrad';
export type NNLossFunction = 'Mean Squared Error' | 'Binary CrossEntropy' | 'Categorical CrossEntropy';

export interface NNLayerConfig {
  id: string;
  name: string;
  type: 'input' | 'dense' | 'dropout' | 'output';
  neurons: number;
  activation: NNActivation;
  dropoutRate?: number;
}

export interface NNTrainingConfig {
  modelName: string;
  symbol: string;
  timeframe: string;
  inputFeatures: string[];
  layers: NNLayerConfig[];
  epochs: number;
  batchSize: number;
  learningRate: number;
  optimizer: NNOptimizer;
  lossFunction: NNLossFunction;
  trainSplit: number;
  valSplit: number;
  testSplit: number;
  earlyStoppingPatience: number;
}

export interface NNTrainingHistoryPoint {
  epoch: number;
  loss: number;
  valLoss: number;
  accuracy: number;
  valAccuracy: number;
}

export interface NNEvaluationMetrics {
  testLoss: number;
  testAccuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  confusionMatrix: [[number, number], [number, number]];
}

/* -------------------------------------------------------------------------- */
/* MT ANALYZER TYPES (FEAT-UI-MT-ANALYZER)                                    */
/* -------------------------------------------------------------------------- */
export interface MTStatementTrade {
  ticket: number;
  openTime: string;
  type: 'buy' | 'sell';
  size: number;
  item: string;
  openPrice: number;
  closeTime: string;
  closePrice: number;
  commission: number;
  swap: number;
  profit: number;
  pips: number;
  comment?: string;
  magicNumber?: number;
}

export interface MTAnalysisMetrics {
  initialDeposit: number;
  totalNetProfit: number;
  grossProfit: number;
  grossLoss: number;
  profitFactor: number;
  expectedPayoff: number;
  absoluteDrawdown: number;
  maximalDrawdown: number;
  maximalDrawdownPercent: number;
  totalTrades: number;
  winRate: number;
  profitTrades: number;
  lossTrades: number;
  averageProfit: number;
  averageLoss: number;
  profitRatio: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
  sharpeRatio: number;
  sqn: number;
}

export interface MTFilterOptions {
  symbol: string;
  magicNumber: string;
  comment: string;
  excludeBalanceOrders: boolean;
}

/* -------------------------------------------------------------------------- */
/* 3D OPTIMIZATION SURFACE TYPES (FEAT-UI-3DSURFACE)                          */
/* -------------------------------------------------------------------------- */
export interface SurfacePoint {
  x: number;
  y: number;
  z: number;
  xParam: string;
  yParam: string;
  zMetric: string;
}

export interface PlateauCluster {
  id: string;
  centerParamX: number;
  centerParamY: number;
  rangeX: [number, number];
  rangeY: [number, number];
  averageMetric: number;
  standardDeviation: number;
  stabilityScore: number;
  profitablePercentage: number;
}
