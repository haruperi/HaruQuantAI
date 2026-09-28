/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { CustomProject, WorkflowTask, JobStatus } from './documents';
interface LocalState { projects: CustomProject[];
activeProjectId: string;
setProjectTasks: (projectId: string, tasks: WorkflowTask[]) => void;
updateTaskInProject: (projectId: string, taskId: string, patch: Partial<WorkflowTask>) => void;
addProject: (project: CustomProject) => void;
deleteProject: (id: string) => void;
addTaskToProject: (projectId: string, task: WorkflowTask) => void;
removeTaskFromProject: (projectId: string, taskId: string) => void;
reorderTaskInProject: (projectId: string, taskId: string, offset: number) => void;
setActiveProject: (id: string) => void;
updateProject: (id: string, patch: Partial<CustomProject>) => void; reset: () => void; }

const customProjects: CustomProject[] = JSON.parse("[{\"id\":\"proj-1\",\"name\":\"FX Trend-Following Research Pipeline\",\"description\":\"Autonomous multi-stage generation, walk-forward retest, correlation filtering and portfolio assembly for Forex majors.\",\"status\":\"idle\",\"tasks\":[{\"id\":\"w1\",\"type\":\"ClearDatabanks\",\"name\":\"Clear temporary candidate databanks\",\"enabled\":true,\"status\":\"idle\",\"input\":\"Temporary\",\"output\":\"Temporary\",\"config\":{\"targetBank\":\"Temporary\",\"keepPinned\":true}},{\"id\":\"w2\",\"type\":\"Build\",\"name\":\"Genetic Strategy Generation (H1)\",\"enabled\":true,\"status\":\"idle\",\"input\":\"EURUSD H1\",\"output\":\"Generated\",\"config\":{\"symbol\":\"EURUSD\",\"timeframe\":\"H1\",\"targetCount\":30,\"minSharpe\":1.1,\"minTrades\":80}},{\"id\":\"w3\",\"type\":\"Retest\",\"name\":\"Higher Precision Multi-Market Retest\",\"enabled\":true,\"status\":\"idle\",\"input\":\"Generated\",\"output\":\"Precise\",\"config\":{\"precision\":\"M1 real tick data\",\"spreadMultiplier\":1.5,\"slippagePips\":1}},{\"id\":\"w4\",\"type\":\"Filtering\",\"name\":\"Sharpe & Drawdown Robustness Filter\",\"enabled\":true,\"status\":\"idle\",\"input\":\"Precise\",\"output\":\"Accepted\",\"config\":{\"filterMetric\":\"Sharpe ratio >= 1.25\",\"maxDrawdownPct\":20,\"minProfitFactor\":1.4}},{\"id\":\"w5\",\"type\":\"AutomaticPortfolioBuilder\",\"name\":\"Uncorrelated 5-Strategy Portfolio Assembly\",\"enabled\":true,\"status\":\"idle\",\"input\":\"Accepted\",\"output\":\"Portfolio\",\"config\":{\"maxStrategies\":5,\"maxCorrelation\":0.45,\"weightingModel\":\"Risk Parity\"}},{\"id\":\"w6\",\"type\":\"SaveToFiles\",\"name\":\"Export Compiled MQL5 / Python Robots\",\"enabled\":false,\"status\":\"idle\",\"input\":\"Portfolio\",\"output\":\"Export Directory\",\"config\":{\"destinationPath\":\"./exports/live_candidates/\",\"format\":\"MQL5 + Python\"}}]},{\"id\":\"proj-2\",\"name\":\"NQ Futures Mean Reversion Scanner\",\"description\":\"High-frequency intraday mean reversion scanner with Monte Carlo validation.\",\"status\":\"idle\",\"tasks\":[{\"id\":\"w2-1\",\"type\":\"UpdateData\",\"name\":\"Sync CME Tick Data Feed\",\"enabled\":true,\"status\":\"idle\",\"input\":\"CME NQ Futures\",\"output\":\"Updated Market Cache\",\"config\":{\"provider\":\"Futures Tick Feed\",\"barsToSync\":50000}},{\"id\":\"w2-2\",\"type\":\"Build\",\"name\":\"Evolve Range Breakout Candidates\",\"enabled\":true,\"status\":\"idle\",\"input\":\"NQ M15\",\"output\":\"Candidates\",\"config\":{\"symbol\":\"NQ\",\"timeframe\":\"M15\",\"targetCount\":20,\"maxDrawdownPct\":15}},{\"id\":\"w2-3\",\"type\":\"CustomAnalysis\",\"name\":\"Monte Carlo Trade Reshuffling Confidence\",\"enabled\":true,\"status\":\"idle\",\"input\":\"Candidates\",\"output\":\"Robust Candidates\",\"config\":{\"confidenceLevel\":95,\"simulations\":1000}},{\"id\":\"w2-4\",\"type\":\"Notification\",\"name\":\"Send Slack / Webhook Alert\",\"enabled\":true,\"status\":\"idle\",\"input\":\"Robust Candidates\",\"output\":\"Webhook Endpoint\",\"config\":{\"webhookUrl\":\"https://hooks.slack.com/services/quant-alerts\",\"notifyOnSuccess\":true}}]}]");
const useLocalState = create<LocalState>()(persist((set) => ({projects: customProjects,
activeProjectId: customProjects[0].id,
setProjectTasks: (projectId, tasks) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? { ...p, tasks } : p),
  })),
updateTaskInProject: (projectId, taskId, patch) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? {
      ...p,
      tasks: p.tasks.map(t => t.id === taskId ? { ...t, ...patch } : t),
    } : p),
  })),
addProject: project => set(s => ({ projects: [...s.projects, project], activeProjectId: project.id })),
deleteProject: id => set(s => {
    const nextProjects = s.projects.filter(p => p.id !== id);
    return {
      projects: nextProjects,
      activeProjectId: s.activeProjectId === id ? (nextProjects[0]?.id || '') : s.activeProjectId,
    };
  }),
addTaskToProject: (projectId, task) => set(s => ({
    projects: s.projects.map(p => p.id === projectId ? { ...p, tasks: [...p.tasks, task] } : p),
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
setActiveProject: activeProjectId => set({ activeProjectId }),
updateProject: (id, patch) => set(s => ({ projects: s.projects.map(p => p.id === id ? { ...p, ...patch } : p) })), reset: () => set({projects: customProjects,
activeProjectId: customProjects[0].id})}), {name: 'workspace.custom_projects.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), merge:mergeViewState}));

type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
