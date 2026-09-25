/**
 * SQX-parity Builder "Full settings" demo state (UI-BUILDER-SETTINGS-005).
 * Tab registry, descriptions, help URLs, and default values follow the
 * installed donor sources (evidence SQX144-EV-000038..043); numeric defaults
 * come from the donor's installed Build task template (genetic evolution:
 * 100 generations / 100 population / 4 islands). Everything is local fixture
 * truth — no engine or persistence claims.
 */

export interface SettingsTabMeta {
  id: string;
  title: string;
  help: string;
  helpUrl: string;
}

const DOCS = 'https://strategyquant.com/doc/strategyquant';

/** Build-task settings tabs; Parts to improve is conditional (SQX144-EV-000055..056). */
export const settingsTabs: SettingsTabMeta[] = [
  { id: 'what-to-build', title: 'What to build', help: 'Choose what kind of strategy to build, its style, build mode, number of conditions in a strategy and Stop Loss + Profit Target ranges.', helpUrl: `${DOCS}/what-to-build/` },
  { id: 'parts-to-improve', title: 'Parts to improve', help: 'Configure which parts of the strategy should be improved. You can further configure if you want to replace the whole part, or add new blocks to it.', helpUrl: `${DOCS}/parts-to-improve/` },
  { id: 'genetic-options', title: 'Genetic options', help: 'Configure Genetic options', helpUrl: `${DOCS}/genetic-options/` },
  { id: 'data', title: 'Data', help: 'Configure trading engine, symbols and timeframes for the main backtest. You can configure also Out of sample (unseen) periods, and default spread, slippage, commissions.', helpUrl: `${DOCS}/data/` },
  { id: 'trading-options', title: 'Trading options', help: 'Trading options define behavior of the strategy and affect how and when strategy trades. You can limit trading time to a range, close the trade at the end of range or limit maximum trades per day.', helpUrl: `${DOCS}/trading-options/` },
  { id: 'building-blocks', title: 'Building blocks', help: 'Here you can choose the building blocks that will be used to generate every strategy. You can affect the probability of choosing a block by increasing its weight.<br>Every block has also advanced parameter settings that allow you to modify how block parameters are generated or define some predefined parameter sets to choose from.', helpUrl: `${DOCS}/building-blocks/` },
  { id: 'atm', title: 'ATM', help: 'Advanced Trading Management', helpUrl: `${DOCS}/settings-atm/` },
  { id: 'money-management', title: 'Money management', help: 'Configure initial capital and desired position sizing method.', helpUrl: `${DOCS}/money-management/` },
  { id: 'cross-checks', title: 'Cross checks (robustness)', help: '', helpUrl: `${DOCS}/cross-checks-automated-strategy-robustness-tests/` },
  { id: 'ranking', title: 'Ranking', help: 'Define how strategy rank is computed and how many strategies to save to databank.<br/>If filtering is available you can configure filters the strategy has to pass before it is saved.', helpUrl: `${DOCS}/ranking-options/` },
  { id: 'notes', title: 'Notes', help: 'Save some notes about this configuration', helpUrl: `${DOCS}/notes/` },
];

/** Donor prev/next label rule: "< {title}" and "{title} >". */
export function visibleSettingsTabs(strategyType: StrategyType): SettingsTabMeta[] {
  return settingsTabs.filter(tab => tab.id !== "parts-to-improve" || strategyType === "improve");
}

export function prevTabLabel(index: number, tabs = settingsTabs): string | null {
  return index > 0 ? `< ${tabs[index - 1].title}` : null;
}

export function nextTabLabel(index: number, tabs = settingsTabs): string | null {
  return index < tabs.length - 1 ? `${tabs[index + 1].title} >` : null;
}

// --- What to build -----------------------------------------------------------

export type StrategyType = 'simple' | 'multiTf' | 'template' | 'improve';

export interface WhatToBuildState {
  strategyType: StrategyType;
  additionalCharts: number;
  templateFile: string;
  improveType: 'strategy' | 'databank';
  tradingDirections: { type: 'both' | 'long' | 'short'; entrySymmetry: boolean; exitSymmetry: boolean };
  strategyStyle: { type: 'sq4' | 'sq4Fuzzy' | 'sq3'; minTrue: number; maxTrue: number };
  buildMode: { generationType: 'genetic-evolution' | 'random-generation'; population: number; maxGenerations: number; islands: number; restartOnFinish: boolean };
  conditions: { minConditions: number; maxConditions: number; maxLookback: number; minPeriod: number; maxPeriod: number };
  stopLoss: { required: boolean; fixedPips: boolean; minPips: number; maxPips: number; percent: boolean; minPercent: number; maxPercent: number; atr: boolean };
  profitTarget: { required: boolean; sameAsSl: boolean; fixedPips: boolean; minPips: number; maxPips: number };
}

export const whatToBuildDefaults: WhatToBuildState = {
  strategyType: 'simple',
  additionalCharts: 2,
  templateFile: 'SQ3StrategyTemplateExample.sq4',
  improveType: 'strategy',
  tradingDirections: { type: 'both', entrySymmetry: true, exitSymmetry: true },
  strategyStyle: { type: 'sq4', minTrue: 60, maxTrue: 100 },
  buildMode: { generationType: 'genetic-evolution', population: 100, maxGenerations: 100, islands: 4, restartOnFinish: true },
  conditions: { minConditions: 1, maxConditions: 12, maxLookback: 10, minPeriod: 10, maxPeriod: 100 },
  stopLoss: { required: true, fixedPips: true, minPips: 20, maxPips: 120, percent: false, minPercent: 0.5, maxPercent: 5, atr: false },
  profitTarget: { required: true, sameAsSl: false, fixedPips: true, minPips: 40, maxPips: 240 },
};

/** The six "Additional build config" rows in donor position order. */
export const additionalConfigRowIds = ['tradingDirections', 'strategyStyle', 'buildMode', 'conditions', 'stopLoss', 'profitTarget'] as const;
export type AdditionalConfigRowId = (typeof additionalConfigRowIds)[number];

export const additionalConfigRowNames: Record<AdditionalConfigRowId, string> = {
  tradingDirections: 'Trading directions',
  strategyStyle: 'Strategy style',
  buildMode: 'Build mode',
  conditions: '# of Conditions, Periods',
  stopLoss: 'Stop Loss',
  profitTarget: 'Profit Target',
};

/** Donor getDescription logic per row (paraphrased shapes, fixture values). */
export function describeAdditionalConfig(state: WhatToBuildState, row: AdditionalConfigRowId): string {
  switch (row) {
    case 'tradingDirections': {
      const d = state.tradingDirections;
      if (d.type === 'long') return 'Long only';
      if (d.type === 'short') return 'Short only';
      let text = 'Both (Long & Short)';
      if (!d.entrySymmetry && !d.exitSymmetry) text += ', No symmetry';
      else {
        if (d.entrySymmetry) text += ', Entry symmetry';
        if (d.exitSymmetry) text += ', Exit symmetry';
      }
      return text;
    }
    case 'strategyStyle': {
      const s = state.strategyStyle;
      if (s.type === 'sq4Fuzzy') return `SQX Signals with Fuzzy Logic, True conditions: ${s.minTrue}-${s.maxTrue} %`;
      if (s.type === 'sq3') return 'Old SQ3 architecture';
      return 'SQX Signals';
    }
    case 'buildMode': {
      const b = state.buildMode;
      if (b.generationType === 'random-generation') return 'Random generation';
      return `Genetic evolution, ${b.maxGenerations} generations max. / ${b.islands} islands / ${b.population} per island${b.restartOnFinish ? ', Restart on finish' : ''}`;
    }
    case 'conditions': {
      const c = state.conditions;
      return `Conditions to generate: ${c.minConditions}-${c.maxConditions}, Max lookback period: ${c.maxLookback}, Indicator periods: ${c.minPeriod}-${c.maxPeriod}`;
    }
    case 'stopLoss': {
      const s = state.stopLoss;
      let text = s.required ? 'Required' : 'Not required';
      if (s.fixedPips) text += `, Pips based: ${s.minPips}-${s.maxPips} pips`;
      if (s.percent) text += `, Percent based: ${s.minPercent}%-${s.maxPercent}%`;
      if (s.atr) text += ', ATR based';
      return text;
    }
    case 'profitTarget': {
      const p = state.profitTarget;
      let text = p.required ? 'Required' : 'Not required';
      if (p.sameAsSl) text += ', same ranges as SL';
      else if (p.fixedPips) text += `, Pips based: ${p.minPips}-${p.maxPips} pips`;
      return text;
    }
  }
}

// --- Genetic options -----------------------------------------------------------

export interface GeneticOptionsState {
  maxGenerations: number;
  populationSize: number;
  crossoverProbability: number;
  mutationProbability: number;
  islands: number;
  migrationModulo: number;
  migrationRate: number;
  useInitialPopulationDatabank: boolean;
  decimationCoef: number;
  freshBloodReplaceSimilar: boolean;
  freshBloodWeakestPct: number;
  freshBloodWeakestGenerations: number;
  showLastGenerationDatabank: boolean;
  restartOnFinish: boolean;
  restartOnStagnation: boolean;
  stagnationGenerations: number;
}

/** Numeric defaults from the installed donor Build task template. */
export const geneticOptionsDefaults: GeneticOptionsState = {
  maxGenerations: 100,
  populationSize: 100,
  crossoverProbability: 93,
  mutationProbability: 30,
  islands: 4,
  migrationModulo: 87,
  migrationRate: 6,
  useInitialPopulationDatabank: false,
  decimationCoef: 5,
  freshBloodReplaceSimilar: true,
  freshBloodWeakestPct: 10,
  freshBloodWeakestGenerations: 50,
  showLastGenerationDatabank: true,
  restartOnFinish: true,
  restartOnStagnation: false,
  stagnationGenerations: 20,
};

// --- Data tab -------------------------------------------------------------------

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

export interface BlockEntry {
  key: string;
  category: 'indicators' | 'orderTypes' | 'exitTypes' | 'signals' | 'stopLimit' | 'customData';
  use: boolean;
  weight: number;
}

/**
 * Catalog derived from the donor Build template's block entries
 * (BuildingBlocks / OrderTypes / ExitTypes). Signals, Stop & Limit and
 * Custom data sections carry small labelled demo lists (engine-fed in the
 * donor, not present in client source).
 */
export const buildingBlocksCatalog: BlockEntry[] = [
  // indicators (from template BuildingBlocks; use/weight defaults)
  ...['ADX', 'AwesomeOscillator', 'BearsPower', 'BullsPower', 'CCI', 'ChaikinMoneyFlow', 'ChaikinVolatility', 'ChandelierExit', 'CommodityChannelIndex', 'DEMA', 'DonchianChannel', 'EMA', 'Envelopes', 'Fractals', 'HeikenAshi', 'HighestHigh', 'HighestValue', 'IchimokuClouds', 'KeltnerChannel', 'LinearRegression', 'LowestLow', 'LowestValue', 'MACD', 'MassIndex', 'MedianPrice', 'Momentum', 'MovingAverage', 'OBV', 'PatternBollingerBands', 'Price', 'Range', 'ROC', 'RSI', 'RSquared', 'SAR', 'SMA', 'SMMA', 'Stochastic', 'SuperTrend', 'TEMA', 'TMA', 'TRIX', 'TypicalPrice', 'UltimateOscillator', 'VIDYA', 'Volume', 'VWAP', 'WeightedClose', 'WilliamsR', 'ZigZag'].map(key => ({ key, category: 'indicators' as const, use: true, weight: 1 })),
  // order types
  ...['EnterAtMarket', 'EnterAtLimit', 'EnterAtStop', 'EnterOnNewBar'].map(key => ({ key, category: 'orderTypes' as const, use: key === 'EnterAtMarket', weight: 1 })),
  // exit types
  { key: 'ExitAfterBars.ExitAfterBars', category: 'exitTypes', use: true, weight: 1 },
  { key: 'MoveSL2BE.MoveSL2BE', category: 'exitTypes', use: false, weight: 1 },
  { key: 'MoveSL2BE.SL2BEAddPips', category: 'exitTypes', use: false, weight: 1 },
  // demo-only sections (engine-fed in the donor)
  ...['CCI(14) is rising', 'Momentum(20) crosses above 0', 'PiercingLine pattern', 'RSI(14) is falling', 'Price crosses above SMA(50)'].map(key => ({ key, category: 'signals' as const, use: true, weight: 1 })),
  ...['Stop Loss (pips)', 'Stop Loss (%)', 'Stop Loss (ATR)', 'Profit Target (pips)', 'Profit Target (%)'].map(key => ({ key, category: 'stopLimit' as const, use: true, weight: 1 })),
  ...['Day of week', 'Time of day', 'Market session'].map(key => ({ key, category: 'customData' as const, use: false, weight: 1 })),
];

export interface BlocksSection {
  id: string;
  title: string;
  countLabel: string;
  help: string;
  category: BlockEntry['category'];
}

/** Accordion sections in donor order. */
export const blocksSections: BlocksSection[] = [
  { id: 'signals', title: 'Signals (Predefined conditions)', countLabel: 'blocks selected', help: 'Signals are predefined complete conditions that combine indicators with comparisons or some propeties. For example: "CCI(14) is rising", "Momentum(20) crosses above 0", "PiercingLine pattern" etc.', category: 'signals' },
  { id: 'indicators', title: 'Indicators', countLabel: 'blocks selected', help: 'By choosing indicators and operators these selected blocks will be randomly combined to create random conditions. They might create new unique combinations not covered in Signals, but being random they might also not make sense.', category: 'indicators' },
  { id: 'orderTypes', title: 'Order types', countLabel: 'blocks selected', help: 'Order types that can be used to enter trades.', category: 'orderTypes' },
  { id: 'exitTypes', title: 'Exit types', countLabel: 'blocks selected', help: 'Advanced exit methods (ATM) that can be added to strategies.', category: 'exitTypes' },
  { id: 'stopLimit', title: 'Stop & Limit blocks', countLabel: 'blocks selected', help: 'Blocks for Stop Loss and Profit Target management.', category: 'stopLimit' },
  { id: 'customData', title: 'Custom data blocks', countLabel: 'blocks selected', help: 'Custom data that can be used as strategy inputs.', category: 'customData' },
];

// --- ATM -----------------------------------------------------------------------------------

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

export interface PartsToImproveState {
  entryLongUse: boolean;
  entryLongAction: string;
  entryShortUse: boolean;
  entryShortAction: string;
  orderLongUse: boolean;
  orderShortUse: boolean;
  exitLongUse: boolean;
  exitLongAction: string;
  exitShortUse: boolean;
  exitShortAction: string;
  improveAtm: boolean;
}

export const partsToImproveActions = ['Replace whole part', 'Add new blocks to existing part'];

export const partsToImproveDefaults: PartsToImproveState = {
  entryLongUse: true,
  entryLongAction: partsToImproveActions[1],
  entryShortUse: false,
  entryShortAction: partsToImproveActions[1],
  orderLongUse: false,
  orderShortUse: false,
  exitLongUse: true,
  exitLongAction: partsToImproveActions[0],
  exitShortUse: false,
  exitShortAction: partsToImproveActions[0],
  improveAtm: false,
};

// --- Custom analysis ------------------------------------------------------------------------------

export const customAnalysisDefaults = {
  perStrategy1: 'none',
  fullDatabank1: 'none',
  perStrategy2: 'none',
  fullDatabank2: 'none',
  inputArgsPerStrategy1: '',
  inputArgsFullDatabank1: '',
  inputArgsPerStrategy2: '',
  inputArgsFullDatabank2: '',
  source: 'Results',
  availableDatabanks: ['Results', 'Last generation', 'Existing portfolio'],
};

export const customAnalysisMethodOptions: { value: string; label: string; group: 'perStrategy' | 'fullDatabank' }[] = [
  { value: 'none', label: 'None', group: 'perStrategy' },
  { value: 'ComputeCorrelation', label: 'Compute correlation', group: 'fullDatabank' },
  { value: 'ComputeCustomMetric', label: 'Compute custom metric', group: 'perStrategy' },
  { value: 'DetectDeltaPeriods', label: 'Detect delta periods', group: 'perStrategy' },
  { value: 'ExportTrades', label: 'Export trades', group: 'perStrategy' },
  { value: 'RemoveCorrelatedStrategies', label: 'Remove correlated strategies', group: 'fullDatabank' },
];
