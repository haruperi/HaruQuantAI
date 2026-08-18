/**
 * Analytics Workspace root shell component (FEAT-UI-32).
 *
 * Exposes the Analytics performance workbench across 7 dedicated sections:
 * - Summary & ratios
 * - Returns & VAMI
 * - Drawdowns & streaks
 * - Trade drilldown & excursions
 * - Period aggregations & calendar
 * - Benchmark relative returns & cost drag
 * - Artifact references & journal replay anchors
 *
 * Every metric is computed by Analytics and strictly validated.
 */

"use client";

import { useState, type ReactNode } from "react";
import {
  AlertTriangle,
  Archive,
  Layers,
} from "lucide-react";

import type { RunCatalogueEntry } from "@/clients";
import { SimulationStatusBadge } from "@/features/simulation-workbench";
import {
  ANALYTICS_TABS,
  AnalyticsNav,
  type AnalyticsTab,
} from "./AnalyticsNav";
import "./analytics-workbench.css";

export interface AnalyticsWorkspaceProps {
  runId?: string;
  runDetail?: RunCatalogueEntry | null;
  activeTab?: AnalyticsTab;
  initialTab?: AnalyticsTab;
  onTabChange?: (tab: AnalyticsTab) => void;
  compareRunIds?: string[];
  onCompareChange?: (runIds: string[]) => void;
  onArchiveToggle?: (archived: boolean) => void;
  className?: string;
  children?: ReactNode;
}

export function AnalyticsWorkspace({
  runId,
  runDetail,
  activeTab: controlledTab,
  initialTab = "overview",
  onTabChange,
  compareRunIds = [],
  onCompareChange,
  onArchiveToggle,
  className = "",
  children,
}: AnalyticsWorkspaceProps): ReactNode {
  const [internalTab, setInternalTab] = useState<AnalyticsTab>(initialTab);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeTab = controlledTab ?? internalTab;

  const handleTabChange = (tab: AnalyticsTab) => {
    if (!controlledTab) {
      setInternalTab(tab);
    }
    setErrorMessage(null);
    onTabChange?.(tab);
  };

  const currentTabInfo =
    ANALYTICS_TABS.find((t) => t.id === activeTab) ?? ANALYTICS_TABS[0];

  const isArchived = runDetail?.archive_state === "archived";

  return (
    <div
      className={`analytics-workbench ${className}`}
      role="region"
      aria-label="Analytics Workspace"
    >
      {/* Run Header */}
      <header className="analytics-workbench__header">
        <div className="analytics-workbench__header-top">
          <div className="analytics-workbench__title-group">
            <span className="analytics-workbench__eyebrow">
              HaruQuantAI Workstation • Analytics V2
            </span>
            <h1 className="analytics-workbench__title">
              {runDetail?.name || (runId ? `Run Analysis: ${runId}` : "Analytics Workspace")}
            </h1>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {runDetail ? (
              <SimulationStatusBadge
                status={runDetail.status}
                evidenceClass={runDetail.evidence_class}
                archiveState={runDetail.archive_state}
              />
            ) : null}

            {onCompareChange ? (
              <button
                type="button"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-slate-800 hover:bg-slate-700 text-teal-300 border border-slate-700"
                onClick={() => onCompareChange(compareRunIds)}
                aria-label="Compare runs"
              >
                <Layers className="w-3.5 h-3.5" aria-hidden="true" />
                Compare ({compareRunIds.length})
              </button>
            ) : null}

            {onArchiveToggle ? (
              <button
                type="button"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                onClick={() => onArchiveToggle(!isArchived)}
                aria-label={isArchived ? "Unarchive run" : "Archive run"}
              >
                <Archive className="w-3.5 h-3.5" aria-hidden="true" />
                {isArchived ? "Unarchive" : "Archive"}
              </button>
            ) : null}
          </div>
        </div>

        {/* Metadata Strip */}
        {runDetail ? (
          <div className="analytics-workbench__meta-strip">
            <div className="analytics-workbench__meta-item">
              <span className="analytics-workbench__meta-label">Strategy:</span>
              <span className="analytics-workbench__meta-value">
                {runDetail.strategy_label || runDetail.strategy_id}
              </span>
            </div>

            <div className="analytics-workbench__meta-item">
              <span className="analytics-workbench__meta-label">Symbols:</span>
              <span className="analytics-workbench__meta-value">
                {runDetail.symbols.join(", ")}
              </span>
            </div>

            <div className="analytics-workbench__meta-item">
              <span className="analytics-workbench__meta-label">Timeframe:</span>
              <span className="analytics-workbench__meta-value">
                {runDetail.timeframe}
              </span>
            </div>

            <div className="analytics-workbench__meta-item">
              <span className="analytics-workbench__meta-label">Window:</span>
              <span className="analytics-workbench__meta-value font-mono text-xs">
                {runDetail.measurement_start.slice(0, 10)} → {runDetail.measurement_end.slice(0, 10)}
              </span>
            </div>

            {runDetail.alias ? (
              <div className="analytics-workbench__meta-item">
                <span className="analytics-workbench__meta-label">Alias:</span>
                <span className="analytics-workbench__meta-value font-mono text-xs">
                  {runDetail.alias}
                </span>
              </div>
            ) : null}
          </div>
        ) : null}
      </header>

      {/* 7-Tab Sub-navigation */}
      <AnalyticsNav activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Error banner */}
      {errorMessage ? (
        <div
          className="analytics-workbench__error-banner p-3 rounded bg-red-950/60 border border-red-800 text-red-300 text-sm flex items-center justify-between"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
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
        id={`analytics-panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`analytics-tab-${activeTab}`}
        tabIndex={0}
        className="analytics-workbench__panel"
      >
        {children ?? (
          <DefaultAnalyticsPanel
            tabInfo={currentTabInfo}
            runId={runId}
            runDetail={runDetail}
          />
        )}
      </main>
    </div>
  );
}

function DefaultAnalyticsPanel({
  tabInfo,
  runId,
  runDetail,
}: {
  tabInfo: (typeof ANALYTICS_TABS)[number];
  runId?: string;
  runDetail?: RunCatalogueEntry | null;
}): ReactNode {
  return (
    <div className="analytics-workbench__empty">
      <div className="p-3 rounded-full bg-slate-800/80 border border-slate-700/60 mb-2">
        <tabInfo.icon className="w-8 h-8 text-teal-400" aria-hidden="true" />
      </div>
      <h2 className="analytics-workbench__empty-title">{tabInfo.label}</h2>
      <p className="text-sm max-w-md text-slate-400">{tabInfo.description}</p>

      {runId ? (
        <p className="text-xs text-slate-500 font-mono mt-2">Active Run: {runId}</p>
      ) : null}
      {runDetail?.strategy_id ? (
        <p className="text-xs text-slate-500 font-mono">Strategy: {runDetail.strategy_id}</p>
      ) : null}
    </div>
  );
}
