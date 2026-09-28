import { describe, expect, it } from 'vitest';
import { databanks, strategies } from '../../../../../app/plugins/databank/Retester/fixtures';

describe('deterministic databank fixtures', () => {
  it('keeps headline metrics consistent with linked trade and equity records', () => {
    for (const strategy of strategies) {
      expect(strategy.metrics.trades).toBe(strategy.trades.length);
      const final = strategy.equity.at(-1)!.value;
      expect(strategy.metrics.netProfit).toBeCloseTo(final - 100000, 2);
      const grossWin = strategy.trades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0);
      const grossLoss = -strategy.trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0);
      expect(strategy.metrics.profitFactor).toBeCloseTo(grossWin / grossLoss, 2);
      expect(strategy.metrics.maxDrawdown).toBe(Math.max(...strategy.equity.map(p => p.drawdown)));
    }
  });

  it('uses stable IDs for databank membership', () => {
    const ids = new Set(strategies.map(s => s.id));
    expect(databanks.every(bank => bank.strategyIds.every(id => ids.has(id)))).toBe(true);
  });
});
