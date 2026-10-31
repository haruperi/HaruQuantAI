import React, { useState } from 'react';
import {
  Activity,
  ArrowDown,
  ArrowUp,
  BarChart2,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  Play,
  Sliders,
  Square,
  Target,
  X,
  Zap,
} from 'lucide-react';
import { useIndicatorTest } from './useIndicatorTest';
import { IndicatorChart } from './IndicatorChart';
import { IndicatorTestPresentation } from './indicator_test_presentation';
import type {
  CalibrationResultDto,
  SuiteIndicatorOptionDto,
  SuiteSnapshotDto,
  SuiteTestCaseDto,
  TestDistributionSnapshotDto,
} from './codeEditorClient';

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

  const [studioMode, setStudioMode] = useState<'single' | 'suite' | 'calibration'>('single');

  // Batch Suite State
  const [suiteOptions, setSuiteOptions] = useState<SuiteIndicatorOptionDto[]>([]);
  const [suiteSnapshot, setSuiteSnapshot] = useState<SuiteSnapshotDto | null>(null);
  const [suiteCandidate, setSuiteCandidate] = useState<string>('ATR');
  const [suiteEngine, setSuiteEngine] = useState<string>('MetaTrader4');
  const [suiteReserveBars, setSuiteReserveBars] = useState<number>(300);
  const [suiteError, setSuiteError] = useState<string | null>(null);
  const [selectedSuiteTestId, setSelectedSuiteTestId] = useState<string | null>(null);
  const [bundlePath, setBundlePath] = useState<string>('');
  const [bundleSha256, setBundleSha256] = useState<string>('');
  const [distributionStatus, setDistributionStatus] = useState<TestDistributionSnapshotDto | null>(null);

  // Calibration State
  const [calProject, setCalProject] = useState<string>('Default');
  const [calSymbols, setCalSymbols] = useState<string>('EURUSD');
  const [calTimeframes, setCalTimeframes] = useState<string>('H1');
  const [calEngine, setCalEngine] = useState<string>('MetaTrader4');
  const [calMaxSteps, setCalMaxSteps] = useState<number>(-1);
  const [calIndicators, setCalIndicators] = useState<string>(indicatorName || 'ATR');
  const [calRangesText, setCalRangesText] = useState<string>('');
  const [calResult, setCalResult] = useState<CalibrationResultDto | null>(null);
  const [calError, setCalError] = useState<string | null>(null);
  const [isCalibrating, setIsCalibrating] = useState<boolean>(false);

  const openSuiteMode = async () => {
    setStudioMode('suite');
    setSuiteError(null);
    try {
      const [opts, snap] = await Promise.all([
        client.suiteIndicators(),
        client.suiteGetConfig(),
      ]);
      setSuiteOptions(opts);
      if (opts.length > 0 && !suiteCandidate) {
        setSuiteCandidate(opts[0].indicator);
      }
      setSuiteSnapshot(snap);
      setSuiteEngine(snap.config.engine);
      setSuiteReserveBars(snap.config.bars_to_reserve);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleCreateSuiteConfig = async () => {
    setSuiteError(null);
    try {
      const snap = await client.suiteCreateConfig(
        suiteCandidate ? [suiteCandidate] : [],
        suiteEngine,
        suiteReserveBars
      );
      setSuiteSnapshot(snap);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleAddSuiteTest = async () => {
    if (!suiteCandidate) return;
    setSuiteError(null);
    try {
      const snap = await client.suiteAddTests([suiteCandidate], false);
      setSuiteSnapshot(snap);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleToggleSuiteRow = async (row: SuiteTestCaseDto) => {
    if (!suiteSnapshot) return;
    const nextTests = suiteSnapshot.config.tests.map((item) =>
      item.test_id === row.test_id ? { ...item, use: !item.use } : item
    );
    const updatedConfig = { ...suiteSnapshot.config, tests: nextTests };
    try {
      const snap = await client.suiteSaveConfig({ config: updatedConfig });
      setSuiteSnapshot(snap);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleEditSuiteRowSignature = async (row: SuiteTestCaseDto, formattedLabel: string) => {
    if (!suiteSnapshot) return;
    const parsedParams = IndicatorTestPresentation.raw_parameters(formattedLabel);
    const parsedShift = IndicatorTestPresentation.shift_text(formattedLabel);
    const nextTests = suiteSnapshot.config.tests.map((item) =>
      item.test_id === row.test_id
        ? {
            ...item,
            parameters: parsedParams !== null ? parsedParams : item.parameters,
            shift: parsedShift !== null && !Number.isNaN(Number(parsedShift)) ? Number(parsedShift) : item.shift,
          }
        : item
    );
    try {
      const snap = await client.suiteSaveConfig({
        config: { ...suiteSnapshot.config, tests: nextTests },
      });
      setSuiteSnapshot(snap);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleStartSuite = async () => {
    setSuiteError(null);
    try {
      const started = await client.suiteStart({
        config: suiteSnapshot?.config,
        selected_only: true,
      });
      setSuiteSnapshot(started);
      const latest = await client.suiteStatus(started.job_id);
      setSuiteSnapshot(latest);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleStopSuite = async () => {
    setSuiteError(null);
    try {
      const stopped = await client.suiteStop(
        suiteSnapshot?.job_id !== 'idle' ? suiteSnapshot?.job_id : undefined
      );
      setSuiteSnapshot(stopped);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDownloadTests = async () => {
    setSuiteError(null);
    try {
      const snap = await client.downloadTests({
        archive_path: bundlePath.trim() || undefined,
        expected_sha256: bundleSha256.trim(),
      });
      setDistributionStatus(snap);
      const refreshed = await client.suiteGetConfig();
      setSuiteSnapshot(refreshed);
    } catch (err: unknown) {
      setSuiteError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleRunCalibration = async () => {
    setCalError(null);
    setIsCalibrating(true);
    try {
      const res = await client.calibrateIndicators({
        project_name: calProject,
        symbols: calSymbols.split(',').map((s) => s.trim()).filter(Boolean),
        timeframes: calTimeframes.split(',').map((t) => t.trim()).filter(Boolean),
        engine: calEngine,
        max_steps: calMaxSteps,
        indicators: calIndicators.split(',').map((i) => i.trim()).filter(Boolean),
        ranges_config_text: calRangesText || null,
      });
      setCalResult(res);
    } catch (err: unknown) {
      setCalError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsCalibrating(false);
    }
  };

  const selectedSuiteRow = suiteSnapshot?.config.tests.find(
    (t) => t.test_id === selectedSuiteTestId
  ) ?? suiteSnapshot?.config.tests[0] ?? null;

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
                onClick={() => {
                  setStudioMode('single');
                  setActiveTab('chart');
                }}
                className={`px-3 py-1 rounded-md transition-colors ${
                  studioMode === 'single' && activeTab === 'chart'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Chart & Visuals
              </button>
              <button
                onClick={() => {
                  setStudioMode('single');
                  setActiveTab('results');
                }}
                className={`px-3 py-1 rounded-md transition-colors ${
                  studioMode === 'single' && activeTab === 'results'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Results & Metrics
              </button>
              <button
                onClick={() => {
                  setStudioMode('single');
                  setActiveTab('data');
                }}
                className={`px-3 py-1 rounded-md transition-colors ${
                  studioMode === 'single' && activeTab === 'data'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Data Table
              </button>
              <button
                onClick={() => {
                  void openSuiteMode();
                }}
                className={`px-3 py-1 rounded-md transition-colors ${
                  studioMode === 'suite'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Batch Suite
              </button>
              <button
                onClick={() => setStudioMode('calibration')}
                className={`px-3 py-1 rounded-md transition-colors ${
                  studioMode === 'calibration'
                    ? 'bg-blue-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Calibration
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
        {studioMode === 'single' && (
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
                      const definition = await client.newIndicatorTest(
                        String(config.indicator_name),
                        String(config.symbol),
                        String(config.timeframe)
                      );
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
                                  {row.diff != null ? `${row.diff.toFixed(5)}` : '—'}
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
        )}

        {studioMode === 'suite' && (
          <div className="flex-1 flex overflow-hidden">
            <div className="w-[340px] border-r border-slate-800 bg-slate-950/50 p-5 flex flex-col justify-between overflow-y-auto space-y-4">
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                  Batch Suite Configuration
                </h3>

                <div>
                  <label htmlFor="suite-engine" className="block text-xs font-medium text-slate-300 mb-1">
                    Reference Engine
                  </label>
                  <select
                    id="suite-engine"
                    value={suiteEngine}
                    onChange={(e) => setSuiteEngine(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                  >
                    <option value="MetaTrader4">MetaTrader4</option>
                    <option value="MetaTrader5">MetaTrader5</option>
                    <option value="TradeStation">TradeStation</option>
                    <option value="MultiCharts">MultiCharts</option>
                    <option value="JForex">JForex</option>
                    <option value="HaruQuantAI">HaruQuantAI</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="suite-reserve" className="block text-xs font-medium text-slate-300 mb-1">
                    Bars to Reserve (Suite)
                  </label>
                  <input
                    id="suite-reserve"
                    type="number"
                    value={suiteReserveBars}
                    onChange={(e) => setSuiteReserveBars(Number(e.target.value))}
                    className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 font-mono"
                  />
                </div>

                <div>
                  <label htmlFor="suite-indicator" className="block text-xs font-medium text-slate-300 mb-1">
                    Indicator / Output Buffer
                  </label>
                  <select
                    id="suite-indicator"
                    value={suiteCandidate}
                    onChange={(e) => setSuiteCandidate(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 font-mono"
                  >
                    {suiteOptions.length === 0 && <option value="ATR">ATR</option>}
                    {suiteOptions.map((opt) => (
                      <option key={opt.identity} value={opt.indicator}>
                        {opt.indicator} ({opt.default_parameters || 'default'})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => void handleAddSuiteTest()}
                    className="py-1.5 px-3 bg-blue-600 hover:bg-blue-500 rounded text-xs font-medium"
                  >
                    Add Test
                  </button>
                  <button
                    onClick={() => void handleCreateSuiteConfig()}
                    className="py-1.5 px-3 bg-slate-800 hover:bg-slate-700 rounded text-xs"
                  >
                    New Suite Config
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => void handleStartSuite()}
                    disabled={suiteSnapshot?.status === 'RUNNING'}
                    className="py-2 px-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-xs font-medium flex items-center justify-center gap-1"
                  >
                    <Play className="w-3.5 h-3.5" /> Start Suite
                  </button>
                  <button
                    onClick={() => void handleStopSuite()}
                    className="py-2 px-3 bg-rose-600/80 hover:bg-rose-600 rounded text-xs font-medium flex items-center justify-center gap-1"
                  >
                    <Square className="w-3.5 h-3.5" /> Stop Suite
                  </button>
                </div>

                <div className="pt-3 border-t border-slate-800 space-y-2">
                  <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Download className="w-3.5 h-3.5 text-blue-400" /> Verified Test Bundle
                  </h4>
                  <input
                    type="text"
                    placeholder="Bundle archive path (.zip)"
                    aria-label="Test bundle archive path"
                    value={bundlePath}
                    onChange={(e) => setBundlePath(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                  <input
                    type="text"
                    placeholder="Expected SHA-256 digest (64 hex)"
                    aria-label="Expected SHA-256 digest"
                    value={bundleSha256}
                    onChange={(e) => setBundleSha256(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                  <button
                    onClick={() => void handleDownloadTests()}
                    disabled={!bundleSha256.trim()}
                    className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded text-xs"
                  >
                    Install Verified Test Bundle
                  </button>
                  {distributionStatus && (
                    <div className="text-[11px] text-emerald-400 font-mono">
                      Bundle {distributionStatus.status}: {distributionStatus.installed_files.length} files installed
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/40 p-5 space-y-4">
              {suiteError && (
                <p role="alert" className="text-red-400 text-xs">
                  {suiteError}
                </p>
              )}

              <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-2.5 text-xs">
                <div className="flex items-center gap-4">
                  <span>
                    Status: <strong className="text-blue-400">{suiteSnapshot?.status ?? 'IDLE'}</strong>
                  </span>
                  <span className="text-emerald-400">Passed: {suiteSnapshot?.passed_tests ?? 0}</span>
                  <span className="text-rose-400">Failed: {suiteSnapshot?.failed_tests ?? 0}</span>
                  <span className="text-amber-400">Skipped: {suiteSnapshot?.skipped_tests ?? 0}</span>
                </div>
                <span className="font-mono text-slate-400">
                  Progress: {Math.round(suiteSnapshot?.progress ?? 0)}%
                </span>
              </div>

              <div className="flex-1 rounded-xl border border-slate-800 bg-slate-950 overflow-y-auto p-2">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                      <th className="py-1.5 px-2">Use</th>
                      <th className="py-1.5 px-2">Indicator</th>
                      <th className="py-1.5 px-2">Formatted Signature</th>
                      <th className="py-1.5 px-2">Decimals</th>
                      <th className="py-1.5 px-2">File</th>
                      <th className="py-1.5 px-2">Exists</th>
                      <th className="py-1.5 px-2">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {(suiteSnapshot?.config.tests ?? []).map((row) => {
                      const formattedSig = IndicatorTestPresentation.format_parameters(
                        row.indicator,
                        row.parameters,
                        row.shift
                      );
                      const rowClass = IndicatorTestPresentation.row_class(row.use, row.result);
                      return (
                        <tr
                          key={row.test_id}
                          data-row-class={rowClass}
                          onClick={() => setSelectedSuiteTestId(row.test_id)}
                          className={`cursor-pointer hover:bg-slate-900/60 ${
                            rowClass === 'passed'
                              ? 'text-emerald-300'
                              : rowClass === 'failed'
                                ? 'text-rose-300'
                                : rowClass === 'other'
                                  ? 'text-amber-300'
                                  : 'text-slate-200'
                          }`}
                        >
                          <td className="py-1.5 px-2">
                            <input
                              type="checkbox"
                              aria-label={`Select ${row.indicator}`}
                              checked={row.use}
                              onChange={() => void handleToggleSuiteRow(row)}
                            />
                          </td>
                          <td className="py-1.5 px-2 font-semibold">{row.indicator}</td>
                          <td
                            className="py-1.5 px-2"
                            onDoubleClick={() => {
                              const edited = prompt('Edit Indicator(params)[shift]:', formattedSig);
                              if (edited) void handleEditSuiteRowSignature(row, edited);
                            }}
                          >
                            {formattedSig}
                          </td>
                          <td className="py-1.5 px-2">{row.decimals}</td>
                          <td className="py-1.5 px-2">{row.file_name}</td>
                          <td className="py-1.5 px-2">{row.exists ? 'yes' : 'no'}</td>
                          <td className="py-1.5 px-2">{row.result || 'Pending'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {selectedSuiteRow && selectedSuiteRow.errors.length > 0 && (
                <div className="h-36 rounded-xl border border-slate-800 bg-slate-950 p-3 overflow-y-auto font-mono text-[11px] text-rose-300">
                  <div className="font-semibold text-slate-300 mb-1">
                    Discrepancies / Errors for {selectedSuiteRow.indicator} ({selectedSuiteRow.errors.length})
                  </div>
                  {selectedSuiteRow.errors.map((errLine, idx) => (
                    <div key={idx}>{errLine}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {studioMode === 'calibration' && (
          <div className="flex-1 flex overflow-hidden">
            <div className="w-[340px] border-r border-slate-800 bg-slate-950/50 p-5 flex flex-col justify-between overflow-y-auto space-y-4">
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-400" /> Indicator Calibration
                </h3>
                <div>
                  <label htmlFor="cal-project" className="block text-xs text-slate-300 mb-1">
                    Project Name
                  </label>
                  <input
                    id="cal-project"
                    type="text"
                    value={calProject}
                    onChange={(e) => setCalProject(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label htmlFor="cal-engine" className="block text-xs text-slate-300 mb-1">
                    Calibration Engine
                  </label>
                  <input
                    id="cal-engine"
                    type="text"
                    value={calEngine}
                    onChange={(e) => setCalEngine(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label htmlFor="cal-symbols" className="block text-xs text-slate-300 mb-1">
                    Symbols (comma-separated)
                  </label>
                  <input
                    id="cal-symbols"
                    type="text"
                    value={calSymbols}
                    onChange={(e) => setCalSymbols(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label htmlFor="cal-timeframes" className="block text-xs text-slate-300 mb-1">
                    Timeframes (comma-separated)
                  </label>
                  <input
                    id="cal-timeframes"
                    type="text"
                    value={calTimeframes}
                    onChange={(e) => setCalTimeframes(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label htmlFor="cal-indicators" className="block text-xs text-slate-300 mb-1">
                    Indicators (comma-separated)
                  </label>
                  <input
                    id="cal-indicators"
                    type="text"
                    value={calIndicators}
                    onChange={(e) => setCalIndicators(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label htmlFor="cal-max-steps" className="block text-xs text-slate-300 mb-1">
                    Max Steps (-1 for decade default)
                  </label>
                  <input
                    id="cal-max-steps"
                    type="number"
                    value={calMaxSteps}
                    onChange={(e) => setCalMaxSteps(Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label htmlFor="cal-ranges" className="block text-xs text-slate-300 mb-1">
                    CalibrationRanges Config
                  </label>
                  <textarea
                    id="cal-ranges"
                    rows={3}
                    value={calRangesText}
                    onChange={(e) => setCalRangesText(e.target.value)}
                    placeholder="RSI.period=10,14,20"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono"
                  />
                </div>
                <button
                  onClick={() => void handleRunCalibration()}
                  disabled={isCalibrating}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded text-xs font-medium"
                >
                  {isCalibrating ? 'Calibrating...' : 'Calibrate Indicators'}
                </button>
              </div>
            </div>

            <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/40 p-5 space-y-4">
              {calError && (
                <p role="alert" className="text-red-400 text-xs">
                  {calError}
                </p>
              )}
              <div className="flex-1 rounded-xl border border-slate-800 bg-slate-950 overflow-y-auto p-3">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                      <th className="py-1.5 px-2">Key</th>
                      <th className="py-1.5 px-2">Min Value</th>
                      <th className="py-1.5 px-2">Max Value</th>
                      <th className="py-1.5 px-2">Step</th>
                      <th className="py-1.5 px-2">Mean</th>
                      <th className="py-1.5 px-2">Std Dev</th>
                      <th className="py-1.5 px-2">Samples</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {(calResult?.ranges ?? []).map((entry) => (
                      <tr key={entry.key}>
                        <td className="py-1.5 px-2 font-semibold text-blue-400">{entry.key}</td>
                        <td className="py-1.5 px-2">{entry.min_value}</td>
                        <td className="py-1.5 px-2">{entry.max_value}</td>
                        <td className="py-1.5 px-2">{entry.step}</td>
                        <td className="py-1.5 px-2">{entry.mean}</td>
                        <td className="py-1.5 px-2">{entry.std_dev}</td>
                        <td className="py-1.5 px-2">{entry.samples}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
