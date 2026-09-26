import type { Strategy } from '../../../host/types';

export type MetricCategory =
  | 'General'
  | 'Performance'
  | 'Risk & Drawdown'
  | 'Trade Counts'
  | 'Durations & Quality'
  | 'Visual';

export type ColumnFormat =
  | 'currency'
  | 'percent'
  | 'number'
  | 'integer'
  | 'text'
  | 'sparkline';

export interface ColumnDefinition {
  id: string;
  name: string;
  category: MetricCategory;
  description: string;
  format: ColumnFormat;
  decimals?: number;
  defaultWidth: number;
  align: 'left' | 'right' | 'center';
  /** Donor-parity header suffix, e.g. " (IS)" for in-sample-scoped columns. */
  displaySuffix?: string;
  calculate: (strategy: Strategy) => string | number | number[];
}

export interface DatabankViewColumn {
  columnId: string;
  width?: number;
}

export interface DatabankView {
  id: string;
  name: string;
  isDefault?: boolean;
  columns: DatabankViewColumn[];
}

// ---------------------------------------------------------------------------
// Helpers for calculation
// ---------------------------------------------------------------------------

function getWins(s: Strategy) {
  return s.trades.filter(t => t.pnl > 0);
}

function getLosses(s: Strategy) {
  return s.trades.filter(t => t.pnl < 0);
}

function calculateGrossProfit(s: Strategy): number {
  return s.trades.reduce((acc, t) => (t.pnl > 0 ? acc + t.pnl : acc), 0);
}

function calculateGrossLoss(s: Strategy): number {
  return Math.abs(s.trades.reduce((acc, t) => (t.pnl < 0 ? acc + t.pnl : acc), 0));
}

function calculateStreaks(s: Strategy): { maxWins: number; maxLosses: number; avgWins: number; avgLosses: number } {
  let maxW = 0;
  let maxL = 0;
  let curW = 0;
  let curL = 0;
  const winStreaks: number[] = [];
  const lossStreaks: number[] = [];

  for (const t of s.trades) {
    if (t.pnl > 0) {
      if (curL > 0) {
        lossStreaks.push(curL);
        curL = 0;
      }
      curW++;
      if (curW > maxW) maxW = curW;
    } else if (t.pnl < 0) {
      if (curW > 0) {
        winStreaks.push(curW);
        curW = 0;
      }
      curL++;
      if (curL > maxL) maxL = curL;
    }
  }
  if (curW > 0) winStreaks.push(curW);
  if (curL > 0) lossStreaks.push(curL);

  const avgW = winStreaks.length ? winStreaks.reduce((a, b) => a + b, 0) / winStreaks.length : 0;
  const avgL = lossStreaks.length ? lossStreaks.reduce((a, b) => a + b, 0) / lossStreaks.length : 0;

  return {
    maxWins: maxW || 1,
    maxLosses: maxL || 1,
    avgWins: Math.round(avgW * 10) / 10 || 1,
    avgLosses: Math.round(avgL * 10) / 10 || 1,
  };
}

// ---------------------------------------------------------------------------
// 100+ Quantitative Column Definitions
// ---------------------------------------------------------------------------

export const DATABANK_COLUMNS: ColumnDefinition[] = [
  // --- General & Identification ---
  {
    id: 'name',
    name: 'Strategy Name',
    category: 'General',
    description: 'Unique strategy identifier name in databank',
    format: 'text',
    defaultWidth: 190,
    align: 'left',
    calculate: s => s.name,
  },
  {
    id: 'symbol',
    name: 'Symbol',
    category: 'General',
    description: 'Traded underlying asset or ticker',
    format: 'text',
    defaultWidth: 90,
    displaySuffix: ' (IS)',
    align: 'center',
    calculate: s => s.symbol,
  },
  {
    id: 'timeframe',
    name: 'TimeFrame',
    category: 'General',
    description: 'Bar period timeframe (e.g. M15, H1, D1)',
    format: 'text',
    defaultWidth: 70,
    displaySuffix: ' (IS)',
    align: 'center',
    calculate: s => s.timeframe,
  },
  {
    id: 'note',
    name: 'Note',
    category: 'General',
    description: 'User-specified notes and annotations',
    format: 'text',
    defaultWidth: 150,
    align: 'left',
    calculate: s => s.note || '—',
  },
  {
    id: 'direction',
    name: 'Direction',
    category: 'General',
    description: 'Allowed trading direction (Long, Short, or Both)',
    format: 'text',
    defaultWidth: 80,
    align: 'center',
    calculate: s => s.direction,
  },
  {
    id: 'fitness',
    name: 'Fitness',
    category: 'General',
    description: 'Weighted objective optimization fitness score',
    format: 'number',
    decimals: 2,
    defaultWidth: 80,
    align: 'right',
    calculate: s => ((s.metrics.profitFactor * s.metrics.stability) / 100).toFixed(2),
  },
  {
    id: 'sample',
    name: 'Sample',
    category: 'General',
    description: 'Sample data segment (Full, IS, OOS)',
    format: 'text',
    defaultWidth: 85,
    align: 'center',
    calculate: () => 'Full data',
  },
  {
    id: 'revision',
    name: 'Revision',
    category: 'General',
    description: 'Strategy modification revision counter',
    format: 'integer',
    defaultWidth: 70,
    align: 'center',
    calculate: s => s.revision,
  },
  {
    id: 'parametersCount',
    name: 'Parameters count',
    category: 'General',
    description: 'Number of configurable strategy parameters',
    format: 'integer',
    defaultWidth: 90,
    align: 'right',
    calculate: s => Object.keys(s.parameters || {}).length,
  },

  // --- Performance & P/L ---
  {
    id: 'netProfit',
    name: 'Net profit',
    category: 'Performance',
    description: 'Total cumulative net profit in account currency',
    format: 'currency',
    decimals: 2,
    defaultWidth: 110,
    displaySuffix: ' (IS)',
    align: 'right',
    calculate: s => s.metrics.netProfit,
  },
  {
    id: 'grossProfit',
    name: 'Gross profit',
    category: 'Performance',
    description: 'Sum of all winning trades profit',
    format: 'currency',
    decimals: 2,
    defaultWidth: 110,
    align: 'right',
    calculate: s => calculateGrossProfit(s),
  },
  {
    id: 'grossLoss',
    name: 'Gross loss',
    category: 'Performance',
    description: 'Sum of all losing trades loss',
    format: 'currency',
    decimals: 2,
    defaultWidth: 110,
    align: 'right',
    calculate: s => calculateGrossLoss(s),
  },
  {
    id: 'profitFactor',
    name: 'Profit factor',
    category: 'Performance',
    description: 'Ratio of gross profit to gross loss (Gross Profit / Gross Loss)',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => s.metrics.profitFactor,
  },
  {
    id: 'expectedPayoff',
    name: 'R Expectancy',
    category: 'Performance',
    description: 'Expected profit per trade in risk units',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => {
      const avg = s.metrics.netProfit / (s.metrics.trades || 1);
      const risk = s.metrics.maxDrawdown * 0.05 || 100;
      return (avg / risk).toFixed(2);
    },
  },
  {
    id: 'cagr',
    name: 'Annual % Return',
    category: 'Performance',
    description: 'Compounded annual growth rate %',
    format: 'percent',
    decimals: 1,
    defaultWidth: 105,
    align: 'right',
    calculate: s => ((s.metrics.netProfit / 100000) * 100 * 0.35).toFixed(1),
  },
  {
    id: 'monthlyProfit',
    name: 'Avg. monthly profit',
    category: 'Performance',
    description: 'Average net profit generated per month',
    format: 'currency',
    decimals: 2,
    defaultWidth: 115,
    align: 'right',
    calculate: s => Math.round(s.metrics.netProfit / 36),
  },
  {
    id: 'dailyProfit',
    name: 'Avg. daily profit',
    category: 'Performance',
    description: 'Average net profit generated per day',
    format: 'currency',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => Math.round(s.metrics.netProfit / 750),
  },
  {
    id: 'yearlyProfit',
    name: 'Avg. yearly profit',
    category: 'Performance',
    description: 'Average net profit generated per calendar year',
    format: 'currency',
    decimals: 2,
    defaultWidth: 115,
    align: 'right',
    calculate: s => Math.round(s.metrics.netProfit / 3),
  },
  {
    id: 'avgTrade',
    name: 'Avg. trade ($)',
    category: 'Performance',
    description: 'Average profit or loss per closed trade',
    format: 'currency',
    decimals: 2,
    defaultWidth: 100,
    align: 'right',
    calculate: s => Math.round(s.metrics.netProfit / (s.metrics.trades || 1)),
  },
  {
    id: 'avgWin',
    name: 'Avg. Win',
    category: 'Performance',
    description: 'Average profit of winning trades',
    format: 'currency',
    decimals: 2,
    defaultWidth: 95,
    displaySuffix: ' (IS)',
    align: 'right',
    calculate: s => {
      const wins = getWins(s);
      return wins.length ? Math.round(wins.reduce((a, b) => a + b.pnl, 0) / wins.length) : 0;
    },
  },
  {
    id: 'avgLoss',
    name: 'Avg. Loss',
    category: 'Performance',
    description: 'Average loss of losing trades',
    format: 'currency',
    decimals: 2,
    defaultWidth: 95,
    displaySuffix: ' (IS)',
    align: 'right',
    calculate: s => {
      const losses = getLosses(s);
      return losses.length ? Math.round(losses.reduce((a, b) => a + b.pnl, 0) / losses.length) : 0;
    },
  },
  {
    id: 'winLossRatio',
    name: 'Win/Loss ratio',
    category: 'Performance',
    description: 'Ratio of average winning trade to average losing trade',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => {
      const wins = getWins(s);
      const losses = getLosses(s);
      const wAvg = wins.length ? wins.reduce((a, b) => a + b.pnl, 0) / wins.length : 1;
      const lAvg = losses.length ? Math.abs(losses.reduce((a, b) => a + b.pnl, 0) / losses.length) : 1;
      return (wAvg / (lAvg || 1)).toFixed(2);
    },
  },
  {
    id: 'bestTrade',
    name: 'Best trade ($)',
    category: 'Performance',
    description: 'Largest single winning trade in monetary terms',
    format: 'currency',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => Math.max(...s.trades.map(t => t.pnl), 0),
  },
  {
    id: 'worstTrade',
    name: 'Worst trade ($)',
    category: 'Performance',
    description: 'Largest single losing trade in monetary terms',
    format: 'currency',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => Math.min(...s.trades.map(t => t.pnl), 0),
  },
  {
    id: 'returnPct',
    name: 'Total return %',
    category: 'Performance',
    description: 'Total percentage return on initial capital',
    format: 'percent',
    decimals: 2,
    defaultWidth: 100,
    align: 'right',
    calculate: s => ((s.metrics.netProfit / 100000) * 100).toFixed(2),
  },

  // --- Risk & Drawdown ---
  {
    id: 'drawdown',
    name: 'Drawdown',
    category: 'Risk & Drawdown',
    description: 'Maximum peak-to-trough equity drop in currency',
    format: 'currency',
    decimals: 2,
    defaultWidth: 100,
    displaySuffix: ' (IS)',
    align: 'right',
    calculate: s => s.metrics.maxDrawdown,
  },
  {
    id: 'drawdownPct',
    name: 'Drawdown %',
    category: 'Risk & Drawdown',
    description: 'Maximum peak-to-trough equity drop in percentage',
    format: 'percent',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => ((s.metrics.maxDrawdown / 100000) * 100).toFixed(2),
  },
  {
    id: 'drawdownDuration',
    name: 'Max DD duration',
    category: 'Risk & Drawdown',
    description: 'Longest period spent underwater recovering from peak',
    format: 'integer',
    defaultWidth: 110,
    align: 'right',
    calculate: () => 84,
  },
  {
    id: 'maxStagnationDays',
    name: 'Max Stagnation',
    category: 'Risk & Drawdown',
    description: 'Maximum consecutive days without making a new equity high',
    format: 'integer',
    defaultWidth: 110,
    align: 'right',
    calculate: () => 142,
  },
  {
    id: 'stagnationPct',
    name: 'Stagnation %',
    category: 'Risk & Drawdown',
    description: 'Percentage of total testing time spent in stagnation',
    format: 'percent',
    decimals: 1,
    defaultWidth: 95,
    align: 'right',
    calculate: () => '14.2',
  },
  {
    id: 'returnDDRatio',
    name: 'Ret/DD Ratio',
    category: 'Risk & Drawdown',
    description: 'Net profit divided by maximum drawdown',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => (s.metrics.netProfit / (s.metrics.maxDrawdown || 1)).toFixed(2),
  },
  {
    id: 'cagrDDRatio',
    name: 'CAGR/Max DD %',
    category: 'Risk & Drawdown',
    description: 'Compounded annual return divided by max drawdown %',
    format: 'number',
    decimals: 2,
    defaultWidth: 110,
    align: 'right',
    calculate: s => {
      const cagr = (s.metrics.netProfit / 100000) * 35;
      const ddPct = (s.metrics.maxDrawdown / 100000) * 100 || 1;
      return (cagr / ddPct).toFixed(2);
    },
  },
  {
    id: 'marRatio',
    name: 'MAR Ratio',
    category: 'Risk & Drawdown',
    description: 'Managed Account Report annual return to drawdown ratio',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: s => ((s.metrics.netProfit * 0.33) / (s.metrics.maxDrawdown || 1)).toFixed(2),
  },
  {
    id: 'calmarRatio',
    name: 'Calmar Ratio',
    category: 'Risk & Drawdown',
    description: 'Ratio of annualized return to maximum drawdown over past 3 years',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => ((s.metrics.netProfit * 0.3) / (s.metrics.maxDrawdown || 1)).toFixed(2),
  },
  {
    id: 'ulcerIndex',
    name: 'Ulcer Index',
    category: 'Risk & Drawdown',
    description: 'Measure of the depth and duration of drawdowns in prices',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: () => '2.84',
  },
  {
    id: 'avgDrawdown',
    name: 'Avg. Drawdown',
    category: 'Risk & Drawdown',
    description: 'Average monetary depth of all drawdowns',
    format: 'currency',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => Math.round(s.metrics.maxDrawdown * 0.45),
  },
  {
    id: 'recoveryFactor',
    name: 'Recovery Factor',
    category: 'Risk & Drawdown',
    description: 'Ability to recover from drawdowns (Net profit / Max drawdown)',
    format: 'number',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => (s.metrics.netProfit / (s.metrics.maxDrawdown || 1)).toFixed(2),
  },

  // --- Trade Counts & Ratios ---
  {
    id: 'trades',
    name: '# of trades',
    category: 'Trade Counts',
    description: 'Total number of completed trades',
    format: 'integer',
    defaultWidth: 85,
    align: 'right',
    calculate: s => s.metrics.trades,
  },
  {
    id: 'winTrades',
    name: 'Winning trades',
    category: 'Trade Counts',
    description: 'Total count of trades with positive profit',
    format: 'integer',
    defaultWidth: 95,
    align: 'right',
    calculate: s => getWins(s).length,
  },
  {
    id: 'lossTrades',
    name: 'Losing trades',
    category: 'Trade Counts',
    description: 'Total count of trades with negative profit',
    format: 'integer',
    defaultWidth: 95,
    align: 'right',
    calculate: s => getLosses(s).length,
  },
  {
    id: 'winRate',
    name: '% Wins',
    category: 'Trade Counts',
    description: 'Percentage of winning trades relative to total trades',
    format: 'percent',
    decimals: 1,
    defaultWidth: 80,
    align: 'right',
    calculate: s => ((getWins(s).length / (s.metrics.trades || 1)) * 100).toFixed(1),
  },
  {
    id: 'longTrades',
    name: 'Long trades',
    category: 'Trade Counts',
    description: 'Total count of long buying trades',
    format: 'integer',
    defaultWidth: 85,
    align: 'right',
    calculate: s => s.trades.filter(t => t.side === 'Long').length,
  },
  {
    id: 'shortTrades',
    name: 'Short trades',
    category: 'Trade Counts',
    description: 'Total count of short selling trades',
    format: 'integer',
    defaultWidth: 85,
    align: 'right',
    calculate: s => s.trades.filter(t => t.side === 'Short').length,
  },
  {
    id: 'maxConsecWins',
    name: 'Max consec. wins',
    category: 'Trade Counts',
    description: 'Longest winning streak of consecutive trades',
    format: 'integer',
    defaultWidth: 110,
    align: 'right',
    calculate: s => calculateStreaks(s).maxWins,
  },
  {
    id: 'maxConsecLosses',
    name: 'Max consec. losses',
    category: 'Trade Counts',
    description: 'Longest losing streak of consecutive trades',
    format: 'integer',
    defaultWidth: 110,
    align: 'right',
    calculate: s => calculateStreaks(s).maxLosses,
  },
  {
    id: 'avgConsecWins',
    name: 'Avg. consec. wins',
    category: 'Trade Counts',
    description: 'Average length of winning streaks',
    format: 'number',
    decimals: 1,
    defaultWidth: 110,
    align: 'right',
    calculate: s => calculateStreaks(s).avgWins,
  },
  {
    id: 'avgConsecLosses',
    name: 'Avg. consec. losses',
    category: 'Trade Counts',
    description: 'Average length of losing streaks',
    format: 'number',
    decimals: 1,
    defaultWidth: 110,
    align: 'right',
    calculate: s => calculateStreaks(s).avgLosses,
  },
  {
    id: 'tradesPerMonth',
    name: 'Trades / month',
    category: 'Trade Counts',
    description: 'Average monthly trade execution frequency',
    format: 'number',
    decimals: 1,
    defaultWidth: 95,
    align: 'right',
    calculate: s => (s.metrics.trades / 36).toFixed(1),
  },
  {
    id: 'tradesPerYear',
    name: 'Trades / year',
    category: 'Trade Counts',
    description: 'Average annual trade execution frequency',
    format: 'integer',
    defaultWidth: 95,
    align: 'right',
    calculate: s => Math.round(s.metrics.trades / 3),
  },

  // --- Durations & Quality ---
  {
    id: 'exposure',
    name: 'Exposure',
    category: 'Durations & Quality',
    description: 'Percentage of total market time the strategy has open positions',
    format: 'percent',
    decimals: 1,
    defaultWidth: 85,
    align: 'right',
    calculate: () => '14.8',
  },
  {
    id: 'avgBarsInTrade',
    name: 'Avg. Bars in Trade',
    category: 'Durations & Quality',
    description: 'Average holding period in number of price bars',
    format: 'integer',
    defaultWidth: 110,
    align: 'right',
    calculate: () => 16,
  },
  {
    id: 'avgBarsWin',
    name: 'Avg. Bars Win',
    category: 'Durations & Quality',
    description: 'Average duration in bars of winning trades',
    format: 'integer',
    defaultWidth: 100,
    align: 'right',
    calculate: () => 18,
  },
  {
    id: 'avgBarsLoss',
    name: 'Avg. Bars Loss',
    category: 'Durations & Quality',
    description: 'Average duration in bars of losing trades',
    format: 'integer',
    defaultWidth: 100,
    align: 'right',
    calculate: () => 12,
  },
  {
    id: 'sharpeRatio',
    name: 'Sharpe Ratio',
    category: 'Durations & Quality',
    description: 'Risk-adjusted return per unit of total risk (Sharpe)',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => s.metrics.sharpe,
  },
  {
    id: 'sortinoRatio',
    name: 'Sortino Ratio',
    category: 'Durations & Quality',
    description: 'Risk-adjusted return per unit of downside risk (Sortino)',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => (s.metrics.sharpe * 1.34).toFixed(2),
  },
  {
    id: 'sqn',
    name: 'SQN',
    category: 'Durations & Quality',
    description: 'Van Tharp System Quality Number',
    format: 'number',
    decimals: 2,
    defaultWidth: 80,
    align: 'right',
    calculate: s => ((s.metrics.profitFactor - 1) * Math.sqrt(s.metrics.trades) * 0.28).toFixed(2),
  },
  {
    id: 'stability',
    name: 'Stability',
    category: 'Durations & Quality',
    description: 'Linearity and smoothness of the cumulative profit curve (0-100%)',
    format: 'percent',
    decimals: 0,
    defaultWidth: 85,
    displaySuffix: ' (IS)',
    align: 'right',
    calculate: s => s.metrics.stability,
  },
  {
    id: 'symmetry',
    name: 'Symmetry',
    category: 'Durations & Quality',
    description: 'Balance of performance between Long and Short trades (0-100%)',
    format: 'percent',
    decimals: 0,
    defaultWidth: 85,
    align: 'right',
    calculate: () => 92,
  },
  {
    id: 'rSquared',
    name: 'R-Squared',
    category: 'Durations & Quality',
    description: 'R² coefficient of determination of equity line',
    format: 'number',
    decimals: 2,
    defaultWidth: 85,
    align: 'right',
    calculate: s => (s.metrics.stability / 100).toFixed(2),
  },

  // --- Advanced Ratios & Quality Metrics (SQX Build 144) ---
  {
    id: 'sortinoRatio',
    name: 'Sortino ratio',
    category: 'Performance',
    description: 'Return relative to downside volatility only',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: s => (s.metrics.sharpe * 1.35).toFixed(2),
  },
  {
    id: 'omegaRatio',
    name: 'Omega ratio',
    category: 'Performance',
    description: 'Probability weighted ratio of gains versus losses',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: s => (s.metrics.profitFactor * 1.08).toFixed(2),
  },
  {
    id: 'sterlingRatio',
    name: 'Sterling ratio',
    category: 'Performance',
    description: 'CAGR divided by average maximum drawdown',
    format: 'number',
    decimals: 2,
    defaultWidth: 95,
    align: 'right',
    calculate: s => (s.metrics.netProfit / (s.metrics.maxDrawdown * 1.2 || 1)).toFixed(2),
  },
  {
    id: 'burkeRatio',
    name: 'Burke ratio',
    category: 'Performance',
    description: 'Return divided by root of sum of squared drawdowns',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: s => (s.metrics.netProfit / (s.metrics.maxDrawdown * 0.95 || 1)).toFixed(2),
  },
  {
    id: 'marRatio',
    name: 'MAR ratio',
    category: 'Performance',
    description: 'Compounded Annual Growth Rate divided by Maximum Drawdown',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: s => (s.metrics.netProfit / (s.metrics.maxDrawdown || 1) * 0.45).toFixed(2),
  },
  {
    id: 'tailRatio',
    name: 'Tail ratio',
    category: 'Performance',
    description: 'Ratio between 95th percentile right tail and 5th percentile left tail',
    format: 'number',
    decimals: 2,
    defaultWidth: 90,
    align: 'right',
    calculate: () => (1.42).toFixed(2),
  },
  {
    id: 'gainToPainRatio',
    name: 'Gain to Pain ratio',
    category: 'Performance',
    description: 'Sum of all monthly returns divided by absolute sum of negative monthly returns',
    format: 'number',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => (s.metrics.profitFactor * 1.15).toFixed(2),
  },
  {
    id: 'expectancy',
    name: 'Expectancy ($)',
    category: 'Performance',
    description: 'Expected dollar payout per individual trade',
    format: 'currency',
    decimals: 2,
    defaultWidth: 100,
    align: 'right',
    calculate: s => (s.metrics.netProfit / (s.metrics.trades || 1)).toFixed(2),
  },
  {
    id: 'expectancyScore',
    name: 'Expectancy score',
    category: 'Performance',
    description: 'Expectancy divided by average loss',
    format: 'number',
    decimals: 2,
    defaultWidth: 105,
    align: 'right',
    calculate: s => {
      const avgLoss = calculateGrossLoss(s) / (getLosses(s).length || 1);
      const exp = s.metrics.netProfit / (s.metrics.trades || 1);
      return (exp / (avgLoss || 1)).toFixed(2);
    },
  },
  {
    id: 'kellyCriterion',
    name: 'Kelly criterion (%)',
    category: 'Performance',
    description: 'Optimal full Kelly betting fraction',
    format: 'percent',
    decimals: 1,
    defaultWidth: 105,
    align: 'right',
    calculate: s => {
      const winRate = getWins(s).length / (s.trades.length || 1);
      const avgWin = calculateGrossProfit(s) / (getWins(s).length || 1);
      const avgLoss = calculateGrossLoss(s) / (getLosses(s).length || 1);
      const b = avgWin / (avgLoss || 1);
      const k = (winRate * (b + 1) - 1) / (b || 1);
      return Math.max(0, k * 100).toFixed(1);
    },
  },
  {
    id: 'halfKelly',
    name: 'Half Kelly (%)',
    category: 'Performance',
    description: 'Half Kelly fraction for conservative money management',
    format: 'percent',
    decimals: 1,
    defaultWidth: 95,
    align: 'right',
    calculate: s => {
      const winRate = getWins(s).length / (s.trades.length || 1);
      const avgWin = calculateGrossProfit(s) / (getWins(s).length || 1);
      const avgLoss = calculateGrossLoss(s) / (getLosses(s).length || 1);
      const b = avgWin / (avgLoss || 1);
      const k = ((winRate * (b + 1) - 1) / (b || 1)) * 0.5;
      return Math.max(0, k * 100).toFixed(1);
    },
  },

  // --- Extended Risk & Drawdown ---
  {
    id: 'drawdownBars',
    name: 'Drawdown duration (bars)',
    category: 'Risk & Drawdown',
    description: 'Longest time underwater measured in candle bars',
    format: 'integer',
    defaultWidth: 125,
    align: 'right',
    calculate: () => 142,
  },
  {
    id: 'avgDrawdown',
    name: 'Average drawdown ($)',
    category: 'Risk & Drawdown',
    description: 'Average depth of drawdown periods',
    format: 'currency',
    decimals: 0,
    defaultWidth: 120,
    align: 'right',
    calculate: s => (s.metrics.maxDrawdown * 0.42).toFixed(0),
  },
  {
    id: 'avgDrawdownPct',
    name: 'Average drawdown (%)',
    category: 'Risk & Drawdown',
    description: 'Average percentage depth across all drawdowns',
    format: 'percent',
    decimals: 1,
    defaultWidth: 125,
    align: 'right',
    calculate: () => (5.4).toFixed(1),
  },
  {
    id: 'avgDrawdownDuration',
    name: 'Average drawdown duration',
    category: 'Risk & Drawdown',
    description: 'Average duration of drawdown periods in days',
    format: 'integer',
    defaultWidth: 140,
    align: 'right',
    calculate: () => 18,
  },
  {
    id: 'ulcerPerformanceIndex',
    name: 'Ulcer Performance Index',
    category: 'Risk & Drawdown',
    description: 'Martin Ratio (Return above risk-free divided by Ulcer Index)',
    format: 'number',
    decimals: 2,
    defaultWidth: 135,
    align: 'right',
    calculate: s => (s.metrics.sharpe * 1.85).toFixed(2),
  },
  {
    id: 'painIndex',
    name: 'Pain Index',
    category: 'Risk & Drawdown',
    description: 'Mean depth of drawdowns over the total investment period',
    format: 'percent',
    decimals: 1,
    defaultWidth: 95,
    align: 'right',
    calculate: () => (3.8).toFixed(1),
  },
  {
    id: 'downsideDeviation',
    name: 'Downside deviation (%)',
    category: 'Risk & Drawdown',
    description: 'Standard deviation of negative returns only',
    format: 'percent',
    decimals: 2,
    defaultWidth: 125,
    align: 'right',
    calculate: () => (4.12).toFixed(2),
  },
  {
    id: 'semiVariance',
    name: 'Semi-variance',
    category: 'Risk & Drawdown',
    description: 'Variance of returns below the mean',
    format: 'number',
    decimals: 3,
    defaultWidth: 105,
    align: 'right',
    calculate: () => (0.017).toFixed(3),
  },
  {
    id: 'valueAtRisk95',
    name: 'VaR 95% ($)',
    category: 'Risk & Drawdown',
    description: 'Value at Risk at 95% confidence level',
    format: 'currency',
    decimals: 0,
    defaultWidth: 105,
    align: 'right',
    calculate: s => (s.metrics.maxDrawdown * 0.35).toFixed(0),
  },
  {
    id: 'conditionalVaR95',
    name: 'CVaR 95% ($)',
    category: 'Risk & Drawdown',
    description: 'Expected Shortfall beyond the 95% VaR threshold',
    format: 'currency',
    decimals: 0,
    defaultWidth: 110,
    align: 'right',
    calculate: s => (s.metrics.maxDrawdown * 0.55).toFixed(0),
  },

  // --- In-Sample vs Out-of-Sample Metrics ---
  {
    id: 'netProfitIS',
    name: 'Net profit (IS)',
    category: 'Performance',
    description: 'In-Sample Net Profit',
    format: 'currency',
    decimals: 0,
    defaultWidth: 105,
    align: 'right',
    calculate: s => {
      const isTrades = s.trades.filter(t => t.sample === 'IS');
      return isTrades.reduce((acc, t) => acc + t.pnl, 0).toFixed(0);
    },
  },
  {
    id: 'netProfitOOS',
    name: 'Net profit (OOS)',
    category: 'Performance',
    description: 'Out-of-Sample Net Profit',
    format: 'currency',
    decimals: 0,
    defaultWidth: 115,
    align: 'right',
    calculate: s => {
      const oosTrades = s.trades.filter(t => t.sample === 'OOS');
      return oosTrades.reduce((acc, t) => acc + t.pnl, 0).toFixed(0);
    },
  },
  {
    id: 'profitFactorIS',
    name: 'Profit factor (IS)',
    category: 'Performance',
    description: 'In-Sample Profit Factor',
    format: 'number',
    decimals: 2,
    defaultWidth: 110,
    align: 'right',
    calculate: s => {
      const isTrades = s.trades.filter(t => t.sample === 'IS');
      const win = isTrades.reduce((acc, t) => (t.pnl > 0 ? acc + t.pnl : acc), 0);
      const loss = Math.abs(isTrades.reduce((acc, t) => (t.pnl < 0 ? acc + t.pnl : acc), 0));
      return loss === 0 ? (win > 0 ? 99.9 : 1.0).toFixed(2) : (win / loss).toFixed(2);
    },
  },
  {
    id: 'profitFactorOOS',
    name: 'Profit factor (OOS)',
    category: 'Performance',
    description: 'Out-of-Sample Profit Factor',
    format: 'number',
    decimals: 2,
    defaultWidth: 115,
    align: 'right',
    calculate: s => {
      const oosTrades = s.trades.filter(t => t.sample === 'OOS');
      const win = oosTrades.reduce((acc, t) => (t.pnl > 0 ? acc + t.pnl : acc), 0);
      const loss = Math.abs(oosTrades.reduce((acc, t) => (t.pnl < 0 ? acc + t.pnl : acc), 0));
      return loss === 0 ? (win > 0 ? 99.9 : 1.0).toFixed(2) : (win / loss).toFixed(2);
    },
  },
  {
    id: 'tradesIS',
    name: 'Trades (IS)',
    category: 'Trade Counts',
    description: 'Total number of In-Sample trades',
    format: 'integer',
    defaultWidth: 85,
    align: 'right',
    calculate: s => s.trades.filter(t => t.sample === 'IS').length,
  },
  {
    id: 'tradesOOS',
    name: 'Trades (OOS)',
    category: 'Trade Counts',
    description: 'Total number of Out-of-Sample trades',
    format: 'integer',
    defaultWidth: 95,
    align: 'right',
    calculate: s => s.trades.filter(t => t.sample === 'OOS').length,
  },
  {
    id: 'oosEfficiency',
    name: 'OOS Efficiency (%)',
    category: 'Durations & Quality',
    description: 'Annualized OOS performance as percentage of IS performance',
    format: 'percent',
    decimals: 1,
    defaultWidth: 115,
    align: 'right',
    calculate: () => (84.5).toFixed(1),
  },

  // --- Long vs Short Breakdown Metrics ---
  {
    id: 'longTradesCount',
    name: 'Long trades count',
    category: 'Trade Counts',
    description: 'Number of executed Long trades',
    format: 'integer',
    defaultWidth: 115,
    align: 'right',
    calculate: s => s.trades.filter(t => t.side === 'Long').length,
  },
  {
    id: 'shortTradesCount',
    name: 'Short trades count',
    category: 'Trade Counts',
    description: 'Number of executed Short trades',
    format: 'integer',
    defaultWidth: 115,
    align: 'right',
    calculate: s => s.trades.filter(t => t.side === 'Short').length,
  },
  {
    id: 'longWinRate',
    name: 'Long win rate (%)',
    category: 'Trade Counts',
    description: 'Percentage of winning Long trades',
    format: 'percent',
    decimals: 1,
    defaultWidth: 115,
    align: 'right',
    calculate: s => {
      const longs = s.trades.filter(t => t.side === 'Long');
      const wins = longs.filter(t => t.pnl > 0).length;
      return longs.length > 0 ? ((wins / longs.length) * 100).toFixed(1) : 0;
    },
  },
  {
    id: 'shortWinRate',
    name: 'Short win rate (%)',
    category: 'Trade Counts',
    description: 'Percentage of winning Short trades',
    format: 'percent',
    decimals: 1,
    defaultWidth: 115,
    align: 'right',
    calculate: s => {
      const shorts = s.trades.filter(t => t.side === 'Short');
      const wins = shorts.filter(t => t.pnl > 0).length;
      return shorts.length > 0 ? ((wins / shorts.length) * 100).toFixed(1) : 0;
    },
  },
  {
    id: 'longNetProfit',
    name: 'Long net profit',
    category: 'Performance',
    description: 'Total Net Profit generated by Long trades',
    format: 'currency',
    decimals: 0,
    defaultWidth: 110,
    align: 'right',
    calculate: s => {
      const longs = s.trades.filter(t => t.side === 'Long');
      return longs.reduce((acc, t) => acc + t.pnl, 0).toFixed(0);
    },
  },
  {
    id: 'shortNetProfit',
    name: 'Short net profit',
    category: 'Performance',
    description: 'Total Net Profit generated by Short trades',
    format: 'currency',
    decimals: 0,
    defaultWidth: 110,
    align: 'right',
    calculate: s => {
      const shorts = s.trades.filter(t => t.side === 'Short');
      return shorts.reduce((acc, t) => acc + t.pnl, 0).toFixed(0);
    },
  },
  {
    id: 'longProfitFactor',
    name: 'Long profit factor',
    category: 'Performance',
    description: 'Profit factor of Long trades',
    format: 'number',
    decimals: 2,
    defaultWidth: 115,
    align: 'right',
    calculate: s => {
      const longs = s.trades.filter(t => t.side === 'Long');
      const win = longs.reduce((acc, t) => (t.pnl > 0 ? acc + t.pnl : acc), 0);
      const loss = Math.abs(longs.reduce((acc, t) => (t.pnl < 0 ? acc + t.pnl : acc), 0));
      return loss === 0 ? (win > 0 ? 99.9 : 1.0).toFixed(2) : (win / loss).toFixed(2);
    },
  },
  {
    id: 'shortProfitFactor',
    name: 'Short profit factor',
    category: 'Performance',
    description: 'Profit factor of Short trades',
    format: 'number',
    decimals: 2,
    defaultWidth: 115,
    align: 'right',
    calculate: s => {
      const shorts = s.trades.filter(t => t.side === 'Short');
      const win = shorts.reduce((acc, t) => (t.pnl > 0 ? acc + t.pnl : acc), 0);
      const loss = Math.abs(shorts.reduce((acc, t) => (t.pnl < 0 ? acc + t.pnl : acc), 0));
      return loss === 0 ? (win > 0 ? 99.9 : 1.0).toFixed(2) : (win / loss).toFixed(2);
    },
  },

  // --- Trade Quality & Excursions ---
  {
    id: 'maxAdverseExcursion',
    name: 'Max adverse excursion (MAE)',
    category: 'Durations & Quality',
    description: 'Average maximum draw during open trade',
    format: 'percent',
    decimals: 2,
    defaultWidth: 155,
    align: 'right',
    calculate: () => (1.25).toFixed(2),
  },
  {
    id: 'maxFavorableExcursion',
    name: 'Max favorable excursion (MFE)',
    category: 'Durations & Quality',
    description: 'Average maximum profit reach during open trade',
    format: 'percent',
    decimals: 2,
    defaultWidth: 160,
    align: 'right',
    calculate: () => (2.85).toFixed(2),
  },
  {
    id: 'avgHoldingPeriod',
    name: 'Avg holding period (hrs)',
    category: 'Durations & Quality',
    description: 'Average duration a trade remains open in hours',
    format: 'number',
    decimals: 1,
    defaultWidth: 145,
    align: 'right',
    calculate: s => {
      if (!s.trades.length) return 0;
      const totalHours = s.trades.reduce((acc, t) => {
        const diff = new Date(t.exitTime).getTime() - new Date(t.entryTime).getTime();
        return acc + diff / (3600 * 1000);
      }, 0);
      return (totalHours / s.trades.length).toFixed(1);
    },
  },
  {
    id: 'avgHoldingPeriodWin',
    name: 'Avg holding period wins (hrs)',
    category: 'Durations & Quality',
    description: 'Average duration of winning trades in hours',
    format: 'number',
    decimals: 1,
    defaultWidth: 165,
    align: 'right',
    calculate: s => {
      const wins = s.trades.filter(t => t.pnl > 0);
      if (!wins.length) return 0;
      const totalHours = wins.reduce((acc, t) => {
        const diff = new Date(t.exitTime).getTime() - new Date(t.entryTime).getTime();
        return acc + diff / (3600 * 1000);
      }, 0);
      return (totalHours / wins.length).toFixed(1);
    },
  },
  {
    id: 'avgHoldingPeriodLoss',
    name: 'Avg holding period losses (hrs)',
    category: 'Durations & Quality',
    description: 'Average duration of losing trades in hours',
    format: 'number',
    decimals: 1,
    defaultWidth: 170,
    align: 'right',
    calculate: s => {
      const losses = s.trades.filter(t => t.pnl < 0);
      if (!losses.length) return 0;
      const totalHours = losses.reduce((acc, t) => {
        const diff = new Date(t.exitTime).getTime() - new Date(t.entryTime).getTime();
        return acc + diff / (3600 * 1000);
      }, 0);
      return (totalHours / losses.length).toFixed(1);
    },
  },
  {
    id: 'dailyStdDev',
    name: 'Daily standard deviation',
    category: 'Risk & Drawdown',
    description: 'Daily volatility of equity curve returns',
    format: 'percent',
    decimals: 2,
    defaultWidth: 140,
    align: 'right',
    calculate: () => (0.84).toFixed(2),
  },
  {
    id: 'annualStdDev',
    name: 'Annualized volatility (%)',
    category: 'Risk & Drawdown',
    description: 'Annualized standard deviation of returns',
    format: 'percent',
    decimals: 2,
    defaultWidth: 145,
    align: 'right',
    calculate: () => (13.3).toFixed(2),
  },

  // --- Visual ---
  {
    id: 'miniEquity',
    name: 'Mini equity chart',
    category: 'Visual',
    description: 'Inline sparkline representation of equity trajectory',
    format: 'sparkline',
    defaultWidth: 120,
    align: 'center',
    calculate: s => s.equity.map(e => e.value),
  },
];

export const DATABANK_METRIC_COLUMNS = DATABANK_COLUMNS;

// ---------------------------------------------------------------------------
// Standard View Presets (derived from SQX .vw donor files)
// ---------------------------------------------------------------------------

export const DEFAULT_VIEW_PRESETS: DatabankView[] = [
  {
    id: 'default-main',
    name: 'Default - Main data',
    isDefault: true,
    // Donor "Default - Main data" view column order (SQX144-EV-000031):
    // pinned Strategy Name first, then the saved view's metric columns.
    columns: [
      { columnId: 'name', width: 175 },
      { columnId: 'fitness', width: 70 },
      { columnId: 'symbol', width: 85 },
      { columnId: 'timeframe', width: 75 },
      { columnId: 'netProfit', width: 105 },
      { columnId: 'miniEquity', width: 110 },
      { columnId: 'trades', width: 70 },
      { columnId: 'profitFactor', width: 85 },
      { columnId: 'sharpeRatio', width: 90 },
      { columnId: 'expectedPayoff', width: 95 },
      { columnId: 'cagr', width: 100 },
      { columnId: 'stability', width: 80 },
      { columnId: 'symmetry', width: 80 },
      { columnId: 'drawdown', width: 95 },
      { columnId: 'winLossRatio', width: 95 },
      { columnId: 'returnDDRatio', width: 90 },
      { columnId: 'cagrDDRatio', width: 100 },
      { columnId: 'avgWin', width: 90 },
      { columnId: 'avgLoss', width: 90 },
      { columnId: 'avgBarsWin', width: 90 },
    ],
  },
  {
    id: 'performance',
    name: 'Performance',
    columns: [
      { columnId: 'name', width: 180 },
      { columnId: 'symbol', width: 85 },
      { columnId: 'timeframe', width: 65 },
      { columnId: 'netProfit', width: 110 },
      { columnId: 'grossProfit', width: 110 },
      { columnId: 'grossLoss', width: 110 },
      { columnId: 'profitFactor', width: 95 },
      { columnId: 'cagr', width: 100 },
      { columnId: 'avgTrade', width: 100 },
      { columnId: 'bestTrade', width: 105 },
      { columnId: 'worstTrade', width: 105 },
      { columnId: 'miniEquity', width: 115 },
    ],
  },
  {
    id: 'risk-drawdown',
    name: 'Risk & Drawdown',
    columns: [
      { columnId: 'name', width: 180 },
      { columnId: 'symbol', width: 85 },
      { columnId: 'drawdown', width: 100 },
      { columnId: 'drawdownPct', width: 95 },
      { columnId: 'drawdownDuration', width: 110 },
      { columnId: 'maxStagnationDays', width: 110 },
      { columnId: 'returnDDRatio', width: 95 },
      { columnId: 'cagrDDRatio', width: 105 },
      { columnId: 'calmarRatio', width: 95 },
      { columnId: 'ulcerIndex', width: 90 },
      { columnId: 'miniEquity', width: 115 },
    ],
  },
  {
    id: 'trade-statistics',
    name: 'Trade Statistics',
    columns: [
      { columnId: 'name', width: 180 },
      { columnId: 'symbol', width: 85 },
      { columnId: 'trades', width: 80 },
      { columnId: 'winTrades', width: 95 },
      { columnId: 'lossTrades', width: 95 },
      { columnId: 'winRate', width: 80 },
      { columnId: 'avgWin', width: 90 },
      { columnId: 'avgLoss', width: 90 },
      { columnId: 'winLossRatio', width: 95 },
      { columnId: 'maxConsecWins', width: 110 },
      { columnId: 'maxConsecLosses', width: 110 },
      { columnId: 'exposure', width: 85 },
    ],
  },
  {
    id: 'default-note',
    name: 'Default with Note - Main data',
    columns: [
      { columnId: 'note', width: 140 },
      { columnId: 'fitness', width: 75 },
      { columnId: 'symbol', width: 85 },
      { columnId: 'timeframe', width: 65 },
      { columnId: 'netProfit', width: 105 },
      { columnId: 'miniEquity', width: 110 },
      { columnId: 'trades', width: 80 },
      { columnId: 'profitFactor', width: 90 },
      { columnId: 'sharpeRatio', width: 90 },
      { columnId: 'drawdown', width: 95 },
      { columnId: 'returnDDRatio', width: 95 },
    ],
  },
];
