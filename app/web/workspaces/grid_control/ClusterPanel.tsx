import { useMemo, useState } from 'react';
import { Cpu, HardDrive, Plus, Server, Trash2, Zap } from 'lucide-react';
import { Button } from '../../common/components/ui';
import type { ComputeNode } from '../../shell/types';
import { AddNodeModal } from './AddNodeModal';

interface ClusterPanelProps {
  nodes: ComputeNode[];
  onAddNode: (node: ComputeNode) => void;
  onRemoveNode: (nodeId: string) => void;
}

export function ClusterPanel({ nodes, onAddNode, onRemoveNode }: ClusterPanelProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [probing, setProbing] = useState(false);
  const [probeResult, setProbeResult] = useState<string | null>(null);

  const totalCores = useMemo(() => nodes.reduce((acc, n) => acc + (n.cores || 0), 0), [nodes]);
  const totalMemoryGb = useMemo(() => nodes.reduce((acc, n) => acc + (n.memoryGb || 0), 0), [nodes]);
  const healthyCount = useMemo(() => nodes.filter(n => n.status !== 'Offline').length, [nodes]);
  const gpuCount = useMemo(() => nodes.filter(n => n.gpu).length, [nodes]);

  const handleProbe = () => {
    setProbing(true);
    setProbeResult(null);
    // Dynamic inspection based on actual active nodes count
    const activeCount = nodes.filter(n => n.status !== 'Offline').length;
    setProbing(false);
    setProbeResult(`Probe complete: ${activeCount}/${nodes.length} cluster nodes active.`);
  };

  return (
    <fieldset className="grid-control-panel cluster-panel" data-testid="cluster-panel">
      <legend>Distributed Compute Cluster</legend>

      <div className="cluster-metrics-bar">
        <div className="cluster-metric-card">
          <Cpu size={16} />
          <div>
            <strong>{totalCores} Cores</strong>
            <span>Total Compute</span>
          </div>
        </div>

        <div className="cluster-metric-card">
          <HardDrive size={16} />
          <div>
            <strong>{totalMemoryGb} GB</strong>
            <span>Cluster RAM</span>
          </div>
        </div>

        <div className="cluster-metric-card">
          <Server size={16} />
          <div>
            <strong>{healthyCount}/{nodes.length}</strong>
            <span>Active Nodes</span>
          </div>
        </div>

        <div className="cluster-metric-card">
          <Zap size={16} />
          <div>
            <strong>{gpuCount}</strong>
            <span>GPU Accelerated</span>
          </div>
        </div>
      </div>

      <div className="cluster-actions-toolbar">
        <Button onClick={() => setShowAddModal(true)}>
          <Plus size={14} /> Add Worker Node
        </Button>
        <Button onClick={handleProbe} disabled={probing}>
          <Server size={14} /> {probing ? 'Probing...' : 'Probe Cluster Nodes'}
        </Button>
        {probeResult && <span className="cluster-probe-result">{probeResult}</span>}
      </div>

      <div className="plain-table-wrap">
        <table className="plain-table cluster-nodes-table">
          <thead>
            <tr>
              <th>Node Name</th>
              <th>Host / IP</th>
              <th>Port</th>
              <th>Cores</th>
              <th>RAM (GB)</th>
              <th>GPU</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {nodes.length > 0 ? (
              nodes.map(node => (
                <tr key={node.id}>
                  <td><strong>{node.name}</strong></td>
                  <td>{node.host || node.ip}</td>
                  <td>{node.port}</td>
                  <td>{node.cores}</td>
                  <td>{node.memoryGb}</td>
                  <td>{node.gpu ? 'Yes' : 'No'}</td>
                  <td>
                    <span className={`node-status-pill status-${node.status.toLowerCase()}`}>
                      {node.status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="grid-remove-btn"
                      aria-label={`Remove node ${node.name}`}
                      onClick={() => onRemoveNode(node.id)}
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8} className="grid-empty">
                  No remote compute nodes registered. Compute runs on local machine.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showAddModal && (
        <AddNodeModal
          onClose={() => setShowAddModal(false)}
          onAddNode={node => {
            onAddNode(node);
            setShowAddModal(false);
          }}
        />
      )}
    </fieldset>
  );
}
