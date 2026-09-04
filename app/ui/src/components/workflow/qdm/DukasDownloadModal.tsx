"use client";

import React, { useState } from "react";
import { X, Download } from "lucide-react";
import { data } from "@/clients";

interface DukasDownloadModalProps {
  symbol: string;
  onClose: () => void;
  onStarted: (taskName: string) => void;
}

export function DukasDownloadModal({
  symbol,
  onClose,
  onStarted,
}: DukasDownloadModalProps) {
  const [dateFrom, setDateFrom] = useState("2020-01-01");
  const [dateTo, setDateTo] = useState(new Date().toISOString().slice(0, 10));
  const [dataType, setDataType] = useState<"M1" | "Tick">("M1");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await data.downloadDukascopy({
        symbols: [symbol],
        date_from: dateFrom,
        date_to: dateTo,
      });
      if (res.status === "success") {
        onStarted(`Downloading Dukascopy: ${symbol} (${dateFrom} to ${dateTo})`);
        onClose();
      } else {
        setError(res.message || "Failed to start download job.");
      }
    } catch (err: any) {
      setError(err?.message || "Download initiation failed.");
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
          width: 480,
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
            <Download size={16} color="#38bdf8" />
            <span style={{ fontWeight: 600, color: "#f8fafc", fontSize: 14 }}>
              Download Data: {symbol}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
          {error && (
            <div style={{ padding: 8, background: "rgba(239, 68, 68, 0.15)", color: "#f87171", fontSize: 12, borderRadius: 4 }}>
              {error}
            </div>
          )}

          <div>
            <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
              Data Precision / Type
            </label>
            <div style={{ display: "flex", gap: 10 }}>
              {(["M1", "Tick"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setDataType(t)}
                  style={{
                    flex: 1,
                    padding: "8px 12px",
                    background: dataType === t ? "rgba(56, 189, 248, 0.15)" : "#1e293b",
                    border: dataType === t ? "1px solid #38bdf8" : "1px solid #334155",
                    color: dataType === t ? "#38bdf8" : "#cbd5e1",
                    borderRadius: 4,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {t === "M1" ? "1-Minute Bars (Fast)" : "Tick-by-Tick Data"}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
                Date From
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 4,
                  color: "#f8fafc",
                  fontSize: 12,
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
                Date To
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 4,
                  color: "#f8fafc",
                  fontSize: 12,
                }}
              />
            </div>
          </div>

          <div
            style={{
              padding: 10,
              background: "#080c11",
              borderRadius: 4,
              fontSize: 11,
              color: "#64748b",
              lineHeight: 1.5,
            }}
          >
            Historical data will be saved directly into canonical Parquet storage at{" "}
            <code style={{ color: "#38bdf8" }}>data/market_data/bars/dukascopy/{symbol.toLowerCase()}/</code>.
          </div>

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
              {submitting ? "Initiating..." : "Start Download"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
