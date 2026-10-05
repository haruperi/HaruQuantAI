import { describe, expect, it } from 'vitest';
import {
  computeCorrelationMatrix,
  computeEqualWeights,
  computeMarkowitzWeights,
  computeMinVarianceWeights,
  computeRiskParityWeights,
  computeStrategyReturn,
  computeStrategyVolatility,
  normalizeWeights,
  simulatePortfolio,
} from '../../../../app/workspace/PortfolioComposer/portfolioOptimization';

describe('Portfolio Optimization & Weighting Algorithms', () => {
  it('normalizes weights array to sum precisely to 100%', () => {
    const raw = [20, 30, 50];
    const normalized = normalizeWeights(raw);
    expect(normalized.reduce((a, b) => a + b, 0)).toBe(100);
    expect(normalized).toEqual([20, 30, 50]);

    const arbitrary = [12, 17, 39];
    const norm2 = normalizeWeights(arbitrary);
    expect(norm2.reduce((a, b) => a + b, 0)).toBe(100);

    const empty = normalizeWeights([]);
    expect(empty).toEqual([]);
  });

  it('computes equal weights correctly summing to 100%', () => {
    const w2 = computeEqualWeights(2);
    expect(w2).toEqual([50, 50]);
    expect(w2.reduce((a, b) => a + b, 0)).toBe(100);

    const w3 = computeEqualWeights(3);
    expect(w3.reduce((a, b) => a + b, 0)).toBe(100);

    const w4 = computeEqualWeights(4);
    expect(w4).toEqual([25, 25, 25, 25]);
    expect(w4.reduce((a, b) => a + b, 0)).toBe(100);

    expect(computeEqualWeights(0)).toEqual([]);
  });

  it('computes risk parity weights inversely proportional to volatility', () => {
    // Low vol should get higher weight, high vol should get lower weight
    const vols = [0.10, 0.20, 0.40];
    const weights = computeRiskParityWeights(vols);

    expect(weights.reduce((a, b) => a + b, 0)).toBe(100);
    expect(weights[0]).toBeGreaterThan(weights[1]);
    expect(weights[1]).toBeGreaterThan(weights[2]);
  });

  it('computes minimum variance weights minimizing aggregate volatility', () => {
    const cov = [
      [0.04, 0.01, 0.00],
      [0.01, 0.09, 0.01],
      [0.00, 0.01, 0.16],
    ];
    const weights = computeMinVarianceWeights(cov);
    expect(weights.reduce((a, b) => a + b, 0)).toBe(100);
    expect(weights[0]).toBeGreaterThan(weights[2]);
  });

  it('computes Markowitz Efficient Frontier weights maximizing Sharpe', () => {
    const returns = [0.25, 0.15, 0.10];
    const vols = [0.15, 0.12, 0.20];
    const cov = [
      [0.0225, 0.005, 0.002],
      [0.005, 0.0144, 0.001],
      [0.002, 0.001, 0.04],
    ];
    const weights = computeMarkowitzWeights(returns, vols, cov, 0.02);
    expect(weights.reduce((a, b) => a + b, 0)).toBe(100);
    expect(weights.length).toBe(3);
  });

  it('computes correlation matrix between equity delta curves', () => {
    const c1 = [100, 105, 110, 115, 120];
    const c2 = [100, 104, 108, 112, 116];
    const c3 = [100, 95, 90, 85, 80];

    const matrix = computeCorrelationMatrix([c1, c2, c3]);
    expect(matrix.length).toBe(3);
    // Diagonal must be 1.0
    expect(matrix[0][0]).toBe(1.0);
    expect(matrix[1][1]).toBe(1.0);
    expect(matrix[2][2]).toBe(1.0);

    // c1 and c2 are perfectly positively correlated
    expect(matrix[0][1]).toBeCloseTo(1.0, 1);
    // c1 and c3 are negatively correlated
    expect(matrix[0][2]).toBeLessThan(0);
  });

  it('computes strategy volatility and returns from equity points', () => {
    const equity = [
      { time: '2026-01-01', value: 100000, drawdown: 0 },
      { time: '2026-02-01', value: 105000, drawdown: 0 },
      { time: '2026-03-01', value: 112000, drawdown: 0 },
    ];
    const ret = computeStrategyReturn(equity);
    expect(ret).toBeCloseTo(0.12, 2);

    const vol = computeStrategyVolatility(equity);
    expect(vol).toBeGreaterThan(0);
  });
});

describe('Portfolio Simulation Engine', () => {
  const dummyEquity = [
    { time: '2026-01-01', value: 100000, drawdown: 0 },
    { time: '2026-02-01', value: 104000, drawdown: 0 },
    { time: '2026-03-01', value: 108000, drawdown: 0 },
    { time: '2026-04-01', value: 106000, drawdown: 2000 },
    { time: '2026-05-01', value: 112000, drawdown: 0 },
  ];

  it('simulates shared-capital portfolio equity and drawdown', () => {
    const members = [
      {
        id: 's1',
        name: 'EURUSD Trend',
        symbol: 'EURUSD',
        sector: 'FX',
        weight: 60,
        multiplier: 1.0,
        enabled: true,
        equity: dummyEquity,
      },
      {
        id: 's2',
        name: 'GBPUSD Trend',
        symbol: 'GBPUSD',
        sector: 'FX',
        weight: 40,
        multiplier: 1.0,
        enabled: true,
        equity: dummyEquity,
      },
    ];

    const result = simulatePortfolio(members, 100000, 20, true);

    expect(result.activeMembers).toBe(2);
    expect(result.equity.length).toBe(dummyEquity.length);
    expect(result.netProfit).toBeGreaterThan(0);
    expect(result.returnDD).toBeGreaterThan(0);
    expect(result.sharpe).toBeGreaterThan(0);
    expect(result.correlationMatrix.length).toBe(2);
    expect(result.monthlyReturns.length).toBeGreaterThan(0);
  });

  it('handles empty or disabled portfolio members gracefully', () => {
    const result = simulatePortfolio([], 100000, 20, true);
    expect(result.activeMembers).toBe(0);
    expect(result.netProfit).toBe(0);
    expect(result.equity.length).toBe(1);
  });
});
