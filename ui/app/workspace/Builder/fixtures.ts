import type { RuleNode } from './documents';

export const rules: RuleNode[] = [
  { id: 'r1', depth: 0, kind: 'event', label: 'On Bar Open' }, { id: 'r2', depth: 1, kind: 'if', label: 'IF' },
  { id: 'r3', depth: 2, kind: 'condition', label: 'EMA(12) crosses above EMA(28)' }, { id: 'r4', depth: 2, kind: 'condition', label: 'ATR(14) > 0.0012' },
  { id: 'r5', depth: 1, kind: 'then', label: 'THEN' }, { id: 'r6', depth: 2, kind: 'action', label: 'Enter at Market (Long)' },
  { id: 'r7', depth: 2, kind: 'action', label: 'Set Stop Loss: 90 pips' }, { id: 'r8', depth: 2, kind: 'action', label: 'Set Profit Target: 180 pips' },
];

// ---------------------------------------------------------------------------
// SQX-parity Builder "Progress" tab demo state (UI-BUILDER-PROGRESS-004).
// Everything below is presentation fixture data reproducing the donor idle
// and running look (evidence SQX144-EV-000032..037). Values are demo truth
// only; no engine, metric, or chart equivalence is claimed.
// ---------------------------------------------------------------------------

export type EngineRunStatus = 'idle' | 'running' | 'paused';
export type SampleType = 'full' | 'in' | 'out';

export interface ProgressStats {
  strategiesGenerated: number;
  timePerStrategy: string;
  timePerAcceptedStrategy: string;
  rejected: string;
  accepted: string;
  strategiesPerHour: string;
  acceptedPerHour: string;
  runningTime: string;
  inDatabank: number;
}

/** Idle snapshot: every value as the donor renders it before the first start. */
export const idleProgressStats: ProgressStats = {
  strategiesGenerated: 0,
  timePerStrategy: '0 ms.',
  timePerAcceptedStrategy: '0 ms.',
  rejected: '0 / 0.00 %',
  accepted: '0 / 0.00 %',
  strategiesPerHour: '0.00',
  acceptedPerHour: '0.00',
  runningTime: '0 ms.',
  inDatabank: 0,
};

const RUN_EVENTS = [
  'Generating new strategies',
  'Backtesting strategies',
  'Applying acceptance criteria',
  'Cross-check: Retest with higher precision',
  'Updating databank',
];

function ms(seconds: number): string {
  return `${(seconds * 137).toFixed(0)} ms.`;
}

/**
 * Deterministic running snapshot for a mock tick. Stats grow monotonically so
 * the progress dashboard animates like the donor engine channel without any
 * backend or random state (tests rely on the determinism).
 */
export function runFrameAt(tick: number): { lastEvent: string; stats: ProgressStats; logLine: string | null } {
  const t = Math.max(0, tick);
  const generated = 12 * t;
  const acceptedCount = Math.max(0, Math.floor(t / 2) - 1);
  const rejectedCount = generated - acceptedCount;
  const pct = (n: number, total: number) => (total === 0 ? '0.00' : ((n / total) * 100).toFixed(2));
  return {
    lastEvent: RUN_EVENTS[t % RUN_EVENTS.length],
    stats: {
      strategiesGenerated: generated,
      timePerStrategy: ms(t),
      timePerAcceptedStrategy: ms(Math.max(0, t - 1)),
      rejected: `${rejectedCount} / ${pct(rejectedCount, generated)} %`,
      accepted: `${acceptedCount} / ${pct(acceptedCount, generated)} %`,
      strategiesPerHour: (generated * 97.3).toFixed(2),
      acceptedPerHour: (acceptedCount * 97.3).toFixed(2),
      runningTime: `${t} s.`,
      inDatabank: acceptedCount,
    },
    logLine: t === 0 ? 'Project started' : `[${String(t).padStart(2, '0')}] ${RUN_EVENTS[(t - 1) % RUN_EVENTS.length]} (+${12} strategies generated)`,
  };
}

// --- Engine chart panels (donor types observed on the idle screenshot) -----

export const ENGINE_CHART_TYPES = ['Databank Fitness - IS Training', 'Heap memory chart'] as const;
export type EngineChartType = (typeof ENGINE_CHART_TYPES)[number];

export interface FitnessSeries {
  name: string;
  color: string;
  points: number[];
}

/** Demo series for the "Databank Fitness - IS Training" look-alike chart. */
export const databankFitnessSeries: FitnessSeries[] = [
  {
    name: 'Top Strategy',
    color: '#57b93f',
    points: [0.22, 0.38, 0.35, 0.52, 0.61, 0.58, 0.72, 0.8, 0.76, 0.88, 0.84, 0.95, 0.91, 0.97, 1.0, 0.94, 0.98, 0.96, 0.99, 0.97],
  },
  {
    name: 'Top 10 Avg',
    color: '#518ec2',
    points: [0.12, 0.18, 0.22, 0.25, 0.3, 0.34, 0.33, 0.41, 0.45, 0.44, 0.52, 0.55, 0.53, 0.6, 0.62, 0.6, 0.66, 0.64, 0.68, 0.7],
  },
  {
    name: 'All Avg',
    color: '#d9534f',
    points: [0.05, 0.08, 0.07, 0.11, 0.13, 0.12, 0.16, 0.18, 0.17, 0.21, 0.23, 0.22, 0.26, 0.27, 0.26, 0.3, 0.29, 0.32, 0.31, 0.34],
  },
];

/** Demo series for the "Heap memory chart" look-alike (used / max heap GB). */
export const heapMemorySeries = {
  used: [1.9, 2.4, 2.9, 3.6, 3.1, 2.6, 3.2, 3.9, 4.6, 4.0, 3.3, 3.8, 4.5, 5.2, 4.4, 3.7, 4.3, 5.0, 5.7, 4.9, 4.1, 4.8, 5.5, 6.1, 5.3, 4.6, 5.2, 5.9, 6.6, 5.8],
  maxGb: 7.8,
};

// --- Settings summary column ------------------------------------------------

export interface PredefinedConfig {
  label: string;
  info: string;
}

/** Menu entries and tooltip texts of the donor "Use predefined config" menu. */
export const predefinedConfigs: PredefinedConfig[] = [
  { label: 'Default (forex)', info: 'Default build config for forex' },
  { label: 'Default (futures)', info: 'Default build config for futures' },
  { label: 'Default (stockpicker)', info: 'Default build config for stockpicker' },
  { label: 'Market', info: 'Strategies that open at market price, they use almost all available signals and can produce a variety of trading approaches' },
  { label: 'Trend following', info: 'Trend following (breakout) strategies that use stop orders to catch breakouts and go with the trend' },
  { label: 'Mean reversal', info: 'Strategies that are exploiting reversal of price from extreme values to mean' },
  { label: 'Fuzzy', info: 'Strategies using fuzzy logic rules - fuzzy rule has multiple conditions, but only a defined % of them must be valid in order for rule to be triggered' },
  { label: 'Daily', info: 'Daily strategies that place high emphasis on their robustness in multiple markets' },
];

export const dataSettingsFixture = {
  engines: ['MetaTrader5 (hedging mode)', 'MetaTrader5 (netting mode)', 'MetaTrader4', 'Tick data (custom)'],
  engine: 'MetaTrader5 (hedging mode)',
  symbol: 'AUDUSD_dukascopy',
  timeframe: 'D1',
  dateRange: '2026.03.19 - 2026.09.18',
  oosLabel: 'OOS: N/A',
};

export interface BuildOptionRow {
  name: string;
  lines: string[];
}

/** Rendered value summaries of the Build options rows (donor default config). */
export const buildOptionRows: BuildOptionRow[] = [
  {
    name: 'What to build',
    lines: [
      'Simple strategies, SL&PT required, fixed pips',
      'Genetic evolution, 100 generations max. / 4 islands / 100 per island, Restart on finish',
    ],
  },
  { name: 'Building blocks', lines: ['117 entry blocks, 5 exit types'] },
  { name: 'Trading options', lines: ['Exit on Friday'] },
  { name: 'Money Management', lines: ['Fixed size, 0.1 lots'] },
];

export interface CrossCheckItem {
  id: string;
  title: string;
  use: boolean;
}

export interface CrossCheckCategory {
  name: string;
  items: CrossCheckItem[];
}

/**
 * Cross-check tree with the nine installed donor plugin titles in their
 * FAST / SLOW / VERY SLOW categories. "Retest with higher precision" is on in
 * the default config, matching the observed idle screenshot.
 */
export const crossCheckCategories: CrossCheckCategory[] = [
  {
    name: 'FAST',
    items: [
      { id: 'what-if', title: 'What If simulations', use: false },
      { id: 'mc-manipulation', title: 'Monte Carlo trades manipulation', use: false },
      { id: 'higher-precision', title: 'Retest with higher precision', use: true },
    ],
  },
  {
    name: 'SLOW',
    items: [
      { id: 'additional-markets', title: 'Retest on additional markets', use: false },
      { id: 'mc-retest', title: 'Monte Carlo retest', use: false },
      { id: 'sequential-optimization', title: 'Sequential Optimization', use: false },
    ],
  },
  {
    name: 'VERY SLOW',
    items: [
      { id: 'opt-profile', title: 'Opt. Profile / Sys. Param. Permutation', use: false },
      { id: 'wf-optimization', title: 'Walk-Forward Optimization', use: false },
      { id: 'wf-matrix', title: 'Walk-Forward Matrix', use: false },
    ],
  },
];

/** Donor truncates cross-check titles to 32 characters plus a period. */
export function displayCrossCheckTitle(title: string): string {
  return title.length > 32 ? `${title.slice(0, 32)}.` : title;
}

export type CrossCheckTree = CrossCheckCategory[];

/** Pure toggle reducer for one cross-check switch respecting "Disable all". */
export function toggleCrossCheck(tree: CrossCheckTree, id: string, disableAll: boolean): CrossCheckTree {
  return tree.map(category => ({
    ...category,
    items: category.items.map(item =>
      item.id === id && !disableAll ? { ...item, use: !item.use } : item,
    ),
  }));
}

// --- Results column ---------------------------------------------------------

export interface ResultStrategy {
  name: string;
  overview: { label: string; value: string }[];
  equity: number[];
}

function equityCurve(seed: number, n: number, drift: number): number[] {
  let value = 100;
  let state = seed >>> 0;
  const points: number[] = [];
  for (let i = 0; i < n; i++) {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    const noise = ((state / 4294967296) - 0.5) * 6;
    value = Math.max(60, value + drift + noise);
    points.push(Math.round(value * 100) / 100);
  }
  return points;
}

/** Demo "best strategies" for the results column (rankings 0-2). */
export const bestStrategies: ResultStrategy[] = [
  {
    name: 'Strategy 023',
    overview: [
      { label: 'Net profit', value: '$48,412.55' },
      { label: 'Profit factor', value: '1.84' },
      { label: 'Trades', value: '486' },
      { label: 'Max. drawdown', value: '12.37 %' },
      { label: 'Return/DD', value: '2.91' },
      { label: 'Win %', value: '58.4 %' },
      { label: 'Sharpe ratio', value: '1.42' },
      { label: 'Stability', value: '78.2 %' },
    ],
    equity: equityCurve(5100 + 22, 60, 1.9),
  },
  {
    name: 'Strategy 007',
    overview: [
      { label: 'Net profit', value: '$41,177.02' },
      { label: 'Profit factor', value: '1.76' },
      { label: 'Trades', value: '522' },
      { label: 'Max. drawdown', value: '14.02 %' },
      { label: 'Return/DD', value: '2.54' },
      { label: 'Win %', value: '56.1 %' },
      { label: 'Sharpe ratio', value: '1.31' },
      { label: 'Stability', value: '74.6 %' },
    ],
    equity: equityCurve(5100 + 6, 60, 1.6),
  },
  {
    name: 'Strategy 041',
    overview: [
      { label: 'Net profit', value: '$36,940.87' },
      { label: 'Profit factor', value: '1.69' },
      { label: 'Trades', value: '498' },
      { label: 'Max. drawdown', value: '13.55 %' },
      { label: 'Return/DD', value: '2.38' },
      { label: 'Win %', value: '55.3 %' },
      { label: 'Sharpe ratio', value: '1.24' },
      { label: 'Stability', value: '71.9 %' },
    ],
    equity: equityCurve(5100 + 40, 60, 1.4),
  },
];

/** Donor ranking titles for the result cards (0 = best). */
export function resultRankTitle(ranking: number, name: string | null): string {
  if (name === null) return 'No results so far';
  if (ranking === 0) return `Best strategy so far: ${name}`;
  if (ranking === 1) return `2nd Best strategy so far: ${name}`;
  return `3rd Best strategy so far: ${name}`;
}

// --- Fitness evolution modal --------------------------------------------------

/** Demo islands table for the Fitness evolution modal (genetic build). */
export const fitnessIslands = Array.from({ length: 4 }, (_, i) => ({
  generation: 37 + i,
  population: 96 - i * 2,
}));
