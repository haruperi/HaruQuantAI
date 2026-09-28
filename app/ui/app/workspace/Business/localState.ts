/** Owner-local prototype state. Shared published resources are accessed through the host. */
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { ownerViewStorage, mergeViewState, previewResources, connectPreviewDocument } from '../../host/resourceClient';
import { useAppStore as useShellStore } from '../../host/store';
import type { ComputeNode, BusinessUser, BusinessWorkspaceItem, McpServerConfig, BusinessConfig } from './documents';
interface LocalState { businessConfig: BusinessConfig;
computeNodes: ComputeNode[];
addBusinessUser: (user: BusinessUser) => void;
updateMcpServer: (id: string, patch: Partial<McpServerConfig>) => void;
addMcpServer: (server: McpServerConfig) => void;
updateBusinessConfig: (patch: Partial<BusinessConfig>) => void;
removeComputeNode: (id: string) => void;
removeMcpServer: (id: string) => void;
addComputeNode: (node: ComputeNode) => void;
updateComputeNode: (id: string, patch: Partial<ComputeNode>) => void;
addBusinessWorkspace: (ws: BusinessWorkspaceItem) => void; reset: () => void; }

const businessConfig: BusinessConfig = JSON.parse("{\"organization\":\"Haru Quant Capital Inc.\",\"activeWorkspace\":\"Production Quantitative Alpha\",\"workspaces\":[{\"id\":\"ws-1\",\"name\":\"Production Quantitative Alpha\",\"coresAllocated\":48,\"memoryAllocated\":96},{\"id\":\"ws-2\",\"name\":\"R&D Sandbox (Crypto / Futures)\",\"coresAllocated\":16,\"memoryAllocated\":32},{\"id\":\"ws-3\",\"name\":\"Backtesting Cluster West\",\"coresAllocated\":8,\"memoryAllocated\":16}],\"users\":[{\"id\":\"u-1\",\"name\":\"Haru Peri\",\"email\":\"haru@quantai.internal\",\"role\":\"Owner\",\"status\":\"Active\"},{\"id\":\"u-2\",\"name\":\"Alex Vance\",\"email\":\"alex@quantai.internal\",\"role\":\"Quant Researcher\",\"status\":\"Active\"},{\"id\":\"u-3\",\"name\":\"Elena Rostova\",\"email\":\"elena@quantai.internal\",\"role\":\"Risk Manager\",\"status\":\"Active\"},{\"id\":\"u-4\",\"name\":\"Audit Service Agent\",\"email\":\"audit@quantai.internal\",\"role\":\"Viewer\",\"status\":\"Service Account\"}],\"mcpServers\":[{\"id\":\"mcp-1\",\"name\":\"Antigravity Alpha Agent Gateway\",\"url\":\"http://localhost:8080/mcp/v1\",\"transport\":\"sse\",\"status\":\"Connected\",\"capabilities\":[\"strategy_generation\",\"backtest_execution\",\"code_synthesis\"],\"activeCalls\":2},{\"id\":\"mcp-2\",\"name\":\"QuantConnect Cloud Bridge\",\"url\":\"stdio:qc-bridge\",\"transport\":\"stdio\",\"status\":\"Connected\",\"capabilities\":[\"live_data_feed\",\"order_routing\"],\"activeCalls\":0},{\"id\":\"mcp-3\",\"name\":\"OpenAI Reasoning Engine\",\"url\":\"http://localhost:8081/mcp/v1\",\"transport\":\"sse\",\"status\":\"Connected\",\"capabilities\":[\"prompt_optimization\",\"code_explanation\"],\"activeCalls\":1}]}");
const computeNodes: ComputeNode[] = JSON.parse("[{\"id\":\"node-local\",\"name\":\"Master Node (Local Engine)\",\"host\":\"127.0.0.1\",\"ip\":\"127.0.0.1\",\"port\":9091,\"cores\":16,\"memoryGb\":32,\"gpu\":true,\"status\":\"Online\",\"cpuUsagePct\":24,\"latencyMs\":1,\"activeTask\":\"Pipeline Execution Manager\"},{\"id\":\"node-cluster-1\",\"name\":\"Cluster-Alpha (Dedicated Server)\",\"host\":\"alpha.cluster.internal\",\"ip\":\"192.168.1.101\",\"port\":9092,\"cores\":32,\"memoryGb\":64,\"gpu\":true,\"status\":\"Busy\",\"cpuUsagePct\":88,\"latencyMs\":3,\"activeTask\":\"Genetic Evolution: Gen 42/100 (EURUSD H1)\"},{\"id\":\"node-cluster-2\",\"name\":\"Cluster-Beta (Cloud Compute Instance)\",\"host\":\"beta.cluster.internal\",\"ip\":\"10.0.0.15\",\"port\":9092,\"cores\":16,\"memoryGb\":32,\"gpu\":false,\"status\":\"Idle\",\"cpuUsagePct\":6,\"latencyMs\":18},{\"id\":\"node-cluster-3\",\"name\":\"Cluster-Gamma (Backup Instance)\",\"host\":\"gamma.cluster.internal\",\"ip\":\"10.0.0.16\",\"port\":9092,\"cores\":8,\"memoryGb\":16,\"gpu\":false,\"status\":\"Offline\",\"cpuUsagePct\":0,\"latencyMs\":0}]");
const useLocalState = create<LocalState>()(persist((set) => ({businessConfig,
computeNodes,
addBusinessUser: user => set(s => ({
    businessConfig: { ...s.businessConfig, users: [...s.businessConfig.users, user] },
  })),
updateMcpServer: (id, patch) => set(s => ({
    businessConfig: {
      ...s.businessConfig,
      mcpServers: s.businessConfig.mcpServers.map(m => m.id === id ? { ...m, ...patch } : m),
    },
  })),
addMcpServer: server => set(s => ({
    businessConfig: { ...s.businessConfig, mcpServers: [...s.businessConfig.mcpServers, server] },
  })),
updateBusinessConfig: patch => set(s => ({
    businessConfig: { ...s.businessConfig, ...patch },
  })),
removeComputeNode: id => set(s => ({
    computeNodes: s.computeNodes.filter(n => n.id !== id),
  })),
removeMcpServer: id => set(s => ({
    businessConfig: {
      ...s.businessConfig,
      mcpServers: s.businessConfig.mcpServers.filter(m => m.id !== id),
    },
  })),
addComputeNode: node => set(s => ({ computeNodes: [...s.computeNodes, node] })),
updateComputeNode: (id, patch) => set(s => ({
    computeNodes: s.computeNodes.map(n => n.id === id ? { ...n, ...patch } : n),
  })),
addBusinessWorkspace: ws => set(s => ({
    businessConfig: { ...s.businessConfig, workspaces: [...s.businessConfig.workspaces, ws] },
  })), reset: () => set({businessConfig,
computeNodes})}), {name: 'workspace.business.view.v1', version: 1, storage:createJSONStorage(() => { if (typeof localStorage === 'undefined') throw new Error('Local view storage unavailable'); return ownerViewStorage; }), merge:mergeViewState}));

type CombinedState = ReturnType<typeof useShellStore.getState> & LocalState;
function useCombinedState<T = CombinedState>(selector: (state: CombinedState) => T = state => state as unknown as T): T {
 const shell=useShellStore(); const local=useLocalState(); return selector({...shell,...local});
}
export const useAppStore=Object.assign(useCombinedState, {getState: (): CombinedState => ({...useShellStore.getState(),...useLocalState.getState()}), setState: useLocalState.setState, subscribe: useLocalState.subscribe, persist:useLocalState.persist});
