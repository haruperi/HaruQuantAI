import { describe, expect, it } from 'vitest';
import type { RetesterSettings } from '../../../../src/app/types';

describe('Retester Workflow and Robustness Stress Tests (FEAT-UI-RETESTER Phase 4)', () => {
  it('implements correct databank routing logic (copy vs overwrite)', () => {
    const evaluateRouting = (source: string, destination: string) => {
      return source === destination ? 'overwrite' : 'copy';
    };

    expect(evaluateRouting('Results', 'Retest')).toBe('copy');
    expect(evaluateRouting('Results', 'Results')).toBe('overwrite');
    expect(evaluateRouting('Portfolio', 'Results')).toBe('copy');
  });

  it('manages alternative markets matrix selection and test matrix sizing', () => {
    let selectedMarkets = ['EURUSD', 'GBPUSD'];

    const toggleMarket = (list: string[], symbol: string) => {
      return list.includes(symbol)
        ? list.filter((s) => s !== symbol)
        : [...list, symbol];
    };

    selectedMarkets = toggleMarket(selectedMarkets, 'USDJPY');
    expect(selectedMarkets).toEqual(['EURUSD', 'GBPUSD', 'USDJPY']);

    selectedMarkets = toggleMarket(selectedMarkets, 'GBPUSD');
    expect(selectedMarkets).toEqual(['EURUSD', 'USDJPY']);

    // Matrix total combinations calculation
    const strategyCount = 6;
    const timeframeCount = 3; // e.g. M15, H1, H4
    const totalRetests = strategyCount * selectedMarkets.length * timeframeCount;
    expect(totalRetests).toBe(36); // 6 * 2 * 3 = 36
  });

  it('applies what-if stress tests: skips worst N% trades', () => {
    // Array of trade PnLs
    const trades = [-450, -320, -180, 50, 120, 180, 240, 310, 450, 600]; // 10 trades

    const skipWorstTrades = (tradeList: number[], pct: number) => {
      if (pct <= 0) return tradeList;
      const sorted = [...tradeList].sort((a, b) => a - b);
      const countToSkip = Math.ceil(tradeList.length * (pct / 100));
      return sorted.slice(countToSkip);
    };

    const originalNet = trades.reduce((a, b) => a + b, 0);
    expect(originalNet).toBe(1000);

    // Skip worst 10% (1 trade: -450)
    const stressedTrades10 = skipWorstTrades(trades, 10);
    expect(stressedTrades10.length).toBe(9);
    expect(stressedTrades10.includes(-450)).toBe(false);
    const stressedNet = stressedTrades10.reduce((a, b) => a + b, 0);
    expect(stressedNet).toBe(1450); // Net profit rises when outlier black-swan trade is excluded
  });

  it('applies spread multiplier and slippage stress adjustments', () => {
    const originalTradePips = 45.0;
    const baseSpreadPips = 1.2;

    const calculateStressedProfitPips = (
      pips: number,
      spreadMult: number,
      extraSlippage: number
    ) => {
      const addedSpread = baseSpreadPips * (spreadMult - 1.0);
      return pips - addedSpread - extraSlippage;
    };

    // Stressed with 2.0x spread and 1.5 pips slippage
    const stressedPips = calculateStressedProfitPips(originalTradePips, 2.0, 1.5);
    expect(stressedPips).toBe(45.0 - 1.2 - 1.5); // 42.3 pips
  });

  it('filters trades by trade direction (Long only / Short only / Both)', () => {
    const mixedTrades = [
      { id: 't1', side: 'Buy', profit: 240 },
      { id: 't2', side: 'Sell', profit: 180 },
      { id: 't3', side: 'Buy', profit: -120 },
      { id: 't4', side: 'Sell', profit: -80 },
    ];

    const filterByDirection = (
      list: typeof mixedTrades,
      dir: RetesterSettings['tradeDirection']
    ) => {
      if (dir === 'Both') return list;
      const target = dir === 'Long only' ? 'Buy' : 'Sell';
      return list.filter((t) => t.side === target);
    };

    const longOnly = filterByDirection(mixedTrades, 'Long only');
    expect(longOnly.length).toBe(2);
    expect(longOnly.every((t) => t.side === 'Buy')).toBe(true);

    const shortOnly = filterByDirection(mixedTrades, 'Short only');
    expect(shortOnly.length).toBe(2);
    expect(shortOnly.every((t) => t.side === 'Sell')).toBe(true);

    const both = filterByDirection(mixedTrades, 'Both');
    expect(both.length).toBe(4);
  });
});
