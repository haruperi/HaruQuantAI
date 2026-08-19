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

import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  AlertTriangle,
  Archive,
  Layers,
} from "lucide-react";

import {
  ApiClientError,
  apiClients,
  type AnalyticsWorkbenchPayload,
  type RunCatalogueEntry,
} from "@/clients";
import { SimulationStatusBadge } from "@/widgets/simulator";
import {
  AnalyticsNav,
  type AnalyticsTab,
} from "./AnalyticsNav";
import { OverviewPanel } from "./OverviewPanel";
import { ReturnsPanel } from "./ReturnsPanel";
import { RiskPanel } from "./RiskPanel";
import { TradesPanel } from "./TradesPanel";
import { PeriodsPanel } from "./PeriodsPanel";
import { BenchmarkPanel } from "./BenchmarkPanel";
import { AnalyticsArtifactDrawer } from "./AnalyticsArtifactDrawer";
import { AnalyticsLibrary } from "./AnalyticsLibrary";
import "./analytics.css";

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

/** Resolve a failure message without implying a successful read. */
function failureMessage(cause: unknown): string {
  if (cause instanceof ApiClientError || cause instanceof Error) {
    return cause.message;
  }
  return "The Analytics workbench projection is unavailable.";
}

export function AnalyticsWorkspace({
  runId: controlledRunId,
  runDetail: controlledRunDetail,
  activeTab: controlledTab,
  initialTab = "overview",
  onTabChange,
  compareRunIds = [],
  onCompareChange,
  onArchiveToggle,
  className = "",
  children,
}: AnalyticsWorkspaceProps): ReactNode {
  const [internalRunId, setInternalRunId] = useState<string | undefined>(controlledRunId);
  const [internalTab, setInternalTab] = useState<AnalyticsTab>(initialTab);
  const [runDetail, setRunDetail] = useState<RunCatalogueEntry | null>(
    controlledRunDetail ?? null,
  );
  const [payload, setPayload] = useState<AnalyticsWorkbenchPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const effectiveRunId = controlledRunId ?? internalRunId ?? runDetail?.run_id;
  const activeTab = controlledTab ?? internalTab;

  // Sync controlled props
  useEffect(() => {
    if (controlledRunId !== undefined) {
      setInternalRunId(controlledRunId);
    }
  }, [controlledRunId]);

  useEffect(() => {
    if (controlledRunDetail !== undefined) {
      setRunDetail(controlledRunDetail);
    }
  }, [controlledRunDetail]);

  const loadData = useCallback(async (id: string) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [runRes, payloadRes] = await Promise.allSettled([
        apiClients.analyticsWorkbench.getRun(id),
        apiClients.analyticsWorkbench.getWorkbenchPayload(id),
      ]);

      if (runRes.status === "fulfilled" && runRes.value.status === "success") {
        setRunDetail(runRes.value.data);
      }
      if (payloadRes.status === "fulfilled" && payloadRes.value.status === "success") {
        setPayload(payloadRes.value.data);
      } else if (
        payloadRes.status === "fulfilled" &&
        payloadRes.value.status === "error"
      ) {
        setErrorMessage(payloadRes.value.error.message);
      }
    } catch (cause) {
      setErrorMessage(failureMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (effectiveRunId) {
      void loadData(effectiveRunId);
    }
  }, [effectiveRunId, loadData]);

  const handleTabChange = (tab: AnalyticsTab) => {
    if (!controlledTab) {
      setInternalTab(tab);
    }
    setErrorMessage(null);
    onTabChange?.(tab);
  };

  const isArchived = runDetail?.archive_state === "archived";

  const renderActivePanel = () => {
    if (children) {
      return children;
    }

    if (!effectiveRunId) {
      return (
        <AnalyticsLibrary
          onSelectRun={(selectedId, tab) => {
            setInternalRunId(selectedId);
            if (tab) handleTabChange(tab);
          }}
          onCompare={onCompareChange}
        />
      );
    }

    switch (activeTab) {
      case "overview":
        return <OverviewPanel runId={effectiveRunId} />;
      case "returns":
        return (
          <ReturnsPanel
            payload={payload}
            loading={loading}
            error={errorMessage}
          />
        );
      case "drawdown":
        return (
          <RiskPanel
            payload={payload}
            loading={loading}
            error={errorMessage}
          />
        );
      case "trades":
        return <TradesPanel runId={effectiveRunId} />;
      case "grouped":
        return <PeriodsPanel runId={effectiveRunId} payload={payload} />;
      case "benchmark":
        return (
          <BenchmarkPanel
            payload={payload}
            loading={loading}
            error={errorMessage}
          />
        );
      case "artifacts":
        return <AnalyticsArtifactDrawer runId={effectiveRunId} />;
      default:
        return <OverviewPanel runId={effectiveRunId} />;
    }
  };

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
              {runDetail?.name || (effectiveRunId ? `Run Analysis: ${effectiveRunId}` : "Analytics Workspace")}
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
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-slate-800 hover:bg-slate-700 text-teal-300 border border-slate-700 cursor-pointer"
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
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 cursor-pointer"
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
                {runDetail.measurement_start ? runDetail.measurement_start.slice(0, 10) : "—"} → {runDetail.measurement_end ? runDetail.measurement_end.slice(0, 10) : "—"}
              </span>
            </div>

            {runDetail.quality_status ? (
              <div className="analytics-workbench__meta-item">
                <span className="analytics-workbench__meta-label">Quality:</span>
                <span className="analytics-workbench__meta-value font-mono text-xs">
                  {runDetail.quality_status}
                </span>
              </div>
            ) : null}

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
      {effectiveRunId ? (
        <AnalyticsNav activeTab={activeTab} onTabChange={handleTabChange} />
      ) : null}

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
            className="text-xs underline hover:text-white cursor-pointer bg-transparent border-0"
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
        {renderActivePanel()}
      </main>
    </div>
  );
}
