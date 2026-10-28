import React, { useEffect, useState } from 'react';
import {
  BarChart2,
  Bot,
  CandlestickChart,
  Check,
  Copy,
  Cpu,
  Database,
  FileCode,
  FlaskConical,
  Folder,
  Layers,
  Network,
  Search,
  Settings,
  Shield,
  TrendingUp,
  X,
  Zap,
} from 'lucide-react';
import { createCodeEditorClient, type SnippetTemplateDto } from './codeEditorClient';

interface CreateFromTemplateModalProps {
  onClose: () => void;
  onSnippetCreated: (tabInfo: { file_path: string; title: string; content: string }) => void;
}

interface TemplateMetadata {
  id: string;
  name: string;
  categoryName: string;
  description: string;
  detailedDoc: string;
  defaultName: string;
  targetDir: string;
  color: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TEMPLATE_METADATA: TemplateMetadata[] = [
  {
    id: 'BlocksIndicators',
    name: 'Blocks Indicators',
    categoryName: 'building_blocks',
    description: 'Technical indicators and market data',
    detailedDoc:
      'Create custom technical indicators using price, volume, and other market data. This template provides a clean structure for building indicators with configurable parameters and easy integration with the HaruQuantAI backtesting framework.',
    defaultName: 'MyIndicator',
    targetDir: 'app/include/snippets/indicators/',
    color: 'bg-blue-600/20 text-blue-400 border-blue-500/30',
    icon: BarChart2,
  },
  {
    id: 'BlocksSignal',
    name: 'Blocks Signal',
    categoryName: 'building_blocks',
    description: 'Trading signals and entry/exit logic',
    detailedDoc:
      'Evaluates conditions across indicator and price series to generate entry or exit triggers for trading strategies.',
    defaultName: 'MySignalCondition',
    targetDir: 'app/include/snippets/signals/',
    color: 'bg-emerald-600/20 text-emerald-400 border-emerald-500/30',
    icon: Zap,
  },
  {
    id: 'BlocksOrder',
    name: 'Blocks Order',
    categoryName: 'building_blocks',
    description: 'Order execution and position control',
    detailedDoc:
      'Custom logic for opening, modifying, and closing trading orders with fine-grained slippage and magic number control.',
    defaultName: 'MyOrderAction',
    targetDir: 'app/include/snippets/orders/',
    color: 'bg-amber-600/20 text-amber-400 border-amber-500/30',
    icon: Layers,
  },
  {
    id: 'BlocksOtherActions',
    name: 'Blocks Other Actions',
    categoryName: 'building_blocks',
    description: 'Miscellaneous trading actions',
    detailedDoc:
      'Side-effect actions triggered on events: logging, sound alerts, email/webhook alerts, and chart markers.',
    defaultName: 'MyAction',
    targetDir: 'app/include/snippets/actions/',
    color: 'bg-purple-600/20 text-purple-400 border-purple-500/30',
    icon: Settings,
  },
  {
    id: 'ColumnsDatabanks',
    name: 'Columns Databanks',
    categoryName: 'databanks',
    description: 'Market and fundamental data columns',
    detailedDoc:
      'Computes custom strategy performance metrics and statistics displayed as filterable columns in Databanks.',
    defaultName: 'MyDatabankMetric',
    targetDir: 'app/include/snippets/metrics/',
    color: 'bg-cyan-600/20 text-cyan-400 border-cyan-500/30',
    icon: Database,
  },
  {
    id: 'ColumnsTrades',
    name: 'Columns Trades',
    categoryName: 'databanks',
    description: 'Trade and position data columns',
    detailedDoc:
      'Computes per-trade analytic columns evaluated over individual historical trade execution records.',
    defaultName: 'MyTradeColumn',
    targetDir: 'app/include/snippets/trade_columns/',
    color: 'bg-pink-600/20 text-pink-400 border-pink-500/30',
    icon: CandlestickChart,
  },
  {
    id: 'MoneyManagement',
    name: 'Money Management',
    categoryName: 'money_management',
    description: 'Position sizing and risk management',
    detailedDoc:
      'Calculates order volume (lots/contracts) dynamically based on risk percentage, equity, and stop-loss distance.',
    defaultName: 'MyPositionSizer',
    targetDir: 'app/include/snippets/money_management/',
    color: 'bg-yellow-600/20 text-yellow-400 border-yellow-500/30',
    icon: Shield,
  },
  {
    id: 'MonteCarloManipulation',
    name: 'Monte Carlo Manipulation',
    categoryName: 'robustness',
    description: 'Monte Carlo data manipulation',
    detailedDoc:
      'Performs trade sequence manipulation: reshuffling, resampling with replacement, randomized skipping, and slippage jitter.',
    defaultName: 'MyMcManipulation',
    targetDir: 'app/include/snippets/monte_carlo/manipulation/',
    color: 'bg-teal-600/20 text-teal-400 border-teal-500/30',
    icon: Network,
  },
  {
    id: 'MonteCarloRetest',
    name: 'Monte Carlo Retest',
    categoryName: 'robustness',
    description: 'Monte Carlo strategy retest',
    detailedDoc:
      'Simulates parameter perturbations to test strategy robustness and sensitivity against overfitting.',
    defaultName: 'MyMcRetest',
    targetDir: 'app/include/snippets/monte_carlo/retest/',
    color: 'bg-indigo-600/20 text-indigo-400 border-indigo-500/30',
    icon: TrendingUp,
  },
  {
    id: 'WhatIf',
    name: 'What If',
    categoryName: 'robustness',
    description: 'Scenario analysis and parameter testing',
    detailedDoc:
      'Hypothetical scenario filtering rule (e.g. drop worst N consecutive trades, filter by day of week or session hours).',
    defaultName: 'MyWhatIfScenario',
    targetDir: 'app/include/snippets/what_if/',
    color: 'bg-red-600/20 text-red-400 border-red-500/30',
    icon: FlaskConical,
  },
  {
    id: 'CustomAnalysis',
    name: 'Custom Analysis',
    categoryName: 'analysis',
    description: 'Custom research and analysis tools',
    detailedDoc:
      'Batch analytical processor and reporting script operating over databanks and multiple strategy results.',
    defaultName: 'MyCustomAnalysis',
    targetDir: 'app/include/snippets/analysis/',
    color: 'bg-sky-600/20 text-sky-400 border-sky-500/30',
    icon: Search,
  },
  {
    id: 'AITools',
    name: 'AI Tools',
    categoryName: 'ai_tools',
    description: 'AI-powered quant research tools',
    detailedDoc:
      'Defines custom tools exposed via Model Context Protocol (MCP) and callable by autonomous AI research agents.',
    defaultName: 'MyAIAssistantTool',
    targetDir: 'app/include/snippets/ai_tools/',
    color: 'bg-fuchsia-600/20 text-fuchsia-400 border-fuchsia-500/30',
    icon: Cpu,
  },
];

export function CreateFromTemplateModal({ onClose, onSnippetCreated }: CreateFromTemplateModalProps) {
  const client = createCodeEditorClient();
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateMetadata>(TEMPLATE_METADATA[0]);
  const [snippetName, setSnippetName] = useState<string>(TEMPLATE_METADATA[0].defaultName);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [previewContent, setPreviewContent] = useState<string>('');
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filter templates
  const filteredTemplates = TEMPLATE_METADATA.filter(
    t =>
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Fetch live template preview from backend
  useEffect(() => {
    let active = true;
    client
      .renderTemplatePreview(selectedTemplate.id, snippetName || selectedTemplate.defaultName)
      .then(res => {
        if (active) setPreviewContent(res.content);
      })
      .catch(() => {
        // Fallback preview
        if (active) setPreviewContent(`# Boilerplate for ${selectedTemplate.name}\nclass ${snippetName}:\n    pass\n`);
      });
    return () => {
      active = false;
    };
  }, [selectedTemplate.id, snippetName]);

  const handleSelectTemplate = (tmpl: TemplateMetadata) => {
    setSelectedTemplate(tmpl);
    setSnippetName(tmpl.defaultName);
    setErrorMsg(null);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(previewContent);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleCreate = async () => {
    if (!snippetName.trim()) {
      setErrorMsg('Please enter a snippet name.');
      return;
    }
    setIsCreating(true);
    setErrorMsg(null);
    try {
      const res = await client.createFromTemplate(
        selectedTemplate.id,
        snippetName.trim().replace(/\.py$/, ''),
        selectedTemplate.categoryName
      );
      onSnippetCreated({
        file_path: res.file_path,
        title: `${snippetName.trim().replace(/\.py$/, '')}.py`,
        content: previewContent,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create snippet from template.';
      setErrorMsg(msg);
    } finally {
      setIsCreating(false);
    }
  };

  const SelectedIcon = selectedTemplate.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-5xl h-[88vh] max-h-[820px] rounded-xl border border-slate-700/80 bg-slate-900 text-slate-100 shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                Create New from Template
              </h2>
              <p className="text-xs text-slate-400">
                Create a new file from a template to get started quickly with your quantitative trading strategy.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 hover:bg-slate-800 p-1.5 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body - 2 Columns */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column: Template List & Search */}
          <div className="w-[360px] border-r border-slate-800 flex flex-col bg-slate-950/40">
            <div className="p-3 border-b border-slate-800/80">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search templates..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900/90 border border-slate-700/60 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1 divide-y divide-transparent">
              {filteredTemplates.map(tmpl => {
                const isSelected = tmpl.id === selectedTemplate.id;
                const Icon = tmpl.icon;
                return (
                  <button
                    key={tmpl.id}
                    onClick={() => handleSelectTemplate(tmpl)}
                    className={`w-full flex items-start gap-3 p-2.5 rounded-lg text-left transition-all ${
                      isSelected
                        ? 'bg-blue-600/20 border border-blue-500/40 shadow-sm'
                        : 'hover:bg-slate-800/50 border border-transparent'
                    }`}
                  >
                    <div
                      className={`p-2 rounded-lg border flex-shrink-0 ${tmpl.color} ${
                        isSelected ? 'ring-1 ring-blue-400/30' : ''
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-semibold text-slate-200 truncate">{tmpl.name}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1">{tmpl.description}</div>
                    </div>
                  </button>
                );
              })}
              {filteredTemplates.length === 0 && (
                <div className="text-center py-10 text-xs text-slate-500">No matching templates found</div>
              )}
            </div>
          </div>

          {/* Right Column: Template Details & Preview */}
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/60 p-6 space-y-4">
            {/* Template Header Card */}
            <div className="flex items-start gap-3.5 pb-2">
              <div className={`p-2.5 rounded-xl border ${selectedTemplate.color}`}>
                <SelectedIcon className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-semibold text-slate-100">{selectedTemplate.name}</h3>
                <p className="text-xs text-slate-400">{selectedTemplate.description}</p>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed bg-slate-800/40 p-2.5 rounded-lg border border-slate-700/40">
                  {selectedTemplate.detailedDoc}
                </p>
              </div>
            </div>

            {/* Code Preview Card */}
            <div className="flex-1 flex flex-col rounded-lg border border-slate-800 bg-slate-950 overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/80 bg-slate-900/80 text-[11px] text-slate-400 font-mono">
                <span className="flex items-center gap-1.5">
                  <FileCode className="w-3.5 h-3.5 text-blue-400" />
                  Template Preview
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {isCopied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div className="flex-1 p-3 overflow-auto font-mono text-[12px] leading-relaxed text-slate-300 whitespace-pre">
                {previewContent}
              </div>
            </div>

            {/* Inputs: Name, Category, Target Path */}
            <div className="grid grid-cols-3 gap-4 pt-1">
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">Name</label>
                <input
                  type="text"
                  value={snippetName}
                  onChange={e => setSnippetName(e.target.value)}
                  placeholder="SnippetName"
                  className="w-full px-3 py-1.5 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">Category</label>
                <div className="px-3 py-1.5 text-xs bg-slate-950/70 border border-slate-800 rounded-lg text-slate-300 flex items-center justify-between">
                  <span className="truncate">{selectedTemplate.name}</span>
                  <span className="text-[10px] text-slate-500 uppercase">{selectedTemplate.categoryName}</span>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">Target Path</label>
                <div className="px-3 py-1.5 text-xs bg-slate-950/70 border border-slate-800 rounded-lg text-slate-400 font-mono flex items-center gap-1.5 truncate">
                  <Folder className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                  <span className="truncate">{selectedTemplate.targetDir}</span>
                </div>
              </div>
            </div>

            {errorMsg && (
              <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/30 px-3 py-2 rounded-lg">
                {errorMsg}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="border-t border-slate-800 px-6 py-3.5 bg-slate-900/90 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors border border-slate-700/80"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="px-5 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <FileCode className="w-4 h-4" />
            {isCreating ? 'Creating...' : 'Create & Open'}
          </button>
        </div>
      </div>
    </div>
  );
}
