import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AppSettings, BuilderSettings, Databank, Job, ModuleId, OptimizationSettings, PortfolioMember, ProjectTab, RuleNode, Strategy, WorkflowTask } from './types';
import { databanks, portfolioMembers, rules, strategies, workflowTasks } from '../mocks/fixtures';

interface AppState {
  module: ModuleId; tab: ProjectTab; selectedStrategyId: string; resultView: string; selectedBankId: string; selectedRows: string[];
  strategies: Strategy[]; databanks: Databank[]; jobs: Record<string, Job>; settings: AppSettings; builder: BuilderSettings; optimization: OptimizationSettings;
  rules: RuleNode[]; portfolio: PortfolioMember[]; workflow: WorkflowTask[]; notifications: string[];
  setModule: (module: ModuleId) => void; setTab: (tab: ProjectTab) => void; selectStrategy: (id: string) => void; setResultView: (view: string) => void;
  setBank: (id: string) => void; setRows: (ids: string[]) => void; updateSettings: (patch: Partial<AppSettings>) => void; updateBuilder: (patch: Partial<BuilderSettings>) => void;
  updateOptimization: (patch: Partial<OptimizationSettings>) => void; setJob: (module: string, job: Job) => void; patchJob: (module: string, patch: Partial<Job>) => void;
  addStrategies: (items: Strategy[], bankId: string) => void; moveStrategies: (ids: string[], targetBank: string, copy: boolean) => void; deleteStrategies: (ids: string[]) => void;
  renameStrategy: (id: string, name: string, note: string) => void; addRule: (rule: RuleNode) => void; removeRule: (id: string) => void; moveRule: (id: string, offset: number) => void;
  updatePortfolio: (id: string, patch: Partial<PortfolioMember>) => void; setWorkflow: (tasks: WorkflowTask[]) => void; notify: (message: string) => void; reset: () => void;
}

const initialSettings: AppSettings = { theme: 'dark', language: 'English', autosave: true, workers: 8, memoryGb: 10, profile: 'Full' };
const initialBuilder: BuilderSettings = { mode: 'Genetic evolution', strategyType: 'Standard', symbol: 'EURUSD', timeframe: 'H1', direction: 'Both', population: 100, islands: 4, mutation: 35, crossover: 85, maxConditions: 5, stopLoss: true, profitTarget: true, slMin: 40, slMax: 180, ptMin: 80, ptMax: 360, precision: 'Selected timeframe only', from: '2012-01-01', to: '2026-08-31', oos: 30 };
const initialOptimization: OptimizationSettings = { mode: 'Simple', parameter: 'FastPeriod', min: 5, max: 50, step: 5, objective: 'Return / Drawdown ratio', keep: 20 };

export const useAppStore = create<AppState>()(persist((set) => ({
  module: 'builder', tab: 'progress', selectedStrategyId: 'str-1', resultView: 'Overview', selectedBankId: 'results', selectedRows: [],
  strategies, databanks, jobs: {}, settings: initialSettings, builder: initialBuilder, optimization: initialOptimization, rules, portfolio: portfolioMembers, workflow: workflowTasks, notifications: [],
  setModule: module => set({ module, tab: ['datamanager', 'algowizard', 'composer', 'codeeditor', 'business', 'home'].includes(module) ? 'settings' : 'progress' }),
  setTab: tab => set({ tab }), selectStrategy: selectedStrategyId => set({ selectedStrategyId }), setResultView: resultView => set({ resultView }),
  setBank: selectedBankId => set({ selectedBankId, selectedRows: [] }), setRows: selectedRows => set({ selectedRows }),
  updateSettings: patch => set(s => ({ settings: { ...s.settings, ...patch } })), updateBuilder: patch => set(s => ({ builder: { ...s.builder, ...patch } })),
  updateOptimization: patch => set(s => ({ optimization: { ...s.optimization, ...patch } })), setJob: (module, job) => set(s => ({ jobs: { ...s.jobs, [module]: job } })),
  patchJob: (module, patch) => set(s => ({ jobs: { ...s.jobs, [module]: { ...s.jobs[module], ...patch } } })),
  addStrategies: (items, bankId) => set(s => ({ strategies: [...s.strategies, ...items.filter(x => !s.strategies.some(y => y.id === x.id))], databanks: s.databanks.map(b => b.id === bankId ? { ...b, strategyIds: [...new Set([...b.strategyIds, ...items.map(x => x.id)])] } : b) })),
  moveStrategies: (ids, targetBank, copy) => set(s => ({ databanks: s.databanks.map(b => b.id === targetBank ? { ...b, strategyIds: [...new Set([...b.strategyIds, ...ids])] } : !copy ? { ...b, strategyIds: b.strategyIds.filter(id => !ids.includes(id)) } : b), strategies: s.strategies.map(x => ids.includes(x.id) && !copy ? { ...x, bankId: targetBank } : x), selectedRows: [] })),
  deleteStrategies: ids => set(s => ({ strategies: s.strategies.filter(x => !ids.includes(x.id)), databanks: s.databanks.map(b => ({ ...b, strategyIds: b.strategyIds.filter(id => !ids.includes(id)) })), selectedRows: [] })),
  renameStrategy: (id, name, note) => set(s => ({ strategies: s.strategies.map(x => x.id === id ? { ...x, name, note } : x) })),
  addRule: rule => set(s => ({ rules: [...s.rules, rule] })), removeRule: id => set(s => ({ rules: s.rules.filter(r => r.id !== id) })),
  moveRule: (id, offset) => set(s => { const list = [...s.rules]; const index = list.findIndex(r => r.id === id); const target = Math.max(0, Math.min(list.length - 1, index + offset)); if (index < 0 || target === index) return {}; [list[index], list[target]] = [list[target], list[index]]; return { rules: list }; }),
  updatePortfolio: (id, patch) => set(s => ({ portfolio: s.portfolio.map(m => m.strategyId === id ? { ...m, ...patch } : m) })), setWorkflow: workflow => set({ workflow }),
  notify: message => set(s => ({ notifications: [message, ...s.notifications].slice(0, 8) })),
  reset: () => set({ module: 'builder', tab: 'progress', selectedStrategyId: 'str-1', resultView: 'Overview', selectedBankId: 'results', selectedRows: [], strategies, databanks, jobs: {}, settings: initialSettings, builder: initialBuilder, optimization: initialOptimization, rules, portfolio: portfolioMembers, workflow: workflowTasks, notifications: [] }),
}), { name: 'sqx-recreation-v1', version: 1, partialize: s => ({ ...s, notifications: [] }) }));
