/** Owner-local presentation/resource documents; no backend execution authority. */
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
  minConditions: number;
  maxPeriods: number;
  minPeriods: number;
  symmetricalRules: boolean;
  fuzzySignals: boolean;
  generateExitRules: boolean;
  stopLoss: boolean;
  profitTarget: boolean;
  slMin: number;
  slMax: number;
  ptMin: number;
  ptMax: number;
  slType: 'Fixed pips' | 'ATR' | 'Percent';
  ptType: 'Fixed pips' | 'ATR' | 'Percent';
  useTrailingStop: boolean;
  trailingStopMin: number;
  trailingStopMax: number;
  useMoveToBE: boolean;
  beTriggerPips: number;
  beProfitOffset: number;
  mmModel: 'Fixed Size' | 'Risk Fixed Amount' | 'Risk % of Equity' | 'Fixed Risk to Return';
  initialCapital: number;
  riskPercent: number;
  fixedLots: number;
  maxGenerations: number;
  migrateCandidates: boolean;
  migrationInterval: number;
  restartStagnantIslands: boolean;
  stagnantGenerations: number;
  seedFromDatabank: boolean;
  inputDatabank: string;
  rankingMetric: string;
  minReturnDD: number;
  minTrades: number;
  maxDrawdownPct: number;
  minSharpe: number;
  minProfitFactor: number;
  crossChecks: CrossCheckItem[];
  customBlocks: Record<string, boolean>;
  precision: string;
  from: string;
  to: string;
  oos: number;
}

export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';

export interface CrossCheckItem {
  id: string;
  name: string;
  enabled: boolean;
}
