"use client";

import React, { useState } from "react";
import { Terminal, X, Trash2 } from "lucide-react";

export interface LogEntry {
  timestamp: string;
  level: "INFO" | "SUCCESS" | "WARN" | "ERROR";
  message: string;
}

interface DataLogViewProps {
  logs: LogEntry[];
  onClear: () => void;
  onClose: () => void;
}

export function DataLogView({ logs, onClear, onClose }: DataLogViewProps) {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");

  const filtered = logs.filter((l) => {
    if (filterLevel === "ALL") return true;
    return l.level === filterLevel;
  });

  return (
    <div
      style={{
        height: 180,
        background: "#080c11",
        borderTop: "1px solid #1e2633",
        display: "flex",
        flexDirection: "column",
        fontSize: 11,
        fontFamily: "monospace",
      }}
    >
      {/* Log Console Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "4px 12px",
          background: "#0f1622",
          borderBottom: "1px solid #1e2633",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Terminal size={13} color="#38bdf8" />
          <span style={{ fontWeight: 600, color: "#f8fafc", fontFamily: "sans-serif" }}>
            QDM Operational Logs ({logs.length})
          </span>
          <div style={{ display: "flex", gap: 4, marginLeft: 10 }}>
            {["ALL", "INFO", "SUCCESS", "WARN", "ERROR"].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                style={{
                  background: filterLevel === lvl ? "#1e293b" : "transparent",
                  color: filterLevel === lvl ? "#38bdf8" : "#64748b",
                  border: "none",
                  borderRadius: 3,
                  padding: "1px 6px",
                  fontSize: 10,
                  cursor: "pointer",
                }}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={onClear}
            style={{
              background: "transparent",
              border: "none",
              color: "#64748b",
              cursor: "pointer",
              padding: 2,
            }}
            title="Clear logs"
          >
            <Trash2 size={13} />
          </button>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#64748b",
              cursor: "pointer",
              padding: 2,
            }}
            title="Close log console"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Log List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "6px 12px" }}>
        {filtered.length === 0 ? (
          <div style={{ color: "#475569", padding: "12px 0" }}>
            No log entries yet. Operations will record status messages here.
          </div>
        ) : (
          filtered.map((item, idx) => {
            const color =
              item.level === "ERROR" ? "#f87171"
              : item.level === "WARN" ? "#fbbf24"
              : item.level === "SUCCESS" ? "#34d399"
              : "#94a3b8";
            return (
              <div key={idx} style={{ lineHeight: "1.6", color: "#e2e8f0" }}>
                <span style={{ color: "#64748b", marginRight: 8 }}>[{item.timestamp}]</span>
                <span style={{ color, fontWeight: 600, marginRight: 8 }}>[{item.level}]</span>
                <span>{item.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
