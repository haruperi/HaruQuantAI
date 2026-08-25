/**
 * Activity log widget (FR-UI-STREAM_ACTIVITY), owned by FEAT-UI-MONITOR_WORK.
 *
 * Presents:
 * - Bounded ordered activity events with sequence numbers, timestamps, severity, and correlation.
 * - Explicit gap markers for discontinuous sequence numbers (never presented as continuous truth).
 * - Staleness banner when snapshot metadata indicates stale state.
 * - Explicit "Awaiting live feed — de-mock stage" note per UI migration rule §8.4.
 * - Bounded truncation notification.
 */

import React, { useMemo } from "react";
import type { WidgetProps } from "../types";
import {
  useActivitySnapshot,
  useMonitorWorkClient,
  ingestSnapshot,
  type ActivityEvent,
} from "../../features/monitor_work";

function getSeverityStyle(severity: ActivityEvent["severity"]): {
  readonly color: string;
  readonly bg: string;
} {
  switch (severity) {
    case "error":
      return { color: "#f87171", bg: "#7f1d1d" };
    case "warning":
      return { color: "#fbbf24", bg: "#78350f" };
    case "debug":
      return { color: "#94a3b8", bg: "#1e293b" };
    case "info":
    default:
      return { color: "#38bdf8", bg: "#0c4a6e" };
  }
}

export const ActivityLogWidget: React.FC<WidgetProps> = () => {
  const client = useMonitorWorkClient();
  const snapshot = useActivitySnapshot();

  const isMock =
    (client as { isDevOnly?: boolean }).isDevOnly === true ||
    snapshot?.is_mock === true;

  const ingestResult = useMemo(() => ingestSnapshot(snapshot), [snapshot]);

  return (
    <div
      className="activity-log-widget"
      data-testid="activity-log-widget"
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        height: "100%",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div style={{ marginBottom: "12px" }}>
        <h3 style={{ margin: "0 0 6px 0", fontSize: "16px", color: "#38bdf8" }}>
          Activity Log
        </h3>
        {/* Mock-stage streaming rule §8.4 status note */}
        <div
          data-testid="activity-log-feed-status"
          style={{ fontSize: "12px", color: "#94a3b8" }}
        >
          Feed status: Awaiting live feed — de-mock stage (bounded snapshot view)
        </div>
      </div>

      {/* FR-UI-STREAM_ACTIVITY: Staleness banner */}
      {ingestResult.is_stale && (
        <div
          data-testid="activity-log-stale-banner"
          role="alert"
          style={{
            marginBottom: "10px",
            padding: "8px 12px",
            backgroundColor: "#78350f",
            color: "#fef3c7",
            borderRadius: "4px",
            fontSize: "12px",
            fontWeight: "bold",
          }}
        >
          Activity snapshot is stale — live reconnect pending.
        </div>
      )}

      {/* Truncation notice */}
      {ingestResult.is_truncated && (
        <div
          data-testid="activity-log-truncation-marker"
          style={{
            marginBottom: "8px",
            padding: "6px 10px",
            backgroundColor: "#1e293b",
            color: "#94a3b8",
            borderRadius: "4px",
            fontSize: "11px",
          }}
        >
          Log buffer truncated: oldest {ingestResult.dropped_count} events dropped.
        </div>
      )}

      {/* Events and Gaps container */}
      <div
        data-testid="activity-log-events"
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
        }}
      >
        {ingestResult.entries.length === 0 ? (
          <div data-testid="activity-log-empty" style={{ color: "#64748b", fontSize: "13px", padding: "12px 0" }}>
            No activity events recorded.
          </div>
        ) : (
          ingestResult.entries.map((entry, idx) => {
            if (entry.type === "truncation") {
              return null; // Handled above
            }

            if (entry.type === "gap") {
              return (
                <div
                  key={`gap-${entry.from_sequence}-${entry.to_sequence}`}
                  data-testid="activity-log-gap-marker"
                  style={{
                    padding: "6px 10px",
                    backgroundColor: "#451a03",
                    border: "1px dashed #d97706",
                    borderRadius: "4px",
                    color: "#fde68a",
                    fontSize: "11px",
                    textAlign: "center",
                  }}
                >
                  Sequence gap detected: missing sequences {entry.from_sequence} through {entry.to_sequence} ({entry.missing_count} event{entry.missing_count > 1 ? "s" : ""})
                </div>
              );
            }

            const evt = entry.event;
            const sev = getSeverityStyle(evt.severity);

            return (
              <div
                key={evt.event_id || `seq-${evt.sequence}-${idx}`}
                data-testid={`activity-event-${evt.sequence}`}
                style={{
                  padding: "8px 10px",
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "4px",
                  fontSize: "12px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span
                      data-testid={`event-seq-${evt.sequence}`}
                      style={{
                        color: "#94a3b8",
                        fontFamily: "monospace",
                        fontSize: "11px",
                      }}
                    >
                      #{evt.sequence}
                    </span>
                    <span
                      data-testid={`event-severity-${evt.sequence}`}
                      style={{
                        padding: "1px 5px",
                        borderRadius: "3px",
                        fontSize: "10px",
                        fontWeight: "bold",
                        textTransform: "uppercase",
                        color: sev.color,
                        backgroundColor: sev.bg,
                      }}
                    >
                      {evt.severity}
                    </span>
                    <strong data-testid={`event-type-${evt.sequence}`} style={{ color: "#f1f5f9" }}>
                      {evt.event_type}
                    </strong>
                  </div>
                  <span
                    data-testid={`event-time-${evt.sequence}`}
                    style={{ color: "#64748b", fontSize: "11px" }}
                  >
                    {evt.timestamp_iso}
                  </span>
                </div>
                <div data-testid={`event-msg-${evt.sequence}`} style={{ color: "#cbd5e1" }}>
                  {evt.message}
                </div>
                {evt.correlation_id && (
                  <div
                    data-testid={`event-corr-${evt.sequence}`}
                    style={{ color: "#64748b", fontSize: "11px", marginTop: "2px" }}
                  >
                    Correlation: {evt.correlation_id}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {isMock && (
        <div
          data-testid="activity-log-mock-label"
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
