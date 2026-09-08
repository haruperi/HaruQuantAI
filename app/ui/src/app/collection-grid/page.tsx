"use client";

import React, { useMemo, useState } from "react";
import {
  CollectionGridFeature,
  type ColumnDefinition,
  type GridState,
  type SelectionToken,
  type SortCriterion,
} from "@/widgets/collection-grid";

interface DemoMarketRow {
  id: number;
  symbol: string;
  price: number | null;
  change: number;
  volume: number;
  status: string;
  lastTradeTime: string | null;
  exchange: string;
  notes?: string;
}

const SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "BRK.B", "JPM", "V"];
const EXCHANGES = ["NASDAQ", "NYSE", "BATS", "IEX"];
const STATUSES = ["ACTIVE", "HALTED", "AUCTION", "CLOSED"];

function generateDemoRows(count: number): DemoMarketRow[] {
  const baseTime = Date.now();
  return Array.from({ length: count }, (_, i) => {
    const symbol = SYMBOLS[i % SYMBOLS.length];
    const isEven = i % 2 === 0;
    const isThird = i % 3 === 0;

    return {
      id: i + 1,
      symbol: `${symbol}-${(i % 100).toString().padStart(2, "0")}`,
      price: i % 17 === 0 ? null : Math.round((100 + (i % 500) * 1.75 + Math.sin(i) * 20) * 100) / 100,
      change: Math.round(Math.sin(i) * 5 * 100) / 100,
      volume: (i * 137) % 1_000_000 + 100,
      status: STATUSES[i % STATUSES.length],
      lastTradeTime: isThird ? null : new Date(baseTime - i * 60_000).toISOString(),
      exchange: EXCHANGES[i % EXCHANGES.length],
      notes: isEven ? (i % 4 === 0 ? undefined : `Batch note ${i + 1}`) : undefined,
    };
  });
}

export default function CollectionGridDemoPage(): React.JSX.Element {
  const [rowCount, setRowCount] = useState<number>(10_000);
  const [gridState, setGridState] = useState<GridState>("idle");
  const [selection, setSelection] = useState<SelectionToken | undefined>(undefined);
  const [sort, setSort] = useState<SortCriterion | null>({ columnId: "id", direction: "asc" });

  const rows = useMemo(() => generateDemoRows(rowCount), [rowCount]);

  const columns: ColumnDefinition<DemoMarketRow>[] = useMemo(
    () => [
      { id: "id", header: "ID", kind: "numeric", width: 75, pinned: "left" },
      { id: "symbol", header: "Symbol", kind: "text", width: 130, pinned: "left" },
      { id: "price", header: "Price ($)", kind: "numeric", width: 110, format: (val) => (val == null ? "—" : `$${Number(val).toFixed(2)}`) },
      { id: "change", header: "Change", kind: "numeric", width: 100 },
      { id: "volume", header: "Volume", kind: "numeric", width: 120 },
      { id: "status", header: "Status", kind: "enum", width: 110 },
      { id: "lastTradeTime", header: "Last Trade", kind: "date", width: 190 },
      { id: "exchange", header: "Exchange", kind: "text", width: 110 },
      { id: "notes", header: "Notes", kind: "text", width: 160 },
    ],
    [],
  );

  return (
    <main
      style={{
        padding: "24px",
        maxWidth: "1400px",
        margin: "0 auto",
        fontFamily: "system-ui, -apple-system, sans-serif",
        color: "#e1e4ea",
        minHeight: "100vh",
        backgroundColor: "#0d1117",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1 style={{ margin: "0 0 4px 0", fontSize: "22px", fontWeight: 600, color: "#fff" }}>
              CollectionGrid Live Interactive Demo
            </h1>
            <p style={{ margin: 0, fontSize: "14px", color: "#8b949e" }}>
              FEAT-UI-VIEW_COLLECTIONS — ARIA grid semantics, virtual window scrolling, bounded $O(1)$ selection, sorting &amp; pinning
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <span
              style={{
                fontSize: "12px",
                padding: "4px 8px",
                borderRadius: "4px",
                background: "#1f6feb22",
                border: "1px solid #1f6feb",
                color: "#58a6ff",
              }}
            >
              Current: {rowCount.toLocaleString()} rows
            </span>
            <span
              style={{
                fontSize: "12px",
                padding: "4px 8px",
                borderRadius: "4px",
                background: "#23863622",
                border: "1px solid #238636",
                color: "#3fb950",
              }}
            >
              Mode: {selection?.mode ?? "empty"}
            </span>
          </div>
        </div>
      </div>

      {/* Control toolbar */}
      <div
        style={{
          display: "flex",
          gap: "16px",
          alignItems: "center",
          flexWrap: "wrap",
          padding: "12px 16px",
          backgroundColor: "#161b22",
          border: "1px solid #30363d",
          borderRadius: "6px",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label htmlFor="row-select" style={{ fontSize: "13px", fontWeight: 500, color: "#c9d1d9" }}>
            Dataset Size:
          </label>
          <select
            id="row-select"
            value={rowCount}
            onChange={(e) => {
              setRowCount(Number(e.target.value));
              setSelection(undefined);
            }}
            style={{
              background: "#21262d",
              color: "#fff",
              border: "1px solid #30363d",
              borderRadius: "4px",
              padding: "4px 8px",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            <option value={100}>100 rows</option>
            <option value={1000}>1,000 rows</option>
            <option value={10000}>10,000 rows</option>
            <option value={100000}>100,000 rows</option>
            <option value={1000000}>1,000,000 rows (Stress Test)</option>
          </select>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label htmlFor="state-select" style={{ fontSize: "13px", fontWeight: 500, color: "#c9d1d9" }}>
            Grid State:
          </label>
          <select
            id="state-select"
            value={gridState}
            onChange={(e) => setGridState(e.target.value as GridState)}
            style={{
              background: "#21262d",
              color: "#fff",
              border: "1px solid #30363d",
              borderRadius: "4px",
              padding: "4px 8px",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            <option value="idle">Normal (idle)</option>
            <option value="loading">Loading State</option>
            <option value="empty">Empty State</option>
            <option value="error">Error State</option>
          </select>
        </div>

        <button
          type="button"
          onClick={() => setSelection(undefined)}
          style={{
            background: "#21262d",
            color: "#c9d1d9",
            border: "1px solid #30363d",
            borderRadius: "4px",
            padding: "4px 12px",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          Clear Selection
        </button>

        <div style={{ marginLeft: "auto", fontSize: "12px", color: "#8b949e" }}>
          Showing visible virtual slice (~20-30 DOM elements)
        </div>
      </div>

      {/* Grid container */}
      <div
        style={{
          border: "1px solid #30363d",
          borderRadius: "6px",
          overflow: "hidden",
          background: "#0d1117",
          boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
        }}
      >
        <CollectionGridFeature<DemoMarketRow>
          columns={columns}
          rows={gridState === "empty" ? [] : rows}
          state={gridState}
          error={gridState === "error" ? { message: "Simulated market data feed error", code: "FEED_UNAVAILABLE" } : null}
          height={560}
          sortCriterion={sort}
          onSortChange={setSort}
          selectionToken={selection}
          onSelectionChange={setSelection}
          onRetry={() => setGridState("idle")}
        />
      </div>

      {/* Interactive guide / keyboard reference */}
      <div
        style={{
          marginTop: "20px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "16px",
        }}
      >
        <div style={{ background: "#161b22", padding: "14px 16px", borderRadius: "6px", border: "1px solid #30363d" }}>
          <h2 style={{ fontSize: "14px", fontWeight: 600, color: "#58a6ff", margin: "0 0 8px 0" }}>🖱️ Mouse &amp; Interactions</h2>
          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "13px", color: "#8b949e", lineHeight: "1.6" }}>
            <li><strong>Click column header</strong> to sort (preserves 2 &lt; 10 numeric logic &amp; dates)</li>
            <li><strong>Shift + Click header</strong> for multi-column sort</li>
            <li><strong>Drag column separator</strong> to resize columns</li>
            <li><strong>Select All checkbox</strong>: Bounded $O(1)$ token selection</li>
            <li><strong>Right-click any row</strong>: Open row context menu</li>
          </ul>
        </div>

        <div style={{ background: "#161b22", padding: "14px 16px", borderRadius: "6px", border: "1px solid #30363d" }}>
          <h2 style={{ fontSize: "14px", fontWeight: 600, color: "#3fb950", margin: "0 0 8px 0" }}>⌨️ Keyboard Navigation</h2>
          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "13px", color: "#8b949e", lineHeight: "1.6" }}>
            <li><strong>↑ / ↓ Arrow keys</strong>: Navigate up/down rows</li>
            <li><strong>PageUp / PageDown</strong>: Jump by page height</li>
            <li><strong>Home / End</strong>: Jump directly to start / end of dataset</li>
            <li><strong>Shift + ↑ / ↓</strong>: Expand range selection</li>
            <li><strong>Space</strong>: Toggle row selection</li>
          </ul>
        </div>

        <div style={{ background: "#161b22", padding: "14px 16px", borderRadius: "6px", border: "1px solid #30363d" }}>
          <h2 style={{ fontSize: "14px", fontWeight: 600, color: "#d29922", margin: "0 0 8px 0" }}>⚡ Performance Guarantees</h2>
          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "13px", color: "#8b949e", lineHeight: "1.6" }}>
            <li>Virtual scrolling renders only visible window (~25 rows)</li>
            <li>Test with 1,000,000 rows without memory crashes</li>
            <li>Select All on 1M rows uses &lt;1KB memory ($O(1)$ token)</li>
            <li>Missing or null values explicitly display <code>—</code> or <code>N/A</code></li>
          </ul>
        </div>
      </div>
    </main>
  );
}
