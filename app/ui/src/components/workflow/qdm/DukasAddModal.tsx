"use client";

import React, { useState } from "react";
import { X, Plus, Search, Check } from "lucide-react";

// Standard popular Dukascopy symbols
const DUKAS_SYMBOLS = [
  { symbol: "EURUSD", name: "Euro vs US Dollar", cat: "Forex Majors" },
  { symbol: "GBPUSD", name: "British Pound vs US Dollar", cat: "Forex Majors" },
  { symbol: "USDJPY", name: "US Dollar vs Japanese Yen", cat: "Forex Majors" },
  { symbol: "USDCHF", name: "US Dollar vs Swiss Franc", cat: "Forex Majors" },
  { symbol: "AUDUSD", name: "Australian Dollar vs US Dollar", cat: "Forex Majors" },
  { symbol: "USDCAD", name: "US Dollar vs Canadian Dollar", cat: "Forex Majors" },
  { symbol: "NZDUSD", name: "New Zealand Dollar vs US Dollar", cat: "Forex Majors" },
  { symbol: "EURGBP", name: "Euro vs British Pound", cat: "Forex Crosses" },
  { symbol: "EURJPY", name: "Euro vs Japanese Yen", cat: "Forex Crosses" },
  { symbol: "GBPJPY", name: "British Pound vs Japanese Yen", cat: "Forex Crosses" },
  { symbol: "XAUUSD", name: "Gold vs US Dollar", cat: "Metals" },
  { symbol: "XAGUSD", name: "Silver vs US Dollar", cat: "Metals" },
  { symbol: "BRENTCMDUSD", name: "Brent Crude Oil", cat: "Commodities" },
  { symbol: "LIGHTCMDUSD", name: "WTI Crude Oil", cat: "Commodities" },
  { symbol: "USA500IDXUSD", name: "US S&P 500 Index", cat: "Indices" },
  { symbol: "USATECHIDXUSD", name: "US Tech 100 Index", cat: "Indices" },
  { symbol: "USA30IDXUSD", name: "Dow Jones 30 Index", cat: "Indices" },
  { symbol: "DEUIDXEUR", name: "Germany DAX 40", cat: "Indices" },
  { symbol: "BTCUSD", name: "Bitcoin vs US Dollar", cat: "Crypto" },
  { symbol: "ETHUSD", name: "Ethereum vs US Dollar", cat: "Crypto" },
];

interface DukasAddModalProps {
  onClose: () => void;
  onAdded: (symbol: string) => void;
}

export function DukasAddModal({ onClose, onAdded }: DukasAddModalProps) {
  const [search, setSearch] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>("EURUSD");
  const [adding, setAdding] = useState(false);

  const filtered = DUKAS_SYMBOLS.filter(
    (s) =>
      s.symbol.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.cat.toLowerCase().includes(search.toLowerCase())
  );

  const handleAdd = async () => {
    if (!selectedSymbol) return;
    setAdding(true);
    try {
      // Notify parent to add or queue download
      onAdded(selectedSymbol);
      onClose();
    } finally {
      setAdding(false);
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
          width: 520,
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
          <span style={{ fontWeight: 600, color: "#f8fafc", fontSize: 14 }}>
            Add Dukascopy Symbol
          </span>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}
          >
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: 18, display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Search bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 10px",
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 4,
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder="Search symbol, currency, or asset class..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                color: "#f8fafc",
                fontSize: 12,
                width: "100%",
                outline: "none",
              }}
            />
          </div>

          {/* List of symbols */}
          <div
            style={{
              maxHeight: 280,
              overflowY: "auto",
              border: "1px solid #1e293b",
              borderRadius: 4,
              background: "#080c11",
            }}
          >
            {filtered.map((item) => {
              const isSelected = selectedSymbol === item.symbol;
              return (
                <div
                  key={item.symbol}
                  onClick={() => setSelectedSymbol(item.symbol)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 12px",
                    borderBottom: "1px solid #151d28",
                    cursor: "pointer",
                    background: isSelected ? "rgba(56, 189, 248, 0.12)" : "transparent",
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, color: isSelected ? "#38bdf8" : "#f1f5f9", fontSize: 13 }}>
                      {item.symbol}
                    </span>
                    <span style={{ fontSize: 11, color: "#64748b", marginLeft: 8 }}>
                      {item.name}
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 6px",
                        borderRadius: 3,
                        background: "#1e293b",
                        color: "#94a3b8",
                      }}
                    >
                      {item.cat}
                    </span>
                    {isSelected && <Check size={14} color="#38bdf8" />}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
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
              type="button"
              onClick={handleAdd}
              disabled={!selectedSymbol || adding}
              style={{
                padding: "8px 16px",
                background: "#0284c7",
                border: "none",
                color: "#fff",
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
                cursor: !selectedSymbol || adding ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <Plus size={14} />
              Add Symbol
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
