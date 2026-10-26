import { useEffect, useState } from 'react';
import { Button, Modal } from '../../../components/ui';
import { activeExternalLines, type ExternalIndicatorDefinition } from './externalIndicators';
import { fetchExternalReview } from './externalIndicatorsApiClient';
import './externalIndicators.css';

export function ExternalIndicatorViewDialog({ item, onClose }: { item: ExternalIndicatorDefinition; onClose: () => void }) {
  const lines = activeExternalLines(item);
  const [loading, setLoading] = useState(item.records.length === 0);
  const [remoteRows, setRemoteRows] = useState<Array<{ timestamp: string; values: (string | number)[] }>>([]);
  const [remoteColumns, setRemoteColumns] = useState<string[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (item.records.length > 0) return;
    let active = true;
    setLoading(true);
    fetchExternalReview(item.name, 200, 0)
      .then(res => {
        if (!active) return;
        const columns = res.columns && res.columns.length > 0 ? res.columns : lines.map(l => l.name);
        setRemoteColumns(columns);
        const mapped = (res.records || []).map(r => ({
          timestamp: r.timestamp,
          values: columns.map(c => (r.values as Record<string, number>)?.[c] ?? ''),
        }));
        setRemoteRows(mapped);
      })
      .catch(cause => {
        if (active) setError(cause instanceof Error ? cause.message : 'Unable to load observations.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [item.name]);

  const displayColumns = remoteColumns.length > 0 ? remoteColumns : lines.map((l, index) => l.name || `Value ${index + 1}`);

  const displayRows = item.records.length > 0
    ? item.records.map(row => ({
        timestamp: new Date(row.timestamp).toISOString().replace('T', ' ').slice(0, 16),
        values: row.values,
      }))
    : remoteRows;

  return (
    <div className="external-flow">
      <Modal title={`View custom data for '${item.name}'`} width={800} onClose={onClose} footer={<Button onClick={onClose}>Close</Button>}>
        {loading && <p className="external-note">Loading observations...</p>}
        {error && <p className="external-error" role="alert">{error}</p>}
        {!loading && (
          <div className="external-view-grid">
            <table className="plain-table" aria-label={`Data for ${item.name}`}>
              <thead>
                <tr>
                  <th>Date</th>
                  {displayColumns.map((colName, index) => (
                    <th key={index}>{colName}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayRows.map((row, index) => (
                  <tr key={`${row.timestamp}-${index}`}>
                    <td>{row.timestamp}</td>
                    {row.values.map((value, vIndex) => (
                      <td key={vIndex}>{value}</td>
                    ))}
                  </tr>
                ))}
                {!displayRows.length && (
                  <tr>
                    <td colSpan={Math.max(1, displayColumns.length + 1)}>No observations recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </div>
  );
}
