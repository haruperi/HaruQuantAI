import React from 'react';
import {
  Activity,
  ArrowDown,
  ArrowUp,
  BarChart2,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Cpu,
  Download,
  Folder,
  Maximize2,
  Play,
  Radio,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  Table,
  Target,
  Trophy,
  X,
  Zap,
} from 'lucide-react';
import { useIndicatorTest } from './useIndicatorTest';

import { IndicatorChart } from './IndicatorChart';

interface IndicatorTesterModalProps {
  onClose: () => void;
  indicatorName: string;
}

export function IndicatorTesterModal({ onClose, indicatorName }: IndicatorTesterModalProps) {
  const {
    client,
    activeTab,
    setActiveTab,
    bottomTab,
    setBottomTab,
    symbol,
    setSymbol,
    timeframe,
    setTimeframe,
    skipDefaults,
    setParametersReady,
    setTestWindow,
    error,
    parameters,
    setParameters,
    defaults,
    setDefaults,
    selectedIndicator,
    setSelectedIndicator,
    isRunning,
    testResult,
    currentPage,
    setCurrentPage,
    rowsPerPage,
    logs,
    setLogs,
    runTest,
    candlesticks,
    tableRows,
    meanVal,
    minVal,
    maxVal,
    signalsCount,
    dateRange,
    totalPages,
    paginatedRows,
  } = useIndicatorTest(indicatorName);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-6xl h-[92vh] max-h-[920px] rounded-xl border border-slate-700/80 bg-slate-900 text-slate-100 shadow-2xl flex flex-col overflow-hidden">
        {/* Top Navbar */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3.5 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">Indicator Test Studio</h2>
              <p className="text-xs text-slate-400">Run and verify indicators against stored Data Manager history.</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setActiveTab('chart')}
                className={`px-3 py-1 rounded-md transition-colors ${
                  activeTab === 'chart'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Chart & Visuals
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`px-3 py-1 rounded-md transition-colors ${
                  activeTab === 'results'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Results & Metrics
              </button>
              <button
                onClick={() => setActiveTab('data')}
                className={`px-3 py-1 rounded-md transition-colors ${
                  activeTab === 'data'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Data Table
              </button>
            </div>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-200 hover:bg-slate-800 p-1.5 rounded-lg transition-colors ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body Split */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Controls Drawer */}
          <div className="w-[320px] border-r border-slate-800 bg-slate-950/50 p-5 flex flex-col justify-between overflow-y-auto space-y-4">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Symbol</label>
                <div className="relative">
                  <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                  />
                  <span className="absolute right-2.5 top-1.5 text-[10px] text-slate-400 uppercase">
                    Forex / Equity
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="M1">M1 (1 Min)</option>
                    <option value="M5">M5 (5 Min)</option>
                    <option value="M15">M15 (15 Min)</option>
                    <option value="H1">H1 (1 Hour)</option>
                    <option value="H4">H4 (4 Hours)</option>
                    <option value="D1">D1 (Daily)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Date Range</label>
                <div className="flex items-center gap-2 px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-300">
                  <Calendar className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  <span className="truncate">{dateRange}</span>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 p-3 space-y-3">
                <span className="text-xs font-semibold">Indicator Parameters</span>
                {Object.entries(parameters).map(([name, value]) => (
                  <label key={name} className="block text-xs text-slate-300">
                    {name}
                    <input
                      className="block w-full bg-slate-900 border border-slate-700 rounded p-1"
                      type={typeof value === 'number' ? 'number' : 'text'}
                      value={String(value ?? '')}
                      onChange={(event) =>
                        setParameters((prev) => ({
                          ...prev,
                          [name]: typeof value === 'number' ? Number(event.target.value) : event.target.value,
                        }))
                      }
                    />
                  </label>
                ))}
              </div>
              <button
                onClick={() => runTest()}
                disabled={isRunning}
                className="w-full py-2 bg-blue-600 rounded text-xs"
              >
                {isRunning ? 'Running...' : 'Run Test'}
              </button>
              <button
                onClick={() => {
                  setParameters(defaults);
                }}
                className="w-full py-2 bg-slate-800 rounded text-xs"
              >
                Reset Parameters
              </button>
              <button
                onClick={async () => {
                  const name = prompt('Save configuration as:');
                  if (!name || !testResult) return;
                  try {
                    const saved = await client.saveTestConfig(testResult.test_id, name);
                    setLogs((prev) => [`Saved configuration ID: ${saved.config_id}`, ...prev]);
                  } catch (error) {
                    setLogs((prev) => [String(error), ...prev]);
                  }
                }}
                disabled={!testResult || testResult.status !== 'success'}
                className="w-full py-2 bg-slate-800 rounded text-xs"
              >
                Save Test Configuration
              </button>
              <button
                onClick={async () => {
                  const id = prompt('Configuration ID:');
                  if (!id) return;
                  try {
                    const { config } = await client.loadTestConfig(id);
                    const definition = await client.newIndicatorTest(String(config.indicator_name), String(config.symbol), String(config.timeframe));
                    setDefaults(definition.params as Record<string, unknown>);
                    setSymbol(String(config.symbol));
                    setTimeframe(String(config.timeframe));
                    if (String(config.indicator_name) !== selectedIndicator) skipDefaults.current = true;
                    setSelectedIndicator(String(config.indicator_name));
                    setParameters(config.params as Record<string, unknown>);
                    setTestWindow({ reserve: Number(config.bars_to_reserve), count: Number(config.bar_count) });
                    setParametersReady(true);
                  } catch (error) {
                    setLogs((prev) => [String(error), ...prev]);
                  }
                }}
                className="w-full py-2 bg-slate-800 rounded text-xs"
              >
                Load Test Configuration
              </button>
            </div>
          </div>

          {/* Right Main Panel */}
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/40 p-5 space-y-4">
            {activeTab === 'chart' && (
              <>
                <IndicatorChart result={testResult} />
                {error && (
                  <p role="alert" className="text-red-400 text-xs">
                    {error}
                  </p>
                )}

                {/* Bottom Sub-Panels (Results / Data / Summary / Logs) */}
                <div className="flex-1 flex flex-col rounded-xl border border-slate-800 bg-slate-950 overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/80 text-xs">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setBottomTab('results')}
                        className={`px-2.5 py-1 rounded transition-colors ${
                          bottomTab === 'results'
                            ? 'bg-slate-800 text-blue-400 font-medium'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Results & Signals
                      </button>
                      <button
                        onClick={() => setBottomTab('data')}
                        className={`px-2.5 py-1 rounded transition-colors ${
                          bottomTab === 'data'
                            ? 'bg-slate-800 text-blue-400 font-medium'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Raw Bars
                      </button>
                      <button
                        onClick={() => setBottomTab('logs')}
                        className={`px-2.5 py-1 rounded transition-colors ${
                          bottomTab === 'logs'
                            ? 'bg-slate-800 text-blue-400 font-medium'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Execution Logs ({logs.length})
                      </button>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400 text-xs">
                      <span>
                        Showing {tableRows.length ? (currentPage - 1) * rowsPerPage + 1 : 0} -{' '}
                        {Math.min(currentPage * rowsPerPage, tableRows.length)} of {tableRows.length}
                      </span>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                          className="p-1 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
                        >
                          <ChevronLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className="font-mono text-slate-300">
                          {currentPage}/{totalPages}
                        </span>
                        <button
                          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                          className="p-1 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
                        >
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto p-2">
                    {bottomTab === 'results' && (
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                            <th className="py-1.5 px-3">#</th>
                            <th className="py-1.5 px-3">Time</th>
                            <th className="py-1.5 px-3">Close</th>
                            <th className="py-1.5 px-3">Indicator Val</th>
                            <th className="py-1.5 px-3">Diff / Ref</th>
                            <th className="py-1.5 px-3">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                          {paginatedRows.map((row, idx) => (
                            <tr key={idx} className="hover:bg-slate-900/60 transition-colors">
                              <td className="py-1.5 px-3 text-slate-500">
                                {(currentPage - 1) * rowsPerPage + idx + 1}
                              </td>
                              <td className="py-1.5 px-3 text-slate-400">
                                {new Date(row.time * 1000).toISOString().slice(11, 16)}
                              </td>
                              <td className="py-1.5 px-3 text-slate-200">{row.close.toFixed(5)}</td>
                              <td className="py-1.5 px-3 text-blue-400 font-semibold">
                                {row.indicator_val?.toFixed(5) ?? 'NaN'}
                              </td>
                              <td className="py-1.5 px-3 text-slate-400">
                                {row.diff !== undefined ? `${row.diff.toFixed(5)}` : '—'}
                              </td>
                              <td className="py-1.5 px-3">
                                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400">
                                  <CheckCircle2 className="w-3 h-3" /> Valid
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}

                    {bottomTab === 'logs' && (
                      <div className="p-2 space-y-1 font-mono text-xs text-slate-300">
                        {logs.map((log, i) => (
                          <div key={i} className="text-slate-400 leading-relaxed">
                            {log}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}

            {activeTab === 'results' && (
              <div className="flex-1 flex flex-col space-y-4 overflow-y-auto">
                {/* Metric Summary Cards */}
                <div className="grid grid-cols-6 gap-3">
                  <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70">
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Bars Processed</span>
                      <BarChart2 className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="text-lg font-bold text-slate-100 font-mono mt-1">{candlesticks.length}</div>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70">
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Mean Value</span>
                      <Activity className="w-4 h-4 text-purple-400" />
                    </div>
                    <div className="text-lg font-bold text-purple-300 font-mono mt-1">{meanVal}</div>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70">
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Min Value</span>
                      <ArrowDown className="w-4 h-4 text-rose-400" />
                    </div>
                    <div className="text-lg font-bold text-rose-300 font-mono mt-1">{minVal}</div>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70">
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Max Value</span>
                      <ArrowUp className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="text-lg font-bold text-emerald-300 font-mono mt-1">{maxVal}</div>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70">
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Signals</span>
                      <Zap className="w-4 h-4 text-amber-400" />
                    </div>
                    <div className="text-lg font-bold text-amber-300 font-mono mt-1">{signalsCount}</div>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70">
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>Discrepancies</span>
                      <Target className="w-4 h-4 text-teal-400" />
                    </div>
                    <div className="text-lg font-bold text-teal-300 font-mono mt-1">
                      {testResult?.discrepancies.length || 0}
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 p-4 text-xs text-slate-300">
                  Current parameters: {JSON.stringify(parameters)}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
