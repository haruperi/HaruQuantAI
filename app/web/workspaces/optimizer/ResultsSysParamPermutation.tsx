import React from 'react';

export interface SPPMetricSummaryRowData {
  metric_id: string;
  label: string;
  original_value: number;
  median_value: number;
  mean_value: number;
  std_dev: number;
  percentile_5: number;
  percentile_95: number;
}

export interface ResultsSysParamPermutationProps {
  strategyId: string;
  totalPermutations: number;
  profitableRunsPct: number;
  summaryRows: SPPMetricSummaryRowData[];
  histogramBins?: [number, number][];
}

export function ResultsSysParamPermutation({
  strategyId,
  totalPermutations,
  profitableRunsPct,
  summaryRows,
  histogramBins = [],
}: ResultsSysParamPermutationProps) {
  return (
    <div className="results-spp-panel" data-testid="results-spp-panel">
      <div className="spp-header">
        <h3>System Parameter Permutation (SPP): {strategyId}</h3>
        <p>
          Total Permutations: {totalPermutations} | Profitable Runs: {profitableRunsPct.toFixed(1)}%
        </p>
      </div>

      <table className="spp-summary-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Original</th>
            <th>Median</th>
            <th>Mean</th>
            <th>Std Dev</th>
            <th>5th %ile</th>
            <th>95th %ile</th>
          </tr>
        </thead>
        <tbody>
          {summaryRows.map((r) => (
            <tr key={r.metric_id}>
              <td>{r.label}</td>
              <td>{r.original_value.toFixed(2)}</td>
              <td>{r.median_value.toFixed(2)}</td>
              <td>{r.mean_value.toFixed(2)}</td>
              <td>{r.std_dev.toFixed(2)}</td>
              <td>{r.percentile_5.toFixed(2)}</td>
              <td>{r.percentile_95.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {histogramBins.length > 0 && (
        <div className="spp-histogram" data-testid="spp-histogram">
          <h4>Distribution Bins ({histogramBins.length})</h4>
          <div className="bins-row">
            {histogramBins.map(([center, count], idx) => (
              <div key={idx} className="bin-item">
                <span>{center.toFixed(1)}</span>: <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
