import React from 'react';

export interface WFWindowRowData {
  window_index: number;
  is_start: string;
  is_end: string;
  oos_start: string;
  oos_end: string;
  best_params: Record<string, number | boolean>;
  is_net_profit: number;
  oos_net_profit: number;
  passed: boolean;
}

export interface WFMatrixCellData {
  runs_count: number;
  oos_pct: number;
  robustness_pct: number;
  passed: boolean;
}

export interface ResultsWalkForwardProps {
  strategyId: string;
  isMatrix: boolean;
  selectedRunsCount: number;
  selectedOosPct: number;
  windows: WFWindowRowData[];
  matrixCells?: WFMatrixCellData[];
  robustnessPassed: number;
  robustnessTotal: number;
  overallPassed: boolean;
  onApplyLatestParams?: () => void;
  onExportCsv?: () => void;
}

export function ResultsWalkForward({
  strategyId,
  isMatrix,
  selectedRunsCount,
  selectedOosPct,
  windows,
  matrixCells = [],
  robustnessPassed,
  robustnessTotal,
  overallPassed,
  onApplyLatestParams,
  onExportCsv,
}: ResultsWalkForwardProps) {
  return (
    <div className="results-walk-forward" data-testid="results-walk-forward">
      <div className="wf-header">
        <h3>Walk-Forward Results: {strategyId}</h3>
        <p>
          Runs: {selectedRunsCount} | OOS: {selectedOosPct}% | Robustness:{' '}
          {robustnessPassed}/{robustnessTotal} ({overallPassed ? 'PASSED' : 'FAILED'})
        </p>
        <div className="wf-actions">
          {onApplyLatestParams && (
            <button
              className="sqd-btn"
              onClick={onApplyLatestParams}
              aria-label="Apply Latest Parameters"
            >
              Apply Latest Window Parameters
            </button>
          )}
          {onExportCsv && (
            <button className="sqd-btn" onClick={onExportCsv} aria-label="Export WF CSV">
              Export CSV
            </button>
          )}
        </div>
      </div>

      <div className="wf-windows-container">
        <h4>Walk-Forward Windows ({windows.length})</h4>
        <table className="wf-windows-table">
          <thead>
            <tr>
              <th>Window</th>
              <th>IS Period</th>
              <th>OOS Period</th>
              <th>IS Profit</th>
              <th>OOS Profit</th>
              <th>Best Params</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {windows.map((w) => (
              <tr key={w.window_index}>
                <td>{w.window_index}</td>
                <td>
                  {w.is_start} to {w.is_end}
                </td>
                <td>
                  {w.oos_start} to {w.oos_end}
                </td>
                <td>{w.is_net_profit.toFixed(2)}</td>
                <td>{w.oos_net_profit.toFixed(2)}</td>
                <td>{JSON.stringify(w.best_params)}</td>
                <td>{w.passed ? 'PASSED' : 'FAILED'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isMatrix && matrixCells.length > 0 && (
        <div className="wf-matrix-heatmap" data-testid="wf-matrix-heatmap">
          <h4>Walk-Forward Matrix Robustness Heatmap ({matrixCells.length} cells)</h4>
          <div className="matrix-cells-grid">
            {matrixCells.map((c, idx) => (
              <div
                key={idx}
                className={`matrix-cell ${c.passed ? 'passed' : 'failed'}`}
                title={`Runs: ${c.runs_count}, OOS: ${c.oos_pct}%, Robustness: ${c.robustness_pct}%`}
              >
                <span>
                  {c.runs_count}r / {c.oos_pct}%
                </span>
                <strong>{c.robustness_pct.toFixed(0)}%</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
