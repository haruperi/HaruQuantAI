import type { BusinessConfig, ComputeNode, CustomProject, Databank, Dataset, ExtensionFile, Instrument, PortfolioMember, RuleNode, Strategy, Trade, WorkflowTask } from '../app/types';

function seeded(seed: number) { let value = seed >>> 0; return () => ((value = Math.imul(1664525, value) + 1013904223 >>> 0) / 4294967296); }

function buildStrategy(index: number, bankId: string): Strategy {
  const random = seeded(5100 + index * 83); const id = `str-${index + 1}`; const start = Date.UTC(2022, 0, 3); const trades: Trade[] = [];
  let balance = 100000; const equity = [{ time: '2022-01-03', value: balance, drawdown: 0 }]; let peak = balance;
  const count = 58 + (index % 7) * 8;
  for (let i = 0; i < count; i++) {
    const entry = 1.05 + random() * .18; const won = random() > .43; const pnl = Math.round((won ? 220 + random() * 620 : -(120 + random() * 480)) * 100) / 100;
    balance += pnl; peak = Math.max(peak, balance); const entryDate = new Date(start + i * 86400000 * 8); const exitDate = new Date(entryDate.getTime() + (1 + Math.floor(random() * 4)) * 86400000);
    trades.push({ id: `${id}-t${i + 1}`, strategyId: id, side: random() > .5 ? 'Long' : 'Short', entryTime: entryDate.toISOString(), exitTime: exitDate.toISOString(), entry, exit: entry + pnl / 200000, size: 1, pnl, sample: i < count * .72 ? 'IS' : 'OOS' });
    equity.push({ time: exitDate.toISOString().slice(0, 10), value: Math.round(balance * 100) / 100, drawdown: Math.round((peak - balance) * 100) / 100 });
  }
  const wins = trades.filter(t => t.pnl > 0).reduce((a, t) => a + t.pnl, 0); const loss = -trades.filter(t => t.pnl < 0).reduce((a, t) => a + t.pnl, 0); const maxDrawdown = Math.max(...equity.map(e => e.drawdown));
  return { id, name: `Strategy ${String(index + 1).padStart(3, '0')}`, symbol: index % 3 === 0 ? 'EURUSD' : index % 3 === 1 ? 'GBPJPY' : 'XAUUSD', timeframe: index % 2 ? 'H1' : 'M30', direction: 'Both', bankId, revision: 1, note: index % 5 === 0 ? 'Promising OOS stability' : '', parameters: { FastPeriod: 12 + index % 9, SlowPeriod: 28 + index % 15, ATRPeriod: 14, StopLoss: 90 + index * 2 }, trades, equity, metrics: { netProfit: Math.round((balance - 100000) * 100) / 100, trades: count, profitFactor: Math.round(wins / Math.max(loss, 1) * 100) / 100, maxDrawdown: Math.round(maxDrawdown * 100) / 100, sharpe: Math.round((.72 + random() * 1.8) * 100) / 100, stability: Math.round((65 + random() * 30) * 10) / 10 } };
}

export const databanks: Databank[] = [
  { id: 'results', name: 'Results', strategyIds: Array.from({ length: 40 }, (_, i) => `str-${i + 1}`) },
  { id: 'retest', name: 'Retest candidates', strategyIds: Array.from({ length: 18 }, (_, i) => `str-${i + 41}`) },
  { id: 'portfolio', name: 'Portfolio candidates', strategyIds: Array.from({ length: 12 }, (_, i) => `str-${i + 59}`) },
];
export const strategies: Strategy[] = Array.from({ length: 70 }, (_, i) => buildStrategy(i, i < 40 ? 'results' : i < 58 ? 'retest' : 'portfolio'));
export const datasets: Dataset[] = [
  { id: 'd1', source: 'Dukascopy', symbol: 'EURUSD', timeframe: 'M1 → H1', from: '2010-01-01', to: '2026-08-31', bars: 6021431, quality: 99.8, status: 'Ready' },
  { id: 'd2', source: 'Dukascopy', symbol: 'GBPJPY', timeframe: 'M1 → H4', from: '2011-04-01', to: '2026-08-31', bars: 5518210, quality: 99.6, status: 'Ready' },
  { id: 'd3', source: 'Futures', symbol: 'NQ', timeframe: 'Tick → D1', from: '2014-01-02', to: '2026-08-31', bars: 12861244, quality: 98.9, status: 'Ready' },
  { id: 'd4', source: 'File import', symbol: 'XAUUSD', timeframe: 'M1 → H1', from: '2012-01-03', to: '2026-08-31', bars: 4882301, quality: 97.6, status: 'Ready' },
];
export const instruments: Instrument[] = [
  { symbol: 'EURUSD', name: 'Euro / US Dollar', type: 'Forex', pointValue: 100000, spread: 1.2, session: 'Forex 24/5', timezone: 'Europe/Prague' },
  { symbol: 'GBPJPY', name: 'British Pound / Yen', type: 'Forex', pointValue: 100000, spread: 2.1, session: 'Forex 24/5', timezone: 'Europe/Prague' },
  { symbol: 'XAUUSD', name: 'Gold / US Dollar', type: 'CFD', pointValue: 100, spread: 2.8, session: 'Metals', timezone: 'America/New_York' },
  { symbol: 'NQ', name: 'E-mini Nasdaq-100', type: 'Futures', pointValue: 20, spread: .25, session: 'CME Equity', timezone: 'America/Chicago' },
];
export const rules: RuleNode[] = [
  { id: 'r1', depth: 0, kind: 'event', label: 'On Bar Open' }, { id: 'r2', depth: 1, kind: 'if', label: 'IF' },
  { id: 'r3', depth: 2, kind: 'condition', label: 'EMA(12) crosses above EMA(28)' }, { id: 'r4', depth: 2, kind: 'condition', label: 'ATR(14) > 0.0012' },
  { id: 'r5', depth: 1, kind: 'then', label: 'THEN' }, { id: 'r6', depth: 2, kind: 'action', label: 'Enter at Market (Long)' },
  { id: 'r7', depth: 2, kind: 'action', label: 'Set Stop Loss: 90 pips' }, { id: 'r8', depth: 2, kind: 'action', label: 'Set Profit Target: 180 pips' },
];
export const portfolioMembers: PortfolioMember[] = strategies.slice(58, 66).map((s, i) => ({ strategyId: s.id, weight: i < 4 ? 15 : 10, enabled: true, sector: i % 3 === 0 ? 'FX Majors' : i % 3 === 1 ? 'Metals' : 'Indices' }));
export const workflowTasks: WorkflowTask[] = [
  { id: 'w1', type: 'ClearDatabanks', name: 'Clear temporary candidates', enabled: true, status: 'idle', input: 'Temporary', output: 'Temporary' },
  { id: 'w2', type: 'Build', name: 'Generate H1 candidates', enabled: true, status: 'idle', input: 'EURUSD H1', output: 'Generated' },
  { id: 'w3', type: 'Retest', name: 'Higher precision retest', enabled: true, status: 'idle', input: 'Generated', output: 'Precise' },
  { id: 'w4', type: 'Filtering', name: 'OOS ranking filter', enabled: true, status: 'idle', input: 'Precise', output: 'Accepted' },
  { id: 'w5', type: 'AutomaticPortfolioBuilder', name: 'Build uncorrelated portfolio', enabled: true, status: 'idle', input: 'Accepted', output: 'Portfolio' },
  { id: 'w6', type: 'SaveToFiles', name: 'Export selected strategies', enabled: false, status: 'idle', input: 'Portfolio', output: 'Mock filesystem' },
];

export const customProjects: CustomProject[] = [
  {
    id: 'proj-1',
    name: 'FX Trend-Following Research Pipeline',
    description: 'Autonomous multi-stage generation, walk-forward retest, correlation filtering and portfolio assembly for Forex majors.',
    status: 'idle',
    tasks: [
      {
        id: 'w1',
        type: 'ClearDatabanks',
        name: 'Clear temporary candidate databanks',
        enabled: true,
        status: 'idle',
        input: 'Temporary',
        output: 'Temporary',
        config: { targetBank: 'Temporary', keepPinned: true },
      },
      {
        id: 'w2',
        type: 'Build',
        name: 'Genetic Strategy Generation (H1)',
        enabled: true,
        status: 'idle',
        input: 'EURUSD H1',
        output: 'Generated',
        config: { symbol: 'EURUSD', timeframe: 'H1', targetCount: 30, minSharpe: 1.1, minTrades: 80 },
      },
      {
        id: 'w3',
        type: 'Retest',
        name: 'Higher Precision Multi-Market Retest',
        enabled: true,
        status: 'idle',
        input: 'Generated',
        output: 'Precise',
        config: { precision: 'M1 real tick data', spreadMultiplier: 1.5, slippagePips: 1.0 },
      },
      {
        id: 'w4',
        type: 'Filtering',
        name: 'Sharpe & Drawdown Robustness Filter',
        enabled: true,
        status: 'idle',
        input: 'Precise',
        output: 'Accepted',
        config: { filterMetric: 'Sharpe ratio >= 1.25', maxDrawdownPct: 20, minProfitFactor: 1.4 },
      },
      {
        id: 'w5',
        type: 'AutomaticPortfolioBuilder',
        name: 'Uncorrelated 5-Strategy Portfolio Assembly',
        enabled: true,
        status: 'idle',
        input: 'Accepted',
        output: 'Portfolio',
        config: { maxStrategies: 5, maxCorrelation: 0.45, weightingModel: 'Risk Parity' },
      },
      {
        id: 'w6',
        type: 'SaveToFiles',
        name: 'Export Compiled MQL5 / Python Robots',
        enabled: false,
        status: 'idle',
        input: 'Portfolio',
        output: 'Export Directory',
        config: { destinationPath: './exports/live_candidates/', format: 'MQL5 + Python' },
      },
    ],
  },
  {
    id: 'proj-2',
    name: 'NQ Futures Mean Reversion Scanner',
    description: 'High-frequency intraday mean reversion scanner with Monte Carlo validation.',
    status: 'idle',
    tasks: [
      {
        id: 'w2-1',
        type: 'UpdateData',
        name: 'Sync CME Tick Data Feed',
        enabled: true,
        status: 'idle',
        input: 'CME NQ Futures',
        output: 'Updated Market Cache',
        config: { provider: 'Futures Tick Feed', barsToSync: 50000 },
      },
      {
        id: 'w2-2',
        type: 'Build',
        name: 'Evolve Range Breakout Candidates',
        enabled: true,
        status: 'idle',
        input: 'NQ M15',
        output: 'Candidates',
        config: { symbol: 'NQ', timeframe: 'M15', targetCount: 20, maxDrawdownPct: 15 },
      },
      {
        id: 'w2-3',
        type: 'CustomAnalysis',
        name: 'Monte Carlo Trade Reshuffling Confidence',
        enabled: true,
        status: 'idle',
        input: 'Candidates',
        output: 'Robust Candidates',
        config: { confidenceLevel: 95, simulations: 1000 },
      },
      {
        id: 'w2-4',
        type: 'Notification',
        name: 'Send Slack / Webhook Alert',
        enabled: true,
        status: 'idle',
        input: 'Robust Candidates',
        output: 'Webhook Endpoint',
        config: { webhookUrl: 'https://hooks.slack.com/services/quant-alerts', notifyOnSuccess: true },
      },
    ],
  },
];

export const extensionFiles: ExtensionFile[] = [
  {
    id: 'ext-1',
    name: 'KeltnerChannel.java',
    category: 'Indicators',
    language: 'java',
    content: `package HaruQuantAI.Indicators;

import haruquantai.lib.core.*;
import haruquantai.lib.indicators.*;

/**
 * Keltner Channel Volatility Envelope Indicator
 * Standard StrategyQuant X extension definition.
 */
public class KeltnerChannel extends Indicator {
    @Parameter(name = "Period", defaultValue = "20", min = 2, max = 200)
    public int period = 20;

    @Parameter(name = "Multiplier", defaultValue = "2.0", min = 0.5, max = 10.0)
    public double multiplier = 2.0;

    @Output(name = "UpperBand")
    public DataSeries upper;

    @Output(name = "MiddleBand")
    public DataSeries middle;

    @Output(name = "LowerBand")
    public DataSeries lower;

    @Override
    public void compute(int bar) {
        middle.set(bar, Indicators.EMA(chart.Close, period, bar));
        double atr = Indicators.ATR(chart, period, bar);
        upper.set(bar, middle.get(bar) + (multiplier * atr));
        lower.set(bar, middle.get(bar) - (multiplier * atr));
    }
}`,
  },
  {
    id: 'ext-2',
    name: 'TrailingStopVolatility.java',
    category: 'Snippets',
    language: 'java',
    content: `package HaruQuantAI.Snippets;

import haruquantai.lib.order.*;

public class TrailingStopVolatility {
    public static void applyTrailingStop(Order order, double currentPrice, double atrValue, double atrMultiplier) {
        if (order.isLong()) {
            double newStop = currentPrice - (atrValue * atrMultiplier);
            if (newStop > order.getStopLoss()) {
                order.setStopLoss(newStop);
            }
        } else if (order.isShort()) {
            double newStop = currentPrice + (atrValue * atrMultiplier);
            if (newStop < order.getStopLoss() || order.getStopLoss() == 0) {
                order.setStopLoss(newStop);
            }
        }
    }
}`,
  },
  {
    id: 'ext-3',
    name: 'SuperTrendBlock.java',
    category: 'Blocks',
    language: 'java',
    content: `package HaruQuantAI.Blocks;

import haruquantai.lib.buildingblocks.*;

@BuildingBlock(name = "SuperTrend Direction Filter", category = "Trend Filters")
public class SuperTrendBlock extends ConditionBlock {
    @Parameter(name = "Period", defaultValue = "10")
    public int period = 10;

    @Parameter(name = "Multiplier", defaultValue = "3.0")
    public double multiplier = 3.0;

    @Override
    public boolean evaluate(Chart chart, int bar) {
        double currentClose = chart.Close.get(bar);
        double supertrend = Indicators.SuperTrend(chart, period, multiplier, bar);
        return currentClose > supertrend;
    }
}`,
  },
  {
    id: 'ext-4',
    name: 'UlcerIndexColumn.java',
    category: 'Columns',
    language: 'java',
    content: `package HaruQuantAI.Columns;

import haruquantai.lib.databank.*;

public class UlcerIndexColumn extends DatabankColumn {
    public UlcerIndexColumn() {
        super("Ulcer Index", "UI", "Downside risk measurement of strategy equity drawdowns.");
    }

    @Override
    public double calculate(StrategyResult result) {
        double[] dd = result.getDrawdownSeries();
        if (dd == null || dd.length == 0) return 0.0;
        double sumSq = 0.0;
        for (double d : dd) {
            sumSq += (d * d);
        }
        return Math.sqrt(sumSq / dd.length);
    }
}`,
  },
  {
    id: 'ext-5',
    name: 'WalkForwardEfficiency.java',
    category: 'CustomAnalysis',
    language: 'java',
    content: `package HaruQuantAI.CustomAnalysis;

import haruquantai.lib.analysis.*;

public class WalkForwardEfficiency extends AnalysisPlugin {
    @Override
    public AnalysisResult analyze(StrategyResult isResult, StrategyResult oosResult) {
        double isAnnualized = isResult.getAnnualizedReturn();
        double oosAnnualized = oosResult.getAnnualizedReturn();
        double wfe = isAnnualized > 0 ? (oosAnnualized / isAnnualized) * 100.0 : 0.0;
        return new AnalysisResult("Walk-Forward Efficiency (%)", wfe, wfe >= 50.0 ? Verdict.PASS : Verdict.FAIL);
    }
}`,
  },
  {
    id: 'ext-6',
    name: 'EquityDriftHeatmap.java',
    category: 'ResultsPlugins',
    language: 'java',
    content: `package HaruQuantAI.ResultsPlugins;

import haruquantai.lib.visualization.*;

public class EquityDriftHeatmap extends VisualResultTab {
    @Override
    public String getTabTitle() {
        return "Equity Drift Analysis";
    }

    @Override
    public RenderableMatrix render(StrategyResult result) {
        return MatrixGenerator.generateRollingMonthlyReturns(result.getEquityCurve());
    }
}`,
  },
];

export const computeNodes: ComputeNode[] = [
  {
    id: 'node-local',
    name: 'Master Node (Local Engine)',
    host: '127.0.0.1',
    ip: '127.0.0.1',
    port: 9091,
    cores: 16,
    memoryGb: 32,
    gpu: true,
    status: 'Online',
    cpuUsagePct: 24,
    latencyMs: 1,
    activeTask: 'Pipeline Execution Manager',
  },
  {
    id: 'node-cluster-1',
    name: 'Cluster-Alpha (Dedicated Server)',
    host: 'alpha.cluster.internal',
    ip: '192.168.1.101',
    port: 9092,
    cores: 32,
    memoryGb: 64,
    gpu: true,
    status: 'Busy',
    cpuUsagePct: 88,
    latencyMs: 3,
    activeTask: 'Genetic Evolution: Gen 42/100 (EURUSD H1)',
  },
  {
    id: 'node-cluster-2',
    name: 'Cluster-Beta (Cloud Compute Instance)',
    host: 'beta.cluster.internal',
    ip: '10.0.0.15',
    port: 9092,
    cores: 16,
    memoryGb: 32,
    gpu: false,
    status: 'Idle',
    cpuUsagePct: 6,
    latencyMs: 18,
  },
  {
    id: 'node-cluster-3',
    name: 'Cluster-Gamma (Backup Instance)',
    host: 'gamma.cluster.internal',
    ip: '10.0.0.16',
    port: 9092,
    cores: 8,
    memoryGb: 16,
    gpu: false,
    status: 'Offline',
    cpuUsagePct: 0,
    latencyMs: 0,
  },
];

export const businessConfig: BusinessConfig = {
  organization: 'Haru Quant Capital Inc.',
  activeWorkspace: 'Production Quantitative Alpha',
  workspaces: [
    { id: 'ws-1', name: 'Production Quantitative Alpha', coresAllocated: 48, memoryAllocated: 96 },
    { id: 'ws-2', name: 'R&D Sandbox (Crypto / Futures)', coresAllocated: 16, memoryAllocated: 32 },
    { id: 'ws-3', name: 'Backtesting Cluster West', coresAllocated: 8, memoryAllocated: 16 },
  ],
  users: [
    { id: 'u-1', name: 'Haru Peri', email: 'haru@quantai.internal', role: 'Owner', status: 'Active' },
    { id: 'u-2', name: 'Alex Vance', email: 'alex@quantai.internal', role: 'Quant Researcher', status: 'Active' },
    { id: 'u-3', name: 'Elena Rostova', email: 'elena@quantai.internal', role: 'Risk Manager', status: 'Active' },
    { id: 'u-4', name: 'Audit Service Agent', email: 'audit@quantai.internal', role: 'Viewer', status: 'Service Account' },
  ],
  mcpServers: [
    {
      id: 'mcp-1',
      name: 'Antigravity Alpha Agent Gateway',
      url: 'http://localhost:8080/mcp/v1',
      transport: 'sse',
      status: 'Connected',
      capabilities: ['strategy_generation', 'backtest_execution', 'code_synthesis'],
      activeCalls: 2,
    },
    {
      id: 'mcp-2',
      name: 'QuantConnect Cloud Bridge',
      url: 'stdio:qc-bridge',
      transport: 'stdio',
      status: 'Connected',
      capabilities: ['live_data_feed', 'order_routing'],
      activeCalls: 0,
    },
    {
      id: 'mcp-3',
      name: 'OpenAI Reasoning Engine',
      url: 'http://localhost:8081/mcp/v1',
      transport: 'sse',
      status: 'Connected',
      capabilities: ['prompt_optimization', 'code_explanation'],
      activeCalls: 1,
    },
  ],
};
