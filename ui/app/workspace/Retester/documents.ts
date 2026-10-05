/** Owner-local presentation/resource documents; no backend execution authority. */
export interface BatchExecutionResult {
  success: boolean;
  trials: BatchTrialResult[];
  issues: ValidationIssue[];
  elapsed_seconds: number;
}

export interface SingleExecutionResult {
  success: boolean;
  outputs: Record<string, unknown>;
  reproducibility?: ExecutionReproducibilityRecord | null;
  issues: ValidationIssue[];
  elapsed_seconds: number;
}

export interface Databank {
  id: string;
  name: string;
  strategyIds: string[];
}

export interface Strategy {
  id: string;
  name: string;
  symbol: string;
  timeframe: string;
  direction: 'Both' | 'Long' | 'Short';
  bankId: string;
  revision: number;
  note: string;
  metrics: {
    netProfit: number;
    trades: number;
    profitFactor: number;
    maxDrawdown: number;
    sharpe: number;
    stability: number;
  };
  trades: Trade[];
  equity: EquityPoint[];
  parameters: Record<string, number>;
}

export interface BatchTrialResult {
  trial_id: string;
  success: boolean;
  outputs: Record<string, unknown>;
  issues: ValidationIssue[];
  elapsed_seconds: number;
}

export interface ValidationIssue {
  path: string;
  code: string;
  message: string;
}

export interface ExecutionReproducibilityRecord {
  graph_id: string;
  graph_fingerprint: string;
  catalog_fingerprint: string;
  dependency_fingerprint: string;
  plugin_versions: [string, string][];
  source_digests: [string, string][];
  normalized_parameters: Record<string, unknown>;
  input_hash: string;
  output_hash: string;
  seed?: number | null;
  numerical_policy: NumericalPolicy;
  engine_version: string;
  elapsed_seconds: number;
  status: string;
}

export interface Trade {
  id: string;
  strategyId: string;
  side: 'Long' | 'Short';
  entryTime: string;
  exitTime: string;
  entry: number;
  exit: number;
  size: number;
  pnl: number;
  sample: 'IS' | 'OOS';
}

export interface EquityPoint {
  time: string;
  value: number;
  drawdown: number;
}

export interface NumericalPolicy {
  tolerance: number;
  nan_policy: string;
  missing_policy: string;
}

import type * as React from 'react';
import type { ReactNode, Dispatch, SetStateAction } from 'react';
import { useAttachment } from '../../host/composition';
export declare function ProjectProgress({ title, run, stats, summary, result, onOpenResults, onSettings, startError }: {
    title: string;
    run: ReturnType<typeof usePreviewRun>;
    stats: [string, string][];
    summary: ReactNode;
    result: ResultDocument | null;
    onOpenResults: () => void;
    onSettings: () => void;
    startError?: string;
}): import("react").JSX.Element;
export declare function usePreviewRun(): {
    status: RunStatus;
    step: number;
    log: string[];
    clearOnStart: boolean;
    setClearOnStart: import("react").Dispatch<import("react").SetStateAction<boolean>>;
    act: (action: "start" | "pause" | "stop") => void;
    clearLog: () => void;
};
export type RunStatus = 'idle' | 'running' | 'paused' | 'complete';
export interface ResultDocument {
    id: string;
    name: string;
    markets: string[];
    trades: MockTrade[];
    equity: number[];
    metrics: [
        string,
        string
    ][];
    chartData: boolean;
    stockpicker: boolean;
    portfolio: boolean;
}
export interface MockTrade {
    id: number;
    market: string;
    direction: 'long' | 'short';
    sample: 'in' | 'out';
    open: string;
    close: string;
    price: number;
    exit: number;
    profit: number;
    expired: boolean;
}
export declare function ProjectSettings({ sections, locked, selectedId, onSelect }: {
    sections: SettingsSection[];
    locked: boolean;
    selectedId?: string;
    onSelect?: (id: string) => void;
}): import("react").JSX.Element;
export interface SettingsSection {
    id: string;
    title: string;
    help: string;
    helpUrl: string;
    content: ReactNode;
}
export declare function DataTab({ initialState }?: {
    initialState?: DataTabState;
}): import("react").JSX.Element;
export interface DataTabState {
    engine: string;
    symbol: string;
    timeframe: string;
    dateFrom: string;
    dateTo: string;
    oosRanges: OosRange[];
}
export interface OosRange {
    type: 'IST' | 'ISV' | 'OOS';
    from: string;
    to: string;
}
export declare function TradingOptionsTab(): import("react").JSX.Element;
export declare function AtmTab(): import("react").JSX.Element;
export declare function MoneyManagementTab(): import("react").JSX.Element;
export declare function CrossChecksTab(): import("react").JSX.Element;
export declare function RankingTab({ task }?: {
    task?: 'Build' | 'Retest' | 'Optimize';
}): import("react").JSX.Element;
export declare function NotesTab(): import("react").JSX.Element;
export declare function ProjectFrame({ title, panel, onPanelChange, running, children }: {
    title: string;
    panel: ProjectPanel;
    onPanelChange: (panel: ProjectPanel) => void;
    running: boolean;
    children: ReactNode;
}): import("react").JSX.Element;
export type ProjectPanel = 'progress' | 'settings' | 'results';
export declare function ProjectResults({ result, extraSections, embedded, visibleTabIds, emptyMessage }: {
    embedded?: boolean;
    visibleTabIds?: readonly string[];
    emptyMessage?: string;
    extraSections?: ResultSection[];
    result: ResultDocument | null;
}): import("react").JSX.Element;
export interface ResultSection {
    id: string;
    title: string;
    position: number;
    content: ReactNode;
}
export declare function demoResult(id: string, name: string): ResultDocument;
export declare const dataTabDefaults: DataTabState;
export interface WorkbenchPorts {
ProjectProgress: typeof ProjectProgress;
ProjectSettings: typeof ProjectSettings;
DataTab: typeof DataTab;
TradingOptionsTab: typeof TradingOptionsTab;
AtmTab: typeof AtmTab;
MoneyManagementTab: typeof MoneyManagementTab;
CrossChecksTab: typeof CrossChecksTab;
RankingTab: typeof RankingTab;
NotesTab: typeof NotesTab;
ProjectFrame: typeof ProjectFrame;
ProjectResults: typeof ProjectResults;
demoResult: typeof demoResult;
usePreviewRun: typeof usePreviewRun;
dataTabDefaults: typeof dataTabDefaults;
}
export function useProjectWorkbench(): WorkbenchPorts { return useAttachment<WorkbenchPorts>('project.workbench'); }
