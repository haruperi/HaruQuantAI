import React, { useState, useMemo } from 'react';
import { Button, Modal } from '../../../../components/ui';
import type { Strategy } from '../presentation';

export interface FilterByCorrelationModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategies: Strategy[];
  onApplyFilter: (keepStrategyIds: string[], removedStrategyIds: string[]) => void;
}

export type CorrelationPeriod = 'Hour' | 'Day' | 'Week' | 'Month' | 'Year';

/**
 * Calculates Pearson correlation coefficient between two numeric arrays.
 */
export function calculatePearsonCorrelation(x: number[], y: number[]): number {
  const n = Math.min(x.length, y.length);
  if (n < 2) return 0;

  let sumX = 0;
  let sumY = 0;
  for (let i = 0; i < n; i++) {
    sumX += x[i];
    sumY += y[i];
  }
  const meanX = sumX / n;
  const meanY = sumY / n;

  let num = 0;
  let denX = 0;
  let denY = 0;
  for (let i = 0; i < n; i++) {
    const diffX = x[i] - meanX;
    const diffY = y[i] - meanY;
    num += diffX * diffY;
    denX += diffX * diffX;
    denY += diffY * diffY;
  }

  const denom = Math.sqrt(denX * denY);
  if (denom === 0) return 0;
  return num / denom;
}

/**
 * Computes return series from equity curve or trades based on period.
 */
export function extractReturnsSeries(strategy: Strategy, period: CorrelationPeriod): number[] {
  if (strategy.equity && strategy.equity.length > 1) {
    const rawValues = strategy.equity.map(e => e.value);
    // Equity return deltas
    const step =
      period === 'Hour' ? 1 : period === 'Day' ? 2 : period === 'Week' ? 5 : period === 'Month' ? 10 : 20;
    const series: number[] = [];
    for (let i = step; i < rawValues.length; i += step) {
      const prev = rawValues[i - step];
      const curr = rawValues[i];
      series.push(prev === 0 ? 0 : (curr - prev) / Math.abs(prev));
    }
    return series.length > 1 ? series : rawValues;
  }

  // Fallback to trade PnLs
  if (strategy.trades && strategy.trades.length > 0) {
    return strategy.trades.map(t => t.pnl);
  }

  return [0, 0];
}

/**
 * Identifies strategies to keep vs remove based on correlation threshold.
 * Strategies with higher netProfit or fitness are preserved preferentially.
 */
export function filterStrategiesByCorrelation(
  strategies: Strategy[],
  maxCorrelation: number,
  period: CorrelationPeriod
): { keepIds: string[]; removedIds: string[]; correlatedPairs: Array<{ s1: string; s2: string; corr: number }> } {
  if (strategies.length <= 1) {
    return {
      keepIds: strategies.map(s => s.id),
      removedIds: [],
      correlatedPairs: [],
    };
  }

  // Sort strategies by performance descending (Net profit or Fitness)
  const sorted = [...strategies].sort((a, b) => {
    const pnlA = a.metrics?.netProfit ?? 0;
    const pnlB = b.metrics?.netProfit ?? 0;
    return pnlB - pnlA;
  });

  const seriesMap = new Map<string, number[]>();
  for (const s of sorted) {
    seriesMap.set(s.id, extractReturnsSeries(s, period));
  }

  const removed = new Set<string>();
  const correlatedPairs: Array<{ s1: string; s2: string; corr: number }> = [];

  for (let i = 0; i < sorted.length; i++) {
    const s1 = sorted[i];
    if (removed.has(s1.id)) continue;
    const series1 = seriesMap.get(s1.id)!;

    for (let j = i + 1; j < sorted.length; j++) {
      const s2 = sorted[j];
      if (removed.has(s2.id)) continue;
      const series2 = seriesMap.get(s2.id)!;

      const corr = calculatePearsonCorrelation(series1, series2);
      if (corr >= maxCorrelation) {
        correlatedPairs.push({ s1: s1.name, s2: s2.name, corr });
        // Since sorted by performance descending, s1 is better, remove s2
        removed.add(s2.id);
      }
    }
  }

  const keepIds = sorted.filter(s => !removed.has(s.id)).map(s => s.id);
  const removedIds = Array.from(removed);

  return { keepIds, removedIds, correlatedPairs };
}

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
