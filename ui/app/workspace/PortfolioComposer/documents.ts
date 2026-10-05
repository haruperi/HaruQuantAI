/** Owner-local presentation/resource documents; no backend execution authority. */
export interface PortfolioMember {
  strategyId: string;
  weight: number;
  enabled: boolean;
  sector: string;
  multiplier?: number;
  color?: string;
  metrics?: {
    netProfit: number;
    maxDrawdown: number;
    profitFactor: number;
    sharpe: number;
  };
}

export interface EquityPoint {
  time: string;
  value: number;
  drawdown: number;
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

import type * as React from 'react';
import type { ReactNode, Dispatch, SetStateAction } from 'react';
import { useAttachment } from '../../host/composition';
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
export declare function demoResult(id: string, name: string): ResultDocument;
export declare function downloadText(name: string, text: string, type?: string): void;
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
export interface WorkbenchPorts {
SqdModal: typeof SqdModal;
ProjectResults: typeof ProjectResults;
ResultsChart: typeof ResultsChart;
demoResult: typeof demoResult;
downloadText: typeof downloadText;
usePreviewRun: typeof usePreviewRun;
}
export function useProjectWorkbench(): WorkbenchPorts { return useAttachment<WorkbenchPorts>('project.workbench'); }
