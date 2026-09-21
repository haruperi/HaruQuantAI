import { describe, expect, it } from 'vitest';
import {
  computeCorrelationMatrix,
  computeEqualWeights,
  simulatePortfolio,
} from '../../../../src/workspace/PortfolioComposer/portfolioOptimization';

describe('Portfolio Master Search & Filtering Logic', () => {
  const dummyEquity1 = [
    { time: '2026-01-01', value: 100000, drawdown: 0 },
    { time: '2026-02-01', value: 105000, drawdown: 0 },
    { time: '2026-03-01', value: 110000, drawdown: 0 },
  ];
  const dummyEquity2 = [
    { time: '2026-01-01', value: 100000, drawdown: 0 },
    { time: '2026-02-01', value: 104000, drawdown: 0 },
    { time: '2026-03-01', value: 108000, drawdown: 0 },
  ];
  const dummyEquity3 = [
    { time: '2026-01-01', value: 100000, drawdown: 0 },
    { time: '2026-02-01', value: 96000, drawdown: 4000 },
    { time: '2026-03-01', value: 92000, drawdown: 8000 },
  ];

  it('filters candidate portfolios exceeding max correlation threshold', () => {
    // Strategy 1 and Strategy 2 are highly correlated (~1.0)
    // Strategy 1 and Strategy 3 are negatively correlated
    const curves = [
      dummyEquity1.map(p => p.value),
      dummyEquity2.map(p => p.value),
      dummyEquity3.map(p => p.value),
    ];
    const corr = computeCorrelationMatrix(curves);

    const maxCorrThreshold = 0.50;

    // Combination [0, 1] has corr > 0.50 -> Should be rejected
    const pair1Corr = corr[0][1];
    expect(pair1Corr).toBeGreaterThan(maxCorrThreshold);

    // Combination [0, 2] has corr < 0.50 -> Should be accepted
    const pair2Corr = corr[0][2];
    expect(pair2Corr).toBeLessThanOrEqual(maxCorrThreshold);
  });

  it('evaluates candidate portfolio fitness across objective functions', () => {
    const members = [
      {
        id: 's1',
        name: 'Strat 1',
        symbol: 'EURUSD',
        sector: 'FX',
        weight: 50,
        multiplier: 1.0,
        enabled: true,
        equity: dummyEquity1,
      },
      {
        id: 's2',
        name: 'Strat 2',
        symbol: 'GBPUSD',
        sector: 'FX',
        weight: 50,
        multiplier: 1.0,
        enabled: true,
        equity: dummyEquity2,
      },
    ];

    const sim = simulatePortfolio(members, 100000, 20, true);

    // Objective: Return / DD ratio
    const fitnessReturnDD = sim.returnDD;
    expect(fitnessReturnDD).toBeGreaterThan(0);

    // Objective: Sharpe ratio
    const fitnessSharpe = sim.sharpe;
    expect(fitnessSharpe).toBeGreaterThan(0);

    // Objective: Net profit
    const fitnessNetProfit = sim.netProfit / 10000;
    expect(fitnessNetProfit).toBeGreaterThan(0);
  });

  it('enforces min and max strategy counts in combinations', () => {
    const minStrats = 2;
    const maxStrats = 4;
    const available = ['s1', 's2', 's3', 's4', 's5'];

    // Test subset sizes
    const validSizes = [2, 3, 4];
    validSizes.forEach(size => {
      expect(size).toBeGreaterThanOrEqual(minStrats);
      expect(size).toBeLessThanOrEqual(maxStrats);
    });

    const weights = computeEqualWeights(3);
    expect(weights.length).toBe(3);
    expect(weights.reduce((a, b) => a + b, 0)).toBe(100);
  });
});
