"use client";

import React, { useState } from "react";
import { X, Clock, Copy, ArrowRight } from "lucide-react";
import { data } from "@/clients";

interface CloneTimezoneModalProps {
  symbol: string;
  onClose: () => void;
  onCloned: (newSymbol: string) => void;
}

export function CloneTimezoneModal({
  symbol,
  onClose,
  onCloned,
}: CloneTimezoneModalProps) {
  const [shiftHours, setShiftHours] = useState(2); // e.g. UTC+2 (EET)
  const [postfix, setPostfix] = useState("_UTC+2");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleShiftChange = (val: number) => {
    setShiftHours(val);
    const sign = val >= 0 ? "+" : "";
    setPostfix(`_UTC${sign}${val}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await data.cloneSeries({
        symbol,
        target_shift_hours: shiftHours,
        postfix,
      });
      if (res.status === "success" && res.data?.symbol) {
        onCloned(res.data.symbol);
        onClose();
      } else {
        setError(res.message || "Failed to clone series.");
      }
    } catch (err: any) {
      setError(err?.message || "Clone operation failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const previewSymbol = `${symbol}${postfix}`;

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
            <Clock size={16} color="#10b981" />
            <span style={{ fontWeight: 600, color: "#f8fafc", fontSize: 14 }}>
              Clone to Timezone: {symbol}
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
              Timezone Shift (Hours relative to UTC)
            </label>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="range"
                min="-12"
                max="14"
                value={shiftHours}
                onChange={(e) => handleShiftChange(parseInt(e.target.value, 10))}
                style={{ flex: 1, accentColor: "#10b981" }}
              />
              <span
                style={{
                  minWidth: 65,
                  padding: "4px 8px",
                  background: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 700,
                  color: "#10b981",
                  textAlign: "center",
                }}
              >
                {shiftHours >= 0 ? `+${shiftHours}` : shiftHours} hrs
              </span>
            </div>
          </div>

          <div>
            <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 6 }}>
              Cloned Symbol Postfix
            </label>
            <input
              type="text"
              value={postfix}
              onChange={(e) => setPostfix(e.target.value)}
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

          {/* Preview banner */}
          <div
            style={{
              padding: 12,
              background: "#080c11",
              borderRadius: 6,
              border: "1px solid #1e2633",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={{ fontSize: 12, color: "#94a3b8" }}>Source: <b>{symbol}</b> (UTC)</span>
            <ArrowRight size={14} color="#64748b" />
            <span style={{ fontSize: 12, color: "#34d399", fontWeight: 700 }}>
              Result: <b>{previewSymbol}</b>
            </span>
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
                background: "#10b981",
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
              <Copy size={14} />
              {submitting ? "Cloning..." : "Execute Clone"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
