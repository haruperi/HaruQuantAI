/**
 * Simulation Workbench root shell component (FEAT-UI-31).
 *
 * Provides the unified workstation shell for Simulator capabilities:
 * - Canonical single backtest execution
 * - Interactive live practice and what-if exploration
 * - Bounded multi-run parameter sweep batches
 * - Immutable run catalogue with evidence badges
 */

"use client";

import { useState, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  History,
  Layers,
  Play,
} from "lucide-react";

import type {
  ArchiveState,
  CatalogueStatus,
  EvidenceClass,
} from "@/clients";
import { SimulationStatusBadge } from "./SimulationStatusBadge";
import "./simulation-workbench.css";

export type SimulationMode = "canonical" | "practice" | "batch" | "history";

export interface SimulationWorkbenchProps {
  initialMode?: SimulationMode;
  initialRunId?: string;
  initialSessionId?: string;
  initialBatchId?: string;
  onModeChange?: (mode: SimulationMode) => void;
  status?: CatalogueStatus | null;
  evidenceClass?: EvidenceClass | null;
  archiveState?: ArchiveState | null;
  className?: string;
  children?: ReactNode;
}

const MODES: ReadonlyArray<{
  id: SimulationMode;
  label: string;
  description: string;
  icon: typeof Play;
}> = [
  {
    id: "canonical",
    label: "Canonical Run",
    description: "Execute single reproducible backtests with full trade ledgers",
    icon: Play,
  },
  {
    id: "practice",
    label: "Live Practice",
    description: "Step tick-by-tick, issue manual orders, and fork what-if branches",
    icon: Activity,
  },
  {
    id: "batch",
    label: "Batch Grid",
    description: "Run bounded parameter grid sweeps with real-time SSE progress",
    icon: Layers,
  },
  {
    id: "history",
    label: "Run Catalogue",
    description: "Search, filter, and inspect immutable simulation evidence",
    icon: History,
  },
];

export function SimulationWorkbench({
  initialMode = "canonical",
  initialRunId,
  initialSessionId,
  initialBatchId,
  onModeChange,
  status,
  evidenceClass,
  archiveState,
  className = "",
  children,
}: SimulationWorkbenchProps): ReactNode {
  const [activeMode, setActiveMode] = useState<SimulationMode>(initialMode);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSelectMode = (mode: SimulationMode) => {
    setActiveMode(mode);
    setErrorMessage(null);
    onModeChange?.(mode);
  };

  const currentModeInfo = MODES.find((m) => m.id === activeMode) ?? MODES[0];

  return (
    <div
      className={`simulation-workbench ${className}`}
      role="region"
      aria-label="Simulation Workbench"
    >
      {/* Top Header */}
      <header className="simulation-workbench__header">
        <div className="simulation-workbench__title-group">
          <span className="simulation-workbench__eyebrow">
            HaruQuantAI Workstation • Engine V2
          </span>
          <h1 className="simulation-workbench__title">Simulation Workbench</h1>
        </div>

        <div className="simulation-workbench__meta">
          <SimulationStatusBadge
            status={status}
            evidenceClass={evidenceClass ?? (activeMode === "canonical" ? "canonical" : activeMode === "practice" ? "practice" : activeMode === "batch" ? "batch_member" : undefined)}
            archiveState={archiveState}
          />
        </div>
      </header>

      {/* Mode Sub-navigation */}
      <nav
        className="simulation-workbench__tabs"
        role="tablist"
        aria-label="Simulation Modes"
      >
        {MODES.map((mode) => {
          const Icon = mode.icon;
          const isSelected = activeMode === mode.id;
          return (
            <button
              key={mode.id}
              role="tab"
              id={`tab-${mode.id}`}
              aria-selected={isSelected}
              aria-controls={`panel-${mode.id}`}
              tabIndex={isSelected ? 0 : -1}
              className="simulation-workbench__tab-btn"
              onClick={() => handleSelectMode(mode.id)}
            >
              <Icon className="w-4 h-4" aria-hidden="true" />
              <span>{mode.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Error banner if active */}
      {errorMessage ? (
        <div
          className="simulation-workbench__error-banner"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" aria-hidden="true" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            className="text-xs underline hover:text-white"
            onClick={() => setErrorMessage(null)}
          >
            Dismiss
          </button>
        </div>
      ) : null}

      {/* Main Panel Content */}
      <main
        id={`panel-${activeMode}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeMode}`}
        tabIndex={0}
        className="simulation-workbench__panel"
      >
        {children ?? (
          <DefaultPanelContent
            modeInfo={currentModeInfo}
            runId={initialRunId}
            sessionId={initialSessionId}
            batchId={initialBatchId}
          />
        )}
      </main>
    </div>
  );
}

function DefaultPanelContent({
  modeInfo,
  runId,
  sessionId,
  batchId,
}: {
  modeInfo: (typeof MODES)[number];
  runId?: string;
  sessionId?: string;
  batchId?: string;
}): ReactNode {
  return (
    <div className="simulation-workbench__empty">
      <div className="p-3 rounded-full bg-slate-800/80 border border-slate-700/60 mb-2">
        <modeInfo.icon className="w-8 h-8 text-teal-400" aria-hidden="true" />
      </div>
      <h2 className="simulation-workbench__empty-title">{modeInfo.label}</h2>
      <p className="text-sm max-w-md text-slate-400">{modeInfo.description}</p>

      {runId ? (
        <p className="text-xs text-slate-500 font-mono mt-2">Active Run: {runId}</p>
      ) : null}
      {sessionId ? (
        <p className="text-xs text-slate-500 font-mono mt-2">Active Session: {sessionId}</p>
      ) : null}
      {batchId ? (
        <p className="text-xs text-slate-500 font-mono mt-2">Active Batch: {batchId}</p>
      ) : null}
    </div>
  );
}
