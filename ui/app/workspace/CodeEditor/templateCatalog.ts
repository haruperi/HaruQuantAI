import type React from 'react';
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
export interface TemplateMetadata {
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

export const TEMPLATE_METADATA: TemplateMetadata[] = [
  {
    id: 'BlocksIndicators',
    name: 'Blocks Indicators',
    categoryName: 'building_blocks',
    description: 'Technical indicators and market data',
    detailedDoc:
      'Create custom technical indicators using price, volume, and other market data. This template provides a clean structure for building indicators with configurable parameters and easy integration with the HaruQuantAI backtesting framework.',
    defaultName: 'MyIndicator',
    targetDir: 'app/include/indicators/',
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
    targetDir: 'app/include/signals/',
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
    targetDir: 'app/include/orders/',
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
    targetDir: 'app/include/actions/',
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
    targetDir: 'app/include/metrics/',
    color: 'bg-cyan-600/20 text-cyan-400 border-cyan-500/30',
    icon: Database,
  },
  {
    id: 'ColumnsTrades',
    name: 'Columns Trades',
    categoryName: 'databanks',
    description: 'Trade and position data columns',
    detailedDoc: 'Computes per-trade analytic columns evaluated over individual historical trade execution records.',
    defaultName: 'MyTradeColumn',
    targetDir: 'app/include/trade_columns/',
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
    targetDir: 'app/include/money_management/',
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
    targetDir: 'app/include/monte_carlo/manipulation/',
    color: 'bg-teal-600/20 text-teal-400 border-teal-500/30',
    icon: Network,
  },
  {
    id: 'MonteCarloRetest',
    name: 'Monte Carlo Retest',
    categoryName: 'robustness',
    description: 'Monte Carlo strategy retest',
    detailedDoc: 'Simulates parameter perturbations to test strategy robustness and sensitivity against overfitting.',
    defaultName: 'MyMcRetest',
    targetDir: 'app/include/monte_carlo/retest/',
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
    targetDir: 'app/include/what_if/',
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
    targetDir: 'app/include/analysis/',
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
    targetDir: 'app/include/ai_tools/',
    color: 'bg-fuchsia-600/20 text-fuchsia-400 border-fuchsia-500/30',
    icon: Cpu,
  },
];
