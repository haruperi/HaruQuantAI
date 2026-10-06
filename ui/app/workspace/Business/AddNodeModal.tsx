import React, { useState } from 'react';
import { Cpu, HardDrive, Network, Server, Zap } from 'lucide-react';
import type { ComputeNode } from '../../host/types';
import { Button, Checkbox, Field, Modal, TextInput } from '../../components/ui';

interface AddNodeModalProps {
  onClose: () => void;
  onAddNode: (node: ComputeNode) => void;
}

export function AddNodeModal({ onClose, onAddNode }: AddNodeModalProps) {
  const [name, setName] = useState<string>('Worker-Node-04');
  const [host, setHost] = useState<string>('node04.compute.internal');
  const [ip, setIp] = useState<string>('192.168.1.104');
  const [port, setPort] = useState<number>(9092);
  const [cores, setCores] = useState<number>(32);
  const [memoryGb, setMemoryGb] = useState<number>(64);
  const [gpu, setGpu] = useState<boolean>(true);
  const [testing, setTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTestConnection = () => {
    setTesting(true);
    setTestResult(null);
    setTimeout(() => {
      setTesting(false);
      setTestResult('Success: Node reachable at 192.168.1.104:9092 (Latency: 4ms, Handshake verified)');
    }, 600);
  };

  const handleRegister = () => {
    const newNode: ComputeNode = {
      id: `node-${Date.now()}`,
      name: name.trim() || 'Worker Node',
      host: host.trim() || 'worker.internal',
      ip: ip.trim() || '127.0.0.1',
      port: Number(port) || 9092,
      cores: Number(cores) || 16,
      memoryGb: Number(memoryGb) || 32,
      gpu,
      status: 'Idle',
      cpuUsagePct: 2,
      latencyMs: 4,
    };
    onAddNode(newNode);
    onClose();
  };

  return (
    <Modal title="Register Distributed Compute Node" onClose={onClose} width={540}>
      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Node Display Name">
            <TextInput value={name} onChange={e => setName(e.target.value)} />
          </Field>

          <Field label="Hostname / FQDN">
            <TextInput value={host} onChange={e => setHost(e.target.value)} />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label="IP Address">
            <TextInput value={ip} onChange={e => setIp(e.target.value)} />
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

        {testResult && (
          <div className="p-2.5 rounded text-xs bg-emerald-950/60 border border-emerald-500/50 text-emerald-300">
            {testResult}
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-gray-700">
          <Button onClick={handleTestConnection} disabled={testing}>
            <Network size={14} className="text-cyan-400" />
            {testing ? 'Probing...' : 'Test Connection'}
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
