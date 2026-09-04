"use client";

import React, { useState } from "react";
import {
  Database,
  Download,
  Upload,
  Trash2,
  Eye,
  FileSpreadsheet,
  Binary,
  Clock,
  Terminal,
  ChevronDown,
  RefreshCw,
  Sparkles,
} from "lucide-react";

export type QdmRibbonTab =
  | "sources"
  | "export"
  | "tools"
  | "instruments"
  | "brokers";

interface QdmRibbonProps {
  activeTab: QdmRibbonTab;
  onSelectTab: (tab: QdmRibbonTab) => void;
  selectedSymbol: string | null;
  selectedSeriesId: number | null;
  onAddNew: (source: "dukascopy" | "file") => void;
  onDownload: () => void;
  onImport: () => void;
  onDelete: () => void;
  onReview: () => void;
  onExportCsv: () => void;
  onExportMt4: () => void;
  onCloneTimezone: () => void;
  onToggleLogs: () => void;
  onRefresh: () => void;
  isSyncing?: boolean;
}

export function QdmRibbon({
  activeTab,
  onSelectTab,
  selectedSymbol,
  selectedSeriesId,
  onAddNew,
  onDownload,
  onImport,
  onDelete,
  onReview,
  onExportCsv,
  onExportMt4,
  onCloneTimezone,
  onToggleLogs,
  onRefresh,
  isSyncing = false,
}: QdmRibbonProps) {
  const [showAddMenu, setShowAddMenu] = useState(false);

  const hasSelection = Boolean(selectedSymbol || selectedSeriesId);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        background: "var(--bg-secondary, #121820)",
        borderBottom: "1px solid var(--border-color, #1e2633)",
        userSelect: "none",
      }}
    >
      {/* Top Ribbon Tabs Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "0 12px",
          gap: 2,
          background: "var(--bg-primary, #0b0f14)",
          borderBottom: "1px solid var(--border-color, #1e2633)",
          height: 34,
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.08em",
            color: "var(--cme-blue-bright, #38bdf8)",
            marginRight: 12,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Database size={14} /> QDM WORKSPACE
        </span>

        {[
          { id: "sources" as const, label: "Data Sources" },
          { id: "export" as const, label: "Export" },
          { id: "tools" as const, label: "Tools" },
          { id: "instruments" as const, label: "Instruments & Sessions" },
          { id: "brokers" as const, label: "Broker Profiles" },
        ].map((t) => {
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => onSelectTab(t.id)}
              style={{
                background: isActive ? "var(--bg-secondary, #121820)" : "transparent",
                color: isActive ? "#f8fafc" : "#94a3b8",
                border: "none",
                borderBottom: isActive ? "2px solid #38bdf8" : "2px solid transparent",
                padding: "6px 14px",
                fontSize: 12,
                fontWeight: isActive ? 600 : 500,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {t.label}
            </button>
          );
        })}

        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={onRefresh}
            disabled={isSyncing}
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid var(--border-color, #1e2633)",
              color: "#cbd5e1",
              borderRadius: 4,
              padding: "4px 8px",
              fontSize: 11,
              display: "flex",
              alignItems: "center",
              gap: 5,
              cursor: isSyncing ? "not-allowed" : "pointer",
            }}
            title="Refresh series catalogue"
          >
            <RefreshCw size={12} className={isSyncing ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Ribbon Action Buttons Area */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "8px 16px",
          gap: 12,
          minHeight: 56,
          overflowX: "auto",
        }}
      >
        {activeTab === "sources" && (
          <>
            {/* Add New Data Split Button */}
            <div style={{ position: "relative", display: "inline-block" }}>
              <div style={{ display: "flex" }}>
                <button
                  onClick={() => onAddNew("dukascopy")}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "6px 10px",
                    background: "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
                    color: "#fff",
                    border: "none",
                    borderTopLeftRadius: 4,
                    borderBottomLeftRadius: 4,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  <Sparkles size={14} /> Add new data
                </button>
                <button
                  onClick={() => setShowAddMenu((v) => !v)}
                  style={{
                    padding: "6px 6px",
                    background: "linear-gradient(135deg, #0369a1 0%, #075985 100%)",
                    color: "#fff",
                    border: "none",
                    borderLeft: "1px solid rgba(255,255,255,0.2)",
                    borderTopRightRadius: 4,
                    borderBottomRightRadius: 4,
                    cursor: "pointer",
                  }}
                >
                  <ChevronDown size={14} />
                </button>
              </div>

              {showAddMenu && (
                <div
                  style={{
                    position: "absolute",
                    top: "100%",
                    left: 0,
                    marginTop: 4,
                    background: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: 4,
                    padding: 4,
                    boxShadow: "0 10px 25px -5px rgba(0,0,0,0.5)",
                    zIndex: 50,
                    minWidth: 180,
                  }}
                  onMouseLeave={() => setShowAddMenu(false)}
                >
                  <button
                    onClick={() => {
                      setShowAddMenu(false);
                      onAddNew("dukascopy");
                    }}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "6px 10px",
                      background: "transparent",
                      border: "none",
                      color: "#e2e8f0",
                      fontSize: 12,
                      cursor: "pointer",
                      borderRadius: 3,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "#1e293b")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    Dukascopy (Free Historical)
                  </button>
                  <button
                    onClick={() => {
                      setShowAddMenu(false);
                      onAddNew("file");
                    }}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "6px 10px",
                      background: "transparent",
                      border: "none",
                      color: "#e2e8f0",
                      fontSize: 12,
                      cursor: "pointer",
                      borderRadius: 3,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "#1e293b")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    Import Custom File (CSV/TXT)
                  </button>
                </div>
              )}
            </div>

            <div style={{ width: 1, height: 28, background: "#1e2633" }} />

            {/* Download Button */}
            <button
              onClick={onDownload}
              disabled={!hasSelection}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                background: "transparent",
                border: "none",
                color: hasSelection ? "#38bdf8" : "#475569",
                cursor: hasSelection ? "pointer" : "not-allowed",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 11,
              }}
              title="Download historical data for selected symbol"
            >
              <Download size={18} />
              <span>Download data</span>
            </button>

            {/* Import Button */}
            <button
              onClick={onImport}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                background: "transparent",
                border: "none",
                color: "#e2e8f0",
                cursor: "pointer",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 11,
              }}
              title="Import historical files into repository"
            >
              <Upload size={18} />
              <span>Import from file</span>
            </button>

            {/* Delete Button */}
            <button
              onClick={onDelete}
              disabled={!hasSelection}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                background: "transparent",
                border: "none",
                color: hasSelection ? "#ef4444" : "#475569",
                cursor: hasSelection ? "pointer" : "not-allowed",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 11,
              }}
              title="Delete selected series and parquet archives"
            >
              <Trash2 size={18} />
              <span>Delete data</span>
            </button>

            <div style={{ width: 1, height: 28, background: "#1e2633" }} />

            {/* Data Review Button */}
            <button
              onClick={onReview}
              disabled={!hasSelection}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                background: hasSelection ? "rgba(56, 189, 248, 0.15)" : "rgba(255,255,255,0.03)",
                border: hasSelection ? "1px solid #38bdf8" : "1px solid #334155",
                color: hasSelection ? "#38bdf8" : "#475569",
                cursor: hasSelection ? "pointer" : "not-allowed",
                padding: "6px 12px",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
              }}
              title="Open full interactive review (Chart + Bar Table + Quality Anomaly Inspector)"
            >
              <Eye size={15} /> Data review
            </button>
          </>
        )}

        {activeTab === "export" && (
          <>
            <button
              onClick={onExportMt4}
              disabled={!hasSelection}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                background: "transparent",
                border: "none",
                color: hasSelection ? "#e2e8f0" : "#475569",
                cursor: hasSelection ? "pointer" : "not-allowed",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 11,
              }}
            >
              <Binary size={18} />
              <span>Export to MT4 (HST/FXT)</span>
            </button>

            <button
              onClick={onExportCsv}
              disabled={!hasSelection}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 3,
                background: "transparent",
                border: "none",
                color: hasSelection ? "#e2e8f0" : "#475569",
                cursor: hasSelection ? "pointer" : "not-allowed",
                padding: "4px 8px",
                borderRadius: 4,
                fontSize: 11,
              }}
            >
              <FileSpreadsheet size={18} />
              <span>Export to CSV</span>
            </button>
          </>
        )}

        {activeTab === "tools" && (
          <>
            <button
              onClick={onCloneTimezone}
              disabled={!hasSelection}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                background: hasSelection ? "rgba(16, 185, 129, 0.15)" : "rgba(255,255,255,0.03)",
                border: hasSelection ? "1px solid #10b981" : "1px solid #334155",
                color: hasSelection ? "#34d399" : "#475569",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
                cursor: hasSelection ? "pointer" : "not-allowed",
              }}
            >
              <Clock size={15} /> Clone to timezone
            </button>

            <button
              onClick={onToggleLogs}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid #334155",
                color: "#e2e8f0",
                borderRadius: 4,
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              <Terminal size={15} /> Log Console
            </button>
          </>
        )}

        {activeTab === "instruments" && (
          <span style={{ fontSize: 12, color: "#94a3b8" }}>
            Click on any instrument name below to edit tick size, spread, commission, and session trading hours.
          </span>
        )}

        {activeTab === "brokers" && (
          <span style={{ fontSize: 12, color: "#94a3b8" }}>
            Broker definitions configure default timezones and platform prefixes/postfixes across instruments.
          </span>
        )}
      </div>
    </div>
  );
}
