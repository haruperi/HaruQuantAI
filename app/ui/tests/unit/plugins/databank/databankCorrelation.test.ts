import { describe, it, expect } from 'vitest';
import {
  calculatePearsonCorrelation,
  extractReturnsSeries,
  filterStrategiesByCorrelation,
} from '../../../../src/plugins/databank/ProjectDatabanks/FilterByCorrelationModal';
import { strategies } from '../../../../src/mocks/fixtures';

describe('Databank Filter By Correlation Math & Logic', () => {
  it('calculates Pearson correlation coefficient accurately', () => {
    // Identical series -> 1.0
    const x = [1, 2, 3, 4, 5];
    const y = [1, 2, 3, 4, 5];
    expect(calculatePearsonCorrelation(x, y)).toBeCloseTo(1.0, 4);

    // Perfectly inverse series -> -1.0
    const yInv = [5, 4, 3, 2, 1];
    expect(calculatePearsonCorrelation(x, yInv)).toBeCloseTo(-1.0, 4);

    // Flat series
    const flat = [2, 2, 2, 2, 2];
    expect(calculatePearsonCorrelation(x, flat)).toBe(0);

    // Insufficient points
    expect(calculatePearsonCorrelation([1], [1])).toBe(0);
  });

  it('extracts returns series for different correlation periods', () => {
    const s = strategies[0];
    const hourSeries = extractReturnsSeries(s, 'Hour');
    const daySeries = extractReturnsSeries(s, 'Day');
    const weekSeries = extractReturnsSeries(s, 'Week');

    expect(Array.isArray(hourSeries)).toBe(true);
    expect(Array.isArray(daySeries)).toBe(true);
    expect(Array.isArray(weekSeries)).toBe(true);
    expect(hourSeries.length).toBeGreaterThan(0);
  });

  it('filters out correlated strategies exceeding threshold and keeps better performers', () => {
    // Clone strategy with slight perturbation to guarantee high correlation
    const s1 = { ...strategies[0], id: 's1', name: 'Alpha Strategy', metrics: { ...strategies[0].metrics, netProfit: 12000 } };
    const s2 = { ...strategies[0], id: 's2', name: 'Beta Clone', metrics: { ...strategies[0].metrics, netProfit: 8000 } };

    const result = filterStrategiesByCorrelation([s1, s2], 0.7, 'Day');
    expect(result.keepIds).toContain('s1');
    expect(result.removedIds).toContain('s2');
    expect(result.correlatedPairs.length).toBe(1);
    expect(result.correlatedPairs[0].corr).toBeGreaterThan(0.9);
  });
});
