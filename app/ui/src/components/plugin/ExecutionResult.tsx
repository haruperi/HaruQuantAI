/**
 * Generic execution result viewer displaying reproducibility metadata, series charts, and output tables.
 */

import React from 'react';
import type { SingleExecutionResult } from '../../api/contracts.generated';

export interface ExecutionResultProps {
  result: SingleExecutionResult | null;
}

export function ExecutionResult({ result }: ExecutionResultProps) {
  if (!result) {
    return (
      <div className="empty-result">
        <p>No execution results available. Run evaluation to inspect outputs.</p>
      </div>
    );
  }

  const { success, outputs, reproducibility, issues, elapsed_seconds } = result;

  return (
    <div className="execution-result-view">
      <div className={`status-banner ${success ? 'banner-success' : 'banner-failure'}`}>
        <strong>{success ? 'Execution Succeeded' : 'Execution Failed'}</strong>
        <span>Elapsed: {(elapsed_seconds * 1000).toFixed(1)} ms</span>
      </div>

      {issues.length > 0 && (
        <div className="issues-card">
          <h4>Validation Issues ({issues.length})</h4>
          <ul>
            {issues.map((issue, i) => (
              <li key={`${issue.path}-${issue.code}-${i}`}>
                <strong>[{issue.code}]</strong> <code>{issue.path}</code>: {issue.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {reproducibility && (
        <div className="reproducibility-card">
          <h4>Execution Provenance</h4>
          <dl className="details-grid">
            <dt>Graph Fingerprint</dt>
            <dd><code>{reproducibility.graph_fingerprint.substring(0, 16)}…</code></dd>
            <dt>Catalog Fingerprint</dt>
            <dd><code>{reproducibility.catalog_fingerprint.substring(0, 16)}…</code></dd>
            <dt>Dependency Fingerprint</dt>
            <dd><code>{reproducibility.dependency_fingerprint.substring(0, 16)}…</code></dd>
            <dt>Input Hash</dt>
            <dd><code>{reproducibility.input_hash.substring(0, 16)}…</code></dd>
            <dt>Output Hash</dt>
            <dd><code>{reproducibility.output_hash.substring(0, 16)}…</code></dd>
          </dl>
        </div>
      )}

      <div className="outputs-section">
        <h4>Outputs ({Object.keys(outputs).length})</h4>
        {Object.entries(outputs).map(([portKey, val]) => {
          const isSeries = Array.isArray(val);

          return (
            <div key={portKey} className="output-card">
              <header className="output-header">
                <strong>{portKey}</strong>
                <span>{isSeries ? `${val.length} samples` : typeof val}</span>
              </header>

              {isSeries ? (
                <div className="series-display">
                  {/* Mini SVG line preview */}
                  <div className="series-chart-preview" style={{ height: 100, width: '100%' }}>
                    <svg viewBox={`0 0 ${val.length * 10} 100`} style={{ width: '100%', height: 100 }}>
                      <polyline
                        fill="none"
                        stroke="#30b7e8"
                        strokeWidth="2"
                        points={val
                          .map((v, i) => {
                            const num =
                              typeof v === 'number'
                                ? v
                                : typeof v === 'object' && v && '__missing__' in (v as object)
                                ? 0
                                : 0;
                            const y = 100 - Math.min(100, Math.max(0, num));
                            return `${i * 10},${y}`;
                          })
                          .join(' ')}
                      />
                    </svg>
                  </div>

                  <div className="plain-table-wrap">
                    <table className="plain-table">
                      <thead>
                        <tr>
                          <th>Index</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {val.slice(0, 20).map((v, idx) => (
                          <tr key={idx}>
                            <td>{idx}</td>
                            <td>
                              {typeof v === 'object' && v && '__missing__' in (v as object) ? (
                                <span className="pill warn">Missing ({(v as any).reason})</span>
                              ) : typeof v === 'boolean' ? (
                                <span className={v ? 'pill green' : 'pill red'}>{String(v)}</span>
                              ) : (
                                String(v)
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {val.length > 20 && (
                      <small className="muted">Showing first 20 of {val.length} samples</small>
                    )}
                  </div>
                </div>
              ) : (
                <div className="scalar-display">
                  <code>{JSON.stringify(val)}</code>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
