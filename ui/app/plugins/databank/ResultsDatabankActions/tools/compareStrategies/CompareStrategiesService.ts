import type { Strategy } from '../../../../../host/types';

/** Existing local mock comparison calculations, without donor backend requests. */
export function buildComparisonModel(s1: Strategy, s2: Strategy) {
  // Prepare normalized equity curves for dual SVG overlay
  const equity1 = s1.equity?.map(e => e.value) || [10000];
  const equity2 = s2.equity?.map(e => e.value) || [10000];
  const maxLen = Math.max(equity1.length, equity2.length);

  const minVal = Math.min(...equity1, ...equity2);
  const maxVal = Math.max(...equity1, ...equity2);
  const valRange = maxVal - minVal || 1;

  const width = 680;
  const height = 150;
  const pad = 12;

  const toPoints = (data: number[]) => {
    if (data.length <= 1) return '';
    return data
      .map((val, idx) => {
        const x = pad + (idx / (data.length - 1)) * (width - 2 * pad);
        const y = height - pad - ((val - minVal) / valRange) * (height - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const points1 = toPoints(equity1);
  const points2 = toPoints(equity2);

  const kpis: Array<{
    label: string;
    v1: number | string;
    v2: number | string;
    format: (v: any) => string;
    isHigherBetter: boolean;
  }> = [
    {
      label: 'Net profit',
      v1: s1.metrics?.netProfit ?? 0,
      v2: s2.metrics?.netProfit ?? 0,
      format: v => `$${Number(v).toLocaleString()}`,
      isHigherBetter: true,
    },
    {
      label: 'Profit factor',
      v1: s1.metrics?.profitFactor ?? 1,
      v2: s2.metrics?.profitFactor ?? 1,
      format: v => Number(v).toFixed(2),
      isHigherBetter: true,
    },
    {
      label: 'Max drawdown',
      v1: s1.metrics?.maxDrawdown ?? 0,
      v2: s2.metrics?.maxDrawdown ?? 0,
      format: v => `$${Number(v).toLocaleString()}`,
      isHigherBetter: false,
    },
    {
      label: 'Sharpe ratio',
      v1: s1.metrics?.sharpe ?? 0,
      v2: s2.metrics?.sharpe ?? 0,
      format: v => Number(v).toFixed(2),
      isHigherBetter: true,
    },
    {
      label: 'Total trades',
      v1: s1.metrics?.trades ?? s1.trades?.length ?? 0,
      v2: s2.metrics?.trades ?? s2.trades?.length ?? 0,
      format: v => `${v}`,
      isHigherBetter: true,
    },
    {
      label: 'Win rate',
      v1:
        s1.trades && s1.trades.length > 0
          ? (s1.trades.filter(t => t.pnl > 0).length / s1.trades.length) * 100
          : 50,
      v2:
        s2.trades && s2.trades.length > 0
          ? (s2.trades.filter(t => t.pnl > 0).length / s2.trades.length) * 100
          : 50,
      format: v => `${Number(v).toFixed(1)}%`,
      isHigherBetter: true,
    },
    {
      label: 'Stability',
      v1: s1.metrics?.stability ?? 80,
      v2: s2.metrics?.stability ?? 80,
      format: v => `${v}%`,
      isHigherBetter: true,
    },
  ];

  return { equity1, equity2, width, height, pad, points1, points2, kpis };
}
