import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  Bot,
  Building2,
  CheckCircle2,
  Code2,
  Cpu,
  Globe,
  HardDrive,
  Key,
  Layers,
  Network,
  Plus,
  RefreshCw,
  Server,
  Shield,
  ShieldCheck,
  Trash2,
  UserPlus,
  Users,
  Zap,
} from 'lucide-react';
import { useAppStore } from './localState';
import type { BusinessUser, BusinessWorkspaceItem, ComputeNode, McpServerConfig } from './documents';
import { Button, Field, Modal, Section, Select, TextInput } from '../../components/ui';
import { AddNodeModal } from './AddNodeModal';
import { ConfigureMcpModal } from './ConfigureMcpModal';

export function BusinessWorkspace() {
  const store = useAppStore();
  const [showAddNodeModal, setShowAddNodeModal] = useState<boolean>(false);
  const [showMcpModal, setShowMcpModal] = useState<boolean>(false);
  const [editingMcp, setEditingMcp] = useState<McpServerConfig | undefined>(undefined);
  const [showInviteModal, setShowInviteModal] = useState<boolean>(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState<boolean>(false);

  // Invite user state
  const [inviteName, setInviteName] = useState<string>('');
  const [inviteEmail, setInviteEmail] = useState<string>('');
  const [inviteRole, setInviteRole] = useState<BusinessUser['role']>('Quant Researcher');

  const config = store.businessConfig;
  const nodes = store.computeNodes;

  // Aggregate cluster metrics
  const totalCores = nodes.reduce((acc, n) => acc + n.cores, 0);
  const totalMemory = nodes.reduce((acc, n) => acc + n.memoryGb, 0);
  const gpuNodesCount = nodes.filter(n => n.gpu).length;
  const busyNodesCount = nodes.filter(n => n.status === 'Busy').length;

  const handlePingAll = () => {
    store.notify('Pinging all cluster compute nodes...');
    setTimeout(() => {
      store.notify('All 4 compute nodes responded within 18ms. Cluster health: 100%');
    }, 400);
  };

  const handleRecycle = () => {
    store.notify('Sent worker process recycling signal to all connected daemons.');
  };

  const handleInviteUser = () => {
    if (!inviteEmail.trim()) return;
    const newUser: BusinessUser = {
      id: `u-${Date.now()}`,
      name: inviteName.trim() || inviteEmail.split('@')[0],
      email: inviteEmail.trim(),
      role: inviteRole,
      status: 'Active',
    };
    store.addBusinessUser(newUser);
    store.notify(`Invited ${newUser.email} as ${newUser.role}`);
    setShowInviteModal(false);
    setInviteName('');
    setInviteEmail('');
  };

  const handleSaveMcp = (server: McpServerConfig) => {
    if (editingMcp) {
      store.updateMcpServer(server.id, server);
      store.notify(`Updated MCP gateway "${server.name}"`);
    } else {
      store.addMcpServer(server);
      store.notify(`Added MCP gateway "${server.name}"`);
    }
  };

  return (
    <div className="business h-full flex flex-col overflow-y-auto bg-[var(--bg)] p-4">
      {/* Title & Organization Header */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[var(--line)]">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-cyan-600 to-blue-800 rounded-lg text-white shadow-md">
            <Building2 size={24} />
          </div>
          <div>
            <h1 className="text-base font-bold text-gray-100 flex items-center gap-2">
              HaruQuantAI for Business & Enterprise
              <span className="text-xs font-normal text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800">
                Multi-Tenant Edition
              </span>
            </h1>
            <span className="text-xs text-gray-400">
              Distributed high-performance computing cluster, Model Context Protocol (MCP) gateways, and access control
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-[var(--panel)] px-3 py-1.5 rounded border border-[var(--line)]">
          <Field label="Active Workspace">
            <Select
              value={config.activeWorkspace}
              onChange={val => store.updateBusinessConfig({ activeWorkspace: val })}
            >
              {config.workspaces.map(ws => (
                <option key={ws.id} value={ws.name}>
                  {ws.name} ({ws.coresAllocated} Cores / {ws.memoryAllocated}GB)
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </div>

      {/* Cluster Resource Metric Cards */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="bg-[var(--panel)] p-3 rounded border border-[var(--line)] flex items-center gap-3">
          <div className="p-2 bg-blue-950/60 text-blue-400 rounded border border-blue-800">
            <Cpu size={20} />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider block">
              Compute Cores
            </span>
            <div className="text-lg font-bold text-gray-100 flex items-baseline gap-1.5">
              <span>{totalCores} Cores</span>
              <span className="text-xs font-normal text-gray-400">across 4 nodes</span>
            </div>
          </div>
        </div>

        <div className="bg-[var(--panel)] p-3 rounded border border-[var(--line)] flex items-center gap-3">
          <div className="p-2 bg-purple-950/60 text-purple-400 rounded border border-purple-800">
            <HardDrive size={20} />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider block">
              Cluster Memory
            </span>
            <div className="text-lg font-bold text-gray-100 flex items-baseline gap-1.5">
              <span>{totalMemory} GB</span>
              <span className="text-xs font-normal text-gray-400">ECC RAM</span>
            </div>
          </div>
        </div>

        <div className="bg-[var(--panel)] p-3 rounded border border-[var(--line)] flex items-center gap-3">
          <div className="p-2 bg-emerald-950/60 text-emerald-400 rounded border border-emerald-800">
            <Zap size={20} />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider block">
              GPU Acceleration
            </span>
            <div className="text-lg font-bold text-gray-100 flex items-baseline gap-1.5">
              <span>{gpuNodesCount} Nodes</span>
              <span className="text-xs font-normal text-emerald-400">CUDA Active</span>
            </div>
          </div>
        </div>

        <div className="bg-[var(--panel)] p-3 rounded border border-[var(--line)] flex items-center gap-3">
          <div className="p-2 bg-cyan-950/60 text-cyan-400 rounded border border-cyan-800">
            <Activity size={20} />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 uppercase tracking-wider block">
              Active Compute Jobs
            </span>
            <div className="text-lg font-bold text-gray-100 flex items-baseline gap-1.5">
              <span>{busyNodesCount} Running</span>
              <span className="text-xs font-normal text-gray-400">
                {nodes.length - busyNodesCount} Available
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Compute Nodes (Left) & MCP / Access (Right) */}
      <div className="grid grid-cols-1 gap-4">
        {/* Section 1: Distributed Compute Nodes */}
        <Section title="Distributed Compute Worker Cluster">
          <div className="p-3 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">
                Registered execution workers performing genetic strategy generation, walk-forward testing, and Monte Carlo runs.
              </span>
              <div className="flex gap-2">
                <Button onClick={handlePingAll}>
                  <Network size={13} className="text-cyan-400" />
                  Ping Cluster
                </Button>
                <Button onClick={handleRecycle}>
                  <RefreshCw size={13} />
                  Recycle Workers
                </Button>
                <Button className="primary" onClick={() => setShowAddNodeModal(true)}>
                  <Plus size={13} />
                  Register Node
                </Button>
              </div>
            </div>

            <div className="overflow-x-auto border border-gray-700 rounded bg-[#101419]">
              <table className="w-full text-xs font-mono border-collapse">
                <thead className="bg-gray-800 text-gray-400">
                  <tr>
                    <th className="p-2 text-left">Node Name / Host</th>
                    <th className="p-2 text-left">Endpoint</th>
                    <th className="p-2 text-center">Cores</th>
                    <th className="p-2 text-center">RAM</th>
                    <th className="p-2 text-center">GPU</th>
                    <th className="p-2 text-center">Status</th>
                    <th className="p-2 text-left w-36">CPU Utilization</th>
                    <th className="p-2 text-right">Ping</th>
                    <th className="p-2 text-left">Current Task</th>
                    <th className="p-2 text-center">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {nodes.map(node => {
                    const isBusy = node.status === 'Busy';
                    const isOnline = node.status === 'Online';
                    const isIdle = node.status === 'Idle';

                    return (
                      <tr key={node.id} className="hover:bg-gray-800/40 border-b border-gray-800">
                        <td className="p-2 font-semibold text-gray-200">
                          {node.name}
                        </td>
                        <td className="p-2 text-gray-400">{node.ip}:{node.port}</td>
                        <td className="p-2 text-center text-cyan-300 font-bold">{node.cores}</td>
                        <td className="p-2 text-center text-gray-300">{node.memoryGb}GB</td>
                        <td className="p-2 text-center">
                          {node.gpu ? (
                            <span className="text-[10px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-800">
                              CUDA
                            </span>
                          ) : (
                            <span className="text-[10px] text-gray-500">-</span>
                          )}
                        </td>
                        <td className="p-2 text-center">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded border font-semibold uppercase ${
                              isBusy
                                ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
                                : isOnline || isIdle
                                ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-400'
                                : 'bg-red-950/60 border-red-500/50 text-red-400'
                            }`}
                          >
                            {node.status}
                          </span>
                        </td>
                        <td className="p-2">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-800 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-2 rounded-full ${
                                  node.cpuUsagePct > 80
                                    ? 'bg-red-500'
                                    : node.cpuUsagePct > 50
                                    ? 'bg-amber-400'
                                    : 'bg-cyan-400'
                                }`}
                                style={{ width: `${node.cpuUsagePct}%` }}
                              />
                            </div>
                            <span className="text-[10px] text-gray-400 w-7 text-right">
                              {node.cpuUsagePct}%
                            </span>
                          </div>
                        </td>
                        <td className="p-2 text-right text-gray-400">{node.latencyMs}ms</td>
                        <td className="p-2 text-gray-300 text-[11px] truncate max-w-[200px]">
                          {node.activeTask || <span className="text-gray-600 italic">Idle</span>}
                        </td>
                        <td className="p-2 text-center">
                          <button
                            className="text-gray-500 hover:text-red-400 p-1"
                            onClick={() => {
                              if (nodes.length <= 1) {
                                store.notify('Cannot remove master node.');
                                return;
                              }
                              store.removeComputeNode(node.id);
                              store.notify(`Removed node "${node.name}"`);
                            }}
                          >
                            <Trash2 size={13} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </Section>

        {/* Section 2: MCP AI Gateways & Team Permissions */}
        <div className="grid grid-cols-2 gap-4">
          {/* MCP Servers */}
          <Section title="Model Context Protocol (MCP) & AI Gateways">
            <div className="p-3 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">
                  Antigravity AI Agent & Model Context Protocol adapters for strategy ideation.
                </span>
                <Button
                  className="primary text-xs"
                  onClick={() => {
                    setEditingMcp(undefined);
                    setShowMcpModal(true);
                  }}
                >
                  <Plus size={13} />
                  Add Gateway
                </Button>
              </div>

              <div className="flex flex-col gap-2">
                {config.mcpServers.map(mcp => (
                  <div
                    key={mcp.id}
                    className="p-2.5 rounded border border-gray-700 bg-[#101419] flex items-start justify-between"
                  >
                    <div className="flex items-start gap-2.5">
                      <div className="p-2 bg-gray-900 rounded border border-gray-700 mt-0.5">
                        <Bot size={16} className="text-cyan-400" />
                      </div>
                      <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                          <strong className="text-xs text-gray-200">{mcp.name}</strong>
                          <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.2 rounded font-mono">
                            {mcp.transport}
                          </span>
                          <span className="text-[10px] text-emerald-400 font-semibold">
                            ● {mcp.status}
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-gray-500 mt-0.5">
                          {mcp.url}
                        </span>
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {mcp.capabilities.map(cap => (
                            <span
                              key={cap}
                              className="text-[9px] bg-cyan-950/70 border border-cyan-800/60 text-cyan-300 px-1.5 py-0.2 rounded font-mono"
                            >
                              {cap}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      <Button
                        className="text-xs px-2 py-1"
                        onClick={() => {
                          setEditingMcp(mcp);
                          setShowMcpModal(true);
                        }}
                      >
                        Edit
                      </Button>
                      <button
                        className="text-gray-500 hover:text-red-400 p-1"
                        onClick={() => store.removeMcpServer(mcp.id)}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Section>

          {/* Users & Team Access Control */}
          <Section title="Team Members & Access Control Matrix">
            <div className="p-3 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">
                  Role-based access control (RBAC) governance.
                </span>
                <div className="flex gap-2">
                  <Button onClick={() => setShowPermissionsModal(true)}>
                    <Shield size={13} className="text-cyan-400" />
                    Permissions Matrix
                  </Button>
                  <Button className="primary text-xs" onClick={() => setShowInviteModal(true)}>
                    <UserPlus size={13} />
                    Invite Member
                  </Button>
                </div>
              </div>

              <div className="border border-gray-700 rounded bg-[#101419] overflow-hidden">
                <table className="w-full text-xs font-mono border-collapse">
                  <thead className="bg-gray-800 text-gray-400">
                    <tr>
                      <th className="p-2 text-left">Member</th>
                      <th className="p-2 text-left">Email</th>
                      <th className="p-2 text-left">Role</th>
                      <th className="p-2 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {config.users.map(user => (
                      <tr key={user.id} className="hover:bg-gray-800/40 border-b border-gray-800">
                        <td className="p-2 font-semibold text-gray-200">{user.name}</td>
                        <td className="p-2 text-gray-400">{user.email}</td>
                        <td className="p-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              user.role === 'Owner'
                                ? 'bg-purple-950 text-purple-300 border border-purple-800'
                                : user.role === 'Quant Researcher'
                                ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                                : user.role === 'Risk Manager'
                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                : 'bg-gray-800 text-gray-400'
                            }`}
                          >
                            {user.role}
                          </span>
                        </td>
                        <td className="p-2 text-center text-emerald-400">{user.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Section>
        </div>
      </div>

      {/* Add Compute Node Modal */}
      {showAddNodeModal && (
        <AddNodeModal
          onClose={() => setShowAddNodeModal(false)}
          onAddNode={node => {
            store.addComputeNode(node);
            store.notify(`Registered compute node "${node.name}"`);
          }}
        />
      )}

      {/* Configure MCP Modal */}
      {showMcpModal && (
        <ConfigureMcpModal
          existingServer={editingMcp}
          onClose={() => setShowMcpModal(false)}
          onSaveServer={handleSaveMcp}
        />
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <Modal title="Invite Organization Member" onClose={() => setShowInviteModal(false)} width={460}>
          <div className="flex flex-col gap-3">
            <Field label="Full Name">
              <TextInput value={inviteName} onChange={e => setInviteName(e.target.value)} />
            </Field>

            <Field label="Email Address">
              <TextInput
                type="email"
                value={inviteEmail}
                onChange={e => setInviteEmail(e.target.value)}
              />
            </Field>

            <Field label="Assigned Role">
              <Select value={inviteRole} onChange={v => setInviteRole(v as any)}>
                <option value="Quant Researcher">Quant Researcher (Build, Retest, Optimize)</option>
                <option value="Risk Manager">Risk Manager (Filter, Portfolios, Audit)</option>
                <option value="Viewer">Viewer (Read-only Databank & Results Access)</option>
                <option value="Owner">Owner (Full Cluster Administration)</option>
              </Select>
            </Field>

            <div className="flex justify-end gap-2 pt-2 border-t border-gray-700">
              <Button onClick={() => setShowInviteModal(false)}>Cancel</Button>
              <Button className="primary" onClick={handleInviteUser}>
                Send Invitation
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Permissions Matrix Modal */}
      {showPermissionsModal && (
        <Modal title="Access Control Permissions Matrix" onClose={() => setShowPermissionsModal(false)} width={640}>
          <div className="flex flex-col gap-3">
            <div className="text-xs text-gray-400">
              Granular role-based capability boundaries across StrategyQuant X subsystems.
            </div>

            <table className="w-full text-xs font-mono border-collapse border border-gray-700">
              <thead className="bg-gray-800 text-gray-300">
                <tr>
                  <th className="p-2 text-left border-b border-gray-700">Subsystem / Action</th>
                  <th className="p-2 text-center border-b border-gray-700">Owner</th>
                  <th className="p-2 text-center border-b border-gray-700">Quant</th>
                  <th className="p-2 text-center border-b border-gray-700">Risk Mgr</th>
                  <th className="p-2 text-center border-b border-gray-700">Viewer</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-800">
                  <td className="p-2 text-gray-300">Builder & Optimizer Execution</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-gray-500">Read</td>
                  <td className="p-2 text-center text-gray-500">Read</td>
                </tr>
                <tr className="border-b border-gray-800">
                  <td className="p-2 text-gray-300">Databank Export & Deletion</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-emerald-400">✓ Export</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-gray-500">None</td>
                </tr>
                <tr className="border-b border-gray-800">
                  <td className="p-2 text-gray-300">Code Editor Extension Deploy</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-gray-500">Read</td>
                  <td className="p-2 text-center text-gray-500">None</td>
                </tr>
                <tr className="border-b border-gray-800">
                  <td className="p-2 text-gray-300">Compute Cluster Node Provisioning</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-gray-500">None</td>
                  <td className="p-2 text-center text-gray-500">None</td>
                  <td className="p-2 text-center text-gray-500">None</td>
                </tr>
                <tr>
                  <td className="p-2 text-gray-300">MCP AI Gateway Registration</td>
                  <td className="p-2 text-center text-emerald-400">✓ Full</td>
                  <td className="p-2 text-center text-emerald-400">✓ Use</td>
                  <td className="p-2 text-center text-gray-500">Read</td>
                  <td className="p-2 text-center text-gray-500">None</td>
                </tr>
              </tbody>
            </table>

            <div className="flex justify-end pt-2 border-t border-gray-700">
              <Button onClick={() => setShowPermissionsModal(false)}>Close</Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export { BusinessWorkspace as Business };
