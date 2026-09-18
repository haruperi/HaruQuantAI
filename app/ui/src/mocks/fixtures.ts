import type { Databank, Dataset, Instrument, PortfolioMember, RuleNode, Strategy, Trade, WorkflowTask } from '../app/types';

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
  { id: 'd3', source: 'SQ Futures', symbol: 'NQ', timeframe: 'Tick → D1', from: '2014-01-02', to: '2026-08-31', bars: 12861244, quality: 98.9, status: 'Ready' },
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
