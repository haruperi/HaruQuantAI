/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { ModuleId, Strategy, Trade, EquityPoint } from './documents';
interface LocalState { strategies: Strategy[]; reset: () => void; }

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
const useLocalState = create<LocalState>()(persist((set) => ({strategies, reset: () => set({strategies})}), {name: 'workspace.home.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), partialize: state => { const {strategies: _strategies, ...view} = state; return view; }, merge:mergeViewState}));
connectPreviewDocument(useLocalState, 'strategies', 'preview.research.strategies', previewResources);
type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
