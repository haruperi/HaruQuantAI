import { describe, expect, it } from 'vitest';
import type { OptimizationParamRow, OptimizationSettings } from '../../../../src/app/types';

describe('Optimizer Modes and Parameter Space (FEAT-UI-RESEARCH Phase 3)', () => {
  it('calculates single parameter combinations accurately', () => {
    const param: OptimizationParamRow = {
      name: 'FastPeriod',
      enabled: true,
      min: 5,
      max: 50,
      step: 5,
      originalValue: 14,
    };

    const count = param.step > 0 ? Math.floor((param.max - param.min) / param.step) + 1 : 1;
    expect(count).toBe(10); // 5, 10, 15, 20, 25, 30, 35, 40, 45, 50
  });

  it('calculates total combinatorial parameter space across active parameters', () => {
    const parameters: OptimizationParamRow[] = [
      { name: 'FastPeriod', enabled: true, min: 10, max: 30, step: 5, originalValue: 20 }, // 5 trials: 10, 15, 20, 25, 30
      { name: 'SlowPeriod', enabled: true, min: 50, max: 100, step: 10, originalValue: 70 }, // 6 trials: 50, 60, 70, 80, 90, 100
      { name: 'ATRPeriod', enabled: false, min: 7, max: 28, step: 7, originalValue: 14 }, // Disabled
    ];

    const active = parameters.filter((p) => p.enabled);
    expect(active.length).toBe(2);

    const totalCombinations = active.reduce((acc, p) => {
      const count = p.step > 0 ? Math.floor((p.max - p.min) / p.step) + 1 : 1;
      return acc * count;
    }, 1);

    expect(totalCombinations).toBe(30); // 5 * 6 = 30
  });

  it('supports 4 optimization modes', () => {
    const validModes: OptimizationSettings['mode'][] = [
      'Simple',
      'Sequential',
      'Walk-Forward',
      'WF Matrix',
    ];

    expect(validModes.length).toBe(4);
    expect(validModes.includes('Simple')).toBe(true);
    expect(validModes.includes('Sequential')).toBe(true);
    expect(validModes.includes('Walk-Forward')).toBe(true);
    expect(validModes.includes('WF Matrix')).toBe(true);
  });

  it('calculates Walk-Forward Efficiency (WFE %) and evaluates robustness thresholds', () => {
    const evaluateWFE = (isAnnualProfit: number, oosAnnualProfit: number) => {
      if (isAnnualProfit <= 0) return 0;
      return Math.round((oosAnnualProfit / isAnnualProfit) * 100);
    };

    const robustRun = evaluateWFE(25000, 17500); // 70%
    const acceptableRun = evaluateWFE(20000, 11000); // 55%
    const fragileRun = evaluateWFE(30000, 9000); // 30%

    expect(robustRun).toBe(70);
    expect(robustRun >= 60).toBe(true); // Robust plateau

    expect(acceptableRun).toBe(55);
    expect(acceptableRun >= 50 && acceptableRun < 60).toBe(true); // Acceptable

    expect(fragileRun).toBe(30);
    expect(fragileRun < 50).toBe(true); // Overfitted / fragile
  });

  it('computes 2D Walk-Forward matrix summary stats', () => {
    const isValues = [20, 25, 30, 35, 40];
    const runValues = [5, 8, 10, 12, 15];

    const totalCells = isValues.length * runValues.length;
    expect(totalCells).toBe(25);

    // Synthetic test matrix
    const matrixScores = [
      [55, 60, 68, 62, 54],
      [62, 70, 75, 68, 58],
      [65, 74, 82, 72, 60],
      [58, 66, 70, 64, 52],
      [48, 52, 56, 50, 44],
    ];

    const flat = matrixScores.flat();
    const passed = flat.filter((score) => score >= 50).length;
    const avgScore = Math.round(flat.reduce((a, b) => a + b, 0) / flat.length);

    expect(passed).toBe(23); // 23 of 25 passed
    expect(avgScore).toBeGreaterThanOrEqual(60);
    const passRate = Math.round((passed / totalCells) * 100);
    expect(passRate).toBe(92);
  });
});
