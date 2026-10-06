import type { Strategy } from '../../../../../host/types';

/** Existing fixture-only cross-check rule, preserved independently of donor statuses. */
export function strategyPassesMockChecks(netProfit: number, trades: number, maxDrawdown: number): boolean {
  return netProfit > 0 && trades >= 80 && maxDrawdown < 30000;
}

export function selectMockStrategies(
  strategies: readonly Strategy[],
  passed: boolean,
  setRows: (ids: string[]) => void,
  notify: (message: string) => void,
): void {
  const ids = strategies
    .filter(s => strategyPassesMockChecks(s.metrics.netProfit, s.metrics.trades, s.metrics.maxDrawdown) === passed)
    .map(s => s.id);
  setRows(ids);
  notify(`${passed ? 'Passed' : 'Failed'} strategies selected (${ids.length})`);
}
