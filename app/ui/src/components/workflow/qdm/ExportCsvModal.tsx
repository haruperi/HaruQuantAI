"use client";

import React, { useState } from "react";
import { X, FileSpreadsheet, Download } from "lucide-react";
import { data } from "@/clients";

interface ExportCsvModalProps {
  symbol: string;
  onClose: () => void;
}

export function ExportCsvModal({ symbol, onClose }: ExportCsvModalProps) {
  const [timeframe, setTimeframe] = useState("M1");
  const [separator, setSeparator] = useState(",");
  const [includeHeaders, setIncludeHeaders] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await data.exportData({
        symbol,
        format: "csv",
        timeframe,
      });

      if (res.status === "success" && res.data?.content) {
        const content = String(res.data.content);
        const filename = (res.data.filename as string) || `${symbol}_${timeframe}.csv`;

        // Trigger browser download
        const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        onClose();
      } else {
        setError(res.message || "Failed to generate CSV export.");
      }
    } catch (err: any) {
      setError(err?.message || "Export failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.7)",
      }}
    >
      <div
        style={{
          width: 440,
          background: "#0f172a",
          border: "1px solid #334155",
          borderRadius: 8,
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 18px",
            background: "#1e293b",
            borderBottom: "1px solid #334155",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <FileSpreadsheet size={16} color="#38bdf8" />
            <span style={{ fontWeight: 600, color: "#f8fafc", fontSize: 14 }}>
              Export to CSV: {symbol}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleExport} style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
          {error && (
            <div style={{ padding: 8, background: "rgba(239, 68, 68, 0.15)", color: "#f87171", fontSize: 12, borderRadius: 4 }}>
              {error}
            </div>
          )}

          <div>
            <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
              Timeframe
            </label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 4,
                color: "#f8fafc",
                fontSize: 12,
              }}
            >
              <option value="M1">M1 (1 Minute)</option>
              <option value="M5">M5 (5 Minutes)</option>
              <option value="M15">M15 (15 Minutes)</option>
              <option value="H1">H1 (1 Hour)</option>
              <option value="D1">D1 (1 Day)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
              Column Delimiter / Separator
            </label>
            <select
              value={separator}
              onChange={(e) => setSeparator(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 4,
                color: "#f8fafc",
                fontSize: 12,
              }}
            >
              <option value=",">Comma (,)</option>
              <option value=";">Semicolon (;)</option>
              <option value="	">Tab (\t)</option>
            </select>
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#cbd5e1", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={includeHeaders}
              onChange={(e) => setIncludeHeaders(e.target.checked)}
              style={{ accentColor: "#0284c7" }}
            />
            Include standard header row (&lt;DATE&gt;,&lt;TIME&gt;,&lt;OPEN&gt;...)
          </label>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: "8px 16px",
                background: "transparent",
                border: "1px solid #334155",
                color: "#94a3b8",
                borderRadius: 4,
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: "8px 16px",
                background: "#0284c7",
                border: "none",
                color: "#fff",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
                cursor: submitting ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <Download size={14} />
              {submitting ? "Exporting..." : "Download CSV"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
