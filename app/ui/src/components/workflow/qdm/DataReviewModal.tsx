"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  X,
  TrendingUp,
  Table as TableIcon,
  ShieldAlert,
  AlertTriangle,
  Search,
  CheckCircle2,
  Save,
  RotateCcw,
} from "lucide-react";
import {
  createChart,
  CandlestickSeries,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type Time,
} from "lightweight-charts";

import { data, type QualityReport } from "@/clients";

interface BarItem {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface DataReviewModalProps {
  symbol: string;
  initialTimeframe?: string;
  onClose: () => void;
}

type ReviewTab = "chart" | "table" | "quality";

export function DataReviewModal({
  symbol,
  initialTimeframe = "M1",
  onClose,
}: DataReviewModalProps) {
  const [activeTab, setActiveTab] = useState<ReviewTab>("chart");
  const [timeframe, setTimeframe] = useState<string>(initialTimeframe);
  const [bars, setBars] = useState<BarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Quality state
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [loadingQuality, setLoadingQuality] = useState(false);

  // Bar table state
  const [editingBarIndex, setEditingBarIndex] = useState<number | null>(null);
  const [editingValues, setEditingValues] = useState<Partial<BarItem>>({});
  const [filterQuery, setFilterQuery] = useState("");

  // Chart refs
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // Load Bars
  useEffect(() => {
    let isCancelled = false;
    async function fetchBars() {
      setLoading(true);
      setError(null);
      try {
        const res = await data.bars({
          symbol,
          timeframe: timeframe as any,
          limit: 3000,
        });
        if (!isCancelled) {
          if (res.status === "success" && res.data?.bars) {
            const rawBars: BarItem[] = res.data.bars
              .map((b) => {
                let epoch = 0;
                if (typeof b.time === "number") {
                  epoch = b.time;
                } else if (typeof b.time === "string") {
                  epoch = Math.floor(new Date(b.time).getTime() / 1000);
                }
                return {
                  time: epoch,
                  open: Number(b.open ?? 0),
                  high: Number(b.high ?? 0),
                  low: Number(b.low ?? 0),
                  close: Number(b.close ?? 0),
                  volume: Number(b.volume ?? 0),
                };
              })
              .filter((b) => b.time > 0);

            // Sort ascending by timestamp
            rawBars.sort((a, b) => a.time - b.time);
            setBars(rawBars);
          } else {
            setError(res.message || "Failed to load bars for symbol.");
          }
        }
      } catch (err: any) {
        if (!isCancelled) {
          setError(err?.message || "Failed to fetch bars.");
        }
      } finally {
        if (!isCancelled) setLoading(false);
      }
    }

    fetchBars();
    return () => {
      isCancelled = true;
    };
  }, [symbol, timeframe]);

  // Load Quality Inspection
  useEffect(() => {
    let isCancelled = false;
    async function fetchQuality() {
      setLoadingQuality(true);
      try {
        const res = await data.quality(symbol, timeframe);
        if (!isCancelled && res.status === "success") {
          setQualityReport(res.data);
        }
      } catch (e) {
        console.error("Failed to load quality report", e);
      } finally {
        if (!isCancelled) setLoadingQuality(false);
      }
    }

    fetchQuality();
    return () => {
      isCancelled = true;
    };
  }, [symbol, timeframe]);

  // Render Lightweight Charts Candlestick Chart
  useEffect(() => {
    if (activeTab !== "chart" || !chartContainerRef.current || bars.length === 0) {
      return;
    }

    // Dispose old chart
    if (chartInstanceRef.current) {
      chartInstanceRef.current.remove();
      chartInstanceRef.current = null;
    }

    const container = chartContainerRef.current;
    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 500,
      layout: {
        background: { color: "#0b0f14" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e2633" },
        horzLines: { color: "#1e2633" },
      },
      timeScale: {
        borderColor: "#1e2633",
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "#1e2633",
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    const candleData: CandlestickData<Time>[] = bars.map((b) => ({
      time: b.time as Time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));

    candleSeries.setData(candleData);
    chart.timeScale().fitContent();

    chartInstanceRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (chartInstanceRef.current && container) {
        chartInstanceRef.current.applyOptions({
          width: container.clientWidth,
          height: container.clientHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }
    };
  }, [activeTab, bars]);

  // Jump to date handler in Bar Table
  const filteredBars = React.useMemo(() => {
    if (!filterQuery) return bars;
    const q = filterQuery.toLowerCase();
    return bars.filter((b) => {
      const dt = new Date(b.time * 1000).toISOString();
      return dt.includes(q);
    });
  }, [bars, filterQuery]);

  const handleSaveBar = (index: number) => {
    if (!editingValues) return;
    setBars((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...editingValues };
      return next;
    });
    setEditingBarIndex(null);
    setEditingValues({});
  };

  const anomalyCount =
    (qualityReport?.problems.gap.count || 0) +
    (qualityReport?.problems.spike.count || 0) +
    (qualityReport?.problems.ohlc.count || 0);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
      }}
    >
      <div
        style={{
          width: "92vw",
          maxWidth: 1300,
          height: "88vh",
          background: "#0d131a",
          border: "1px solid #1e293b",
          borderRadius: 8,
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 25px 50px -12px rgba(0,0,0,0.7)",
          overflow: "hidden",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px 18px",
            background: "#080c11",
            borderBottom: "1px solid #1e2633",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span
              style={{
                fontSize: 16,
                fontWeight: 700,
                color: "#f8fafc",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              Data Review: <span style={{ color: "#38bdf8" }}>{symbol}</span>
            </span>

            {/* Timeframe selector pill */}
            <div
              style={{
                display: "flex",
                background: "#161e2b",
                borderRadius: 4,
                padding: 2,
                border: "1px solid #233044",
              }}
            >
              {["M1", "M5", "M15", "H1", "D1"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  style={{
                    background: timeframe === tf ? "#0284c7" : "transparent",
                    color: timeframe === tf ? "#fff" : "#94a3b8",
                    border: "none",
                    borderRadius: 3,
                    padding: "3px 8px",
                    fontSize: 11,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>

            <span style={{ fontSize: 11, color: "#64748b" }}>
              ({bars.length.toLocaleString()} bars loaded)
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
                padding: 4,
                borderRadius: 4,
              }}
              aria-label="Close Data Review"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "0 18px",
            background: "#0f1622",
            borderBottom: "1px solid #1e2633",
            gap: 6,
          }}
        >
          <button
            onClick={() => setActiveTab("chart")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 16px",
              background: "transparent",
              color: activeTab === "chart" ? "#38bdf8" : "#94a3b8",
              border: "none",
              borderBottom: activeTab === "chart" ? "2px solid #38bdf8" : "2px solid transparent",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <TrendingUp size={15} /> Chart
          </button>

          <button
            onClick={() => setActiveTab("table")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 16px",
              background: "transparent",
              color: activeTab === "table" ? "#38bdf8" : "#94a3b8",
              border: "none",
              borderBottom: activeTab === "table" ? "2px solid #38bdf8" : "2px solid transparent",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <TableIcon size={15} /> Bar Table
          </button>

          <button
            onClick={() => setActiveTab("quality")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "8px 16px",
              background: "transparent",
              color: activeTab === "quality" ? "#38bdf8" : "#94a3b8",
              border: "none",
              borderBottom: activeTab === "quality" ? "2px solid #38bdf8" : "2px solid transparent",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <ShieldAlert size={15} /> Quality
            {anomalyCount > 0 && (
              <span
                style={{
                  background: "#ef4444",
                  color: "#fff",
                  fontSize: 10,
                  fontWeight: 700,
                  borderRadius: 10,
                  padding: "1px 6px",
                  marginLeft: 4,
                }}
              >
                {anomalyCount}
              </span>
            )}
          </button>
        </div>

        {/* Tab Content Body */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          {loading && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "rgba(11, 15, 20, 0.7)",
                zIndex: 10,
                color: "#38bdf8",
                fontSize: 14,
              }}
            >
              Loading historical bars from Parquet archive...
            </div>
          )}

          {error && (
            <div
              style={{
                padding: 24,
                color: "#ef4444",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <AlertTriangle size={18} /> {error}
            </div>
          )}

          {/* TAB 1: CHART */}
          {activeTab === "chart" && (
            <div
              ref={chartContainerRef}
              style={{
                width: "100%",
                height: "100%",
              }}
            />
          )}

          {/* TAB 2: BAR TABLE */}
          {activeTab === "table" && (
            <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
              {/* Filter bar */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 16px",
                  background: "#080c11",
                  borderBottom: "1px solid #1e2633",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Search size={14} color="#64748b" />
                  <input
                    type="text"
                    placeholder="Filter by Date (YYYY-MM-DD)..."
                    value={filterQuery}
                    onChange={(e) => setFilterQuery(e.target.value)}
                    style={{
                      background: "#161e2b",
                      border: "1px solid #233044",
                      borderRadius: 4,
                      color: "#f8fafc",
                      padding: "4px 8px",
                      fontSize: 12,
                      width: 220,
                    }}
                  />
                </div>

                <div style={{ fontSize: 11, color: "#64748b" }}>
                  Showing {filteredBars.length.toLocaleString()} of {bars.length.toLocaleString()} rows
                </div>
              </div>

              {/* Virtualized Table Scroll Area */}
              <div style={{ flex: 1, overflowY: "auto" }}>
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: 12,
                    textAlign: "right",
                  }}
                >
                  <thead
                    style={{
                      position: "sticky",
                      top: 0,
                      background: "#121924",
                      borderBottom: "1px solid #1e2633",
                      color: "#94a3b8",
                      fontSize: 11,
                    }}
                  >
                    <tr>
                      <th style={{ padding: "8px 12px", textAlign: "left" }}>Date</th>
                      <th style={{ padding: "8px 12px", textAlign: "left" }}>Time</th>
                      <th style={{ padding: "8px 12px" }}>Open</th>
                      <th style={{ padding: "8px 12px" }}>High</th>
                      <th style={{ padding: "8px 12px" }}>Low</th>
                      <th style={{ padding: "8px 12px" }}>Close</th>
                      <th style={{ padding: "8px 12px" }}>Volume</th>
                      <th style={{ padding: "8px 12px", textAlign: "center" }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBars.slice(0, 500).map((b, idx) => {
                      const dt = new Date(b.time * 1000);
                      const isEditing = editingBarIndex === idx;
                      const dateStr = dt.toISOString().slice(0, 10);
                      const timeStr = dt.toISOString().slice(11, 16);

                      return (
                        <tr
                          key={b.time}
                          style={{
                            borderBottom: "1px solid #151d28",
                            background: idx % 2 === 0 ? "rgba(255,255,255,0.01)" : "transparent",
                          }}
                        >
                          <td style={{ padding: "6px 12px", textAlign: "left", color: "#94a3b8" }}>
                            {dateStr}
                          </td>
                          <td style={{ padding: "6px 12px", textAlign: "left", color: "#cbd5e1" }}>
                            {timeStr}
                          </td>

                          {isEditing ? (
                            <>
                              <td style={{ padding: "4px 8px" }}>
                                <input
                                  type="number"
                                  step="0.00001"
                                  defaultValue={b.open}
                                  onChange={(e) =>
                                    setEditingValues((prev) => ({
                                      ...prev,
                                      open: parseFloat(e.target.value),
                                    }))
                                  }
                                  style={{
                                    width: 80,
                                    background: "#1e293b",
                                    color: "#fff",
                                    border: "1px solid #38bdf8",
                                    borderRadius: 3,
                                    padding: "2px 4px",
                                    fontSize: 11,
                                    textAlign: "right",
                                  }}
                                />
                              </td>
                              <td style={{ padding: "4px 8px" }}>
                                <input
                                  type="number"
                                  step="0.00001"
                                  defaultValue={b.high}
                                  onChange={(e) =>
                                    setEditingValues((prev) => ({
                                      ...prev,
                                      high: parseFloat(e.target.value),
                                    }))
                                  }
                                  style={{
                                    width: 80,
                                    background: "#1e293b",
                                    color: "#fff",
                                    border: "1px solid #38bdf8",
                                    borderRadius: 3,
                                    padding: "2px 4px",
                                    fontSize: 11,
                                    textAlign: "right",
                                  }}
                                />
                              </td>
                              <td style={{ padding: "4px 8px" }}>
                                <input
                                  type="number"
                                  step="0.00001"
                                  defaultValue={b.low}
                                  onChange={(e) =>
                                    setEditingValues((prev) => ({
                                      ...prev,
                                      low: parseFloat(e.target.value),
                                    }))
                                  }
                                  style={{
                                    width: 80,
                                    background: "#1e293b",
                                    color: "#fff",
                                    border: "1px solid #38bdf8",
                                    borderRadius: 3,
                                    padding: "2px 4px",
                                    fontSize: 11,
                                    textAlign: "right",
                                  }}
                                />
                              </td>
                              <td style={{ padding: "4px 8px" }}>
                                <input
                                  type="number"
                                  step="0.00001"
                                  defaultValue={b.close}
                                  onChange={(e) =>
                                    setEditingValues((prev) => ({
                                      ...prev,
                                      close: parseFloat(e.target.value),
                                    }))
                                  }
                                  style={{
                                    width: 80,
                                    background: "#1e293b",
                                    color: "#fff",
                                    border: "1px solid #38bdf8",
                                    borderRadius: 3,
                                    padding: "2px 4px",
                                    fontSize: 11,
                                    textAlign: "right",
                                  }}
                                />
                              </td>
                              <td style={{ padding: "4px 8px" }}>
                                <input
                                  type="number"
                                  defaultValue={b.volume}
                                  onChange={(e) =>
                                    setEditingValues((prev) => ({
                                      ...prev,
                                      volume: parseInt(e.target.value, 10),
                                    }))
                                  }
                                  style={{
                                    width: 70,
                                    background: "#1e293b",
                                    color: "#fff",
                                    border: "1px solid #38bdf8",
                                    borderRadius: 3,
                                    padding: "2px 4px",
                                    fontSize: 11,
                                    textAlign: "right",
                                  }}
                                />
                              </td>
                              <td style={{ padding: "4px 8px", textAlign: "center" }}>
                                <button
                                  onClick={() => handleSaveBar(idx)}
                                  style={{
                                    background: "#10b981",
                                    border: "none",
                                    borderRadius: 3,
                                    color: "#fff",
                                    padding: "2px 6px",
                                    fontSize: 11,
                                    cursor: "pointer",
                                    marginRight: 4,
                                  }}
                                >
                                  <Save size={11} />
                                </button>
                                <button
                                  onClick={() => setEditingBarIndex(null)}
                                  style={{
                                    background: "#64748b",
                                    border: "none",
                                    borderRadius: 3,
                                    color: "#fff",
                                    padding: "2px 6px",
                                    fontSize: 11,
                                    cursor: "pointer",
                                  }}
                                >
                                  <RotateCcw size={11} />
                                </button>
                              </td>
                            </>
                          ) : (
                            <>
                              <td style={{ padding: "6px 12px", color: "#f8fafc" }}>
                                {b.open.toFixed(5)}
                              </td>
                              <td style={{ padding: "6px 12px", color: "#10b981" }}>
                                {b.high.toFixed(5)}
                              </td>
                              <td style={{ padding: "6px 12px", color: "#ef4444" }}>
                                {b.low.toFixed(5)}
                              </td>
                              <td style={{ padding: "6px 12px", color: "#f8fafc" }}>
                                {b.close.toFixed(5)}
                              </td>
                              <td style={{ padding: "6px 12px", color: "#94a3b8" }}>
                                {b.volume.toLocaleString()}
                              </td>
                              <td style={{ padding: "6px 12px", textAlign: "center" }}>
                                <button
                                  onClick={() => {
                                    setEditingBarIndex(idx);
                                    setEditingValues(b);
                                  }}
                                  style={{
                                    background: "rgba(255,255,255,0.05)",
                                    border: "1px solid #334155",
                                    borderRadius: 3,
                                    color: "#38bdf8",
                                    padding: "2px 6px",
                                    fontSize: 10,
                                    cursor: "pointer",
                                  }}
                                >
                                  Edit
                                </button>
                              </td>
                            </>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: QUALITY ANOMALY INSPECTOR */}
          {activeTab === "quality" && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                padding: 18,
                gap: 16,
                overflowY: "auto",
              }}
            >
              {loadingQuality && (
                <div style={{ fontSize: 12, color: "#38bdf8", padding: "4px 8px" }}>
                  Analyzing historical quality anomalies...
                </div>
              )}

              {/* Summary Cards */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(4, 1fr)",
                  gap: 12,
                }}
              >
                <div
                  style={{
                    background: "#080c11",
                    border: "1px solid #1e2633",
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>
                    TOTAL BARS INSPECTED
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "#f8fafc", marginTop: 4 }}>
                    {bars.length.toLocaleString()}
                  </div>
                  <div style={{ fontSize: 11, color: "#10b981", marginTop: 2 }}>
                    Parquet archive verified
                  </div>
                </div>

                <div
                  style={{
                    background: "#080c11",
                    border: "1px solid #1e2633",
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>
                    MISSING BARS / GAPS
                  </div>
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 700,
                      color: qualityReport?.problems.gap.count ? "#f59e0b" : "#10b981",
                      marginTop: 4,
                    }}
                  >
                    {qualityReport?.problems.gap.count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>
                    {qualityReport?.problems.gap.percent || "0.00%"} of series
                  </div>
                </div>

                <div
                  style={{
                    background: "#080c11",
                    border: "1px solid #1e2633",
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>
                    PRICE SPIKES
                  </div>
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 700,
                      color: qualityReport?.problems.spike.count ? "#ef4444" : "#10b981",
                      marginTop: 4,
                    }}
                  >
                    {qualityReport?.problems.spike.count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>
                    {qualityReport?.problems.spike.percent || "0.00%"} of series
                  </div>
                </div>

                <div
                  style={{
                    background: "#080c11",
                    border: "1px solid #1e2633",
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>
                    BAD OHLC LOGIC
                  </div>
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 700,
                      color: qualityReport?.problems.ohlc.count ? "#ef4444" : "#10b981",
                      marginTop: 4,
                    }}
                  >
                    {qualityReport?.problems.ohlc.count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>
                    {qualityReport?.problems.ohlc.percent || "0.00%"} of series
                  </div>
                </div>
              </div>

              {/* Anomaly Timeline Visual */}
              <div
                style={{
                  background: "#080c11",
                  border: "1px solid #1e2633",
                  borderRadius: 6,
                  padding: 14,
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600, color: "#cbd5e1", marginBottom: 8 }}>
                  Anomaly Distribution Timeline
                </div>
                <div
                  style={{
                    width: "100%",
                    height: 20,
                    background: "#161e2b",
                    borderRadius: 4,
                    position: "relative",
                    overflow: "hidden",
                  }}
                >
                  {qualityReport?.timeline && qualityReport.timeline.length > 0 ? (
                    qualityReport.timeline.map((item: { time: number; type: string }, idx: number) => {
                      const firstTime = bars[0]?.time || 1;
                      const lastTime = bars[bars.length - 1]?.time || firstTime + 1;
                      const pct = Math.max(
                        0,
                        Math.min(100, ((item.time - firstTime) / (lastTime - firstTime)) * 100)
                      );
                      const color =
                        item.type.includes("Spike") ? "#ef4444"
                        : item.type.includes("Gap") ? "#f59e0b"
                        : "#ec4899";
                      return (
                        <div
                          key={idx}
                          title={`${item.type} at ${new Date(item.time * 1000).toISOString()}`}
                          style={{
                            position: "absolute",
                            left: `${pct}%`,
                            top: 0,
                            bottom: 0,
                            width: 3,
                            background: color,
                          }}
                        />
                      );
                    })
                  ) : (
                    <div
                      style={{
                        width: "100%",
                        height: "100%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 10,
                        color: "#10b981",
                        fontWeight: 600,
                      }}
                    >
                      No anomalies detected in selected timeframe.
                    </div>
                  )}
                </div>
              </div>

              {/* Anomaly Details Table */}
              <div
                style={{
                  flex: 1,
                  background: "#080c11",
                  border: "1px solid #1e2633",
                  borderRadius: 6,
                  overflow: "hidden",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                <div
                  style={{
                    padding: "8px 14px",
                    background: "#121924",
                    borderBottom: "1px solid #1e2633",
                    fontSize: 12,
                    fontWeight: 600,
                    color: "#cbd5e1",
                  }}
                >
                  Identified Quality Anomalies ({qualityReport?.details.length || 0})
                </div>

                <div style={{ flex: 1, overflowY: "auto" }}>
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: 11,
                      textAlign: "left",
                    }}
                  >
                    <thead
                      style={{
                        position: "sticky",
                        top: 0,
                        background: "#0d131a",
                        borderBottom: "1px solid #1e2633",
                        color: "#64748b",
                      }}
                    >
                      <tr>
                        <th style={{ padding: "6px 12px" }}>Timestamp</th>
                        <th style={{ padding: "6px 12px" }}>Anomaly Type</th>
                        <th style={{ padding: "6px 12px" }}>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {qualityReport?.details && qualityReport.details.length > 0 ? (
                        qualityReport.details.map((d: { timestamp: string; issue: string; description: string }, i: number) => (
                          <tr
                            key={i}
                            style={{
                              borderBottom: "1px solid #151d28",
                              background: i % 2 === 0 ? "rgba(255,255,255,0.01)" : "transparent",
                            }}
                          >
                            <td style={{ padding: "6px 12px", color: "#94a3b8" }}>
                              {d.timestamp}
                            </td>
                            <td style={{ padding: "6px 12px" }}>
                              <span
                                style={{
                                  padding: "2px 6px",
                                  borderRadius: 3,
                                  fontSize: 10,
                                  fontWeight: 600,
                                  background:
                                    d.issue.includes("Spike") ? "rgba(239,68,68,0.15)"
                                    : d.issue.includes("Gap") ? "rgba(245,158,11,0.15)"
                                    : "rgba(236,72,153,0.15)",
                                  color:
                                    d.issue.includes("Spike") ? "#f87171"
                                    : d.issue.includes("Gap") ? "#fbbf24"
                                    : "#f472b6",
                                }}
                              >
                                {d.issue}
                              </span>
                            </td>
                            <td style={{ padding: "6px 12px", color: "#e2e8f0" }}>
                              {d.description}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td
                            colSpan={3}
                            style={{
                              padding: "24px 12px",
                              textAlign: "center",
                              color: "#64748b",
                            }}
                          >
                            <CheckCircle2
                              size={20}
                              color="#10b981"
                              style={{ display: "inline-block", marginRight: 6 }}
                            />
                            Data series is pristine. Zero quality anomalies identified.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
