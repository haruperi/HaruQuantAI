/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { Job, BuilderSettings, JobStatus, CrossCheckItem } from './documents';
interface LocalState { jobs: Record<string, Job>;
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

const useLocalState = create<LocalState>()(persist((set) => ({jobs: {},
builder: initialBuilder, reset: () => set({jobs: {},
builder: initialBuilder})}), {name: 'workspace.debug_console.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), merge:mergeViewState}));

type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
