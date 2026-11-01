import React from 'react';

export interface OptimizationRunRowData {
  run_index: number;
  parameters: Record<string, number>;
  metrics: Record<string, number>;
  passed: boolean;
}

export interface OptimizationProfileChartGridData {
  param_x: string;
  param_y?: string | null;
  metric: string;
  x_values: number[];
  y_values: number[];
  z_matrix: (number | null)[][];
}

export interface ResultsOptimizationProfileProps {
  strategyId: string;
  grid?: OptimizationProfileChartGridData;
  runs?: OptimizationRunRowData[];
  onExportCsv?: () => void;
}

export function ResultsOptimizationProfile({
  strategyId,
  grid,
  runs = [],
  onExportCsv,
}: ResultsOptimizationProfileProps) {
  return (
    <div className="results-optimization-profile" data-testid="results-optimization-profile">
      <div className="profile-header">
        <h3>Optimization Profile: {strategyId}</h3>
        {onExportCsv && (
          <button className="sqd-btn" onClick={onExportCsv} aria-label="Export CSV">
            Export CSV
          </button>
        )}
      </div>

      {grid && (
        <div className="profile-grid" data-testid="profile-chart-grid">
          <h4>
            Surface: {grid.param_x} {grid.param_y ? `vs ${grid.param_y}` : ''} ({grid.metric})
          </h4>
          <div className="grid-summary">
            <span>X steps: {grid.x_values.length}</span>
            <span>Y steps: {grid.y_values.length}</span>
          </div>
        </div>
      )}

      <div className="runs-table-container">
        <h4>Evaluated Combinations ({runs.length})</h4>
        <table className="runs-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Parameters</th>
              <th>Metrics</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.run_index}>
                <td>{r.run_index}</td>
                <td>{JSON.stringify(r.parameters)}</td>
                <td>{JSON.stringify(r.metrics)}</td>
                <td>{r.passed ? 'PASSED' : 'FAILED'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
