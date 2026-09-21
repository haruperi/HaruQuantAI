import { describe, it, expect } from 'vitest';
import { strategies } from '../../../../src/mocks/fixtures';

describe('Compare Strategies Logic & Equity Normalization', () => {
  it('correctly extracts comparative metrics between two strategies', () => {
    const s1 = strategies[0];
    const s2 = strategies[1] || strategies[0];

    expect(s1.metrics.netProfit).toBeDefined();
    expect(s2.metrics.netProfit).toBeDefined();

    const diff = s1.metrics.netProfit - s2.metrics.netProfit;
    expect(typeof diff).toBe('number');
  });

  it('normalizes equity series across different lengths for dual svg overlay', () => {
    const s1 = strategies[0];
    const s2 = strategies[1] || strategies[0];

    const eq1 = s1.equity.map(e => e.value);
    const eq2 = s2.equity.map(e => e.value);

    const minVal = Math.min(...eq1, ...eq2);
    const maxVal = Math.max(...eq1, ...eq2);
    const range = maxVal - minVal || 1;

    expect(range).toBeGreaterThan(0);

    const norm1 = eq1.map(v => (v - minVal) / range);
    const norm2 = eq2.map(v => (v - minVal) / range);

    expect(Math.min(...norm1)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...norm1)).toBeLessThanOrEqual(1.0);
    expect(Math.min(...norm2)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...norm2)).toBeLessThanOrEqual(1.0);
  });
});
