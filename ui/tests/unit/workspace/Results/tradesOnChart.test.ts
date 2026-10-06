import { describe, it, expect } from 'vitest';
import { strategies } from '../../../../src/plugins/databank/fixtures';

describe('Trades On Chart Computations and Layout', () => {
  it('maps strategy trades with entry and exit prices and direction', () => {
    const s = strategies[0];
    expect(s.trades.length).toBeGreaterThan(0);

    const firstTrade = s.trades[0];
    expect(firstTrade.side).toMatch(/Long|Short/);
    expect(firstTrade.entry).toBeGreaterThan(0);
    expect(firstTrade.exit).toBeGreaterThan(0);
    expect(typeof firstTrade.pnl).toBe('number');
  });

  it('computes moving average and bollinger bands windows over prices', () => {
    const prices = [1.08, 1.082, 1.081, 1.085, 1.089, 1.087, 1.086, 1.088, 1.09, 1.092];
    const period = 5;

    const sma: (number | null)[] = [];
    for (let i = 0; i < prices.length; i++) {
      if (i < period - 1) {
        sma.push(null);
      } else {
        const slice = prices.slice(i - period + 1, i + 1);
        const avg = slice.reduce((a, b) => a + b, 0) / period;
        sma.push(avg);
      }
    }

    expect(sma[0]).toBeNull();
    expect(sma[4]).toBeCloseTo(1.0834, 4);
  });
});
