import { memo, useState } from 'react';

export interface LogEntry {
  timestampMs: number;
  level: 'INFO' | 'WARNING' | 'REJECTED';
  strategyId: string | null;
  message: string;
}

export interface PortfolioComposerLogProps {
  entries: LogEntry[];
  totalOrdersEvaluated: number;
  rejectedMarginOrders: number;
}

export const ResultsPortfolioComposerLog = memo(function ResultsPortfolioComposerLog({
  entries,
  totalOrdersEvaluated,
  rejectedMarginOrders,
}: PortfolioComposerLogProps) {
  const [levelFilter, setLevelFilter] = useState<string>('ALL');

  const filtered = entries.filter(
    e => levelFilter === 'ALL' || e.level === levelFilter
  );

  return (
    <div className="sqr-content pf-log-view">
      <h4>Portfolio Composer Execution Log</h4>
      <div className="pf-log-stats">
        <span>Total Orders Evaluated: {totalOrdersEvaluated}</span>
        <span className={rejectedMarginOrders > 0 ? 'pf-warning' : ''}>
          Margin Rejections: {rejectedMarginOrders}
        </span>
      </div>
      <div className="pf-log-toolbar">
        <label>
          Filter Level:
          <select
            value={levelFilter}
            onChange={e => setLevelFilter(e.target.value)}
            aria-label="Log level filter"
          >
            <option value="ALL">All</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </label>
      </div>
      <table className="sqr-data-table pf-log-table">
        <thead>
          <tr>
            <th>Time (ms)</th>
            <th>Level</th>
            <th>Strategy</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan={4} className="pf-empty">
                No log entries recorded.
              </td>
            </tr>
          ) : (
            filtered.map((entry, idx) => (
              <tr key={idx} className={`pf-log-row-${entry.level.toLowerCase()}`}>
                <td>{entry.timestampMs}</td>
                <td>{entry.level}</td>
                <td>{entry.strategyId ?? '-'}</td>
                <td>{entry.message}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
});
