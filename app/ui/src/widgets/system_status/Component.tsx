import React from "react";
import type { WidgetProps } from "../types";
import { useShellSnapshot } from "../../runtime/context";

export const SystemStatusWidget: React.FC<WidgetProps> = () => {
  const snapshot = useShellSnapshot();

  return (
    <div
      className="system-status-widget"
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
        System Status & Capabilities
      </h3>
      <div style={{ marginBottom: "12px", fontSize: "13px" }}>
        <strong>Global Status:</strong>{" "}
        <span style={{ color: snapshot.is_ready ? "#4ade80" : "#facc15" }}>
          {snapshot.status_message}
        </span>
      </div>

      <div style={{ fontSize: "13px", fontWeight: "bold", marginBottom: "8px" }}>
        Capability Readiness:
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {Object.entries(snapshot.capability_states).length === 0 ? (
          <div style={{ color: "#64748b", fontSize: "12px" }}>No registered capabilities.</div>
        ) : (
          Object.entries(snapshot.capability_states).map(([capId, state]) => (
            <div
              key={capId}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "6px 10px",
                backgroundColor: "#1e293b",
                borderRadius: "4px",
                fontSize: "12px",
              }}
            >
              <code>{capId}</code>
              <span
                style={{
                  fontWeight: "bold",
                  color: state === "ready" ? "#4ade80" : state === "loading" ? "#facc15" : "#f87171",
                }}
              >
                {state.toUpperCase()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
