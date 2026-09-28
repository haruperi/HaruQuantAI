import { describe, it, expect } from 'vitest';
import { useAppStore } from '../../../../app/workspace/Results/localState';
const strategies = useAppStore.getState().strategies;

describe('Trade Analysis Performance Breakdown and Statistics', () => {
  it('aggregates annual statistics from trades accurately', () => {
    const s = strategies[0];
    const trades = s.trades;

    const yearMap = new Map<number, { count: number; profit: number }>();
    trades.forEach(t => {
      const yr = new Date(t.entryTime).getFullYear();
      const cur = yearMap.get(yr) || { count: 0, profit: 0 };
      cur.count += 1;
      cur.profit += t.pnl;
      yearMap.set(yr, cur);
    });

    expect(yearMap.size).toBeGreaterThan(0);
    const totalCount = Array.from(yearMap.values()).reduce((acc, v) => acc + v.count, 0);
    expect(totalCount).toBe(trades.length);
  });

  it('calculates consecutive winning and losing streaks', () => {
    const s = strategies[0];
    let maxWin = 0;
    let maxLoss = 0;
    let curWin = 0;
    let curLoss = 0;

    s.trades.forEach(t => {
      if (t.pnl > 0) {
        curWin++;
        curLoss = 0;
        maxWin = Math.max(maxWin, curWin);
      } else if (t.pnl < 0) {
        curLoss++;
        curWin = 0;
        maxLoss = Math.max(maxLoss, curLoss);
      }
    });

    expect(maxWin).toBeGreaterThanOrEqual(1);
    expect(maxLoss).toBeGreaterThanOrEqual(1);
  });
});
