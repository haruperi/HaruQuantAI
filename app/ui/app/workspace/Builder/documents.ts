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

export interface RuleNode {
  id: string;
  depth: number;
  kind: 'event' | 'if' | 'then' | 'condition' | 'action';
  label: string;
  parentId?: string;
  operator?: 'AND' | 'OR';
  leftExpr?: string;
  compOp?: '>' | '<' | '>=' | '<=' | '==' | '!=' | 'crosses above' | 'crosses below' | 'is rising' | 'is falling';
  rightExpr?: string;
  actionType?: 'Enter at Market' | 'Place Stop Order' | 'Place Limit Order' | 'Set Stop Loss' | 'Set Profit Target' | 'Trailing Stop' | 'Move SL to BE' | 'Exit Market';
  actionParams?: Record<string, number | string>;
  signalGroup?: 'Long Entry' | 'Short Entry' | 'Long Exit' | 'Short Exit';
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

export interface BuilderSettings {
  mode: 'Genetic evolution' | 'Random generation' | 'Improve existing';
  strategyType: 'Standard' | 'Multi-TF' | 'Stockpicker';
  symbol: string;
  timeframe: string;
  direction: 'Both' | 'Long' | 'Short';
  population: number;
  islands: number;
  mutation: number;
  crossover: number;
  maxConditions: number;
  minConditions: number;
  maxPeriods: number;
  minPeriods: number;
  symmetricalRules: boolean;
  fuzzySignals: boolean;
  generateExitRules: boolean;
  stopLoss: boolean;
  profitTarget: boolean;
  slMin: number;
  slMax: number;
  ptMin: number;
  ptMax: number;
  slType: 'Fixed pips' | 'ATR' | 'Percent';
  ptType: 'Fixed pips' | 'ATR' | 'Percent';
  useTrailingStop: boolean;
  trailingStopMin: number;
  trailingStopMax: number;
  useMoveToBE: boolean;
  beTriggerPips: number;
  beProfitOffset: number;
  mmModel: 'Fixed Size' | 'Risk Fixed Amount' | 'Risk % of Equity' | 'Fixed Risk to Return';
  initialCapital: number;
  riskPercent: number;
  fixedLots: number;
  maxGenerations: number;
  migrateCandidates: boolean;
  migrationInterval: number;
  restartStagnantIslands: boolean;
  stagnantGenerations: number;
  seedFromDatabank: boolean;
  inputDatabank: string;
  rankingMetric: string;
  minReturnDD: number;
  minTrades: number;
  maxDrawdownPct: number;
  minSharpe: number;
  minProfitFactor: number;
  crossChecks: CrossCheckItem[];
  customBlocks: Record<string, boolean>;
  precision: string;
  from: string;
  to: string;
  oos: number;
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

export interface CrossCheckItem {
  id: string;
  name: string;
  enabled: boolean;
}

export interface NumericalPolicy {
  tolerance: number;
  nan_policy: string;
  missing_policy: string;
}

import type * as React from 'react';
import type { ReactNode, Dispatch, SetStateAction } from 'react';
import { useAttachment } from '../../host/composition';
export declare function ProjectFrame({ title, panel, onPanelChange, running, children }: {
    title: string;
    panel: ProjectPanel;
    onPanelChange: (panel: ProjectPanel) => void;
    running: boolean;
    children: ReactNode;
}): import("react").JSX.Element;
export type ProjectPanel = 'progress' | 'settings' | 'results';
export declare function SqdModal({ title, onClose, children, footer, width, }: {
    title: string;
    onClose: () => void;
    children: ReactNode;
    footer?: ReactNode;
    width?: number;
}): import("react").JSX.Element;
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
export declare function ResultsChart({ values, title, benchmark, bars, points, crosshair, trendline, markers, stagnation, stagnationV2 }: {
    values: number[];
    title?: string;
    benchmark?: boolean;
    bars?: boolean;
    points?: string;
    crosshair?: boolean;
    trendline?: boolean;
    markers?: string;
    stagnation?: string | number;
    stagnationV2?: string | number;
}): import("react").JSX.Element;
export declare function TradesChart(): import("react").JSX.Element;
export declare function SqrDropdown({ open, onClose, children, className, }: {
    open: boolean;
    onClose: () => void;
    children: ReactNode;
    className?: string;
}): import("react").JSX.Element | null;
export declare function SegmentedButtons<T extends string | number>({ options, value, onChange, ariaLabel, }: {
    options: {
        value: T;
        label: string;
    }[];
    value: T;
    onChange: (value: T) => void;
    ariaLabel: string;
}): import("react").JSX.Element;
export declare function ResultsToolbar({ dataKey, dataItems, onDataChange, direction, sampleType, onDirectionChange, onSampleTypeChange, extendedSample, showDataSelect, showDirection, showSample, children, }: {
    dataKey?: string;
    dataItems?: string[];
    onDataChange?: (key: string) => void;
    direction: Direction;
    sampleType: SampleType;
    onDirectionChange: (d: Direction) => void;
    onSampleTypeChange: (s: SampleType) => void;
    extendedSample?: boolean;
    showDataSelect?: boolean;
    showDirection?: boolean;
    showSample?: boolean;
    children?: ReactNode;
}): import("react").JSX.Element;
export type Direction = 'both' | 'long' | 'short';
export type SampleType = 'full' | 'in' | 'out';
export declare function NewAnalysisModal({ existingNames, onClose, onCreate, }: {
    existingNames: string[];
    onClose: () => void;
    onCreate: (name: string) => void;
}): import("react").JSX.Element;
export declare function RenameAnalysisModal({ currentName, existingNames, onClose, onRename, }: {
    currentName: string;
    existingNames: string[];
    onClose: () => void;
    onRename: (name: string) => void;
}): import("react").JSX.Element;
export declare function DeleteAnalysisModal({ name, onClose, onDelete, }: {
    name: string;
    onClose: () => void;
    onDelete: () => void;
}): import("react").JSX.Element;
export declare function ManageViewsModal({ onClose }: {
    onClose: () => void;
}): import("react").JSX.Element;
export declare function ExportTradesModal({ onClose, onExport }: {
    onClose: () => void;
    onExport: (comma: boolean) => void;
}): import("react").JSX.Element;
export declare function ModalLinks({ children }: {
    children: ReactNode;
}): import("react").JSX.Element;
export declare function ConditionalTabs({ id, result }: {
    id: string;
    result: ResultDocument;
}): import("react").JSX.Element;
export declare function EquityChartTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function OverviewTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function SpOverviewTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function TradeAnalysisTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function ProfileChartTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function StrategyConfigTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function CustomAnalysisTab({ name, result }: {
    name: string;
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function SourceCodeTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function TradeListTab({ result }: {
    result: ResultDocument | null;
}): import("react").JSX.Element;
export declare function AtmTab(): import("react").JSX.Element;
export declare function CrossChecksTab(): import("react").JSX.Element;
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
export declare function MoneyManagementTab(): import("react").JSX.Element;
export declare function NotesTab(): import("react").JSX.Element;
export declare function RankingTab({ task }?: {
    task?: 'Build' | 'Retest' | 'Optimize';
}): import("react").JSX.Element;
export declare function SqdFieldset({ legend, children, className }: {
    legend?: ReactNode;
    children: ReactNode;
    className?: string;
}): import("react").JSX.Element;
export declare function SqdRadio({ name, value, checked, onChange, disabled, children, }: {
    name: string;
    value: string;
    checked: boolean;
    onChange: (value: string) => void;
    disabled?: boolean;
    children: ReactNode;
}): import("react").JSX.Element;
export declare function SqdSpinner({ value, onChange, min, max, step, disabled, ariaLabel, }: {
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
    step?: number;
    disabled?: boolean;
    ariaLabel: string;
}): import("react").JSX.Element;
export declare function SqdSlider({ value, onChange, min, max, step, postfix, ariaLabel, }: {
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
    step?: number;
    postfix?: string;
    ariaLabel: string;
}): import("react").JSX.Element;
export declare function SqdCheckbox({ checked, onChange, disabled, children, }: {
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
    children: ReactNode;
}): import("react").JSX.Element;
export declare function SqdSelect({ value, onChange, options, disabled, ariaLabel, width, }: {
    value: string;
    onChange: (value: string) => void;
    options: {
        value: string;
        label: string;
    }[];
    disabled?: boolean;
    ariaLabel: string;
    width?: number;
}): import("react").JSX.Element;
export declare function SqdTextInput({ value, onChange, ariaLabel, width, }: {
    value: string;
    onChange: (value: string) => void;
    ariaLabel: string;
    width?: number;
}): import("react").JSX.Element;
export declare function SqdHelpLink({ url }: {
    url: string;
}): import("react").JSX.Element;
export declare function GearLink({ onClick, title }: {
    onClick: () => void;
    title: string;
}): import("react").JSX.Element;
export declare function AdditionalConfigPopup({ setting, onHelp, onClose, onSave, onReset, children, }: {
    setting: string;
    onHelp: () => void;
    onClose: () => void;
    onSave: () => void;
    onReset?: () => void;
    children: ReactNode;
}): import("react").JSX.Element;
export declare function useOpenState(): [string | null, (id: string | null) => void, () => void];
export declare function TradingOptionsTab(): import("react").JSX.Element;
export interface WorkbenchPorts {ProjectFrame: typeof ProjectFrame;
SqdModal: typeof SqdModal;
ProjectResults: typeof ProjectResults;
ResultsChart: typeof ResultsChart;
TradesChart: typeof TradesChart;
SqrDropdown: typeof SqrDropdown;
SegmentedButtons: typeof SegmentedButtons;
ResultsToolbar: typeof ResultsToolbar;
NewAnalysisModal: typeof NewAnalysisModal;
RenameAnalysisModal: typeof RenameAnalysisModal;
DeleteAnalysisModal: typeof DeleteAnalysisModal;
ManageViewsModal: typeof ManageViewsModal;
ExportTradesModal: typeof ExportTradesModal;
ModalLinks: typeof ModalLinks;
ConditionalTabs: typeof ConditionalTabs;
EquityChartTab: typeof EquityChartTab;
OverviewTab: typeof OverviewTab;
SpOverviewTab: typeof SpOverviewTab;
TradeAnalysisTab: typeof TradeAnalysisTab;
ProfileChartTab: typeof ProfileChartTab;
StrategyConfigTab: typeof StrategyConfigTab;
CustomAnalysisTab: typeof CustomAnalysisTab;
SourceCodeTab: typeof SourceCodeTab;
TradeListTab: typeof TradeListTab;
AtmTab: typeof AtmTab;
CrossChecksTab: typeof CrossChecksTab;
DataTab: typeof DataTab;
MoneyManagementTab: typeof MoneyManagementTab;
NotesTab: typeof NotesTab;
RankingTab: typeof RankingTab;
SqdFieldset: typeof SqdFieldset;
SqdRadio: typeof SqdRadio;
SqdSpinner: typeof SqdSpinner;
SqdSlider: typeof SqdSlider;
SqdCheckbox: typeof SqdCheckbox;
SqdSelect: typeof SqdSelect;
SqdTextInput: typeof SqdTextInput;
SqdHelpLink: typeof SqdHelpLink;
GearLink: typeof GearLink;
AdditionalConfigPopup: typeof AdditionalConfigPopup;
useOpenState: typeof useOpenState;
TradingOptionsTab: typeof TradingOptionsTab;}
export function useProjectWorkbench():WorkbenchPorts { return useAttachment<WorkbenchPorts>('project.workbench'); }
