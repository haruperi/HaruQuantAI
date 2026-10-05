/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { BatchExecutionResult, SingleExecutionResult, RuleNode, Strategy, BuilderSettings, BatchTrialResult, ValidationIssue, ExecutionReproducibilityRecord, Trade, EquityPoint, CrossCheckItem, NumericalPolicy } from './documents';
interface LocalState { strategies: Strategy[];
rules: RuleNode[];
builder: BuilderSettings; reset: () => void; }
const initialBuilder: BuilderSettings = {
  mode: 'Genetic evolution',
  strategyType: 'Standard',
  symbol: 'EURUSD',
  timeframe: 'H1',
  direction: 'Both',
  population: 100,
  islands: 4,
  mutation: 35,
  crossover: 85,
  maxConditions: 5,
  minConditions: 1,
  maxPeriods: 200,
  minPeriods: 5,
  symmetricalRules: true,
  fuzzySignals: false,
  generateExitRules: true,
  stopLoss: true,
  profitTarget: true,
  slMin: 40,
  slMax: 180,
  ptMin: 80,
  ptMax: 360,
  slType: 'Fixed pips',
  ptType: 'Fixed pips',
  useTrailingStop: false,
  trailingStopMin: 20,
  trailingStopMax: 80,
  useMoveToBE: false,
  beTriggerPips: 30,
  beProfitOffset: 5,
  mmModel: 'Fixed Size',
  initialCapital: 10000,
  riskPercent: 1.5,
  fixedLots: 0.1,
  maxGenerations: 100,
  migrateCandidates: true,
  migrationInterval: 10,
  restartStagnantIslands: true,
  stagnantGenerations: 20,
  seedFromDatabank: false,
  inputDatabank: 'Results',
  rankingMetric: 'Return / Drawdown ratio',
  minReturnDD: 1.4,
  minTrades: 80,
  maxDrawdownPct: 25,
  minSharpe: 1.0,
  minProfitFactor: 1.3,
  crossChecks: [
    { id: 'precision', name: 'Higher testing precision', enabled: true },
    { id: 'additional_markets', name: 'Additional markets', enabled: true },
    { id: 'mc_trades', name: 'Monte Carlo trades', enabled: true },
    { id: 'mc_retest', name: 'Monte Carlo retest', enabled: true },
    { id: 'what_if', name: 'What-if analysis', enabled: false },
    { id: 'opt_profile', name: 'Optimization profile', enabled: false },
    { id: 'walk_forward', name: 'Walk-forward', enabled: false },
    { id: 'seq_opt', name: 'Sequential optimization', enabled: false },
  ],
  customBlocks: {},
  precision: 'Selected timeframe only',
  from: '2012-01-01',
  to: '2026-08-31',
  oos: 30,
};
const strategies: Strategy[] = Array.from({ length: 70 }, (_, i) => buildStrategy(i, i < 40 ? 'results' : i < 58 ? 'retest' : 'portfolio'));
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
const rules: RuleNode[] = JSON.parse("[{\"id\":\"r1\",\"depth\":0,\"kind\":\"event\",\"label\":\"On Bar Open\"},{\"id\":\"r2\",\"depth\":1,\"kind\":\"if\",\"label\":\"IF\"},{\"id\":\"r3\",\"depth\":2,\"kind\":\"condition\",\"label\":\"EMA(12) crosses above EMA(28)\"},{\"id\":\"r4\",\"depth\":2,\"kind\":\"condition\",\"label\":\"ATR(14) > 0.0012\"},{\"id\":\"r5\",\"depth\":1,\"kind\":\"then\",\"label\":\"THEN\"},{\"id\":\"r6\",\"depth\":2,\"kind\":\"action\",\"label\":\"Enter at Market (Long)\"},{\"id\":\"r7\",\"depth\":2,\"kind\":\"action\",\"label\":\"Set Stop Loss: 90 pips\"},{\"id\":\"r8\",\"depth\":2,\"kind\":\"action\",\"label\":\"Set Profit Target: 180 pips\"}]");
const useLocalState = create<LocalState>()(persist((set) => ({strategies,
rules,
builder: initialBuilder, reset: () => set({strategies,
rules,
builder: initialBuilder})}), {name: 'workspace.builder.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), partialize: state => { const {strategies: _strategies, ...view} = state; return view; }, merge:mergeViewState}));
connectPreviewDocument(useLocalState, 'strategies', 'preview.research.strategies', previewResources);
type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
