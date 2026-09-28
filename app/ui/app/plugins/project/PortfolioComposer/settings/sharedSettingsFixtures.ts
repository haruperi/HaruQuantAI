/** Local presentation defaults, not quantitative schemas. */
export interface OosRange {
  type: 'IST' | 'ISV' | 'OOS';
  from: string;
  to: string;
}

export interface DataTabState {
  engine: string;
  symbol: string;
  timeframe: string;
  dateFrom: string;
  dateTo: string;
  oosRanges: OosRange[];
}

/** The five donor "Most used configs" presets (title texts from tooltips). */
export const oosPresets: { id: number; label: string; title: string }[] = [
  { id: 1, label: '50/20/30', title: 'IST: 50, ISV: 20, OOS: 30' },
  { id: 2, label: '30/20/50', title: 'OOS: 30, ISV: 20, IST: 50' },
  { id: 3, label: '20/20/10 x2', title: 'IST: 20, ISV: 20, OOS:10, IST: 20, ISV: 20, OOS:10' },
  { id: 4, label: 'alternating ISV', title: 'IST,ISV,IST,ISV,IST,ISV,IST,ISV,IST,ISV,IST,ISV,IST,ISV,IST,ISV,IST,ISV,IST,ISV,OOS:30' },
  { id: 5, label: 'alternating OOS', title: 'IST,OOS,IST,OOS,IST,OOS,IST,OOS,IST,OOS,IST,OOS,IST,OOS,IST,OOS,IST,OOS,IST,OOS' },
];

export const dataTabDefaults: DataTabState = {
  engine: 'MetaTrader5 (hedging mode)',
  symbol: 'AUDUSD_dukascopy',
  timeframe: 'D1',
  dateFrom: '2026.03.19',
  dateTo: '2026.09.18',
  oosRanges: [
    { type: 'IST', from: '2026.03.19', to: '2026.06.05' },
    { type: 'ISV', from: '2026.06.05', to: '2026.07.28' },
    { type: 'OOS', from: '2026.07.28', to: '2026.09.18' },
  ],
};

/** Percent of the total date range per OOS part (for the "(N%)" labels). */
export function oosRangePercents(ranges: OosRange[]): number[] {
  const times = ranges.map(r => new Date(r.to).getTime() - new Date(r.from).getTime());
  const total = times.reduce((a, b) => a + b, 0) || 1;
  return times.map(t => Math.round((t / total) * 100));
}

// --- Trading options --------------------------------------------------------------

export interface TradingOptionProperty {
  key: string;
  label: string;
  type: 'checkbox' | 'spinner' | 'time' | 'select';
  value: boolean | number | string;
  options?: string[];
}

/** Entries and defaults from the donor BuildTradingOptions params. */
export const tradingOptionsDefaults: TradingOptionProperty[] = [
  { key: 'ExitAtEndOfDay', label: 'Exit at end of day', type: 'checkbox', value: false },
  { key: 'EODExitTime', label: 'End of day exit time', type: 'time', value: 82800 },
  { key: 'ExitOnFriday', label: 'Exit on Friday', type: 'checkbox', value: false },
  { key: 'FridayExitTime', label: 'Friday exit time', type: 'time', value: 82800 },
  { key: 'LimitTimeRange', label: 'Limit time range', type: 'checkbox', value: false },
  { key: 'SignalTimeRangeFrom', label: 'Signal time range from', type: 'time', value: 32400 },
  { key: 'SignalTimeRangeTo', label: 'Signal time range to', type: 'time', value: 57600 },
  { key: 'ExitAtEndOfRange', label: 'Exit at end of range', type: 'checkbox', value: false },
  { key: 'MaxTradesPerDay', label: 'Max trades per day', type: 'spinner', value: 1 },
  { key: 'Session', label: 'Session', type: 'select', value: 'No Session', options: ['No Session', 'New York', 'London', 'Tokyo', 'Sydney'] },
  { key: 'StoreChartData', label: 'Store chart data', type: 'checkbox', value: false },
];

/** Seconds of day -> "HH:MM" for the time properties. */
export function formatTimeOfDay(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// --- Money management ----------------------------------------------------------------

export interface MmMethod {
  key: string;
  label: string;
  use: boolean;
  params: { key: string; label: string; value: string }[];
}

/** Methods and defaults from the donor template's MoneyManagement section. */
export const moneyManagementDefaults: { initialCapital: number; methods: MmMethod[] } = {
  initialCapital: 10000,
  methods: [
    { key: 'FixedSize', label: 'FixedSize', use: true, params: [{ key: 'Size', label: 'Size', value: '0.1' }] },
    { key: 'RiskFixedBalancePct', label: 'RiskFixedBalancePct', use: false, params: [{ key: 'Risk', label: 'Risk', value: '5' }, { key: 'Decimals', label: 'Decimals', value: '1' }, { key: 'LotsIfNoMM', label: 'Lots if no MM', value: '1' }, { key: 'MaxLots', label: 'Max lots', value: '5.1' }] },
    { key: 'FixedAmount', label: 'FixedAmount', use: false, params: [{ key: 'RiskedMoney', label: 'Risked money', value: '500' }, { key: 'Decimals', label: 'Decimals', value: '1' }, { key: 'LotsIfNoMM', label: 'Lots if no MM', value: '1' }, { key: 'MaxLots', label: 'Max lots', value: '5' }] },
    { key: 'RiskFixedPctOfAccount', label: 'RiskFixedPctOfAccount', use: false, params: [{ key: 'Risk', label: 'Risk', value: '5' }, { key: 'Decimals', label: 'Decimals', value: '1' }, { key: 'StopLoss', label: 'Stop loss', value: '100' }, { key: 'LotsIfNoMM', label: 'Lots if no MM', value: '1' }, { key: 'MaxLots', label: 'Max lots', value: '5' }] },
    { key: 'StocksSizeByPrice', label: 'StocksSizeByPrice', use: false, params: [{ key: 'UseAccountBalance', label: 'Use account balance', value: 'true' }, { key: 'MaxSize', label: 'Max size', value: '100' }] },
  ],
};

// --- Building blocks ---------------------------------------------------------------------

export interface AtmMethod {
  key: string;
  label: string;
  use: boolean;
  params: { key: string; label: string; value: number }[];
}

/** Demo ATM surface derived from the donor template's exit formulas. */
export const atmDefaults: AtmMethod[] = [
  { key: 'stopLoss', label: 'Stop Loss', use: true, params: [{ key: 'min', label: 'Min (pips)', value: 20 }, { key: 'max', label: 'Max (pips)', value: 120 }] },
  { key: 'profitTarget', label: 'Profit Target', use: true, params: [{ key: 'min', label: 'Min (pips)', value: 40 }, { key: 'max', label: 'Max (pips)', value: 240 }] },
  { key: 'moveSl2Be', label: 'Move SL to BE', use: false, params: [{ key: 'addPips', label: 'Add pips', value: 0 }] },
  { key: 'trailingStop', label: 'Trailing Stop', use: false, params: [{ key: 'activation', label: 'Activation level', value: 30 }] },
  { key: 'exitAfterBars', label: 'Exit After Bars', use: false, params: [{ key: 'bars', label: 'Bars', value: 10 }] },
];

// --- Cross checks tab --------------------------------------------------------------------------

export interface CrossCheckTabItem {
  id: string;
  title: string;
  use: boolean;
  section: 0 | 1 | 2;
  settingsInfo: string;
  acceptInfo: string;
}

export const crossChecksTabSectionTitles: { section: 0 | 1 | 2; title: string; desc: string }[] = [
  { section: 0, title: 'Basic (fast)', desc: 'These cross checks require none or only one additional backtest, so they are fast.' },
  { section: 1, title: 'Standard (slow)', desc: 'Cross checks that require multiple additional backtests, thus multiplying the time of processing the whole strategy.' },
  { section: 2, title: 'Extensive (slowest)', desc: 'Walk-Forward process is very slow, it requires tens or even hundreds of repeated backtests of the strategy in different time ranges and settings.' },
];

/** The nine installed cross checks with demo summary cells (donor rows are backend-fed). */
export const crossChecksTabDefaults: CrossCheckTabItem[] = [
  { id: 'what-if', title: 'What If simulations', use: false, section: 0, settingsInfo: '3 simulation(s)', acceptInfo: 'Accept if: profit > 0' },
  { id: 'mc-manipulation', title: 'Monte Carlo trades manipulation', use: false, section: 0, settingsInfo: '10 simulations', acceptInfo: 'Accept if: DD < 30%' },
  { id: 'higher-precision', title: 'Retest with higher precision', use: true, section: 0, settingsInfo: 'Precision: Real ticks', acceptInfo: 'Accept if: profit > 0' },
  { id: 'additional-markets', title: 'Retest on additional markets', use: false, section: 1, settingsInfo: '2 markets', acceptInfo: 'Accept if: profit > 0' },
  { id: 'mc-retest', title: 'Monte Carlo retest', use: false, section: 1, settingsInfo: '10 simulations', acceptInfo: 'Accept if: profit > 0' },
  { id: 'sequential-optimization', title: 'Sequential Optimization', use: false, section: 1, settingsInfo: '2 steps', acceptInfo: 'Accept if: WF result valid' },
  { id: 'opt-profile', title: 'Opt. Profile / Sys. Param. Permutation', use: false, section: 2, settingsInfo: 'Permutation', acceptInfo: 'Accept if: profile OK' },
  { id: 'wf-optimization', title: 'Walk-Forward Optimization', use: false, section: 2, settingsInfo: '10 runs', acceptInfo: 'Accept if: WF profit > 0' },
  { id: 'wf-matrix', title: 'Walk-Forward Matrix', use: false, section: 2, settingsInfo: '3x3 matrix', acceptInfo: 'Accept if: WF profit > 0' },
];

// --- Ranking ----------------------------------------------------------------------------------

export interface RankingState {
  maxStrategies: number;
  stopConditionType: 'never' | 'passedCount' | 'databankFull' | 'timeLimit';
  passedStrategies: number;
  days: number;
  hours: number;
  minutes: number;
  fitnessCriteria: { key: string; label: string }[];
}

export const rankingDefaults: RankingState = {
  maxStrategies: 100,
  stopConditionType: 'never',
  passedStrategies: 100,
  days: 0,
  hours: 8,
  minutes: 0,
  fitnessCriteria: [{ key: 'ReturnDDRatio', label: 'Return / Drawdown' }],
};

/** Donor fitness method options (installed methods list). */
export const fitnessMethods: { value: string; label: string }[] = [
  { value: 'ComputeFromStrategyResult', label: 'Compute from strategy result' },
  { value: 'ReturnDDRatio', label: 'Return / Drawdown' },
  { value: 'NetProfit', label: 'Net profit' },
  { value: 'ProfitFactor', label: 'Profit factor' },
  { value: 'SharpeRatio', label: 'Sharpe ratio' },
  { value: 'Stability', label: 'Stability' },
  { value: 'Custom', label: 'Custom formula' },
];

// --- Parts to improve ---------------------------------------------------------------------------
