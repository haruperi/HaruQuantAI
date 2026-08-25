/**
 * Job progress widget (FR-UI-TRACK_PROGRESS, FR-UI-PRESENT_FAILURES),
 * owned by FEAT-UI-MONITOR_WORK.
 *
 * Implements:
 * - Bounded progress tracking without fabricating precision; indeterminate work labeled indeterminate (R15).
 * - Structured failure presentation with error code, title, detail, causal reference, retryability, and suggested action (R16).
 * - Non-blocking degraded state when provider is unavailable.
 */

import React, { useEffect, useState } from "react";
import type { WidgetProps } from "../types";
import type { ProgressPresentation, ErrorPresentation } from "../../contracts/generated/ui";
import { useMonitorWorkClient } from "../../features/monitor_work";

interface JobProgressState {
  readonly status: "loading" | "ready" | "unavailable";
  readonly progress: ProgressPresentation | null;
  readonly error: ErrorPresentation | null;
  readonly statusMessage?: string;
}

function newRequestId(prefix: string): string {
  const cryptoRef = globalThis.crypto as Crypto | undefined;
  if (cryptoRef && typeof cryptoRef.randomUUID === "function") {
    return `${prefix}-${cryptoRef.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

export const JobProgressWidget: React.FC<WidgetProps> = () => {
  const client = useMonitorWorkClient();
  const [state, setState] = useState<JobProgressState>({
    status: "loading",
    progress: null,
    error: null,
    statusMessage: "Fetching work monitoring state...",
  });

  const isMockClient = (client as { isDevOnly?: boolean }).isDevOnly === true;

  useEffect(() => {
    let cancelled = false;
    client
      .monitorWork({
        request_id: newRequestId("req-monitor-work"),
        capability_snapshot_id: "snap-current",
        operation: "TRACK",
      })
      .then((res) => {
        if (cancelled) return;
        setState({
          status: "ready",
          progress: res.progress ?? null,
          error: res.error ?? null,
        });
      })
      .catch(() => {
        if (cancelled) return;
        setState({
          status: "unavailable",
          progress: null,
          error: null,
          statusMessage: "Work monitoring provider unavailable.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [client]);

  return (
    <div
      className="job-progress-widget"
      data-testid="job-progress-widget"
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        height: "100%",
        boxSizing: "border-box",
        overflow: "auto",
      }}
    >
      <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", color: "#38bdf8" }}>
        Work Monitor & Progress
      </h3>

      {state.status === "loading" && (
        <div data-testid="job-progress-loading" style={{ color: "#94a3b8", fontSize: "13px" }}>
          {state.statusMessage}
        </div>
      )}

      {state.status === "unavailable" && (
        <div
          data-testid="job-progress-unavailable"
          style={{
            padding: "10px",
            backgroundColor: "#451a03",
            color: "#fdba74",
            borderRadius: "4px",
            fontSize: "13px",
          }}
        >
          {state.statusMessage}
        </div>
      )}

      {state.status === "ready" && (
        <>
          {/* FR-UI-PRESENT_FAILURES: Structured failure card */}
          {state.error && (
            <div
              data-testid="job-progress-failure-card"
              role="alert"
              style={{
                marginBottom: "16px",
                padding: "12px",
                backgroundColor: "#450a0a",
                border: "1px solid #dc2626",
                borderRadius: "6px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span
                  data-testid="failure-error-code"
                  style={{
                    fontSize: "11px",
                    fontWeight: "bold",
                    color: "#f87171",
                    backgroundColor: "#7f1d1d",
                    padding: "2px 6px",
                    borderRadius: "3px",
                  }}
                >
                  {state.error.error_code}
                </span>
                <span
                  data-testid="failure-retryability"
                  style={{
                    fontSize: "11px",
                    fontWeight: "bold",
                    color: state.error.is_retryable ? "#86efac" : "#fca5a5",
                    backgroundColor: state.error.is_retryable ? "#14532d" : "#7f1d1d",
                    padding: "2px 6px",
                    borderRadius: "3px",
                  }}
                >
                  {state.error.is_retryable ? "Retryable" : "Non-retryable"}
                </span>
              </div>
              <div data-testid="failure-title" style={{ fontSize: "14px", fontWeight: "bold", color: "#fecaca", marginBottom: "4px" }}>
                {state.error.title}
              </div>
              <div data-testid="failure-detail" style={{ fontSize: "13px", color: "#e2e8f0", marginBottom: "8px" }}>
                {state.error.detail}
              </div>
              {state.error.causal_reference && (
                <div data-testid="failure-causal-ref" style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                  <strong>Causal Reference:</strong> {state.error.causal_reference}
                </div>
              )}
              {state.error.suggested_action && (
                <div data-testid="failure-suggested-action" style={{ fontSize: "12px", color: "#38bdf8", marginTop: "6px" }}>
                  <strong>Suggested Action:</strong> {state.error.suggested_action}
                </div>
              )}
            </div>
          )}

          {/* FR-UI-TRACK_PROGRESS: Bounded progress with indeterminate discrimination */}
          {state.progress ? (
            <div data-testid="job-progress-details" style={{ backgroundColor: "#1e293b", padding: "12px", borderRadius: "6px" }}>
              <div data-testid="job-progress-task-id" style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
                <strong>Task ID:</strong> {state.progress.task_id}
              </div>
              <div data-testid="job-progress-stage" style={{ fontSize: "14px", fontWeight: "bold", color: "#f1f5f9", marginBottom: "6px" }}>
                Stage: {state.progress.stage_name}
              </div>

              {state.progress.is_indeterminate || state.progress.progress_percent == null ? (
                <div
                  data-testid="job-progress-indeterminate"
                  style={{
                    display: "inline-block",
                    padding: "4px 8px",
                    backgroundColor: "#334155",
                    color: "#facc15",
                    borderRadius: "4px",
                    fontSize: "12px",
                    fontWeight: "bold",
                    marginBottom: "8px",
                  }}
                >
                  Progress: Indeterminate
                </div>
              ) : (
                <div style={{ marginBottom: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                    <span>Progress</span>
                    <span data-testid="job-progress-percent">{state.progress.progress_percent}%</span>
                  </div>
                  <div style={{ width: "100%", height: "8px", backgroundColor: "#334155", borderRadius: "4px", overflow: "hidden" }}>
                    <div
                      data-testid="job-progress-bar"
                      style={{
                        width: `${Math.min(100, Math.max(0, parseFloat(state.progress.progress_percent) || 0))}%`,
                        height: "100%",
                        backgroundColor: "#38bdf8",
                        borderRadius: "4px",
                      }}
                    />
                  </div>
                </div>
              )}

              {state.progress.message && (
                <div data-testid="job-progress-message" style={{ fontSize: "13px", color: "#cbd5e1", marginTop: "6px" }}>
                  {state.progress.message}
                </div>
              )}
            </div>
          ) : (
            !state.error && (
              <div data-testid="job-progress-idle" style={{ color: "#64748b", fontSize: "13px" }}>
                No active work in progress.
              </div>
            )
          )}
        </>
      )}

      {isMockClient && (
        <div
          data-testid="job-progress-mock-label"
          role="note"
          style={{
            marginTop: "12px",
            padding: "6px 10px",
            backgroundColor: "#422006",
            color: "#fbbf24",
            borderRadius: "4px",
            fontSize: "12px",
            fontWeight: "bold",
          }}
        >
          MOCK DATA — non-authoritative (dev-only provider)
        </div>
      )}
    </div>
  );
};
