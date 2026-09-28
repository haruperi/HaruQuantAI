/** Owner-local presentation/resource documents; no backend execution authority. */
export interface ComputeNode {
  id: string;
  name: string;
  host: string;
  ip: string;
  port: number;
  cores: number;
  memoryGb: number;
  gpu: boolean;
  status: 'Online' | 'Busy' | 'Idle' | 'Offline';
  cpuUsagePct: number;
  latencyMs: number;
  activeTask?: string;
}

export interface BusinessUser {
  id: string;
  name: string;
  email: string;
  role: 'Owner' | 'Quant Researcher' | 'Risk Manager' | 'Viewer';
  status: string;
}

export interface BusinessWorkspaceItem {
  id: string;
  name: string;
  coresAllocated: number;
  memoryAllocated: number;
}

export interface McpServerConfig {
  id: string;
  name: string;
  url: string;
  transport: 'sse' | 'stdio';
  status: 'Connected' | 'Error' | 'Disabled';
  capabilities: string[];
  activeCalls: number;
}

export interface BusinessConfig {
  organization: string;
  activeWorkspace: string;
  workspaces: BusinessWorkspaceItem[];
  users: BusinessUser[];
  mcpServers: McpServerConfig[];
}
