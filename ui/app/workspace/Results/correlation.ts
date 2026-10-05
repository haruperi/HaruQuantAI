/** Local preview interpretation of immutable input; no peer algorithm dependency. */
import type { Strategy } from './documents';
export type CorrelationPeriod = 'Hour' | 'Day' | 'Week' | 'Month' | 'Year';

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
