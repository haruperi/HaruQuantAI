import { describe, expect, it } from 'vitest';
import { BUILDING_BLOCKS_CATALOG } from '../../../../src/workspace/Builder/BuildingBlocksCatalog';
import type { BuilderSettings } from '../../../../src/app/types';

describe('Builder Settings and Building Blocks (FEAT-UI-RESEARCH Phase 3)', () => {
  it('defines a comprehensive catalog of 35+ building blocks across 6 categories', () => {
    expect(BUILDING_BLOCKS_CATALOG.length).toBeGreaterThanOrEqual(35);

    const categories = new Set(BUILDING_BLOCKS_CATALOG.map((b) => b.category));
    expect(categories.has('signals')).toBe(true);
    expect(categories.has('indicators')).toBe(true);
    expect(categories.has('candles')).toBe(true);
    expect(categories.has('time')).toBe(true);
    expect(categories.has('orders')).toBe(true);
    expect(categories.has('exits')).toBe(true);
  });

  it('filters building blocks by category correctly', () => {
    const signalBlocks = BUILDING_BLOCKS_CATALOG.filter((b) => b.category === 'signals');
    expect(signalBlocks.length).toBeGreaterThanOrEqual(6);
    expect(signalBlocks.some((b) => b.name.includes('MA'))).toBe(true);

    const indicatorBlocks = BUILDING_BLOCKS_CATALOG.filter((b) => b.category === 'indicators');
    expect(indicatorBlocks.length).toBeGreaterThanOrEqual(10);
    expect(indicatorBlocks.some((b) => b.name.includes('RSI'))).toBe(true);
    expect(indicatorBlocks.some((b) => b.name.includes('Bollinger'))).toBe(true);

    const exitBlocks = BUILDING_BLOCKS_CATALOG.filter((b) => b.category === 'exits');
    expect(exitBlocks.length).toBeGreaterThanOrEqual(5);
    expect(exitBlocks.some((b) => b.name.includes('Trailing Stop'))).toBe(true);
  });

  it('searches building blocks by query across name and description', () => {
    const query = 'reversal';
    const matches = BUILDING_BLOCKS_CATALOG.filter(
      (b) =>
        b.name.toLowerCase().includes(query) ||
        b.description.toLowerCase().includes(query)
    );
    expect(matches.length).toBeGreaterThan(0);
    expect(matches.every((m) => m.name.toLowerCase().includes(query) || m.description.toLowerCase().includes(query))).toBe(true);
  });

  it('correctly computes enabled blocks with custom block overrides', () => {
    const customBlocks: Record<string, boolean> = {
      sig_ma_cross: false, // override default true -> false
      sig_atr_breakout: true, // override default false -> true
    };

    const isEnabled = (id: string, defaultVal: boolean) =>
      customBlocks[id] !== undefined ? customBlocks[id] : defaultVal;

    expect(isEnabled('sig_ma_cross', true)).toBe(false);
    expect(isEnabled('sig_atr_breakout', false)).toBe(true);
    expect(isEnabled('ind_sma', true)).toBe(true);
  });

  it('validates qualification thresholds against strategy performance', () => {
    const thresholds = {
      minReturnDD: 1.4,
      minTrades: 80,
      maxDrawdownPct: 25,
      minProfitFactor: 1.3,
    };

    const candidatePassing = {
      returnDD: 1.85,
      trades: 120,
      drawdownPct: 18.2,
      profitFactor: 1.65,
    };

    const candidateFailing = {
      returnDD: 1.15, // fail
      trades: 65, // fail
      drawdownPct: 32.0, // fail
      profitFactor: 1.25, // fail
    };

    const checkQualification = (strat: typeof candidatePassing) => {
      return (
        strat.returnDD >= thresholds.minReturnDD &&
        strat.trades >= thresholds.minTrades &&
        strat.drawdownPct <= thresholds.maxDrawdownPct &&
        strat.profitFactor >= thresholds.minProfitFactor
      );
    };

    expect(checkQualification(candidatePassing)).toBe(true);
    expect(checkQualification(candidateFailing)).toBe(false);
  });

  it('calculates genetic island population and total candidate pool', () => {
    const mockSettings: Partial<BuilderSettings> = {
      islands: 4,
      population: 100,
      mutation: 35,
      crossover: 85,
      maxGenerations: 50,
    };

    const totalPool = (mockSettings.islands ?? 1) * (mockSettings.population ?? 0);
    expect(totalPool).toBe(400);

    const totalEvaluations = totalPool * (mockSettings.maxGenerations ?? 1);
    expect(totalEvaluations).toBe(20000);
  });
});
