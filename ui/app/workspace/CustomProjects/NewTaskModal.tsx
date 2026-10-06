import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  Bell,
  CheckSquare,
  Database,
  Download,
  FastForward,
  FileCode,
  FileDown,
  Filter,
  Layers,
  PauseCircle,
  Play,
  RefreshCw,
  Sliders,
  Terminal,
  Upload,
  Workflow,
} from 'lucide-react';
import type { WorkflowTask } from '../../host/types';
import { Button, Field, Modal, Select, TextInput } from '../../components/ui';

export interface TaskTypeDefinition {
  type: string;
  name: string;
  category: 'Strategy Generation' | 'Testing & Robustness' | 'Databanks & Files' | 'Automation & Control';
  icon: React.ReactNode;
  description: string;
  defaultInput: string;
  defaultOutput: string;
  defaultConfig: Record<string, any>;
}

export const SQX_TASK_TYPES: TaskTypeDefinition[] = [
  // Strategy Generation
  {
    type: 'Build',
    name: 'Build Strategies',
    category: 'Strategy Generation',
    icon: <Play size={16} className="text-cyan-400" />,
    description: 'Autonomous strategy evolution using genetic algorithms, random generation, or island models.',
    defaultInput: 'EURUSD H1',
    defaultOutput: 'Generated',
    defaultConfig: { symbol: 'EURUSD', timeframe: 'H1', targetCount: 25, rankingMetric: 'Return / Drawdown ratio' },
  },
  {
    type: 'AutomaticPortfolioBuilder',
    name: 'Automatic Portfolio Builder',
    category: 'Strategy Generation',
    icon: <Layers size={16} className="text-purple-400" />,
    description: 'Assemble optimal multi-strategy portfolios enforcing correlation limits and risk parity weighting.',
    defaultInput: 'Accepted',
    defaultOutput: 'Portfolio',
    defaultConfig: { maxStrategies: 5, maxCorrelation: 0.5, weightingModel: 'Risk Parity' },
  },

  // Testing & Robustness
  {
    type: 'Retest',
    name: 'Retest Strategies',
    category: 'Testing & Robustness',
    icon: <RefreshCw size={16} className="text-blue-400" />,
    description: 'Retest strategies against higher precision tick data, spread multipliers, or slippage models.',
    defaultInput: 'Generated',
    defaultOutput: 'Precise',
    defaultConfig: { precision: 'Selected timeframe only', spreadMultiplier: 1.2, slippagePips: 1.0 },
  },
  {
    type: 'Optimize',
    name: 'Optimize Strategies',
    category: 'Testing & Robustness',
    icon: <Sliders size={16} className="text-emerald-400" />,
    description: 'Run simple parameter sweeps or Walk-Forward cluster analysis across parameter ranges.',
    defaultInput: 'Generated',
    defaultOutput: 'Optimized',
    defaultConfig: { mode: 'Simple', runs: 10, keepBest: 5 },
  },
  {
    type: 'Filtering',
    name: 'Filter Databank',
    category: 'Testing & Robustness',
    icon: <Filter size={16} className="text-amber-400" />,
    description: 'Eliminate strategies failing specific criteria (e.g. Sharpe < 1.2, Drawdown > 25%, Trades < 100).',
    defaultInput: 'Precise',
    defaultOutput: 'Accepted',
    defaultConfig: { minSharpe: 1.2, maxDrawdownPct: 20, minTrades: 80, minProfitFactor: 1.3 },
  },
  {
    type: 'CustomAnalysis',
    name: 'Custom Analysis / Monte Carlo',
    category: 'Testing & Robustness',
    icon: <Activity size={16} className="text-rose-400" />,
    description: 'Execute Monte Carlo trade reshuffling, randomized skip, or custom statistical plugins.',
    defaultInput: 'Accepted',
    defaultOutput: 'Validated',
    defaultConfig: { simulations: 500, confidenceLevel: 95, analysisType: 'Monte Carlo Trades' },
  },

  // Databanks & Files
  {
    type: 'ClearDatabanks',
    name: 'Clear Databanks',
    category: 'Databanks & Files',
    icon: <Database size={16} className="text-red-400" />,
    description: 'Purge obsolete candidates from temporary or intermediate working databanks.',
    defaultInput: 'Temporary',
    defaultOutput: 'Temporary',
    defaultConfig: { targetBank: 'Temporary', keepPinned: true },
  },
  {
    type: 'LoadFromFiles',
    name: 'Load from Files',
    category: 'Databanks & Files',
    icon: <FileDown size={16} className="text-teal-400" />,
    description: 'Import strategy files (.str, .mq5, .ea) from a local or network directory into a databank.',
    defaultInput: 'Filesystem',
    defaultOutput: 'Imported',
    defaultConfig: { sourceDirectory: './strategies/inbox/', filePattern: '*.str' },
  },
  {
    type: 'SaveToFiles',
    name: 'Save to Files',
    category: 'Databanks & Files',
    icon: <Download size={16} className="text-sky-400" />,
    description: 'Export strategies from target databank to disk as MQL4, MQL5, EasyLanguage, or Python files.',
    defaultInput: 'Portfolio',
    defaultOutput: 'Exports',
    defaultConfig: { destinationPath: './strategies/live/', format: 'MQL5' },
  },
  {
    type: 'UpdateData',
    name: 'Update Data',
    category: 'Databanks & Files',
    icon: <Upload size={16} className="text-lime-400" />,
    description: 'Download the latest market bars and ticks from configured data feeds (Dukascopy, MT5, Yahoo).',
    defaultInput: 'Feed Provider',
    defaultOutput: 'Market Cache',
    defaultConfig: { provider: 'Dukascopy', symbols: ['EURUSD', 'GBPUSD'], timeframe: 'M1' },
  },
  {
    type: 'LogDatabankStats',
    name: 'Log Databank Stats',
    category: 'Databanks & Files',
    icon: <FileCode size={16} className="text-indigo-400" />,
    description: 'Calculate and output databank summary metrics and strategy counts to execution log.',
    defaultInput: 'Accepted',
    defaultOutput: 'Log Console',
    defaultConfig: { logMetrics: ['count', 'avgProfit', 'avgSharpe', 'avgDrawdown'] },
  },

  // Automation & Control
  {
    type: 'CallExternalScript',
    name: 'Call External Script',
    category: 'Automation & Control',
    icon: <Terminal size={16} className="text-yellow-400" />,
    description: 'Invoke an external Python script, bash executable, or external machine learning pipeline.',
    defaultInput: 'Accepted',
    defaultOutput: 'Script Output',
    defaultConfig: { scriptPath: './scripts/ml_classifier.py', passDatabankJson: true, timeoutSec: 120 },
  },
  {
    type: 'Notification',
    name: 'Send Notification',
    category: 'Automation & Control',
    icon: <Bell size={16} className="text-amber-400" />,
    description: 'Broadcast email, Telegram message, Slack alert, or HTTP Webhook upon reaching this task.',
    defaultInput: 'Status',
    defaultOutput: 'Notification Log',
    defaultConfig: { channel: 'Webhook', targetUrl: 'https://webhook.site/alerts', notifyOnFailure: true },
  },
  {
    type: 'WaitFor',
    name: 'Wait For Delay / Event',
    category: 'Automation & Control',
    icon: <PauseCircle size={16} className="text-zinc-400" />,
    description: 'Pause pipeline execution for a specified duration or until an external signal file appears.',
    defaultInput: 'Clock',
    defaultOutput: 'Resume',
    defaultConfig: { waitDurationMinutes: 15, waitForFile: '' },
  },
  {
    type: 'GoToTask',
    name: 'Go To Task (Jump / Loop)',
    category: 'Automation & Control',
    icon: <FastForward size={16} className="text-orange-400" />,
    description: 'Direct pipeline control flow to another task step conditionally (looping or branching).',
    defaultInput: 'Condition',
    defaultOutput: 'Jump Target',
    defaultConfig: { targetTaskIndex: 1, maxLoopCount: 5, currentLoops: 0 },
  },
  {
    type: 'StopAndStart',
    name: 'Stop and Start Workers',
    category: 'Automation & Control',
    icon: <Workflow size={16} className="text-violet-400" />,
    description: 'Restart compute workers to free memory cache and recycle worker process handles.',
    defaultInput: 'Worker Pool',
    defaultOutput: 'Refreshed Pool',
    defaultConfig: { purgeMemoryCache: true, restartComputeEngines: true },
  },
];

interface NewTaskModalProps {
  onClose: () => void;
  onAddTask: (task: WorkflowTask) => void;
  existingTasksCount: number;
}

export function NewTaskModal({ onClose, onAddTask, existingTasksCount }: NewTaskModalProps) {
  const [selectedType, setSelectedType] = useState<string>('Build');
  const [taskName, setTaskName] = useState<string>('');
  const [inputBank, setInputBank] = useState<string>('');
  const [outputBank, setOutputBank] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const selectedDef = SQX_TASK_TYPES.find(t => t.type === selectedType) || SQX_TASK_TYPES[0];

  const handleSelectType = (def: TaskTypeDefinition) => {
    setSelectedType(def.type);
    setTaskName(`${def.name} #${existingTasksCount + 1}`);
    setInputBank(def.defaultInput);
    setOutputBank(def.defaultOutput);
  };

  const handleCreate = () => {
    const newTask: WorkflowTask = {
      id: `task-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      type: selectedDef.type,
      name: taskName || `${selectedDef.name} #${existingTasksCount + 1}`,
      enabled: true,
      status: 'idle',
      input: inputBank || selectedDef.defaultInput,
      output: outputBank || selectedDef.defaultOutput,
      config: { ...selectedDef.defaultConfig },
      errorPolicy: 'Stop project',
    };
    onAddTask(newTask);
    onClose();
  };

  const categories = ['All', 'Strategy Generation', 'Testing & Robustness', 'Databanks & Files', 'Automation & Control'];
  const filteredTypes = selectedCategory === 'All'
    ? SQX_TASK_TYPES
    : SQX_TASK_TYPES.filter(t => t.category === selectedCategory);

  return (
    <Modal title="Add StrategyQuant X Workflow Task" onClose={onClose} width={820}>
      <div className="flex flex-col gap-4">
        <div className="flex gap-2 border-b border-gray-700 pb-2">
          {categories.map(cat => (
            <button
              key={cat}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                selectedCategory === cat ? 'bg-cyan-600 text-white font-medium' : 'text-gray-400 hover:bg-gray-800'
              }`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2 max-h-72 overflow-y-auto pr-1">
          {filteredTypes.map(def => {
            const isSelected = selectedType === def.type;
            return (
              <div
                key={def.type}
                onClick={() => handleSelectType(def)}
                className={`flex items-start gap-3 p-2.5 rounded border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-cyan-500 bg-cyan-950/30'
                    : 'border-gray-700 bg-gray-850 hover:bg-gray-800'
                }`}
              >
                <div className="p-1.5 bg-gray-900 rounded border border-gray-700 mt-0.5">
                  {def.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-200">{def.name}</span>
                    <span className="text-[10px] text-gray-400 bg-gray-900 px-1.5 py-0.5 rounded border border-gray-700">
                      {def.type}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-400 mt-1 line-clamp-2 leading-relaxed">
                    {def.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-gray-900 p-3 rounded border border-gray-700 flex flex-col gap-3">
          <div className="text-xs font-semibold text-gray-300 flex items-center gap-2">
            <CheckSquare size={14} className="text-cyan-400" />
            Task Configuration
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label="Task Name">
              <TextInput
                value={taskName || `${selectedDef.name} #${existingTasksCount + 1}`}
                onChange={e => setTaskName(e.target.value)}
              />
            </Field>

            <Field label="Input Databank / Feed">
              <TextInput
                value={inputBank || selectedDef.defaultInput}
                onChange={e => setInputBank(e.target.value)}
              />
            </Field>

            <Field label="Output Databank / Target">
              <TextInput
                value={outputBank || selectedDef.defaultOutput}
                onChange={e => setOutputBank(e.target.value)}
              />
            </Field>
          </div>

          <div className="text-[11px] text-gray-400 bg-gray-800/60 p-2 rounded border border-gray-700 flex items-center gap-2">
            <AlertCircle size={14} className="text-cyan-400 shrink-0" />
            <span>
              Downstream tasks can automatically consume <strong className="text-gray-200">{outputBank || selectedDef.defaultOutput}</strong> as their input databank.
            </span>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-gray-700">
          <Button onClick={onClose}>Cancel</Button>
          <Button className="primary" onClick={handleCreate}>
            <Play size={14} />
            Add Task to Project
          </Button>
        </div>
      </div>
    </Modal>
  );
}
