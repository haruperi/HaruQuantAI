import type { Strategy } from '../../../host/types';

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
