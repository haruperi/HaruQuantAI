import React, { useState, useMemo } from 'react';
import { Button, Modal } from '../../../components/ui';
import { filterStrategiesByCorrelation, type CorrelationPeriod, type FilterByCorrelationModalProps } from '../ProjectDatabanks/FilterByCorrelationModal';

export function FilterByCorrelationModal({
  isOpen,
  onClose,
  strategies,
  onApplyFilter,
}: FilterByCorrelationModalProps) {
  const [period, setPeriod] = useState<CorrelationPeriod>('Day');
  const [maxCorrelation, setMaxCorrelation] = useState<number>(0.5);

  const filterResult = useMemo(() => {
    return filterStrategiesByCorrelation(strategies, maxCorrelation, period);
  }, [strategies, maxCorrelation, period]);

  if (!isOpen) return null;

  const handleFilter = () => {
    onApplyFilter(filterResult.keepIds, filterResult.removedIds);
    onClose();
  };

  return (
    <Modal
      title="Filter by correlation"
      onClose={onClose}
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, width: '100%' }}>
          <Button onClick={onClose}>Close</Button>
          <Button
            className="primary"
            onClick={handleFilter}
            disabled={filterResult.removedIds.length === 0}
          >
            Filter ({filterResult.removedIds.length} will be removed)
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 440 }}>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted, #8b949e)', lineHeight: 1.5 }}>
          All strategies that have correlation bigger than Max will be removed from the current databank.
          Better performing strategies (higher net profit) will be retained.
        </p>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            padding: 14,
            background: 'var(--surface-muted, #1a1e24)',
            borderRadius: 4,
            border: '1px solid var(--border-color, #2d333b)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ fontSize: 13, fontWeight: 500 }}>Correlation period:</label>
            <select
              className="text-input"
              style={{ width: 140 }}
              value={period}
              onChange={e => setPeriod(e.target.value as CorrelationPeriod)}
            >
              <option value="Hour">Hour</option>
              <option value="Day">Day</option>
              <option value="Week">Week</option>
              <option value="Month">Month</option>
              <option value="Year">Year</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ fontSize: 13, fontWeight: 500 }}>Max correlation:</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                className="text-input"
                style={{ width: 90, textAlign: 'right' }}
                value={maxCorrelation}
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  if (!isNaN(val)) setMaxCorrelation(Math.max(0, Math.min(1, val)));
                }}
              />
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={maxCorrelation}
                onChange={e => setMaxCorrelation(parseFloat(e.target.value))}
                style={{ width: 100 }}
              />
            </div>
          </div>
        </div>

        {/* Results summary preview */}
        <div
          style={{
            padding: 12,
            borderRadius: 4,
            background: 'var(--surface-color, #12161c)',
            border: '1px solid var(--border-subtle, #21262d)',
            fontSize: 12,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span>Total strategies in databank:</span>
            <strong>{strategies.length}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, color: '#3fb950' }}>
            <span>Strategies to keep:</span>
            <strong>{filterResult.keepIds.length}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#f85149' }}>
            <span>Correlated strategies to remove:</span>
            <strong>{filterResult.removedIds.length}</strong>
          </div>

          {filterResult.correlatedPairs.length > 0 && (
            <div style={{ marginTop: 10, borderTop: '1px solid #30363d', paddingTop: 8 }}>
              <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4 }}>
                Detected Correlated Pairs (&gt; {maxCorrelation.toFixed(2)}):
              </div>
              <div style={{ maxHeight: 100, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 3 }}>
                {filterResult.correlatedPairs.map((pair, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 11,
                      padding: '2px 4px',
                      background: 'rgba(255,255,255,0.02)',
                    }}
                  >
                    <span>{pair.s1} ↔ {pair.s2}</span>
                    <span style={{ color: '#f0883e', fontWeight: 600 }}>
                      r = {pair.corr.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
