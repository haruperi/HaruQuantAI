import { useState } from 'react';
import { Network, Server } from 'lucide-react';
import type { ComputeNode } from '../../shell/types';
import { Button, Checkbox, Field, Modal, TextInput } from '../../common/components/ui';

interface AddNodeModalProps {
  onClose: () => void;
  onAddNode: (node: ComputeNode) => void;
}

export function AddNodeModal({ onClose, onAddNode }: AddNodeModalProps) {
  const [name, setName] = useState<string>('');
  const [host, setHost] = useState<string>('');
  const [ip, setIp] = useState<string>('');
  const [port, setPort] = useState<number>(9092);
  const [cores, setCores] = useState<number>(4);
  const [memoryGb, setMemoryGb] = useState<number>(8);
  const [gpu, setGpu] = useState<boolean>(false);
  const [validationMsg, setValidationMsg] = useState<string | null>(null);

  const handleTestConnection = () => {
    if (!host.trim() && !ip.trim()) {
      setValidationMsg('Error: Please provide a valid hostname or IP address.');
      return;
    }
    if (port <= 0 || port > 65535) {
      setValidationMsg('Error: Port must be between 1 and 65535.');
      return;
    }
    setValidationMsg(`Verified node target configuration for ${host.trim() || ip.trim()}:${port}.`);
  };

  const handleRegister = () => {
    const cleanHost = host.trim();
    const cleanIp = ip.trim();
    if (!cleanHost && !cleanIp) {
      setValidationMsg('Error: Please provide a valid hostname or IP address.');
      return;
    }

    const targetAddr = cleanHost || cleanIp;
    const cleanPort = Number(port) || 9092;
    const cleanName = name.trim() || `worker-${targetAddr}`;
    const nodeId = `node-${targetAddr.replace(/[^a-zA-Z0-9_-]/g, '_')}-${cleanPort}`;

    const newNode: ComputeNode = {
      id: nodeId,
      name: cleanName,
      host: cleanHost || targetAddr,
      ip: cleanIp || cleanHost,
      port: cleanPort,
      cores: Math.max(1, Number(cores) || 1),
      memoryGb: Math.max(1, Number(memoryGb) || 1),
      gpu,
      status: 'Idle',
      cpuUsagePct: 0,
      latencyMs: 1,
    };
    onAddNode(newNode);
    onClose();
  };

  return (
    <Modal title="Register Distributed Compute Node" onClose={onClose} width={540}>
      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Node Display Name">
            <TextInput
              value={name}
              placeholder="e.g. Cluster-Worker-01"
              onChange={e => setName(e.target.value)}
            />
          </Field>

          <Field label="Hostname / FQDN">
            <TextInput
              value={host}
              placeholder="e.g. worker.compute.internal"
              onChange={e => setHost(e.target.value)}
            />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label="IP Address">
            <TextInput
              value={ip}
              placeholder="e.g. 192.168.1.50"
              onChange={e => setIp(e.target.value)}
            />
          </Field>

          <Field label="Worker Daemon Port">
            <TextInput
              type="number"
              value={port}
              onChange={e => setPort(Number(e.target.value))}
            />
          </Field>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <Field label="CPU Cores">
            <TextInput
              type="number"
              value={cores}
              onChange={e => setCores(Number(e.target.value))}
            />
          </Field>

          <Field label="RAM (GB)">
            <TextInput
              type="number"
              value={memoryGb}
              onChange={e => setMemoryGb(Number(e.target.value))}
            />
          </Field>

          <div className="flex flex-col justify-center pt-3">
            <Checkbox
              label="GPU Acceleration"
              checked={gpu}
              onChange={val => setGpu(val)}
            />
          </div>
        </div>

        {validationMsg && (
          <div
            className={`p-2.5 rounded text-xs border ${
              validationMsg.startsWith('Error')
                ? 'bg-red-950/60 border-red-500/50 text-red-300'
                : 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
            }`}
          >
            {validationMsg}
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-gray-700">
          <Button onClick={handleTestConnection}>
            <Network size={14} className="text-cyan-400" />
            Validate Target
          </Button>

          <div className="flex gap-2">
            <Button onClick={onClose}>Cancel</Button>
            <Button className="primary" onClick={handleRegister}>
              <Server size={14} />
              Register Node
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
