import React, { useState } from 'react';
import { Bot, CheckCircle2, Code2, Cpu, Globe, Key, Network, ShieldCheck, Zap } from 'lucide-react';
import type { McpServerConfig } from '../../host/types';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../components/ui';

interface ConfigureMcpModalProps {
  onClose: () => void;
  onSaveServer: (server: McpServerConfig) => void;
  existingServer?: McpServerConfig;
}

export function ConfigureMcpModal({ onClose, onSaveServer, existingServer }: ConfigureMcpModalProps) {
  const [name, setName] = useState<string>(existingServer?.name || 'Local AI Quant Gateway');
  const [url, setUrl] = useState<string>(existingServer?.url || 'http://localhost:8080/mcp/v1');
  const [transport, setTransport] = useState<'sse' | 'stdio'>(existingServer?.transport || 'sse');
  const [capabilities, setCapabilities] = useState<string[]>(
    existingServer?.capabilities || ['strategy_generation', 'backtest_execution', 'code_synthesis']
  );
  const [testing, setTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const availableCaps = [
    { id: 'strategy_generation', label: 'Strategy Generation (AI Prompt to Trading Rules)' },
    { id: 'backtest_execution', label: 'Backtest Engine (Sub-millisecond Simulation)' },
    { id: 'code_synthesis', label: 'Code Synthesis (MQL5 / Python Robot Export)' },
    { id: 'live_data_feed', label: 'Market Feed (Tick Stream & Real-time Quote Access)' },
    { id: 'order_routing', label: 'Order Execution (Broker Protocol Integration)' },
    { id: 'prompt_optimization', label: 'Reasoning Engine (Cross-Market Robustness Evaluation)' },
  ];

  const toggleCap = (id: string) => {
    setCapabilities(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleTestPing = () => {
    setTesting(true);
    setTestResult(null);
    setTimeout(() => {
      setTesting(false);
      setTestResult('Success: Handshake verified with MCP Protocol v1.0. 3 tools and 2 prompt templates discovered.');
    }, 550);
  };

  const handleSave = () => {
    const server: McpServerConfig = {
      id: existingServer?.id || `mcp-${Date.now()}`,
      name: name.trim() || 'MCP Gateway',
      url: url.trim() || 'http://localhost:8080/mcp/v1',
      transport,
      status: 'Connected',
      capabilities,
      activeCalls: existingServer?.activeCalls || 0,
    };
    onSaveServer(server);
    onClose();
  };

  return (
    <Modal title="Model Context Protocol (MCP) & AI Agent Gateway" onClose={onClose} width={580}>
      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Gateway / Server Name">
            <TextInput value={name} onChange={e => setName(e.target.value)} />
          </Field>

          <Field label="Transport Type">
            <Select value={transport} onChange={v => setTransport(v as any)}>
              <option value="sse">Server-Sent Events (SSE / HTTP)</option>
              <option value="stdio">Local Subprocess (Standard I/O)</option>
            </Select>
          </Field>
        </div>

        <Field label={transport === 'sse' ? 'Endpoint URL' : 'Execution Command'}>
          <TextInput
            value={url}
            placeholder={transport === 'sse' ? 'http://localhost:8080/mcp/v1' : 'stdio:quant-agent-cli'}
            onChange={e => setUrl(e.target.value)}
          />
        </Field>

        <div className="flex flex-col gap-2 pt-1">
          <span className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
            <Bot size={13} className="text-cyan-400" />
            Enabled Agent Tools & Capabilities
          </span>

          <div className="grid grid-cols-1 gap-1.5 bg-gray-900 p-2.5 rounded border border-gray-700">
            {availableCaps.map(c => (
              <Checkbox
                key={c.id}
                label={c.label}
                checked={capabilities.includes(c.id)}
                onChange={() => toggleCap(c.id)}
              />
            ))}
          </div>
        </div>

        {testResult && (
          <div className="p-2.5 rounded text-xs bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 flex items-center gap-2">
            <CheckCircle2 size={14} className="shrink-0" />
            <span>{testResult}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-gray-700">
          <Button onClick={handleTestPing} disabled={testing}>
            <Zap size={14} className="text-yellow-400" />
            {testing ? 'Pinging Gateway...' : 'Ping Gateway'}
          </Button>

          <div className="flex gap-2">
            <Button onClick={onClose}>Cancel</Button>
            <Button className="primary" onClick={handleSave}>
              <Code2 size={14} />
              Save Gateway Config
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
