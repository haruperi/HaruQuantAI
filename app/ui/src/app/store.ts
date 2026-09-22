import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AppSettings, BuilderSettings, BusinessConfig, BusinessUser, BusinessWorkspaceItem, ComputeNode, CustomProject, Databank, ExtensionFile, Job, McpServerConfig, ModuleId, OptimizationSettings, PortfolioMasterSettings, PortfolioMember, PortfolioSettings, ProjectTab, RetesterSettings, RuleNode, Strategy, WorkflowTask } from './types';
import { businessConfig, computeNodes } from '../workspace/Business/fixtures';
import { rules } from '../workspace/Builder/fixtures';
import { extensionFiles } from '../workspace/CodeEditor/fixtures';
import { customProjects, workflowTasks } from '../workspace/CustomProjects/fixtures';
import { portfolioMembers } from '../workspace/PortfolioComposer/fixtures';
import { databanks, strategies } from '../plugins/databank/fixtures';
import { createInitialAppSettings, mergeAppSettings } from './globalSettings';
import type { BatchExecutionResult, SingleExecutionResult } from './transport';

interface AppState {
  module: ModuleId; tab: ProjectTab; selectedStrategyId: string; resultView: string; selectedBankId: string; selectedRows: string[];
  strategies: Strategy[]; databanks: Databank[]; jobs: Record<string, Job>; settings: AppSettings; builder: BuilderSettings; optimization: OptimizationSettings; retester: RetesterSettings;
  portfolioSettings: PortfolioSettings; portfolioMasterSettings: PortfolioMasterSettings;
  rules: RuleNode[]; portfolio: PortfolioMember[]; workflow: WorkflowTask[]; notifications: string[];
  projects: CustomProject[]; activeProjectId: string;
  extensionFiles: ExtensionFile[]; activeFileId: string; openFileIds: string[]; compileOutput: string;
  computeNodes: ComputeNode[]; businessConfig: BusinessConfig;
  lastExecutionResult: SingleExecutionResult | null; lastBatchResult: BatchExecutionResult | null;
  setLastExecutionResult: (res: SingleExecutionResult | null) => void;
  setLastBatchResult: (res: BatchExecutionResult | null) => void;
  setModule: (module: ModuleId) => void; setTab: (tab: ProjectTab) => void; selectStrategy: (id: string) => void; setResultView: (view: string) => void;
  setBank: (id: string) => void; setRows: (ids: string[]) => void; updateSettings: (patch: Partial<AppSettings>) => void; updateBuilder: (patch: Partial<BuilderSettings>) => void;
  updateOptimization: (patch: Partial<OptimizationSettings>) => void; updateRetester: (patch: Partial<RetesterSettings>) => void;
  updatePortfolioSettings: (patch: Partial<PortfolioSettings>) => void; updatePortfolioMasterSettings: (patch: Partial<PortfolioMasterSettings>) => void;
  setJob: (module: string, job: Job) => void; patchJob: (module: string, patch: Partial<Job>) => void;
  addStrategies: (items: Strategy[], bankId: string) => void; moveStrategies: (ids: string[], targetBank: string, copy: boolean) => void; deleteStrategies: (ids: string[]) => void;
  renameStrategy: (id: string, name: string, note: string) => void;
  addRule: (rule: RuleNode) => void; updateRule: (id: string, patch: Partial<RuleNode>) => void; removeRule: (id: string) => void; moveRule: (id: string, offset: number) => void;
  clearRules: () => void; loadStrategyTemplate: (templateRules: RuleNode[]) => void;
  updatePortfolio: (id: string, patch: Partial<PortfolioMember>) => void; setPortfolioMembers: (members: PortfolioMember[]) => void;
  addPortfolioMember: (member: PortfolioMember) => void; removePortfolioMember: (strategyId: string) => void; normalizePortfolioWeights: () => void;
  setWorkflow: (tasks: WorkflowTask[]) => void;
  addProject: (project: CustomProject) => void; updateProject: (id: string, patch: Partial<CustomProject>) => void; deleteProject: (id: string) => void; setActiveProject: (id: string) => void;
  addTaskToProject: (projectId: string, task: WorkflowTask) => void; updateTaskInProject: (projectId: string, taskId: string, patch: Partial<WorkflowTask>) => void;
  removeTaskFromProject: (projectId: string, taskId: string) => void; reorderTaskInProject: (projectId: string, taskId: string, offset: number) => void; setProjectTasks: (projectId: string, tasks: WorkflowTask[]) => void;
  setActiveFile: (id: string) => void; openFile: (id: string) => void; closeFile: (id: string) => void; updateFileContent: (id: string, content: string) => void;
  saveFile: (id: string) => void; addExtensionFile: (file: ExtensionFile) => void; deleteExtensionFile: (id: string) => void; setCompileOutput: (output: string) => void;
  addComputeNode: (node: ComputeNode) => void; updateComputeNode: (id: string, patch: Partial<ComputeNode>) => void; removeComputeNode: (id: string) => void;
  updateBusinessConfig: (patch: Partial<BusinessConfig>) => void; addBusinessWorkspace: (ws: BusinessWorkspaceItem) => void; addBusinessUser: (user: BusinessUser) => void;
  addMcpServer: (server: McpServerConfig) => void; updateMcpServer: (id: string, patch: Partial<McpServerConfig>) => void; removeMcpServer: (id: string) => void;
  notify: (message: string) => void; reset: () => void;
}

const initialSettings: AppSettings = createInitialAppSettings();

const initialPortfolioSettings: PortfolioSettings = {
  initialCapital: 100000,
  leverage: 20,
  weightingModel: 'Manual weights',
  maxCorrelation: 0.55,
  maxStrategies: 8,
  maxSectorWeight: 40,
  dateRange: 'full',
  startDate: '2015-01-01',
  endDate: '2026-08-31',
  sharedCapital: true,
  skipOnMargin: true,
};

const initialPortfolioMasterSettings: PortfolioMasterSettings = {
  searchType: 'bruteforce',
  sourceDatabank: 'Results',
  targetDatabank: 'Portfolio',
  minStrategies: 3,
  maxStrategies: 6,
  maxCorrelation: 0.50,
  fitness: 'Return / Drawdown ratio',
  population: 100,
  generations: 30,
  mutation: 30,
  crossover: 80,
};

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

const initialOptimization: OptimizationSettings = {
  mode: 'Simple',
  source: 'databank',
  sourceDatabank: 'Results',
  outputDatabank: 'Results',
  parameter: 'FastPeriod',
  min: 5,
  max: 50,
  step: 5,
  objective: 'Return / Drawdown ratio',
  keep: 20,
  parameters: [
    { name: 'FastPeriod', enabled: true, min: 5, max: 50, step: 5, originalValue: 14 },
    { name: 'SlowPeriod', enabled: true, min: 20, max: 200, step: 10, originalValue: 50 },
    { name: 'ATRPeriod', enabled: false, min: 7, max: 28, step: 7, originalValue: 14 },
    { name: 'StopLoss', enabled: false, min: 30, max: 150, step: 15, originalValue: 60 },
    { name: 'ProfitTarget', enabled: false, min: 60, max: 300, step: 30, originalValue: 120 },
  ],
  isMonths: 24,
  oosMonths: 6,
  wfRuns: 8,
  storeBestRevisions: true,
  storeAllTrials: false,
};

const initialRetester: RetesterSettings = {
  sourceDatabank: 'Results',
  outputDatabank: 'Retest',
  symbol: 'EURUSD',
  timeframe: 'H1',
  precision: 'Selected timeframe only',
  from: '2015-01-01',
  to: '2026-08-31',
  spreadMultiplier: 1.0,
  slippagePips: 0,
  stressSpreadSlippage: false,
  skipWorstTradesPct: 0,
  tradeDirection: 'Both',
  additionalMarkets: ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'],
  additionalTimeframes: ['M15', 'M30', 'H1', 'H4'],
  portfolioRetest: false,
};

export const useAppStore = create<AppState>()(persist((set) => ({
  module: 'builder', tab: 'progress', selectedStrategyId: 'str-1', resultView: 'Overview', selectedBankId: 'results', selectedRows: [],
  strategies, databanks, jobs: {}, settings: initialSettings, builder: initialBuilder, optimization: initialOptimization, retester: initialRetester,
  portfolioSettings: initialPortfolioSettings, portfolioMasterSettings: initialPortfolioMasterSettings,
  rules, portfolio: portfolioMembers, workflow: workflowTasks, notifications: [],
  projects: customProjects, activeProjectId: customProjects[0].id,
  extensionFiles, activeFileId: extensionFiles[0].id, openFileIds: [extensionFiles[0].id],
  compileOutput: '[info] Compiler ready. Select an extension and click Compile to run AST validation.',
  computeNodes, businessConfig,
  setModule: module => set({ module, tab: ['datamanager', 'algowizard', 'composer', 'codeeditor', 'business', 'home', 'debugconsole', 'gridcontrol'].includes(module) ? 'settings' : 'progress' }),
  setTab: tab => set({ tab }), selectStrategy: selectedStrategyId => set({ selectedStrategyId }), setResultView: resultView => set({ resultView }),
  setBank: selectedBankId => set({ selectedBankId, selectedRows: [] }), setRows: selectedRows => set({ selectedRows }),
  updateSettings: patch => set(s => ({ settings: { ...s.settings, ...patch } })), updateBuilder: patch => set(s => ({ builder: { ...s.builder, ...patch } })),
  updateOptimization: patch => set(s => ({ optimization: { ...s.optimization, ...patch } })),
  updateRetester: patch => set(s => ({ retester: { ...s.retester, ...patch } })),
  updatePortfolioSettings: patch => set(s => ({ portfolioSettings: { ...s.portfolioSettings, ...patch } })),
  updatePortfolioMasterSettings: patch => set(s => ({ portfolioMasterSettings: { ...s.portfolioMasterSettings, ...patch } })),
  setJob: (module, job) => set(s => ({ jobs: { ...s.jobs, [module]: job } })),
  patchJob: (module, patch) => set(s => ({ jobs: { ...s.jobs, [module]: { ...s.jobs[module], ...patch } } })),
  addStrategies: (items, bankId) => set(s => ({ strategies: [...s.strategies, ...items.filter(x => !s.strategies.some(y => y.id === x.id))], databanks: s.databanks.map(b => b.id === bankId ? { ...b, strategyIds: [...new Set([...b.strategyIds, ...items.map(x => x.id)])] } : b) })),
  moveStrategies: (ids, targetBank, copy) => set(s => ({ databanks: s.databanks.map(b => b.id === targetBank ? { ...b, strategyIds: [...new Set([...b.strategyIds, ...ids])] } : !copy ? { ...b, strategyIds: b.strategyIds.filter(id => !ids.includes(id)) } : b), strategies: s.strategies.map(x => ids.includes(x.id) && !copy ? { ...x, bankId: targetBank } : x), selectedRows: [] })),
  deleteStrategies: ids => set(s => ({ strategies: s.strategies.filter(x => !ids.includes(x.id)), databanks: s.databanks.map(b => ({ ...b, strategyIds: b.strategyIds.filter(id => !ids.includes(id)) })), selectedRows: [] })),
  renameStrategy: (id, name, note) => set(s => ({ strategies: s.strategies.map(x => x.id === id ? { ...x, name, note } : x) })),
  addRule: rule => set(s => ({ rules: [...s.rules, rule] })),
  updateRule: (id, patch) => set(s => ({ rules: s.rules.map(r => r.id === id ? { ...r, ...patch } : r) })),
  removeRule: id => set(s => ({ rules: s.rules.filter(r => r.id !== id) })),
  moveRule: (id, offset) => set(s => { const list = [...s.rules]; const index = list.findIndex(r => r.id === id); const target = Math.max(0, Math.min(list.length - 1, index + offset)); if (index < 0 || target === index) return {}; [list[index], list[target]] = [list[target], list[index]]; return { rules: list }; }),
  clearRules: () => set({ rules: [] }),
  loadStrategyTemplate: templateRules => set({ rules: templateRules }),
  updatePortfolio: (id, patch) => set(s => ({ portfolio: s.portfolio.map(m => m.strategyId === id ? { ...m, ...patch } : m) })),
  setPortfolioMembers: members => set({ portfolio: members }),
  addPortfolioMember: member => set(s => ({ portfolio: [...s.portfolio.filter(m => m.strategyId !== member.strategyId), member] })),
  removePortfolioMember: strategyId => set(s => ({ portfolio: s.portfolio.filter(m => m.strategyId !== strategyId) })),
  normalizePortfolioWeights: () => set(s => {
    const active = s.portfolio.filter(m => m.enabled);
    if (active.length === 0) return {};
    const sum = active.reduce((acc, m) => acc + m.weight, 0);
    if (sum === 0) {
      const eq = Math.floor(100 / active.length);
      return { portfolio: s.portfolio.map(m => m.enabled ? { ...m, weight: eq } : m) };
    }
    const activeIndices = s.portfolio.map((m, idx) => m.enabled ? idx : -1).filter(idx => idx >= 0);
    const lastActiveIdx = activeIndices.length > 0 ? activeIndices[activeIndices.length - 1] : -1;
    let allocated = 0;
    const updated = s.portfolio.map((m, i) => {
      if (!m.enabled) return m;
      const isLast = i === lastActiveIdx;
      const normalized = isLast ? Math.max(0, 100 - allocated) : Math.round((m.weight / sum) * 100);
      allocated += normalized;
      return { ...m, weight: Math.max(0, normalized) };
    });
    return { portfolio: updated };
  }),
  setWorkflow: workflow => set({ workflow }),
  addProject: project => set(s => ({ projects: [...s.projects, project], activeProjectId: project.id })),
  updateProject: (id, patch) => set(s => ({ projects: s.projects.map(p => p.id === id ? { ...p, ...patch } : p) })),
  deleteProject: id => set(s => {
    const nextProjects = s.projects.filter(p => p.id !== id);
    return {
      projects: nextProjects,
      activeProjectId: s.activeProjectId === id ? (nextProjects[0]?.id || '') : s.activeProjectId,
    };
  }),
  setActiveProject: activeProjectId => set({ activeProjectId }),
  addTaskToProject: (projectId, task) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? { ...p, tasks: [...p.tasks, task] } : p),
  })),
  updateTaskInProject: (projectId, taskId, patch) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? {
      ...p,
      tasks: p.tasks.map(t => t.id === taskId ? { ...t, ...patch } : t),
    } : p),
  })),
  removeTaskFromProject: (projectId, taskId) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? {
      ...p,
      tasks: p.tasks.filter(t => t.id !== taskId),
    } : p),
  })),
  reorderTaskInProject: (projectId, taskId, offset) => set(s => {
    const project = s.projects.find(p => p.id === projectId);
    if (!project) return {};
    const list = [...project.tasks];
    const index = list.findIndex(t => t.id === taskId);
    const target = Math.max(0, Math.min(list.length - 1, index + offset));
    if (index < 0 || target === index) return {};
    [list[index], list[target]] = [list[target], list[index]];
    return {
      projects: s.projects.map(p => p.id === projectId ? { ...p, tasks: list } : p),
    };
  }),
  setProjectTasks: (projectId, tasks) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? { ...p, tasks } : p),
  })),
  setActiveFile: activeFileId => set(s => ({
    activeFileId,
    openFileIds: s.openFileIds.includes(activeFileId) ? s.openFileIds : [...s.openFileIds, activeFileId],
  })),
  openFile: id => set(s => ({
    activeFileId: id,
    openFileIds: s.openFileIds.includes(id) ? s.openFileIds : [...s.openFileIds, id],
  })),
  closeFile: id => set(s => {
    const nextOpen = s.openFileIds.filter(fId => fId !== id);
    const nextActive = s.activeFileId === id ? (nextOpen[nextOpen.length - 1] || '') : s.activeFileId;
    return { openFileIds: nextOpen, activeFileId: nextActive };
  }),
  updateFileContent: (id, content) => set(s => ({
    extensionFiles: s.extensionFiles.map(f => f.id === id ? { ...f, content, dirty: true } : f),
  })),
  saveFile: id => set(s => ({
    extensionFiles: s.extensionFiles.map(f => f.id === id ? { ...f, dirty: false } : f),
  })),
  addExtensionFile: file => set(s => ({
    extensionFiles: [...s.extensionFiles, file],
    activeFileId: file.id,
    openFileIds: [...s.openFileIds, file.id],
  })),
  deleteExtensionFile: id => set(s => {
    const nextFiles = s.extensionFiles.filter(f => f.id !== id);
    const nextOpen = s.openFileIds.filter(fId => fId !== id);
    return {
      extensionFiles: nextFiles,
      openFileIds: nextOpen,
      activeFileId: s.activeFileId === id ? (nextOpen[0] || nextFiles[0]?.id || '') : s.activeFileId,
    };
  }),
  setCompileOutput: compileOutput => set({ compileOutput }),
  addComputeNode: node => set(s => ({ computeNodes: [...s.computeNodes, node] })),
  updateComputeNode: (id, patch) => set(s => ({
    computeNodes: s.computeNodes.map(n => n.id === id ? { ...n, ...patch } : n),
  })),
  removeComputeNode: id => set(s => ({
    computeNodes: s.computeNodes.filter(n => n.id !== id),
  })),
  updateBusinessConfig: patch => set(s => ({
    businessConfig: { ...s.businessConfig, ...patch },
  })),
  addBusinessWorkspace: ws => set(s => ({
    businessConfig: { ...s.businessConfig, workspaces: [...s.businessConfig.workspaces, ws] },
  })),
  addBusinessUser: user => set(s => ({
    businessConfig: { ...s.businessConfig, users: [...s.businessConfig.users, user] },
  })),
  addMcpServer: server => set(s => ({
    businessConfig: { ...s.businessConfig, mcpServers: [...s.businessConfig.mcpServers, server] },
  })),
  updateMcpServer: (id, patch) => set(s => ({
    businessConfig: {
      ...s.businessConfig,
      mcpServers: s.businessConfig.mcpServers.map(m => m.id === id ? { ...m, ...patch } : m),
    },
  })),
  removeMcpServer: id => set(s => ({
    businessConfig: {
      ...s.businessConfig,
      mcpServers: s.businessConfig.mcpServers.filter(m => m.id !== id),
    },
  })),
  lastExecutionResult: null,
  lastBatchResult: null,
  setLastExecutionResult: res => set({ lastExecutionResult: res }),
  setLastBatchResult: res => set({ lastBatchResult: res }),
  notify: message => set(s => ({ notifications: [message, ...s.notifications].slice(0, 8) })),
  reset: () => set({
    module: 'builder', tab: 'progress', selectedStrategyId: 'str-1', resultView: 'Overview', selectedBankId: 'results', selectedRows: [],
    strategies, databanks, jobs: {}, settings: initialSettings, builder: initialBuilder, optimization: initialOptimization, retester: initialRetester,
    portfolioSettings: initialPortfolioSettings, portfolioMasterSettings: initialPortfolioMasterSettings, rules, portfolio: portfolioMembers,
    workflow: workflowTasks, projects: customProjects, activeProjectId: customProjects[0].id, extensionFiles, activeFileId: extensionFiles[0].id,
    openFileIds: [extensionFiles[0].id], compileOutput: '[info] Compiler ready.', computeNodes, businessConfig, notifications: [],
    lastExecutionResult: null, lastBatchResult: null
  }),
}), {
  name: 'sqx-recreation-v1', version: 1,
  partialize: s => ({ ...s, notifications: [] }),
  merge: (persisted, current) => {
    const saved = persisted as Partial<AppState>;
    const savedModule = (saved as { module?: unknown }).module;
    return { ...current, ...saved, module: savedModule === 'improver' ? 'builder' : saved.module ?? current.module, settings: mergeAppSettings(saved.settings) };
  },
}));
