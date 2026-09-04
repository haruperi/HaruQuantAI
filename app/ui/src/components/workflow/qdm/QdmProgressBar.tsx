"use client";

import React from "react";
import { Play, Pause, XCircle, Settings2, CheckCircle2, AlertCircle } from "lucide-react";

export interface BatchTask {
  id: string;
  name: string;
  progress: number; // 0 to 100
  status: "running" | "paused" | "completed" | "failed";
  details?: string;
}

interface QdmProgressBarProps {
  task: BatchTask | null;
  onPauseResume?: () => void;
  onCancel?: () => void;
  onOpenSettings?: () => void;
}

export function QdmProgressBar({
  task,
  onPauseResume,
  onCancel,
  onOpenSettings,
}: QdmProgressBarProps) {
  if (!task) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "6px 14px",
          background: "#0b0f14",
          borderTop: "1px solid var(--border-color, #1e2633)",
          fontSize: 11,
          color: "#64748b",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <CheckCircle2 size={13} color="#10b981" />
          <span>QDM Engine Idle — All operations complete.</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={onOpenSettings}
            style={{
              background: "transparent",
              border: "none",
              color: "#64748b",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <Settings2 size={13} />
            Settings
          </button>
        </div>
      </div>
    );
  }

  const isPaused = task.status === "paused";
  const isFailed = task.status === "failed";
  const isCompleted = task.status === "completed";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        background: "#0f172a",
        borderTop: "1px solid #1e293b",
        padding: "8px 14px",
        gap: 6,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {isFailed ? (
            <AlertCircle size={14} color="#ef4444" />
          ) : isCompleted ? (
            <CheckCircle2 size={14} color="#10b981" />
          ) : (
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: isPaused ? "#f59e0b" : "#38bdf8",
                animation: isPaused ? "none" : "pulse 1.5s infinite",
              }}
            />
          )}
          <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{task.name}</span>
          {task.details && (
            <span style={{ color: "#94a3b8", fontSize: 11 }}>({task.details})</span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontWeight: 700, color: "#38bdf8", fontSize: 12 }}>
            {task.progress}%
          </span>

          {!isCompleted && !isFailed && onPauseResume && (
            <button
              onClick={onPauseResume}
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid #334155",
                borderRadius: 4,
                padding: "2px 6px",
                color: "#e2e8f0",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 4,
                fontSize: 11,
              }}
            >
              {isPaused ? <Play size={11} /> : <Pause size={11} />}
              {isPaused ? "Resume" : "Pause"}
            </button>
          )}

          {!isCompleted && onCancel && (
            <button
              onClick={onCancel}
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
                borderRadius: 4,
                padding: "2px 6px",
                color: "#f87171",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 4,
                fontSize: 11,
              }}
            >
              <XCircle size={11} />
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Progress Track */}
      <div
        style={{
          width: "100%",
          height: 6,
          background: "#1e293b",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${task.progress}%`,
            height: "100%",
            background: isFailed
              ? "#ef4444"
              : isCompleted
              ? "#10b981"
              : "linear-gradient(90deg, #0284c7 0%, #38bdf8 100%)",
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}
