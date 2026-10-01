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
  const [rows, setRows] = useState<Array<Array<string | number | null>>>([]);
  const [columns, setColumns] = useState(['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']);
  const [revisions, setRevisions] = useState<Record<string, number>>({});
  const [edits, setEdits] = useState<Record<string, { values?: Record<string, number>; delete?: boolean }>>({});
  const [reload, setReload] = useState(0);
  const [saving, setSaving] = useState(false);
  const [qualityScope, setQualityScope] = useState('');
  const [totalRows, setTotalRows] = useState<number>(0);
  const [page, setPage] = useState<number>(0);
  const pageSize = 100;

  // Tab 2: Chart Candles state
  const [candles, setCandles] = useState<ReviewCandle[]>([]);

  // Tab 3: Quality state
  const [qualityScore, setQualityScore] = useState<number | null>(null);
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
            dataset_id: target.id,
            symbol: target.symbol,
            timeframe,
            offset: page * pageSize,
            limit: pageSize,
          });
          if (!cancelled) {
            setRows(res.rows); setRevisions(res.revisions || {}); setEdits({});
            setColumns(res.columns || ['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume']);
            setTotalRows(res.totalRows);
          }
        } else if (activeTab === 'chart') {
          const res = await actionsClient.reviewChart({
            dataset_id: target.id,
            symbol: target.symbol,
            timeframe,
            limit: 500,
          });
          if (!cancelled) {
            setCandles(res.chart);
          }
        } else if (activeTab === 'quality') {
          const res = await actionsClient.reviewQuality({
            dataset_id: target.id,
            symbol: target.symbol,
            timeframe,
          });
          if (!cancelled) {
            setQualityScore(res.qualityScore);
            setQualityScope(res.scope || '');
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
  }, [target.id, target.symbol, timeframe, activeTab, page, reload]);

  async function saveEdits() {
    setSaving(true); setError('');
    try { await actionsClient.saveDataChanges({ dataset_id: target.id, timeframe, expected_revisions: revisions, changes: Object.entries(edits).filter(([, change]) => change.delete || Object.keys(change.values || {}).length).map(([timestamp, change]) => ({ timestamp, ...change })) }); setEdits({}); setReload(value => value + 1); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save changes.'); }
    finally { setSaving(false); }
  }
  const editable = timeframe === (target.timeframe || 'M1');
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
                <option value={target.timeframe || 'M1'}>{target.timeframe || 'M1'} (Stored)</option>
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
            Data Quality ({qualityScore === null ? '—' : `${qualityScore}%`})
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
                {editable && <Button disabled={saving || !Object.keys(edits).length} onClick={() => void saveEdits()}>{saving ? 'Saving…' : 'Save changes'}</Button>}
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
                      {columns.map(column => <th key={column}>{column}</th>)}{editable && <th>Delete</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, idx) => (
                      <tr key={idx}>
                        {row.map((value, column) => <td key={column}>{editable && column > 0 ? <input aria-label={`${columns[column]} ${row[0]}`} type="number" step="any" disabled={saving || edits[String(row[0])]?.delete} value={edits[String(row[0])]?.values?.[columns[column]] ?? value ?? ''} onChange={event => { const timestamp = String(row[0]); const number = Number(event.target.value); setEdits(current => ({ ...current, [timestamp]: { ...current[timestamp], values: { ...current[timestamp]?.values, [columns[column]]: number } } })); }} /> : value === null ? 'Invalid' : value}</td>)}
                        {editable && <td><input type="checkbox" aria-label={`Delete ${row[0]}`} disabled={saving} checked={edits[String(row[0])]?.delete || false} onChange={event => { const timestamp = String(row[0]); setEdits(current => ({ ...current, [timestamp]: { ...current[timestamp], delete: event.target.checked } })); }} /></td>}
                      </tr>
                    ))}
                    {!rows.length && (
                      <tr>
                        <td colSpan={columns.length} style={{ textAlign: 'center', padding: 20 }}>
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
              <p>{qualityScope}</p>
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
                      <td style={{ fontSize: 16, fontWeight: 700, color: (qualityScore ?? 0) >= 90 ? 'var(--good, #68d391)' : 'var(--warn, #e7c88e)' }}>
                        {qualityScore === null ? '—' : `${qualityScore}%`}
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
                          No issues found by the checks performed.
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
