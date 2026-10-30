import { useEffect, useMemo, useRef, useState } from 'react';
import { createCodeEditorClient, type IndicatorTestResultDto } from './codeEditorClient';

export function useIndicatorTest(indicatorName: string) {
  const client = useMemo(() => createCodeEditorClient(), []);

  // Navigation & View
  const [activeTab, setActiveTab] = useState<'chart' | 'results' | 'data'>('chart');
  const [bottomTab, setBottomTab] = useState<'results' | 'data' | 'summary' | 'logs'>('results');

  // Parameters
  const [symbol, setSymbol] = useState<string>('EURUSD');
  const [timeframe, setTimeframe] = useState<string>('H1');
  const skipDefaults = useRef(false);
  const requestNumber = useRef(0);
  const [parametersReady, setParametersReady] = useState(false);
  const [testWindow, setTestWindow] = useState({ reserve: 50, count: 150 });
  const [error, setError] = useState<string | null>(null);
  const [parameters, setParameters] = useState<Record<string, unknown>>({});
  const [defaults, setDefaults] = useState<Record<string, unknown>>({});
  const [selectedIndicator, setSelectedIndicator] = useState<string>(indicatorName || 'MovingAverage');

  // Results & Execution state
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<IndicatorTestResultDto | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [logs, setLogs] = useState<string[]>([]);

  const runTest = async (inputs = parameters) => {
    const request = ++requestNumber.current;
    setError(null);
    setIsRunning(true);
    const startMs = performance.now();
    try {
      const res = await client.runIndicatorTest({
        indicatorName: selectedIndicator,
        symbol,
        timeframe,
        params: inputs,
        barsToReserve: testWindow.reserve,
        barCount: testWindow.count,
      });
      if (request !== requestNumber.current) return;
      setTestResult(res);
      if (res.status === 'failed') throw new Error(res.error ?? 'Indicator calculation failed');
      setCurrentPage(1);
      const elapsed = ((performance.now() - startMs) / 1000).toFixed(3);
      setLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Executed test for ${selectedIndicator} on ${symbol} (${timeframe}): ${res.bars_calculated} bars calculated in ${elapsed}s. Discrepancies: ${res.discrepancies.length}`,
        ...prev,
      ]);
    } catch (err: unknown) {
      if (request !== requestNumber.current) return;
      const msg = err instanceof Error ? err.message : 'Execution error';
      setError(msg);
      setLogs((prev) => [`[${new Date().toLocaleTimeString()}] Error: ${msg}`, ...prev]);
    } finally {
      if (request === requestNumber.current) setIsRunning(false);
    }
  };

  useEffect(() => {
    if (skipDefaults.current) {
      skipDefaults.current = false;
      return;
    }
    let cancelled = false;
    setParametersReady(false);
    client
      .newIndicatorTest(selectedIndicator, symbol, timeframe)
      .then((config) => {
        if (cancelled) return;
        const inputs = config.params as Record<string, unknown>;
        setDefaults(inputs);
        setParameters(inputs);
        setParametersReady(true);
      })
      .catch((error) => {
        setError(String(error));
        setLogs((prev) => [String(error), ...prev]);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedIndicator]);

  useEffect(() => {
    if (!parametersReady) return;
    const timer = window.setTimeout(() => {
      void runTest();
    }, 250);
    return () => window.clearTimeout(timer);
  }, [parameters, symbol, timeframe, testWindow, parametersReady]);

  // Derived dataset from testResult or default fallback
  const candlesticks = testResult?.candlesticks || [];
  const indicatorPlots = testResult?.indicator_plots || [];
  const tableRows = testResult?.table_rows || [];

  // Metrics calculation
  const values = indicatorPlots.flatMap((p) => (p.value === undefined ? [] : [p.value]));
  const meanVal = values.length ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2) : '0.00';
  const minVal = values.length ? Math.min(...values).toFixed(2) : '0.00';
  const maxVal = values.length ? Math.max(...values).toFixed(2) : '0.00';
  const signalsCount = values.filter((v, i) => i > 0 && v > values[i - 1]).length;

  const dateRange = candlesticks.length
    ? `${new Date(candlesticks[0].time * 1000).toISOString().slice(0, 10)} to ${new Date(candlesticks[candlesticks.length - 1].time * 1000).toISOString().slice(0, 10)}`
    : 'No historical bars loaded';

  // Pagination for rows
  const totalPages = Math.ceil(tableRows.length / rowsPerPage) || 1;
  const paginatedRows = tableRows.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

  return {
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
  };
}
