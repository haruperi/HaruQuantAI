import { useEffect, useState } from 'react';
import { Button, Modal, Select } from '../../../components/ui';
import { actionsClient, type ReviewCandle, type ReviewProblem } from './actionsClient';
import { DataReviewChart } from './DataReviewChart';
import './actions.css';

export interface ViewAnalyzeTarget {
  id: string;
  symbol: string;
  timeframe?: string;
  instrument?: string;
  from?: string;
  to?: string;
  bars?: number;
}

export function ViewAnalyzeDialog({
  target,
  onClose,
}: {
  target: ViewAnalyzeTarget;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'data' | 'chart' | 'quality'>('data');
  const [timeframe, setTimeframe] = useState<string>(target.timeframe || 'M1');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Tab 1: Data Table state
  const [rows, setRows] = useState<Array<[string, number, number, number, number, number]>>([]);
  const [totalRows, setTotalRows] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const pageSize = 100;

  // Tab 2: Chart Candles state
  const [candles, setCandles] = useState<ReviewCandle[]>([]);

  // Tab 3: Quality state
  const [qualityScore, setQualityScore] = useState<number>(100);
  const [totalBars, setTotalBars] = useState<number>(0);
  const [totalErrors, setTotalErrors] = useState<number>(0);
  const [problems, setProblems] = useState<ReviewProblem[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      setLoading(true);
      setError('');
      try {
        if (activeTab === 'data') {
          const res = await actionsClient.reviewData({
            symbol: target.symbol,
            timeframe,
            offset: page * pageSize,
            limit: pageSize,
          });
          if (!cancelled) {
            setRows(res.rows);
            setTotalRows(res.totalRows);
          }
        } else if (activeTab === 'chart') {
          const res = await actionsClient.reviewChart({
            symbol: target.symbol,
            timeframe,
            limit: 500,
          });
          if (!cancelled) {
            setCandles(res.chart);
          }
        } else if (activeTab === 'quality') {
          const res = await actionsClient.reviewQuality({
            symbol: target.symbol,
            timeframe,
          });
          if (!cancelled) {
            setQualityScore(res.qualityScore);
            setTotalBars(res.totalBars);
            setTotalErrors(res.totalErrors);
            setProblems(res.problems);
          }
        }
      } catch (exc: any) {
        if (!cancelled) {
          setError(exc?.message || 'Failed to retrieve data review');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void fetchData();
    return () => {
      cancelled = true;
    };
  }, [target.symbol, timeframe, activeTab, page]);

  const totalPages = Math.ceil(totalRows / pageSize) || 1;
  const isTick = timeframe.toUpperCase().includes('TICK');

  return (
    <div className="data-tools-flow">
      <Modal
        title={`View & Analyze - ${target.symbol} (${timeframe})`}
        width={850}
        onClose={onClose}
        footer={
          <Button className="secondary" onClick={onClose}>
            Close
          </Button>
        }
      >
        <div className="review-metadata">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <label style={{ fontSize: 12, fontWeight: 600 }}>Timeframe:</label>
              <Select value={timeframe} onChange={setTimeframe}>
                <option value="M1">M1 (1 Minute)</option>
                <option value="M5">M5 (5 Minutes)</option>
                <option value="M15">M15 (15 Minutes)</option>
                <option value="H1">H1 (1 Hour)</option>
                <option value="D1">D1 (Daily)</option>
              </Select>
            </div>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>
              Range: {target.from || '—'} to {target.to || '—'}
            </div>
          </div>
        </div>

        {error && (
          <p role="alert" className="actions-error">
            {error}
          </p>
        )}

        <div className="review-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === 'data'}
            onClick={() => setActiveTab('data')}
          >
            Data Table
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'chart'}
            onClick={() => setActiveTab('chart')}
          >
            Chart
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'quality'}
            onClick={() => setActiveTab('quality')}
          >
            Data Quality ({qualityScore}%)
          </button>
        </div>

        <div className="review-tab-panel">
          {loading && (
            <div style={{ padding: 16, textAlign: 'center', color: 'var(--muted)' }}>
              Loading {activeTab} data…
            </div>
          )}

          {!loading && activeTab === 'data' && (
            <>
              <div className="review-data-toolbar">
                <span style={{ fontSize: 12 }}>
                  Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, totalRows)} of {totalRows} bars
                </span>
                <div>
                  <Button
                    disabled={page <= 0}
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                  >
                    Previous
                  </Button>
                  <Button
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage(p => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
              <div className="review-virtual-table">
                <table>
                  <thead>
                    <tr>
                      <th>DateTime</th>
                      <th>Open</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Close</th>
                      <th>Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, idx) => (
                      <tr key={idx}>
                        <td>{row[0]}</td>
                        <td>{typeof row[1] === 'number' ? row[1].toFixed(5) : row[1]}</td>
                        <td>{typeof row[2] === 'number' ? row[2].toFixed(5) : row[2]}</td>
                        <td>{typeof row[3] === 'number' ? row[3].toFixed(5) : row[3]}</td>
                        <td>{typeof row[4] === 'number' ? row[4].toFixed(5) : row[4]}</td>
                        <td>{row[5]}</td>
                      </tr>
                    ))}
                    {!rows.length && (
                      <tr>
                        <td colSpan={6} style={{ textAlign: 'center', padding: 20 }}>
                          No bars available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {!loading && activeTab === 'chart' && (
            <DataReviewChart candles={candles} isTick={isTick} />
          )}

          {!loading && activeTab === 'quality' && (
            <div className="quality-view">
              <div className="quality-summary">
                <table>
                  <thead>
                    <tr>
                      <th>Quality Score</th>
                      <th>Total Bars</th>
                      <th>Identified Problems</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontSize: 16, fontWeight: 700, color: qualityScore >= 90 ? 'var(--good, #68d391)' : 'var(--warn, #e7c88e)' }}>
                        {qualityScore}%
                      </td>
                      <td>{totalBars.toLocaleString()}</td>
                      <td style={{ color: totalErrors > 0 ? 'var(--bad)' : 'inherit' }}>
                        {totalErrors}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="quality-details">
                <table>
                  <thead>
                    <tr>
                      <th style={{ width: 140 }}>Timestamp</th>
                      <th>Identified Issue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {problems.map((p, idx) => (
                      <tr key={idx}>
                        <td>{p.date}</td>
                        <td style={{ textAlign: 'left' }}>{p.problem}</td>
                      </tr>
                    ))}
                    {!problems.length && (
                      <tr>
                        <td colSpan={2} style={{ color: 'var(--good, #68d391)', padding: 12 }}>
                          No quality defects detected. Data is continuous and within bounds.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
