"use client";

import React, { useState } from "react";
import { X, Binary, Download } from "lucide-react";
import { data } from "@/clients";

interface ExportMt4ModalProps {
  symbol: string;
  onClose: () => void;
  onSuccess: (result: Record<string, unknown>) => void;
}

export function ExportMt4Modal({
  symbol,
  onClose,
  onSuccess,
}: ExportMt4ModalProps) {
  const [timeframe, setTimeframe] = useState("M1");
  const [spread, setSpread] = useState(15);
  const [digits, setDigits] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await data.exportData({
        symbol,
        format: "mt4",
        timeframe,
      });

      if (res.status === "success" && res.data) {
        onSuccess(res.data);
        onClose();
      } else {
        setError(res.message || "Failed to generate MT4 export.");
      }
    } catch (err: any) {
      setError(err?.message || "MT4 export generation failed.");
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
          width: 460,
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
            <Binary size={16} color="#38bdf8" />
            <span style={{ fontWeight: 600, color: "#f8fafc", fontSize: 14 }}>
              Export to MetaTrader 4: {symbol}
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
              Target MT4 Chart Period
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
              <option value="M1">M1 (1 Minute HST & FXT)</option>
              <option value="M5">M5 (5 Minutes HST & FXT)</option>
              <option value="M15">M15 (15 Minutes HST & FXT)</option>
              <option value="H1">H1 (1 Hour HST & FXT)</option>
              <option value="D1">D1 (Daily HST & FXT)</option>
            </select>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
                Spread (points)
              </label>
              <input
                type="number"
                value={spread}
                onChange={(e) => setSpread(parseInt(e.target.value, 10))}
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
                Price Digits
              </label>
              <input
                type="number"
                value={digits}
                onChange={(e) => setDigits(parseInt(e.target.value, 10))}
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
            Generates standard MetaTrader 4 HST history format and FXT 99% tick modeling files
            directly in the target output folder.
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
              {submitting ? "Generating..." : "Generate HST/FXT"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
