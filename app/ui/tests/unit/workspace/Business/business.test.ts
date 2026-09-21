import { beforeEach, describe, expect, it } from 'vitest';
import { useAppStore } from '../../../../src/app/store';
import type { BusinessUser, BusinessWorkspaceItem, ComputeNode, McpServerConfig } from '../../../../src/app/types';

describe('Business, Distributed Compute & MCP Gateways', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it('aggregates distributed compute node cluster metrics correctly', () => {
    const store = useAppStore.getState();
    const nodes = store.computeNodes;
    expect(nodes.length).toBe(4);

    const totalCores = nodes.reduce((acc, n) => acc + n.cores, 0);
    expect(totalCores).toBe(16 + 32 + 16 + 8); // 72 Cores

    const totalMemory = nodes.reduce((acc, n) => acc + n.memoryGb, 0);
    expect(totalMemory).toBe(32 + 64 + 32 + 16); // 144 GB

    const gpuNodes = nodes.filter(n => n.gpu);
    expect(gpuNodes.length).toBe(2);

    const busyNodes = nodes.filter(n => n.status === 'Busy');
    expect(busyNodes.length).toBe(1);
    expect(busyNodes[0].activeTask).toContain('Genetic Evolution');
  });

  it('registers and removes compute nodes dynamically', () => {
    const store = useAppStore.getState();
    const initialCount = store.computeNodes.length;

    const newNode: ComputeNode = {
      id: 'node-test-cloud-4',
      name: 'Cloud-Worker-04',
      host: 'worker04.cloud.internal',
      ip: '10.0.0.18',
      port: 9092,
      cores: 64,
      memoryGb: 128,
      gpu: true,
      status: 'Idle',
      cpuUsagePct: 1,
      latencyMs: 12,
    };

    store.addComputeNode(newNode);
    expect(useAppStore.getState().computeNodes.length).toBe(initialCount + 1);

    // Update node
    store.updateComputeNode('node-test-cloud-4', { status: 'Busy', cpuUsagePct: 92 });
    let found = useAppStore.getState().computeNodes.find(n => n.id === 'node-test-cloud-4');
    expect(found?.status).toBe('Busy');
    expect(found?.cpuUsagePct).toBe(92);

    // Remove node
    store.removeComputeNode('node-test-cloud-4');
    expect(useAppStore.getState().computeNodes.length).toBe(initialCount);
  });

  it('configures Model Context Protocol (MCP) servers and capabilities', () => {
    const store = useAppStore.getState();
    const servers = store.businessConfig.mcpServers;
    expect(servers.length).toBeGreaterThanOrEqual(3);

    const alphaGateway = servers.find(s => s.name.includes('Antigravity Alpha Agent'));
    expect(alphaGateway).toBeDefined();
    expect(alphaGateway?.transport).toBe('sse');
    expect(alphaGateway?.status).toBe('Connected');
    expect(alphaGateway?.capabilities).toContain('strategy_generation');
    expect(alphaGateway?.capabilities).toContain('backtest_execution');
    expect(alphaGateway?.capabilities).toContain('code_synthesis');

    // Add new MCP server
    const newServer: McpServerConfig = {
      id: 'mcp-test-custom',
      name: 'Custom Research LLM Bridge',
      url: 'http://localhost:9095/mcp',
      transport: 'sse',
      status: 'Connected',
      capabilities: ['prompt_optimization'],
      activeCalls: 0,
    };

    store.addMcpServer(newServer);
    expect(useAppStore.getState().businessConfig.mcpServers.some(s => s.id === 'mcp-test-custom')).toBe(true);

    // Update MCP server
    store.updateMcpServer('mcp-test-custom', { status: 'Disabled' });
    const updated = useAppStore.getState().businessConfig.mcpServers.find(s => s.id === 'mcp-test-custom');
    expect(updated?.status).toBe('Disabled');

    // Remove MCP server
    store.removeMcpServer('mcp-test-custom');
    expect(useAppStore.getState().businessConfig.mcpServers.some(s => s.id === 'mcp-test-custom')).toBe(false);
  });

  it('manages organization workspaces and RBAC user role permissions', () => {
    const store = useAppStore.getState();
    const config = store.businessConfig;

    expect(config.organization).toBe('Haru Quant Capital Inc.');
    expect(config.workspaces.length).toBe(3);
    expect(config.users.length).toBe(4);

    const roles = config.users.map(u => u.role);
    expect(roles).toContain('Owner');
    expect(roles).toContain('Quant Researcher');
    expect(roles).toContain('Risk Manager');
    expect(roles).toContain('Viewer');

    // Add workspace
    const newWs: BusinessWorkspaceItem = {
      id: 'ws-crypto-desk',
      name: 'Crypto Execution Desk',
      coresAllocated: 24,
      memoryAllocated: 48,
    };
    store.addBusinessWorkspace(newWs);
    expect(useAppStore.getState().businessConfig.workspaces.some(w => w.id === 'ws-crypto-desk')).toBe(true);

    // Add user
    const newUser: BusinessUser = {
      id: 'u-dev-1',
      name: 'Sarah Connor',
      email: 'sarah@quantai.internal',
      role: 'Quant Researcher',
      status: 'Active',
    };
    store.addBusinessUser(newUser);
    expect(useAppStore.getState().businessConfig.users.some(u => u.id === 'u-dev-1')).toBe(true);
  });
});
