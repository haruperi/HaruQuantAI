import React, { useState, useRef, useMemo } from 'react';
import {
  FileText,
  Upload,
  RotateCw,
  SlidersHorizontal,
  TrendingUp,
  BarChart3,
  ListFilter,
  CheckCircle2,
  Calendar,
  DollarSign,
  Percent,
  X,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
} from 'lucide-react';
import { useMTAnalyzerStore } from './mtAnalyzerStore';
import type { MTStatementTrade } from '../../host/types';

export const MTAnalyzerWorkspace: React.FC = () => {
  const {
    trades,
    filteredTrades,
    metrics,
    filters,
    selectedPreset,
    isConfigureModalOpen,
    activeTab,
    statementFileName,
    loadPreset,
    importHtmlStatement,
    setFilters,
    setIsConfigureModalOpen,
    setActiveTab,
    refreshTrades,
  } = useMTAnalyzerStore();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<MTStatementTrade | null>(null);

  // Extract unique symbols and magic numbers for filter dropdowns
  const availableSymbols = useMemo(() => {
    const syms = Array.from(new Set(trades.map((t) => t.item)));
    return ['ALL', ...syms];
  }, [trades]);

  const availableMagics = useMemo(() => {
    const magics = Array.from(new Set(trades.map((t) => String(t.magicNumber || '')))).filter(Boolean);
    return ['ALL', ...magics];
  }, [trades]);

  // Handle file drop or selection
  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      if (content) {
        importHtmlStatement(content, file.name);
      }
    };
    reader.readAsText(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  // Generate monthly returns heatmap matrix (Year x Month)
  const monthlyHeatmap = useMemo(() => {
    const matrix: Record<number, Record<number, number>> = {};
    filteredTrades.forEach((t) => {
      const d = new Date(t.closeTime || t.openTime);
      const year = d.getFullYear();
      const month = d.getMonth(); // 0-11
      if (!matrix[year]) matrix[year] = {};
      matrix[year][month] = (matrix[year][month] || 0) + t.profit;
    });
    return matrix;
  }, [filteredTrades]);

  // Equity curve data points
  const equityPoints = useMemo(() => {
    let currentBalance = metrics.initialDeposit;
    let peak = currentBalance;
    return filteredTrades.map((t, idx) => {
      currentBalance += t.profit;
      if (currentBalance > peak) peak = currentBalance;
      const dd = ((peak - currentBalance) / peak) * 100;
      return {
        idx: idx + 1,
        date: t.closeTime.split(' ')[0],
        balance: currentBalance,
        drawdown: dd,
        profit: t.profit,
      };
    });
  }, [filteredTrades, metrics.initialDeposit]);

  // Hour-of-day distribution
  const hourDistribution = useMemo(() => {
    const hours = Array(24).fill(0);
    filteredTrades.forEach((t) => {
      const hour = parseInt(t.openTime.split(' ')[1]?.split(':')[0] || '0', 10);
      if (hour >= 0 && hour < 24) {
        hours[hour]++;
      }
    });
    return hours;
  }, [filteredTrades]);

  const maxHourTrades = Math.max(...hourDistribution, 1);

  return (
    <div
      className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden"
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept=".htm,.html,.csv"
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
          }
        }}
      />

      {/* Drag & Drop Overlay */}
      {dragOver && (
        <div className="absolute inset-0 z-50 bg-indigo-950/80 backdrop-blur-sm border-2 border-dashed border-indigo-400 flex flex-col items-center justify-center p-8">
          <Upload className="w-16 h-16 text-indigo-400 animate-bounce mb-4" />
          <h2 className="text-2xl font-bold text-white">Drop MetaTrader Statement Here</h2>
          <p className="text-slate-300 text-sm mt-2">Supports standard MT4 / MT5 HTML and CSV reports</p>
        </div>
      )}

      {/* Top Header Bar matching SQX QuantAnalyzer header */}
      <div className="h-16 px-6 bg-slate-900 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-indigo-600 to-sky-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">QuantAnalyzer for MetaTrader</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                MT4 / MT5
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {statementFileName ? (
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Loaded: <strong className="text-slate-200">{statementFileName}</strong> ({filteredTrades.length} trades)
                </span>
              ) : (
                'Load a statement to analyze performance, drawdown, and statistical edge'
              )}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {/* Quick Presets */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 px-2 py-1 rounded-md border border-slate-700">
            <span className="text-xs text-slate-400">Preset:</span>
            <select
              value={selectedPreset}
              onChange={(e) => loadPreset(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="scalper" className="bg-slate-800">EURUSD H1 Scalper</option>
              <option value="trend" className="bg-slate-800">GBPUSD Daily Trend</option>
              <option value="breakout" className="bg-slate-800">USATECH Breakout</option>
              {selectedPreset === 'custom' && <option value="custom" className="bg-slate-800">Imported Statement</option>}
            </select>
          </div>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-750 text-slate-200 hover:text-white border border-slate-700 text-xs font-medium transition"
          >
            <Upload className="w-3.5 h-3.5" />
            Import Statement
          </button>

          <button
            onClick={refreshTrades}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-750 text-slate-200 hover:text-white border border-slate-700 text-xs font-medium transition"
            title="Refresh trades and recalculate statistics"
          >
            <RotateCw className="w-3.5 h-3.5" />
            Refresh
          </button>

          <button
            onClick={() => setIsConfigureModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-sm transition"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Configure
          </button>
        </div>
      </div>

      {/* Filter / Breakdown Sub-Header */}
      <div className="h-10 px-6 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span>Symbol:</span>
            <select
              value={filters.symbol}
              onChange={(e) => setFilters({ symbol: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-0.5 text-slate-200 focus:outline-none"
            >
              {availableSymbols.map((sym) => (
                <option key={sym} value={sym}>{sym}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span>Magic Number:</span>
            <select
              value={filters.magicNumber}
              onChange={(e) => setFilters({ magicNumber: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-0.5 text-slate-200 focus:outline-none"
            >
              {availableMagics.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span>Filter Comment:</span>
            <input
              type="text"
              placeholder="Search comments..."
              value={filters.comment}
              onChange={(e) => setFilters({ comment: e.target.value })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-0.5 text-slate-200 focus:outline-none w-36 placeholder:text-slate-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-4 text-[11px]">
          <span>Initial Deposit: <strong className="text-slate-200">${metrics.initialDeposit.toLocaleString()}</strong></span>
          <span>Filtered Trades: <strong className="text-indigo-400">{filteredTrades.length}</strong> of {trades.length}</span>
        </div>
      </div>

      {/* Result Tabs Navigation matching SQX: overview, equityChart, tradeAnalysis, tradeList */}
      <div className="flex items-center gap-2 px-6 border-b border-slate-800 bg-slate-900/40 text-xs font-medium shrink-0">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 py-2.5 px-4 border-b-2 transition ${
            activeTab === 'overview'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Overview & Metrics
        </button>

        <button
          onClick={() => setActiveTab('equityChart')}
          className={`flex items-center gap-2 py-2.5 px-4 border-b-2 transition ${
            activeTab === 'equityChart'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          Equity & Drawdown Chart
        </button>

        <button
          onClick={() => setActiveTab('tradeAnalysis')}
          className={`flex items-center gap-2 py-2.5 px-4 border-b-2 transition ${
            activeTab === 'tradeAnalysis'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          Trade & Time Analysis
        </button>

        <button
          onClick={() => setActiveTab('tradeList')}
          className={`flex items-center gap-2 py-2.5 px-4 border-b-2 transition ${
            activeTab === 'tradeList'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ListFilter className="w-3.5 h-3.5" />
          Trades Journal ({filteredTrades.length})
        </button>
      </div>

      {/* Main Tab Content Body */}
      <div className="flex-1 p-6 overflow-y-auto min-h-0">
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* KPI Metric Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Total Net Profit</span>
                <div className={`text-xl font-bold mt-1 ${metrics.totalNetProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  ${metrics.totalNetProfit >= 0 ? '+' : ''}{metrics.totalNetProfit.toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Gross: +${metrics.grossProfit} / -${metrics.grossLoss}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Profit Factor</span>
                <div className="text-xl font-bold mt-1 text-sky-400">
                  {metrics.profitFactor}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Payoff: ${metrics.expectedPayoff} / trade
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Max Drawdown</span>
                <div className="text-xl font-bold mt-1 text-rose-400">
                  ${metrics.maximalDrawdown.toLocaleString()} ({metrics.maximalDrawdownPercent}%)
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Absolute DD: ${metrics.absoluteDrawdown}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Win Rate</span>
                <div className="text-xl font-bold mt-1 text-emerald-400">
                  {metrics.winRate}%
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {metrics.profitTrades} wins / {metrics.lossTrades} losses
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">SQN (System Quality)</span>
                <div className={`text-xl font-bold mt-1 ${metrics.sqn >= 2.5 ? 'text-emerald-400' : metrics.sqn >= 1.5 ? 'text-amber-400' : 'text-slate-300'}`}>
                  {metrics.sqn}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {metrics.sqn >= 3.0 ? 'Superb' : metrics.sqn >= 2.0 ? 'Good Edge' : 'Average'}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Sharpe Ratio</span>
                <div className="text-xl font-bold mt-1 text-indigo-400">
                  {metrics.sharpeRatio}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Total Trades: {metrics.totalTrades}
                </div>
              </div>
            </div>

            {/* Performance Ratios Table & Monthly Returns Heatmap */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Detailed Performance Statistics Panel */}
              <div className="lg:col-span-1 rounded-xl bg-slate-900 border border-slate-800 p-5 space-y-4">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-400" />
                  Trade Breakdown & Ratios
                </h3>

                <div className="divide-y divide-slate-800 text-xs">
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Average Win Trade</span>
                    <span className="text-emerald-400 font-medium">+${metrics.averageProfit}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Average Loss Trade</span>
                    <span className="text-rose-400 font-medium">-${metrics.averageLoss}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Win / Loss Ratio (Avg P/L)</span>
                    <span className="text-slate-200 font-medium">{metrics.profitRatio}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Max Consecutive Wins</span>
                    <span className="text-emerald-400 font-medium">{metrics.maxConsecutiveWins}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Max Consecutive Losses</span>
                    <span className="text-rose-400 font-medium">{metrics.maxConsecutiveLosses}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Return on Account</span>
                    <span className={`font-medium ${metrics.totalNetProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {((metrics.totalNetProfit / metrics.initialDeposit) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Monthly Returns Matrix Heatmap */}
              <div className="lg:col-span-2 rounded-xl bg-slate-900 border border-slate-800 p-5 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
                    <Calendar className="w-4 h-4 text-indigo-400" />
                    Monthly Returns Breakdown ($ Net)
                  </h3>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-center border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase">
                          <th className="py-2 text-left px-2 font-medium">Year</th>
                          {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m) => (
                            <th key={m} className="py-2 px-1 font-medium">{m}</th>
                          ))}
                          <th className="py-2 px-2 text-right font-medium">Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {Object.keys(monthlyHeatmap).length === 0 ? (
                          <tr>
                            <td colSpan={14} className="py-6 text-slate-500 text-center">No trades found in dataset</td>
                          </tr>
                        ) : (
                          Object.entries(monthlyHeatmap).map(([year, months]) => {
                            const yearTotal = Object.values(months).reduce((a, b) => a + b, 0);
                            return (
                              <tr key={year} className="hover:bg-slate-800/40">
                                <td className="py-2 px-2 text-left font-semibold text-slate-300">{year}</td>
                                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((mIdx) => {
                                  const val = months[mIdx];
                                  if (val === undefined) {
                                    return <td key={mIdx} className="py-2 px-1 text-slate-600">-</td>;
                                  }
                                  const isPos = val >= 0;
                                  const bg = isPos
                                    ? val > 500 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-emerald-500/10 text-emerald-400'
                                    : val < -500 ? 'bg-rose-500/20 text-rose-300' : 'bg-rose-500/10 text-rose-400';
                                  return (
                                    <td key={mIdx} className="py-2 px-1">
                                      <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-mono ${bg}`}>
                                        ${Math.round(val)}
                                      </span>
                                    </td>
                                  );
                                })}
                                <td className="py-2 px-2 text-right font-bold">
                                  <span className={yearTotal >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                    ${Math.round(yearTotal).toLocaleString()}
                                  </span>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-800/80 pt-3 mt-4">
                  <span>* Values reflect closed trade net profit including broker swap & commission</span>
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-emerald-500/30 border border-emerald-500/60" /> Positive</span>
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-rose-500/30 border border-rose-500/60" /> Negative</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: EQUITY & DRAWDOWN CHART */}
        {activeTab === 'equityChart' && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Equity Curve SVG */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Cumulative Account Equity Curve ($)
                </h3>
                <span className="text-xs text-slate-400">Initial: ${metrics.initialDeposit} → Peak: ${(metrics.initialDeposit + metrics.totalNetProfit).toFixed(2)}</span>
              </div>

              <div className="h-64 w-full relative flex items-end">
                {equityPoints.length > 1 ? (
                  <svg className="w-full h-full overflow-visible" viewBox="0 0 800 200" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Grid lines */}
                    <line x1="0" y1="50" x2="800" y2="50" stroke="#334155" strokeDasharray="3,3" />
                    <line x1="0" y1="100" x2="800" y2="100" stroke="#334155" strokeDasharray="3,3" />
                    <line x1="0" y1="150" x2="800" y2="150" stroke="#334155" strokeDasharray="3,3" />

                    {(() => {
                      const minBal = Math.min(metrics.initialDeposit, ...equityPoints.map((p) => p.balance));
                      const maxBal = Math.max(metrics.initialDeposit, ...equityPoints.map((p) => p.balance)) * 1.05;
                      const range = maxBal - minBal || 1;

                      const points = equityPoints
                        .map((p, i) => {
                          const x = (i / (equityPoints.length - 1)) * 800;
                          const y = 200 - ((p.balance - minBal) / range) * 190 - 5;
                          return `${x},${y}`;
                        })
                        .join(' ');

                      const firstX = 0;
                      const lastX = 800;
                      const areaPoints = `${firstX},200 ${points} ${lastX},200`;

                      return (
                        <>
                          <polygon points={areaPoints} fill="url(#eqGrad)" />
                          <polyline points={points} fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </>
                      );
                    })()}
                  </svg>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
                    Not enough trades to plot equity curve
                  </div>
                )}
              </div>
            </div>

            {/* Drawdown Underwater SVG */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  Underwater Drawdown (%)
                </h3>
                <span className="text-xs text-rose-400">Max DD: -{metrics.maximalDrawdownPercent}%</span>
              </div>

              <div className="h-44 w-full relative flex items-end">
                {equityPoints.length > 1 ? (
                  <svg className="w-full h-full overflow-visible" viewBox="0 0 800 120" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.0" />
                        <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.4" />
                      </linearGradient>
                    </defs>

                    {/* Grid lines */}
                    <line x1="0" y1="30" x2="800" y2="30" stroke="#334155" strokeDasharray="3,3" />
                    <line x1="0" y1="60" x2="800" y2="60" stroke="#334155" strokeDasharray="3,3" />
                    <line x1="0" y1="90" x2="800" y2="90" stroke="#334155" strokeDasharray="3,3" />

                    {(() => {
                      const maxDD = Math.max(...equityPoints.map((p) => p.drawdown), 1);
                      const points = equityPoints
                        .map((p, i) => {
                          const x = (i / (equityPoints.length - 1)) * 800;
                          const y = (p.drawdown / maxDD) * 110 + 5;
                          return `${x},${y}`;
                        })
                        .join(' ');

                      const firstX = 0;
                      const lastX = 800;
                      const areaPoints = `${firstX},0 ${points} ${lastX},0`;

                      return (
                        <>
                          <polygon points={areaPoints} fill="url(#ddGrad)" />
                          <polyline points={points} fill="none" stroke="#f43f5e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </>
                      );
                    })()}
                  </svg>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
                    No drawdown data
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: TRADE & TIME ANALYSIS */}
        {activeTab === 'tradeAnalysis' && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Hour-of-day Entry Distribution */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-4">
                <Clock className="w-4 h-4 text-indigo-400" />
                Trades by Hour of Day (UTC)
              </h3>

              <div className="h-48 flex items-end gap-1 pt-6 px-2">
                {hourDistribution.map((count, hour) => {
                  const heightPct = (count / maxHourTrades) * 100;
                  return (
                    <div key={hour} className="flex-1 flex flex-col items-center group relative">
                      {/* Tooltip */}
                      <div className="absolute -top-7 opacity-0 group-hover:opacity-100 bg-slate-800 text-[10px] text-slate-200 px-1.5 py-0.5 rounded border border-slate-700 transition pointer-events-none z-10">
                        {count} trades
                      </div>
                      <div
                        style={{ height: `${Math.max(heightPct, 4)}%` }}
                        className={`w-full rounded-t transition ${count > 0 ? 'bg-indigo-500 hover:bg-indigo-400' : 'bg-slate-800'}`}
                      />
                      <span className="text-[10px] text-slate-500 mt-1 font-mono">{hour}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Long vs Short Performance Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {(() => {
                const longs = filteredTrades.filter((t) => t.type === 'buy');
                const shorts = filteredTrades.filter((t) => t.type === 'sell');

                const longProfit = longs.reduce((acc, t) => acc + t.profit, 0);
                const shortProfit = shorts.reduce((acc, t) => acc + t.profit, 0);

                const longWins = longs.filter((t) => t.profit > 0).length;
                const shortWins = shorts.filter((t) => t.profit > 0).length;

                return (
                  <>
                    <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                          <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                          Long Trades (Buy)
                        </span>
                        <span className="text-xs text-slate-400 font-mono">{longs.length} trades</span>
                      </div>
                      <div className="text-2xl font-bold text-emerald-400 font-mono">
                        ${longProfit.toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-400 flex justify-between border-t border-slate-800 pt-2">
                        <span>Win Rate:</span>
                        <span className="text-slate-200 font-medium">
                          {longs.length > 0 ? ((longWins / longs.length) * 100).toFixed(1) : 0}% ({longWins} / {longs.length})
                        </span>
                      </div>
                    </div>

                    <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                          <ArrowDownRight className="w-4 h-4 text-rose-400" />
                          Short Trades (Sell)
                        </span>
                        <span className="text-xs text-slate-400 font-mono">{shorts.length} trades</span>
                      </div>
                      <div className="text-2xl font-bold text-rose-400 font-mono">
                        ${shortProfit.toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-400 flex justify-between border-t border-slate-800 pt-2">
                        <span>Win Rate:</span>
                        <span className="text-slate-200 font-medium">
                          {shorts.length > 0 ? ((shortWins / shorts.length) * 100).toFixed(1) : 0}% ({shortWins} / {shorts.length})
                        </span>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        )}

        {/* TAB 4: TRADES JOURNAL */}
        {activeTab === 'tradeList' && (
          <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden flex flex-col max-w-7xl mx-auto">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
              <h3 className="text-sm font-semibold text-slate-200">
                Closed Trades ({filteredTrades.length})
              </h3>
              <span className="text-xs text-slate-400">Click any row to inspect execution details</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Ticket</th>
                    <th className="py-2.5 px-3">Open Time</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Size</th>
                    <th className="py-2.5 px-3">Item</th>
                    <th className="py-2.5 px-3">Open Price</th>
                    <th className="py-2.5 px-3">Close Time</th>
                    <th className="py-2.5 px-3">Close Price</th>
                    <th className="py-2.5 px-3 text-right">Pips</th>
                    <th className="py-2.5 px-3 text-right">Commission</th>
                    <th className="py-2.5 px-3 text-right">Swap</th>
                    <th className="py-2.5 px-3 text-right font-bold">Profit ($)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredTrades.map((t) => (
                    <tr
                      key={t.ticket}
                      onClick={() => setSelectedTrade(t)}
                      className={`hover:bg-slate-800/50 cursor-pointer transition ${
                        selectedTrade?.ticket === t.ticket ? 'bg-indigo-950/40' : ''
                      }`}
                    >
                      <td className="py-2 px-3 text-slate-400">#{t.ticket}</td>
                      <td className="py-2 px-3 text-slate-300 whitespace-nowrap">{t.openTime}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                            t.type === 'buy'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {t.type}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-300">{t.size}</td>
                      <td className="py-2 px-3 text-indigo-300 font-semibold">{t.item}</td>
                      <td className="py-2 px-3 text-slate-300">{t.openPrice}</td>
                      <td className="py-2 px-3 text-slate-300 whitespace-nowrap">{t.closeTime}</td>
                      <td className="py-2 px-3 text-slate-300">{t.closePrice}</td>
                      <td className={`py-2 px-3 text-right ${t.pips >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {t.pips >= 0 ? '+' : ''}{t.pips}
                      </td>
                      <td className="py-2 px-3 text-right text-slate-400">${t.commission}</td>
                      <td className="py-2 px-3 text-right text-slate-400">${t.swap}</td>
                      <td className={`py-2 px-3 text-right font-bold ${t.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        ${t.profit >= 0 ? '+' : ''}{t.profit}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* CONFIGURE MODAL (matching SQX configure.html) */}
      {isConfigureModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
                Configure Trade Organization
              </h3>
              <button
                onClick={() => setIsConfigureModalOpen(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <fieldset className="border border-slate-800 rounded-lg p-4 space-y-3">
              <legend className="text-xs font-semibold text-indigo-400 px-2">
                Organize trades into sub-results
              </legend>

              <label className="flex items-center gap-3 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.symbol !== 'ALL'}
                  onChange={(e) => setFilters({ symbol: e.target.checked ? (availableSymbols[1] || 'EURUSD') : 'ALL' })}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                />
                Filter / Group by Symbol ({filters.symbol})
              </label>

              <label className="flex items-center gap-3 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.magicNumber !== 'ALL'}
                  onChange={(e) => setFilters({ magicNumber: e.target.checked ? (availableMagics[1] || '10101') : 'ALL' })}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                />
                Filter / Group by Magic Numbers ({filters.magicNumber})
              </label>
            </fieldset>

            <fieldset className="border border-slate-800 rounded-lg p-4 space-y-3">
              <legend className="text-xs font-semibold text-indigo-400 px-2">
                Equity Chart Calculation
              </legend>

              <label className="flex items-center gap-3 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.excludeBalanceOrders}
                  onChange={(e) => setFilters({ excludeBalanceOrders: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                />
                Filter out balance & deposit orders
              </label>
            </fieldset>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setIsConfigureModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs font-medium transition"
              >
                Close
              </button>
              <button
                onClick={() => {
                  refreshTrades();
                  setIsConfigureModalOpen(false);
                }}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md transition"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
