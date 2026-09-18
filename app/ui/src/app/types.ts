export type ModuleId = 'home' | 'builder' | 'improver' | 'retester' | 'optimizer' | 'datamanager' | 'algowizard' | 'portfolio' | 'composer' | 'projects' | 'codeeditor' | 'business';
export type ProjectTab = 'progress' | 'settings' | 'results';
export type JobStatus = 'idle' | 'queued' | 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
export type Theme = 'dark' | 'light';

export interface Trade { id: string; strategyId: string; side: 'Long' | 'Short'; entryTime: string; exitTime: string; entry: number; exit: number; size: number; pnl: number; sample: 'IS' | 'OOS'; }
export interface EquityPoint { time: string; value: number; drawdown: number; }
export interface Strategy {
  id: string; name: string; symbol: string; timeframe: string; direction: 'Both' | 'Long' | 'Short'; bankId: string; revision: number; note: string;
  metrics: { netProfit: number; trades: number; profitFactor: number; maxDrawdown: number; sharpe: number; stability: number; };
  trades: Trade[]; equity: EquityPoint[]; parameters: Record<string, number>;
}
export interface Databank { id: string; name: string; strategyIds: string[]; }
export interface Job { id: string; kind: string; status: JobStatus; progress: number; accepted: number; rejected: number; startedAt?: string; message: string; }
export interface Dataset { id: string; source: string; symbol: string; timeframe: string; from: string; to: string; bars: number; quality: number; status: 'Ready' | 'Updating' | 'Error'; }
export interface Instrument { symbol: string; name: string; type: string; pointValue: number; spread: number; session: string; timezone: string; }
export interface RuleNode { id: string; depth: number; kind: 'event' | 'if' | 'then' | 'condition' | 'action'; label: string; }
export interface PortfolioMember { strategyId: string; weight: number; enabled: boolean; sector: string; }
export interface WorkflowTask { id: string; type: string; name: string; enabled: boolean; status: JobStatus; input: string; output: string; }
export interface AppSettings { theme: Theme; language: string; autosave: boolean; workers: number; memoryGb: number; profile: 'Full' | 'Starter'; }
export interface BuilderSettings {
  mode: 'Genetic evolution' | 'Random generation' | 'Improve existing'; strategyType: 'Standard' | 'Multi-TF' | 'Stockpicker'; symbol: string; timeframe: string;
  direction: 'Both' | 'Long' | 'Short'; population: number; islands: number; mutation: number; crossover: number; maxConditions: number;
  stopLoss: boolean; profitTarget: boolean; slMin: number; slMax: number; ptMin: number; ptMax: number; precision: string; from: string; to: string; oos: number;
}
export interface OptimizationSettings { mode: 'Simple' | 'Sequential' | 'Walk-Forward' | 'WF Matrix'; parameter: string; min: number; max: number; step: number; objective: string; keep: number; }
